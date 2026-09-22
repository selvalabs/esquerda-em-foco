"""Executable specification for the FUTURE canonical filters (#53).
Not imported by any public page. Inputs are already-reviewed evidence, never
candidate biographies or party names. This module neither infers nor creates tags.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
SCOPES={'current_support','documented_topic','legacy_context'}
IDENTITY=re.compile(r'^(\d{4})-[a-z]{2}-(federais|estaduais)$')

def domain_lookup(source_id: str, crosswalk: dict) -> dict:
    """Return a concept decision, not candidate membership or a political position."""
    item=next((x for x in crosswalk['entries'] if x['source_concept_id']==source_id),None)
    if item is None:raise ValueError('Unknown source concept; no fuzzy or keyword fallback')
    return {k:item[k] for k in ('source_concept_id','target_concept_id','relation','scope_relation','automatic_candidate_mapping','activation_requirement')}

def _source_ok(source: dict) -> bool:
    if not isinstance(source,dict):return False
    if not isinstance(source.get('url'),str) or not isinstance(source.get('locator'),str):return False
    try:u=urlsplit(source['url'])
    except (ValueError,TypeError):return False
    return u.scheme in ('https','http') and bool(u.netloc) and not u.username and not u.password and bool(source.get('locator'))

def eligible(e: dict, edition_id: str, view: str) -> bool:
    """Fail closed. A catalogue match by itself can NEVER pass these requirements."""
    if view not in SCOPES or not IDENTITY.fullmatch(edition_id):raise ValueError('Invalid view or edition')
    if not isinstance(e,dict) or e.get('edition_id')!=edition_id:return False
    if not isinstance(e.get('candidate_id'),str) or not re.fullmatch(r'\d{12}',e['candidate_id']):return False
    if e.get('association_reviewed') is not True or e.get('individual_attribution') is not True:return False
    if not e.get('evidence_id') or not e.get('object') or not e.get('topic_id'):return False
    sources=e.get('sources');
    if not isinstance(sources,list) or not sources or not all(_source_ok(s) for s in sources):return False
    original=e.get('semantic')
    if not isinstance(original,str) or original not in SCOPES:return False
    if view=='legacy_context':return original=='legacy_context'
    if original=='legacy_context':return False  # A new claim-level review belongs to D2/D3, not a catalogue conversion.
    if not e.get('claim_id') or not e.get('nature'):return False
    if view=='documented_topic':return original in ('documented_topic','current_support')
    return (original=='current_support' and e.get('direction') in ('apoio','prioridade')
        and e.get('currentness_reviewed') is True
        and type(e.get('current_context_year')) is int
        and e['current_context_year']==int(edition_id[:4])
        and isinstance(e.get('current_context_sources'),list) and bool(e['current_context_sources'])
        and all(_source_ok(s) for s in e['current_context_sources']))

def select(evidence: list[dict], edition_id: str, view: str, selectors: list[tuple[str,str]], mode: str, taxonomy: dict, universe: list[str] | None = None) -> list[str]:
    """Union/intersection of proven topic memberships; groups never tag siblings.
Returns stable candidate keys for tests; ordering is not a product ranking.
"""
    if view not in SCOPES or not IDENTITY.fullmatch(edition_id):raise ValueError('Invalid view or edition')
    if mode not in ('any','all'):raise ValueError('Unknown combination; never fall back silently')
    if not selectors:
        if universe is None:raise ValueError('Empty selection requires explicit candidate universe; undocumented people must not disappear')
        if any(not isinstance(id,str) or not re.fullmatch(r'\d{12}',id) for id in universe):raise ValueError('Invalid universe identity')
        return sorted({edition_id+':'+id for id in universe})
    topics={t['id'] for t in taxonomy['topics']};groups={g['id']:set(g['members']) for g in taxonomy['groups']}
    expanded=[]
    for kind,id in selectors:
        if kind=='topic' and id in topics:expanded.append({id})
        elif kind=='group' and id in groups:expanded.append(groups[id])
        else:raise ValueError('Unknown selector or namespace')
    matched={}
    for e in evidence:
        if not eligible(e,edition_id,view):continue
        if e['topic_id'] not in topics:raise ValueError('Unknown evidence topic')
        key=edition_id+':'+e['candidate_id'];matched.setdefault(key,set()).add(e['topic_id'])
    return sorted(k for k,ts in matched.items() if not expanded or
        (all(ts & allowed for allowed in expanded) if mode=='all' else any(ts & allowed for allowed in expanded)))

def mandate_from_legacy(value):
    """Compatibility classification only, not verification of actual exercise."""
    if value is True or value=='true':return 'institutional_record_requires_source'
    if value is False or value=='false' or value is None:return 'not_confirmed'
    raise ValueError('Unsupported mandate flag')

def prior_history(rows: list[dict] | None, collection_state: str, election_year: int) -> str:
    if collection_state!='covered_snapshot' or rows is None:return 'not_established'
    if any(type(r.get('year')) is not int for r in rows):return 'not_established'
    return 'linked_prior_race' if any(r['year']<election_year for r in rows) else 'no_prior_in_covered_snapshot'

def vote_state(votes, verification: str) -> str:
    if verification=='verified_nominal':
        if type(votes) is not int or votes<0:raise ValueError('Verified nominal votes require a nonnegative integer')
        return 'verified_nominal'
    if votes is not None:raise ValueError('Unknown/uncollected/nonapplicable values cannot be coerced to zero')
    if verification not in ('not_collected','not_verified','not_applicable','not_yet_held'):raise ValueError('Unmapped vote status')
    return verification

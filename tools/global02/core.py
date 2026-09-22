"""Versioned metadata, rendering helpers and loss-preserving public adapters.
No collection, classification or network access belongs in this module.
"""
from __future__ import annotations
import copy
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[2]
PATH = re.compile(r'^/(?:[a-z0-9-]+/)*$')
ID = re.compile(r'^\d{4}-[a-z]{2}-(?:federais|estaduais)$')
STATES = {'ready', 'partial', 'absent', 'blocked_data', 'edition_specific', 'not_applicable'}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate(registry: dict) -> None:
    require(registry.get('schema_version') == '1.0.0', 'Unsupported editions schema')
    seen_ids, seen_routes, seen_aliases = set(), set(), set()
    states = registry['states']
    require(len({s['code'] for s in states}) == len(states), 'Duplicate state')
    for e in registry['editions']:
        eid = e['edition_id']
        require(bool(ID.fullmatch(eid)) and eid not in seen_ids, 'Invalid or duplicate edition')
        seen_ids.add(eid)
        require(eid == f"{e['election_year']}-{e['state'].lower()}-{e['office'].split('-')[-1]}", 'Identity mismatch')
        require(e['state'] in {s['code'] for s in states}, 'Unknown state')
        require(e['publication_status'] in ('published', 'branch_only', 'archived'), 'Invalid publication state')
        require(e['research']['status'] in ('partial_documentation', 'not_started', 'reviewed_scope'), 'Invalid research state')
        require('snapshot' in e and 'source' in e['snapshot'], 'Snapshot provenance missing')
        route = e['canonical_path']
        require(bool(PATH.fullmatch(route)) and route not in seen_routes, 'Invalid or duplicate canonical')
        seen_routes.add(route)
        require(e['current_path'] is None or bool(PATH.fullmatch(e['current_path'])), 'Invalid current path')
        require(e['publication_status'] != 'branch_only' or e['current_path'] is None, 'Branch must not have a public entry')
        for alias in e['aliases']:
            require(bool(PATH.fullmatch(alias)) and alias not in seen_aliases, 'Invalid or duplicate alias')
            seen_aliases.add(alias)
        for c in e['capabilities'].values():
            require(c['state'] in STATES, 'Invalid capability state')
            require(c['semantic'] in (None, 'current_support', 'documented_topic', 'legacy_context'), 'Invalid semantic')
        for alias in e['legacy_ids']:
            require(alias not in seen_ids, 'Duplicate legacy edition identity')
            seen_ids.add(alias)
    require(not seen_routes.intersection(seen_aliases), 'Alias shadows canonical route')
    currents = [e['current_path'] for e in registry['editions'] if e['current_path'] is not None]
    require(len(currents) == len(set(currents)), 'Duplicate current route')
    for e in registry['editions']:
        for other in registry['editions']:
            if e is not other:
                require(e['current_path'] not in [other['canonical_path'], *other['aliases']], 'Current route shadows another edition')


def url(base: str, path: str) -> str:
    u = urlsplit(base)
    require(u.scheme in ('http', 'https') and bool(u.netloc) and not u.username and not u.password and not u.query and not u.fragment, 'Invalid site base')
    require(bool(PATH.fullmatch(u.path)) and bool(PATH.fullmatch(path)), 'Invalid base or route')
    return urljoin(base, path.lstrip('/'))


def route(e: dict, phase: str = 'current') -> str | None:
    require(phase in ('current', 'next'), 'Invalid phase')
    if e['publication_status'] != 'published':
        return None
    return e['canonical_path'] if phase == 'next' else e['current_path']


def hub_data(registry: dict, phase: str = 'current') -> list[dict]:
    return [{**s, 'editions': [{**e, 'href': route(e, phase)} for e in registry['editions'] if e['state'] == s['code']]}
            for s in registry['states']]


def indexable_paths(registry: dict, phase: str = 'current') -> list[str]:
    paths = ['/']
    paths += [s['path'] for s in registry['states'] if phase == 'next' or s['published']]
    paths += [p for e in registry['editions'] if (p := route(e, phase)) is not None]
    return sorted(set(paths))


def sitemap(registry: dict, base: str, phase: str = 'current') -> str:
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    lines += ['  <url><loc>' + html.escape(url(base, p)) + '</loc></url>' for p in indexable_paths(registry, phase)]
    return '\n'.join(lines + ['</urlset>', ''])


def shell(registry: dict, base: str, current: str | None, phase: str = 'current') -> str:
    """Native details/links work with no JS; namespaced controls avoid local IDs."""
    esc = html.escape
    selected = next((e for e in registry['editions'] if e['edition_id'] == current), None)
    label = 'Estados e cargos' if selected is None else f"{selected['state']} · {selected['office_label']}"
    blocks = []
    for s in hub_data(registry, phase):
        heading = esc(s['name'])
        if phase == 'next' or s['published']:
            heading = f'<a href="{esc(url(base,s["path"]))}">{heading}</a>'
        items = []
        for e in s['editions']:
            if e['href'] is None:
                items.append(f'<li><span>{esc(e["office_label"])} — em preparação</span></li>')
            else:
                active = ' aria-current="page"' if current == e['edition_id'] else ''
                items.append(f'<li><a href="{esc(url(base,e["href"]))}"{active}>{esc(e["office_label"])}</a></li>')
        blocks.append(f'<section><h3>{heading}</h3><ul>'+''.join(items)+'</ul></section>')
    crumbs = [f'<a href="{esc(url(base,"/"))}">{"Início" if phase == "next" else "Entrada atual · SC"}</a>']
    if selected:
        state = next(s for s in registry['states'] if s['code'] == selected['state'])
        crumbs += [f'<a href="{esc(url(base,state["path"]))}">{esc(state["name"])}</a>' if phase == 'next' or state['published'] else esc(state['name']), esc(selected['office_label'])]
    return '<div class="eef-global-shell"><nav aria-label="Localização" class="eef-breadcrumb">'+'<span aria-hidden="true"> / </span>'.join(crumbs)+'</nav><details class="eef-edition-menu"><summary>'+esc(label)+'</summary><div class="eef-edition-grid">'+''.join(blocks)+'</div></details></div>'


def metadata(e: dict, base: str, phase: str = 'current') -> dict:
    p = route(e, phase)
    return {'title': e['metadata']['title'], 'description': e['metadata']['description'],
            'canonical': url(base, p) if p else None, 'robots': 'index,follow' if p else 'noindex,nofollow'}


HISTORY_KEYS = ('year','cycle_year','round','election_id','election_date','election_type','candidate_id','office','place','uf','party','result','votes','votes_status','vote_status','vote_join_key','votes_source','votes_provenance','source','source_record','profile_url')
SOURCE_KEYS = ('source_id','id','url','title','label','publisher','type','source_type','source_kind','period','published_at','publication_date','consulted_at','checked_at','retrieved_at','locator','link_check','limitation')
CLAIM_KEYS = ('claim_id','item_id','text','source_ids','theme_ids','period','direction','position_target','object','nature','evidence_type','event_date','published_at','consulted_at','locator','rationale_and_locator','association_ids')


def pick(record: dict, keys: tuple) -> dict:
    return {k: copy.deepcopy(record[k]) for k in keys if k in record}


def adapt_claim(record: dict, semantic: str, *, explicitly_eligible: bool = False) -> dict:
    require(semantic in ('current_support', 'documented_topic', 'legacy_context'), 'Unknown claim semantic')
    out = pick(record, CLAIM_KEYS)
    # The review supplies eligibility; year, words, party and occupation never do.
    out['semantic'] = semantic
    out['filter_eligible'] = bool(explicitly_eligible and record.get('source_ids') and semantic != 'legacy_context')
    out['missing'] = [k for k in ('period', 'direction', 'nature', 'locator') if not record.get(k)]
    return out


def adapt_candidate(record: dict, e: dict, source_path: str) -> dict:
    """Non-mutating bridge over reviewed public exports, without filling gaps."""
    cid = str(record.get('id', record.get('candidate_id', '')))
    require(bool(re.fullmatch(r'\d{12}', cid)), 'Invalid current candidate identity')
    if 'state' in record: require(record['state'] == e['state'], 'Foreign state')
    if 'election_year' in record: require(record['election_year'] == e['election_year'], 'Foreign election')
    if 'office_code' in record: require(record['office_code'] == e['office_code'], 'Foreign office')
    sources = record.get('sources', record.get('editorial_sources', []))
    out = {
        'key': e['edition_id'] + ':' + cid, 'edition_id': e['edition_id'], 'candidate_id': cid,
        'identity': pick(record, ('name','full_name','number','party','occupation','federation')),
        'registration': pick(record, ('registration_status','registration_group','registration_details','status','status_id','status_date','status_api','status_group','apt_api','profile_checked_at','status_fields','substitution_links','replaced_flag','registration_election','source_record','identity_source','tse_url')),
        'mandate': pick(record, ('current_office','current_role_observation','mandate_documented','mandate_state','mandate_label','mandate_note','mandate_source','mandate_source_kind','mandate_verification')),
        'history': [pick(h, HISTORY_KEYS) for h in record.get('history', [])],
        'research': pick(record, ('research_status','research_state','research_date','review_completed_in_round','reviewed_at','documentation_note','gap_review_scope','source_limitation','limitations')),
        'context': pick(record, ('pautas','topics','topics_source','topics_kind','topics_material_date','topics_review_status','biography','biography_source','biography_sources','summary_kind','official_summary','region','themes','themes_2026','sources_and_context')),
        'sources': [({'url': s} if isinstance(s, str) else pick(s, SOURCE_KEYS)) for s in sources],
        'claims': [adapt_claim(c, 'documented_topic', explicitly_eligible=bool(c.get('source_ids')))
                   for c in record.get('claims_2026', [])] +
                  [adapt_claim(c, 'legacy_context') for c in record.get('claims_other', [])],
        'corrections': copy.deepcopy(record.get('corrections', [])),
        'provenance': {'path': source_path, 'source_id': cid, 'adapter_version': '1.0.0'},
    }
    # SC semantic-v2 sections retain their original grouping. No promotional mapping.
    if 'sections' in record:
        out['context']['sections'] = copy.deepcopy(record['sections'])
    return out

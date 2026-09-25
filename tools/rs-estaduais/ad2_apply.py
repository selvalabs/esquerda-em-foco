"""Apply A-D.2 reviewed evidence; no scraping, inference or network writes here.

A named search is a first pass, not exhaustive research. Past registration state
never replaces 2026 registration state. A national vote has its own provenance;
it never overwrites the source object for the RS subset of the same election.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais/ad2'
CUTOFF='2026-09-21'
CODES={'presidente':'1','governador':'3','senador':'5','deputado federal':'6','deputado estadual':'7','prefeito':'11','vereador':'13'}

def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def helpers():
    spec=importlib.util.spec_from_file_location('ad2_reviewed_merge',ROOT/'tools/rs-estaduais/phase2_apply.py')
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def row_key(cid,h):return ':'.join([cid,str(h['year']),str(h['candidate_id']),str(h['round'])])

def vote_key(record,turn):
    t=record['target']
    return ':'.join([str(record['year']),str(t['candidate_id']),str(turn),str(t['unit'])])

def apply_vote_evidence(history,evidence,identities,prior_helper):
    indexed={}
    for record in evidence:
        t=record['target'];cid=t['current_candidate_id'];year=int(record['year'])
        if not record.get('read') or year>=2026 or cid not in identities:
            raise ValueError('Unverified, current or unknown electoral evidence')
        prior_helper.valid_date(record['checked_at'])
        if urlsplit(record['source_url']).hostname!='cdn.tse.jus.br':raise ValueError('Official TSE vote source required')
        if not re.fullmatch('[a-f0-9]{64}',record.get('member_sha256','')) or not re.fullmatch('[a-f0-9]{8}',record.get('member_crc32','')):
            raise ValueError('Complete member integrity evidence missing')
        if record.get('archive_sha256') is not None:raise ValueError('These range transfers do not hash the complete archive')
        if prior_helper.norm(t['name'])!=prior_helper.norm(identities[cid]['NM_CANDIDATO']):raise ValueError('Civil identity mismatch')
        matches=[h for h in history[cid] if int(h['year'])==year and str(h['candidate_id'])==str(t['candidate_id'])]
        if len(matches)!=1 or len(record['totals'])!=1:raise ValueError('Historical row/turn is ambiguous')
        h=matches[0];turn=next(iter(record['totals']));ctx=record['contexts'][turn]
        if CODES.get(prior_helper.norm(h.get('office')))!=t['office']:raise ValueError('Historical office mismatch')
        expected={'candidate_id':str(t['candidate_id']),'year':year,'round':int(turn),'office_code':t['office'],'electoral_unit':t['unit'],'ballot_number':t['number'],'civil_name':t['name']}
        for key,value in expected.items():
            actual=ctx.get(key)
            if key=='civil_name':actual=prior_helper.norm(actual);value=prior_helper.norm(value)
            if actual!=value:raise ValueError('Vote context mismatch: '+key)
        if t.get('round') is not None and int(t['round'])!=int(turn):raise ValueError('Unexpected turn')
        if t.get('election_code') and str(t['election_code'])!=str(ctx['election_code']):raise ValueError('Wrong election code')
        if not h.get('round_note') and int(h['round'])!=int(turn):raise ValueError('Linked turn differs from source')
        if t['unit']=='BR':
            if t['office']!='1' or not record['member'].upper().endswith('_BR.CSV'):
                raise ValueError('Presidential national source must not be replaced by RS')
            if h.get('uf') not in (None,'','BR'):raise ValueError('Unexpected prior presidential population')
            h['uf']='BR';h['place']='BRASIL';h['electoral_unit']='BR'
        elif t['unit']=='RS':
            if h.get('uf')!='RS' or not record['member'].upper().endswith('_RS.CSV'):raise ValueError('Wrong state source member')
        else:raise ValueError('Unsupported population')
        amount=record['totals'][turn]
        if type(amount) is not int or amount<0 or record['rows_per_total'].get(turn,0)<1:raise ValueError('Invalid nominal total or empty match')
        if h.get('votes') is not None and h['votes']!=amount:raise ValueError('Existing nominal total conflict')
        if h.get('round_note'):h['prior_source_round_note']=h.pop('round_note')
        key=vote_key(record,turn)
        h.update({'round':int(turn),'votes':amount,'votes_status':'verified_nominal','votes_source':record['source_url'],'votes_evidence_id':key,'votes_population':ctx['population'],'votes_electoral_unit':t['unit'],'votes_election_code':ctx['election_code'],'votes_source_generated_at':record.get('generation'),'votes_checked_at':record['checked_at'],'round_confirmed_by':'Exact unique row context in official nominal-vote table'})
        indexed[key]={'current_candidate_id':cid,'context':ctx,'votes':amount,'source_url':record['source_url'],'member':record['member'],'member_sha256':record['member_sha256'],'member_crc32':record['member_crc32'],'archive_sha256':None,'checked_at':record['checked_at'],'rows_per_total':record['rows_per_total'][turn]}
    return indexed

def apply_past_status(history,records,identities,prior_helper):
    checked=[]
    for record in records:
        cid=record['current_candidate_id'];year=int(record['year']);old_id=str(record['historical_id'])
        if year>=2026 or cid not in identities or record.get('vote_total_verified_by_this_record') is not False:
            raise ValueError('Past status must not be a current record or nominal total')
        prior_helper.valid_date(record['checked_at'])
        parts=urlsplit(record['source_url'])
        match=re.search(r'/buscar/(\d+)/([^/]+)/(\d+)/candidato/(\d+)$',parts.path)
        if parts.hostname!='divulgacandcontas.tse.jus.br' or not match or int(match[1])!=year or match[4]!=old_id:
            raise ValueError('Past status URL identity mismatch')
        if prior_helper.norm(record['civil_name'])!=prior_helper.norm(identities[cid]['NM_CANDIDATO']):raise ValueError('Past status civil name mismatch')
        matches=[h for h in history[cid] if int(h['year'])==year and str(h['candidate_id'])==old_id]
        if len(matches)!=1:raise ValueError('Past status linkage is ambiguous')
        h=matches[0]
        if CODES.get(prior_helper.norm(h.get('office')))!=record['office_code']:raise ValueError('Past status office mismatch')
        old_unit=h.get('electoral_unit')
        if old_unit and str(old_unit)!=match[2]:raise ValueError('Past status electoral unit mismatch')
        h['historical_registration_review']={k:v for k,v in record.items() if k not in ('current_candidate_id','civil_name')}
        h['historical_registration_review']['scope_note']='Situação referente apenas à disputa histórica indicada, consultada em 21/09/2026; não substitui o registro de 2026 e não comprova total nominal.'
        checked.append({'current_candidate_id':cid,'historical_id':old_id,'year':year,'source_url':record['source_url'],'registration_status':record.get('registration_status'),'nominal_total_still_unresolved':h.get('votes') is None})
    return checked

def make_ledger(searches,patches,offices,source_checks,identities):
    entries={}
    for cid,queries in searches['queries'].items():
        if cid not in identities or not queries:raise ValueError('Unknown or unsearched candidate in research log')
        c=identities[cid]
        entries[cid]={'candidate_id':cid,'name':c['NM_URNA_CANDIDATO'],'number':c['NR_CANDIDATO'],'party':c['SG_PARTIDO'],'checked_at':CUTOFF,'searches':[{'query':q,'execution_reference':ref} for q,ref in queries],'exhaustive':False,'accepted_sources':patches.get(cid,{}).get('sources',[]),'source_checks':[],'current_office_source':offices.get(cid,{}).get('source'),'status':'summary_supported' if patches.get(cid,{}).get('pautas') else 'institutional_act_only' if patches.get(cid,{}).get('activities_append') else 'nominal_search_done_deeper_research_pending'}
    for item in source_checks.get('checks',[]):
        if item['candidate_id'] in entries:entries[item['candidate_id']]['source_checks'].append(item)
    attempts=source_checks.get('municipal_api_attempts',{})
    for item in attempts.get('sources',[]):
        if item['candidate_id'] in entries:
            for resource in item['resources']:
                entries[item['candidate_id']]['source_checks'].append({'method':'institutional_api','url':item['base']+resource,'outcome':'Timeout; conteúdo não lido e mandato não confirmado.','checked_at':attempts['checked_at']})
    return list(entries.values())

def run():
    prior=helpers()
    searches=load(D/'ad2-searches.json');patches=load(D/'ad2-editorial.json');office_patches=load(D/'ad2-offices.json')
    identities={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json')}
    editorial=load(D/'editorial.json',{});offices=load(D/'offices-verified.json',{});history=load(D/'history-normalized.json',{})
    baseline_path=A/'baseline.json'
    if not baseline_path.exists():
        missing={cid for cid in identities if not editorial.get(cid,{}).get('pautas')}
        if len(identities)!=searches['baseline_candidates'] or set(searches['queries'])!=missing:
            raise ValueError('The current cohort changed; reconcile the baseline before applying evidence')
        old_votes={row_key(cid,h):h['votes'] for cid,rows in history.items() for h in rows if h['year']<2026 and h.get('votes') is not None}
        baseline={'source_commit':searches['baseline_commit'],'candidate_ids':sorted(identities),'gap_ids':sorted(missing),'policy_summaries':{cid:e['pautas'] for cid,e in editorial.items() if e.get('pautas')},'offices':copy.deepcopy(offices),'verified_votes':old_votes,'counts':{'candidates':len(identities),'policy_summaries':sum(bool(e.get('pautas')) for e in editorial.values()),'policy_gaps':len(missing),'current_offices':len(offices),'with_activity':sum(bool(e.get('activities')) for e in editorial.values()),'historical_vote_rows':len(old_votes)},'scope_note':'Canonical scope correction to 149 records predates A-D.2 and is preserved.'}
        save(baseline_path,baseline)
    baseline=load(baseline_path)
    if set(identities)!=set(baseline['candidate_ids']) or set(searches['queries'])!=set(baseline['gap_ids']):raise ValueError('Research cohort drift')
    check=prior.apply(editorial,offices,patches,office_patches,identities)
    checked_statuses=apply_past_status(history,load(D/'ad2-historical-status.json'),identities,prior)
    vote_index=apply_vote_evidence(history,load(D/'ad2-votes.json'),identities,prior)
    for cid,text in baseline['policy_summaries'].items():
        if editorial[cid]['pautas']!=text:raise ValueError('Earlier summary altered')
    for cid,office in baseline['offices'].items():
        if offices[cid]!=office:raise ValueError('Earlier office evidence altered')
    after_votes={row_key(cid,h):h['votes'] for cid,rows in history.items() for h in rows if h['year']<2026 and h.get('votes') is not None}
    if any(after_votes.get(k)!=v for k,v in baseline['verified_votes'].items()):raise ValueError('Earlier historical total changed')
    ledger=make_ledger(searches,patches,office_patches,load(D/'ad2-source-checks.json'),identities)
    save(D/'editorial.json',editorial);save(D/'offices-verified.json',offices);save(D/'history-normalized.json',history)
    save(D/'ad2-research-ledger.json',ledger);save(D/'ad2-vote-index.json',vote_index)
    save(A/'applied.json',{'cutoff':CUTOFF,'baseline':baseline['counts'],'candidates':len(identities),'nominal_searches_candidates':len(ledger),'new_summary_inputs':sum(bool(p.get('pautas')) for p in patches.values()),'editorial_evidence_candidates':len(check),'new_office_inputs':len(office_patches),'historical_statuses_reviewed':len(checked_statuses),'nominal_totals_added':len(vote_index),'earlier_summaries_offices_votes_preserved':True,'all_gaps_exhaustively_researched':False,'historical_status_checks':checked_statuses,'input_sha256':{p.name:digest(p) for p in [D/'ad2-searches.json',D/'ad2-editorial.json',D/'ad2-offices.json',D/'ad2-source-checks.json',D/'ad2-votes.json',D/'ad2-historical-status.json']}})
    print(json.dumps({'candidates':len(identities),'summaries':sum(bool(e.get('pautas')) for e in editorial.values()),'offices':len(offices),'historical_vote_rows':len(after_votes),'nominal_searches':len(ledger)},ensure_ascii=False))

if __name__=='__main__':run()

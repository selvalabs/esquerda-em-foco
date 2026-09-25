"""Apply source-reviewed A-C batches by exact TSE identity, preserving prior work.
No automatic synthesis, party inference, implicit mandate or silent overwrite.
"""
from __future__ import annotations
import hashlib,json,unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais/phase2';CUTOFF=date(2026,9,21)
def load(path,default):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(value):return ' '.join(''.join(c for c in unicodedata.normalize('NFD',str(value).casefold()) if unicodedata.category(c)!='Mn').split())
def valid_date(value):
    parsed=date.fromisoformat(str(value)[:10])
    if parsed>CUTOFF:raise ValueError('Source/date beyond declared cutoff: '+str(value))
    return parsed
def valid_url(value):
    parts=urlsplit(str(value))
    if parts.scheme not in ('http','https') or not parts.hostname or parts.username or parts.password:raise ValueError('Invalid public source URL')
    return value
def merge_unique(existing,incoming):
    tokens={json.dumps(item,sort_keys=True,ensure_ascii=False) for item in existing}
    for item in incoming:
        token=json.dumps(item,sort_keys=True,ensure_ascii=False)
        if token not in tokens:existing.append(item);tokens.add(token)
def batches(prefix):
    result={};paths=sorted(D.glob(prefix+'*.json'))
    for path in paths:
        for cid,patch in load(path,{}).items():
            target=result.setdefault(cid,{})
            for key,value in patch.items():
                if key in ('sources','activities_append'):
                    merge_unique(target.setdefault(key,[]),value)
                elif key in target and target[key]!=value:
                    raise ValueError('Contradictory batch input: '+cid+' '+key)
                else:target[key]=value
    return result,paths

def apply(editorial,offices,patches,office_patches,identities):
    checks=[]
    for cid,patch in patches.items():
        if cid not in identities or norm(patch.get('expected_name',''))!=norm(identities[cid]['NM_URNA_CANDIDATO']):raise ValueError('Current TSE identity mismatch: '+cid)
        if patch.get('reviewed') is not True or not patch.get('sources'):raise ValueError('Editorial input has not been reviewed: '+cid)
        valid_date(patch['checked_at'])
        for source in patch['sources']:
            valid_url(source['url'])
            if not source.get('locator') or not source.get('type'):raise ValueError('Missing source locator/type')
            valid_date(source.get('checked_at',patch['checked_at']))
            if source.get('published_at'):valid_date(source['published_at'])
        target=editorial.setdefault(cid,{})
        for field in ('pautas','biography'):
            if patch.get(field):
                if target.get(field) and target[field]!=patch[field]:raise ValueError('Conflicting reviewed '+field+': '+cid)
                target[field]=patch[field]
        if patch.get('pautas'):
            if patch.get('pautas_type') not in ('candidate_declaration','institutional_record'):raise ValueError('Unknown policy evidence type')
            target['pautas_type']=patch['pautas_type']
        for activity in patch.get('activities_append',[]):
            valid_url(activity['source']);host=urlsplit(activity['source']).hostname or ''
            if not host.endswith(('.gov.br','.leg.br')):raise ValueError('An institutional primary source is required for acts')
            if not activity.get('text') or not activity.get('kind'):raise ValueError('Incomplete act description')
            if not activity.get('date'):raise ValueError('New phase2 acts require an explicit date')
            valid_date(activity['date'])
        merge_unique(target.setdefault('sources',[]),patch['sources']);merge_unique(target.setdefault('activities',[]),patch.get('activities_append',[]))
        target['reviewed']=True;target['checked_at']=patch['checked_at']
        checks.append({'candidate_id':cid,'name':patch['expected_name'],'identity_match':True,'policy_summary_input':bool(patch.get('pautas')),'act_inputs':len(patch.get('activities_append',[])),'source_urls':list(dict.fromkeys(s['url'] for s in patch['sources']))})
    for cid,patch in office_patches.items():
        if cid not in identities or norm(patch.get('expected_name',''))!=norm(identities[cid]['NM_URNA_CANDIDATO']):raise ValueError('Office identity mismatch: '+cid)
        valid_date(patch['checked_at']);valid_url(patch['source'])
        if not (urlsplit(patch['source']).hostname or '').endswith(('.gov.br','.leg.br')):raise ValueError('Current office requires institutional source')
        if patch.get('verification') not in ('current_directory','current_individual_profile'):raise ValueError('Current institutional evidence required')
        if not patch.get('detail') or not patch.get('label'):raise ValueError('Incomplete office')
        value={k:v for k,v in patch.items() if k!='expected_name'}
        if cid in offices and offices[cid]!=value:raise ValueError('Existing office conflict; resolve explicitly: '+cid)
        offices[cid]=value
    return checks

def run():
    patches,epaths=batches('phase2-editorial');office_patches,opaths=batches('phase2-offices')
    editorial=load(D/'editorial.json',{});offices=load(D/'offices-verified.json',{})
    identities={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json',[])}
    checks=apply(editorial,offices,patches,office_patches,identities)
    save(D/'editorial.json',editorial);save(D/'offices-verified.json',offices)
    ledger=load(D/'phase2-research-ledger.json',{})
    for row in checks:
        cid=row['candidate_id'];ledger[cid]={**ledger.get(cid,{}),'candidate_id':cid,'name':row['name'],'status':'individual_evidence_reviewed','new_policy_summary_input':row['policy_summary_input'],'new_act_inputs':row['act_inputs'],'source_urls':row['source_urls'],'checked_at':'2026-09-21'}
    for cid,patch in office_patches.items():
        row=ledger.setdefault(cid,{'candidate_id':cid,'name':patch['expected_name'],'status':'current_office_source_reviewed','checked_at':'2026-09-21'});row['office_source']=patch['source']
    save(D/'phase2-research-ledger.json',ledger)
    report={'cutoff':'2026-09-21','editorial_inputs':len(patches),'policy_summary_inputs':sum(bool(p.get('pautas')) for p in patches.values()),'new_current_office_inputs':len(office_patches),'total_policy_summaries':sum(bool(e.get('pautas')) for e in editorial.values()),'total_act_candidates':sum(bool(e.get('activities')) for e in editorial.values()),'total_current_offices':len(offices),'individual_checks':checks,'input_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in epaths+opaths},'note':'A reviewed record does not imply an exhaustive search of every unresolved candidature. Dated actions, declarations and current-office confirmations remain separate.'}
    save(A/'applied.json',report);print(json.dumps({k:v for k,v in report.items() if k!='individual_checks'},ensure_ascii=False,indent=2))
if __name__=='__main__':run()

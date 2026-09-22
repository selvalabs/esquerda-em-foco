"""Freeze previous read-only artifacts as sanitized, versioned evidence metadata.
Only api.github.com receives the job token; artifact redirects carry no token.
Raw campaign text stays transient. Availability is not editorial validation.
"""
from __future__ import annotations
import hashlib, io, json, os, re, subprocess, urllib.error, urllib.request, zipfile
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[2];I=ROOT/'data/rs-estaduais/ad3';A=ROOT/'docs/rs-estaduais/ad3'
ARTIFACTS=[(10695576078,'538fc705da36ed71eade22028b76d1fd62af31922b1a0969a66be7602a37b8fc','sources.json','source-access.json'),(10696431450,'a10e028e96364484a0e952d0e0bb0bc1bbc77962b1b33d4708bbaceae5164926','follow.json','follow-source-audit.json')]
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(p):return json.loads(p.read_text(encoding='utf-8'))
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None

def download(aid,expected,member):
    token=os.environ.get('GH_TOKEN')
    if not token:raise ValueError('GitHub job token required only for first artifact freeze')
    url=f'https://api.github.com/repos/selvalabs/esquerda-em-foco/actions/artifacts/{aid}/zip'
    request=urllib.request.Request(url,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','User-Agent':'esquerda-em-foco-ad3-audit'})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request,timeout=30) as response:raw=response.read(10_000_001)
    except urllib.error.HTTPError as exc:
        if exc.code not in (301,302,303,307,308):raise
        target=exc.headers.get('Location','');p=urlsplit(target)
        if p.scheme!='https' or not p.hostname or not p.hostname.endswith(('.blob.core.windows.net','.githubusercontent.com','.actions.githubusercontent.com')):raise ValueError('Unexpected artifact redirect host')
        with urllib.request.urlopen(urllib.request.Request(target,headers={'User-Agent':'esquerda-em-foco-ad3-audit'}),timeout=30) as response:raw=response.read(10_000_001)
    if len(raw)>10_000_000 or hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Artifact size/digest mismatch')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        if z.getinfo(member).file_size>3_000_000:raise ValueError('Oversized artifact JSON')
        return json.loads(z.read(member))

def sanitize(row):
    clean={k:v for k,v in row.items() if k not in ('review_text','links','relevant_links')}
    text=row.get('review_text','')
    if re.search(r'not a robot|não é um robô|security verification|not a bot',text,re.I):
        clean.update({'read':False,'outcome':'access_interstitial','manual_classification_correction':True})
    clean['editorial_verified']=False
    return clean

def run():
    I.mkdir(parents=True,exist_ok=True);A.mkdir(parents=True,exist_ok=True)
    for aid,checksum,member,output in ARTIFACTS:
        if (I/output).exists():continue
        raw=download(aid,checksum,member)
        save(I/output,{'artifact_id':aid,'artifact_sha256':checksum,'sources':[sanitize(r) for r in raw['sources']],'note':'Disponibilidade e corpo recuperável não comprovam programa. Nenhum texto integral de campanha foi exportado.'})
        if member=='follow.json':
            historical=[]
            for item in raw['historical']:
                row={k:v for k,v in item.items() if k!='available_top_level_keys'}
                row.update({'nominal_total_verified':False,'decision':'registration_revalidated_nominal_total_still_pending','reason':'Cadastro histórico identifica a disputa, mas não fornece total nominal verificável. Indeferimento ou renúncia não viram zero.'});historical.append(row)
            save(I/'historical-follow-up.json',{'checked_at':'2026-09-22','records':historical,'new_nominal_totals':0,'nominal_investigation_complete':False,'scope_note':'Onze perfis históricos relidos. Ainda é necessária fonte nominal compatível; não houve nova leitura integral das tabelas nominais para todas as pendências.'})
    queries=load(I/'queries.json');patches=load(I/'editorial.json')
    before=json.loads(subprocess.check_output(['git','show','b9ec0c352cdc0dc2a77be8ea4cf28469f1c09502:data/rs-estaduais/normalized.json'],cwd=ROOT))['candidates']
    missing={c['id']:c for c in before if not c['pautas']}
    if set(queries)!=set(missing):raise ValueError('Query identities do not match the 88-item baseline queue')
    ledger={}
    for index,(cid,qs) in enumerate(queries.items()):
        c=missing[cid];checks=[]
        for source in load(I/'source-access.json')['sources']+load(I/'follow-source-audit.json')['sources']:
            ids=source.get('candidate_ids',[source.get('candidate_id')])
            if cid in ids:checks.append({k:source[k] for k in ('url','checked_at','outcome','read','raw_sha256','rendered_sha256') if k in source})
        if cid in patches:
            for s in patches[cid]['sources']:checks.append({'url':s['url'],'checked_at':s['checked_at'],'locator':s['locator'],'identity_basis':s['identity_basis'],'method':s.get('read_method'),'decision':'supports_individual_summary'})
        ledger[cid]={'candidate_id':cid,'expected_name':c['official_name'],'party':c['party'],'batch':1+index//12,'review_completed_in_round':cid in patches,'queries':[{'query':q,'performed_on':'2026-09-22','method':'web_search','result_review':'Search results examined; not equivalent to full-source reading'} for q in qs],'source_checks':checks,'decision':'policy_summary_verified' if cid in patches else 'research_pending','notes':['Investigações sem fonte individual suficiente continuam parciais; nenhuma alegação de exaustividade.']}
    for note in load(I/'manual-follow-up.json'):
        if note['candidate_id'] in ledger:ledger[note['candidate_id']]['source_checks'].append(note)
    save(I/'research-ledger.json',ledger)
    save(A/'source-freeze.json',{'artifact_ids':[x[0] for x in ARTIFACTS],'decoded_metadata_versioned':True,'contains_raw_campaign_text':False,'performed_queries':sum(len(q) for q in queries.values()),'source_retrieval_is_not_editorial_completion':True})
    print(json.dumps({'queue':len(ledger),'performed_queries':sum(len(q) for q in queries.values())}))
if __name__=='__main__':run()

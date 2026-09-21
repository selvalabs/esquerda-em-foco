"""Audit the canonical 2026 party scope against official TSE data and current project editions."""
from __future__ import annotations
import collections, csv, hashlib, io, json, subprocess, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
CONFIG=json.loads((ROOT/'config/party-scope-2026.json').read_text())
PARTIES=CONFIG['parties']
PARTY_UPPER={p.upper():p for p in PARTIES}
OFFICES=CONFIG['offices']
STATES=('SC','RS','PR')
URL='https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip'
OUT=ROOT/'docs/methodology/party-scope-audit.json'

def now(): return datetime.now(timezone.utc).isoformat()
def download(url):
    errors=[]
    for n in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'EsquerdaEmFoco/1.0 scope audit','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=120) as r: raw=r.read()
            if not raw: raise ValueError('empty response')
            return raw
        except Exception as e:
            errors.append(str(e)); time.sleep(n+1)
    raise RuntimeError('; '.join(errors))
def decode(blob):
    try:return blob.decode('utf-8-sig')
    except UnicodeDecodeError:return blob.decode('latin-1')
def count_party(rows):
    c=collections.Counter(r['party'] for r in rows)
    return {p:c.get(p,0) for p in PARTIES}
def normalize_party(v):
    return PARTY_UPPER.get(str(v or '').upper(),str(v or ''))
def normalize_project(items):
    result=[]
    for x in items:
        cid=str(x.get('id') or x.get('SQ_CANDIDATO') or x.get('tse_id') or x.get('sq_candidato') or '')
        party=normalize_party(x.get('party') or x.get('SG_PARTIDO') or x.get('partido') or x.get('sigla_partido'))
        office=str(x.get('office_code') or x.get('CD_CARGO') or x.get('cargo_codigo') or '')
        if cid and party: result.append({'id':cid,'party':party,'office':office})
    return result
def from_sc_federal():
    soup=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
    out=[]
    for node in soup.select('article.candidate'):
        cid=str(node.get('data-tse-id') or '').strip()
        party=normalize_party(node.get('data-party'))
        if cid and party: out.append({'id':cid,'party':party,'office':'6'})
    return out
def from_json(path, default_office):
    data=json.loads(path.read_text())
    items=data if isinstance(data,list) else data.get('candidates') or data.get('candidaturas') or []
    out=normalize_project(items)
    for x in out:
        if not x['office']:x['office']=default_office
    return out
def git_json(ref,path,default_office):
    raw=subprocess.check_output(['git','show',f'{ref}:{path}'])
    data=json.loads(raw)
    items=data if isinstance(data,list) else data.get('candidates') or []
    out=normalize_project(items)
    for x in out:
        if not x['office']:x['office']=default_office
    return out

PROJECT={
 ('SC','6'):('main:index.html',from_sc_federal),
 ('SC','7'):('main:deputados-estaduais/data/candidaturas.json',lambda:from_json(ROOT/'deputados-estaduais/data/candidaturas.json','7')),
 ('RS','6'):('main:data/rs/normalized.json',lambda:from_json(ROOT/'data/rs/normalized.json','6')),
 ('RS','7'):('origin/feat/rs-deputados-estaduais:data/rs-estaduais/candidates-official.json',lambda:git_json('origin/feat/rs-deputados-estaduais','data/rs-estaduais/candidates-official.json','7')),
 ('PR','6'):('main:data/pr/normalized.json',lambda:[x for x in from_json(ROOT/'data/pr/normalized.json','') if x['office']=='6']),
 ('PR','7'):('main:data/pr/normalized.json',lambda:[x for x in from_json(ROOT/'data/pr/normalized.json','') if x['office']=='7']),
}

def main():
    raw=download(URL);archive=zipfile.ZipFile(io.BytesIO(raw))
    report={
      'schema_version':1,'generated_at':now(),'source':{
        'url':URL,'sha256':hashlib.sha256(raw).hexdigest()
      },'canonical_scope':CONFIG,'states':{},'summary':{}
    }
    total_missing=total_extra=0
    for uf in STATES:
        names=[n for n in archive.namelist() if n.upper().endswith(f'_{uf}.CSV')]
        assert len(names)==1,(uf,names)
        blob=archive.read(names[0]);rows=list(csv.DictReader(io.StringIO(decode(blob)),delimiter=';'))
        report['states'][uf]={'source_member':names[0],'member_sha256':hashlib.sha256(blob).hexdigest(),'offices':{}}
        for code in OFFICES:
            official=[]
            for r in rows:
                if r.get('SG_UF')!=uf or r.get('ANO_ELEICAO')!='2026' or r.get('CD_CARGO')!=code:continue
                p=PARTY_UPPER.get(r.get('SG_PARTIDO','').upper())
                if p:official.append({'id':r['SQ_CANDIDATO'],'party':p,'status':r.get('DS_SITUACAO_CANDIDATURA'),'name':r.get('NM_URNA_CANDIDATO')})
            source,loader=PROJECT[(uf,code)]
            project=[x for x in loader() if x['party'] in PARTIES]
            official_ids={x['id'] for x in official};project_ids={x['id'] for x in project}
            missing=sorted(official_ids-project_ids);extra=sorted(project_ids-official_ids)
            off_by={x['id']:x for x in official};proj_by={x['id']:x for x in project}
            result={
              'official_canonical_total':len(official),
              'official_by_party':count_party(official),
              'project_total':len(project),
              'project_by_party':count_party(project),
              'project_source':source,
              'missing_total':len(missing),
              'extra_total':len(extra),
              'missing':[off_by[i] for i in missing],
              'extra':[proj_by[i] for i in extra],
              'aligned':not missing and not extra
            }
            report['states'][uf]['offices'][code]=result
            total_missing+=len(missing);total_extra+=len(extra)
    report['summary']={
      'combinations':6,
      'aligned_combinations':sum(v['aligned'] for s in report['states'].values() for v in s['offices'].values()),
      'missing_records':total_missing,'extra_records':total_extra,
      'all_aligned':total_missing==0 and total_extra==0
    }
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report['summary'],ensure_ascii=False,indent=2))
    for uf,state in report['states'].items():
      for code,item in state['offices'].items():
        print(uf,code,'official',item['official_canonical_total'],'project',item['project_total'],'missing',item['missing_total'],'extra',item['extra_total'])
if __name__=='__main__':main()

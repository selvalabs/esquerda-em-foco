#!/usr/bin/env python3
"""Reconcile votes by person AND electoral context; never by name alone."""
from __future__ import annotations
import csv, io, json, re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from http_archive import archive
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'audit/review2'
BASE='https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def num(v):
 try:return str(int(v))
 except (TypeError,ValueError):return str(v or '').strip()
def pick(r,*keys):return next((r[k] for k in keys if k in r),'')
def date_iso(value):
 s=str(value or '').strip()
 for fmt in ('%Y-%m-%d','%d/%m/%Y'):
  try:return datetime.strptime(s[:10],fmt).date().isoformat()
  except ValueError:pass
 return None

def identity(r,year=None):
 cargo=num(pick(r,'CD_CARGO','CODIGO_CARGO'));uf=pick(r,'SG_UF','SIGLA_UF') or 'SC'
 # 2010 municipality-zone files put the counting municipality in SG_UE even
 # for statewide offices. The electorate for those offices is the whole UF.
 unit=uf if cargo in ('3','4','5','6','7','8','9','10') else num(pick(r,'SG_UE','CODIGO_UE'))
 return (num(year or pick(r,'ANO_ELEICAO')),unit,cargo,num(pick(r,'NR_CANDIDATO','NUMERO_CANDIDATO')),num(pick(r,'NR_TURNO','NUM_TURNO')))
def vote_key(r):return ':'.join(str(r[k]) for k in ['ANO_ELEICAO','SQ_CANDIDATO','NR_TURNO','SG_UE','CD_CARGO','NR_CANDIDATO','CD_ELEICAO'])
def legacy_key(r):
 return f"{r['ANO_ELEICAO']}:chapa:{r['SG_UE']}:{r['NR_CANDIDATO']}:{r['NR_TURNO']}" if r['CD_CARGO'] in ['4','12'] else f"{r['ANO_ELEICAO']}:{r['SQ_CANDIDATO']}:{r['NR_TURNO']}"
def same_election(row,target):
 # Legacy IDs are not shared between the history and votes archives:
 # 2004: history 6 / votes 200412; 2006: history 7 / votes 2006001.
 # 2022 history also retains first-round election ID on linked vice records.
 # The actual date, election type and round disambiguate without aliases.
 a,b=date_iso(row.get('DT_ELEICAO')),date_iso(target.get('DT_ELEICAO'))
 if not a or not b or a!=b:return False
 a,b=row.get('CD_TIPO_ELEICAO'),target.get('CD_TIPO_ELEICAO')
 if a not in (None,'','-1','-3') and b not in (None,'','-1','-3') and num(a)!=num(b):return False
 return True

def main():
 grouped=defaultdict(dict)
 for r in load(OUT/'snapshot/historico-sc-2026.json'):
  if int(r['ANO_ELEICAO'])<2026:grouped[r['ANO_ELEICAO']][vote_key(r)]=r
 old=load(ROOT/'data/votos-historicos.json')
 def collect_year(item):
  year,targets=item;url=BASE+f'votacao_candidato_munzona_{year}.zip';found={};by_context=defaultdict(list);candidate_ids={num(r['SQ_CANDIDATO']) for r in targets.values()};samples=[]
  for k,r in targets.items():
   ident=list(identity(r));ticket=r['CD_CARGO'] in ['4','12']
   if ticket:ident[2]='3' if r['CD_CARGO']=='4' else '11'
   by_context[tuple(ident)].append((k,r,ticket))
  meta={'url':url,'year':year,'target_elections':len(targets),'read_complete':False}
  try:
   z,m=archive(url);meta.update(m)
   with z:
    names=[n for n in z.namelist() if re.search(r'_SC\.csv$',n,re.I)]
    if len(names)!=1:raise ValueError('Expected one SC member')
    meta['member']=names[0]
    with z.open(names[0]) as f:
     reader=csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';');meta['columns']=reader.fieldnames;consumed=0
     for row in reader:
      consumed+=1
      if pick(row,'SG_UF','SIGLA_UF') not in ('','SC'):continue
      sid=pick(row,'SQ_CANDIDATO','SEQUENCIAL_CANDIDATO');matches=by_context.get(identity(row,year),[])
      if num(sid) in candidate_ids and len(samples)<12:
       sample={k:row.get(k) for k in ['SG_UF','SG_UE','CD_CARGO','NR_CANDIDATO','NR_TURNO','SQ_CANDIDATO','CD_ELEICAO','CD_TIPO_ELEICAO','DT_ELEICAO']}
       if sample not in samples:samples.append(sample)
      for k,target,ticket in matches:
       if not same_election(row,target):continue
       if not ticket and num(sid)!=num(target['SQ_CANDIDATO']):continue
       amount=pick(row,'QT_VOTOS_NOMINAIS','QTDE_VOTOS')
       if not re.fullmatch(r'\d+',str(amount)):raise ValueError('Non-integer vote count')
       if k not in found:found[k]={'year':year,'candidate_id':target['SQ_CANDIDATO'],'source_candidate_id':sid,'round':target['NR_TURNO'],'electoral_unit':target['SG_UE'],'office_code':target['CD_CARGO'],'number':target['NR_CANDIDATO'],'election_id':target['CD_ELEICAO'],'source_election_id':row.get('CD_ELEICAO'),'election_date':date_iso(target['DT_ELEICAO']),'election_type':target.get('NM_TIPO_ELEICAO'),'votes':0,'rows':0,'source':url,'type':'chapa' if ticket else 'nominal','match_method':'year+UF+electoral_unit+office+number+round+actual_date+election_type+'+('ticket' if ticket else 'candidate_id')}
       found[k]['votes']+=int(amount);found[k]['rows']+=1
     meta.update(read_complete=True,source_rows=consumed,matched=len(found),join_samples=samples)
  except Exception as exc:meta['error']=str(exc)
  print('Contextual votes',year,len(found),'/',len(targets),meta.get('error','OK'),flush=True)
  return year,found,meta
 results={};sources={}
 with ThreadPoolExecutor(max_workers=3) as pool:
  for year,values,meta in pool.map(collect_year,sorted(grouped.items())):results.update(values);sources[year]=meta
 changes=[];gaps=[]
 for year,targets in sorted(grouped.items()):
  for k,r in targets.items():
   previous=(old.get(k) or old.get(legacy_key(r),{})).get('votes');now=results.get(k,{}).get('votes')
   detail={'current_id':r['SQ_CANDIDATO_ATUAL'],'historical_id':r['SQ_CANDIDATO'],'name':r.get('NM_URNA_CANDIDATO'),'year':int(year),'date':r['DT_ELEICAO'],'election_id':r['CD_ELEICAO'],'unit':r['SG_UE'],'office':r['CD_CARGO'],'number':r['NR_CANDIDATO'],'previous_votes':previous,'reconciled_votes':now}
   if now is None:gaps.append(detail)
   if previous!=now:changes.append(detail)
 report={'consulted_at':datetime.now(timezone.utc).isoformat(),'all_archives_read':all(x.get('read_complete') for x in sources.values()),'sources':sources,'targets':sum(len(x) for x in grouped.values()),'matched':len(results),'changes':changes,'gaps':gaps,'rule':'Strict contextual join by actual date and type. Missing total is null, never zero. Supplementary elections stay separate. Vice candidates receive explicitly identified ticket votes.'}
 save(OUT/'votes-contextual.json',results);save(OUT/'votes-audit.json',report)
 print(json.dumps({k:v for k,v in report.items() if k!='sources'},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

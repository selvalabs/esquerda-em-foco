#!/usr/bin/env python3
"""Fresh transactional TSE snapshot; published files remain untouched."""
from __future__ import annotations
import csv, hashlib, io, json, re, subprocess
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from http_archive import archive
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent
OUT=ROOT/'audit/review2'; STAGE=OUT/'snapshot'
BASE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
PARTIES={'PT','PCDOB','PV','PSOL','REDE','PDT','PSB','PSTU','UP','PCO'}
PRIVATE=('CPF','TITULO_ELEITOR','EMAIL','NASCIMENTO','PROCESSO','ENDERECO','TELEFONE')
SOURCES={
 'universo-sc-2026.json':BASE+'consulta_cand/consulta_cand_2026.zip',
 'historico-sc-2026.json':BASE+'historico_candidatura/historico_candidatura_2026.zip',
 'redes-sc-2026.json':BASE+'consulta_cand/rede_social_candidato_2026.zip',
 'situacao-sc-2026.json':BASE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip'}
def load(p):
 obj=json.loads(p.read_text(encoding='utf-8'))
 if p.name=='candidaturas.json' and isinstance(obj,dict):
  if not isinstance(obj.get('candidates'),list): raise ValueError('Unknown candidate schema')
  return obj['candidates']
 return obj
def save(p,obj):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def public(r): return {k:v for k,v in r.items() if not any(x in k for x in PRIVATE)}
def key(r): return r['SQ_CANDIDATO']
def main():
 STAGE.mkdir(parents=True,exist_ok=True)
 if not (OUT/'baseline.json').exists():
  paths=subprocess.check_output(['git','ls-files','-z'],cwd=REPO).decode().split('\0')
  hashes={p:digest(REPO/p) for p in paths if p and not p.startswith('deputados-estaduais/') and not p.startswith('.github/workflows/estaduais-review2')}
  save(OUT/'baseline.json',{'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=REPO).decode().strip(),'outside_state_sha256':hashes,'state_data_sha256':digest(ROOT/'data/candidaturas.json'),'profiles':load(ROOT/'data/candidaturas.json')})
 now=datetime.now(timezone.utc).isoformat()
 report={'consulted_at':now,'election_year':2026,'uf':'SC','office_code':'7','fresh_requests':True,'sources':{},'errors':[],'passed':False}
 downloaded={}; ids=set()
 try:
  for filename,url in SOURCES.items():
   z,meta=archive(url); rows=[]; generations=set()
   with z:
    names=[n for n in z.namelist() if re.search(r'_SC\.csv$',n,re.I)]
    if len(names)!=1: raise ValueError(f'Expected one SC member in {url}: {names}')
    with z.open(names[0]) as f:
     for r in csv.DictReader(io.TextIOWrapper(f,encoding='latin-1',newline=''),delimiter=';'):
      include=(r.get('SG_UF')=='SC' and r.get('CD_CARGO')=='7' and r.get('ANO_ELEICAO')=='2026') if filename.startswith('universo') else (r.get('SQ_CANDIDATO_ATUAL') or r.get('SQ_CANDIDATO')) in ids
      if include:
       rows.append(public(r)); generations.add((r.get('DT_GERACAO',''),r.get('HH_GERACAO','')))
   if filename.startswith('universo'):
    if not rows or len({key(r) for r in rows})!=len(rows): raise ValueError('Empty or duplicated official universe')
    ids={key(r) for r in rows if r['SG_PARTIDO'].upper() in PARTIES}
    if not ids: raise ValueError('Empty scope; manual review required')
   if filename.startswith('situacao') and {key(r) for r in rows}!=ids: raise ValueError('Incomplete registration join')
   downloaded[filename]=rows
   meta.update(member=names[0],matched_rows=len(rows),source_generations=[list(x) for x in sorted(generations)],fetched_at=now)
   report['sources'][filename]=meta
   print(filename,len(rows),'rows',flush=True)
  for filename,rows in downloaded.items(): save(STAGE/filename,rows)
  old={key(r):r for r in load(ROOT/'data/universo-sc-2026.json') if r['SG_PARTIDO'].upper() in PARTIES}
  new={key(r):r for r in downloaded['universo-sc-2026.json'] if r['SG_PARTIDO'].upper() in PARTIES}
  oldstatus={key(r):r for r in load(ROOT/'data/situacao-sc-2026.json')}
  newstatus={key(r):r for r in downloaded['situacao-sc-2026.json']}
  fields=['NM_URNA_CANDIDATO','NM_CANDIDATO','NR_CANDIDATO','SG_PARTIDO','NM_FEDERACAO','DS_OCUPACAO','DS_GRAU_INSTRUCAO']
  changes=[]
  for sid in sorted(old.keys() & new.keys()):
   delta={f:{'before':old[sid].get(f),'after':new[sid].get(f)} for f in fields if old[sid].get(f)!=new[sid].get(f)}
   for f in ['DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CANDIDATO_URNA','ST_SUBSTITUIDO','SQ_SUBSTITUIDO','DS_SITUACAO_CASSACAO']:
    if oldstatus.get(sid,{}).get(f)!=newstatus[sid].get(f): delta[f]={'before':oldstatus.get(sid,{}).get(f),'after':newstatus[sid].get(f)}
   if delta: changes.append({'id':sid,'name':new[sid]['NM_URNA_CANDIDATO'],'changes':delta})
  diff={'before_count':len(old),'after_count':len(new),'universe_count':len(downloaded['universo-sc-2026.json']),'retained':len(old.keys() & new.keys()),'added':[{'id':s,'name':new[s]['NM_URNA_CANDIDATO']} for s in sorted(new.keys()-old.keys())],'absent':[{'id':s,'name':old[s]['NM_URNA_CANDIDATO']} for s in sorted(old.keys()-new.keys())],'changes':changes,'registration_statuses':dict(Counter(r.get('DS_SITUACAO_JULGAMENTO','Não informado') for r in newstatus.values())),'by_party':dict(Counter(r['SG_PARTIDO'] for r in new.values()))}
  save(OUT/'tse-diff.json',diff)
  existing={p['id']:p for p in load(ROOT/'data/candidaturas.json')}; networks=defaultdict(list)
  for r in downloaded['redes-sc-2026.json']: networks[key(r)].append(r['DS_URL'])
  ordered=sorted(new.values(),key=lambda r:(r['SG_PARTIDO'],r['NM_URNA_CANDIDATO']))
  for start in range(0,len(ordered),12):
   lines=[]
   for r in ordered[start:start+12]:
    sid=key(r); p=existing.get(sid,{})
    lines.extend([f"## {sid} | {r['NM_URNA_CANDIDATO']} | {r['SG_PARTIDO']} | {r['NR_CANDIDATO']}",f"Nome: {r['NM_CANDIDATO']}; ocupação: {r['DS_OCUPACAO']}",f"Mandato anterior: {p.get('mandate_label')}; fonte: {p.get('mandate_source')}"])
    selected=[h for h in p.get('history',[]) if str(h.get('result','')).lower().startswith('eleit') or h.get('year') in (2022,2024)]
    lines.append('Histórico relevante: '+json.dumps(selected,ensure_ascii=False))
    lines.append('Canais declarados: '+' | '.join(networks[sid]))
    lines.append('Síntese anterior: '+str(p.get('topics'))+' | '+str(p.get('topics_source')))
   (OUT/f'queue-{start//12+1:02d}.md').write_text('\n\n'.join(lines)+'\n',encoding='utf-8')
  report.update(passed=True,counts={'universe':diff['universe_count'],'scope':len(new),'statuses':len(newstatus)})
  print(json.dumps(diff,ensure_ascii=False,indent=2))
 except Exception as exc:
  report['errors'].append(str(exc)); raise
 finally: save(OUT/'collection.json',report)
if __name__=='__main__': main()

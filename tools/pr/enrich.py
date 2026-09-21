"""Public-only supplementary verification. All outputs are under data/pr or docs/pr."""
from __future__ import annotations
import collections,csv,hashlib,importlib.util,io,json,re,time,urllib.parse
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from collect import DATA,DOC,ROOT,URLS,get,read,save,ziprows,now

def norm(v):
 import unicodedata
 return ''.join(c for c in unicodedata.normalize('NFD',str(v)) if not unicodedata.combining(c)).casefold().strip()

def run():
 candidates=read(DATA/'candidates-official.json',[]);ids={c['SQ_CANDIDATO'] for c in candidates}
 audit=read(DOC/'supplementary-sources.json',{'sources':{},'errors':[]})
 if 'status_extended' not in audit['sources']:
  try:
   raw=get(URLS['status']);rows,meta=ziprows(raw)
   fields={'SQ_CANDIDATO','DT_GERACAO','HH_GERACAO','ST_SUBSTITUIDO','SQ_SUBSTITUIDO','ST_CANDIDATO_INSERIDO_URNA','ST_REELEICAO','DS_SITUACAO_CANDIDATO_URNA','DS_SITUACAO_CANDIDATO_PLEITO','DS_SITUACAO_CANDIDATO_TOT','DS_SITUACAO_JULGAMENTO','DS_SITUACAO_JULGAMENTO_URNA','DS_SITUACAO_CASSACAO','DS_SITUACAO_DIPLOMA','DS_DETALHE_SITUACAO_CAND'}
   selected=[{k:v for k,v in r.items() if k in fields} for r in rows if r.get('SQ_CANDIDATO') in ids]
   assert len(selected)==len(candidates)
   save(DATA/'status-extended.json',selected);audit['sources']['status_extended']={'url':URLS['status'],'checked_at':now(),'sha256':hashlib.sha256(raw).hexdigest(),**meta}
  except Exception as e:audit['errors'].append({'stage':'status_extended','error':str(e)})
 offices=read(DATA/'offices-verified.json',{});camara=read(DATA/'camara-records.json',{})
 if not camara:
  try:
   directory='https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=PR&itens=100&ordem=ASC&ordenarPor=nome'
   raw=get(directory);listing=json.loads(raw);audit['sources']['camara_directory']={'url':directory,'checked_at':now(),'sha256':hashlib.sha256(raw).hexdigest()}
   byname={norm(c['NM_CANDIDATO']):c for c in candidates}
   for deputy in listing['dados']:
    if not any(norm(deputy['nome']) in (norm(c['NM_URNA_CANDIDATO']),norm(c['NM_CANDIDATO'])) for c in candidates):continue
    detail_raw=get(deputy['uri']);detail=json.loads(detail_raw)['dados'];c=byname.get(norm(detail.get('nomeCivil')))
    if not c:continue
    cid=c['SQ_CANDIDATO'];state=detail.get('ultimoStatus',{})
    page='https://www.camara.leg.br/deputados/'+str(deputy['id'])
    camara[cid]={'deputy_id':deputy['id'],'name':detail['nomeCivil'],'parliamentary_name':state.get('nome'),'situation':state.get('situacao'),'condition':state.get('condicaoEleitoral'),'state_date':state.get('data'),'source':deputy['uri'],'profile_url':page,'checked_at':now(),'sha256':hashlib.sha256(detail_raw).hexdigest()}
    if norm(state.get('situacao'))=='exercicio':offices[cid]={'label':'Deputado(a) federal em exercício','detail':'Câmara dos Deputados · '+str(state.get('condicaoEleitoral',''))+'. Consulta de 21/09/2026.','source':page,'api_source':deputy['uri'],'checked_at':now()}
   save(DATA/'camara-records.json',camara)
  except Exception as e:audit['errors'].append({'stage':'camara','error':str(e)})
 # Directory links remain public while some institutional biographies are suspended.
 if 'alep_directory' not in audit['sources']:
  try:
   source='https://www.assembleia.pr.leg.br/deputados/representacao-partidaria';raw=get(source);soup=BeautifulSoup(raw,'html.parser')
   aliases={'160002546872':'GOURA','160002542281':'PROFESSOR LEMOS','160002542256':'DOUTOR ANTENOR','160002536499':'ARILSON MAROLDI CHIORATO','160002536522':'RENATO FREITAS','160002536521':'LUCIANA RAFAGNIN','160002536516':'ANA JÚLIA'}
   links=[a for a in soup.select('a[href]') if '/deputados/perfil/' in a['href']]
   for cid,name in aliases.items():
    if cid not in ids:continue
    found=[a for a in links if norm(a.get_text(' ',strip=True)).startswith(norm(name))]
    if len(found)!=1:continue
    offices[cid]={'label':'Deputado(a) estadual na ALEP','detail':'Listado na composição atual da Assembleia, consultada em 21/09/2026; não se infere situação de licença a partir da biografia.','source':source,'profile_source':urllib.parse.urljoin(source,found[0]['href']),'checked_at':now()}
   audit['sources']['alep_directory']={'url':source,'checked_at':now(),'sha256':hashlib.sha256(raw).hexdigest(),'matched_candidates':[cid for cid in aliases if cid in offices]}
  except Exception as e:audit['errors'].append({'stage':'alep','error':str(e)})
 save(DATA/'offices-verified.json',offices)
 save(DOC/'supplementary-sources.json',audit)
 # Import read-only, CRC-checked range utilities; do not invoke the RS collector.
 spec=importlib.util.spec_from_file_location('eef_ranges',ROOT/'tools/rs/votes_ranges.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 votes=read(DATA/'votes-official.json',{});history=read(DATA/'history-official.json',[])
 vote_audit=read(DOC/'votes-ranges.json',{'years':{},'errors':[]})
 for year in (2024,2022,2020,2018,2016,2014,2012):
  if str(year) in votes:continue
  targets={h['SQ_CANDIDATO'] for h in history if h.get('ANO_ELEICAO')==str(year) and h.get('SG_UF')=='PR' and not h.get('DS_CARGO','').startswith('VICE')}
  if not targets:continue
  source=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
  try:
   first,total=v.segment(source,0,255);remote=v.RangeFile(source,total)
   with v.zipfile.ZipFile(remote) as archive:
    names=[n for n in archive.namelist() if n.upper().endswith('_PR.CSV')];assert len(names)==1
    info=archive.getinfo(names[0]);totals=collections.defaultdict(int);line_counts=collections.Counter();generated=None
    with archive.open(info) as payload:
     tracked=v.DigestReader(payload)
     with io.TextIOWrapper(io.BufferedReader(tracked),encoding='latin-1',newline='') as stream:
      reader=csv.DictReader(stream,delimiter=';');assert {'SQ_CANDIDATO','QT_VOTOS_NOMINAIS','NR_TURNO','SG_UF'}.issubset(reader.fieldnames)
      for row in reader:
       if row.get('SQ_CANDIDATO') not in targets or row.get('SG_UF')!='PR':continue
       assert int(row.get('ANO_ELEICAO',year))==year
       key=row['SQ_CANDIDATO']+':'+row['NR_TURNO'];totals[key]+=int(row['QT_VOTOS_NOMINAIS']);line_counts[key]+=1
       generated=generated or row.get('DT_GERACAO','')+' '+row.get('HH_GERACAO','')
     assert tracked.count==info.file_size,'Incomplete member'
   assert totals,'No matching historical totals'
   votes[str(year)]={'source_url':source,'dataset':f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}','member':names[0],'archive_sha256':None,'member_sha256':tracked.digest.hexdigest(),'member_crc32':f'{info.CRC:08x}','member_bytes':tracked.count,'http_bytes_read':remote.transferred+len(first),'generated_at':generated,'checked_at':now(),'method':'Exact public HTTP ranges, ZIP CRC and full PR CSV SHA-256; no claim of full archive hash.','totals':dict(totals),'rows_per_total':dict(line_counts)}
   vote_audit['years'][str(year)]={'target_ids':len(targets),'matched_totals':len(totals)};save(DATA/'votes-official.json',votes)
  except Exception as e:vote_audit['errors'].append({'year':year,'error':str(e)})
  save(DOC/'votes-ranges.json',vote_audit)
 print(json.dumps({'offices':len(offices),'historical_years':list(votes),'source_errors':audit['errors'],'vote_errors':vote_audit['errors']},ensure_ascii=False,indent=2))
if __name__=='__main__':run()

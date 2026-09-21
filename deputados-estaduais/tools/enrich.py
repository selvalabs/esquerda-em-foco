"""Enrich the isolated public dataset. No federal writes; no inferred mandates."""
from __future__ import annotations
import csv, hashlib, io, json, os, re, sys, subprocess, time, zipfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data'; A = ROOT / 'audit'; P = ROOT / 'assets' / 'portraits'
P.mkdir(parents=True, exist_ok=True)
PARTIES = ['PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO']
BASE = 'https://cdn.tse.jus.br/estatistica/sead/odsele/'
REPORT = {'sources': {}, 'errors': []}

def save(path, obj):
 Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def get(url):
 last = None
 for i in range(3):
  try:
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (public electoral data research)'}),timeout=150) as r:
    return r.read()
  except Exception as e:
   last=e; time.sleep(i+1)
 raise RuntimeError(f'{url}: {last}')

def csvs(z, pattern=r'_SC\.csv$'):
 names=[n for n in z.namelist() if re.search(pattern,n,re.I)]
 if not names: raise ValueError(f'CSV not found: {pattern}: {z.namelist()[:8]}')
 for name in names:
  with z.open(name) as f:
   with io.TextIOWrapper(f,encoding='latin-1',newline='') as t:
    yield name,csv.DictReader(t,delimiter=';')

def run():
 universe=json.loads((D/'universo-sc-2026.json').read_text())
 candidates=[r for r in universe if r['SG_PARTIDO'] in PARTIES]
 ids={r['SQ_CANDIDATO'] for r in candidates}
 history=[r for r in json.loads((D/'historico-sc-2026.json').read_text()) if r['SQ_CANDIDATO_ATUAL'] in ids and int(r['ANO_ELEICAO'])<2026]
 save(D/'recorte-sc-2026.json',candidates)
 REPORT['scope']={'parties_considered':PARTIES,'universe':len(universe),'selected':len(candidates),'rule':'Filiação registrada no TSE; não é classificação individual de ideologia nem recomendação de voto.'}
 # The main CSV leaves registration status empty. Complementary CSV is authoritative here.
 url=BASE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip'
 try:
  raw=get(url); z=zipfile.ZipFile(io.BytesIO(raw)); rows=[]
  REPORT['sources']['complementar']={'url':url,'sha256':hashlib.sha256(raw).hexdigest()}
  for name, reader in csvs(z):
   REPORT['sources']['complementar']['columns']=reader.fieldnames
   for r in reader:
    if r.get('SQ_CANDIDATO') in ids:
     rows.append({k:v for k,v in r.items() if not any(w in k for w in ['CPF','TITULO','EMAIL','NASCIMENTO','PROCESSO','ENDERECO','TELEFONE'])})
  save(D/'situacao-sc-2026.json',rows)
  REPORT['sources']['complementar']['matched']=len(rows)
 except Exception as e: REPORT['errors'].append(str(e))
 # Official portraits, matched only by the stable candidate identifier.
 url='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SC_div.zip'
 try:
  raw=get(url); z=zipfile.ZipFile(io.BytesIO(raw)); photos={}
  REPORT['sources']['photos']={'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'archive_files':len(z.namelist())}
  for name in z.namelist():
   match=next((sid for sid in ids if re.search(r'(?<!\d)'+sid+r'(?!\d)',name)),None)
   if not match or not re.search(r'\.(jpe?g|png)$',name,re.I): continue
   image=ImageOps.exif_transpose(Image.open(io.BytesIO(z.read(name)))).convert('RGB')
   image.thumbnail((360,450))
   image.save(P/f'{match}.webp','WEBP',quality=84,method=6)
   photos[match]={'path':f'assets/portraits/{match}.webp','archive_member':name,'width':image.width,'height':image.height}
  save(D/'portraits.json',photos)
  REPORT['sources']['photos']['matched']=len(photos)
 except Exception as e: REPORT['errors'].append(str(e))
 # Historical vote totals: sum municipality/zone records, independently for each round.
 # RemoteZip reads SC only through HTTP Range; the national archive is not committed.
 if not (D/'votos-historicos.json').exists():
  try:
   from remotezip import RemoteZip
  except ImportError:
   subprocess.check_call([sys.executable,'-m','pip','install','remotezip'])
   from remotezip import RemoteZip
  by_year=defaultdict(set)
  for r in history:
   if r['CD_CARGO']!='12': # vice mayor has no separate nominal vote
    by_year[r['ANO_ELEICAO']].add((r['SQ_CANDIDATO'],r['NR_TURNO']))
  def votes(year):
   url=BASE+f'votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
   out={}; source={'url':url,'method':'SC CSV via HTTP Range; sum QT_VOTOS_NOMINAIS per SQ_CANDIDATO and NR_TURNO'}
   try:
    with RemoteZip(url,initial_buffer_size=131072,timeout=150) as z:
     for name, reader in csvs(z):
      source['member']=name; source['columns']=reader.fieldnames
      for r in reader:
       sid=r.get('SQ_CANDIDATO',r.get('SEQUENCIAL_CANDIDATO',''))
       turn=r.get('NR_TURNO',r.get('NUM_TURNO',''))
       if (sid,turn) not in by_year[year]: continue
       key=f'{year}:{sid}:{turn}'
       if key not in out: out[key]={'year':year,'candidate_id':sid,'round':turn,'votes':0,'valid_votes':0,'rows':0,'source':url}
       out[key]['votes']+=int(r.get('QT_VOTOS_NOMINAIS',r.get('QTDE_VOTOS','0')))
       out[key]['valid_votes']+=int(r.get('QT_VOTOS_NOMINAIS_VALIDOS','0'))
       out[key]['rows']+=1
    source['matched']=len(out)
   except Exception as e: source['error']=str(e)
   return year,out,source
  merged={}
  with ThreadPoolExecutor(max_workers=3) as pool:
   for year,vals,source in pool.map(votes,sorted(by_year)):
    merged.update(vals); REPORT['sources']['votes_'+year]=source
    print(year,len(vals),source.get('error','OK'),flush=True)
  save(D/'votos-historicos.json',merged)
 else: REPORT['sources']['votes']={'cached_file':'data/votos-historicos.json'}
 save(A/'enrichment.json',REPORT)
 print(json.dumps(REPORT,ensure_ascii=False,indent=2),flush=True)

if __name__=='__main__': run()

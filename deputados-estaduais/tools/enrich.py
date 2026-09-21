"""Official status, portraits and historical votes. Federal files stay untouched."""
from __future__ import annotations
import csv,hashlib,io,json,re,sys,subprocess,time,zipfile,tempfile,shutil
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; A=ROOT/'audit'; P=ROOT/'assets'/'portraits'
P.mkdir(parents=True,exist_ok=True)
PARTIES=['PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO']
BASE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
HEADERS={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*'}

def save(path,obj): Path(path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def get(url):
 error=None
 for i in range(3):
  try:
   with urlopen(Request(url,headers=HEADERS),timeout=180) as r: return r.read()
  except Exception as e: error=e; time.sleep(i+1)
 raise RuntimeError(f'{url}: {error}')
def csvs(z):
 names=[n for n in z.namelist() if re.search(r'_SC\.csv$',n,re.I)]
 if not names: raise ValueError('SC CSV missing: '+str(z.namelist()[:4]))
 for name in names:
  with z.open(name) as f:
   with io.TextIOWrapper(f,encoding='latin-1',newline='') as t: yield name,csv.DictReader(t,delimiter=';')

def run():
 previous=json.loads((A/'enrichment.json').read_text()) if (A/'enrichment.json').exists() else {}
 report={'sources':previous.get('sources',{}),'errors':[]}
 universe=json.loads((D/'universo-sc-2026.json').read_text())
 candidates=[r for r in universe if r['SG_PARTIDO'] in PARTIES]
 ids={r['SQ_CANDIDATO'] for r in candidates}
 history=[r for r in json.loads((D/'historico-sc-2026.json').read_text()) if r['SQ_CANDIDATO_ATUAL'] in ids and int(r['ANO_ELEICAO'])<2026]
 save(D/'recorte-sc-2026.json',candidates)
 report['scope']={'parties_considered':PARTIES,'universe':len(universe),'selected':len(candidates),'rule':'Filiação registrada no TSE; não é classificação individual de ideologia nem recomendação de voto.'}
 url=BASE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip'
 if not (D/'situacao-sc-2026.json').exists():
  try:
   raw=get(url); rows=[]; source={'url':url,'sha256':hashlib.sha256(raw).hexdigest()}
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    for name,reader in csvs(z):
     source['columns']=reader.fieldnames; source['member']=name
     for r in reader:
      if r.get('SQ_CANDIDATO') in ids:
       rows.append({k:v for k,v in r.items() if not any(w in k for w in ['CPF','TITULO','EMAIL','NASCIMENTO','PROCESSO','ENDERECO','TELEFONE'])})
   if not rows: raise ValueError('No complementary matches')
   save(D/'situacao-sc-2026.json',rows); source['matched']=len(rows); report['sources']['complementar']=source
  except Exception as e: report['errors'].append(str(e))
 url='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SC_div.zip'
 if not (D/'portraits.json').exists():
  try:
   raw=get(url); photos={}; source={'url':url,'sha256':hashlib.sha256(raw).hexdigest()}
   with zipfile.ZipFile(io.BytesIO(raw)) as z:
    source['archive_files']=len(z.namelist())
    for name in z.namelist():
     match=next((sid for sid in ids if re.search(r'(?<!\d)'+sid+r'(?!\d)',name)),None)
     if not match or not re.search(r'\.(jpe?g|png)$',name,re.I): continue
     image=ImageOps.exif_transpose(Image.open(io.BytesIO(z.read(name)))).convert('RGB'); image.thumbnail((360,450))
     image.save(P/f'{match}.webp','WEBP',quality=84,method=6)
     photos[match]={'path':f'assets/portraits/{match}.webp','archive_member':name,'width':image.width,'height':image.height}
   if not photos: raise ValueError('No matched official portraits')
   save(D/'portraits.json',photos); source['matched']=len(photos); report['sources']['photos']=source
  except Exception as e: report['errors'].append(str(e))
 merged=json.loads((D/'votos-historicos.json').read_text()) if (D/'votos-historicos.json').exists() else {}
 by_year=defaultdict(set); chapas=defaultdict(set)
 for r in history:
  if r['CD_CARGO']=='12': chapas[r['ANO_ELEICAO']].add((r['SG_UE'],r['NR_CANDIDATO'],r['NR_TURNO']))
  else: by_year[r['ANO_ELEICAO']].add((r['SQ_CANDIDATO'],r['NR_TURNO']))
 years=[y for y in sorted(set(by_year)|set(chapas)) if not report['sources'].get('votes_'+y,{}).get('complete')]
 if years:
  try: from remotezip import RemoteZip
  except ImportError:
   subprocess.check_call([sys.executable,'-m','pip','install','remotezip'])
   from remotezip import RemoteZip
  def votes(year):
   url=BASE+f'votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
   out={}; source={'url':url,'method':'SC CSV; sum municipality/zone nominal votes per candidate and round'}; temp=None
   try:
    try:
     z=RemoteZip(url,initial_buffer_size=131072,timeout=90,headers=HEADERS)
     z.namelist(); source['transfer']='HTTP Range'
    except Exception:
     temp=tempfile.TemporaryFile()
     with urlopen(Request(url,headers=HEADERS),timeout=180) as response: shutil.copyfileobj(response,temp)
     temp.seek(0); z=zipfile.ZipFile(temp); source['transfer']='Full official ZIP; only SC CSV read'
    with z:
     for name,reader in csvs(z):
      source['member']=name; source['columns']=reader.fieldnames
      for r in reader:
       sid=r.get('SQ_CANDIDATO',r.get('SEQUENCIAL_CANDIDATO','')); turn=r.get('NR_TURNO',r.get('NUM_TURNO',''))
       ue=r.get('SG_UE',r.get('CODIGO_UE','')); number=r.get('NR_CANDIDATO',r.get('NUMERO_CANDIDATO','')); office=r.get('CD_CARGO',r.get('CODIGO_CARGO',''))
       is_chapa=office=='11' and (ue,number,turn) in chapas[year]
       if (sid,turn) not in by_year[year] and not is_chapa: continue
       key=f'{year}:chapa:{ue}:{number}:{turn}' if is_chapa else f'{year}:{sid}:{turn}'
       if key not in out: out[key]={'year':year,'candidate_id':sid,'round':turn,'votes':0,'rows':0,'source':url,'type':'chapa' if is_chapa else 'nominal'}
       out[key]['votes']+=int(r.get('QT_VOTOS_NOMINAIS',r.get('QTDE_VOTOS','0'))); out[key]['rows']+=1
    source['matched']=len(out); source['complete']=bool(out)
   except Exception as e: source['error']=str(e)
   finally:
    if temp: temp.close()
   return year,out,source
  with ThreadPoolExecutor(max_workers=2) as pool:
   for year,vals,source in pool.map(votes,years):
    merged.update(vals); report['sources']['votes_'+year]=source
    print('Historical votes',year,len(vals),source.get('error','OK'),flush=True)
 save(D/'votos-historicos.json',merged)
 save(A/'enrichment.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__': run()

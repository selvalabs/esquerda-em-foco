"""TSE public archives via verified HTTP Range. Keep only scoped public records."""
from __future__ import annotations
import concurrent.futures,csv,hashlib,io,json,re,time,zipfile
from collections import defaultdict
from pathlib import Path
from urllib.request import Request,urlopen
from PIL import Image,ImageOps
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; A=ROOT/'audit'; P=ROOT/'assets/portraits'; P.mkdir(parents=True,exist_ok=True)
BASE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
PARTIES={'PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO'}
def save(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def archive(url):
 headers={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*','Range':'bytes=0-'}
 for attempt in range(2):
  try:
   with urlopen(Request(url,headers=headers),timeout=45) as r:
    raw=r.read(); content_range=r.headers.get('Content-Range'); status=r.status
   if content_range:
    match=re.fullmatch(r'bytes 0-(\d+)/(\d+)',content_range)
    if not match or int(match[2])!=len(raw) or int(match[1])+1!=len(raw): raise ValueError('Incomplete byte range: '+content_range)
   z=zipfile.ZipFile(io.BytesIO(raw))
   return z,{'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'http_status':status,'content_range':content_range,'method':'Complete archive requested as bytes=0-; length and ZIP directory verified'}
  except Exception:
   if attempt: raise
   time.sleep(1)
def tables(z):
 names=[n for n in z.namelist() if re.search(r'_SC\.csv$',n,re.I)]
 if not names: raise ValueError('No SC CSV in archive')
 for name in names:
  with z.open(name) as binary:
   with io.TextIOWrapper(binary,encoding='latin-1',newline='') as text: yield name,csv.DictReader(text,delimiter=';')
def run():
 previous=json.loads((A/'official.json').read_text()) if (A/'official.json').exists() else {}
 report={'sources':previous.get('sources',{}),'errors':[]}
 candidates=[r for r in json.loads((D/'universo-sc-2026.json').read_text()) if r['SG_PARTIDO'] in PARTIES]
 ids={r['SQ_CANDIDATO'] for r in candidates}
 history=[r for r in json.loads((D/'historico-sc-2026.json').read_text()) if r['SQ_CANDIDATO_ATUAL'] in ids and int(r['ANO_ELEICAO'])<2026]
 url=BASE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip'
 if not report['sources'].get('registration',{}).get('complete'):
  try:
   z,source=archive(url); rows=[]
   with z:
    for name,reader in tables(z):
     source.update(member=name,columns=reader.fieldnames)
     for r in reader:
      if r.get('SQ_CANDIDATO') in ids: rows.append({k:v for k,v in r.items() if not any(w in k for w in ['CPF','TITULO','EMAIL','NASCIMENTO','PROCESSO','ENDERECO','TELEFONE'])})
   save(D/'situacao-sc-2026.json',rows); source.update(matched=len(rows),complete=len(rows)==len(ids)); report['sources']['registration']=source
  except Exception as e: report['errors'].append({'url':url,'error':str(e)})
  save(A/'official.json',report)
 url='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SC_div.zip'
 if not report['sources'].get('photos',{}).get('complete'):
  try:
   z,source=archive(url); photos={}
   with z:
    for name in z.namelist():
     match=next((sid for sid in ids if re.search(r'(?<!\d)'+sid+r'(?!\d)',name)),None)
     if not match or not re.search(r'\.(jpe?g|png)$',name,re.I): continue
     original=z.read(name); image=ImageOps.exif_transpose(Image.open(io.BytesIO(original))).convert('RGB'); image.thumbnail((360,450)); image.save(P/f'{match}.webp','WEBP',quality=84,method=6)
     photos[match]={'path':f'assets/portraits/{match}.webp','source':url,'archive_member':name,'source_kind':'Arquivo oficial de fotos do TSE','sha256_source':hashlib.sha256(original).hexdigest(),'matched_by':'SQ_CANDIDATO in official archive member','width':image.width,'height':image.height}
   if photos: save(D/'portraits.json',photos)
   source.update(matched=len(photos),complete=len(photos)==len(ids)); report['sources']['photos']=source
  except Exception as e: report['errors'].append({'url':url,'error':str(e)})
  save(A/'official.json',report)
 by_year=defaultdict(set); tickets=defaultdict(set)
 for r in history:
  if r['CD_CARGO']=='12': tickets[r['ANO_ELEICAO']].add((r['SG_UE'],r['NR_CANDIDATO'],r['NR_TURNO']))
  else: by_year[r['ANO_ELEICAO']].add((r['SQ_CANDIDATO'],r['NR_TURNO']))
 merged=json.loads((D/'votos-historicos.json').read_text()) if (D/'votos-historicos.json').exists() else {}
 years=[y for y in sorted(set(by_year)|set(tickets)) if not report['sources'].get('votes_'+y,{}).get('complete')]
 def year_votes(year):
  url=BASE+f'votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'; out={}; source={'url':url}
  try:
   z,source=archive(url)
   with z:
    for name,reader in tables(z):
     source.update(member=name,columns=reader.fieldnames)
     for r in reader:
      sid=r.get('SQ_CANDIDATO',r.get('SEQUENCIAL_CANDIDATO','')); turn=r.get('NR_TURNO',r.get('NUM_TURNO',''))
      ue=r.get('SG_UE',r.get('CODIGO_UE','')); nr=r.get('NR_CANDIDATO',r.get('NUMERO_CANDIDATO','')); cargo=r.get('CD_CARGO',r.get('CODIGO_CARGO',''))
      ticket=cargo=='11' and (ue,nr,turn) in tickets[year]
      if (sid,turn) not in by_year[year] and not ticket: continue
      key=f'{year}:chapa:{ue}:{nr}:{turn}' if ticket else f'{year}:{sid}:{turn}'
      if key not in out: out[key]={'year':year,'candidate_id':sid,'round':turn,'votes':0,'rows':0,'source':url,'type':'chapa' if ticket else 'nominal'}
      out[key]['votes']+=int(r.get('QT_VOTOS_NOMINAIS',r.get('QTDE_VOTOS','0'))); out[key]['rows']+=1
   source.update(matched=len(out),complete=bool(out))
  except Exception as e: source['error']=str(e)
  return year,out,source
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for year,found,source in pool.map(year_votes,years):
   merged.update(found); report['sources']['votes_'+year]=source
   save(D/'votos-historicos.json',merged); save(A/'official.json',report)
   print('Official results',year,len(found),source.get('error','OK'),flush=True)
 print('Official coverage',json.dumps({k:v.get('matched') for k,v in report['sources'].items()}),flush=True)
if __name__=='__main__': run()

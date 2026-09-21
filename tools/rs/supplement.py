"""Read direct official public resources after dataset HTML availability failures."""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, io, json, re, tempfile, time, unicodedata, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';A=ROOT/'docs/rs'
def load(name,default):
 p=D/name
 return json.loads(p.read_text()) if p.exists() else default
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(s):return ''.join(c for c in unicodedata.normalize('NFD',str(s).casefold()) if unicodedata.category(c)!='Mn')
def request(url,timeout=20):return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (public electoral data verification)'}),timeout=timeout)
def run():
 if (A/'supplement.json').exists():return
 audit={'checked_at':datetime.now(timezone.utc).isoformat(),'errors':[],'votes':{},'institutions':[]}
 records=load('candidates-official.json',[]);history=load('history-normalized.json',{});votes=load('votes-official.json',{})
 for year in (2024,2022):
  if str(year) in votes:continue
  targets={h['candidate_id'] for hs in history.values() for h in hs if h['year']==year}
  if not targets:continue
  url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
  try:
   digest=hashlib.sha256();count=0;start=time.monotonic()
   with tempfile.TemporaryFile() as f:
    with request(url,30) as response:
     while True:
      chunk=response.read(1024*1024)
      if not chunk:break
      digest.update(chunk);count+=len(chunk);f.write(chunk)
      if count>700_000_000 or time.monotonic()-start>180:raise TimeoutError('Bounded archive transfer limit')
    f.seek(0);z=zipfile.ZipFile(f);names=[n for n in z.namelist() if n.upper().endswith('_RS.CSV')]
    if len(names)!=1:raise ValueError('Expected exactly one RS CSV')
    totals=collections.defaultdict(int);lines=collections.Counter();sample=None
    with z.open(names[0]) as payload:
     text=io.TextIOWrapper(payload,encoding='utf-8-sig' if payload.peek(3)[:3]==b'\xef\xbb\xbf' else 'latin-1',newline='')
     for r in csv.DictReader(text,delimiter=';'):
      if r.get('SQ_CANDIDATO') not in targets or r.get('SG_UF')!='RS':continue
      key=r['SQ_CANDIDATO']+':'+r['NR_TURNO'];totals[key]+=int(r['QT_VOTOS_NOMINAIS']);lines[key]+=1
      if sample is None:sample={k:r[k] for k in ('SQ_CANDIDATO','NR_TURNO','CD_CARGO','QT_VOTOS_NOMINAIS','DT_GERACAO','HH_GERACAO') if k in r}
    if not totals:raise ValueError('No matching vote totals; refusing empty success')
    votes[str(year)]={'source_url':url,'dataset':f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}','sha256':digest.hexdigest(),'bytes':count,'member':names[0],'totals':dict(totals),'rows_per_total':dict(lines),'sample':sample,'checked_at':audit['checked_at']}
    save(D/'votes-official.json',votes);audit['votes'][str(year)]={'matched':len(totals),'sha256':digest.hexdigest()}
  except Exception as exc:audit['errors'].append({'stage':'votes','year':year,'error':str(exc)})
 try:
  directory_url='https://dadosabertos.camara.leg.br/arquivos/deputados/json/deputados.json'
  with request(directory_url) as response:directory=json.load(response)
  if isinstance(directory,dict):directory=directory.get('dados',[])
  audit['directory_columns']=list(directory[0]) if directory else []
  names={norm(r['NM_CANDIDATO']) for r in records}|{norm(r['NM_URNA_CANDIDATO']) for r in records};ids=set()
  for item in directory:
   if any(norm(item.get(k,'')) in names for k in ('nome','nomeCivil','nomeEleitoral')):
    did=item.get('id') or item.get('idDeputado')
    if not did:
     match=re.search(r'/deputados/(\d+)',str(item.get('uri','')));did=match[1] if match else None
    if did:ids.add(int(did))
  def institution(did):
   url=f'https://www.camara.leg.br/deputados/{did}'
   try:
    with request(url,18) as response:raw=response.read(3_000_000)
    page=BeautifulSoup(raw,'html.parser');text=page.get_text(' ',strip=True)
    name=re.search(r'Nome Civil:\s*(.*?)\s*Partido:',text);status=re.search(r'(titular|suplente)\s+(em exercício|fora de exercício|não em exercício|licenciado)[^\d]*2023\s*-\s*2027',text,re.I)
    return {'id':did,'source':url,'civil_name':name[1].strip() if name else '', 'status':status[0] if status else '', 'checked_at':audit['checked_at'],'sha256':hashlib.sha256(raw).hexdigest()}
   except Exception as exc:return {'id':did,'source':url,'error':str(exc)}
  with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:profiles=list(pool.map(institution,sorted(ids)))
  offices=load('offices-verified.json',{})
  for r in records:
   matches=[p for p in profiles if norm(p.get('civil_name',''))==norm(r['NM_CANDIDATO']) and re.match(r'^(titular|suplente) em exercício',p.get('status',''),re.I)]
   if len(matches)==1:
    p=matches[0];offices[r['SQ_CANDIDATO']]={'label':'Deputado(a) federal','source':p['source'],'detail':p['status'],'checked_at':p['checked_at']}
  save(D/'offices-verified.json',offices);audit['institutions']=profiles;audit['current_offices_confirmed']=len(offices)
 except Exception as exc:audit['errors'].append({'stage':'current_offices','error':str(exc)})
 save(A/'supplement.json',audit)
if __name__=='__main__':run()

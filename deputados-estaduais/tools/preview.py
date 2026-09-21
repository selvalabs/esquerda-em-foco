"""Bounded review build. Record unavailable sources without inventing replacements."""
from pathlib import Path
import concurrent.futures, hashlib, io, json, runpy, time
from urllib.request import Request, urlopen
from PIL import Image, ImageOps
ROOT=Path(__file__).resolve().parents[1]; D=ROOT/'data'; A=ROOT/'audit'; P=ROOT/'assets/portraits'; P.mkdir(parents=True,exist_ok=True)
SOURCES=[
 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip',
 'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SC_div.zip',
 'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_2024.zip',
 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/listar/2026/SC/6259/7/candidatos',
 'https://realidadebrasil.com.br/media/photos/240002540083.jpg'
]
def probe(url):
 out={'url':url}; start=time.monotonic()
 try:
  with urlopen(Request(url,headers={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*','Range':'bytes=0-255'}),timeout=15) as r:
   data=r.read(1000000); out.update(status=r.status,headers=dict(r.headers),bytes_read=len(data),first_bytes=data[:60].hex())
 except Exception as e: out['error']=str(e)
 out['seconds']=round(time.monotonic()-start,2); return out
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: results=list(pool.map(probe,SOURCES))
(A/'source-probes.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print(json.dumps(results,ensure_ascii=False,indent=2),flush=True)
# This is the same public mirror already used by the federal edition. It is
# explicitly identified as a mirror, not presented as a direct TSE download.
portraits=json.loads((D/'portraits.json').read_text()) if (D/'portraits.json').exists() else {}
raw=json.loads((D/'universo-sc-2026.json').read_text()); parties={'PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO'}
selected=[r for r in raw if r['SG_PARTIDO'] in parties]
def portrait(r):
 sid=r['SQ_CANDIDATO']; url=f'https://realidadebrasil.com.br/media/photos/{sid}.jpg'
 if sid in portraits: return sid,portraits[sid],None
 try:
  with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=12) as response: raw=response.read(2000000)
  image=ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB'); image.thumbnail((360,450)); image.save(P/f'{sid}.webp','WEBP',quality=84,method=6)
  return sid,{'path':f'assets/portraits/{sid}.webp','source':url,'source_kind':'Espelho público das fotos de candidatura; não é download direto do TSE','sha256_source':hashlib.sha256(raw).hexdigest(),'matched_by':'SQ_CANDIDATO in URL','width':image.width,'height':image.height},None
 except Exception as e: return sid,None,str(e)
errors=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
 for sid,photo,error in pool.map(portrait,selected):
  if photo: portraits[sid]=photo
  if error: errors.append({'id':sid,'error':error})
(D/'portraits.json').write_text(json.dumps(portraits,ensure_ascii=False,indent=2))
(A/'portrait-review.json').write_text(json.dumps({'matched':len(portraits),'unavailable':errors,'source_kind':'Direct official archive when available; public mirror explicitly labelled otherwise'},ensure_ascii=False,indent=2))
# Read institutional pages and declared campaign sites for manual review.
try:
 from research import run
 run()
except Exception as e: print('Source reading:',str(e),flush=True)
runpy.run_path(str(Path(__file__).with_name('render.py')),run_name='__main__')

"""Download complete public ZIPs using bounded ranges and strict byte validation."""
from __future__ import annotations
import concurrent.futures,hashlib,io,re,time,zipfile
from urllib.request import Request,urlopen
CHUNK=2*1024*1024
HEADERS={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*'}
def segment(url,start,end):
 error=None
 for attempt in range(2):
  try:
   req=Request(url,headers={**HEADERS,'Range':f'bytes={start}-{end}'})
   with urlopen(req,timeout=18) as r:
    status=r.status; cr=r.headers.get('Content-Range',''); raw=r.read(end-start+2)
   match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
   if status!=206 or not match: raise ValueError(f'Expected partial response, received {status} {cr}')
   first,last,total=map(int,match.groups())
   if first!=start or last!=min(end,total-1) or len(raw)!=last-first+1: raise ValueError(f'Range mismatch {start}-{end}: {cr}, {len(raw)} bytes')
   return raw,total
  except Exception as exc:
   error=exc; time.sleep(.5)
 raise RuntimeError(f'{url}: range {start}-{end}: {error}')
def archive(url):
 first,total=segment(url,0,255)
 if total>250*1024*1024: raise ValueError(f'Archive exceeds 250 MiB review bound: {total}')
 payload=bytearray(total); payload[:len(first)]=first
 ranges=[(n,min(n+CHUNK-1,total-1)) for n in range(len(first),total,CHUNK)]
 def read(pair):
  start,end=pair; raw,size=segment(url,start,end)
  if size!=total: raise ValueError('Archive changed during download')
  return start,raw
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for start,raw in pool.map(read,ranges): payload[start:start+len(raw)]=raw
 digest=hashlib.sha256(payload).hexdigest()
 z=zipfile.ZipFile(io.BytesIO(payload))
 return z,{'url':url,'sha256':digest,'bytes':total,'http_status':206,'chunks':len(ranges)+1,'method':'Complete ZIP reconstructed from strictly validated bounded HTTP byte ranges'}

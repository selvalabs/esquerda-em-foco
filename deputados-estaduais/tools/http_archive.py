"""Validated public HTTP ranges; large ZIPs expose only requested members."""
from __future__ import annotations
import concurrent.futures,hashlib,io,re,time,zipfile
from collections import OrderedDict
from urllib.request import Request,urlopen
CHUNK=2*1024*1024
HEADERS={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*'}
def segment(url,start,end):
 error=None
 for attempt in range(2):
  try:
   with urlopen(Request(url,headers={**HEADERS,'Range':f'bytes={start}-{end}'}),timeout=18) as r:
    status=r.status; cr=r.headers.get('Content-Range',''); raw=r.read(end-start+2)
   match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
   if status!=206 or not match: raise ValueError(f'Expected partial response: {status} {cr}')
   first,last,total=map(int,match.groups())
   if first!=start or last!=min(end,total-1) or len(raw)!=last-first+1: raise ValueError(f'Range mismatch: {cr}, {len(raw)} bytes')
   return raw,total
  except Exception as exc: error=exc; time.sleep(.5)
 raise RuntimeError(f'{url}: range {start}-{end}: {error}')

class RangeFile(io.RawIOBase):
 def __init__(self,url,size):
  super().__init__(); self.url=url; self.size=size; self.position=0; self.cache=OrderedDict()
 def readable(self): return True
 def seekable(self): return True
 def tell(self): return self.position
 def seek(self,offset,whence=0):
  pos=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
  if pos<0: raise ValueError('Negative seek')
  self.position=pos; return pos
 def block(self,index):
  if index not in self.cache:
   start=index*CHUNK; raw,total=segment(self.url,start,min(start+CHUNK-1,self.size-1))
   if total!=self.size: raise ValueError('Archive changed during download')
   self.cache[index]=raw
   if len(self.cache)>8: self.cache.popitem(last=False)
  else: self.cache.move_to_end(index)
  return self.cache[index]
 def read(self,size=-1):
  stop=self.size if size<0 else min(self.size,self.position+size)
  parts=[]
  while self.position<stop:
   index=self.position//CHUNK; offset=self.position%CHUNK; data=self.block(index)
   take=min(stop-self.position,len(data)-offset)
   if take<=0: raise EOFError('Unexpected end of range')
   parts.append(data[offset:offset+take]); self.position+=take
  return b''.join(parts)
 def readinto(self,buffer):
  raw=self.read(len(buffer)); buffer[:len(raw)]=raw; return len(raw)

class MemberReader(io.BufferedIOBase):
 def __init__(self,stream,info,record):
  super().__init__(); self.stream=stream; self.info=info; self.record=record; self.digest=hashlib.sha256(); self.count=0
 def readable(self): return True
 def seekable(self): return False
 def read(self,size=-1):
  raw=self.stream.read(size); self.digest.update(raw); self.count+=len(raw); return raw
 def read1(self,size=-1): return self.read(size)
 def readinto(self,buffer):
  raw=self.read(len(buffer)); buffer[:len(raw)]=raw; return len(raw)
 def close(self):
  if not self.closed:
   self.record['bytes_read']=self.count
   self.record['sha256']=self.digest.hexdigest() if self.count==self.info.file_size else None
   self.record['complete']=self.count==self.info.file_size
   self.stream.close()
  super().close()

class TrackedZip(zipfile.ZipFile):
 def __init__(self,file,source):
  self.source=source; super().__init__(file)
 def open(self,name,mode='r',pwd=None,*,force_zip64=False):
  stream=super().open(name,mode,pwd,force_zip64=force_zip64)
  if mode!='r': return stream
  info=name if isinstance(name,zipfile.ZipInfo) else self.getinfo(name)
  record={'uncompressed_bytes':info.file_size,'compressed_bytes':info.compress_size,'crc32':f'{info.CRC:08x}'}
  self.source.setdefault('read_members',{})[info.filename]=record
  return MemberReader(stream,info,record)

def archive(url):
 first,total=segment(url,0,255)
 if total>250*1024*1024:
  source={'url':url,'archive_bytes':total,'sha256':None,'sha256_scope':'Individual fully read members, not the entire archive','http_status':206,'method':'ZIP central directory and SC member only, using bounded validated HTTP ranges; ZIP CRC and member SHA-256 recorded'}
  return TrackedZip(RangeFile(url,total),source),source
 payload=bytearray(total); payload[:len(first)]=first
 ranges=[(n,min(n+CHUNK-1,total-1)) for n in range(len(first),total,CHUNK)]
 def read(pair):
  start,end=pair; raw,size=segment(url,start,end)
  if size!=total: raise ValueError('Archive changed during download')
  return start,raw
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  for start,raw in pool.map(read,ranges): payload[start:start+len(raw)]=raw
 source={'url':url,'sha256':hashlib.sha256(payload).hexdigest(),'bytes':total,'http_status':206,'chunks':len(ranges)+1,'method':'Complete ZIP reconstructed from strictly validated bounded HTTP byte ranges'}
 return zipfile.ZipFile(io.BytesIO(payload)),source

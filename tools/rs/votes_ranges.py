"""Read only the RS member of large public TSE ZIPs. No authentication bypass.
HTTP ranges must be exact; ZipFile verifies CRC and the full member gets SHA-256.
The archive's own hash is not claimed when only parts of it are transferred.
"""
from __future__ import annotations
import collections,csv,hashlib,io,json,re,time,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';A=ROOT/'docs/rs';CHUNK=2*1024*1024
HEADERS={'User-Agent':'EsquerdaEmFoco/1.0 public-data-audit','Accept':'*/*'}
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def segment(url,start,end):
 error=None
 for attempt in range(2):
  try:
   with urllib.request.urlopen(urllib.request.Request(url,headers={**HEADERS,'Range':f'bytes={start}-{end}'}),timeout=18) as r:
    status=r.status;cr=r.headers.get('Content-Range','');raw=r.read(end-start+2)
   match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',cr)
   if status!=206 or not match:raise ValueError(f'Expected partial response: {status} {cr}')
   first,last,total=map(int,match.groups())
   if first!=start or last!=min(end,total-1) or len(raw)!=last-first+1:raise ValueError(f'Range mismatch: {cr}; {len(raw)} bytes')
   return raw,total
  except Exception as exc:error=exc;time.sleep(.5)
 raise RuntimeError(str(error))
class RangeFile(io.RawIOBase):
 def __init__(self,url,size):super().__init__();self.url=url;self.size=size;self.position=0;self.cache=collections.OrderedDict();self.started=time.monotonic();self.transferred=0
 def readable(self):return True
 def seekable(self):return True
 def tell(self):return self.position
 def seek(self,offset,whence=0):
  position=offset if whence==0 else self.position+offset if whence==1 else self.size+offset
  if position<0:raise ValueError('Negative position')
  self.position=position;return position
 def block(self,index):
  if time.monotonic()-self.started>180:raise TimeoutError('Archive range time budget exceeded')
  if index not in self.cache:
   start=index*CHUNK;raw,total=segment(self.url,start,min(start+CHUNK-1,self.size-1))
   if total!=self.size:raise ValueError('Archive changed during collection')
   self.cache[index]=raw;self.transferred+=len(raw)
   if len(self.cache)>8:self.cache.popitem(last=False)
  else:self.cache.move_to_end(index)
  return self.cache[index]
 def read(self,size=-1):
  stop=self.size if size<0 else min(self.size,self.position+size);parts=[]
  while self.position<stop:
   index=self.position//CHUNK;offset=self.position%CHUNK;data=self.block(index);take=min(stop-self.position,len(data)-offset)
   if take<=0:raise EOFError('Unexpected end of range')
   parts.append(data[offset:offset+take]);self.position+=take
  return b''.join(parts)
 def readinto(self,buffer):raw=self.read(len(buffer));buffer[:len(raw)]=raw;return len(raw)
class DigestReader(io.RawIOBase):
 def __init__(self,stream):super().__init__();self.stream=stream;self.digest=hashlib.sha256();self.count=0
 def readable(self):return True
 def readinto(self,buffer):
  raw=self.stream.read(len(buffer));self.digest.update(raw);self.count+=len(raw);buffer[:len(raw)]=raw;return len(raw)
def run():
 if (A/'votes-ranges.json').exists():return
 history=json.loads((D/'history-normalized.json').read_text());votes=json.loads((D/'votes-official.json').read_text()) if (D/'votes-official.json').exists() else {}
 audit={'checked_at':datetime.now(timezone.utc).isoformat(),'method':'Validated public HTTP byte ranges, ZIP CRC, complete RS-member SHA-256','years':{},'errors':[]}
 for year in (2024,2022):
  if str(year) in votes:continue
  targets={h['candidate_id'] for hs in history.values() for h in hs if h['year']==year and not str(h.get('office','')).upper().startswith('VICE')}
  if not targets:continue
  url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
  try:
   first,total=segment(url,0,255);remote=RangeFile(url,total)
   with zipfile.ZipFile(remote) as archive:
    names=[n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
    if len(names)!=1:raise ValueError('Expected a unique RS CSV')
    info=archive.getinfo(names[0]);totals=collections.defaultdict(int);lines=collections.Counter();generation=None
    with archive.open(info) as payload:
     tracked=DigestReader(payload)
     with io.TextIOWrapper(io.BufferedReader(tracked),encoding='latin-1',newline='') as text:
      reader=csv.DictReader(text,delimiter=';')
      if not {'SQ_CANDIDATO','QT_VOTOS_NOMINAIS','NR_TURNO','SG_UF'}.issubset(reader.fieldnames):raise ValueError('Required vote columns absent')
      for r in reader:
       if r.get('SQ_CANDIDATO') not in targets or r.get('SG_UF')!='RS':continue
       if int(r.get('ANO_ELEICAO',year))!=year:raise ValueError('Wrong election year')
       key=r['SQ_CANDIDATO']+':'+r['NR_TURNO'];totals[key]+=int(r['QT_VOTOS_NOMINAIS']);lines[key]+=1
       if generation is None:generation=r.get('DT_GERACAO','')+' '+r.get('HH_GERACAO','')
     if tracked.count!=info.file_size:raise ValueError('Incomplete CSV read')
    if not totals:raise ValueError('No matching totals; not a successful reconciliation')
    source={'source_url':url,'dataset':f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}','member':names[0],'archive_bytes':total,'archive_sha256':None,'member_sha256':tracked.digest.hexdigest(),'member_bytes':tracked.count,'member_crc32':f'{info.CRC:08x}','http_bytes_read':remote.transferred+len(first),'totals':dict(totals),'rows_per_total':dict(lines),'generated_at':generation,'checked_at':audit['checked_at'],'method':audit['method']}
    votes[str(year)]=source;save(D/'votes-official.json',votes);audit['years'][str(year)]={'matched_totals':len(totals),'member_sha256':source['member_sha256'],'target_ids':len(targets)}
  except Exception as exc:audit['errors'].append({'year':year,'error':str(exc)})
 save(A/'votes-ranges.json',audit);print(json.dumps(audit,ensure_ascii=False,indent=2))
if __name__=='__main__':run()

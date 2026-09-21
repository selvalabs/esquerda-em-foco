"""Round 2: bounded, public-only collection. Does not modify any other edition."""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, importlib.util, io, json, re, time, unicodedata, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'data/rs'; A=ROOT/'docs/rs/review'; A.mkdir(parents=True,exist_ok=True)
NOW=datetime.now(timezone.utc).isoformat()
def load(path,default=None): return json.loads(path.read_text()) if path.exists() else default

def save(path,value): path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')).strip()
def get(url,limit=6_000_000):
 req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 EsquerdaEmFoco public-source-review','Accept':'*/*'})
 with urllib.request.urlopen(req,timeout=18) as r:
  raw=r.read(limit+1)
  if len(raw)>limit:raise ValueError('Response exceeds bounded size')
  return raw,r.geturl(),r.status,r.headers.get('Content-Type','')
spec=importlib.util.spec_from_file_location('ranges',ROOT/'tools/rs/votes_ranges.py'); ranges=importlib.util.module_from_spec(spec);spec.loader.exec_module(ranges)
def rs_csv(url):
 first,size=ranges.segment(url,0,255); remote=ranges.RangeFile(url,size)
 with zipfile.ZipFile(remote) as z:
  names=[n for n in z.namelist() if n.upper().endswith('_RS.CSV')]
  if len(names)!=1:raise ValueError('A unique RS member is required')
  member=names[0];raw=z.read(member)
  text=raw.decode('utf-8-sig') if raw.startswith(b'\xef\xbb\xbf') else raw.decode('latin-1')
  return list(csv.DictReader(io.StringIO(text),delimiter=';')),{'url':url,'member':member,'member_sha256':hashlib.sha256(raw).hexdigest(),'archive_sha256':None,'method':'Validated HTTP byte ranges; ZIP CRC; complete RS CSV SHA-256','checked_at':NOW,'http_bytes':remote.transferred+len(first)}

def run():
 records=load(D/'candidates-official.json',[]); ids={r['SQ_CANDIDATO'] for r in records}; normalized=load(D/'normalized.json',{})['candidates']
 if not (A/'baseline-matrix.json').exists():
  save(A/'baseline-matrix.json',{'baseline':'810a7896b3355254d50852761a41bae31ce3f567','checked_at':NOW,'candidates':[{'id':c['id'],'name':c['name'],'party':c['party'],'summary':bool(c['pautas']),'biography':bool(c.get('biography')),'current_office':c.get('current_office'),'history_previous':sum(h['year']<2026 for h in c['history']),'missing_vote_rows':sum(h['year']<2026 and h.get('votes') is None for h in c['history']),'invalid_url_count':len(c['invalid_declared_urls']),'status':c['status']} for c in normalized]})
 report={'checked_at':NOW,'sources':[],'errors':[],'scope_before':len(ids)}
 party_map={r['SG_PARTIDO'].upper():r['SG_PARTIDO'] for r in records};party_map['PCO']='PCO'
 base='https://cdn.tse.jus.br/estatistica/sead/odsele/'
 jobs=[('candidates-official.json',base+'consulta_cand/consulta_cand_2026.zip'),('status-official.json',base+'consulta_cand_complementar/consulta_cand_complementar_2026.zip'),('social-official.json',base+'consulta_cand/rede_social_candidato_2026.zip')]
 for filename,address in jobs:
  try:
   rows,evidence=rs_csv(address)
   original=load(D/filename,[]);allowed=set().union(*(r.keys() for r in original))
   if filename=='candidates-official.json':
    chosen=[r for r in rows if r.get('SG_UF')=='RS' and r.get('CD_CARGO')=='6' and r.get('ANO_ELEICAO')=='2026' and r.get('SG_PARTIDO','').upper() in party_map]
    found={r['SQ_CANDIDATO'] for r in chosen};report['added_ids']=sorted(found-ids);report['removed_ids']=sorted(ids-found)
    if found!=ids:raise ValueError('Scope IDs changed; manual reconciliation required before replacement')
    for r in chosen:r['SG_PARTIDO']=party_map[r['SG_PARTIDO'].upper()]
   else:chosen=[r for r in rows if r.get('SQ_CANDIDATO') in ids]
   cleaned=[{k:r.get(k,'') for k in sorted(allowed)} for r in chosen]
   if filename=='status-official.json' and {r['SQ_CANDIDATO'] for r in cleaned}!=ids:raise ValueError('Incomplete status refresh')
   save(D/filename,cleaned);evidence['selected_rows']=len(cleaned);report['sources'].append(evidence)
  except Exception as e:report['errors'].append({'stage':filename,'error':str(e)})
 profiles=load(D/'profiles-official.json',{})
 def profile(cid):
  address=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/RS/20322002026/candidato/{cid}'
  try:
   raw,final,status,ctype=get(address);p=json.loads(raw)
   if str(p.get('id'))!=cid:raise ValueError('ID mismatch')
   allowed=['id','nomeUrna','numero','nomeCompleto','descricaoSituacao','descricaoTotalizacao','ocupacao','cargo','partido','eleicao','sites','eleicoesAnteriores','st_REELEICAO','candidatoApto','isCandidatoInapto','descricaoSituacaoCandidato']
   return cid,{'data':{k:p[k] for k in allowed if k in p},'url':address,'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':NOW}
  except Exception as e:return cid,{'url':address,'error':str(e),'checked_at':NOW}
 successes=0
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for cid,result in pool.map(profile,sorted(ids)):
   if result.get('data'):profiles[cid]=result;successes+=1
   else:report['errors'].append({'stage':'profile','id':cid,**result})
 save(D/'profiles-official.json',profiles);report['profiles_refreshed']=successes
 # Verify the nine existing mandate claims against current institutional pages.
 offices=load(D/'offices-verified.json',{});checks=[]
 def office(item):
  cid,entry=item
  try:
   raw,final,status,ctype=get(entry['source']);soup=BeautifulSoup(raw,'html.parser');text=soup.get_text(' ',strip=True);c=next(r for r in records if r['SQ_CANDIDATO']==cid)
   name_ok=norm(c['NM_CANDIDATO']) in norm(text);current=('titular em exercicio' in norm(text) or 'suplente em exercicio' in norm(text))
   return {'id':cid,'url':entry['source'],'name_match':name_ok,'current_marker':current,'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':NOW,'verified':name_ok and current}
  except Exception as e:return {'id':cid,'url':entry['source'],'error':str(e),'verified':False,'checked_at':NOW}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:checks=list(pool.map(office,offices.items()))
 for check in checks:
  if check['verified']:offices[check['id']]['checked_at']=NOW
 save(D/'offices-verified.json',offices);save(A/'existing-offices-refresh.json',checks)
 # Inventory metadata only: do not publish full scraped pages or private registration fields.
 addresses=sorted({s['url'] for e in load(D/'editorial.json',{}).values() for s in e.get('sources',[])}|{s['url'] for c in normalized for s in c['sites'] if '@' not in urllib.parse.urlsplit(s['url']).netloc})
 def inspect(address):
  result={'url':address,'checked_at':NOW}
  try:
   raw,final,status,ctype=get(address);soup=BeautifulSoup(raw,'html.parser');result.update({'http_status':status,'final_url':final,'sha256':hashlib.sha256(raw).hexdigest(),'title':soup.title.get_text(' ',strip=True) if soup.title else None,'content_type':ctype})
   for x in soup.select('script,style,nav,header,footer'):x.decompose()
   text=soup.get_text(' ',strip=True);result['text_length']=len(text);result['name_matches']=[c['id'] for c in normalized if norm(c['name']) in norm(text)]
  except Exception as e:result['error']=str(e)
  return result
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:metadata=list(pool.map(inspect,addresses))
 save(A/'source-http-review.json',metadata)
 report['site_sources_checked']=len(metadata);report['completed_at']=datetime.now(timezone.utc).isoformat();save(A/'official-refresh.json',report)
 print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':run()

#!/usr/bin/env python3
"""Check declared and cited public URLs. HTTP success is not editorial verification.
Full extracted text is temporary: audit/source-extracts.json is git-ignored.
"""
from __future__ import annotations
import hashlib, json, re, time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'audit/review2'
def load(p,default=None): return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def tidy(value):
 value=str(value).strip(); value=re.sub(r'^HTTPS?://',lambda m:m[0].lower(),value)
 try:
  p=urlsplit(value);host=(p.hostname or '').lower()
  if p.scheme not in ('https','http') or not host or p.username:return None
  if host in ('localhost','127.0.0.1') or host.endswith('.local'):return None
  path=p.path
  if value.upper()==str(value):path=path.lower()
  if any(host==d or host.endswith('.'+d) for d in ('instagram.com','facebook.com','tiktok.com','threads.net')):path=path.lower()
  return urlunsplit((p.scheme,host,path,p.query,p.fragment))
 except ValueError:return None
def main():
 people=load(ROOT/'data/candidaturas.json')['candidates']; urls=defaultdict(set); origins=defaultdict(set)
 def add(value,sid,kind):
  u=tidy(value)
  if u: urls[u].add(sid);origins[u].add(kind)
 for p in people:
  for u in p.get('declared_links',[]):add(u,p['id'],'declared_channel')
  for field in ('topics_source','mandate_source'):
   if p.get(field):add(p[field],p['id'],field)
 old=load(ROOT/'editorial/perfis.json',{}).get('profiles',{})
 raw=load(OUT/'snapshot/universo-sc-2026.json',[]); byname={r['NM_URNA_CANDIDATO']:r['SQ_CANDIDATO'] for r in raw}
 for name,note in old.items():
  for field in ('topics_source','mandate_source','additional_source'):
   if note.get(field):add(note[field],byname.get(name,''),field)
 for sid,note in load(ROOT/'editorial/review2.json',{}).get('profiles',{}).items():
  for field in ('topics_source','biography_source','mandate_source'):
   if note.get(field):add(note[field],sid,field)
  for u in note.get('additional_sources',[]):add(u,sid,'additional_source')
 for item in load(ROOT/'editorial/review2-extra-sources.json',[]):
  for sid in item.get('candidate_ids',['']):add(item['url'],sid,item.get('kind','institution'))
 now=datetime.now(timezone.utc).isoformat();texts={}
 def fetch(url):
  meta={'url':url,'candidate_ids':sorted(urls[url]),'kinds':sorted(origins[url]),'checked_at':now};start=time.monotonic();text=''
  try:
   with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0 (compatible; EsquerdaEmFoco/2.0; public-source-review)','Accept':'text/html,application/xhtml+xml;q=0.9,*/*;q=0.1'}),timeout=15) as response:
    raw=response.read(1500001);meta.update(http_status=response.status,final_url=response.url,content_type=response.headers.get('Content-Type',''),sha256=hashlib.sha256(raw).hexdigest())
   if len(raw)>1500000:meta['state']='oversize_not_reviewed'
   elif 'pdf' in meta['content_type'].lower():meta['state']='pdf_requires_review'
   else:
    soup=BeautifulSoup(raw,'html.parser');meta['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
    for el in soup(['script','style','nav','footer','noscript','svg','form']):el.decompose()
    text=re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).strip()
    probe=(meta['title']+' '+text[:1200]).lower()
    blocked=('bot verification','verificação de segurança','verify you are human','just a moment','access denied','captcha','enable javascript and cookies','verifique se você é humano','pardon our interruption')
    if any(x in probe for x in blocked):meta['state']='blocked_not_verified';text=''
    elif len(text)<100:meta['state']='insufficient_text'
    elif any(x in meta.get('final_url','') for x in ('/accounts/login','/login.php','/checkpoint/')):meta['state']='login_required';text=''
    else:meta['state']='text_available_requires_editorial_review'
    meta['text_characters']=len(text)
    dates=re.findall(r'\b(?:20\d{2}-[01]\d-[0-3]\d|[0-3]?\d/[01]?\d/20\d{2})\b',text[:20000]);meta['dates_in_text']=list(dict.fromkeys(dates))[:10]
  except HTTPError as exc:
   meta.update(http_status=exc.code,state='not_found' if exc.code in (404,410) else 'blocked_not_verified' if exc.code in (401,403,406,429) else 'server_error',error=str(exc))
  except Exception as exc:meta.update(state='unavailable_at_check',error=str(exc))
  meta['seconds']=round(time.monotonic()-start,2)
  return meta,text
 reports=[]
 with ThreadPoolExecutor(max_workers=6) as pool:
  for meta,text in pool.map(fetch,sorted(urls)):
   reports.append(meta)
   if text:texts[meta['url']]={'metadata':meta,'text':text[:60000]}
 save(OUT/'link-checks.json',{'checked_at':now,'counts':dict(Counter(x['state'] for x in reports)),'links':reports,'rule':'Availability checks only. A 200 response or matching title does not establish any candidate claim.'})
 save(ROOT/'audit/source-extracts.json',texts)
 summary=[]
 for p in people:
  relevant=[x for x in reports if p['id'] in x['candidate_ids']]
  summary.append({'id':p['id'],'name':p['name'],'attempted_urls':len(relevant),'text_available':sum(x['state']=='text_available_requires_editorial_review' for x in relevant),'sources':[{'url':x['url'],'state':x['state'],'title':x.get('title','')} for x in relevant]})
 save(OUT/'source-coverage.json',summary)
 print(json.dumps({'urls_checked':len(reports),'states':dict(Counter(x['state'] for x in reports))},ensure_ascii=False,indent=2))
if __name__=='__main__':main()

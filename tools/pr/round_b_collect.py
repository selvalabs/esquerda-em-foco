"""Collect review-only public evidence. No automatic editorial classification.

Fetched texts stay in the temporary review artifact, never the public source tree.
Only HTTP(S), public hosts, bounded responses and same-site editorial links are read.
No authentication, social-platform scraping, donations, form submissions or private data.
"""
from __future__ import annotations
import argparse, concurrent.futures, hashlib, ipaddress, json, re, socket, threading, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
MAX_BYTES=2_000_000
SKIP_HOSTS={'instagram.com','facebook.com','fb.com','fb.me','m.facebook.com','youtube.com','youtu.be','tiktok.com','x.com','twitter.com','wa.me','wa.link','whatsapp.com','api.whatsapp.com','t.me','telegram.me','threads.net','threads.com','kwai.com','kwai-video.com','open.spotify.com','soundcloud.com','on.soundcloud.com','forms.gle','docs.google.com','queroapoiar.com.br','apoiaai.com.br','apoiar.me','vakinha.com.br','frameyu.com','twb.nz','twibbonize.com','giphy.com','ig.me','1drv.ms','mobilizaai.com.br','apoio.top','bsky.app'}
EDITORIAL=re.compile(r'propost|pautas|bandeiras|quem.sou|quem-e|biografia|trajet.ria|sobre.mim|compromiss|prioridad|lutas|plano.de|programa|hist.ria',re.I)
EMAIL=re.compile(r'[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}',re.I)
locks={};lock_guard=threading.Lock()
def now():return datetime.now(timezone.utc).isoformat()
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def host(url):return (urllib.parse.urlsplit(url).hostname or '').lower().removeprefix('www.')
def validate(url):
 p=urllib.parse.urlsplit(url)
 if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.port not in (None,80,443):raise ValueError('non-public or invalid URL')
 if p.hostname.endswith(('.local','.internal','.localhost')) or '.' not in p.hostname:raise ValueError('non-public hostname')
 addresses=socket.getaddrinfo(p.hostname,p.port or (443 if p.scheme=='https' else 80),type=socket.SOCK_STREAM)
 if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):raise ValueError('non-public resolved address')
 return url
class SafeRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):return super().redirect_request(req,fp,code,msg,headers,validate(newurl))
def fetch(url):
 result={'requested_url':url,'checked_at':now()}
 try:
  validate(url)
  with lock_guard:lock=locks.setdefault(host(url),threading.Lock())
  with lock:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (EsquerdaEmFoco public electoral research)','Accept':'text/html,application/json;q=0.8'})
   with urllib.request.build_opener(SafeRedirect()).open(req,timeout=12) as response:
    raw=response.read(MAX_BYTES+1);content_type=response.headers.get('Content-Type','');final=response.url;status=response.status
   time.sleep(.2)
  if len(raw)>MAX_BYTES:raise ValueError('response exceeds review limit')
  result.update({'final_url':final,'http_status':status,'content_type':content_type,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)})
  if 'html' not in content_type and not raw.lstrip().startswith((b'<!',b'<html',b'<HTML')):
   result['state']='non_html_not_reviewed';return result
  soup=BeautifulSoup(raw,'html.parser')
  result['title']=soup.title.get_text(' ',strip=True) if soup.title else ''
  result['published_at']=[m.get('content') for m in soup.select('meta[property="article:published_time"],meta[name="date"],meta[itemprop="datePublished"]') if m.get('content')]
  links=[]
  for a in soup.select('a[href]'):
   target=urllib.parse.urljoin(final,a['href']);label=a.get_text(' ',strip=True)
   if host(target)!=host(final) or not EDITORIAL.search(label+' '+target):continue
   if any(x in target.lower() for x in ('wp-login','admin','/feed','privacidade','privacy','logout','contato')):continue
   target=urllib.parse.urldefrag(target)[0]
   if target not in links:links.append(target)
  result['editorial_links']=links[:5]
  for node in soup.select('script,style,noscript,svg,header,footer,nav,form'):node.decompose()
  text='\n'.join(x for x in (line.strip() for line in soup.get_text('\n',strip=True).splitlines()) if x)
  result['review_text']=EMAIL.sub('[contato omitido]',text)[:55000]
  result['state']='read' if len(text.strip())>100 else 'insufficient_text'
  if re.search(r'verify you are human|checking your browser|just a moment|access denied|enable javascript and cookies',text[:1500],re.I):result['state']='access_barrier'
 except Exception as exc:result.update({'state':'access_error','error':str(exc)[:500]})
 return result

def main():
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);args=p.parse_args();out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
 candidates=json.loads((ROOT/'data/pr/normalized.json').read_text())['candidates'];editorial=json.loads((ROOT/'data/pr/editorial.json').read_text());urls={};ledger={}
 for c in candidates:
  selected=[];skipped=[]
  for item in c.get('sites',[])+c.get('socials',[])+editorial.get(c['id'],{}).get('sources',[]):
   u=item.get('url','');h=host(u)
   if not h or urllib.parse.urlsplit(u).scheme not in ('http','https'):continue
   if any(h==x or h.endswith('.'+x) for x in SKIP_HOSTS):skipped.append({'url':u,'state':'requires_manual_public_search'});continue
   if any(s in u.lower() for s in ('/privacidade','/privacy','/painel','/login','/admin')):continue
   if u not in selected:selected.append(u)
  for u in selected[:6]:urls.setdefault(u,set()).add(c['id'])
  ledger[c['id']]={'name':c['name'],'full_name':c['full_name'],'party':c['party'],'office_code':c['office_code'],'initial_sources':selected[:6],'manual_channels':skipped,'editorial_complete':False,'note':'Source access does not establish identity or substantiate a theme; manual review is required.'}
 results={}
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
  for r in pool.map(fetch,urls):results[r['requested_url']]=r
 follow={}
 for u,r in list(results.items()):
  if r.get('state')!='read':continue
  for link in r.get('editorial_links',[])[:3]:
   if link not in results:follow.setdefault(link,set()).update(urls[u])
 with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
  for r in pool.map(fetch,follow):results[r['requested_url']]=r
 for u,ids in follow.items():urls.setdefault(u,set()).update(ids)
 for cid,item in ledger.items():
  item['access_results']=[{'url':u,'state':results[u]['state'],'sha256':results[u].get('sha256'),'checked_at':results[u]['checked_at'],'title':results[u].get('title'),'error':results[u].get('error')} for u,ids in urls.items() if cid in ids]
 save(out/'declared-source-review.json',{'generated_at':now(),'results':results,'candidate_ledger':ledger})
 # Snapshot official current directories, and bounded legislative lists for the named PR deputies.
 institutional={}
 for label,u in {'alep':'https://www.assembleia.pr.leg.br/deputados/representacao-partidaria','camara':'https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=PR&itens=100&ordem=ASC&ordenarPor=nome'}.items():
  if label=='alep':institutional[label]=fetch(u)
  else:
   try:
    with urllib.request.urlopen(urllib.request.Request(u,headers={'Accept':'application/json','User-Agent':'EsquerdaEmFoco'}),timeout=20) as response:raw=response.read(MAX_BYTES)
    institutional[label]={'url':u,'checked_at':now(),'sha256':hashlib.sha256(raw).hexdigest(),'data':json.loads(raw)}
   except Exception as exc:institutional[label]={'url':u,'error':str(exc),'checked_at':now()}
 save(out/'institutional-directories.json',institutional)
 print(json.dumps({'candidates':len(ledger),'urls':len(results),'read':sum(r['state']=='read' for r in results.values()),'access_errors':sum(r['state']=='access_error' for r in results.values()),'output':str(out)},ensure_ascii=False))
if __name__=='__main__':main()

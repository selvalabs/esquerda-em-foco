#!/usr/bin/env python3
"""Read explicitly identified public pages with normal browser navigation.
No login, challenge bypass, stealth settings or form submissions. Full text stays
in the ignored review artifact; published audit retains only provenance metadata.
"""
from __future__ import annotations
import asyncio, hashlib, json, re
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from playwright.async_api import async_playwright
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'audit/review2'
def load(p,default=None):return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def tidy(s):
 try:
  p=urlsplit(str(s).strip());host=(p.hostname or '').lower()
  if p.scheme.lower() not in ('http','https') or not host or p.username:return None
  return urlunsplit((p.scheme.lower(),host,p.path,p.query,p.fragment))
 except ValueError:return None
SOCIAL=('instagram.com','facebook.com','tiktok.com','x.com','twitter.com','threads.net','threads.com','linkedin.com','youtube.com','youtu.be','bsky.app','wa.me','whatsapp.com','t.me','telegram.me')
def social(u):
 host=urlsplit(u).hostname or ''
 return any(host==d or host.endswith('.'+d) for d in SOCIAL)
async def main():
 now=datetime.now(timezone.utc).isoformat(); urls=defaultdict(set); kinds=defaultdict(set)
 def add(u,sid,kind):
  u=tidy(u)
  if u and not social(u):urls[u].add(sid);kinds[u].add(kind)
 # Preserve path/query case from the fresh TSE file, rather than old renderer URLs.
 networks=load(OUT/'snapshot/redes-sc-2026.json',[])
 for r in networks:add(r['DS_URL'],r['SQ_CANDIDATO'],'declared_site')
 people=load(ROOT/'data/candidaturas.json')['candidates']
 for p in people:
  for field in ('topics_source','mandate_source'):
   if p.get(field):add(p[field],p['id'],field)
 for sid,note in load(ROOT/'editorial/review2.json',{}).get('profiles',{}).items():
  for field in ('topics_source','biography_source','mandate_source'):
   if note.get(field):add(note[field],sid,field)
 for item in load(ROOT/'editorial/review2-extra-sources.json',[]):
  for sid in item.get('candidate_ids',['']):add(item['url'],sid,item.get('kind','institution'))
 extracts=load(ROOT/'audit/source-extracts.json',{}); reports=[]; queue=list(urls)
 async with async_playwright() as pw:
  browser=await pw.chromium.launch()
  context=await browser.new_context(locale='pt-BR',viewport={'width':1280,'height':900})
  sem=asyncio.Semaphore(4)
  async def read(url):
   async with sem:
    page=await context.new_page();m={'url':url,'candidate_ids':sorted(urls[url]),'kinds':sorted(kinds[url]),'checked_at':now,'method':'normal Chromium public-page navigation'}
    try:
     response=await page.goto(url,wait_until='domcontentloaded',timeout=20000)
     await page.wait_for_timeout(1500)
     m.update(http_status=response.status if response else None,final_url=page.url,title=await page.title())
     text=await page.locator('body').inner_text(timeout=5000)
     probe=(m['title']+' '+text[:1200]).lower()
     blocked=('bot verification','verificação de segurança','verify you are human','just a moment','access denied','captcha','enable javascript and cookies','verifique se você é humano','pardon our interruption')
     if any(x in probe for x in blocked):m['state']='blocked_not_verified'
     elif m['http_status'] in (404,410):m['state']='not_found'
     elif m['http_status'] and m['http_status']>=400:m['state']='http_error'
     elif len(text)<150:m['state']='insufficient_text'
     elif '/aviso-periodo-eleitoral' in page.url:m['state']='electoral_period_notice'
     else:
      m['state']='text_available_requires_editorial_review'
      anchors=await page.locator('a[href]').evaluate_all('(els)=>els.map(a=>({url:a.href,text:a.innerText.trim()})).filter(a=>a.text)')
      anchors=[a for a in anchors if tidy(a['url'])][:250]
      m['text_sha256']=hashlib.sha256(text.encode()).hexdigest();m['text_characters']=len(text)
      extracts[url]={'metadata':m,'text':text[:75000],'anchors':anchors}
    except Exception as exc:m.update(state='unavailable_at_check',error=str(exc)[:700])
    finally:await page.close()
    reports.append(m);print(m.get('http_status'),m['state'],url,flush=True)
  await asyncio.gather(*(read(u) for u in queue))
  await context.close();await browser.close()
 save(ROOT/'audit/source-extracts.json',extracts)
 save(OUT/'browser-sources.json',{'checked_at':now,'urls':len(reports),'states':dict(Counter(r['state'] for r in reports)),'sources':reports,'rule':'Content availability is not editorial verification; titles and snippets alone do not establish claims.'})
if __name__=='__main__':asyncio.run(main())

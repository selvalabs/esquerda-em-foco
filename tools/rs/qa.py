"""Actual HTTP browser checks, served below both a Pages prefix and a VPS root."""
from __future__ import annotations
import functools, hashlib, http.server, json, os, threading
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/rs';SHOTS=OUT/'screenshots';SHOTS.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  prefix='/esquerda-em-foco/'
  if self.path.startswith(prefix):self.path='/'+self.path[len(prefix):]
  return super().do_GET()
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)));threading.Thread(target=server.serve_forever,daemon=True).start()
origin=f'http://127.0.0.1:{server.server_port}';url=origin+'/esquerda-em-foco/rs/deputados-federais/'
report={'checked_at':datetime.now(timezone.utc).isoformat(),'engine':'Chromium','checks':[],'viewports':[],'errors':[]}
def check(name,condition,details=None):
 report['checks'].append({'name':name,'passed':bool(condition),'details':details})
 if not condition:raise AssertionError(name+': '+str(details))
def no_overflow(page,name):
 sizes=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth})');check(name,sizes['scroll']<=sizes['width']+1 and sizes['body']<=sizes['width']+1,sizes)
def state(page):return page.eval_on_selector_all('.party-section','ss=>ss.map(s=>({party:s.dataset.partySection,cards:[...s.querySelectorAll(".candidate")].map(c=>c.dataset.tseId)}))')
try:
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True,executable_path=os.getenv('CHROMIUM_EXECUTABLE') or None,args=['--no-sandbox'])
  for width in [320,360,390,430,768,1024,1440]:
   context=browser.new_context(viewport={'width':width,'height':900 if width>=768 else 844},timezone_id='America/Sao_Paulo',reduced_motion='reduce')
   context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort())
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   response=page.goto(url,wait_until='domcontentloaded');page.wait_for_timeout(350)
   check(f'HTTP 200 {width}',response.status==200);check(f'107 cards {width}',page.locator('.candidate').count()==107);no_overflow(page,f'header overflow {width}')
   check(f'no JavaScript errors {width}',not errors,errors)
   if width in (390,1440):page.screenshot(path=str(SHOTS/f'header-{width}.png'))
   page.locator('.candidate').first.evaluate("e=>e.scrollIntoView({block:'start'})");page.wait_for_timeout(100);no_overflow(page,f'card overflow {width}')
   check(f'navbar sticky {width}',abs(page.locator('#siteNav').bounding_box()['y'])<=1)
   if width in (390,1440):page.screenshot(path=str(SHOTS/f'card-{width}.png'))
   page.locator('.rs-history summary').first.click();no_overflow(page,f'expanded history overflow {width}')
   if width in (390,1440):page.screenshot(path=str(SHOTS/f'history-{width}.png'))
   page.evaluate('window.scrollTo(0,document.documentElement.scrollHeight)');page.wait_for_timeout(100);no_overflow(page,f'footer overflow {width}')
   if width in (390,1440):page.screenshot(path=str(SHOTS/f'footer-{width}.png'))
   page.locator('#searchInput').fill('tiago dominguez');check(f'name search {width}',page.locator('.candidate:visible').count()>=1 and page.locator('#candidato-210002533914').is_visible())
   page.locator('#searchInput').fill('5075');check(f'number search {width}',page.locator('#candidato-210002533914').is_visible())
   page.locator('#searchInput').fill('agroecologia');check(f'platform search {width}',page.locator('.candidate:visible').count()>=1)
   page.locator('#searchInput').fill('PDT');check(f'party search {width}',page.locator('.candidate[data-party="PDT"]:visible').count()==32)
   page.locator('#searchInput').fill('zzzz-sem-candidato-xyz');check(f'empty result {width}',page.locator('.candidate:visible').count()==0 and page.locator('#emptyResults').is_visible());check(f'counter zero {width}',page.locator('#resultCount').text_content()=='0 resultados')
   page.locator('#searchInput').fill('');check(f'reset search {width}',page.locator('.candidate:visible').count()==107)
   if width<=760:
    menu=page.locator('#siteNavMenu');menu.click();check(f'menu opens {width}',menu.get_attribute('aria-expanded')=='true' and page.locator('#siteNavLinks').is_visible());no_overflow(page,f'menu overflow {width}')
    page.keyboard.press('Escape');check(f'Escape closes menu {width}',menu.get_attribute('aria-expanded')=='false')
    menu.click();page.locator('#siteNavLinks a[href="#sobre-levantamento"]').click();check(f'menu selection closes {width}',menu.get_attribute('aria-expanded')=='false');check(f'about anchor opens {width}',page.locator('#sobre-levantamento').get_attribute('open') is not None)
    menu.click();page.locator('.overview-copy h2').click();check(f'outside click closes {width}',menu.get_attribute('aria-expanded')=='false')
   page.goto(url+'#candidato-210002535928',wait_until='domcontentloaded');page.wait_for_timeout(200)
   target=page.locator('#candidato-210002535928');box=target.bounding_box();check(f'direct candidate link {width}',box['y']<700 and box['y']+box['height']>0,box)
   page.reload(wait_until='domcontentloaded');page.wait_for_timeout(150);check(f'direct link reload {width}',target.bounding_box()['y']<700)
   check(f'no errors after interactions {width}',not errors,errors);report['viewports'].append({'width':width,'passed':True});context.close()
  context=browser.new_context(viewport={'width':1440,'height':900});context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort());page=context.new_page();page.goto(url,wait_until='domcontentloaded')
  images=page.evaluate('''async()=>await Promise.all([...document.querySelectorAll('img.candidate-photo')].map(el=>new Promise(resolve=>{const img=new Image();img.onload=()=>resolve({url:el.getAttribute('src'),ok:img.naturalWidth>0});img.onerror=()=>resolve({url:el.getAttribute('src'),ok:false});img.src=el.src;})))''')
  check('107 official photographs decode',len(images)==107 and all(i['ok'] for i in images),{'total':len(images),'failed':[i for i in images if not i['ok']]})
  page.goto(origin+'/rs/deputados-federais/',wait_until='domcontentloaded');check('VPS root route',page.title().startswith('Candidatos a Deputado Federal no RS'))
  for name in ['dados.json','fontes.json','sitemap.xml','site.webmanifest','assets/og-rs.png','favicon.svg']:
   response=context.request.get(url+name);check('local resource '+name,response.status==200)
  context.close();orders=[]
  for date in ['2026-09-21T15:00:00Z','2026-09-22T15:00:00Z','2026-09-22T02:59:00Z']:
   context=browser.new_context(viewport={'width':1024,'height':768},timezone_id='Asia/Tokyo');context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) else route.abort());page=context.new_page()
   page.clock.set_fixed_time(datetime.fromisoformat(date.replace('Z','+00:00')));page.goto(url,wait_until='domcontentloaded');before=state(page);page.reload(wait_until='domcontentloaded');check('stable reload '+date,before==state(page));orders.append(before);context.close()
  first,second,before_midnight=orders;check('rotation of parties by one',[x['party'] for x in second]==[x['party'] for x in first[1:]+first[:1]])
  mapping={x['party']:x['cards'] for x in first}
  for entry in second:
   old=mapping[entry['party']];check('candidate rotation '+entry['party'],entry['cards']==old[1:]+old[:1])
  check('Brasilia date independent of client timezone',before_midnight==first);browser.close()
 check('SC remains byte-identical',hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest()=='4b7f82c4e8dc95e54ec3e3be2a9954f81d06b0edceb530e900aebe68cd2c36ea')
except Exception as exc:report['errors'].append(str(exc))
finally:
 server.shutdown();report['passed']=not report['errors'] and all(c['passed'] for c in report['checks']);report['checks_run']=len(report['checks']);(OUT/'browser-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
if not report['passed']:raise SystemExit(1)

"""Real-browser acceptance tests against the generated static routes."""
from __future__ import annotations
import functools, http.server, json, threading, traceback
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/pr/qa';OUT.mkdir(parents=True,exist_ok=True)
DATA=json.loads((ROOT/'data/pr/normalized.json').read_text())['candidates']
report={'checked_at':datetime.now(timezone.utc).isoformat(),'checks':[],'browser_errors':[],'http_errors':[],'passed':False}
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}'
def check(name,condition,detail=None):
 report['checks'].append({'name':name,'pass':bool(condition),'detail':detail})
 assert condition,name+': '+str(detail)
def count(page):return page.locator('article.candidate:not([hidden])').count()
def clear(page):
 expected=page.locator('article.candidate').count();page.locator('#clearFilters').click();page.wait_for_function('(n)=>document.documentElement.dataset.visibleCount === String(n)',expected)
def run():
 with sync_playwright() as p:
  browser=p.chromium.launch(headless=True)
  context=browser.new_context(viewport={'width':1440,'height':1000},reduced_motion='reduce')
  context.route('https://fonts.googleapis.com/**',lambda route:route.abort())
  context.route('https://fonts.gstatic.com/**',lambda route:route.abort())
  for code,slug in [(6,'deputados-federais'),(7,'deputados-estaduais')]:
   records=[c for c in DATA if c['office_code']==code];page=context.new_page();url=base+'/pr/'+slug+'/'
   page.on('pageerror',lambda err:report['browser_errors'].append(str(err)))
   page.on('response',lambda response:report['http_errors'].append({'url':response.url,'status':response.status}) if response.url.startswith(base) and response.status>=400 else None)
   response=page.goto(url,wait_until='networkidle');check(slug+': HTTP 200',response.status==200)
   check(slug+': initial full census',count(page)==len(records),count(page))
   for width,height in [(360,800),(390,844),(768,1024),(1440,1000)]:
    page.set_viewport_size({'width':width,'height':height});page.wait_for_timeout(100)
    sizes=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
    check(slug+f': viewport {width}',max(sizes['document'],sizes['body'])<=width+1,sizes)
    if width in (390,1440):page.screenshot(path=str(OUT/f'{slug}-{width}.png'))
   page.set_viewport_size({'width':1440,'height':1000})
   for party in sorted({c['party'] for c in records}):
    page.select_option('#partyFilter',party);check(slug+': party '+party,count(page)==sum(c['party']==party for c in records))
   clear(page)
   for group in ('apta','inapta'):
    page.select_option('#statusFilter',group);check(slug+': aptitude '+group,count(page)==sum(c['status_group']==group for c in records))
   clear(page)
   for flag in ('true','false'):
    page.select_option('#mandateFilter',flag);check(slug+': office '+flag,count(page)==sum(bool(c['current_office'])==(flag=='true') for c in records))
   clear(page)
   for flag in ('true','false'):
    page.select_option('#historyFilter',flag);check(slug+': history '+flag,count(page)==sum(bool(c['history'])==(flag=='true') for c in records))
   clear(page)
   for region in sorted({c['region']['label'] for c in records if c.get('region')}):
    page.select_option('#regionFilter',region);check(slug+': documented region '+region,count(page)==sum(c.get('region',{}).get('label')==region for c in records if c.get('region')))
   clear(page)
   page.fill('#searchInput','zzzzzz-sem-correspondencia-2026');check(slug+': empty search',count(page)==0 and page.locator('#emptyResults').is_visible())
   clear(page)
   sample=next(c for c in records if len(c['themes'])>=2);selected=[t['id']for t in sample['themes'][:2]]
   for theme in selected:page.locator('button[data-theme="'+theme+'"]').click()
   expected=sum(set(selected)<={t['id']for t in c['themes']}for c in records)
   check(slug+': AND themes',count(page)==expected,{'actual':count(page),'expected':expected})
   check(slug+': shareable theme URL','pautas='in page.url)
   page.reload(wait_until='networkidle');check(slug+': URL reload restores filters',count(page)==expected)
   clear(page)
   page.fill('#searchInput',sample['number']);check(slug+': exact number includes identity',page.locator('#candidato-'+sample['id']).is_visible())
   clear(page)
   other=next(c['party']for c in records if c['party']!=sample['party'])
   page.goto(url+'?partido='+other+'#candidato-'+sample['id'],wait_until='networkidle')
   check(slug+': direct profile anchor overrides conflicting filters',page.locator('#candidato-'+sample['id']).is_visible())
   card=page.locator('#candidato-'+sample['id']);card.scroll_into_view_if_needed();page.screenshot(path=str(OUT/f'{slug}-card-1440.png'))
   page.goto(url+'?partido=UNKNOWN&pautas=unknown-theme&situacao=invalid',wait_until='networkidle');check(slug+': unknown URL values ignored',count(page)==len(records))
   page.set_viewport_size({'width':390,'height':844});page.goto(url,wait_until='networkidle')
   menu=page.locator('#siteNavMenu');check(slug+': mobile menu visible',menu.is_visible())
   menu.click();check(slug+': menu opens',menu.get_attribute('aria-expanded')=='true')
   page.keyboard.press('Escape');check(slug+': Escape closes menu',menu.get_attribute('aria-expanded')=='false')
   # The heading is covered by the dropdown; click a visible region genuinely outside it.
   menu.click();page.locator('.masthead .meta').click();check(slug+': outside closes menu',menu.get_attribute('aria-expanded')=='false')
   page.goto(url+'#candidato-'+sample['id'],wait_until='networkidle');page.screenshot(path=str(OUT/f'{slug}-card-390.png'))
   bounds=page.locator('#candidato-'+sample['id']).bounding_box();check(slug+': mobile card containment',bounds['x']>=-1 and bounds['x']+bounds['width']<=391,bounds)
   dates=page.evaluate("[EEFPR.dateInBrazil(new Date('2026-09-22T02:59:59Z')),EEFPR.dateInBrazil(new Date('2026-09-22T03:00:00Z'))]")
   check(slug+': São Paulo midnight boundary',dates==['2026-09-21','2026-09-22'],dates)
   rotation=page.evaluate('EEFPR.rotate([1,2,3],-1)');check(slug+': rotation preserves exact membership',rotation==[3,1,2])
   for c in records:
    photo=page.request.get(base+'/pr/assets/photos/'+c['id']+'.webp');check(slug+': portrait '+c['id'],photo.status==200)
   for resource in ('dados.json','candidaturas.csv','fontes.json','auditoria.json','sitemap.xml'):
    check(slug+': download '+resource,page.request.get(url+resource).status==200)
   page.close()
  check('Paraná index route',context.request.get(base+'/pr/').status==200)
  check('No browser exceptions',not report['browser_errors'],report['browser_errors'])
  check('No local HTTP errors',not report['http_errors'],report['http_errors'])
  report['passed']=True;browser.close()
try:run()
except Exception:
 report['failure']=traceback.format_exc();raise
finally:
 server.shutdown();(OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':report['passed'],'checks':len(report['checks']),'browser_errors':report['browser_errors'],'http_errors':report['http_errors']},ensure_ascii=False))

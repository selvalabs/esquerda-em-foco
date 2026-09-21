"""Responsive browser tests; the existing federal page remains read-only."""
from pathlib import Path
import functools,hashlib,http.server,json,os,threading
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent; OUT=ROOT/'audit'; SHOTS=OUT/'screenshots'; SHOTS.mkdir(parents=True,exist_ok=True)
report={'checks':[],'viewports':[]}
def check(name,ok,detail=None):
 report['checks'].append({'name':name,'passed':bool(ok),'detail':detail})
 print(name,ok,detail,flush=True)
original=hashlib.sha256((REPO/'index.html').read_bytes()).hexdigest()
data=json.loads((ROOT/'data/candidaturas.json').read_text()); people=data['candidates']; soup=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
check('profile count',len(soup.select('article.candidate'))==len(people))
check('unique ids',len({p['id'] for p in people})==len(people))
check('five digit numbers',all(len(p['number'])==5 and p['number'].isdigit() for p in people))
check('one heading',len(soup.find_all('h1'))==1)
check('canonical',soup.select_one('link[rel=canonical]')['href'].endswith('/deputados-estaduais/'))
check('clean displayed values',not any(x in soup.get_text() for x in ['#NE','#NULO']))
class Quiet(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args): pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(REPO)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/deputados-estaduais/'
with sync_playwright() as p:
 opts={'headless':True,'args':['--no-sandbox']}
 if os.path.exists('/usr/bin/chromium'): opts['executable_path']='/usr/bin/chromium'
 browser=p.chromium.launch(**opts)
 for width,height in [(360,800),(390,844),(768,1024),(1440,1000)]:
  page=browser.new_page(viewport={'width':width,'height':height}); errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(url,wait_until='networkidle'); page.emulate_media(reduced_motion='reduce'); page.wait_for_timeout(150)
  overflow=page.evaluate('({width:innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
  check(f'width {width}',max(overflow['doc'],overflow['body'])<=width+1,overflow)
  page.screenshot(path=str(SHOTS/f'hero-{width}.png'))
  page.locator('.candidate').first.scroll_into_view_if_needed(); page.screenshot(path=str(SHOTS/f'cards-{width}.png'))
  check(f'sticky {width}',abs(page.locator('#siteNav').bounding_box()['y'])<2)
  page.locator('#searchInput').fill('13601'); check(f'number search {width}',page.locator('.candidate:visible').count()==1)
  page.locator('#searchInput').fill('luciane'); check(f'name search {width}',page.locator('.candidate:visible').count()==1)
  page.locator('#resetFilters').click(); page.locator('#partyFilter').select_option('PCDOB')
  check(f'party filter {width}',page.locator('.candidate:visible').count()==sum(x['party_code']=='PCDOB' for x in people))
  page.locator('#resetFilters').click(); page.locator('#trajectoryFilter').select_option('first')
  check(f'history filter {width}',page.locator('.candidate:visible').count()==data['counts']['first_in_linked_history'])
  page.locator('#searchInput').fill('zzzznone998'); check(f'empty state {width}',page.locator('#emptyState').is_visible())
  page.locator('#emptyReset').click(); check(f'reset {width}',page.locator('.candidate:visible').count()==len(people))
  first=page.locator('.candidate').first; first.locator('.state-history > summary').click(); check(f'details {width}',first.locator('.state-history').evaluate('(e)=>e.open'))
  if width<=760:
   page.locator('#siteNavMenu').click(); check(f'menu open {width}',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='true')
   page.keyboard.press('Escape'); check(f'menu close {width}',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='false')
  page.goto(url+'#candidato-240002540083',wait_until='networkidle'); page.wait_for_timeout(200)
  check(f'deep link {width}',page.locator('#candidato-240002540083').is_visible())
  check(f'javascript {width}',not errors,errors)
  report['viewports'].append(overflow); page.close()
 browser.close()
server.shutdown()
check('federal unchanged',hashlib.sha256((REPO/'index.html').read_bytes()).hexdigest()==original,original)
report['passed']=all(x['passed'] for x in report['checks']); report['coverage']=data['counts']
(OUT/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
if not report['passed']: raise SystemExit(1)

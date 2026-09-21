"""Additional browser checks for changed cards; no external requests."""
import functools,http.server,json,os,threading
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/rs/fed03';SHOTS=OUT/'screenshots';SHOTS.mkdir(parents=True,exist_ok=True)
class Handler(http.server.SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start();origin=f'http://127.0.0.1:{server.server_port}'
report={'checked_at':datetime.now(timezone.utc).isoformat(),'checks':[],'errors':[]}
def check(name,ok,details=None):
 report['checks'].append({'name':name,'passed':bool(ok),'details':details})
 if not ok:raise AssertionError(name)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path=os.getenv('CHROMIUM_EXECUTABLE') or None,args=['--no-sandbox'])
  for width in (320,390,1440):
   context=browser.new_context(viewport={'width':width,'height':844},timezone_id='America/Sao_Paulo',reduced_motion='reduce')
   context.route('**/*',lambda r:r.continue_() if r.request.url.startswith(origin) else r.abort())
   page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   page.goto(origin+'/rs/deputados-federais/',wait_until='domcontentloaded')
   for cid in ('210002537050','210002535907','210002535917','210002537042','210002534586'):
    card=page.locator('#candidato-'+cid);card.evaluate("e=>{e.scrollIntoView({block:'start'});e.querySelectorAll('details').forEach(d=>d.open=true)}")
    sizes=page.evaluate('({width:innerWidth,html:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
    check(f'changed card {cid} width {width}',sizes['html']<=width+1 and sizes['body']<=width+1,sizes)
   check(f'identity conflict note {width}','divergência de nome civil' in page.locator('#candidato-210002537042').inner_text())
   check(f'recovered votes note {width}','15.473 votos nominais' in page.locator('#candidato-210002535917').inner_text())
   check(f'inapt historical note {width}','não descreve a candidatura de 2026' in page.locator('#candidato-210002534586').inner_text())
   check(f'no script errors {width}',not errors,errors)
   page.locator('#candidato-210002535907').evaluate("e=>e.scrollIntoView({block:'start'})");page.screenshot(path=str(SHOTS/f'new-office-{width}.png'))
   page.locator('#candidato-210002537042').evaluate("e=>e.scrollIntoView({block:'start'})");page.screenshot(path=str(SHOTS/f'history-conflict-{width}.png'))
   context.close()
  browser.close()
except Exception as exc:report['errors'].append(str(exc))
finally:
 server.shutdown();report['passed']=not report['errors'];report['checks_run']=len(report['checks']);(OUT/'browser-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
if not report['passed']:raise SystemExit(1)

"""Visual-structure gates missed by overflow-only tests. Isolated prototype only.
Viewport captures are unmodified. Element captures hide only the unrelated fixed
footer during the screenshot, so a long card does not have that bar stamped on it.
"""
from __future__ import annotations
import argparse,functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
CHECKS=[]
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def run(prototype,out):
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(prototype)))
 threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_address[1]}/'
 cases=json.loads((prototype/'audit/cases.json').read_text());chosen={}
 for case in cases:chosen.setdefault(case['edition_id'],case)
 shots=out/'screenshots';shots.mkdir(parents=True,exist_ok=True)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();ctx=browser.new_context(reduced_motion='reduce');ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url.startswith('data:') else r.abort())
   page=ctx.new_page();page.set_default_timeout(12000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   for eid,case in chosen.items():
    for width in (320,360,390,430,768,1024,1440):
     page.set_viewport_size({'width':width,'height':960});page.goto('about:blank');page.goto(base+case['path'],wait_until='domcontentloaded')
     page.wait_for_function("typeof EEFQueryUI==='object'&&typeof EEFCollectionUI==='object'")
     card=page.locator('#candidato-'+case['candidate_id']);card.evaluate('(e)=>e.scrollIntoView({block:"start"})')
     geometry=card.evaluate('''c=>{
       const rect=s=>{const r=c.querySelector(s).getBoundingClientRect();return {top:r.top,bottom:r.bottom,width:r.width,height:r.height};};
       const number=c.querySelector('.number'), nr=number.getBoundingClientRect();
       return {context:rect('.cc-context'),header:rect('header'),nav:rect('.cc-card-nav'),reading:rect('.cc-reading-title'),number:{height:nr.height,line:parseFloat(getComputedStyle(number).lineHeight)},width:innerWidth,scroll:document.documentElement.scrollWidth};
     }''')
     check(eid+f' ordered reading {width}',geometry['context']['bottom']<=geometry['header']['top']+1 and geometry['header']['bottom']<=geometry['nav']['top']+1 and geometry['nav']['bottom']<=geometry['reading']['top']+1,geometry)
     check(eid+f' number not wrapped {width}',geometry['number']['height']<=geometry['number']['line']*1.65,geometry['number'])
     check(eid+f' page width {width}',geometry['scroll']<=width+1)
     for selector in ('.cc-history','.cc-channels'):
      if card.locator(selector).count():
       d=card.locator(selector);d.locator(':scope>summary').click()
       check(eid+f' expanded {selector} {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
       d.locator(':scope>summary').click()
     if width in (390,1440):
      card.evaluate('(e)=>e.scrollIntoView({block:"start"})');page.wait_for_timeout(80)
      page.screenshot(path=str(shots/(eid+f'-viewport-{width}.png')))
      card.screenshot(path=str(shots/(eid+f'-card-{width}.png')),style='.persistent-footer{visibility:hidden!important}')
      d=card.locator('.cc-transparency');d.locator(':scope>summary').click()
      d.screenshot(path=str(shots/(eid+f'-provenance-{width}.png')),style='.persistent-footer{visibility:hidden!important}')
      d.locator(':scope>summary').click()
   check('no page errors',not errors,errors);ctx.close();browser.close()
 finally:server.shutdown()
def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 try:run(a.prototype,a.out)
 except Exception as e:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(e)});raise
 finally:(a.out/'layout.json').write_text(json.dumps({'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,'capture_note':'Viewport screenshots are unmodified. Element screenshots temporarily hide the unrelated fixed footer only. No source/runtime is changed for this capture.'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

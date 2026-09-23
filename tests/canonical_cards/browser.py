"""Actual Chromium integration on isolated output: all six editions, no deployment."""
from __future__ import annotations
import argparse,functools,json,sys,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import save
CHECKS=[]
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def run(prototype,out):
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(prototype)))
 threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_address[1]}/'
 editions=json.loads((ROOT/'config/editions.json').read_text())['editions'];cases=json.loads((prototype/'audit/cases.json').read_text());screens=out/'screenshots';screens.mkdir(parents=True,exist_ok=True)
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch();ctx=browser.new_context(reduced_motion='reduce');ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url.startswith('data:') else r.abort())
   g=ctx.new_page();g.set_default_timeout(12000);errors=[];g.on('pageerror',lambda e:errors.append(str(e)))
   def start(path):
    g.goto('about:blank');g.goto(base+path,wait_until='domcontentloaded');g.wait_for_function("typeof EEFQueryUI==='object'&&typeof EEFCollectionUI==='object'")
   for e in editions:
    if e['publication_status']!='published':continue
    eid=e['edition_id'];selected=[c for c in cases if c['edition_id']==eid]
    for width in [320,360,390,430,768,1024,1440]:
     g.set_viewport_size({'width':width,'height':960});start(e['entrypoint'])
     check(eid+f' width {width}',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
     check(eid+f' one original per ID {width}',g.evaluate('(()=>{const a=[...document.querySelectorAll("[id]")].map(x=>x.id);return a.length===new Set(a).size})()'))
    for case in selected:
     start(case['path']);cid=case['candidate_id'];card=g.locator('#candidato-'+cid)
     check(eid+' case '+cid+' context',card.locator('.cc-context').inner_text().endswith('Eleição 2026'))
     card.locator('.cc-transparency>summary').click();check(cid+' context opens',card.locator('.cc-transparency').evaluate('(e)=>e.open'))
     check(cid+' no raw identity in UI',eid+':'+cid not in card.inner_text())
     card.locator('.cc-transparency>summary').click()
     if card.locator('.cc-proof').count():
      proof=card.locator('.cc-proof');proof.locator(':scope>summary').click();buttons=proof.locator('[data-cc-topic]')
      if buttons.count():
       b=buttons.first;topic=b.get_attribute('data-cc-topic');b.click();check(cid+' evidence focus retained',b.evaluate('(e)=>e===document.activeElement'))
       visible=proof.locator('[data-cc-evidence]:not([hidden])').evaluate_all('(xs)=>xs.map(x=>x.dataset.ccTopics.split(" "))')
       check(cid+' evidence is pertinent',bool(visible) and all(topic in ts for ts in visible))
       proof.locator('[data-cc-reset]').click();check(cid+' all evidence restorable',proof.locator('[data-cc-evidence][hidden]').count()==0)
      proof.locator(':scope>summary').click()
    rich=selected[0];cid=rich['candidate_id'];start(rich['path']);card=g.locator('#candidato-'+cid)
    for width in [390,1440]:
     g.set_viewport_size({'width':width,'height':960});card.evaluate('(e)=>e.scrollIntoView({block:"start"})');g.wait_for_timeout(80)
     card.screenshot(path=str(screens/(eid+f'-card-{width}.png')))
    # Existing query and collection must operate on the exact same article node.
    g.evaluate('window.originalPrototypeCard=document.getElementById(arguments[0])' if False else '(id)=>window.originalPrototypeCard=document.getElementById(id)','candidato-'+cid)
    g.locator('#searchInput').fill(card.locator('h3').inner_text());g.wait_for_timeout(100);query=g.evaluate('EEFQueryUI.snapshot()')
    card.locator('[data-eef-toggle]').click();g.locator('#eefSelectedNav').click();g.wait_for_selector('#eefCollection[open]')
    check(eid+' reader uses original node',g.evaluate('document.querySelector("#eefCollection article.candidate")===window.originalPrototypeCard'))
    reader=g.locator('#eefCollection');reader.locator('.cc-transparency>summary').click()
    check(eid+' context available in reader',reader.locator('.cc-transparency').evaluate('(e)=>e.open'))
    reader.locator('.cc-transparency>summary').click();g.locator('#eefShareCollection').click();link=g.locator('#eefShareUrl').input_value();g.locator('#eefShareClose').click()
    g.locator('#eefCollectionClose').click();g.wait_for_timeout(80);check(eid+' query survives reader',g.evaluate('EEFQueryUI.snapshot()')==query)
    new=ctx.new_page();new.goto(link,wait_until='domcontentloaded');new.wait_for_selector('#eefCollection[open]');check(eid+' shared original canonical card',new.locator('#eefCollection article[data-canonical-card]').count()==1);new.close()
    # Suspend a conflicting query through the already released deep-link controller.
    g.locator('#searchInput').fill('fixture-impossible-result-canonical');g.wait_for_timeout(80);g.evaluate('(id)=>location.hash=id','candidato-'+cid);g.wait_for_timeout(80)
    check(eid+' hidden deep link restored',card.is_visible());g.locator('#eefRestoreQuery').click();g.wait_for_timeout(80);check(eid+' original query restorable',g.evaluate('EEFQueryUI.snapshot().q')=='fixture-impossible-result-canonical')
    start(e['entrypoint']);case=selected[0];card=g.locator('#candidato-'+case['candidate_id'])
    if eid=='2026-sc-federais':
     g.set_viewport_size({'width':1440,'height':960});g.locator('[data-pauta-topic]').first.click();check('SC existing inline reasons',g.locator('.eef-filter-note').count()>0)
    check(eid+' no persistent preferences',g.evaluate('localStorage.length+sessionStorage.length')==0)
   check('no runtime page errors',not errors,errors);ctx.close()
   nojs=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':960});nojs.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url.startswith('data:') else r.abort());page=nojs.new_page()
   for e in editions:
    if e['publication_status']!='published':continue
    page.goto(base+e['entrypoint'],wait_until='domcontentloaded');card=page.locator('article.candidate').first
    check(e['edition_id']+' noJS original content',card.locator('.candidate-copy').inner_text()!='')
    card.locator('.cc-transparency>summary').click();check(e['edition_id']+' noJS provenance',card.locator('.cc-transparency').evaluate('(e)=>e.open'))
    check(e['edition_id']+' noJS controls hidden',page.locator('.cc-evidence-controls:visible').count()==0)
   nojs.close();browser.close()
 finally:http.shutdown()

def main():
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 try:run(a.prototype,a.out)
 except Exception as e:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(e)});raise
 finally:save(a.out/'browser.json',{'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'checks':CHECKS,'count':len(CHECKS),'scope':'Isolated prototype, not production or new political research','limits':['No real WhatsApp send','No physical device or screen reader','External sources not refetched']})
 print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

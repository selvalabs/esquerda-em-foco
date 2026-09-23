"""Real-browser rollout tests, both local mounts or the actual public deployment.
External requests blocked except same-site dependencies. Share outcomes simulated;
no WhatsApp is sent and no remote political-source validation is claimed.
"""
from __future__ import annotations
import argparse,functools,itertools,json,threading,tempfile,sys
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,urlencode
from playwright.sync_api import sync_playwright,expect
ROOT=Path(__file__).resolve().parents[2]
CHECKS=[]
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def expected(cfg,s):
 # Independent scalar + set oracle; never call the production matcher.
 import unicodedata
 def normal(x):return ''.join(c for c in unicodedata.normalize('NFD',str(x)) if not unicodedata.combining(c)).lower()
 output=[]
 for r in cfg['records']:
  if s['parties'] and r['party'] not in s['parties']:continue
  if any(normal(t) not in normal(r['search']) for t in s['q'].split()):continue
  scalars=True
  for f in ('registration','aptitude','mandate','history','region'):
   value=s[f]
   if not value:continue
   if value.startswith('legacy:'):
    key={'registration':'status','mandate':'mandate','history':'history','region':'region'}[f];value=value[7:]
    choices=['nao-confirmada','deferida-sem-confirmacao-api'] if f=='registration' and cfg['legacy_contract']['dialect']=='PR' and value=='nao-confirmada' else [value]
    if r['legacy'][key] not in choices:scalars=False
   elif r[f]!=value:scalars=False
  if not scalars:continue
  hits=[]
  for select in s['selectors']:
   if select['kind']=='legacy':hits.append(select['id'] in r['legacy']['topics'])
   else:
    target=[select['id']] if select['kind']=='topic' else next(g['members'] for g in cfg['groups'] if g['id']==select['id'])
    hits.append(any(e['topic'] in target and s['scope'] in e['scopes'] for e in r['evidence']))
  if not hits or (all(hits) if s['mode']=='all' else any(hits)):output.append(r['id'])
 return sorted(output)
def serve(root):
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)));threading.Thread(target=server.serve_forever,daemon=True).start()
 return server,'http://127.0.0.1:'+str(server.server_address[1])+'/'
def visible(page):return sorted(page.locator('article.candidate:not([hidden])').evaluate_all('xs=>xs.map(c=>c.id.replace("candidato-",""))'))
def snapshot(page):return page.evaluate('EEFQueryUI.snapshot()')
def ready(page,url):
 page.goto('about:blank');res=page.goto(url,wait_until='domcontentloaded');assert res and res.status==200
 page.wait_for_function('Boolean(window.EEFCanonicalQuery&&window.EEFQueryUI&&window.EEFCollectionUI)&&document.documentElement.classList.contains("eef-rollout-ready")')
def initcontext(browser,base,**kwargs):
 c=browser.new_context(reduced_motion='reduce',**kwargs)
 c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) or r.request.url.startswith('data:') else r.abort());return c
def openpanel(page):
 if not page.locator('#cqPanel').evaluate('(e)=>e.open'):page.locator('#cqPanel>summary').click()
def geometry(page,card,label):
 check(label+' document width',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
 data=card.evaluate('''c=>{const r=s=>{const d=c.querySelector(s).getBoundingClientRect();return {top:d.top,bottom:d.bottom}};const n=c.querySelector('.number');return {context:r('.cc-context'),header:r('header'),nav:r('.cc-card-nav'),reading:r('.cc-reading-title'),number:n.getBoundingClientRect().height,line:parseFloat(getComputedStyle(n).lineHeight)};}''')
 check(label+' reading order',data['context']['bottom']<=data['header']['top']+1 and data['header']['bottom']<=data['nav']['top']+1 and data['nav']['bottom']<=data['reading']['top']+1,data)
 check(label+' number unbroken',data['number']<=data['line']*1.65,data)
def run(base,out,browser,live):
 reg=json.loads((ROOT/'config/editions.json').read_text());pub=[e for e in reg['editions'] if e['publication_status']=='published'];ctx=initcontext(browser,base,viewport={'width':1440,'height':960});page=ctx.new_page();page.set_default_timeout(15000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 shots=out/'screenshots';shots.mkdir(parents=True,exist_ok=True)
 for edition in pub:
  eid=edition['edition_id'];url=base+edition['canonical_path'].lstrip('/');ready(page,url)
  cfg=page.evaluate('JSON.parse(document.getElementById("cqData").textContent)');default=snapshot(page)
  check(eid+' exact initial catalogue',visible(page)==sorted(r['id'] for r in cfg['records']))
  check(eid+' 39/16 grammar',page.locator('[data-cq-topic]').count()==39 and page.locator('[data-cq-group]').count()==16)
  check(eid+' no duplicate IDs',page.evaluate('(()=>{const x=[...document.querySelectorAll("[id]")].map(n=>n.id);return x.length===new Set(x).size})()'))
  # Compare rendered visibility against an independently computed record set.
  cases=[default,{**default,'parties':cfg['parties'][:2]}]
  for dim in cfg['dimensions']:
   for option in dim['options']:cases.append({**default,dim['id']:option['value']})
  for scope in ('documented_topic','current_support','legacy_context'):
   topics=cfg['available'][scope];chosen=topics[:2] or [cfg['topics'][0]['id']]
   for mode in ('any','all'):cases.append({**default,'scope':scope,'mode':mode,'selectors':[{'kind':'topic','id':t} for t in chosen]})
   for group in cfg['groups'][:2]:cases.append({**default,'scope':scope,'selectors':[{'kind':'group','id':group['id']}]})
  for i,state in enumerate(cases):
   page.evaluate('s=>EEFEditionQuery.applyState(s)',state);actual=visible(page);oracle=expected(cfg,state)
   check(eid+f' exact DOM set {i}',actual==oracle,{'actual':len(actual),'expected':len(oracle)})
   actual_css=page.locator('article.candidate').evaluate_all('xs=>xs.filter(x=>getComputedStyle(x).display!=="none").map(x=>x.id.replace("candidato-","")).sort()')
   check(eid+f' hidden is visually hidden {i}',actual_css==oracle)
  ready(page,url);openpanel(page);parties=[p for p in cfg['parties'] if any(r['party']==p for r in cfg['records'])][:2]
  for party in parties:
   b=page.locator('[data-cq-party="'+party+'"]');b.click();check(eid+' party button focus '+party,b.evaluate('(e)=>e===document.activeElement'))
  selected=snapshot(page);check(eid+' UI multiparty OR',visible(page)==expected(cfg,selected))
  check(eid+' no URL preference writes',not urlsplit(page.url).query and not urlsplit(page.url).fragment)
  check(eid+' opaque history state only',page.evaluate('Object.keys(history.state||{}).sort()')==['eefQueryEntry'])
  page.go_back();page.wait_for_timeout(80);check(eid+' back restores first party',snapshot(page)['parties']==[parties[0]])
  page.go_forward();page.wait_for_timeout(80);check(eid+' forward restores both',snapshot(page)==selected)
  page.locator('#eefShareQuery').click();shared=page.locator('#eefQueryShareUrl').input_value();check(eid+' versioned new query link','#eef=query&v=2&edition='+eid+'&taxonomy=1.0.0' in shared)
  check(eid+' WhatsApp draft no recipient',page.locator('#eefQueryWhatsapp').get_attribute('href').startswith('https://wa.me/?text='));page.keyboard.press('Escape');check(eid+' share close focus',page.locator('#eefShareQuery').evaluate('(e)=>e===document.activeElement'))
  new=ctx.new_page();ready(new,shared);check(eid+' new document query round trip',snapshot(new)==selected and visible(new)==expected(cfg,selected));new.close()
  # Old queries retain native clauses, not newly widened groups or different scopes.
  native=cfg['legacy_contract']['valid'];oldthemes=native['topics'][:2]
  old=page.evaluate('v=>({...EEFGlobal.emptyQuery(v.edition_id),topics:v.topics.slice(0,2),mode:v.modes[0],semantic:v.semantic})',native)
  oldlink=page.evaluate('x=>EEFGlobal.queryLink(new URL("./",location.href).href,x.state,x.valid)',{'state':old,'valid':native})
  ready(page,oldlink);imported=snapshot(page);check(eid+' old query v1 preserved',visible(page)==expected(cfg,imported) and all(s['kind']=='legacy' for s in imported['selectors']))
  if cfg['legacy_contract']['dialect']=='PR':
   ready(page,url+'?'+urlencode({'pautas':','.join(oldthemes),'partido':parties[0]}));oldstate=snapshot(page)
   check(eid+' old PR link still ALL',oldstate['mode']=='all' and visible(page)==expected(cfg,oldstate))
   openpanel(page);page.locator('[name="cq-mode"][value="any"]').check();check(eid+' PR ANY operational',snapshot(page)['mode']=='any' and visible(page)==expected(cfg,snapshot(page)))
  # New themes in the UI + evidence controls use the existing sources, not text tags.
  ready(page,url);openpanel(page);scope=next((s for s in ('documented_topic','legacy_context') if cfg['available'][s]),None)
  if scope:
   page.locator('#cqScope').select_option(scope);topic=cfg['available'][scope][0]
   page.locator('[data-cq-topic="'+topic+'"]').evaluate('(e)=>e.closest("details").open=true');page.locator('[data-cq-topic="'+topic+'"]').click()
   check(eid+' UI topic exact',visible(page)==expected(cfg,snapshot(page)) and bool(visible(page)))
   article=page.locator('article.candidate:not([hidden])').first;article.locator('[data-cq-reason]').click();check(eid+' focused evidence accessible',article.locator('.cc-proof').evaluate('(e)=>e.open'))
   if article.locator('[data-cc-reset]').count():article.locator('[data-cc-reset]').click();check(eid+' full evidence context restorable',article.locator('[data-cc-evidence][hidden]').count()==0)
  # Original-node reader and query/collection links remain different.
  ready(page,url);cid=cfg['records'][0]['id'];article=page.locator('#candidato-'+cid);page.evaluate('id=>window.originalNode=document.getElementById(id)','candidato-'+cid)
  page.locator('#searchInput').fill(cfg['records'][0]['name']);query=snapshot(page);article.locator('[data-eef-toggle]').click();page.locator('#eefSelectedNav').click();page.wait_for_selector('#eefCollection[open]')
  check(eid+' reader original node',page.evaluate('document.querySelector("#eefCollection article.candidate")===window.originalNode'))
  page.locator('#eefCollection .cc-transparency>summary').click();check(eid+' provenance inside reader',page.locator('#eefCollection .cc-transparency').evaluate('(e)=>e.open'))
  page.locator('#eefShareCollection').click();link=page.locator('#eefShareUrl').input_value();check(eid+' collection v2 kept','eef=collection' in link)
  page.locator('#eefShareClose').click();page.locator('#eefCollectionClose').click();page.wait_for_timeout(80);check(eid+' query retained after reader',snapshot(page)==query)
  fresh=ctx.new_page();ready(fresh,link);fresh.wait_for_selector('#eefCollection[open]');check(eid+' shared canonical original card',fresh.locator('#eefCollection #candidato-'+cid+'[data-canonical-card]').count()==1);fresh.close()
  page.locator('#searchInput').fill('not-a-match-eef-fixture-2626');page.evaluate('h=>location.hash=h','candidato-'+cid);page.wait_for_timeout(100)
  check(eid+' hidden deep link recovered',article.is_visible() and page.locator('#eefDeepLinkNotice').is_visible());page.locator('#eefRestoreQuery').click();check(eid+' displaced query recovered',snapshot(page)['q']=='not-a-match-eef-fixture-2626' and visible(page)==[])
  prior=snapshot(page);page.evaluate('h=>location.hash=h','eef=query&v=2&edition=invalid&taxonomy=1.0.0&state={}')
  page.wait_for_timeout(60);check(eid+' malformed link atomic',snapshot(page)==prior and page.locator('#eefQueryNotice').is_visible())
  check(eid+' no stored political choices',page.evaluate('localStorage.length+sessionStorage.length')==0 and not ctx.cookies())
  # Layout, numeric header and open disclosures, including mobile.
  for width in ([390,1440] if live else [320,360,390,430,768,1024,1440]):
   page.set_viewport_size({'width':width,'height':960});ready(page,url);article=page.locator('article.candidate').first;geometry(page,article,eid+f' {width}')
   openpanel(page);page.locator('.cq-advanced').evaluate('(e)=>e.open=true');page.locator('.cq-group').first.evaluate('(e)=>e.open=true')
   check(eid+f' expanded filters width {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   if width in (390,1440):
    page.locator('#cqPanel').scroll_into_view_if_needed();page.screenshot(path=str(shots/(eid+f'-filters-{width}.png')))
   page.locator('#cqPanel').evaluate('(e)=>e.open=false');article.locator('.cc-transparency>summary').click()
   check(eid+f' expanded provenance width {width}',page.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
   article.locator('.cc-transparency>summary').click()
   if width in (390,1440):article.screenshot(path=str(shots/(eid+f'-card-{width}.png')),style='.persistent-footer{visibility:hidden!important}')
  page.locator('#global-edition-menu>summary').click();links=page.locator('#global-edition-menu li a').evaluate_all('xs=>xs.map(a=>a.href).sort()');check(eid+' six edition links',links==sorted(base+e['canonical_path'].lstrip('/') for e in pub));page.keyboard.press('Escape')
 check('no JS errors',not errors,errors)
 # Exercise copy fallback and cancellation without writing clipboard or sending data.
 ready(page,base+'sp/deputados-federais/');page.locator('#searchInput').fill('copy fixture')
 page.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}});Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('cancel','AbortError')}})")
 page.locator('#eefShareQuery').click();page.locator('#eefQueryCopy').click();page.wait_for_timeout(40);check('copy manual fallback','automaticamente' in page.locator('#eefQueryShareStatus').inner_text())
 page.locator('#eefQueryNative').click();page.wait_for_timeout(40);check('native cancel recognized','cancelado' in page.locator('#eefQueryShareStatus').inner_text());page.keyboard.press('Escape');ctx.close()
 nojs=initcontext(browser,base,java_script_enabled=False,viewport={'width':390,'height':960});page=nojs.new_page()
 for e in pub:
  page.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded');cards=page.locator('article.candidate');check(e['edition_id']+' noJS all cards',cards.count()==len(json.loads(page.locator('#cqData').text_content())['records']))
  cards.first.locator('.cc-transparency>summary').click();check(e['edition_id']+' noJS context',cards.first.locator('.cc-transparency').evaluate('(e)=>e.open'));check(e['edition_id']+' noJS controls hidden',not page.locator('#eefQueryTools').is_visible())
 nojs.close()
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--live-base');p.add_argument('--edition');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);http=None
 try:
  with tempfile.TemporaryDirectory(prefix='eef-rollout-web-') as t:
   if a.live_base:bases=[a.live_base]
   else:
    web=Path(t)
    for item in ROOT.iterdir():
     if item.name!='.git':(web/item.name).symlink_to(item,target_is_directory=item.is_dir())
    (web/'esquerda-em-foco').symlink_to(ROOT,target_is_directory=True);http,base=serve(web);bases=[base,base+'esquerda-em-foco/']
   with sync_playwright() as p:
    browser=p.chromium.launch()
    for i,base in enumerate(bases):run(base,a.out/f'mount-{i}',browser,bool(a.live_base))
    browser.close()
 except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
 finally:
  (a.out/'browser.json').write_text(json.dumps({'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,'scope':'Published rollout' if a.live_base else 'Production pages in local mounts','limits':['External political sources not refetched','No real WhatsApp or clipboard write','No physical device or screen reader certification']},ensure_ascii=False,indent=2)+'\n')
  if http:http.shutdown()
 print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

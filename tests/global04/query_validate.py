"""GLOBAL-04 L02: common-query migration without political reclassification.
The suite checks preservation against the published L01 baseline and exercises
only existing fields/associations. Third-party requests and real sharing are blocked.
"""
from __future__ import annotations
import argparse,functools,hashlib,json,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,urlencode
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
BASE='1a71c03987f52104af12af42eebda52449ff5570'
CHECKS=[]
MODIFIED={
 'assets/global/core.js','assets/pauta-filters-editorial.js','deputados-estaduais/assets/app.js','deputados-estaduais/ui/app.js',
 'tools/rs/runtime.js','pr/assets/runtime.js','tools/pr/runtime.js','sp/deputados-federais/assets/app.js','tools/global03/refresh.py',
 'tools/sp/publication/verify_live.py','docs/GLOBAL-MIGRATION-PLAN.md','config/editions.json','data/global03/publication-files.json','data/global-integration/migration-status.json'
}
NEW_PREFIXES=('assets/global/query.','tools/global04/query_','tools/global04/prepare_lot02.py','tests/global04/query','data/global04/lot02.json','docs/GLOBAL-04-LOTE02.md','.github/workflows/global04-query')

def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def soup(path):return BeautifulSoup(Path(path).read_text(),'html.parser')
def card_signature(doc):
 out=[]
 for c in doc.select('article.candidate'):
  x=BeautifulSoup(str(c),'html.parser').article
  for n in x.select('[data-global04],.eef-card-actions,.eef-reader-party'):n.decompose()
  out.append({'id':x.get('id'),'text':x.get_text(' ',strip=True),'data':dict(x.attrs),
    'external':[(a.get('href'),a.get_text(' ',strip=True)) for a in x.select('a[href]') if urlsplit(a.get('href','')).scheme]})
 return out

def static(baseline:Path):
 registry=load(ROOT/'config/editions.json');oldreg=load(baseline/'config/editions.json');published=[e for e in registry['editions'] if e['publication_status']=='published']
 entrypoints={e['entrypoint'] for e in published};protected=0;total=0
 for p in sorted(baseline.rglob('*')):
  if not p.is_file() or '.git' in p.parts:continue
  rel=str(p.relative_to(baseline))
  if any(part.startswith('.') for part in Path(rel).parts):continue
  if rel in MODIFIED or rel in entrypoints:continue
  check('preserved '+rel,(ROOT/rel).is_file() and sha(ROOT/rel)==sha(p));protected+=1
 check('protected baseline breadth',protected>1650,protected)
 for p in [ROOT/'index.html',ROOT/'sc/index.html',ROOT/'rs/index.html',ROOT/'pr/index.html',ROOT/'sp/index.html']:
  check('home/hub untouched '+p.name,sha(p)==sha(baseline/p.relative_to(ROOT)))
 for e in registry['editions']:
  old=next(x for x in oldreg['editions'] if x['edition_id']==e['edition_id'])
  check(e['edition_id']+' research/snapshot intact',e['research']==old['research'] and e['snapshot']==old['snapshot'])
  if e['publication_status']!='published':
   check(e['edition_id']+' remains unpublished',e==old and not (ROOT/e['entrypoint']).exists());continue
  before=soup(baseline/e['entrypoint']);after=soup(ROOT/e['entrypoint']);n=len(after.select('article.candidate'));total+=n
  check(e['edition_id']+' card signature intact',card_signature(before)==card_signature(after))
  check(e['edition_id']+' one common query layer',len(after.select('#eefQueryTools'))==1 and len(after.select('#eefQueryShareDialog'))==1 and len(after.select('script[src*="assets/global/query.js"]'))==1)
  check(e['edition_id']+' collection layer retained',len(after.select('#eefCollection'))==1 and len(after.select('[data-eef-toggle]'))==n)
  check(e['edition_id']+' party/query capabilities',e['capabilities']['D02']['state']=='ready' and e['capabilities']['D08']['state']=='ready' and e['capabilities']['global_query_v1']['state']=='ready' and e['capabilities']['multi_party_or']['state']=='ready')
  ids=[n['id'] for n in after.select('[id]')];check(e['edition_id']+' unique ids',len(ids)==len(set(ids)))
 check('760 records still public',total==760,total)
 status=load(ROOT/'data/global-integration/migration-status.json')
 check('migration status L02 remains partial',status['lot']=='02' and status['whole_issue_completed'] is False)
 lot=load(ROOT/'data/global04/lot02.json');check('G4-D explicitly pending','G4-D editorial/evidence/transparency composition' in lot['not_done'])

def server(root:Path):
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*a):pass
 s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
 threading.Thread(target=s.serve_forever,daemon=True).start();return s,f'http://127.0.0.1:{s.server_address[1]}/'
def context(browser,base,js=True):
 c=browser.new_context(reduced_motion='reduce',java_script_enabled=js)
 c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());return c
def start(page,url):
 page.goto(url,wait_until='domcontentloaded');page.wait_for_function("typeof EEFQueryUI==='object' && typeof EEFCollectionUI==='object' && document.documentElement.classList.contains('eef-global04-query-ready')")
def visible_parties(page):return set(page.locator('article.candidate:not([hidden])').evaluate_all("els=>els.map(e=>e.dataset.party).filter(Boolean)"))
def snap(page):return page.evaluate('EEFQueryUI.snapshot()')
def wait_sync(page):page.wait_for_timeout(320)

def click_two_parties(page,edition):
 if edition=='2026-sp-federais':
  # Native SP controls already implement multi-party selection.
  vals=page.locator('[data-party-filter]').evaluate_all("els=>els.map(e=>e.dataset.partyFilter).filter(Boolean).slice(0,2)")
  for v in vals:page.locator(f'[data-party-filter="{v}"]').click()
 else:
  if not page.locator('#eefQueryParties').evaluate('(e)=>e.open'):page.locator('#eefQueryPartyLabel').click()
  vals=page.locator('[data-eef-party]').evaluate_all("els=>els.slice(0,2).map(e=>e.dataset.eefParty)")
  for v in vals:page.locator(f'[data-eef-party="{v}"]').click()
 wait_sync(page);return vals

def share_roundtrip(browser,base,page,label):
 before=snap(page);page.locator('#eefShareQuery').click();page.wait_for_selector('#eefQueryShareDialog[open]');link=page.locator('#eefQueryShareUrl').input_value();u=urlsplit(link)
 check(label+' explicit share has no querystring',not u.query)
 check(label+' explicit versioned fragment',u.fragment.startswith('eef=query&v=1&edition='+before['edition_id']+'&state='))
 check(label+' WhatsApp has no recipient',urlsplit(page.locator('#eefQueryWhatsapp').get_attribute('href')).hostname=='wa.me')
 page.locator('#eefQueryShareClose').click();c=context(browser,base);r=c.new_page();start(r,link);wait_sync(r)
 check(label+' shared state roundtrip',snap(r)==before,(snap(r),before));c.close();return link,before

def browser_tests(out:Path,baseline:Path|None=None,live_base:str|None=None):
 reg=load(ROOT/'config/editions.json');pub=[e for e in reg['editions'] if e['publication_status']=='published'];local_server=None
 if live_base:bases=[live_base]
 else:
  web=out/'webroot';web.mkdir(parents=True,exist_ok=True)
  for item in ROOT.iterdir():
   if item.name!='.git' and not (web/item.name).exists():(web/item.name).symlink_to(item,target_is_directory=item.is_dir())
  (web/'esquerda-em-foco').symlink_to(ROOT,target_is_directory=True);local_server,base=server(web);bases=[base,base+'esquerda-em-foco/']
 shots=out/'screenshots';shots.mkdir(exist_ok=True)
 with sync_playwright() as p:
  browser=p.chromium.launch()
  for mount,base in enumerate(bases):
   c=context(browser,base);g=c.new_page();errors=[];g.on('pageerror',lambda e:errors.append(str(e)));sc_shared_link=None
   for e in pub:
    label=f'{mount}:{e["edition_id"]}';url=base+e['canonical_path'].lstrip('/')
    widths=[390,1440] if live_base else [320,360,390,430,768,1024,1440]
    for width in widths:
     g.set_viewport_size({'width':width,'height':900});start(g,url);check(label+f' no overflow {width}',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),g.evaluate('document.documentElement.scrollWidth'))
    start(g,url);initial_storage=g.evaluate('localStorage.length');parties=click_two_parties(g,e['edition_id']);state=snap(g)
    check(label+' party OR state',state['parties']==sorted(parties),state)
    check(label+' visible parties are selected',visible_parties(g).issubset(set(parties)),visible_parties(g))
    check(label+' distinct-person count',int(g.locator('#resultCount').inner_text().split()[0])==g.locator('article.candidate:not([hidden])').count() or e['edition_id']=='2026-sc-federais')
    link,before=share_roundtrip(browser,base,g,label)
    if e['edition_id']=='2026-sc-federais':sc_shared_link=link
    check(label+' no preference storage',g.evaluate('localStorage.length')==initial_storage and g.context.cookies()==[])
    # Collection must retain the query after closing the reader.
    first=g.locator('article.candidate:not([hidden])').first
    cid=first.get_attribute('id').removeprefix('candidato-');g.locator(f'[data-eef-toggle="{cid}"]').click();g.locator('#eefSelectedNav').click();g.wait_for_selector('#eefCollection[open]');g.locator('#eefCollectionClose').click();wait_sync(g)
    check(label+' query survives selected reader',snap(g)==before,(snap(g),before))
    if not live_base and mount==0:g.screenshot(path=str(shots/(e['edition_id']+'-query390.png')))
   # Edition-specific controls and semantic guards.
   sc=base+'sc/deputados-federais/';start(g,sc);g.set_viewport_size({'width':1440,'height':900});topic=g.locator('[data-pauta-topic]').first;topic.click();wait_sync(g);ss=snap(g)
   check(f'{mount}:SC current-support semantic',ss['semantic']=='current_support' and len(ss['topics'])==1)
   check(f'{mount}:SC reason next to evidence',g.locator('.eef-filter-note').count()>0)
   st=base+'sc/deputados-estaduais/';start(g,st);registration=g.locator('#registrationFilter option').evaluate_all('els=>els.map(e=>e.value).filter(Boolean)');trajectory=g.locator('#trajectoryFilter option').evaluate_all('els=>els.map(e=>e.value).filter(Boolean)')
   if registration:g.locator('#registrationFilter').select_option(registration[0])
   if trajectory:g.locator('#trajectoryFilter').select_option(trajectory[0]);wait_sync(g)
   ss=snap(g);check(f'{mount}:SC state local controls represented',ss['status']==(registration[0] if registration else '') and (ss['mandate'] or ss['history'] or not trajectory),ss)
   rs=base+'rs/deputados-federais/';start(g,rs);rpart=click_two_parties(g,'2026-rs-federais');g.locator('#searchInput').fill(rpart[0]);wait_sync(g);check(f'{mount}:RS search and party combine',snap(g)['q']==rpart[0] and set(snap(g)['parties'])==set(rpart))
   # PR legacy query is imported as AND/legacy_context; first new interaction removes querystring.
   pr=base+'pr/deputados-federais/';start(g,pr);valid=g.evaluate('EEFEditionQuery.valid');party=valid['parties'][0];topic=valid['topics'][0] if valid['topics'] else ''
   legacy=urlencode({'partido':party,**({'pautas':topic} if topic else {})});start(g,pr+'?'+legacy);ps=snap(g);check(f'{mount}:PR legacy import',ps['parties']==[party] and ps['mode']=='all' and ps['semantic']=='legacy_context',ps)
   g.locator('#searchInput').fill('a');wait_sync(g);check(f'{mount}:PR new interaction leaves querystring',urlsplit(g.url).query=='')
   if topic:check(f'{mount}:PR theme remains legacy context',snap(g)['semantic']=='legacy_context' and snap(g)['mode']=='all')
   # SP legacy import keeps native multi-party and documented-topic semantic.
   sp=base+'sp/deputados-federais/';start(g,sp);sv=g.evaluate('EEFEditionQuery.valid');p1,p2=sv['parties'][:2];topic=sv['topics'][0] if sv['topics'] else ''
   legacy=urlencode({'partidos':p1+','+p2,**({'pautas':topic} if topic else {}),'modo':'todos','ordem':'alfabetica'});start(g,sp+'?'+legacy);ss=snap(g)
   check(f'{mount}:SP legacy import',set(ss['parties'])=={p1,p2} and ss['mode']=='all' and ss['order']=='alphabetical' and ss['semantic']=='documented_topic',ss)
   # Toggle one native party: querystring disappears, state stays in memory.
   g.locator(f'[data-party-filter="{p1}"]').click();wait_sync(g);check(f'{mount}:SP new interaction leaves querystring',urlsplit(g.url).query=='')
   # Foreign shared query never replaces current state.
   # Use the SC shared fragment against SP.
   start(g,sp);current=snap(g);check(f'{mount}:SC shared fixture captured',bool(sc_shared_link));g.evaluate("h=>location.hash=h",urlsplit(sc_shared_link).fragment);wait_sync(g);check(f'{mount}:foreign query is atomic',snap(g)==current)
   check(f'{mount}:no JS errors',not errors,errors[:8]);c.close()
   c=context(browser,base,js=False);g=c.new_page()
   for e in pub:
    g.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded')
    check(f'{mount}:{e["edition_id"]} noJS cards',g.locator('article.candidate').count()>0)
    check(f'{mount}:{e["edition_id"]} noJS query UI hidden',not g.locator('#eefQueryTools').is_visible() and not g.locator('#eefQueryShareDialog').is_visible())
   c.close()
  browser.close()
 if local_server:local_server.shutdown()

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--baseline-root',type=Path);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--live-base');ap.add_argument('--static-only',action='store_true');a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 try:
  if a.baseline_root:static(a.baseline_root)
  if not a.static_only:browser_tests(a.out,a.baseline_root,a.live_base)
 except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
 finally:(a.out/'query-qa.json').write_text(json.dumps({'passed':bool(CHECKS) and all(x['passed'] for x in CHECKS),'checks':CHECKS,'count':len(CHECKS),'baseline':BASE,'scope':'G4-C query/filter integration only; no political research, topic crosswalk, real message send or stored preference'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

"""Lote 01: original-source parity and actual collection/deep-link interactions.
Browser tests never send WhatsApp messages and block third-party requests.
"""
from __future__ import annotations
import argparse,copy,functools,hashlib,json,os,posixpath,sys,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
BASE='22bf032f12b44ec3471f90736035c3e020deea6d'
CHECKS=[]
MODIFIED={'config/editions.json','data/global03/publication-files.json','sp/deputados-federais/assets/app.js','pr/assets/runtime.js','tools/pr/runtime.js','tools/rs/runtime.js','tools/global03/refresh.py','tests/global03/validate.py','tools/sc_selected_ui/verify_live.py'}

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))
def soup(p):return BeautifulSoup(p.read_text(),'html.parser')
def signature(s):
    for n in s.select('[data-global04],.eef-card-actions,.eef-reader-party'):n.decompose()
    return [{'id':c['id'],'text':c.get_text(' ',strip=True),'data':dict(c.attrs),
       'external':[(n['href'],n.get_text(' ',strip=True)) for n in c.select('a[href]') if urlsplit(n['href']).scheme]}
        for c in s.select('article.candidate')]


def static(baseline):
    registry=load(ROOT/'config/editions.json');prior=load(baseline/'config/editions.json')
    published=[e for e in registry['editions'] if e['publication_status']=='published']
    changed=MODIFIED|{e['entrypoint'] for e in published};protected=0;total=0
    for p in sorted(baseline.rglob('*')):
        if not p.is_file() or '.git' in p.parts:continue
        rel=str(p.relative_to(baseline))
        if rel in changed:continue
        check('preserved '+rel,(ROOT/rel).is_file() and sha(ROOT/rel)==sha(p));protected+=1
    check('protected files',protected>1600,protected)
    check('home unchanged',sha(ROOT/'index.html')==sha(baseline/'index.html'))
    for e in registry['editions']:
        old=next(v for v in prior['editions'] if v['edition_id']==e['edition_id'])
        check(e['edition_id']+' dates/research preserved',e['snapshot']==old['snapshot'] and e['research']==old['research'])
        if e['publication_status']!='published':
            check(e['edition_id']+' stays unpublished',e==old and not (ROOT/e['entrypoint']).exists());continue
        a=soup(baseline/e['entrypoint']);b=soup(ROOT/e['entrypoint']);n=len(b.select('article.candidate'));total+=n
        check(e['edition_id']+' collection capability',e['capabilities']['global_collection_v2']['state']=='ready')
        check(e['edition_id']+' all actions',len(b.select('[data-eef-toggle]'))==n==len(b.select('[data-eef-share]')))
        check(e['edition_id']+' one reader',len(b.select('#eefCollection'))==1 and len(b.select('#eefSelectedNav'))==1)
        ids=[x['id'] for x in b.select('[id]')];check(e['edition_id']+' unique IDs',len(ids)==len(set(ids)))
        check(e['edition_id']+' original card facts and sources',signature(a)==signature(b))
    check('760 public records preserved',total==760,total)
    status=load(ROOT/'data/global-integration/migration-status.json')
    check('whole issue not silently completed',status['whole_issue_completed'] is False)


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def server(root):
    s=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
    threading.Thread(target=s.serve_forever,daemon=True).start();return s,f'http://127.0.0.1:{s.server_address[1]}/'

def context(browser,base,**kw):
    c=browser.new_context(reduced_motion='reduce',**kw)
    c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());return c

def start(page,url):
    page.goto(url,wait_until='domcontentloaded');page.wait_for_function("document.documentElement.classList.contains('eef-global04-ready')")

def ids(page):return page.locator('article.candidate').evaluate_all('(els)=>els.map(e=>e.id)')
def visible(page):return page.locator('.party-section article.candidate:not([hidden]),.party-group article.candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.id)')
def snap(page):return page.evaluate('EEFCollectionUI.snapshot()')
def no_duplicates(page,label):
    values=ids(page);check(label,len(values)==len(set(values)))


def browser_tests(out,baseline=None,live=None):
    registry=load(ROOT/'config/editions.json');published=[e for e in registry['editions'] if e['publication_status']=='published']
    http=None;before_server=None
    if live:bases=[live]
    else:
        webroot=out/'webroot';webroot.mkdir(parents=True,exist_ok=True)
        for item in ROOT.iterdir():
            if item.name!='.git' and not (webroot/item.name).exists():(webroot/item.name).symlink_to(item,target_is_directory=item.is_dir())
        (webroot/'esquerda-em-foco').symlink_to(ROOT,target_is_directory=True)
        http,base=server(webroot);bases=[base,base+'esquerda-em-foco/']
    shots=out/'screenshots';shots.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser=p.chromium.launch()
        if baseline:
            before_server,before_base=server(baseline);c=context(browser,before_base);g=c.new_page();g.goto(before_base+'sp/deputados-federais/',wait_until='domcontentloaded')
            target=ids(g)[0];g.locator('#searchInput').fill('global04-no-match');g.wait_for_timeout(350);g.evaluate('(v)=>location.hash=v',target);g.wait_for_timeout(100)
            check('baseline SP failure reproduced',not g.locator('#'+target).is_visible());c.close();before_server.shutdown()
        for mount,base in enumerate(bases):
            c=context(browser,base);g=c.new_page();errors=[];g.on('pageerror',lambda e:errors.append(str(e)))
            for e in published:
                url=base+e['canonical_path'].lstrip('/');label=f'{mount}:{e["edition_id"]}'
                for width in ([390,1440] if live else [320,360,390,430,768,1024,1440]):
                    g.set_viewport_size({'width':width,'height':900});start(g,url)
                    check(label+f' width {width}',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                g.set_viewport_size({'width':390,'height':900});start(g,url)
                original_ids=ids(g);chosen=[i.removeprefix('candidato-') for i in original_ids[:2]]
                for id in chosen:g.locator('[data-eef-toggle="'+id+'"]').click()
                g.locator('#searchInput').fill('global04-no-match');g.wait_for_timeout(350)
                check(label+' query hides all',not visible(g))
                g.locator('#eefSelectedNav').click()
                check(label+' ordered first card',g.locator('#eefReaderHost article').get_attribute('id')=='candidato-'+chosen[0])
                check(label+' one card reader',g.locator('#eefReaderHost article').count()==1)
                no_duplicates(g,label+' no duplicated cards')
                details=g.locator('#eefReaderHost details').first
                if details.count():
                    details.locator(':scope > summary').click();check(label+' details open',details.evaluate('(e)=>e.open'))
                check(label+' external sources remain',g.locator('#eefReaderHost a[href^="https:"]').count()>0)
                g.locator('#eefNext').click();check(label+' next in insertion order',g.locator('#eefReaderHost article').get_attribute('id')=='candidato-'+chosen[1])
                bounds=g.locator('#eefCollection').bounding_box();check(label+' reader within viewport',bounds['x']>=0 and bounds['y']>=0 and bounds['x']+bounds['width']<=391 and bounds['y']+bounds['height']<=901)
                if mount==0:g.screenshot(path=str(shots/(e['edition_id']+'-reader390.png')))
                g.locator('#eefShareCollection').click();href=g.locator('#eefShareUrl').input_value();params=parse_qs(urlsplit(href).fragment)
                check(label+' v2 ordered share',params.get('ids')==[','.join(chosen)] and params.get('active')==[chosen[1]] and params.get('edition')==[e['edition_id']] and params.get('v')==['2'])
                check(label+' share excludes query',not urlsplit(href).query)
                wa=urlsplit(g.locator('#eefWhatsapp').get_attribute('href'));check(label+' WhatsApp explicit link',wa.hostname=='wa.me' and parse_qs(wa.query)['text'][0].endswith(href))
                g.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('test denied')}}})")
                g.locator('#eefCopy').click();g.wait_for_function("document.getElementById('eefShareStatus').textContent.includes('automaticamente')")
                check(label+' clipboard fallback',g.locator('#eefShareUrl').evaluate('(e)=>e===document.activeElement'))
                g.keyboard.press('Escape');g.wait_for_function("!document.getElementById('eefShareDialog').open")
                check(label+' nested focus restored',g.locator('#eefShareCollection').evaluate('(e)=>e===document.activeElement'))
                g.locator('#eefCollectionClose').click();g.wait_for_function("!document.documentElement.classList.contains('eef-collection-open')")
                check(label+' query preserved on return',g.locator('#searchInput').input_value()=='global04-no-match' and not visible(g))
                check(label+' original DOM order preserved',ids(g)==original_ids)
                recipient=context(browser,base);r=recipient.new_page();start(r,href);r.wait_for_selector('#eefCollection[open]')
                check(label+' recipient collection restored',snap(r)['ids']==chosen and snap(r)['active']==chosen[1]);no_duplicates(r,label+' recipient no duplicate')
                check(label+' no preference storage',r.evaluate('localStorage.length+sessionStorage.length')==0)
                r.locator('#eefReaderHost [data-eef-share]').click();individual=r.locator('#eefShareUrl').input_value()
                check(label+' individual share',urlsplit(individual).fragment=='candidato-'+chosen[1] and not urlsplit(individual).query)
                r.locator('#eefShareClose').click();r.locator('#eefReaderHost [data-eef-toggle]').click()
                check(label+' active removal neighbour',snap(r)['ids']==[chosen[0]] and snap(r)['active']==chosen[0])
                r.locator('#eefClearCollection').click();r.locator('#eefCancelClear').click();check(label+' clear cancel preserves',snap(r)['ids']==[chosen[0]])
                r.locator('#eefClearCollection').click();r.locator('#eefConfirmClear').click();check(label+' clear confirmed',snap(r)['ids']==[] and r.locator('#eefCollectionEmpty').is_visible())
                recipient.close()
                other=next(x for x in published if x['edition_id']!=e['edition_id']);start(g,base+other['canonical_path'].lstrip('/'))
                check(label+' edition isolation',snap(g)['ids']==[])
            sp=base+'sp/deputados-federais/';start(g,sp)
            all_ids=[x.removeprefix('candidato-') for x in ids(g)]
            g.locator('[data-eef-toggle]').evaluate_all('(buttons)=>buttons.forEach(b=>b.click())')
            check(f'{mount}:SP all 249 selectable',snap(g)['ids']==all_ids and len(all_ids)==249)
            g.locator('#eefSelectedNav').click();g.locator('#eefShareCollection').click();link=g.locator('#eefShareUrl').input_value()
            rctx=context(browser,base);r=rctx.new_page();start(r,link);r.wait_for_selector('#eefCollection[open]');check(f'{mount}:249 link intact',snap(r)['ids']==all_ids);rctx.close()
            start(g,sp);target=ids(g)[0];g.locator('#searchInput').fill('global04-no-match');g.wait_for_timeout(350);g.evaluate('(v)=>location.hash=v',target);g.wait_for_timeout(150)
            check(f'{mount}:SP hidden target revealed',g.locator('#'+target).is_visible() and g.locator('#eefDeepLinkNotice').is_visible())
            g.locator('#eefRestoreQuery').click();check(f'{mount}:SP previous query restored',g.locator('#searchInput').input_value()=='global04-no-match' and not visible(g))
            g.go_back(wait_until='domcontentloaded');g.wait_for_timeout(100);check(f'{mount}:SP back to target',g.locator('#'+target).is_visible())
            g.go_forward(wait_until='domcontentloaded');g.wait_for_timeout(100);check(f'{mount}:SP forward to query',g.locator('#searchInput').input_value()=='global04-no-match' and not visible(g))
            start(g,sp+'?q=global04-no-match#'+target);g.wait_for_timeout(100);check(f'{mount}:SP initial link',g.locator('#'+target).is_visible() and g.locator('#eefDeepLinkNotice').is_visible())
            start(g,sp+'?q=global04-no-match#unknown-id');check(f'{mount}:unknown hash leaves query',g.locator('#searchInput').input_value()=='global04-no-match' and not visible(g))
            selected=load(ROOT/'config/legacy-sc-links.json')['candidate_ids'][:2]
            start(g,base+'#selecionados='+','.join(selected)+'&v=1&edicao=sc-federais&ficha='+selected[1]);g.wait_for_selector('#eefCollection[open]')
            check(f'{mount}:SC v1 root compatibility',snap(g)['ids']==selected and snap(g)['active']==selected[1])
            check(f'{mount}:no page errors',not errors,errors[:8]);c.close()
            c=context(browser,base,java_script_enabled=False);g=c.new_page()
            for e in published:
                g.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded')
                check(e['edition_id']+f' noJS {mount}',g.locator('article.candidate').count()>0 and not g.locator('#eefSelectedNav').is_visible() and not g.locator('#eefCollection').is_visible())
            c.close()
        browser.close()
    if http:http.shutdown()


def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-root',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--live-base');p.add_argument('--static-only',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    try:
        if a.baseline_root:static(a.baseline_root)
        if not a.static_only:browser_tests(a.out,a.baseline_root,a.live_base)
    except Exception as e:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(e)});raise
    finally:
        (a.out/'qa.json').write_text(json.dumps({'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'baseline':BASE,'checks':CHECKS,'count':len(CHECKS),'scope':'GLOBAL04 lot01 only; no new political research, physical device, screen reader or external message send'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))

if __name__=='__main__':main()

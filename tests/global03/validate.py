"""Static content parity plus real browser tests; never reclassifies candidates."""
from __future__ import annotations
import argparse,functools,hashlib,json,os,posixpath,sys,threading
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote,urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global03'))
from build import content_signature,public_editions,SITE,BASELINE
sys.path.insert(0,str(ROOT/'tools/global02'))
from core import validate,load,save,indexable_paths
CHECKS=[]
CHANGED={'index.html','deputados-estaduais/index.html','rs/deputados-federais/index.html','pr/deputados-federais/index.html','pr/deputados-estaduais/index.html','sp/deputados-federais/index.html','pr/index.html','sp/index.html','404.html','config/editions.json','sitemap.xml','robots.txt','site.webmanifest','assets/global/core.js','tests/global02/core.test.cjs','README.md'}
def check(name,condition,detail=None):
    CHECKS.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(name+': '+str(detail))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def static(baseline):
    r=load(ROOT/'config/editions.json');old=load(baseline/'config/editions.json');validate(r)
    check('global root activated',r['root_mode']=='global_home')
    check('six public editions, one branch',len(public_editions(r))==6 and len(r['editions'])==7)
    check('four live hubs',all(s['published'] for s in r['states']))
    for e in r['editions']:
        prior=next(v for v in old['editions'] if v['edition_id']==e['edition_id'])
        check(e['edition_id']+' snapshot unchanged',e['snapshot']==prior['snapshot'])
        check(e['edition_id']+' research unchanged',e['research']==prior['research'])
        if e['publication_status']!='published':
            check('RS state not silently published',not (ROOT/e['entrypoint']).exists());continue
        a=BeautifulSoup((baseline/prior['entrypoint']).read_text(),'html.parser');b=BeautifulSoup((ROOT/e['entrypoint']).read_text(),'html.parser')
        check(e['edition_id']+' candidate content, IDs, metadata, external sources preserved',content_signature(a)==content_signature(b))
        before=[n.get_text() for n in a.select('script:not([src])') if n.get('type') not in ('application/json','application/ld+json')]
        after=[n.get_text() for n in b.select('script:not([src])') if n.get('type') not in ('application/json','application/ld+json')]
        check(e['edition_id']+' inline application unchanged',before==after)
        check(e['edition_id']+' script payload unchanged',[n.get_text() for n in a.select('script[type="application/json"]')]==[n.get_text() for n in b.select('script[type="application/json"]')])
        check(e['edition_id']+' current equals canonical',e['current_path']==e['canonical_path'])
    protected=0
    for p in sorted(baseline.rglob('*')):
        if not p.is_file() or '.git' in p.parts:continue
        rel=str(p.relative_to(baseline))
        if rel in CHANGED:continue
        check('preserved '+rel,(ROOT/rel).is_file() and digest(ROOT/rel)==digest(p));protected+=1
    check('protected preexisting file count',protected>1600,protected)
    paths=indexable_paths(r,'current');check('sitemap 11 unique canonical pages',len(paths)==11)
    sm=BeautifulSoup((ROOT/'sitemap.xml').read_text(),'xml')
    check('sitemap matches registry',[n.get_text() for n in sm.select('loc')]==[SITE+p.lstrip('/') for p in paths])
    check('robots permits published pages','Allow: /' in (ROOT/'robots.txt').read_text() and 'User-agent: *\nDisallow: /' not in (ROOT/'robots.txt').read_text())
    soups={}
    for path in paths:
        rel=path.lstrip('/')+'index.html';s=BeautifulSoup((ROOT/rel).read_text(),'html.parser');soups[rel]=s
        check(path+' canonical',s.select_one('link[rel=canonical]')['href']==SITE+path.lstrip('/'))
        check(path+' indexable',not any('noindex' in n['content'] for n in s.select('meta[name=robots]')))
        check(path+' one title/headline',len(s.select('title'))==len(s.select('h1'))==1)
        check(path+' OG URL',s.select_one('meta[property="og:url"]')['content']==SITE+path.lstrip('/'))
        ids=[n['id'] for n in s.select('[id]')];check(path+' unique IDs',len(ids)==len(set(ids)))
        check(path+' one edition picker',len(s.select('#global-edition-menu'))==1)
        check(path+' no branch links',not s.select('a[href*="rs/deputados-estaduais"]'))
        for script in s.select('script[type="application/ld+json"]'):
            graph=json.loads(script.string);check(path+' structured JSON valid',bool(graph))
            def walk(v):
                if isinstance(v,str) and (v.startswith(SITE+'#candidato-') or v.startswith(SITE+'deputados-estaduais/#candidato-')):return False
                if isinstance(v,dict):return all(walk(vv) for vv in v.values())
                if isinstance(v,list):return all(walk(vv) for vv in v)
                return True
            check(path+' structured SC links relocated',walk(graph))
    failures=[];link_count=0
    for rel,s in list(soups.items()):
        for n in s.select('a[href],script[src],link[href],img[src]'):
            value=n.get('href',n.get('src',''));u=urlsplit(value)
            if not value or u.scheme or value.startswith('//'):continue
            target=posixpath.normpath(posixpath.join(posixpath.dirname(rel),unquote(u.path))) if u.path else rel
            if target=='.':target='index.html'
            p=ROOT/target
            if p.is_dir():p=p/'index.html';target=str(p.relative_to(ROOT))
            if not p.is_file():failures.append({'page':rel,'url':value,'missing':target});continue
            link_count+=1
            if n.name=='a' and u.fragment and p.suffix=='.html':
                if '=' in u.fragment:continue
                if target not in soups:soups[target]=BeautifulSoup(p.read_text(),'html.parser')
                if not soups[target].find(id=unquote(u.fragment)):failures.append({'page':rel,'url':value,'missing_anchor':u.fragment})
    check('internal static links resolve',not failures,{'count':link_count,'failures':failures[:20]})
    a=BeautifulSoup((ROOT/'deputados-estaduais/index.html').read_text(),'html.parser')
    check('state legacy alias noindex','noindex' in a.select_one('meta[name=robots]')['content'])
    check('state alias correct canonical',a.select_one('link[rel=canonical]')['href']==SITE+'sc/deputados-estaduais/')
    check('404 safe absolute base',BeautifulSoup((ROOT/'404.html').read_text(),'html.parser').base['href']==SITE)
    check('privacy scripts absent on new entry','metrics' not in str(soups['index.html'].select('script[src]')))
    return protected,link_count

class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def translate_path(self,path):
        if path.startswith('/esquerda-em-foco/'):path=path[len('/esquerda-em-foco'):]
        return super().translate_path(path)

def browser(out,live_base=None):
    registry=load(ROOT/'config/editions.json');fixtures=load(ROOT/'config/legacy-sc-links.json');server=None
    if live_base:bases=[live_base]
    else:
        server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
        threading.Thread(target=server.serve_forever,daemon=True).start()
        origin=f'http://127.0.0.1:{server.server_address[1]}';bases=[origin+'/',origin+'/esquerda-em-foco/']
    shots=out/'screenshots';shots.mkdir(parents=True,exist_ok=True)
    with sync_playwright() as p:
        options={}
        if os.environ.get('EEF_CHROMIUM'):options['executable_path']=os.environ['EEF_CHROMIUM']
        b=p.chromium.launch(headless=True,**options)
        for mount,base in enumerate(bases):
            c=b.new_context(reduced_motion='reduce');errors=[];http_errors=[]
            c.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
            page=c.new_page();page.on('pageerror',lambda e:errors.append(str(e)));page.on('response',lambda res:http_errors.append({'url':res.url,'status':res.status}) if res.status>=400 else None)
            widths=[390,1440] if live_base else [320,360,390,430,768,1024,1440]
            for path in indexable_paths(registry,'current'):
                for width in widths:
                    page.set_viewport_size({'width':width,'height':900});page.goto(base+path.lstrip('/'),wait_until='domcontentloaded');page.wait_for_timeout(100)
                    dim=page.evaluate('({w:innerWidth,scroll:document.documentElement.scrollWidth})')
                    check(f'{mount}:{path} width {width}',dim['scroll']<=dim['w']+1,dim)
                    check(f'{mount}:{path} picker visible {width}',page.locator('#global-edition-menu>summary').is_visible())
                    if mount==0 and width in (390,1440):
                        name='home' if path=='/' else path.strip('/').replace('/','-')
                        page.screenshot(path=str(shots/(name+'-'+str(width)+'.png')),full_page=path.count('/')<3)
                page.locator('#global-edition-menu>summary').click()
                # Resolve URLs: the current edition can correctly be written as ./.
                targets=page.locator('#global-edition-menu .eef-edition-grid li a').evaluate_all('(nodes)=>nodes.map(n=>n.href).sort()')
                expected=sorted(base+e['canonical_path'].lstrip('/') for e in public_editions(registry))
                check(f'{mount}:{path} six edition links',len(targets)==6 and targets==expected,targets)
                page.keyboard.press('Escape')
                check(f'{mount}:{path} Escape and focus',page.locator('#global-edition-menu').evaluate('(n)=>!n.open') and page.locator('#global-edition-menu>summary').evaluate('(n)=>n===document.activeElement'))
            for e in public_editions(registry):
                page.set_viewport_size({'width':390,'height':900});page.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded')
                page.locator('#searchInput').fill('zzzz-sem-correspondencia-global03');page.wait_for_timeout(350)
                check(e['edition_id']+f' search {mount}',page.locator('article.candidate:visible').count()==0)
                page.locator('#searchInput').fill('');page.wait_for_timeout(350)
                check(e['edition_id']+f' clear {mount}',page.locator('article.candidate:visible').count()>0)
                page.evaluate('scrollTo(0,0)');page.locator('#siteNavMenu').click()
                check(e['edition_id']+f' local menu {mount}',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='true')
                page.locator('#global-edition-menu>summary').click();page.wait_for_timeout(70)
                check(e['edition_id']+f' global closes local {mount}',page.locator('#siteNavMenu').get_attribute('aria-expanded')=='false' and page.locator('#global-edition-menu').evaluate('(n)=>n.open'))
                target=next(x for x in public_editions(registry) if x['state']!=e['state'])
                page.locator('#global-edition-menu a[href*="'+target['canonical_path'].strip('/')+'"]').click();page.wait_for_url('**'+target['canonical_path'])
                check(e['edition_id']+f' changes edition {mount}',page.locator('body').get_attribute('data-global03-edition')==target['edition_id'])
            page.goto(base);page.locator('#global-estado-sc h3 a').click();page.wait_for_url('**/sc/')
            page.locator('.global-office-card a[href*="deputados-federais"]').click();page.wait_for_url('**/sc/deputados-federais/')
            check('home hub edition flow '+str(mount),page.locator('article.candidate').count()==48)
            for anchor in [fixtures['anchors'][0],'topo','fontes',next(a for a in fixtures['anchors'] if a.startswith('candidato-')),next(a for a in fixtures['anchors'] if a.startswith('partido-'))]:
                page.goto(base+'#'+anchor);page.wait_for_url('**/sc/deputados-federais/**')
                check(f'bridge:{mount}:{anchor}',page.locator('[id="'+anchor+'"]').count()==1 and page.url.endswith('#'+anchor))
            for fragment in ['#global-estados','#global-metodologia','#unknown-fragment','#selecionados=INVALID&v=1&edicao=sc-federais']:
                page.goto(base+fragment);page.wait_for_timeout(100)
                check(f'no redirect:{mount}:{fragment}',urlsplit(page.url).path==urlsplit(base).path)
            ids=fixtures['candidate_ids'][:2];h='#selecionados='+','.join(ids)+'&v=1&edicao=sc-federais&ficha='+ids[1]
            page.goto(base+h);page.wait_for_selector('#eefCollection[open]');check('legacy active card '+str(mount),page.locator('#eefCollection #candidato-'+ids[1]).count()==1)
            page.locator('#eefShareCollection').click();page.wait_for_selector('#eefShareDialog[open]');share=page.locator('#eefShareUrl').input_value()
            check('new collection URL canonical '+str(mount),share.startswith(base+'sc/deputados-federais/#eef=collection&v=2&edition=2026-sc-federais&'))
            check('WhatsApp link prepared, not sent '+str(mount),'wa.me' in page.locator('#eefWhatsapp').get_attribute('href'))
            page.locator('#eefShareClose').click();page.locator('#eefCollectionClose').click()
            page.set_viewport_size({'width':320,'height':850});page.evaluate('scrollTo(0,0)')
            check('selected navbar 320 '+str(mount),page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
            fresh_context=b.new_context();fresh_context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort())
            fresh=fresh_context.new_page();fresh.goto(share);fresh.wait_for_selector('#eefCollection[open]')
            check('fresh context collection '+str(mount),fresh.locator('#eefCollection #candidato-'+ids[1]).count()==1);fresh_context.close()
            page.goto(base+'deputados-estaduais/#candidato-240002540095');page.wait_for_url('**/sc/deputados-estaduais/**')
            check('state alias fragment '+str(mount),page.url.endswith('#candidato-240002540095'))
            check('no first-party HTTP failures '+str(mount),not http_errors,http_errors[:10]);check('no JS page errors '+str(mount),not errors,errors[:10])
            c.close();c=b.new_context(java_script_enabled=False)
            c.route('**/*',lambda route:route.continue_() if route.request.url.startswith(base) else route.abort());page=c.new_page()
            page.set_viewport_size({'width':390,'height':900});page.goto(base)
            check('noJS home state links '+str(mount),page.locator('.global-state h3 a').count()==4)
            page.locator('#global-edition-menu>summary').click();check('noJS picker '+str(mount),page.locator('#global-edition-menu').evaluate('(n)=>n.open'))
            for e in public_editions(registry):
                page.goto(base+e['canonical_path'].lstrip('/'));check(e['edition_id']+' noJS '+str(mount),page.locator('article.candidate').count()>0)
            page.goto(base+'deputados-estaduais/');check('noJS alias fallback '+str(mount),page.locator('#global-alias-target').is_visible());c.close()
        b.close()
    if server:server.shutdown()

def main():
    p=argparse.ArgumentParser();p.add_argument('--baseline-root',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--static-only',action='store_true');p.add_argument('--live-base');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    try:
        if a.baseline_root:static(a.baseline_root)
        if not a.static_only:browser(a.out,a.live_base)
    except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
    finally:save(a.out/'qa.json',{'baseline':BASELINE,'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,'live':a.live_base,'limits':['External candidate photos blocked during browser tests','No WhatsApp message sent','No new electoral collection or political-content review','No physical device or screen reader certification']})
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

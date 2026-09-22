"""Foundation validation with original-source parity and browser rehearsal.
No external research and no test sends messages or stores political choices.
"""
from __future__ import annotations
import argparse
import copy
import functools
import json
import shutil
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
import jsonschema
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global02'))
from core import load,save,digest,validate,sitemap,shell,indexable_paths,adapt_candidate,adapt_claim
from build import build
CHECKS=[]


def check(name,condition,detail=None):
    CHECKS.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(name+': '+str(detail))


def expected_failure(name,callback):
    try:callback()
    except (ValueError,jsonschema.ValidationError):check(name,True);return
    check(name,False)


def metadata_tests(rs_root):
    registry=load(ROOT/'config/editions.json');validate(registry)
    jsonschema.Draft202012Validator(load(ROOT/'config/editions.schema.json')).validate(registry)
    check('registry schema',True)
    check('publication axes',sum(e['publication_status']=='published' for e in registry['editions'])==6)
    check('no invented SP state edition',not any(e['state']=='SP' and e['office_code']==7 for e in registry['editions']))
    for name,mutate in [
        ('duplicate edition',lambda r:r['editions'].append(copy.deepcopy(r['editions'][0]))),
        ('duplicate route',lambda r:r['editions'][1].update(canonical_path=r['editions'][0]['canonical_path'])),
        ('alias collision',lambda r:r['editions'][1]['aliases'].append(r['editions'][0]['canonical_path'])),
        ('branch advertised',lambda r:r['editions'][3].update(current_path='/rs/deputados-estaduais/')),
        ('year identity',lambda r:r['editions'][0].update(election_year=2030)),
        ('unsupported capability',lambda r:r['editions'][0]['capabilities']['A01'].update(state='ready-by-inference')),
    ]:
        r=copy.deepcopy(registry);mutate(r);expected_failure(name,lambda:validate(r))
    current=indexable_paths(registry,'current');future=indexable_paths(registry,'next')
    check('current sitemap 8 routes',len(current)==8)
    check('future sitemap 11 routes',len(future)==11)
    check('branch excluded sitemap','/rs/deputados-estaduais/' not in current+future)
    check('SC alias not indexed in next','/deputados-estaduais/' not in future)
    check('root sitemap regenerated',(ROOT/'sitemap.xml').read_text()==sitemap(registry,'https://selvalabs.github.io/esquerda-em-foco/'))
    tax=load(ROOT/'config/taxonomies.json');counts={c['namespace']:len(c['concepts']) for c in tax['catalogs']}
    check('all four taxonomies intact',counts=={'sc-v1':29,'sp-product-v1':30,'rs-v1':28,'pr-v1':25})
    check('no inferred crosswalk',tax['reviewed_crosswalk']==[] and all(not c['equivalent_to'] for cat in tax['catalogs'] for c in cat['concepts']))
    check('SP science extension',any('ciencia' in c['source_id'] for c in tax['catalogs'][1]['concepts']))
    sources={
      '2026-sc-federais':('data/sc-semantic-v2/candidate-content.json','candidates'),
      '2026-sc-estaduais':('deputados-estaduais/data/candidaturas.json','candidates'),
      '2026-rs-federais':('rs/deputados-federais/dados.json','candidates'),
      '2026-rs-estaduais':('rs/deputados-estaduais/dados.json','candidates'),
      '2026-pr-federais':('pr/deputados-federais/dados.json','candidates'),
      '2026-pr-estaduais':('pr/deputados-estaduais/dados.json','candidates'),
      '2026-sp-federais':('sp/deputados-federais/dados.json','records')}
    adapted_total=0
    for e in registry['editions']:
        path,key=sources[e['edition_id']];root=rs_root if e['publication_status']=='branch_only' else ROOT
        if root is None:continue
        records=load(root/path)[key];before=json.dumps(records,ensure_ascii=False,sort_keys=True)
        adapters=[adapt_candidate(r,e,path) for r in records];adapted_total+=len(adapters)
        check(e['edition_id']+' adapter identities',len({a['key'] for a in adapters})==len(records))
        check(e['edition_id']+' adapter nonmutating',before==json.dumps(records,ensure_ascii=False,sort_keys=True))
        check(e['edition_id']+' votes never coerced',all([h.get('votes') for h in r.get('history',[])]==[h.get('votes') for h in a['history']] for r,a in zip(records,adapters)))
        check(e['edition_id']+' current collection stays opt-in',e['capabilities']['selected_collection']['state']==('ready' if e['edition_id']=='2026-sc-federais' else 'absent'))
    check('adapters cover published set',adapted_total >= 760, adapted_total)
    e=registry['editions'][0];sample={'id':'240000000000','history':[{'votes':None,'votes_status':'not_applicable'},{'votes':0,'votes_status':'verified_nominal'}],
      'research_status':'source_access_blocked','review_completed_in_round':False,'cpf':'DO_NOT_EXPORT','corrections':[{'before':'old','after':'new','reason':'source revision'}]}
    a=adapt_candidate(sample,e,'fixture');check('null distinct from zero',a['history'][0]['votes'] is None and a['history'][1]['votes']==0)
    check('research not review completion',a['research']['research_status']=='source_access_blocked' and a['research']['review_completed_in_round'] is False)
    check('private field excluded','DO_NOT_EXPORT' not in json.dumps(a));check('correction retained',a['corrections']==sample['corrections'])
    expected_failure('foreign identity rejected',lambda:adapt_candidate({**sample,'state':'SP'},e,'fixture'))
    claim=adapt_claim({'text':'fixture','period':'2026','direction':'atuacao_documentada','source_ids':['s']},'current_support')
    check('year alone does not imply current support',claim['filter_eligible'] is False)
    for c in tax['catalogs']:check(c['namespace']+' source hash',digest(ROOT/c['source'])==c['source_sha256'])


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*_args):pass


def browser_tests(out):
    registry=load(ROOT/'config/editions.json');fixtures=load(ROOT/'config/legacy-sc-links.json')
    serverroot=out/'server';serverroot.mkdir(parents=True,exist_ok=True)
    http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(serverroot)))
    threading.Thread(target=http.serve_forever,daemon=True).start()
    origin=f'http://127.0.0.1:{http.server_address[1]}'
    shots=out/'screenshots';shots.mkdir(exist_ok=True)
    with sync_playwright() as p:
        executable=shutil.which('chromium')
        browser=p.chromium.launch(headless=True,**({'executable_path':executable} if executable else {}))
        for prefix in ('/','/esquerda-em-foco/'):
            site=serverroot/prefix.strip('/') if prefix!='/' else serverroot
            base=origin+prefix
            report=build(site,base);check('build rehearsal '+prefix,report['root_replaced_in_repository'] is False)
            ctx=browser.new_context()
            ctx.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
            page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            for e in registry['editions']:
                if e['publication_status']!='published':continue
                for width in (320,360,390,430,768,1024,1440):
                    page.set_viewport_size({'width':width,'height':900});page.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded');page.wait_for_timeout(80)
                    measured=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth,ids:[...document.querySelectorAll("[id]")].map(n=>n.id)})')
                    check(f'{prefix}{e["edition_id"]} width {width}',measured['scroll']<=width+1,measured['scroll'])
                    check(f'{prefix}{e["edition_id"]} one shell {width}',page.locator('.eef-global-shell').count()==1)
                    check(f'{prefix}{e["edition_id"]} IDs {width}',len(measured['ids'])==len(set(measured['ids'])))
                    if width in (390,1440) and prefix=='/':page.screenshot(path=str(shots/f'{e["edition_id"]}-{width}.png'))
                page.locator('.eef-edition-menu>summary').click();page.keyboard.press('Escape')
                check(prefix+e['edition_id']+' Escape closes',not page.locator('.eef-edition-menu').evaluate('(e)=>e.open'))
                check(prefix+e['edition_id']+' return focus',page.locator('.eef-edition-menu>summary').evaluate('(e)=>e===document.activeElement'))
                check(prefix+e['edition_id']+' branch not linked',page.locator('.eef-global-shell a[href*="rs/deputados-estaduais"]').count()==0)
            page.goto(base);check(prefix+' plain root remains harness',page.locator('h1').inner_text()=='Validação da navegação global')
            page.goto(base+'#global-estados');check(prefix+' unknown fragment stays',urlsplit(page.url).path==prefix)
            for anchor in [next(a for a in fixtures['anchors'] if a.startswith('candidato-')),next(a for a in fixtures['anchors'] if a.startswith('partido-')),'fontes']:
                page.goto(base+'#'+anchor);page.wait_for_url('**/sc/deputados-federais/**')
                check(prefix+' legacy target '+anchor,page.locator('[id="'+anchor+'"]').count()==1 and page.url.endswith('#'+anchor))
            first,second=fixtures['candidate_ids'][:2]
            h=f'#selecionados={first},{second}&v=1&edicao=sc-federais&ficha={second}'
            page.goto(base+h);page.wait_for_selector('#eefCollection[open]')
            check(prefix+' legacy collection opens',page.locator('#eefCollection[open] article.candidate').count()==1)
            check(prefix+' legacy active preserved',page.locator('#eefCollection #candidato-'+second).count()==1)
            page.goto(base+'deputados-estaduais/#candidato-240002540095');page.wait_for_url('**/sc/deputados-estaduais/**')
            check(prefix+' state alias keeps fragment',page.url.endswith('#candidato-240002540095'))
            page.goto(base+'404.html');check(prefix+' 404 navigation',page.locator('.eef-edition-grid a').count()>=6)
            check(prefix+' no JS errors',not errors,errors)
            ctx.close()
            nojs=browser.new_context(java_script_enabled=False)
            nojs.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='127.0.0.1' else r.abort())
            page=nojs.new_page();page.goto(base)
            check(prefix+' noJS root access',page.locator('main a').count()>=1)
            for e in registry['editions']:
                if e['publication_status']!='published':continue
                page.goto(base+e['canonical_path'].lstrip('/'))
                check(prefix+e['edition_id']+' noJS cards',page.locator('article.candidate').count()>0)
                page.locator('.eef-edition-menu>summary').click();check(prefix+e['edition_id']+' noJS menu',page.locator('.eef-edition-menu').evaluate('(e)=>e.open'))
            nojs.close()
        browser.close()
    http.shutdown()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--rs-root',type=Path);ap.add_argument('--no-browser',action='store_true');args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    try:
        metadata_tests(args.rs_root)
        if not args.no_browser:browser_tests(args.out)
    except Exception as exc:
        CHECKS.append({'name':'uncaught_validation_error','passed':False,'detail':repr(exc)})
        raise
    finally:
        save(args.out/'validation.json',{'passed':all(c['passed'] for c in CHECKS),'checks':CHECKS,'count':len(CHECKS),'limits':['No live HTTP verification','No new political research','No physical device or screen reader','SP original hidden-hash finding remains outside this foundation']})
    print(json.dumps({'passed':True,'checks':len(CHECKS)},ensure_ascii=False))


if __name__=='__main__':main()

"""Simulate legacy SC/SP runtime replacement, then exercise the actual refresh.
The old research-generating pipelines are deliberately not replayed over new data.
Only a disposable worktree is changed. Baseline research/HTML remain untouched.
"""
from __future__ import annotations
import argparse,hashlib,json,os,subprocess,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
from query_validate import ROOT,BASE,server,context,start,snap,card_signature
CHECKS=[]
def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(out):
    work=out/'worktree';http=None
    env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','EEFOCO_OFFLINE_BUILD':'1'}
    subprocess.run(['git','worktree','add','--detach',str(work),'HEAD'],cwd=ROOT,check=True)
    specs=[('2026-sc-federais','sc/deputados-federais/index.html','assets/pauta-filters-editorial.js','sc-federal.js'),
           ('2026-sp-federais','sp/deputados-federais/index.html','sp/deputados-federais/assets/app.js','sp-federal.js')]
    try:
        home=sha(work/'index.html')
        research={str(p.relative_to(work)):sha(p) for p in work.rglob('*.json') if not str(p.relative_to(work)).startswith(('config/','data/global'))}
        for eid,page,runtime,source in specs:
            signature=card_signature(BeautifulSoup((work/page).read_text(),'html.parser'))
            managed=ROOT/'tools/global04/query_runtime'/source
            check(eid+' managed source matches released runtime',sha(managed)==sha(ROOT/runtime))
            (work/runtime).write_bytes(subprocess.check_output(['git','show',BASE+':'+runtime],cwd=ROOT))
            check(eid+' legacy replacement really differs',sha(work/runtime)!=sha(managed))
            with (out/(eid+'.log')).open('w') as log:
                subprocess.run([sys.executable,'tools/global03/refresh.py','--edition',eid,'--input',page,'--source-path',page],cwd=work,env=env,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=180)
            check(eid+' current runtime reapplied',sha(work/runtime)==sha(managed))
            check(eid+' every original card retained',signature==card_signature(BeautifulSoup((work/page).read_text(),'html.parser')))
        check('home unchanged',sha(work/'index.html')==home)
        check('research JSON unchanged',all((work/p).exists() and sha(work/p)==h for p,h in research.items()),len(research))
        http,base=server(work)
        with sync_playwright() as p:
            browser=p.chromium.launch();c=context(browser,base);g=c.new_page();g.set_default_timeout(10000);errors=[];g.on('pageerror',lambda e:errors.append(str(e)))
            for eid,page,_,_ in specs:
                url=base+page.removesuffix('index.html');start(g,url)
                valid=g.evaluate('EEFEditionQuery.valid');parties=valid['parties'][:2]
                if eid=='2026-sc-federais':
                    g.locator('#eefQueryParties').evaluate('(e)=>e.open=true')
                    for party in parties:g.locator('[data-eef-party="'+party+'"]').click()
                else:
                    g.locator('#filterDetails').evaluate('(e)=>e.open=true')
                    for party in parties:g.locator('[data-party-filter="'+party+'"]').click()
                expected=g.locator('article.candidate').evaluate_all('(els,ps)=>els.filter(c=>ps.includes(c.dataset.party)).map(c=>c.id).sort()',parties)
                actual=g.locator('article.candidate:not([hidden])').evaluate_all('els=>els.map(c=>c.id).sort()')
                check(eid+' rebuilt exact multiparty results',actual==expected and bool(actual))
                state=snap(g);g.locator('#eefShareQuery').click();link=g.locator('#eefQueryShareUrl').input_value();g.locator('#eefQueryShareClose').click();start(g,link)
                check(eid+' rebuilt query link',snap(g)==state)
                cid=actual[0].replace('candidato-','');g.locator('[data-eef-toggle="'+cid+'"]').click();g.locator('#eefSelectedNav').click();g.wait_for_selector('#eefCollection[open]');g.locator('#eefCollectionClose').click();g.wait_for_timeout(50)
                check(eid+' rebuilt collection retains query',snap(g)==state)
            check('rebuilt pages no JS errors',not errors,errors);c.close();browser.close()
    finally:
        if http:http.shutdown()
        subprocess.run(['git','worktree','remove','--force',str(work)],cwd=ROOT,check=False)
def main():
    a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);args=a.parse_args();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    try:run(out)
    except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
    finally:(out/'maintenance.json').write_text(json.dumps({'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,'scope':'Runtime overwrite simulation plus real refresh/browser; not full SC/SP research regeneration'},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

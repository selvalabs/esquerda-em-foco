"""Browser checks for the closure disclosure; extend, never replace, earlier QA."""
from __future__ import annotations
import functools
import http.server
import json
import socketserver
import threading
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/rs-estaduais';P=ROOT/'rs/deputados-estaduais'
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def run():
    report=json.loads((DOC/'browser-qa.json').read_text())
    if not report['passed']:raise ValueError('Previous browser gate must pass first')
    records=json.loads((P/'dados.json').read_text())['candidates']
    checks=[];errors=[]
    def check(name,passed,detail=None):checks.append({'name':'closure: '+name,'passed':bool(passed),'detail':detail})
    server=socketserver.TCPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_address[1]}/rs/deputados-estaduais/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch()
            page=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(base,wait_until='networkidle')
            check('all candidates have a disclosure',page.locator('details[data-close-status]').count()==len(records))
            response=page.request.get(base+'pesquisa-status.json')
            check('research JSON available',response.status==200)
            research=response.json()
            check('research JSON covers all candidates',research['candidate_count']==len(records) and len(research['candidates'])==len(records))
            check('status totals close exactly',sum(research['status_counts'].values())==len(records))
            chosen=next(c for c in records if c['research_status']['status']=='source_access_blocked')
            page.fill('#searchInput',chosen['number'])
            candidate=page.locator('#candidato-'+chosen['id'])
            disclosure=candidate.locator('details[data-close-status]')
            summary=disclosure.locator('summary')
            summary.focus();page.keyboard.press('Enter')
            check('disclosure opens by keyboard',disclosure.get_attribute('open') is not None)
            check('blocked source not described as no proposals','não uma avaliação' in disclosure.inner_text())
            page.keyboard.press('Enter')
            check('disclosure closes by keyboard',disclosure.get_attribute('open') is None)
            for width in (320,360,390,768,1024,1440):
                page.set_viewport_size({'width':width,'height':844 if width<768 else 1000})
                if disclosure.get_attribute('open') is None:summary.click()
                box=page.evaluate('({width:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth})')
                check(f'expanded disclosure no horizontal overflow {width}',box['scroll']<=box['width']+1,box)
                if width in (390,1440):
                    candidate.screenshot(path=str(DOC/'screenshots'/f'research-status-{width}.png'))
            page.goto(base+'#candidato-'+chosen['id'],wait_until='networkidle')
            check('direct candidate link retains disclosure',page.locator('#candidato-'+chosen['id']+' details[data-close-status]').count()==1)
            check('original historical controls remain separate',page.locator('.rs-history summary').count()==len(records))
            check('no closure runtime errors',not errors,errors)
            browser.close()
    finally:
        server.shutdown();server.server_close()
        report['checks']=[x for x in report['checks'] if not x['name'].startswith('closure: ')]+checks
        report['check_count']=len(report['checks'])
        report['passed']=all(x['passed'] for x in report['checks']) and not errors
        report['closure_checked_at']=datetime.now(timezone.utc).isoformat()
        report['closure_runtime_errors']=errors
        report['screenshots']=[p.name for p in sorted((DOC/'screenshots').glob('*.png'))]
        (DOC/'browser-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        (DOC/'ad2-close/browser-closure.json').write_text(json.dumps({'checks':checks,'passed':all(x['passed'] for x in checks),'runtime_errors':errors},ensure_ascii=False,indent=2)+'\n')
    if not report['passed']:raise AssertionError('Closure browser checks failed')
    print(json.dumps({'combined_browser_checks':report['check_count'],'passed':report['passed']}))
if __name__=='__main__':run()

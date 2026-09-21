"""Run real Chromium checks and retain representative screenshots, not a giant 145-card image."""
from __future__ import annotations
import functools
import http.server
import json
import socketserver
import threading
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
A=ROOT/'docs/rs-estaduais'
P=ROOT/'rs/deputados-estaduais'

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def run():
    A.mkdir(parents=True,exist_ok=True)
    screenshots=A/'screenshots';screenshots.mkdir(exist_ok=True)
    data=json.loads((P/'dados.json').read_text())
    records=data['candidates']
    checks=[];errors=[];console=[];responses=[]
    def check(name,condition,detail=None):
        checks.append({'name':name,'passed':bool(condition),'detail':detail})
    handler=functools.partial(QuietHandler,directory=str(ROOT))
    server=socketserver.TCPServer(('127.0.0.1',0),handler)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    base=f'http://127.0.0.1:{server.server_address[1]}/rs/deputados-estaduais/'
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch()
            page=browser.new_page(viewport={'width':1440,'height':1000},reduced_motion='reduce',device_scale_factor=1)
            page.on('pageerror',lambda error:errors.append(str(error)))
            page.on('console',lambda message:console.append({'type':message.type,'text':message.text}) if message.type=='error' else None)
            page.on('response',lambda response:responses.append({'url':response.url,'status':response.status}) if response.url.startswith(base) and response.status>=400 else None)
            page.goto(base,wait_until='networkidle',timeout=60000)
            page.wait_for_function('Boolean(window.EEFOCO_STATE)',timeout=10000)
            check('all cards rendered',page.locator('article.candidate').count()==len(records))
            check('all cards visible initially',page.locator('article.candidate:not([hidden])').count()==len(records))
            check('state office visible',page.locator('.office-title').inner_text()=='Deputado(a) Estadual')
            for width in (320,360,390,768,1024,1440):
                page.set_viewport_size({'width':width,'height':900 if width>760 else 844})
                page.evaluate('window.EEFOCO_STATE.clear()')
                page.evaluate('window.scrollTo(0,0)')
                dimensions=page.evaluate('({client:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
                check(f'no horizontal overflow {width}',dimensions['scroll']<=dimensions['client']+1 and dimensions['body']<=dimensions['client']+1,dimensions)
                if width in (390,1440):page.screenshot(path=str(screenshots/f'hero-{width}.png'),full_page=False)
            page.set_viewport_size({'width':1440,'height':1000})
            for party in sorted({c['party'] for c in records}):
                page.select_option('#partyFilter',party)
                actual=page.locator('article.candidate:not([hidden])').count()
                expected=sum(c['party']==party for c in records)
                check('party filter '+party,actual==expected,{'actual':actual,'expected':expected})
            page.click('#clearFilters')
            page.fill('#searchInput','PT')
            check('exact party text search',page.locator('article.candidate:not([hidden])').count()==sum(c['party']=='PT' for c in records))
            page.fill('#searchInput','luciana genro')
            check('name search',page.locator('article.candidate:not([hidden])').count()==1)
            page.fill('#searchInput','ZE NUNES')
            check('accent insensitive search',page.locator('article.candidate:not([hidden])').count()==1)
            selected=records[0]
            page.fill('#searchInput',selected['number'])
            check('ballot number search',page.locator('article.candidate:not([hidden])').count()==1)
            page.fill('#searchInput','zzzz-no-such-candidate-000000')
            check('empty search state',page.locator('article.candidate:not([hidden])').count()==0 and page.locator('#emptyResults').is_visible())
            page.click('#clearFilters')
            check('clear restores and focuses',page.locator('article.candidate:not([hidden])').count()==len(records) and page.locator('#searchInput').evaluate('(el)=>el===document.activeElement'))
            for value in ('true','false'):
                page.select_option('#historyFilter',value)
                expected=sum(str(any(h['year']<2026 for h in c['history'])).lower()==value for c in records)
                check('history filter '+value,page.locator('article.candidate:not([hidden])').count()==expected)
            page.click('#clearFilters')
            page.select_option('#statusFilter',records[0]['status'])
            check('status filter',page.locator('article.candidate:not([hidden])').count()==sum(c['status']==records[0]['status'] for c in records))
            page.fill('#searchInput','no-matches')
            page.evaluate('(id)=>{location.hash="candidato-"+id}',selected['id'])
            page.wait_for_function('(id)=>!document.getElementById("candidato-"+id).hidden',arg=selected['id'])
            check('hidden deep link clears conflicting filters',page.locator('#candidato-'+selected['id']).is_visible() and page.input_value('#searchInput')=='')
            page.locator('#candidato-'+selected['id']+' .rs-history summary').click()
            check('history disclosure',page.locator('#candidato-'+selected['id']+' .rs-history').get_attribute('open') is not None)
            timings=page.evaluate('''() => ({
                before: EEFOCO_STATE.days(new Date('2026-09-22T02:59:59Z')),
                after: EEFOCO_STATE.days(new Date('2026-09-22T03:00:00Z')),
                empty: EEFOCO_STATE.rotated([],7),
                single: EEFOCO_STATE.rotated(['PT'],12)
            })''')
            check('São Paulo midnight boundary',timings['before']==0 and timings['after']==1,timings)
            check('empty and single rotation safe',timings['empty']==[] and timings['single']==['PT'])
            order_script='Array.from(document.querySelectorAll(".party-section")).map(s=>({party:s.dataset.partySection,ids:Array.from(s.querySelectorAll("article.candidate")).map(c=>c.dataset.tseId)}))'
            page.evaluate("EEFOCO_STATE.rotate(new Date('2026-09-21T15:00:00Z'))")
            first=page.evaluate(order_script)
            page.evaluate("EEFOCO_STATE.rotate(new Date('2026-09-21T15:00:00Z'))")
            check('stable order on same date',first==page.evaluate(order_script))
            page.evaluate("EEFOCO_STATE.rotate(new Date('2026-09-22T15:00:00Z'))")
            second=page.evaluate(order_script)
            check('parties rotate by one',[s['party'] for s in second]==[s['party'] for s in first[1:]+first[:1]])
            original={s['party']:s['ids'] for s in first}
            check('candidates rotate independently',all(s['ids']==original[s['party']][1:]+original[s['party']][:1] for s in second))
            page.evaluate('EEFOCO_STATE.rotate(new Date());EEFOCO_STATE.clear()')
            # Check all image bytes; loading every lazy image avoids false missing-image passes.
            page.evaluate('document.querySelectorAll("img[loading]").forEach(i=>i.loading="eager")')
            page.wait_for_function('Array.from(document.querySelectorAll(".candidate-photo")).every(i=>i.complete)',timeout=30000)
            broken=page.locator('.candidate-photo').evaluate_all('(images)=>images.filter(i=>!i.naturalWidth).map(i=>i.src)')
            check('all official portraits load',not broken,broken)
            for name in ('dados.json','fontes.json','cobertura.json','candidaturas.csv','sitemap.xml','site.webmanifest','assets/og-rs-estaduais.png'):
                response=page.request.get(base+name)
                check('export available '+name,response.status==200)
            page.set_viewport_size({'width':390,'height':844})
            page.evaluate('window.scrollTo(0,0)')
            menu=page.locator('#siteNavMenu')
            if menu.is_visible():
                menu.click()
                check('mobile menu expands',menu.get_attribute('aria-expanded')=='true')
                page.keyboard.press('Escape')
                check('mobile menu Escape and focus',menu.get_attribute('aria-expanded')=='false' and menu.evaluate('(el)=>el===document.activeElement'))
            else:check('mobile menu visible',False)
            page.fill('#searchInput','luciana genro')
            candidate=page.locator('article.candidate:not([hidden])')
            candidate.scroll_into_view_if_needed()
            page.screenshot(path=str(screenshots/'candidate-mobile.png'),full_page=False)
            page.set_viewport_size({'width':1440,'height':1000})
            candidate.screenshot(path=str(screenshots/'candidate-desktop.png'))
            check('result count announced politely',page.locator('#resultCount').get_attribute('aria-live')=='polite')
            check('no browser runtime errors',not errors,errors)
            check('no local resource failures',not responses,responses)
            browser.close()
    finally:
        server.shutdown();server.server_close()
        report={'checked_at':datetime.now(timezone.utc).isoformat(),'passed':all(x['passed'] for x in checks),'check_count':len(checks),'checks':checks,'page_errors':errors,'console_errors':console,'resource_errors':responses,'screenshots':[p.name for p in sorted(screenshots.glob('*.png'))]}
        (A/'browser-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(report,ensure_ascii=False,indent=2))
    assert report['passed'],'Browser QA failed; inspect docs/rs-estaduais/browser-qa.json'

if __name__=='__main__':run()

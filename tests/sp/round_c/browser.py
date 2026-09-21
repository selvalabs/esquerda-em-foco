"""Real HTTP browser checks for SP-C; run with Playwright Chromium in CI.
No external website is used as a test oracle. Sources have their own availability report.
"""
from __future__ import annotations
import functools, hashlib, json, os, threading, time, traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[3]
DOC=ROOT/'docs/sp/round-c'; SHOTS=DOC/'screenshots'
PRODUCT=json.loads((ROOT/'sp/deputados-federais/dados.json').read_text())
RECORDS=PRODUCT['records']; BYID={r['id']:r for r in RECORDS}
RESULTS=[]
class Handler(SimpleHTTPRequestHandler):
    def translate_path(self,path):
        if path.startswith('/esquerda-em-foco/'):path=path[len('/esquerda-em-foco'):]
        return super().translate_path(path)
    def log_message(self,*args):pass


def check(name,fn):
    start=time.monotonic()
    try:
        detail=fn()
        RESULTS.append({'name':name,'result':'PASS','seconds':round(time.monotonic()-start,3),'details':detail})
        print('PASS',name,flush=True)
    except Exception as exc:
        RESULTS.append({'name':name,'result':'FAIL','seconds':round(time.monotonic()-start,3),'error':str(exc),'traceback':traceback.format_exc()})
        print('FAIL',name,str(exc),flush=True)


def width_check(page):
    sizes=page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
    assert sizes['scroll']<=sizes['width']+1,sizes
    return sizes

def visible(page):return page.locator('article.candidate:not([hidden])').count()
def wait_count(page,n):
    expect(page.locator('#resultCount')).to_have_text(f'{n} de 249 registros')
    assert visible(page)==n,(visible(page),n)
def go(page,url):
    response=page.goto(url,wait_until='domcontentloaded')
    assert response and response.status==200
    page.wait_for_function("document.documentElement.classList.contains('js')")
    return response

def main():
    DOC.mkdir(parents=True,exist_ok=True);SHOTS.mkdir(exist_ok=True)
    server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Handler,directory=str(ROOT)))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    origin=f'http://127.0.0.1:{server.server_port}'
    url=origin+'/esquerda-em-foco/sp/deputados-federais/'
    screenshots=[];asset_failures=[];page_errors=[]
    with sync_playwright() as pw:
        launch={'headless':True}
        if os.getenv('PLAYWRIGHT_CHROMIUM_EXECUTABLE'):launch['executable_path']=os.environ['PLAYWRIGHT_CHROMIUM_EXECUTABLE']
        browser=pw.chromium.launch(**launch)
        context=browser.new_context(viewport={'width':1440,'height':1000},locale='pt-BR',timezone_id='America/Sao_Paulo',reduced_motion='reduce')
        context.route('**/*',lambda route:route.continue_() if route.request.url.startswith(origin) or route.request.url.startswith('data:') else route.abort())
        page=context.new_page();page.set_default_timeout(15000)
        page.on('pageerror',lambda err:page_errors.append(str(err)))
        page.on('response',lambda r:asset_failures.append({'url':r.url,'status':r.status}) if r.url.startswith(origin) and r.status>=400 else None)
        def screen(name):
            path=SHOTS/name;page.screenshot(path=str(path));screenshots.append(str(path.relative_to(ROOT)))
        def initial():
            start=time.monotonic();go(page,url);wait_count(page,249)
            width_check(page)
            assert page.locator('#filterDetails').evaluate('(e)=>e.open')
            assert page.locator('[data-party-filter]').count()==12
            assert page.locator('[data-topic-filter]').count()==30
            screen('desktop-1440.png')
            return {'load_and_ready_seconds':round(time.monotonic()-start,3),'cards':249,'viewport':'1440x1000'}
        check('initial_page_under_GitHub_Pages_subpath',initial)
        def party_union():
            page.locator('[data-party-filter="PT"]').click();wait_count(page,49)
            assert 'partidos=PT' in page.url
            page.locator('[data-party-filter="PSOL"]').click();wait_count(page,85)
            page.locator('[data-party-filter="PT"]').click();wait_count(page,36)
            page.locator('[data-party-filter=""]').click();wait_count(page,249)
        check('party_selection_OR_and_clear',party_union)
        def topics_any_all():
            page.locator('[data-topic-filter="saude"]').click()
            page.locator('[data-topic-filter="educacao"]').click()
            union=sum(bool({'saude','educacao'} & {t['id'] for t in r['themes_2026']}) for r in RECORDS)
            intersection=sum({'saude','educacao'} <= {t['id'] for t in r['themes_2026']} for r in RECORDS)
            wait_count(page,union);page.locator('#topicMode').select_option('todos');wait_count(page,intersection)
            page.locator('[data-party-filter="PT"]').click()
            n=sum(r['party']=='PT' and {'saude','educacao'} <= {t['id'] for t in r['themes_2026']} for r in RECORDS)
            wait_count(page,n)
            return {'union':union,'intersection':intersection,'intersection_PT':n}
        check('topic_union_intersection_and_party_combination',topics_any_all)
        def state_reload():
            saved=page.url;before=visible(page)
            page.reload(wait_until='domcontentloaded');page.wait_for_function("document.documentElement.classList.contains('js')")
            wait_count(page,before);assert page.url==saved
            assert page.locator('#topicMode').input_value()=='todos'
            expect(page.locator('[data-topic-filter="saude"]')).to_have_attribute('aria-pressed','true')
            page.locator('[data-party-filter="PSOL"]').click();after=visible(page)
            page.go_back();wait_count(page,before)
            page.go_forward();wait_count(page,after)
            return {'reload_count':before,'forward_count':after}
        check('shareable_URL_reload_back_and_forward',state_reload)
        def search():
            go(page,url);page.locator('#searchInput').fill('sâmia 5000');wait_count(page,1)
            assert page.locator('article.candidate:not([hidden])').get_attribute('data-id')=='250002539604'
            page.locator('#searchInput').fill('<script>window.injected=true</script>');wait_count(page,0)
            assert page.evaluate('typeof window.injected')=='undefined'
            expect(page.locator('#emptyResults')).to_be_visible()
        check('accent_search_AND_terms_and_XSS_text_only',search)
        def zero_and_status():
            go(page,url);page.locator('[data-party-filter="PCB"]').click();wait_count(page,0)
            page.locator('#emptyResults [data-clear-filters]').click();wait_count(page,249)
            page.locator('#statusFilter').select_option('renuncia');wait_count(page,6)
            assert all(s=='renuncia' for s in page.locator('article.candidate:not([hidden])').evaluate_all('(xs)=>xs.map(x=>x.dataset.status)'))
        check('zero_party_empty_state_and_renunciations',zero_and_status)
        def evidence():
            go(page,url+'?q=5000');wait_count(page,1)
            card=page.locator('#candidato-250002539604')
            button=card.locator('[data-show-evidence="saude"]');button.click()
            expect(button).to_have_attribute('aria-expanded','true')
            details=card.locator('.current-evidence');assert details.evaluate('(e)=>e.open')
            selected=details.locator('.claim:not([hidden])')
            assert selected.count()>=1
            assert all('saude' in x.split() for x in selected.evaluate_all('(xs)=>xs.map(x=>x.dataset.topics)'))
            assert details.locator('a[href^="https://"]').count()>0
            card.screenshot(path=str(SHOTS/'evidence-card.png'));screenshots.append('docs/sp/round-c/screenshots/evidence-card.png')
            details.locator('[data-all-evidence]').click()
            assert details.locator('.claim:not([hidden])').count()==len(BYID['250002539604']['claims_2026'])
            details.locator('summary').click();expect(button).to_have_attribute('aria-expanded','false')
        check('topic_chip_opens_exact_claim_and_source',evidence)
        def legacy_and_invalid():
            go(page,url+'?pautas=apostas-protecao-economica');wait_count(page,2)
            expect(page.locator('[data-topic-filter="apostas-jogos"]')).to_have_attribute('aria-pressed','true')
            go(page,url+'?partidos=FAKE,PT&pautas=unknown&situacao=bad');wait_count(page,49)
            expect(page.locator('#filterWarning')).to_be_visible()
        check('legacy_topic_alias_and_invalid_URL_handling',legacy_and_invalid)
        def historical_exclusion():
            old=[r for r in RECORDS if r['claims_other'] and not r['claims_2026']]
            for r in old:
                go(page,url+'?q='+r['number']);wait_count(page,1)
                card=page.locator('#candidato-'+r['id'])
                assert card.locator('[data-show-evidence]').count()==0
                assert not r['themes_2026']
            return {'history_or_undated_only_records':len(old)}
        check('historical_only_six_records_excluded_from_current_tags',historical_exclusion)
        def copy_and_anchor():
            page.add_init_script("Object.defineProperty(navigator,'clipboard',{value:{writeText:()=>Promise.reject(new Error('denied'))},configurable:true});")
            go(page,url+'?partidos=PT&pautas=saude')
            page.locator('#shareFilters').click();expect(page.locator('#shareFallback')).to_be_visible()
            shared=page.locator('#shareURL').input_value();assert 'partidos=PT' in shared and 'pautas=saude' in shared
            page.keyboard.press('Escape');expect(page.locator('#shareFallback')).not_to_be_visible()
            go(page,url+'?q=5000');page.locator('[data-share-candidate="250002539604"]').click()
            copied=page.locator('#shareURL').input_value();assert '?' not in copied and copied.endswith('#candidato-250002539604')
            go(page,copied);wait_count(page,249);page.wait_for_timeout(150)
            el=page.locator('#candidato-250002539604');box=el.bounding_box();assert box and box['y']<1000
            return {'filters_copy_fallback':True,'candidate_link_excludes_filters':True}
        check('clipboard_fallback_and_candidate_permalink',copy_and_anchor)
        def alphabetical():
            go(page,url);page.locator('#orderFilter').select_option('alfabetica')
            ordered=page.locator('.party-group:not([hidden])').evaluate_all('(xs)=>xs.map(x=>x.dataset.party)')
            expected=page.evaluate("(a)=>a.sort((x,y)=>x.localeCompare(y,'pt-BR',{sensitivity:'base'}))",list({r['party'] for r in RECORDS}))
            assert ordered==expected,(ordered,expected)
            assert 'ordem=alfabetica' in page.url
            page.locator('#seeResults').click();assert page.locator('#filterDetails').evaluate('(e)=>e.open')
        check('alphabetical_option_and_desktop_filters_stay_open',alphabetical)
        def keyboard():
            go(page,url)
            button=page.locator('[data-party-filter="PT"]');button.focus();page.keyboard.press('Space');wait_count(page,49)
            expect(button).to_have_attribute('aria-pressed','true')
            page.keyboard.press('Space');wait_count(page,249)
            page.locator('#searchInput').focus();page.keyboard.insert_text('5070');page.keyboard.press('Enter');wait_count(page,1)
            card=page.locator('#candidato-250002539612');summary=card.locator('.current-evidence > summary');summary.focus();page.keyboard.press('Enter')
            assert card.locator('.current-evidence').evaluate('(e)=>e.open')
        check('keyboard_buttons_and_native_disclosures',keyboard)
        for w,h in [(320,740),(390,844),(768,1024),(1440,1000)]:
            def viewport_case(w=w,h=h):
                page.set_viewport_size({'width':w,'height':h});go(page,url);wait_count(page,249)
                width_check(page)
                if w<=760:
                    assert not page.locator('#filterDetails').evaluate('(e)=>e.open')
                    page.locator('#siteNavMenu').click();expect(page.locator('#siteNavMenu')).to_have_attribute('aria-expanded','true')
                    width_check(page);page.keyboard.press('Escape');expect(page.locator('#siteNavMenu')).to_have_attribute('aria-expanded','false')
                    page.locator('#filterDetails > summary').click()
                    page.locator('[data-topic-filter="educacao"]').click();wait_count(page,20)
                    page.locator('#seeResults').click();page.wait_for_timeout(120)
                    assert not page.locator('#filterDetails').evaluate('(e)=>e.open')
                    assert page.locator('#resultsStart').evaluate('(e)=>e===document.activeElement')
                    width_check(page);screen(f'mobile-results-{w}.png')
                    go(page,url);screen(f'mobile-top-{w}.png')
                else:
                    assert page.locator('#filterDetails').evaluate('(e)=>e.open')
                    screen(f'viewport-{w}.png')
                return {'width':w,'height':h,'overflow':0}
            check(f'viewport_{w}_responsive_navigation_filters',viewport_case)
        def zoom():
            page.set_viewport_size({'width':1280,'height':900});go(page,url)
            page.evaluate("document.documentElement.style.zoom='2'");width_check(page)
            screen('zoom-200-percent.png')
            page.evaluate("document.documentElement.style.zoom='1'")
            return {'css_zoom':2,'viewport':'1280x900'}
        check('200_percent_zoom_reflow',zoom)
        def all_photos():
            go(page,url)
            page.locator('.portrait img').evaluate_all("xs=>xs.forEach(x=>x.loading='eager')")
            page.wait_for_function("[...document.querySelectorAll('.portrait img')].every(x=>x.complete)")
            broken=page.locator('.portrait img').evaluate_all('xs=>xs.filter(x=>!x.naturalWidth).map(x=>x.src)')
            assert not broken,broken
            return {'decoded_photos':249}
        check('all_249_local_portraits_decode',all_photos)
        def fallback_photo():
            card=page.locator('article.candidate').first
            img=card.locator('.portrait img');img.evaluate("x=>{x.src='data:image/png;base64,invalid';}")
            expect(img).not_to_be_visible()
            width_check(page)
        check('broken_photo_fallback_does_not_break_layout',fallback_photo)
        def VPS_root():
            go(page,origin+'/sp/deputados-federais/?partidos=REDE');wait_count(page,10)
            width_check(page)
            response=page.goto(origin+'/sp/',wait_until='domcontentloaded');assert response.status==200
            page.locator('a[href="deputados-federais/"]').click();page.wait_for_function("document.documentElement.classList.contains('js')");wait_count(page,249)
        check('VPS_root_and_SP_hub_routes',VPS_root)
        def nojs():
            ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844})
            p=ctx.new_page();r=p.goto(url,wait_until='domcontentloaded');assert r.status==200
            assert p.locator('article.candidate').count()==249
            assert not p.locator('aside.rail').is_visible()
            p.locator('.current-evidence > summary').first.click()
            assert p.locator('.current-evidence').first.evaluate('(e)=>e.open')
            width_check(p);p.screenshot(path=str(SHOTS/'no-js-mobile.png'));screenshots.append('docs/sp/round-c/screenshots/no-js-mobile.png')
            ctx.close();return {'cards_without_JS':249,'disclosures_native':True}
        check('no_javascript_progressive_enhancement',nojs)
        def legacy():
            paths=['index.html','deputados-estaduais/index.html','rs/deputados-federais/index.html','pr/deputados-federais/index.html','pr/deputados-estaduais/index.html']
            observations=[]
            for path in paths:
                target=origin+'/esquerda-em-foco/'+path
                baseline=BeautifulSoup((ROOT/path).read_text(),'html.parser')
                for w in (390,1440):
                    page.set_viewport_size({'width':w,'height':1000})
                    r=page.goto(target,wait_until='domcontentloaded');assert r.status==200
                    assert page.locator('h1').count()>=1
                    assert page.locator('article.candidate').count()==len(baseline.select('article.candidate'))
                    observations.append({'path':path,'viewport':w,'cards':len(baseline.select('article.candidate')),'width':page.evaluate('document.documentElement.scrollWidth')})
            page.goto(origin+'/esquerda-em-foco/',wait_until='domcontentloaded')
            page.locator('a.edition-sp-link').click();page.wait_for_function("document.documentElement.classList.contains('js')");wait_count(page,249)
            return observations
        check('SP_runtime_has_no_pageerrors_or_local_asset_failures',lambda:(_ for _ in ()).throw(AssertionError({'errors':page_errors,'assets':asset_failures})) if page_errors or asset_failures else {'pageerrors':0,'asset_failures':0})
        page_errors.clear();asset_failures.clear()
        check('SC_RS_PR_existing_editions_smoke_and_home_link',legacy)
        legacy_runtime={'pageerrors':page_errors,'asset_failures':asset_failures}
        context.close();browser.close()
    server.shutdown();server.server_close()
    report={'gate':'PASS' if all(x['result']=='PASS' for x in RESULTS) else 'BLOCKED','browser':'Chromium / Playwright','browser_version_note':'See GitHub Actions environment/log; real HTTP local server','tests':len(RESULTS),'passed':sum(x['result']=='PASS' for x in RESULTS),'failed':sum(x['result']=='FAIL' for x in RESULTS),'results':RESULTS,'screenshots':screenshots,'legacy_runtime_observations':legacy_runtime,'scope':'Interface and frozen-data integration, not a new editorial fact-check.'}
    (DOC/'browser-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ['results','legacy_runtime_observations']},ensure_ascii=False,indent=2))
    if report['gate']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()

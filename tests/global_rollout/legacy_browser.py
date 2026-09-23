"""Exact legacy meaning and source checks under the new shared interface.
Uses frozen v1 queries, not renamed global groups. No external political research.
"""
from __future__ import annotations
import json
from pathlib import Path
from urllib.parse import urlencode
from playwright.sync_api import expect
ROOT=Path(__file__).resolve().parents[2]

def legacy_link(url,eid,**changes):
    legacy=json.loads((ROOT/'config/rollout-legacy.json').read_text())['editions'][eid]['valid']
    state=dict(edition_id=eid,q='',parties=[],topics=[],status='',mandate='',history='',region='',mode=legacy['modes'][0],order=legacy['orders'][0],semantic=legacy['semantic'])
    state.update(changes)
    return url+'#'+urlencode(dict(eef='query',v='1',edition=eid,state=json.dumps(state,ensure_ascii=False,separators=(',',':'))))

def context(browser,site,width):
    ctx=browser.new_context(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
    ctx.route('**/*',lambda r:r.continue_() if r.request.url.startswith(site) or r.request.url.startswith('data:') else r.abort())
    return ctx

def go(page,address):
    page.goto('about:blank');response=page.goto(address,wait_until='domcontentloaded')
    assert response and response.status==200
    page.wait_for_function("Boolean(window.EEFQueryUI&&window.EEFCollectionUI&&window.EEFCanonicalQuery)")

def width_ok(page):assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+1')
def visible(page):return page.locator('article.candidate:not([hidden])')

def sc(browser,site,out):
    results=[];url=site+'sc/deputados-federais/'
    for width in (390,1440):
        ctx=context(browser,site,width);page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        go(page,url);assert visible(page).count()==48
        assert page.locator('[data-cq-topic]').count()==39 and page.locator('[data-cq-group]').count()==16
        assert page.evaluate("EEFEditionQuery.valid.legacy_contract.valid.topics.length")==13
        go(page,legacy_link(url,'2026-sc-federais',topics=['economia-estado']))
        assert visible(page).count()==4
        ju=page.locator('#candidato-240002533832');ju.locator('[data-cq-reason]').click()
        evidence=ju.locator('.cc-proof [data-cc-evidence]:not([hidden])')
        text='\n'.join(evidence.locator('.cc-evidence-text').all_inner_texts())
        assert 'Defende impostos proporcionais à renda e ao patrimônio.' in text
        assert evidence.locator('.cc-source a[href^="https://"]').count()>0
        objects=evidence.locator('.cc-evidence-meta').all_inner_texts()
        assert objects
        page.locator('#searchInput').fill('impostos proporcionais')
        found=visible(page).evaluate_all('xs=>xs.map(c=>c.dataset.tseId)');assert found==['240002533832'],found
        page.screenshot(path=str(out/f'{width}-economia.png'))
        go(page,legacy_link(url,'2026-sc-federais',topics=['trabalho-renda']))
        ana=page.locator('#candidato-240002533824');ana.locator('[data-cq-reason]').click()
        evidence=ana.locator('.cc-proof [data-cc-evidence]:not([hidden])')
        current_text='\n'.join(evidence.locator('.cc-evidence-text,.cc-evidence-meta').all_inner_texts())
        assert '6×1' not in current_text,current_text
        assert '6×1' in ana.locator('[data-pauta-section="historico"]').inner_text()
        assert evidence.locator('.cc-source a[href^="https://"]').count()>0
        width_ok(page);assert not errors,errors
        page.screenshot(path=str(out/f'{width}-historico.png'))
        results.append(dict(width=width,initial_candidates=48,legacy_macro_definitions=13,global_topics=39,global_groups=16,economia_results=4,taxation_text_verified=True,search_candidate_ids=found,history_not_used_as_support=True,specific_match_sources_checked=True,js_errors=errors,overflow=False))
        ctx.close()
    return results

def sp(browser,site,out,rows):
    results=[];url=site+'sp/deputados-federais/';expected=sum(r['party']=='PT' and any(t['id']=='saude' for t in r['themes_2026']) for r in rows)
    for width in (1440,390):
        ctx=context(browser,site,width);page=ctx.new_page();page.set_default_timeout(20000);errors=[];assets=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.on('response',lambda r:assets.append({'url':r.url,'status':r.status}) if r.url.startswith(site) and r.status>=400 else None)
        def count(n):
            expect(page.locator('#resultCount')).to_have_text(f'{n} de 249 registros')
            assert visible(page).count()==n
        go(page,url);count(249)
        cfg=json.loads(page.locator('#cqData').text_content())
        assert page.locator('[data-cq-party]').count()==len(cfg['parties'])
        assert page.locator('#cqClearParties').count()==1
        assert page.locator('[data-cq-topic]').count()==len(cfg['topics'])==39
        assert page.locator('[data-cq-group]').count()==len(cfg['groups'])==16
        page.locator('#cqPanel>summary').click();page.locator('[data-cq-party="PT"]').click();count(49)
        width_ok(page);page.screenshot(path=str(out/f'sp-published-{width}.png'))
        results.append(dict(name='initial_page_and_party',width=width,records=249,PT=49,result='PASS'))
        go(page,legacy_link(url,'2026-sp-federais',parties=['PT'],topics=['saude']));count(expected)
        page.locator('#eefShareQuery').click();shared=page.locator('#eefQueryShareUrl').input_value();assert '#eef=query&v=2&edition=2026-sp-federais&taxonomy=1.0.0&state=' in shared
        page.locator('#eefQueryShareClose').click();go(page,shared);count(expected);page.reload(wait_until='domcontentloaded');count(expected);width_ok(page)
        results.append(dict(name='legacy_party_topic_new_share_and_reload',width=width,records=expected,result='PASS'))
        for party,n in [('PSTU',5),('REDE',10),('PCB',0)]:
            go(page,url+'?partidos='+party);count(n)
            assert visible(page).locator('[data-show-evidence]').count()==0
            if n==0:expect(page.locator('#emptyResults')).to_be_visible()
        results.append(dict(name='parties_without_inferred_topics',width=width,result='PASS'))
        go(page,url+'?q=5070');count(1);card=page.locator('#candidato-250002539612');card.locator('.current-evidence>summary').click()
        assert card.locator('.current-evidence').evaluate('(e)=>e.open') and card.locator('[data-claim-id]').count()>=1
        assert card.locator('a[href^="https://www.camara.leg.br/"]').count()>=1
        card.locator('.cc-proof>summary').click();assert card.locator('.cc-proof .cc-source a').count()>0; width_ok(page)
        results.append(dict(name='search_and_documented_evidence',width=width,result='PASS'))
        go(page,url);page.locator('.portrait img').evaluate_all("xs=>xs.forEach(x=>x.loading='eager')")
        page.wait_for_function("[...document.querySelectorAll('.portrait img')].every(x=>x.complete)")
        broken=page.locator('.portrait img').evaluate_all('xs=>xs.filter(x=>!x.naturalWidth).map(x=>x.src)');assert not broken,broken
        assert not errors and not assets,dict(errors=errors,assets=assets)
        results.append(dict(name='all_portraits_and_runtime',width=width,decoded_photos=249,result='PASS'))
        if width==1440:
            page.goto(site,wait_until='domcontentloaded');assert page.locator('.global-state').count()==4 and page.locator('article.candidate').count()==0
            page.locator('#global-estado-sc h3 a').click();page.wait_for_url(site+'sc/')
            page.locator('.global-office-card a[href*="deputados-federais"]').click();page.wait_for_url(site+'sc/deputados-federais/')
            assert page.locator('article.candidate').count()==48 and page.locator('[data-cq-topic]').count()==39
            page.locator('#global-edition-menu>summary').click();page.locator('#global-edition-menu a[href*="sp/deputados-federais"]').click();page.wait_for_url(url);count(249)
            assert not errors and not assets,dict(errors=errors,assets=assets)
            results.append(dict(name='home_hub_SC_to_SP',width=width,result='PASS'))
        ctx.close()
    ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':900});page=ctx.new_page();response=page.goto(url,wait_until='domcontentloaded');assert response and response.status==200
    assert page.locator('article.candidate').count()==249
    page.locator('.current-evidence>summary').first.click();assert page.locator('.current-evidence').first.evaluate('(e)=>e.open')
    page.locator('.cc-transparency>summary').first.click();assert page.locator('.cc-transparency').first.evaluate('(e)=>e.open')
    assert not page.locator('#eefQueryTools').is_visible();results.append(dict(name='no_javascript_original_and_provenance',result='PASS'));ctx.close()
    return results

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--base',required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    from playwright.sync_api import sync_playwright
    report={'passed':False,'scope':'Legacy browser semantics under canonical UI; photos checked against same-site assets, not political fact checking'}
    try:
        with sync_playwright() as pw:
            b=pw.chromium.launch();report['SC']=sc(b,a.base,a.out);report['SP']=sp(b,a.base,a.out,json.loads((ROOT/'sp/deputados-federais/dados.json').read_text())['records']);b.close();report['passed']=True
    finally:(a.out/'legacy-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')

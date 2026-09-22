"""Additional UI gates: source navigation, native-share outcomes and 513 synthetic IDs.
The synthetic catalogue is served only by Playwright's test route, never published.
"""
from __future__ import annotations
import argparse,functools,json,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
CHECKS=[]
def check(name,ok,detail=None):
    CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
    if not ok:raise AssertionError(name+': '+str(detail))
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*a):pass

def fixture(base):
    values=[str(900000000000+i) for i in range(513)]
    cards=''.join(f'<article class="candidate" id="candidato-{v}"><h3>Registro sintético {i}</h3><div class="eef-card-actions" hidden><button data-eef-toggle="{v}">Selecionar</button><button data-eef-share="{v}">Compartilhar ficha</button></div><p>Somente teste de escala, sem candidatura real.</p></article>' for i,v in enumerate(values))
    dialogs=(ROOT/'templates/global04/collection.html.txt').read_text()
    data=json.dumps({'edition_id':'2026-sp-federais','label':'Catálogo sintético de teste','election_year':2026})
    scripts=''.join('<script defer src="'+base+p+'"></script>' for p in ['assets/global/core.js','assets/selecionados-core.js','assets/global/selection-adapter.js','assets/global/selection.js'])
    html='<html><head><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="stylesheet" href="'+base+'assets/global/selection.css"></head><body><label>Busca <input id="searchInput"></label><button id="eefSelectedNav" data-eef-open hidden>Selecionados <span data-eef-count>0</span></button>'+cards+dialogs+'<script id="eefEditionSelectionData" type="application/json">'+data+'</script>'+scripts+'</body></html>'
    return html,values

def run(out,live=None):
    http=None
    if live:base=live
    else:
        http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT)))
        threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_address[1]}/'
    reg=json.loads((ROOT/'config/editions.json').read_text())
    with sync_playwright() as p:
        b=p.chromium.launch();c=b.new_context(reduced_motion='reduce')
        c.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort())
        g=c.new_page();errors=[];g.on('pageerror',lambda e:errors.append(str(e)))
        def start(url):
            g.goto(url,wait_until='domcontentloaded');g.wait_for_function("document.documentElement.classList.contains('eef-global04-ready')")
        for e in reg['editions']:
            if e['publication_status']!='published':continue
            label=e['edition_id'];start(base+e['canonical_path'].lstrip('/'))
            id=g.locator('article.candidate').first.get_attribute('id');value=id.removeprefix('candidato-')
            g.locator('[data-eef-toggle="'+value+'"]').click();g.locator('#searchInput').fill('global04-no-match');g.wait_for_timeout(350)
            g.locator('#eefSelectedNav').click();g.locator('#eefOpenFull').click();g.wait_for_timeout(150)
            check(label+' open original full card reveals it',g.locator('#'+id).is_visible() and not g.locator('#eefCollection').evaluate('(d)=>d.open'))
            g.locator('#eefSelectedNav').click()
            source=g.locator('#eefReaderHost a[href^="#"]').evaluate_all("els=>els.map(a=>a.getAttribute('href')).find(h=>{const n=document.getElementById(decodeURIComponent(h.slice(1)));return n&&!n.closest('#eefCollection')})")
            if source:
                g.locator('#eefReaderHost a[href="'+source+'"]').first.click();g.wait_for_timeout(150)
                check(label+' outside source exits reader',not g.locator('#eefCollection').evaluate('(d)=>d.open'))
                check(label+' source target remains visible',g.locator('[id="'+source[1:]+'"]').is_visible())
            else:g.locator('#eefCollectionClose').click()
            g.evaluate("window.__copies=[];Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.__copies.push(text)}}});Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{const e=new Error('test cancellation');e.name='AbortError';throw e;}})")
            g.locator('[data-eef-share="'+value+'"]').click();g.locator('#eefNativeShare').click();g.wait_for_function("document.getElementById('eefShareStatus').textContent.includes('cancelado')")
            check(label+' native cancellation no clipboard',g.evaluate('__copies.length')==0)
            g.locator('#eefCopy').click();g.wait_for_function("document.getElementById('eefShareStatus').textContent==='Link copiado.'")
            check(label+' confirmed copy matches URL',g.evaluate('__copies[0]')==g.locator('#eefShareUrl').input_value())
        check('actual editions no script errors',not errors,errors[:8]);c.close()
        if not live:
            doc,values=fixture(base);fixture_base=base+'global04-fixture/';url=fixture_base+'index.html'
            def ctx():
                x=b.new_context(reduced_motion='reduce');x.route('**/*',lambda r:r.continue_() if r.request.url.startswith(base) else r.abort());x.route(fixture_base+'**',lambda r:r.fulfill(status=200,content_type='text/html',body=doc));return x
            c=ctx();g=c.new_page();g.goto(url);g.wait_for_function("window.EEFCollectionUI")
            g.locator('[data-eef-toggle]').evaluate_all('(buttons)=>buttons.forEach(b=>b.click())')
            check('synthetic 513 selected by real controls',g.evaluate('EEFCollectionUI.snapshot().ids')==values)
            g.locator('#eefSelectedNav').click();g.evaluate("for(let i=0;i<512;i++)document.getElementById('eefNext').click()")
            check('synthetic 513 last original card active',g.locator('#eefReaderHost article').get_attribute('id')=='candidato-'+values[-1])
            g.locator('#eefShareCollection').click();g.wait_for_selector('#eefShareDialog[open]')
            link=g.locator('#eefShareUrl').input_value();check('synthetic share uses valid canonical fixture path',link.startswith(fixture_base+'#eef=collection&v=2&'))
            g.locator('#eefShareClose').click()
            g.evaluate("location.hash='#eef=collection&v=2&edition=2026-pr-federais&ids=900000000000'");g.wait_for_timeout(100)
            check('foreign link preserves existing collection',g.evaluate('EEFCollectionUI.snapshot().ids')==values)
            recipient=ctx();r=recipient.new_page();r.goto(link);r.wait_for_selector('#eefCollection[open]')
            check('synthetic 513 full URL roundtrip',r.evaluate('EEFCollectionUI.snapshot().ids')==values and r.evaluate('EEFCollectionUI.snapshot().active')==values[-1])
            check('synthetic 513 not cloned',r.locator('article.candidate').count()==513 and r.locator('#eefReaderHost article').count()==1)
            recipient.close();c.close()
        b.close()
    if http:http.shutdown()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--live-base');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
    try:run(a.out,a.live_base)
    except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
    finally:(a.out/'edge-cases.json').write_text(json.dumps({'passed':bool(CHECKS) and all(x['passed'] for x in CHECKS),'checks':CHECKS,'count':len(CHECKS),'synthetic_only_in_local_test_route':not bool(a.live_base),'native_share_and_clipboard_are_mocked_not_real_OS_send':True},ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))

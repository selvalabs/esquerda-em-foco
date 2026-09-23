"""GLOBAL-05 focused UX regression. Default: real local HTTP navigation.
--offline-fixture renders locally read HTML/CSS/JS with set_content, makes NO
network navigation claims and explicitly omits URL/share end-to-end checks.
"""
from __future__ import annotations
import argparse,base64,functools,hashlib,json,mimetypes,os,re,threading
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from urllib.parse import urlsplit,unquote
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[2]
WIDTHS=(320,360,390,430,768,1024,1440)

def fixture(root:Path,path:str,omit_scripts:tuple[str,...]=())->str:
    p=root/path;text=p.read_text();deferred=[]
    def local(value):
        u=urlsplit(value)
        if u.scheme or u.netloc:return None
        f=(p.parent/unquote(u.path)).resolve()
        return f if f.is_relative_to(root.resolve()) and f.is_file() else None
    def style(m):
        f=local(m[2]);return '<style>'+f.read_text().replace('</style','<\\/style')+'</style>' if f else ''
    def script(m):
        f=local(m[2])
        if f and str(f.relative_to(root.resolve())) in omit_scripts:return ''
        code='<script>'+f.read_text().replace('</script','<\\/script')+'</script>' if f else ''
        # Preserve deferred execution: a script in the original head must not run
        # before the body and return early because its DOM targets do not exist.
        if re.search(r'\bdefer(?:\s|=|>)',m[0],re.I):deferred.append(code);return ''
        return code
    def image(m):
        f=local(m[2]);raw=f.read_bytes() if f else b'<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>'
        mime=(mimetypes.guess_type(str(f))[0] or 'application/octet-stream') if f else 'image/svg+xml'
        return m[0].replace(m[2],'data:'+mime+';base64,'+base64.b64encode(raw).decode())
    text=re.sub(r'<link\b(?=[^>]*\brel=["\']stylesheet["\'])[^>]*?href=(["\'])(.*?)\1[^>]*>',style,text,flags=re.I)
    text=re.sub(r'<script\b[^>]*?src=(["\'])(.*?)\1[^>]*>\s*</script>',script,text,flags=re.I)
    text=re.sub(r'<img\b[^>]*?src=(["\'])(.*?)\1[^>]*>',image,text,flags=re.I)
    return text.replace('</body>', ''.join(deferred)+'</body>')

VISIBLE="""n=>{const r=n.getBoundingClientRect(),x=(r.left+r.right)/2,y=(r.top+r.bottom)/2;
 const hit=x>0&&x<innerWidth&&y>0&&y<innerHeight?document.elementFromPoint(x,y):null;
 return {visible:!!hit&&(n.contains(hit)||hit.contains(n)),top:r.top,bottom:r.bottom,hit:hit?hit.tagName+'#'+hit.id:null};}"""

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path,required=True);p.add_argument('--offline-fixture',action='store_true');p.add_argument('--edition');p.add_argument('--base-url');p.add_argument('--record-only',action='store_true');a=p.parse_args()
    root=a.root.resolve();out=a.out;out.mkdir(parents=True,exist_ok=True);checks=[];http=None
    reg=json.loads((root/'config/editions.json').read_text());editions=[e for e in reg['editions'] if e['publication_status']=='published' and (not a.edition or e['edition_id']==a.edition)]
    def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
    if not a.offline_fixture and not a.base_url:
        class Quiet(SimpleHTTPRequestHandler):
            def log_message(self,*args):pass
        http=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(root)))
        threading.Thread(target=http.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{http.server_address[1]}/'
    else:base=a.base_url
    mode='offline-inline-fixture' if a.offline_fixture else 'http-browser'
    try:
      with sync_playwright() as p:
        executable=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE')
        browser=p.chromium.launch(**({'executable_path':executable} if executable else {}))
        version=browser.version
        for e in editions:
          eid=e['edition_id'];ctx=browser.new_context(reduced_motion='reduce',viewport={'width':390,'height':844});errors=[]
          ctx.route('**/*',lambda r:r.continue_() if not a.offline_fixture and r.request.url.startswith(base) else r.abort())
          g=ctx.new_page();g.set_default_timeout(4000);g.on('pageerror',lambda err:errors.append(str(err)))
          try:
            if a.offline_fixture:g.set_content(fixture(root,e['entrypoint']),wait_until='domcontentloaded')
            else:
                response=g.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded');check(eid+' HTTP',response.status==200)
            g.wait_for_function('typeof EEFQueryUI==="object" && typeof EEFCollectionUI==="object"')
            for width in WIDTHS:
                g.set_viewport_size({'width':width,'height':844});label=f'{eid}:{width}'
                check(label+' no horizontal overflow',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                menu=g.locator('#siteNavMenu');links=g.locator('#siteNavLinks')
                if width<1200:
                    menu.click();check(label+' mobile menu announced and visible',menu.get_attribute('aria-expanded')=='true' and links.is_visible())
                    if links.is_visible():links.locator('a').first.focus()
                    g.keyboard.press('Escape');check(label+' menu Escape and focus',menu.get_attribute('aria-expanded')=='false' and menu.evaluate('(n)=>n===document.activeElement'))
                else:check(label+' desktop links visible',links.is_visible())
                picker=g.locator('#global-edition-menu');picker.locator(':scope>summary').click();g.keyboard.press('Escape')
                check(label+' edition picker Escape',not picker.evaluate('(n)=>n.open') and picker.locator(':scope>summary').evaluate('(n)=>n===document.activeElement'))
                card=g.locator('article.candidate').first;cid=card.get_attribute('id')
                g.evaluate('(id)=>EEFQueryUI.reveal("#"+id)',cid);g.wait_for_timeout(30)
                v=card.locator('h3').evaluate(VISIBLE);check(label+' identity not obscured',v['visible'],v)
                if width in (390,1440):g.screenshot(path=str(out/(eid+f'-anchor-{width}.png')))
                q=g.evaluate('EEFQueryUI.snapshot()');g.evaluate('(id)=>window.qaOriginal=document.getElementById(id)',cid)
                toggle=card.locator('[data-eef-toggle]')
                if toggle.get_attribute('aria-pressed')!='true':toggle.click()
                nav=g.locator('#eefSelectedNav');nav.click();g.wait_for_selector('#eefCollection[open]')
                check(label+' reader uses original article',g.evaluate('document.querySelector("#eefCollection article.candidate")===window.qaOriginal'))
                reader=g.locator('#eefCollection');detail=reader.locator('.cc-transparency');detail.evaluate('(n)=>n.open=false')
                reader.locator('.cc-card-nav a').filter(has_text='Origem').click();g.wait_for_timeout(50)
                check(label+' origin anchor opens detail',detail.evaluate('(n)=>n.open'))
                check(label+' origin focus goes to summary',detail.locator(':scope>summary').evaluate('(n)=>n===document.activeElement'))
                v=detail.locator(':scope>summary').evaluate(VISIBLE);check(label+' origin not covered by reader header',v['visible'],v)
                check(label+' reader anchor preserves query',g.evaluate('EEFQueryUI.snapshot()')==q)
                if width in (390,1440):g.screenshot(path=str(out/(eid+f'-reader-{width}.png')))
                # Native modal keeps focus inside; use real Tab rather than assigning focus.
                tab_states=[]
                for _ in range(4):
                    g.keyboard.press('Tab')
                    tab_states.append(g.evaluate('({documentFocused:document.hasFocus(),inside:document.querySelector("#eefCollection").contains(document.activeElement)})'))
                # Native Chromium dialogs allow Tab into browser chrome. That is
                # not focus on the inert page behind the modal. On returning to
                # the document, focus must re-enter the reader, not its background.
                if not g.evaluate('document.hasFocus()'):
                    g.keyboard.press('Tab')
                    tab_states.append(g.evaluate('({documentFocused:document.hasFocus(),inside:document.querySelector("#eefCollection").contains(document.activeElement)})'))
                check(label+' modal Tab never focuses background content',all(not x['documentFocused'] or x['inside'] for x in tab_states) and reader.evaluate('(n)=>n.contains(document.activeElement)'),tab_states)
                g.keyboard.press('Escape');g.wait_for_timeout(30)
                check(label+' reader Escape returns focus',not reader.evaluate('(n)=>n.open') and nav.evaluate('(n)=>n===document.activeElement'))
                g.locator('#searchInput').fill('global05-no-match-probe');check(label+' empty query has no results',g.locator('article.candidate:not([hidden])').count()==0)
                g.locator('#cqActive button').filter(has_text='Busca:').click();g.wait_for_timeout(30)
                check(label+' removed chip returns focus to search',g.locator('#searchInput').evaluate('(n)=>n===document.activeElement'))
                v=g.locator('#searchInput').evaluate(VISIBLE);check(label+' recovered focus visible',v['visible'],v)
                panel=g.locator('#cqPanel');panel.evaluate('(n)=>n.open=true');panel.locator(':scope>summary').focus();g.keyboard.press('Escape')
                check(label+' filter panel Escape',not panel.evaluate('(n)=>n.open') and panel.locator(':scope>summary').evaluate('(n)=>n===document.activeElement'))
            # Confirmation dialog with an actual collection, including cancellation.
            g.locator('#eefSelectedNav').click();g.locator('#eefClearCollection').click();g.keyboard.press('Escape');g.wait_for_timeout(30)
            check(eid+' cancelling clear preserves selection',bool(g.evaluate('EEFCollectionUI.snapshot().ids.length')) and g.locator('#eefClearCollection').evaluate('(n)=>n===document.activeElement'))
            g.locator('#eefClearCollection').click();g.locator('#eefConfirmClear').click();g.wait_for_timeout(30)
            check(eid+' confirming clear returns focus',g.evaluate('EEFCollectionUI.snapshot().ids.length')==0 and g.locator('#eefCollectionTitle').evaluate('(n)=>n===document.activeElement'))
            g.keyboard.press('Escape');g.wait_for_timeout(30)
            if not a.offline_fixture:
                g.locator('#searchInput').fill('consulta');expected=g.evaluate('EEFQueryUI.snapshot()');g.locator('#eefShareQuery').click();link=g.locator('#eefQueryShareUrl').input_value()
                check(eid+' explicit query URL',urlsplit(link).fragment.startswith('eef=query&v=2&'))
                check(eid+' WhatsApp is only a draft',g.locator('#eefQueryWhatsapp').get_attribute('href').startswith('https://wa.me/?text='))
                g.keyboard.press('Escape');other=ctx.new_page();other.goto(link,wait_until='domcontentloaded');other.wait_for_function('typeof EEFQueryUI==="object"');check(eid+' query restored in new document',other.evaluate('EEFQueryUI.snapshot()')==expected);other.close()
            check(eid+' no page errors',not errors,errors)
          except Exception as exc:check(eid+' execution error',False,repr(exc))
          finally:g.close();ctx.close()
          # Real browser with scripting disabled; inline CSS only is still a fixture.
          ctx=browser.new_context(java_script_enabled=False,viewport={'width':390,'height':844});ctx.route('**/*',lambda r:r.continue_() if not a.offline_fixture and r.request.url.startswith(base) else r.abort());g=ctx.new_page()
          if a.offline_fixture:g.set_content(fixture(root,e['entrypoint']),wait_until='domcontentloaded')
          else:g.goto(base+e['canonical_path'].lstrip('/'),wait_until='domcontentloaded')
          card=g.locator('article.candidate').first;check(eid+' noJS text',bool(card.locator('.candidate-copy').inner_text().strip()))
          card.locator('.cc-transparency>summary').click();check(eid+' noJS details',card.locator('.cc-transparency').evaluate('(n)=>n.open'))
          check(eid+' noJS query controls hidden',not g.locator('#eefQueryTools').is_visible());ctx.close()
        browser.close()
    finally:
      if http:http.shutdown()
      report={'passed':bool(checks) and all(c['passed'] for c in checks),'mode':mode,'browser':locals().get('version'),'checks':checks,'count':len(checks),
       'limits':['No physical device or screen reader','No real WhatsApp, clipboard or OS share action','External political sources not rechecked'],
       'not_exercised':['HTTP/navigation across pages','Query/collection URLs in a new browser document','HTTP status/redirect/404 behavior','End-to-end share launcher using location.href'] if a.offline_fixture else []}
      (out/'browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'count':len(checks),'mode':mode}))
    if not report['passed'] and not a.record_only:raise SystemExit(1)
if __name__=='__main__':main()

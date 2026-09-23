"""Offline viewport/keyboard fixtures of the home, hubs, alias and 404 body.
Navigation, HTTP redirect and HTTP 404 status require the separate public gate.
"""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser import fixture,WIDTHS,ROOT,VISIBLE

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root.resolve();a.out.mkdir(parents=True,exist_ok=True);checks=[]
 def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
 reg=json.loads((root/'config/editions.json').read_text());pages=['index.html']+[s['path'].lstrip('/')+'index.html' for s in reg['states']]+['deputados-estaduais/index.html','404.html']
 with sync_playwright() as p:
  exe=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE');b=p.chromium.launch(**({'executable_path':exe} if exe else {}));version=b.version
  for path in pages:
   c=b.new_context(reduced_motion='reduce');c.route('**/*',lambda r:r.abort());g=c.new_page();errors=[];g.on('pageerror',lambda e:errors.append(str(e)));g.set_content(fixture(root,path,omit_scripts=('assets/global/legacy-bridge.js',)),wait_until='domcontentloaded')
   for width in WIDTHS:
    g.set_viewport_size({'width':width,'height':844});label=path+':'+str(width)
    check(label+' no horizontal overflow',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
    picker=g.locator('#global-edition-menu');summary=picker.locator(':scope>summary');summary.focus();g.keyboard.press('Enter');g.wait_for_timeout(25)
    check(label+' picker opens from keyboard',picker.evaluate('(n)=>n.open'))
    g.keyboard.press('Tab');check(label+' picker link reached',g.evaluate('document.activeElement.matches("#global-edition-menu a")'))
    g.keyboard.press('Escape');check(label+' picker closes and returns focus',not picker.evaluate('(n)=>n.open') and summary.evaluate('(n)=>n===document.activeElement'))
    h=g.locator('h1');h.scroll_into_view_if_needed();v=h.evaluate(VISIBLE);check(label+' heading visible',v['visible'],v)
    if width in (390,1440):g.screenshot(path=str(a.out/(path.replace('/','-')+f'-{width}.png')))
   check(path+' no JS error',not errors,errors);c.close()
  b.close()
 report={'passed':all(c['passed'] for c in checks),'mode':'offline-inline-fixture','browser':version,'count':len(checks),'checks':checks,'omitted_scripts':['assets/global/legacy-bridge.js: requires a real URL base; redirect logic is not part of this offline layout fixture'],'limits':['No HTTP/redirect/404-status verification','No page-to-page navigation','No screen reader, physical device or WCAG certification']}
 (a.out/'pages.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','count','mode')}))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()

"""Sampled text contrast on offline fixtures, not a WCAG conformance audit.
Solid ancestor backgrounds are composited; text over images/gradients is not
certified. Disabled controls are excluded. The report preserves every sample.
"""
import argparse,json,os
from pathlib import Path
from playwright.sync_api import sync_playwright
from browser import fixture,ROOT
JS=r"""() => {
const rgba=s=>(s.match(/[\d.]+/g)||[]).map(Number), blend=(a,b)=>a.slice(0,3).map((v,i)=>v*(a[3]??1)+b[i]*(1-(a[3]??1)));
const luminance=c=>c.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);
const results=[];
for (const n of document.querySelectorAll('#eefQueryTools *,article.candidate:first-of-type .cc-context,article.candidate:first-of-type .cc-detail-body *,article.candidate:first-of-type .civil-name,article.candidate:first-of-type .registration time,#siteNav a')){
 if(![...n.childNodes].some(x=>x.nodeType===3&&x.textContent.trim())||n.closest('button:disabled,select:disabled')||!n.checkVisibility({checkOpacity:true,checkVisibilityCSS:true}))continue;
 let ancestors=[],el=n;while(el){ancestors.unshift(el);el=el.parentElement;}let bg=[255,255,255],opacity=1;
 for (const a of ancestors){const s=getComputedStyle(a);bg=blend(rgba(s.backgroundColor),bg);opacity*=Number(s.opacity);}
 const style=getComputedStyle(n),fg=rgba(style.color);if(fg.length<3||bg.length<3)throw new Error('Unsupported CSS color calculation');fg[3]=(fg[3]??1)*opacity;
 const ink=blend(fg,bg),L1=luminance(ink),L2=luminance(bg),ratio=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05);
 const large=parseFloat(style.fontSize)>=24||(parseFloat(style.fontSize)>=18.667&&Number(style.fontWeight)>=700);
 results.push({text:n.textContent.trim().slice(0,100),id:n.id,cls:n.className,color:style.color,bg,opacity,font:style.fontSize,ratio,threshold:large?3:4.5,pass:ratio>=(large?3:4.5)});
}return results; }"""
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--out',type=Path,required=True);a=p.parse_args();root=a.root.resolve();res=[]
 eds=[e for e in json.loads((root/'config/editions.json').read_text())['editions'] if e['publication_status']=='published']
 with sync_playwright() as p:
  exe=os.environ.get('PLAYWRIGHT_CHROMIUM_EXECUTABLE');b=p.chromium.launch(**({'executable_path':exe} if exe else {}));version=b.version
  for e in eds:
   g=b.new_page(viewport={'width':390,'height':844});g.route('**/*',lambda r:r.abort());g.set_content(fixture(root,e['entrypoint']),wait_until='domcontentloaded');g.wait_for_function('typeof EEFQueryUI==="object"')
   g.locator('#cqPanel').evaluate('(n)=>n.open=true');g.locator('.cq-advanced').evaluate('(n)=>n.open=true');g.locator('article.candidate').first.locator('.cc-transparency').evaluate('(n)=>n.open=true');g.locator('.cq-group').first.evaluate('(n)=>n.open=true');g.wait_for_timeout(30)
   res.append({'edition':e['edition_id'],'samples':g.evaluate(JS)});g.close()
  b.close()
 vals=[v for r in res for v in r['samples']];report={'passed':all(v['pass'] for v in vals),'sample_count':len(vals),'browser':version,'mode':'offline-inline-fixture','thresholds':{'normal':4.5,'large':3},'editions':res,'limits':['Selected visible text in filters, navigation, and card context only','Not all text, states, focus rings, images or graphic controls','Solid-background calculation; not full WCAG certification']}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','sample_count','mode')}))
 if not report['passed']:raise SystemExit(1)
if __name__=='__main__':main()

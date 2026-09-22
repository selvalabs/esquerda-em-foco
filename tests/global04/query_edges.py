"""Independent ID-set oracle and query interaction regression for all six editions.
No real share/copy/send, no third-party fetch, no inferred political associations.
"""
from __future__ import annotations
import argparse,itertools,json,sys
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
from query_validate import ROOT,load,server,context,start,snap
CHECKS=[]
def check(name,passed,detail=None):
    CHECKS.append({'name':name,'passed':bool(passed),'detail':detail})
    if not passed:raise AssertionError(name+': '+str(detail))
def visible(g):return g.locator('article.candidate:not([hidden])').evaluate_all('els=>els.map(e=>e.id.replace(/^candidato-/,""))')
def party_button(g,eid,party):
    if eid=='2026-sp-federais':
        g.locator('#filterDetails').evaluate('(e)=>e.open=true')
        return g.locator('[data-party-filter="'+party+'"]')
    g.locator('#eefQueryParties').evaluate('(e)=>e.open=true')
    return g.locator('[data-eef-party="'+party+'"]')
def expected(records,s,eid):
    out=[]
    for r in records:
        if s['parties'] and r['party'] not in s['parties']:continue
        if s['status']:
            accepted=['nao-confirmada','deferida-sem-confirmacao-api'] if eid.startswith('2026-pr-') and s['status']=='nao-confirmada' else [s['status']]
            if r['status'] not in accepted:continue
        if s['mandate'] and r['mandate']!=s['mandate']:continue
        if s['history'] and r['history']!=s['history']:continue
        if s['region'] and r['region']!=s['region']:continue
        hits=[t in r['topics'] for t in s['topics']]
        if hits and not (all(hits) if s['mode']=='all' else any(hits)):continue
        out.append(r['id'])
    return sorted(out)
def run_matrix(g,eid):
    valid=g.evaluate('EEFEditionQuery.valid');default=snap(g)
    records=g.evaluate('''() => [...document.querySelectorAll('article.candidate')].map(c=>{
      const id=c.id.replace(/^candidato-/,''),d=c.dataset,sc=window.EEF_SC_FEDERAIS_FILTERS_V2;
      return {id,party:d.party,status:d.registration||d.statusGroup||d.status||'',
        mandate:d.currentOffice||'',history:d.hasHistory||(d.rookie!==undefined?(d.rookie==='true'?'false':'true'):''),region:d.region||'',
        topics:sc?(sc.candidates.find(r=>r.id===id)?.topicIds||[]):(d.themes||d.topics||'').split(' ').filter(Boolean)};
    })''')
    cases=[('default',default)]
    for n in [1,2]:
        for ps in itertools.combinations(valid['parties'],n):cases.append(('parties:'+','.join(ps),{**default,'parties':list(ps)}))
    for field,key in [('status','statuses'),('mandate','mandates'),('history','histories'),('region','regions')]:
        for v in valid.get(key,[]):
            if v:cases.append((field+':'+v,{**default,field:v}))
    for t in valid['topics']:cases.append(('topic:'+t,{**default,'topics':[t]}))
    for a,b in zip(valid['topics'][:6],valid['topics'][1:7]):
        for mode in valid['modes']:
            cases.append(('themes:'+a+':'+b+':'+mode,{**default,'topics':[a,b],'mode':mode}))
            cases.append(('combined:'+a+':'+mode,{**default,'parties':valid['parties'][:2],'topics':[a,b],'mode':mode}))
    for i in range(0,len(cases),12):
        batch=cases[i:i+12]
        results=g.evaluate('''states=>states.map(s=>{
          EEFEditionQuery.applyState(s);
          return [...document.querySelectorAll('article.candidate:not([hidden])')].map(c=>c.id.replace(/^candidato-/,''));
        })''',[s for _,s in batch])
        for (label,s),ids in zip(batch,results):
            oracle=expected(records,s,eid)
            check(eid+' exact '+label,sorted(ids)==oracle,{'actual':len(ids),'expected':len(oracle)})
    g.evaluate('s=>EEFEditionQuery.applyState(s)',default)
    return valid

def exercise(browser,base,out,live):
    pub=[e for e in load(ROOT/'config/editions.json')['editions'] if e['publication_status']=='published']
    c=context(browser,base);g=c.new_page();g.set_default_timeout(8000);errors=[];g.on('pageerror',lambda e:errors.append(str(e)))
    try:
        for e in pub:
            eid=e['edition_id'];url=base+e['canonical_path'].lstrip('/');g.set_viewport_size({'width':1440,'height':960});start(g,url)
            valid=run_matrix(g,eid)
            start(g,url);first=valid['parties'][0];second=valid['parties'][1]
            b=party_button(g,eid,first);b.click();before=snap(g)
            check(eid+' party focus retained',b.evaluate('(e)=>e===document.activeElement'))
            party_button(g,eid,second).click();two=snap(g)
            check(eid+' native history contains no query',set(g.evaluate('Object.keys(history.state||{})'))=={'eefQueryEntry'})
            check(eid+' no auto query or fragment',not urlsplit(g.url).query and not urlsplit(g.url).fragment)
            g.go_back();g.wait_for_timeout(100);check(eid+' back restores parties',snap(g)==before)
            g.go_forward();g.wait_for_timeout(100);check(eid+' forward restores parties',snap(g)==two)
            g.locator('#eefQueryClear').click();check(eid+' clear all',len(visible(g))==len(g.locator('article.candidate').all()) and not snap(g)['parties'])
            # Search is a conjunction of normalized words, independent of their order.
            name=g.locator('article.candidate h3').first.inner_text().strip();target=g.locator('article.candidate').first.get_attribute('id')
            words=name.split();g.locator('#searchInput').fill(' '.join(reversed(words)));g.wait_for_timeout(100)
            check(eid+' reversed-name terms',g.locator('#'+target).is_visible())
            # A complete query round-trip; subsequent interaction must detach stale shared hash.
            g.locator('#eefShareQuery').click();link=g.locator('#eefQueryShareUrl').input_value();g.locator('#eefQueryShareClose').click();saved=snap(g)
            start(g,link);check(eid+' query link is exact',snap(g)==saved)
            g.locator('#searchInput').fill('no-query-match-262626');check(eid+' edit detaches shared URL',not urlsplit(g.url).fragment)
            g.evaluate('h=>location.hash=h',target);g.wait_for_timeout(100)
            check(eid+' hidden-link explanation',g.locator('#'+target).is_visible() and g.locator('#eefDeepLinkNotice').is_visible())
            g.locator('#eefRestoreQuery').click();check(eid+' restore displaced query',snap(g)['q']=='no-query-match-262626' and not visible(g))
            g.go_back();g.wait_for_timeout(100);check(eid+' back to revealed card',g.locator('#'+target).is_visible())
            g.go_forward();g.wait_for_timeout(100);check(eid+' forward to displaced query',snap(g)['q']=='no-query-match-262626' and not visible(g))
            # A malformed link must not partially apply valid options or replace the session.
            saved=snap(g);invalid='eef=query&v=1&edition='+eid+'&state='+json.dumps({**saved,'parties':['INVALID']},separators=(',',':'))
            g.evaluate('h=>location.hash=h',invalid);g.wait_for_timeout(100)
            check(eid+' invalid import atomic',snap(g)==saved and g.locator('#eefQueryNotice').is_visible())
            check(eid+' query preference not persisted',g.evaluate('localStorage.length+sessionStorage.length')==0 and not c.cookies())
            # Real dimensions, not mislabeled screenshots. Both folded and expanded controls.
            start(g,url)
            for width in [390,1440]:
                g.set_viewport_size({'width':width,'height':960});party_button(g,eid,first)
                g.locator('#eefQueryTools').scroll_into_view_if_needed()
                check(eid+f' controls overflow {width}',g.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                g.screenshot(path=str(out/(eid+f'-controls-{width}.png')))
        # Controlled promises: never invoke real clipboard, OS sharing or WhatsApp.
        start(g,base+'sp/deputados-federais/');g.locator('#searchInput').fill('fixture-query-copy')
        g.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async()=>{throw new Error('denied')}}});Object.defineProperty(navigator,'share',{configurable:true,value:async()=>{throw new DOMException('cancel','AbortError')}})")
        g.locator('#eefShareQuery').click();g.locator('#eefQueryCopy').click();g.wait_for_timeout(30)
        check('copy failure manual fallback','automaticamente' in g.locator('#eefQueryShareStatus').inner_text() and g.locator('#eefQueryShareUrl').evaluate('(e)=>e===document.activeElement'))
        g.locator('#eefQueryNative').click();g.wait_for_timeout(30);check('native cancel reported','cancelado' in g.locator('#eefQueryShareStatus').inner_text())
        check('WhatsApp draft no recipient',g.locator('#eefQueryWhatsapp').get_attribute('href').startswith('https://wa.me/?text='))
        g.keyboard.press('Escape');g.wait_for_timeout(30);check('query share Escape and focus',not g.locator('#eefQueryShareDialog').is_visible() and g.locator('#eefShareQuery').evaluate('(e)=>e===document.activeElement'))
        g.evaluate("Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:()=>new Promise(resolve=>window.resolveCopy=resolve)}})")
        g.locator('#eefShareQuery').click();g.locator('#eefQueryCopy').click();g.locator('#eefQueryShareClose').click();g.wait_for_timeout(30)
        g.locator('#eefShareQuery').click();g.evaluate('resolveCopy()');g.wait_for_timeout(30)
        check('late copy does not affect a new dialog',g.locator('#eefQueryShareStatus').inner_text()=='')
        check('no browser errors',not errors,errors)
    finally:
        if any(not t['passed'] for t in CHECKS):g.screenshot(path=str(out/'failure.png'))
        c.close()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--live-base');args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=True);http=None
    if args.live_base:base=args.live_base
    else:http,base=server(ROOT)
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch();exercise(browser,base,args.out,bool(args.live_base));browser.close()
    except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
    finally:
        (args.out/'query-edges.json').write_text(json.dumps({'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,'limits':['No real messages or clipboard writes','No new political evidence','No physical device or screen reader']},ensure_ascii=False,indent=2)+'\n')
        if http:http.shutdown()
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))
if __name__=='__main__':main()

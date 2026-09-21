#!/usr/bin/env python3
"""Review-2 data regressions and real browser tests, scoped to the state front."""
from __future__ import annotations
import functools, hashlib, http.server, json, os, sys, threading
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent; OUT=ROOT/'audit/review2'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 report={'checks':[],'browser_viewports':[],'scope':'deputados-estaduais only'}
 def check(name,condition,detail=None):
  report['checks'].append({'name':name,'passed':bool(condition),'detail':detail})
  print(name,bool(condition),detail or '',flush=True)
  return bool(condition)
 data=read(ROOT/'data/candidaturas.json'); people={p['id']:p for p in data['candidates']}
 html=(ROOT/'index.html').read_text(encoding='utf-8');doc=BeautifulSoup(html,'html.parser')
 notes=read(ROOT/'editorial/review2.json')['profiles']; votes=read(OUT/'votes-contextual.json')
 raw=read(OUT/'snapshot/historico-sc-2026.json'); mandate=read(OUT/'report.json')
 check('candidate IDs equal fresh reviewed scope',set(people)==set(notes))
 check('individual search or direct-source review recorded for every profile',all(p.get('queries') or p.get('evidence') or p.get('review_evidence') for p in notes.values()))
 check('all topic summaries have individual source',all(not p.get('topics') or p.get('topics_source') for p in people.values()))
 check('all additional biographies have individual source',all(not p.get('biography') or p.get('biography_source') for p in people.values()))
 check('three distinct registration groups allowed',all(p['registration_group'] in ('deferido','recursal','outro') for p in people.values()))
 recursal={p['id'] for p in people.values() if p['registration_group']=='recursal'}
 check('recursal baseline preserved',recursal=={'240002537803','240002537805','240002540081'})
 check('private identifiers absent from public normalized export',not any(x in (ROOT/'data/candidaturas.json').read_text().upper() for x in ('NR_CPF_CANDIDATO','NR_TITULO_ELEITORAL','DS_EMAIL','DT_NASCIMENTO')))
 check('supplementary election is shown in actual year',any(h['year']==2023 and h['cycle_year']==2020 and h['votes']==15679 and h['election_date']=='2023-09-03' for h in people['240002540081']['history']))
 check('regular and supplementary totals remain separate',any(h['year']==2020 and h['votes']==12324 for h in people['240002540081']['history']))
 check('historical short-ID collision regression',next(h['votes'] for h in people['240002533282']['history'] if h['year']==2004)==328)
 check('historical IDs use composite context',all(h.get('vote_join_key') and h.get('election_date') for p in people.values() for h in p['history']))
 missing=[(p['id'],h['year']) for p in people.values() for h in p['history'] if h['votes'] is None]
 check('only two verified missing historical totals',set(missing)=={('240002537807',2012),('240002537819',2022)})
 check('zero totals require actual matched rows',all(h['votes']!=0 or votes[h['vote_join_key']]['rows']>0 for p in people.values() for h in p['history']))
 check('histories sorted by actual date',all([h['election_date'] for h in p['history']]==sorted((h['election_date'] for h in p['history']),reverse=True) for p in people.values()))
 check('generic index replaced by individual bill evidence',people['240002533287'].get('topics_source')=='https://www.cmf.sc.gov.br/proposicoes/Projetos-de-Leis-ordinarias/0/1/26/111376')
 check('biography heading precedes text and source',all(not p.get('biography') or doc.select_one(f'#candidato-{sid} .state-public-bio').previous_sibling.get_text()=='Trajetória pública' for sid,p in people.items()))
 check('institutional mandate total matches provenance',data['counts']['mandates_documented']==sum(p['mandate_verification'] in ('institutional_current','institutional_leave') for p in people.values()))
 check('self-reports are not counted as institutional mandates',all(not p['mandate_documented'] for p in people.values() if p['mandate_verification'] in ('candidate_report','previous_source_unverified','candidate_report_substitute')))
 check('all 97 portraits are local and present',all((ROOT/p['portrait']['path']).is_file() for p in people.values()))
 check('research coverage visible',doc.select_one('#cobertura-revisao') is not None and str(data['counts']['topics_not_consolidated']) in doc.select_one('#cobertura-revisao').get_text())
 # Preserve case-sensitive path/query fragments exactly as they were declared.
 declared=read(ROOT/'data/redes-sc-2026.json'); sets={sid:set() for sid in people}
 for row in declared:
  if row['SQ_CANDIDATO'] not in sets:continue
  u=urlsplit(row['DS_URL'])
  if u.scheme.lower() in ('http','https') and u.hostname and not u.username:
   sets[row['SQ_CANDIDATO']].add(urlunsplit((u.scheme.lower(),u.netloc.lower(),u.path,u.query,u.fragment)))
 check('declared URL paths and query case preserved',all(set(p['declared_links'])==sets[sid] for sid,p in people.items()))
 check('every profile has separate registration history and channels controls',all(len(doc.select(f'#candidato-{sid} .registration-detail'))==1 and len(doc.select(f'#candidato-{sid} .state-history'))==1 and len(doc.select(f'#candidato-{sid} .state-channels'))==1 for sid in people))
 outside=read(OUT/'baseline.json')['outside_state_sha256']
 absent=[p for p in outside if not (REPO/p).exists()]
 changed=[p for p,s in outside.items() if (REPO/p).exists() and sha(REPO/p)!=s]
 check('all protected files still present',not absent,absent)
 check('all protected files byte-identical',not changed,changed)
 check('build asserted full isolation',mandate['outside_state_unchanged'])
 class Quiet(http.server.SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 if '--static-only' not in sys.argv:
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(REPO)))
  threading.Thread(target=server.serve_forever,daemon=True).start()
  url=f'http://127.0.0.1:{server.server_port}/deputados-estaduais/'
  shots=ROOT/'audit/screenshots';shots.mkdir(exist_ok=True)
  try:
   with sync_playwright() as pw:
    opts={'headless':True,'args':['--no-sandbox']}
    if os.path.isfile('/usr/bin/chromium'):opts['executable_path']='/usr/bin/chromium'
    browser=pw.chromium.launch(**opts)
    for width,height in ((360,800),(390,844),(768,1024),(1440,1000)):
     page=browser.new_page(viewport={'width':width,'height':height});errors=[]
     page.on('pageerror',lambda e:errors.append(str(e)))
     page.goto(url,wait_until='networkidle');page.emulate_media(reduced_motion='reduce')
     page.locator('#registrationFilter').select_option('recursal')
     shown=set(page.locator('.candidate:visible').evaluate_all('(els)=>els.map(e=>e.id.replace("candidato-",""))'))
     check(f'registration filter {width}',shown==recursal,sorted(shown))
     page.locator('#partyFilter').select_option('PT')
     check(f'combined party and registration filter {width}',page.locator('.candidate:visible').count()==1 and page.locator('#candidato-240002540081').is_visible())
     page.locator('#searchInput').fill('zzzznotfound998')
     check(f'combined empty state {width}',page.locator('#emptyState').is_visible())
     page.locator('#emptyReset').click()
     check(f'reset restores all filters {width}',page.locator('.candidate:visible').count()==len(people) and page.locator('#registrationFilter').input_value()=='')
     page.locator('#registrationFilter').select_option('recursal')
     page.evaluate("location.hash='candidato-240002540083'");page.wait_for_timeout(200)
     check(f'deep link reveals filtered profile {width}',page.locator('#candidato-240002540083').is_visible() and page.locator('#registrationFilter').input_value()=='')
     page.locator('#searchInput').fill('13030');card=page.locator('#candidato-240002540081')
     card.locator('.registration-detail > summary').click()
     card.locator('.state-history > summary').click()
     card.scroll_into_view_if_needed();page.wait_for_timeout(100)
     check(f'supplementary visible history {width}','2023 · suplementar' in card.inner_text() and '15.679' in card.inner_text())
     page.screenshot(path=str(shots/f'review2-profile-{width}.png'))
     overflow=page.evaluate('({viewport:innerWidth,document:document.documentElement.scrollWidth,body:document.body.scrollWidth})')
     check(f'expanded profile no horizontal overflow {width}',max(overflow['document'],overflow['body'])<=width+1,overflow)
     page.locator('#resetFilters').click();page.locator('#cobertura-revisao > summary').click();page.locator('#cobertura-revisao').scroll_into_view_if_needed()
     page.screenshot(path=str(shots/f'review2-coverage-{width}.png'))
     check(f'review coverage expanded {width}',page.locator('#cobertura-revisao').evaluate('(e)=>e.open'))
     page.evaluate("location.hash='%E0%A4%A'");page.wait_for_timeout(50)
     check(f'no javascript errors including malformed fragment {width}',not errors,errors)
     report['browser_viewports'].append(overflow);page.close()
    browser.close()
  finally:server.shutdown()
 report['passed']=all(x['passed'] for x in report['checks'])
 report['coverage']=data['counts']
 (OUT/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 if not report['passed']:raise SystemExit('Review-2 checks failed; do not publish')
if __name__=='__main__':main()

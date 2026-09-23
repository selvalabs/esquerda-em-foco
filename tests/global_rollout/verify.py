"""Release gate: preserve the real baseline, not a generated approximation.
HTML changes are intentional; all original card text, data, links, IDs and research
remain protected. Every projected association is traced to an existing source.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global_rollout'))
from build import original_signature,strip_card,load,BASE
sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import resolve,jsha,safe_url
CHECKS=[]
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def config(doc):return json.loads(doc.select_one('#cqData').get_text())
def verify(baseline):
 reg=load(ROOT/'config/editions.json');pub=[e for e in reg['editions'] if e['publication_status']=='published']
 pages={e['entrypoint'] for e in pub};protected=0
 allowed=pages|{'config/editions.json','data/global03/publication-files.json','tools/global03/refresh.py','data/global-integration/migration-status.json',
  'tools/sp/publication/verify_live.py','tools/sc_semantic_v2_ui/verify_live.py',
  '.github/workflows/global04-query-maintenance.yml',
  'tests/global03/validate.py','tests/global04/validate.py','tests/global04/edge_cases.py',
  'tests/global04/query_validate.py','tests/global04/query_edges.py','tests/global04/query_maintenance.py'}
 # GLOBAL-05 is a later, explicitly baselined QA stage. Its own verifier compares
 # every intentional existing-file change against 4a330000...; acknowledge only
 # those exact shell/SEO paths here so the D4 political-content protections remain.
 if (ROOT/'tools/global05/build.py').is_file():
  g05=(ROOT/'tools/global05/build.py').read_text()
  check('GLOBAL-05 baseline is explicit',"BASELINE='4a3300005fafbf85e13c4a61e763db1496924348'" in g05)
  check('GLOBAL-05 preservation verifier exists',(ROOT/'tests/global05/validate.py').is_file())
  allowed|={'README.md','404.html','index.html','deputados-estaduais/index.html',
   'assets/global/navigation.css','assets/global/rollout.js','tools/global03/publication.py','tests/global_rollout/verify.py',
   'sc/index.html','rs/index.html','pr/index.html','sp/index.html'}
 # All other old files, including every research export, must be exact bytes.
 for file in sorted(baseline.rglob('*')):
  if not file.is_file() or '.git' in file.relative_to(baseline).parts:continue
  name=str(file.relative_to(baseline))
  if name in allowed:continue
  target=ROOT/name;check('unchanged '+name,target.is_file() and target.read_bytes()==file.read_bytes());protected+=1
 check('baseline protection breadth',protected>1700,protected)
 total=0;projected=0;cache={}
 for e in pub:
  name=e['edition_id'];before=BeautifulSoup((baseline/e['entrypoint']).read_bytes(),'html.parser');after=BeautifulSoup((ROOT/e['entrypoint']).read_bytes(),'html.parser')
  b={c['id']:original_signature(c) for c in before.select('article.candidate')};a={}
  for c in after.select('article.candidate'):
   strip_card(c);a[c['id']]=original_signature(c)
  check(name+' original card text/data/destinations',b==a);total+=len(a)
  ids=[n['id'] for n in after.select('[id]')];check(name+' unique IDs',len(ids)==len(set(ids)))
  cfg=config(after);check(name+' one common controller',len(after.select('script[src*="rollout.js"]'))==1 and not any(x in n.get('src','') for n in after.select('script[src]') for x in ['pauta-filters-editorial','runtime.js','deputados-estaduais/assets/app.js','sp/deputados-federais/assets/app.js','global/query.js']))
  check(name+' same catalogue',set(a)=={'candidato-'+r['id'] for r in cfg['records']})
  check(name+' 39 topics and 16 groups',len(cfg['topics'])==39 and len(cfg['groups'])==16)
  check(name+' production indexability',not after.select('.cc-prototype-note') and not any('noindex' in n.get('content','') for n in after.select('meta[name=robots]')))
  check(name+' canonical stable',str(before.select_one('link[rel=canonical]'))==str(after.select_one('link[rel=canonical]')))
  old=next(x for x in load(baseline/'config/editions.json')['editions'] if x['edition_id']==name)
  check(name+' research/snapshot intact',e['research']==old['research'] and e['snapshot']==old['snapshot'])
  for r in cfg['records']:
   # Raw original filtering attributes are independently checked against the old HTML.
   oldcard=before.select_one('#candidato-'+r['id']);legacy=r['legacy']
   check(name+':'+r['id']+' party retained',r['party']==oldcard['data-party'])
   for ev in r['evidence']:
    ref=ev['ref'];path=ref['path']
    if path not in cache:cache[path]=load(ROOT/path)
    check('source hash '+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==ref['sha256'])
    value=resolve(cache[path],ref['pointer']);check('source value '+path+ref['pointer'],jsha(value)==ref['value_sha256'])
    check('safe sources '+r['id'],bool(ev['sources']) and all(safe_url(s['url']) and s['locator'] for s in ev['sources']))
    if ev['semantic']=='legacy_context':check('legacy not promoted '+r['id'],ev['scopes']==['legacy_context'])
    if name=='2026-sp-federais':check('SP not promoted to support '+r['id'],'current_support' not in ev['scopes'])
    if name=='2026-sc-federais':check('SC object is reviewed text '+r['id'],ev['object']==value['match_text'])
    if 'current_support' in ev['scopes']:check('reviewed current support '+r['id'],value['eligible_v2'] and value['original_direction'] in ('apoio','prioridade'))
    if ev['individual_review']:check('object review bound to actual text '+r['id'],ev['individual_review']['object_sha256']==jsha(ev['object']))
    for source in ev['sources']:
     if source.get('external_locator_missing'):check('missing external locator is honest '+r['id'],source['locator_kind']=='research_record_not_external_passage' and ref['pointer'] in source['locator'])
    projected+=1
 newstatus=load(ROOT/'data/global-integration/migration-status.json');newstatus.pop('canonical_rollout')
 if 'reconciliation' in newstatus:
  closing=newstatus.pop('reconciliation')
  check('D5 closure identity',closing.get('issue')==57 and closing.get('baseline')=='8a36b2a47a893746ea528646ff0bb40d6a2d9101' and closing.get('global05_completed') is False)
  check('D5 preserves previous flag',closing.get('previous_whole_issue_completed') is False)
  if (ROOT/'tools/global05/build.py').is_file():
   d5_base='4a3300005fafbf85e13c4a61e763db1496924348'
   for d5_path in ('data/global-integration/reconciliation.json','tools/global_reconciliation/reconcile.py','docs/GLOBAL-04-RECONCILIATION.md'):
    expected=subprocess.check_output(['git','show',d5_base+':'+d5_path],cwd=ROOT)
    check('D5 core unchanged under GLOBAL-05 '+d5_path,(ROOT/d5_path).read_bytes()==expected)
  else:
   subprocess.run([sys.executable,str(ROOT/'tools/global_reconciliation/reconcile.py'),'--check'],check=True)
  newstatus['whole_issue_completed']=closing['previous_whole_issue_completed']
 check('prior migration history retained',newstatus==load(baseline/'data/global-integration/migration-status.json'))
 check('760 published cards',total==760,total);check('projection covers existing reviewed associations',projected>650,projected)
 for e in reg['editions']:
  if e['publication_status']!='published':check(e['edition_id']+' unpublished untouched',e==next(x for x in load(baseline/'config/editions.json')['editions'] if x['edition_id']==e['edition_id']))
 check('no prototype public directory',not (ROOT/'audit').exists() and not (ROOT/'galeria').exists())
 # Raw inputs are current and exact, never an old prototype's fields copied by hand.
 for path,expected in load(ROOT/'data/global-rollout/source-hashes.json')['json_sources'].items():check('current input '+path,hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected)
 return {'protected_original_files':protected,'cards':total,'projected_existing_associations':projected}
def main():
 p=argparse.ArgumentParser();p.add_argument('--baseline-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.parent.mkdir(parents=True,exist_ok=True);stats={}
 try:stats=verify(a.baseline_root)
 except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
 finally:a.out.write_text(json.dumps({'passed':bool(CHECKS) and all(x['passed'] for x in CHECKS),'baseline':BASE,'count':len(CHECKS),'statistics':stats,'checks':CHECKS,'scope':'Software preservation and source traceability, not a new external political fact check'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':True,'count':len(CHECKS),**stats}))
if __name__=='__main__':main()

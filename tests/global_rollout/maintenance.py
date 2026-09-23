"""Actual production refresh and stale-provenance regression in disposable copies.
No old political-research collector is rerun. Current reviewed raw HTML inputs are
used, and generated transparency is invalidated when its source changes.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global_rollout'))
from build import build,strip_card,original_signature
CHECKS=[]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(name,ok,detail=None):
 CHECKS.append({'name':name,'passed':bool(ok),'detail':detail})
 if not ok:raise AssertionError(name+': '+str(detail))
def signatures(p):
 s=BeautifulSoup(p.read_bytes(),'html.parser');d={}
 for c in s.select('article.candidate'):strip_card(c);d[c['id']]=original_signature(c)
 return d
def run(out):
 env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'}
 with tempfile.TemporaryDirectory(prefix='eef-production-refresh-') as temp:
  root=Path(temp)/'repo';shutil.copytree(ROOT,root,ignore=shutil.ignore_patterns('.git','__pycache__'))
  reg=json.loads((root/'config/editions.json').read_text());pub=[e for e in reg['editions'] if e['publication_status']=='published']
  home={str(p.relative_to(root)):digest(p) for p in [root/'index.html',root/'sc/index.html',root/'rs/index.html',root/'pr/index.html',root/'sp/index.html']}
  research={str(p.relative_to(root)):digest(p) for p in root.rglob('*.json') if not str(p.relative_to(root)).startswith(('config/','data/global'))}
  for e in pub:
   page=root/e['entrypoint'];before=signatures(page)
   # Replay the shell/selection/query integration on an already composed page.
   with (out/(e['edition_id']+'.log')).open('w') as log:
    subprocess.run([sys.executable,'tools/global03/refresh.py','--edition',e['edition_id'],'--input',e['entrypoint'],'--source-path',e['entrypoint']],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
   check(e['edition_id']+' refresh preserves original text/data/links',before==signatures(page))
   doc=BeautifulSoup(page.read_bytes(),'html.parser');check(e['edition_id']+' refresh reapplies one global controller',len(doc.select('script[src*="rollout.js"]'))==1 and not doc.select('script[src*="global/query.js"]'))
   check(e['edition_id']+' fresh provenance and original reader',len(doc.select('.cc-transparency'))==len(doc.select('article.candidate')) and len(doc.select('#eefCollection'))==1)
  check('home/hubs not changed by refresh',all(digest(root/p)==h for p,h in home.items()))
  check('research not changed by refresh',all(digest(root/p)==h for p,h in research.items()),len(research))
  # Clearly synthetic input mutation only in this temporary copy.
  target=root/'deputados-estaduais/data/candidaturas.json';data=json.loads(target.read_text());record=data['candidates'][0];record['mandate_note']='FIXTURE DE TESTE: metadado atualizado, nunca publicar.';cid=record['id'];target.write_text(json.dumps(data,ensure_ascii=False))
  build(root,edition='2026-sc-estaduais',metadata=False)
  page=root/'sc/deputados-estaduais/index.html';doc=BeautifulSoup(page.read_bytes(),'html.parser')
  check('changed raw metadata refreshes previously composed HTML','FIXTURE DE TESTE' in doc.select_one('#candidato-'+cid+' .cc-transparency').get_text())
  first=page.read_bytes();build(root,edition='2026-sc-estaduais',metadata=False);check('composed regeneration is idempotent',page.read_bytes()==first)
  check('fixture never touched working research','FIXTURE DE TESTE' not in (ROOT/'deputados-estaduais/data/candidaturas.json').read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 try:run(a.out)
 except Exception as exc:CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
 finally:(a.out/'maintenance.json').write_text(json.dumps({'passed':bool(CHECKS) and all(x['passed'] for x in CHECKS),'checks':CHECKS,'count':len(CHECKS),'scope':'Production refresh integration and synthetic stale-metadata test; no research collector execution'},ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'passed':True,'count':len(CHECKS)}))
if __name__=='__main__':main()

"""Rebuild legacy outputs in a disposable current worktree, reapply route adapter."""
import argparse,json,os,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global03'))
from build import content_signature
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
work=a.out/'worktree';checks=[]
env={**os.environ,'EEFOCO_OFFLINE_BUILD':'1','PYTHONDONTWRITEBYTECODE':'1'}
def run(cmd,name):
    with (a.out/(name+'.log')).open('a') as log:subprocess.run(cmd,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
def check(name,ok):
    checks.append({'name':name,'passed':bool(ok)})
    if not ok:raise AssertionError(name)
try:
    subprocess.run(['git','worktree','add','--detach',str(work),'HEAD'],cwd=ROOT,check=True)
    r=json.loads((work/'config/editions.json').read_text())
    pairs=[('2026-sc-estaduais','deputados-estaduais/index.html',[sys.executable,'-c',"import sys,hashlib;from pathlib import Path;sys.path.insert(0,'deputados-estaduais/tools');import review2_build as b;r=Path('.');h={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and not str(p).startswith(('deputados-estaduais/','.git'))};b.main(isolation_baseline=h)"]),
      ('2026-rs-federais','rs/deputados-federais/index.html',[sys.executable,'tools/rs/build.py']),
      ('2026-pr-federais','pr/deputados-federais/index.html',[sys.executable,'tools/pr/build.py']),
      ('2026-pr-estaduais','pr/deputados-estaduais/index.html',None)]
    signatures={e['edition_id']:content_signature(BeautifulSoup((work/e['entrypoint']).read_text(),'html.parser')) for e in r['editions'] if e['publication_status']=='published'}
    home=(work/'index.html').read_bytes()
    for eid,raw,command in pairs:
        if command:run(command,eid)
        run([sys.executable,'tools/global03/refresh.py','--edition',eid,'--input',raw,'--source-path',raw],eid)
        e=next(e for e in r['editions'] if e['edition_id']==eid);s=BeautifulSoup((work/e['entrypoint']).read_text(),'html.parser')
        check(eid+' regenerated research signature',content_signature(s)==signatures[eid])
        check(eid+' shell restored',len(s.select('#global-edition-menu'))==1)
        check(eid+' canonical restored',s.select_one('link[rel=canonical]')['href'].endswith(e['canonical_path']))
        check(eid+' home preserved',(work/'index.html').read_bytes()==home)
    check('SC legacy alias not overwritten','global-alias-target' in (work/'deputados-estaduais/index.html').read_text())
    check('RS branch not published',not (work/'rs/deputados-estaduais').exists())
except Exception as exc:checks.append({'name':'execution_error','passed':False,'detail':repr(exc)});raise
finally:
    (a.out/'qa.json').write_text(json.dumps({'passed':bool(checks) and all(c['passed'] for c in checks),'checks':checks,'count':len(checks)},indent=2))
    subprocess.run(['git','worktree','remove','--force',str(work)],cwd=ROOT,check=False)
print(json.dumps({'passed':True,'checks':len(checks)}))

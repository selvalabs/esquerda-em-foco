"""Exercise real generators in disposable worktrees, not in published paths.
The RS branch's AD3 incremental pipeline is replayed, not its older base builder.
Reports explicitly distinguish published-source parity from template independence.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, subprocess, sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global02'))
from core import save,load,digest
from prepare import BASE,RS
CHECKS=[]
MODIFIED={'deputados-estaduais/tools/render.py','deputados-estaduais/tools/review2_build.py','tools/rs/build.py','tools/pr/build.py','sitemap.xml'}
PREFIXES=('assets/global/','tools/global02/','tests/global02/','templates/global02/','data/global02/')
NEW={'config/editions.json','config/editions.schema.json','config/taxonomies.json','config/legacy-sc-links.json',
     '.github/workflows/global02-foundation.yml'}


def check(name,condition,detail=None):
    CHECKS.append({'name':name,'passed':bool(condition),'detail':detail})
    if not condition:raise AssertionError(name+': '+str(detail))


def run(args,cwd,log):
    env={**os.environ,'EEFOCO_OFFLINE_BUILD':'1','PYTHONDONTWRITEBYTECODE':'1'}
    with log.open('a') as out:
        out.write('\n$ '+ ' '.join(map(str,args))+'\n');out.flush()
        subprocess.run(list(map(str,args)),cwd=cwd,env=env,stdout=out,stderr=subprocess.STDOUT,check=True,timeout=240)


def baseline(path,ref=BASE):
    return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)


def preservation():
    paths=subprocess.check_output(['git','ls-tree','-r','--name-only',BASE],cwd=ROOT,text=True).splitlines()
    checked=0
    for p in paths:
        if p in MODIFIED:continue
        original=hashlib.sha256(baseline(p)).hexdigest()
        check('preserved '+p,(ROOT/p).is_file() and digest(ROOT/p)==original)
        checked+=1
    for p in subprocess.check_output(['git','diff','--name-only',BASE],cwd=ROOT,text=True).splitlines():
        check('allowed diff '+p,p in MODIFIED or p in NEW or p.startswith(PREFIXES) or p.startswith('docs/GLOBAL-'))
    check('original files protected',checked>1600,checked)
    for t in load(ROOT/'templates/global02/manifest.json')['templates']:
        check('frozen source '+t['id'],digest(ROOT/t['path'])==t['sha256']==hashlib.sha256(baseline(t['source_path'],t['source_ref'])).hexdigest())


def worktree(path,ref):
    subprocess.run(['git','worktree','add','--detach',str(path),ref],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    return path


def cards(path):
    doc=BeautifulSoup(path.read_text(),'html.parser')
    return [(c['id'],c.get_text(' ',strip=True)) for c in doc.select('article.candidate')]


def outputs(root,paths):
    return {p:digest(root/p) for p in paths}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    clones=[]
    try:
        preservation()
        main=worktree(out/'main',BASE);clones.append(main)
        for rel in MODIFIED-{'sitemap.xml'}:shutil.copy2(ROOT/rel,main/rel)
        shutil.copytree(ROOT/'templates/global02',main/'templates/global02',dirs_exist_ok=True)
        jobs=[('sc-state',[sys.executable,'-c',
            "import sys,hashlib;from pathlib import Path;sys.path.insert(0,'deputados-estaduais/tools');import review2_build as b;r=Path('.');h={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in r.rglob('*') if p.is_file() and not str(p).startswith(('deputados-estaduais/','.git'))};b.main(isolation_baseline=h)"],
            ['deputados-estaduais/index.html','deputados-estaduais/data/candidaturas.json','deputados-estaduais/data/votos-historicos.json']),
          ('rs-federal',[sys.executable,'tools/rs/build.py'],['rs/deputados-federais/index.html','rs/deputados-federais/dados.json']),
          ('pr',[sys.executable,'tools/pr/build.py'],['pr/deputados-federais/index.html','pr/deputados-federais/dados.json','pr/deputados-estaduais/index.html','pr/deputados-estaduais/dados.json'])]
        for name,command,paths in jobs:
            published={p:cards(main/p) for p in paths if p.endswith('index.html')}
            run(command,main,out/(name+'.log'))
            first=outputs(main,paths)
            # Baseline identity/text comparison is explicit. Do not hide deviations.
            for p,before in published.items():
                check(name+' published card content '+p,before==cards(main/p))
            donor=['index.html']+(['rs/deputados-federais/index.html'] if name=='pr' else [])
            saved={p:(main/p).read_bytes() for p in donor}
            for p in donor:(main/p).write_text('<!doctype html><title>Future home independence fixture</title><main>No candidate template here</main>')
            try:
                run(command,main,out/(name+'.log'))
                check(name+' outputs independent of ready pages',first==outputs(main,paths),paths)
            finally:
                for p,raw in saved.items():(main/p).write_bytes(raw)
        rs=worktree(out/'rs',RS);clones.append(rs)
        shutil.copytree(ROOT/'templates/global02',rs/'templates/global02',dirs_exist_ok=True)
        subprocess.run(['git','apply',str(ROOT/'data/global02/rs-estaduais-template.patch')],cwd=rs,check=True)
        paths=['rs/deputados-estaduais/'+p for p in ['index.html','dados.json','pesquisa-status.json','revisoes.json']]
        published={p:digest(rs/p) for p in paths};content=cards(rs/paths[0])
        run([sys.executable,'tools/rs-estaduais/ad3.py','render'],rs,out/'rs-state.log')
        first=outputs(rs,paths)
        check('RS AD3 original card content',content==cards(rs/paths[0]))
        check('RS AD3 original data preserved',all(published[p]==first[p] for p in paths[1:]))
        for p in ('index.html','rs/deputados-federais/index.html'):(rs/p).write_text('<main>Not a template</main>')
        run([sys.executable,'tools/rs-estaduais/ad3.py','render'],rs,out/'rs-state.log')
        check('RS AD3 independent of both pages',first==outputs(rs,paths))
        data=load(rs/'rs/deputados-estaduais/dados.json')['candidates']
        check('RS AD3 partial research not overwritten',len(data)==149 and sum(bool(c['pautas']) for c in data)==72)
        check('branch was not published',not (ROOT/'rs/deputados-estaduais').exists())
    except Exception as exc:
        CHECKS.append({'name':'execution_error','passed':False,'detail':repr(exc)})
        raise
    finally:
        save(out/'rebuild.json',{'passed':bool(CHECKS) and all(c['passed'] for c in CHECKS),'count':len(CHECKS),'checks':CHECKS,
          'baseline':BASE,'branch_ref':RS,'writes_to_public_repository':False})
        for clone in clones:subprocess.run(['git','worktree','remove','--force',str(clone)],cwd=ROOT,check=False)
    print(json.dumps({'passed':True,'checks':len(CHECKS)}))

if __name__=='__main__':main()

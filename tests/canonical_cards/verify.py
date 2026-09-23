"""Verify frozen-input, every observation and original Git tree preservation."""
from __future__ import annotations
import argparse,json,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import BASE,sha,jsha,load,save,resolve

def verify(prototype,check_git=True):
 models=load(prototype/'audit/models.json');inputs=load(ROOT/'config/canonical-card-inputs.json')['files']
 for p,h in inputs.items():
  if sha((ROOT/p).read_bytes())!=h:raise AssertionError('Input changed '+p)
 cache={};observations=0
 def examine(o):
  nonlocal observations
  ref=o['ref'];p=ref['path']
  if p not in inputs:raise AssertionError('Unregistered source '+p)
  if ref['sha256']!=inputs[p]:raise AssertionError('Source digest differs')
  if p not in cache:cache[p]=load(ROOT/p) if ref['kind']=='json' else BeautifulSoup((ROOT/p).read_bytes(),'html.parser')
  if ref['kind']=='json':v=resolve(cache[p],ref['pointer'])
  else:
   node=cache[p].select_one(ref['selector'])
   if node is None:raise AssertionError('Missing node')
   v=node.get_text(' ',strip=True)
  if v!=o['value'] or jsha(v)!=ref['value_sha256']:raise AssertionError('Untraceable displayed observation')
  observations+=1
 for m in models:
  for o in m['observations'].values():examine(o)
  for o in m['history']['provenance']:examine(o)
  for ev in m['evidence']:
   for o in ev['provenance']:examine(o)
   for source in ev['sources']:
    examine(source['provenance'])
    if source.get('review_provenance'):examine(source['review_provenance'])
 preserved=None;changes=[]
 if check_git:
  baseline=subprocess.check_output(['git','ls-tree','-r',BASE],cwd=ROOT,text=True).splitlines()
  current=subprocess.check_output(['git','ls-tree','-r','HEAD'],cwd=ROOT,text=True).splitlines()
  tree={s.split('\t',1)[1]:s.split('\t',1)[0] for s in current}
  for line in baseline:
   obj,p=line.split('\t',1)
   if tree.get(p)!=obj:raise AssertionError('Preexisting Git object changed: '+p)
  preserved=len(baseline)
  changes=subprocess.check_output(['git','diff','--name-only',BASE,'HEAD'],cwd=ROOT,text=True).splitlines()
  for p in changes:
   if not p.startswith(('tools/canonical_cards/','tests/canonical_cards/','config/canonical-card','docs/GLOBAL-CARD','.github/workflows/canonical-cards.yml')):raise AssertionError('Unexpected diff '+p)
  if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip():raise AssertionError('Dirty working tree')
 return {'passed':True,'baseline':BASE,'cards':len(models),'input_files_verified':len(inputs),'observations_verified':observations,'git_objects_preserved':preserved,'new_paths':changes,'public_activation':False}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prototype',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--no-git',action='store_true');a=p.parse_args()
 result=verify(a.prototype,not a.no_git);save(a.out,result);print(json.dumps(result,ensure_ascii=False))

"""Verify D1's change boundary against the actual frozen Git commit.
All existing files must be unchanged except an additive migration-status section.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess
from pathlib import Path
from decisions import BASE
ROOT=Path(__file__).resolve().parents[2]
STATUS='data/global-integration/migration-status.json'
ALLOWED_NEW=('tools/global_filters/','tests/global_filters/','config/global-filter-taxonomy',
 'data/global-integration/filter-','docs/GLOBAL-FILTER-', '.github/workflows/global-filter-taxonomy.yml')
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT)
def tree(ref):
    d={}
    for line in git('ls-tree','-r',ref).decode().splitlines():
        meta,path=line.split('\t',1);d[path]=meta
    return d

def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    before,after=tree(BASE),tree('HEAD');violations=[]
    protected=[path for path in before if path!=STATUS]
    for path in protected:
        if after.get(path)!=before[path]:violations.append('Existing file changed: '+path)
    for path in after.keys()-before.keys():
        if not path.startswith(ALLOWED_NEW):violations.append('New path outside D1: '+path)
    old=json.loads(git('show',BASE+':'+STATUS));new=json.loads(git('show','HEAD:'+STATUS))
    addition=new.pop('canonical_filter_contract',None)
    if old!=new or not addition or addition.get('issue')!=53:violations.append('Status is not an additive D1 contract')
    for item in json.loads((ROOT/'data/global-integration/filter-inputs.json').read_text())['sources']:
        original=hashlib.sha256(git('show',BASE+':'+item['path'])).hexdigest()
        if original!=item['sha256']:violations.append('Input hash does not match real Git baseline: '+item['path'])
    if git('status','--porcelain').strip():violations.append('Working tree is not clean')
    report={'baseline':BASE,'executed_commit':git('rev-parse','HEAD').decode().strip(),'passed':not violations,
       'protected_preexisting_files':len(protected),'source_hashes_checked':len(json.loads((ROOT/'data/global-integration/filter-inputs.json').read_text())['sources']),
       'changed_preexisting_files':[STATUS],'new_files':sorted(after.keys()-before.keys()),'violations':violations,
       'scope':'Git objects and source SHA-256; no new browser or public HTTP claims'}
    a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False));
    if violations:raise SystemExit(1)
if __name__=='__main__':main()

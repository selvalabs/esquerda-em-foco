"""Deterministically extract the approved SC reader and bind it to six editions.
This is a development generator, not an electoral-data collector. Final CI is read-only.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
from bs4 import BeautifulSoup
from build import ROOT,BASE,load,save
from patch_runtime import patch


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--baseline-root',type=Path);a=ap.parse_args()
    def original(path):
        return (a.baseline_root/path).read_bytes() if a.baseline_root else subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
    html=BeautifulSoup(original('sc/deputados-federais/index.html').decode(),'html.parser')
    parts=[]
    for id in ['eefSelectionBar','eefCollection','eefShareDialog','eefConfirm','eefSelectionStatus']:
        n=html.find(id=id)
        if n is None:raise ValueError('Missing approved dialog '+id)
        n['data-global04']='collection';parts.append(str(n))
    path=ROOT/'templates/global04/collection.html.txt';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(parts).replace('viewbox=','viewBox='))
    shutil.copyfile(ROOT/'assets/selecionados.js',ROOT/'assets/global/selection.js')
    subprocess.run(['git','apply','--check','tools/global04/selection-runtime.patch'],cwd=ROOT,check=True)
    subprocess.run(['git','apply','tools/global04/selection-runtime.patch'],cwd=ROOT,check=True)
    css=(ROOT/'assets/editorial-selected.css').read_text().split('@media(max-width:1200px)')[0]
    css=css.replace('/* Escopo local SC/Federais. Os dados e a ordem da listagem não mudam. */','/* Shared reader adapted from SC; original cards and data remain edition-specific. */')
    (ROOT/'assets/global/selection.css').write_text(css+(ROOT/'tools/global04/selection-css-tail.txt').read_text())
    patch()
    subprocess.run([sys.executable,'tools/global04/build.py'],cwd=ROOT,check=True)
    previous=json.loads(original('config/editions.json'));current=load(ROOT/'config/editions.json')
    matrix=load(ROOT/'data/global-integration/capability-matrix.json')
    rows=[]
    for e in current['editions']:
        before=next(p for p in previous['editions'] if p['edition_id']==e['edition_id'])
        public=e['publication_status']=='published'
        rows.append({'edition_id':e['edition_id'],'baseline':BASE,'publication_status':e['publication_status'],
            'before':before['capabilities'],'after_lot01':e['capabilities'],
            'capability_decisions':[{'id':c['id'],'name':c['name'],
                'lot01':('implemented_pending_release_check' if public and c['id'] in ['I01','I02','I03']+(['I04'] if e['state']=='SP' else []) else 'preserved_not_migrated_in_this_lot')}
                for c in matrix['capabilities']],
            'implemented_in_code':['selection','single-card-reader','collection-v2','individual-sharing']+(['SP-deep-link-recovery'] if e['state']=='SP' else []) if public else [],
            'remaining':['G4-C common query controls and explicit query sharing','G4-D editorial/evidence/transparency composition'] if public else ['Independent RS state publication gate'],
            'test_suite':'tests/global04/validate.py' if public else None,
            'release_evidence':'Issue #43 / lot01 PR; generator does not claim publication'})
    save(ROOT/'data/global-integration/migration-status.json',{'schema_version':'1.0.0','baseline':BASE,'issue':43,'lot':'01','whole_issue_completed':False,'editions':rows})
    subprocess.run([sys.executable,'tools/global03/publication.py','--prepare'],cwd=ROOT,check=True)

if __name__=='__main__':main()

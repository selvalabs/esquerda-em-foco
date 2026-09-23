"""Apply route/shell to reviewed local-renderer output; no datasets or publication."""
import argparse,shutil
from pathlib import Path
from build import ROOT,SITE,load,validate,edition_page,alias
p=argparse.ArgumentParser();p.add_argument('--edition',required=True);p.add_argument('--input',type=Path,required=True);p.add_argument('--source-path',required=True);a=p.parse_args()
r=load(ROOT/'config/editions.json');validate(r)
if r['root_mode']!='global_home':raise ValueError('Activate global home first')
e=next((e for e in r['editions'] if e['edition_id']==a.edition and e['publication_status']=='published'),None)
if not e:raise ValueError('Unknown or unpublished edition')
# The legacy SC/SP generators also replace their executable assets. Restore the
# versioned integration runtime, not any candidate payload, before hashing links.
if e.get('capabilities',{}).get('global_query_v1',{}).get('state')=='ready':
    runtime={'2026-sc-federais':('sc-federal.js','assets/pauta-filters-editorial.js'),
             '2026-sp-federais':('sp-federal.js','sp/deputados-federais/assets/app.js')}.get(e['edition_id'])
    if runtime:
        src,dest=runtime
        shutil.copyfile(ROOT/'tools/global04/query_runtime'/src,ROOT/dest)
raw=a.input.read_text();result=edition_page(raw,e,r,a.source_path,e['entrypoint'],SITE)
(ROOT/e['entrypoint']).write_text(result)
if a.edition=='2026-sc-estaduais':(ROOT/'deputados-estaduais/index.html').write_text(alias(r,SITE))
if e.get('capabilities',{}).get('global_collection_v2',{}).get('state')=='ready':
    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT/'tools/global04/build.py'),'--edition',e['edition_id']],check=True)
if e.get('capabilities',{}).get('canonical_filters',{}).get('state')=='ready':
    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT/'tools/global_rollout/build.py'),'--edition',e['edition_id'],'--no-metadata'],check=True)
elif e.get('capabilities',{}).get('global_query_v1',{}).get('state')=='ready':
    import subprocess,sys
    subprocess.run([sys.executable,str(ROOT/'tools/global04/query_build.py'),'--edition',e['edition_id'],'--no-metadata'],check=True)
print(e['entrypoint'])

"""One-time, pinned migration of layout inputs and deterministic metadata generation.
--freeze is used only when preparing the branch. Normal builds consume committed
files and never retrieve historical HTML. No public edition is rendered here.
"""
from __future__ import annotations
import argparse
import copy
import re
import subprocess
from pathlib import Path
from bs4 import BeautifulSoup
from core import ROOT, load, save, digest, validate, sitemap, require
BASE = 'cb845fcfb0b57f7907fd9d129555b6bb558a9ce1'
OLD = '71d123b909cdbf3d84bd1cdca89511890759d395'
RS = 'c2bfa3ece357f21e8aa09e32f624a9e214ad9113'


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding='utf-8')
    if new in text:
        return
    require(text.count(old) == 1, 'Missing or ambiguous migration anchor: ' + str(path))
    path.write_text(text.replace(old, new, 1), encoding='utf-8')


def freeze() -> None:
    manifest_path = ROOT / 'templates/global02/manifest.json'
    if manifest_path.exists():
        for item in load(manifest_path)['templates']:
            require(digest(ROOT / item['path']) == item['sha256'], 'Frozen template changed')
        return
    specs = [('sc-state', BASE, 'index.html'), ('rs-federal', OLD, 'index.html'),
             ('pr', BASE, 'rs/deputados-federais/index.html'),
             ('rs-state', RS, 'rs/deputados-federais/index.html')]
    items = []
    for name, ref, source in specs:
        raw = subprocess.check_output(['git', 'show', f'{ref}:{source}'], cwd=ROOT)
        path = ROOT / f'templates/global02/{name}.html.txt'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        items.append({'id':name,'path':str(path.relative_to(ROOT)),'sha256':digest(path),
                      'source_ref':ref,'source_path':source,
                      'purpose':'Frozen legacy renderer input; not the global design system or research source.'})
    save(manifest_path, {'schema_version':'1.0.0','templates':items})


def decouple() -> None:
    replace_once(ROOT/'deputados-estaduais/tools/render.py',
        "federal=(REPO/'index.html').read_bytes(); before=hashlib.sha256(federal).hexdigest()",
        "federal=(REPO/'templates/global02/sc-state.html.txt').read_bytes(); before=hashlib.sha256((REPO/'index.html').read_bytes()).hexdigest()")
    old = """def template_bytes():
 try:return subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT,stderr=subprocess.DEVNULL)
 except (OSError,subprocess.CalledProcessError):
  raw=(ROOT/'index.html').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=BASELINE_HASH:raise RuntimeError('Frozen SC template unavailable')
  return raw"""
    new = """def template_bytes():
 raw=(ROOT/'templates/global02/rs-federal.html.txt').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=BASELINE_HASH:raise RuntimeError('Versioned legacy template changed')
 return raw"""
    replace_once(ROOT/'tools/rs/build.py', old, new)
    replace_once(ROOT/'tools/pr/build.py',
        "template=(ROOT/'rs/deputados-federais/index.html').read_text()",
        "template=(ROOT/'templates/global02/pr.html.txt').read_text()")
    # Explicit per-run isolation input. Historical baseline remains the default.
    path = ROOT/'deputados-estaduais/tools/review2_build.py'
    replace_once(path, 'def main(preview=False):', 'def main(preview=False, isolation_baseline=None):')
    replace_once(path, "baseline=load(REVIEW/'baseline.json')", "baseline=load(REVIEW/'baseline.json')\n if isolation_baseline is not None: baseline={**baseline,'outside_state_sha256':isolation_baseline}")
    # RS Estadual is NOT merged. Store a deterministic patch for its own release.
    source = subprocess.check_output(['git','show',f'{RS}:tools/rs-estaduais/build.py'],cwd=ROOT).decode()
    target = source.replace("ROOT/'rs/deputados-federais/index.html'", "ROOT/'templates/global02/rs-state.html.txt'")
    require(source != target, 'RS Estadual template input not found')
    import difflib
    patch = ''.join(difflib.unified_diff(source.splitlines(True), target.splitlines(True),
        fromfile='a/tools/rs-estaduais/build.py',tofile='b/tools/rs-estaduais/build.py'))
    p=ROOT/'data/global02/rs-estaduais-template.patch';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(patch)


def registry() -> dict:
    inventory = load(ROOT/'data/global-integration/current-editions.json')
    matrix = load(ROOT/'data/global-integration/capability-matrix.json')
    names = {'SC':'Santa Catarina','RS':'Rio Grande do Sul','PR':'Paraná','SP':'São Paulo'}
    out={'schema_version':'1.0.0','baseline_commit':BASE,'root_mode':'sc_federal_until_global03',
         'states':[{'code':uf,'name':names[uf],'path':'/'+uf.lower()+'/', 'published':uf in ('PR','SP')} for uf in ('SC','RS','PR','SP')],
         'editions':[]}
    for i, old in enumerate(inventory['editions']):
        eid=old['edition_id']; pub=old['publication_status']!='branch_only'
        office=old['office']; label='Deputados federais' if office.endswith('federais') else 'Deputados estaduais'
        capabilities={c['id']:{'state':{'functional':'ready','partial':'partial','absent':'absent','incompatible':'edition_specific'}[c['states'][i]],
                             'semantic':None,'audit_ref':c['id']} for c in matrix['capabilities']}
        for cap, state, semantic in [
            ('current_support','ready' if eid=='sc-federais' else 'blocked_data','current_support'),
            ('documented_topic','ready' if eid=='sp-federais' else 'partial' if eid.startswith('pr-') else 'absent','documented_topic'),
            ('selected_collection','ready' if eid=='sc-federais' else 'absent',None),
            ('global_shell','absent',None)]:
            capabilities[cap]={'state':state,'semantic':semantic,'audit_ref':'GLOBAL-01'}
        entry=ROOT/old['entrypoint']
        description = None
        if pub:
            soup=BeautifulSoup(entry.read_text(), 'html.parser')
            title=soup.title.get_text();meta=soup.select_one('meta[name="description"]')
            description=meta.get('content','') if meta else ''
        else:
            title=f'{label} · {names[old["state"]]} · 2026 | Esquerda em Foco'
            description='Edição em preparação; publicação sujeita à revisão própria.'
        out['editions'].append({
            'edition_id':'2026-'+eid,'legacy_ids':[eid],'election_year':2026,'state':old['state'],
            'office':office,'office_code':6 if office.endswith('federais') else 7,'office_label':label,
            'canonical_path':old['future_route_proposal'],'current_path':old['route'] if pub else None,
            'aliases':[old['route']] if eid=='sc-estaduais' else [],
            'entrypoint':old['entrypoint'],'publication_status':'published' if pub else 'branch_only',
            'research':{'status':old['research_status'],'source':'data/global-integration/current-editions.json','release_dependency':old['release_dependency']},
            'snapshot':{'source':old['entrypoint'],'sha256':old['html_sha256'],'source_ref':inventory['refs'][old['ref']], 'kind':'published_html_not_new_electoral_collection'},
            'capabilities':capabilities,'metadata':{'title':title,'description':description},
            'migration':{'routes_active':not eid.startswith('sc-'),'shell_active':False,'template_contract':'global02'},
        })
    validate(out);return out


def schemas() -> dict:
    cap={'type':'object','required':['state','semantic','audit_ref'],'additionalProperties':False,'properties':{
        'state':{'enum':['ready','partial','absent','blocked_data','edition_specific','not_applicable']},
        'semantic':{'enum':[None,'current_support','documented_topic','legacy_context']},'audit_ref':{'type':'string'}}}
    string={'type':'string'};path={'type':'string','pattern':'^/(?:[a-z0-9-]+/)*$'}
    properties={'edition_id':{'type':'string','pattern':'^[0-9]{4}-[a-z]{2}-(federais|estaduais)$'},
      'legacy_ids':{'type':'array','items':string,'uniqueItems':True},'election_year':{'type':'integer','minimum':2000},
      'state':{'type':'string','pattern':'^[A-Z]{2}$'},'office':{'enum':['deputados-federais','deputados-estaduais']},
      'office_code':{'enum':[6,7]},'office_label':string,'canonical_path':path,'current_path':{'anyOf':[path,{'type':'null'}]},
      'aliases':{'type':'array','items':path,'uniqueItems':True},'entrypoint':string,
      'publication_status':{'enum':['published','branch_only','archived']},
      'research':{'type':'object','required':['status','source','release_dependency']},
      'snapshot':{'type':'object','required':['source','sha256','source_ref','kind']},
      'capabilities':{'type':'object','minProperties':1,'additionalProperties':cap},
      'metadata':{'type':'object','required':['title','description'],'properties':{'title':string,'description':string},'additionalProperties':False},
      'migration':{'type':'object','required':['routes_active','shell_active','template_contract']}}
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'Esquerda em Foco · Editions 1.0',
       'type':'object','required':['schema_version','baseline_commit','root_mode','states','editions'],'additionalProperties':False,
       'properties':{'schema_version':{'const':'1.0.0'},'baseline_commit':string,'root_mode':{'enum':['sc_federal_until_global03','global_home']},
         'states':{'type':'array','items':{'type':'object','required':['code','name','path','published'],'additionalProperties':False,
           'properties':{'code':string,'name':string,'path':path,'published':{'type':'boolean'}}}},
         'editions':{'type':'array','minItems':1,'items':{'type':'object','required':list(properties),'additionalProperties':False,'properties':properties}}}}


def taxonomies() -> dict:
    specs=[('sc-v1','config/topics-v1.json','topics'),('sp-product-v1','sp/deputados-federais/dados.json','taxonomy'),
           ('rs-v1','data/rs/topics.json','topics'),('pr-v1','data/pr/taxonomy.json','themes')]
    catalogs=[]
    for namespace,src,key in specs:
        data=load(ROOT/src)[key]
        values=[{'id':k,'label':v} for k,v in data.items()] if isinstance(data,dict) else data
        concepts=[{'id':namespace+':'+x['id'],'source_id':x['id'],'label':x.get('label',x.get('name',x['id'])),
                   'definition':copy.deepcopy(x),'crosswalk_status':'unreviewed','equivalent_to':[]}
                  for x in values]
        catalogs.append({'namespace':namespace,'source':src,'source_sha256':digest(ROOT/src),'concepts':concepts})
    return {'schema_version':'1.0.0','association_policy':'No automatic conversion, alias or keyword classification.',
            'semantics':['current_support','documented_topic','legacy_context'],'catalogs':catalogs,'reviewed_crosswalk':[]}


def main() -> None:
    parser=argparse.ArgumentParser();parser.add_argument('--freeze',action='store_true');args=parser.parse_args()
    if args.freeze:
        freeze();decouple()
    require(digest(ROOT/'index.html') == load(ROOT/'data/global-integration/current-editions.json')['editions'][0]['html_sha256'], 'Bootstrap refuses changed root; edit the registry deliberately after GLOBAL-03')
    out=registry();save(ROOT/'config/editions.json',out);save(ROOT/'config/editions.schema.json',schemas())
    save(ROOT/'config/taxonomies.json',taxonomies())
    soup=BeautifulSoup((ROOT/'index.html').read_text(), 'html.parser')
    save(ROOT/'config/legacy-sc-links.json',{'schema_version':'1.0.0','source_ref':BASE,'source_sha256':digest(ROOT/'index.html'),
      'target':'/sc/deputados-federais/','candidate_ids':[n['id'].removeprefix('candidato-') for n in soup.select('article.candidate[id]')],
      'anchors':sorted({n['id'] for n in soup.select('[id]')}),
      'reserved_home_prefix':'global-','note':'Global home must use global-* IDs. Unknown fragments are never redirected.'})
    base='https://selvalabs.github.io/esquerda-em-foco/'
    (ROOT/'sitemap.xml').write_text(sitemap(out,base,'current'))
    p=ROOT/'data/global02/sitemap-next.xml';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(sitemap(out,base,'next'))


if __name__=='__main__':main()

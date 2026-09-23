"""Static routes, metadata, local references and exact research preservation.
This is NOT HTTP verification. Historical snapshots are compared, not rewritten.
"""
from __future__ import annotations
import argparse,collections,hashlib,html,importlib.util,json,re,xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urljoin,urlsplit,unquote,parse_qs
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
SITE='https://selvalabs.github.io/esquerda-em-foco/'
BASELINE='4a3300005fafbf85e13c4a61e763db1496924348'
spec=importlib.util.spec_from_file_location('global05_head',ROOT/'tools/global05/build.py');head=importlib.util.module_from_spec(spec);spec.loader.exec_module(head)

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--baseline-root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--record-only',action='store_true');a=p.parse_args()
 root=a.root.resolve();base=a.baseline_root.resolve();checks=[];pages=head.public_pages(root);docs={};ids={};total_links=0
 def check(name,ok,detail=None):checks.append({'name':name,'passed':bool(ok),'detail':detail})
 def doc(path):
  if path not in docs:docs[path]=BeautifulSoup((root/path).read_text(),'html.parser');ids[path]={n['id'] for n in docs[path].select('[id]')}
  return docs[path]
 reg=json.loads((root/'config/editions.json').read_text());editions=[e for e in reg['editions'] if e['publication_status']=='published'];indexable=pages[:-2]
 routes={s:SITE+(s[:-10] if s.endswith('index.html') else s) for s in pages}
 titles=[];descriptions=[];rows=[]
 for path in pages:
  d=doc(path);meta=lambda selector:(d.select_one(selector).get('content','').strip() if d.select_one(selector) else '')
  title=d.title.get_text(strip=True) if d.title else '';description=meta('meta[name="description"]');canonical=d.select('link[rel="canonical"]');canonical_url=canonical[0].get('href','') if canonical else ''
  expected=SITE+'sc/deputados-estaduais/' if path=='deputados-estaduais/index.html' else routes[path]
  check(path+' title and description',bool(title) and bool(description));check(path+' language',d.html.get('lang')=='pt-BR')
  check(path+' one main/H1',len(d.select('main'))==1 and len(d.select('h1'))==1)
  check(path+' canonical',len(canonical)==0 if path=='404.html' else len(canonical)==1 and canonical_url==expected,canonical_url) # A noindex 404 intentionally has no canonical.
  check(path+' viewport',bool(meta('meta[name="viewport"]')))
  check(path+' robots',('noindex' not in meta('meta[name="robots"]').lower()) if path in indexable else ('noindex' in meta('meta[name="robots"]').lower()))
  check(path+' one ID per element',len(d.select('[id]'))==len(ids[path]))
  # A resolved label must identify real text, not merely an empty label element.
  label_for={x.get('for'):x.get_text(' ',strip=True) for x in d.select('label[for]')};missing=[];aria=[]
  for n in d.select('input:not([type="hidden"]),select,textarea,button'):
   name=n.get('aria-label') or label_for.get(n.get('id')) or (n.find_parent('label').get_text(' ',strip=True) if n.find_parent('label') else '') or (n.get_text(' ',strip=True) if n.name=='button' else '')
   named_by=n.get('aria-labelledby','').split()
   if not name and named_by:name=' '.join(d.find(id=i).get_text(' ',strip=True) for i in named_by if d.find(id=i))
   if not name:missing.append(str(n)[:180])
  for n in d.select('[aria-labelledby],[aria-describedby],[aria-controls]'):
   for attr in ('aria-labelledby','aria-describedby','aria-controls'):
    for ref in n.get(attr,'').split():
     if ref not in ids[path]:aria.append({'id':n.get('id'),'attribute':attr,'reference':ref})
  check(path+' named controls',not missing,missing);check(path+' ARIA references resolve',not aria,aria)
  og={n.get('property'):n.get('content') for n in d.select('meta[property^="og:"]')}
  check(path+' Open Graph baseline',all(og.get(k) for k in ('og:title','og:description','og:url','og:type','og:image','og:site_name')))
  image=og.get('og:image','');check(path+' absolute share image',image.startswith(SITE) and (root/unquote(image.removeprefix(SITE))).is_file(),image)
  errors=[];revisions=[]
  for n in d.select('a[href],script[src],link[rel="stylesheet"],link[rel="icon"],img[src]'):
   value=n.get('href',n.get('src',''));u=urlsplit(urljoin(routes[path],value))
   if u.scheme not in ('http','https') or u.netloc!='selvalabs.github.io' or not u.path.startswith('/esquerda-em-foco/'):continue
   rel=unquote(u.path.removeprefix('/esquerda-em-foco/'));target=(root/(rel or 'index.html')).resolve()
   if target.is_dir():target=target/'index.html'
   total_links+=1
   if not target.is_relative_to(root) or not target.is_file():errors.append({'url':value,'problem':'file absent'});continue
   target_rel=str(target.relative_to(root))
   if u.fragment and target.suffix=='.html' and not u.fragment.startswith('eef='):
    doc(target_rel)
    legacy_root=target_rel=='index.html' and u.fragment.startswith(('candidato-','partido-','fonte-'))
    if unquote(u.fragment) not in ids[target_rel] and not legacy_root:errors.append({'url':value,'problem':'anchor absent'})
   if target.suffix in ('.js','.css'):
    actual=parse_qs(u.query).get('v',[]);expected_rev=digest(target)[:12]
    if actual!=[expected_rev]:revisions.append({'url':value,'expected':expected_rev})
  check(path+' local links/files/anchors',not errors,errors);check(path+' asset revisions match bytes',not revisions,revisions)
  rows.append({'path':path,'canonical':canonical_url,'title':title,'description':description,'robots':meta('meta[name="robots"]'),'og_image':image,'html_sha256':digest(root/path),'indexable':path in indexable})
  if path in indexable:titles.append(title);descriptions.append(description)
 check('unique indexable titles',len(titles)==len(set(titles))==11);check('unique indexable descriptions',len(descriptions)==len(set(descriptions))==11)
 sitemap=ET.parse(root/'sitemap.xml').getroot();locations=[n.text for n in sitemap.findall('{*}url/{*}loc')]
 check('sitemap exactly matches 11 catalog routes',set(locations)=={routes[p] for p in indexable} and len(locations)==11)
 check('robots references sitemap',('Sitemap: '+SITE+'sitemap.xml') in (root/'robots.txt').read_text())
 # Robots file in a project subpath is not asserted to control host-root crawling.
 check('website manifest scope',json.loads((root/'site.webmanifest').read_text()).get('scope')=='./')
 allow=set(pages)|{'assets/global/home.css','assets/global/selection.css','assets/global/navigation.css','assets/global/rollout.js','data/global03/publication-files.json','tools/global03/publication.py','README.md','tests/global_rollout/verify.py'}
 changed=[];protected=0;unexpected=[]
 for f in sorted(base.rglob('*')):
  if not f.is_file():continue
  path=str(f.relative_to(base));other=root/path
  if not other.is_file() or digest(f)!=digest(other):
   changed.append(path)
   if path not in allow:unexpected.append(path)
  else:protected+=1
 check('outside-scope files unchanged',not unexpected,unexpected)
 total_cards=0
 for e in editions:
  path=e['entrypoint'];old=BeautifulSoup((base/path).read_text(),'html.parser');new=doc(path)
  oc=old.select('article.candidate');nc=new.select('article.candidate');total_cards+=len(nc)
  check(e['edition_id']+' original card markup exact',[str(x) for x in nc]==[str(x) for x in oc],{'cards':len(nc)})
  check(e['edition_id']+' query data unchanged',new.select_one('#cqData').get_text()==old.select_one('#cqData').get_text())
  check(e['edition_id']+' original outside-head text unchanged',new.body.get_text()==old.body.get_text())
 check('760 original cards',total_cards==760,total_cards)
 manifest=json.loads((root/'data/global03/publication-files.json').read_text())['files'];badmanifest=[i['path'] for i in manifest if digest(root/i['path'])!=i['sha256']]
 check('publication manifest matches local bytes',not badmanifest,{'files':len(manifest),'mismatches':badmanifest})
 check('head finalization idempotent',not head.apply(root,write=False)['changed_pages'])
 report={'passed':bool(checks) and all(c['passed'] for c in checks),'mode':'static-files-not-HTTP','baseline_commit':BASELINE,'checks':checks,'count':len(checks),'routes':rows,'local_references_checked':total_links,'original_cards':total_cards,'protected_files':protected,'intentional_original_changes':changed,'limits':['HTTP redirects, root robots, 404 status, external URLs and crawler indexing are not tested','Metadata completeness is not a promise of social-preview rendering or search ranking']}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({k:report[k] for k in ('passed','mode','count','original_cards','protected_files','local_references_checked')}))
 if not report['passed'] and not a.record_only:raise SystemExit(1)
if __name__=='__main__':main()

"""Build the isolated D2/D3 prototype and audit. Never writes public entrypoints.
Usage: python tools/canonical_cards/build.py --out /tmp/eef-card-prototype
"""
from __future__ import annotations
import argparse,copy,html,json,posixpath,re,shutil
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
from model import ROOT,BASE,Repository,save,sha,jsha,resolve
from render import enhance_card,original_signature,added


def topic_labels(root,e):
 namespace={'SC':'sc-v1','SP':'sp-product-v1','RS':'rs-v1','PR':'pr-v1'}[e['state']]
 catalog=next(x for x in json.loads((root/'config/taxonomies.json').read_text())['catalogs'] if x['namespace']==namespace)
 return {c['source_id']:c['label'] for c in catalog['concepts']}

def editorial_variants(repo,e,models):
 """Explicit precedence ledger, not a word-similarity assertion of factual parity."""
 rows=[];eid=e['edition_id']
 for m in models:
  row={'key':m['key'],'current':m['original_card'],'decision':'preserve_current_prose_sources_and_caveats','variants':[]}
  if eid=='2026-sc-federais':
   for p in ['data/sc-semantic-v2/candidate-content.json','data/sc-editorial-selected-r1/editorial.json']:
    arr=repo.read(p)['candidates'];i=next(i for i,x in enumerate(arr) if x['candidate_id']==m['candidate_id']);x=arr[i]
    row['variants'].append({'role':'atomic_semantics' if 'semantic-v2/' in p else 'readable_editorial',
     'ref':repo.observation(p,f'/candidates/{i}')['ref'],'sections':[s['id'] for s in x.get('sections',[])],
     'decision':'retain_atomic_evidence_with_readable_current_paragraphs' if 'semantic-v2/' in p else 'preserve_current_wording_and_limitations'})
  elif eid=='2026-rs-federais':
   old=repo.read('data/rs/editorial-baseline.json');current=repo.read('data/rs/editorial.json');cid=m['candidate_id']
   if cid in old:
    changed=old[cid]!=current.get(cid)
    row['variants'].append({'role':'pre_review_baseline','ref':repo.observation('data/rs/editorial-baseline.json','/'+cid)['ref'],
     'changed_in_later_review':changed,'decision':'do_not_reinstate_superseded_assertions_without_individual_review' if changed else 'same_content_preserved',
     'current_ref':repo.observation('data/rs/editorial.json','/'+cid)['ref'] if cid in current else None})
  elif eid.startswith('2026-pr-'):
   current=repo.read('data/pr/editorial.json');cid=m['candidate_id']
   if cid in current:row['variants'].append({'role':'editorial_source','ref':repo.observation('data/pr/editorial.json','/'+cid)['ref'],'decision':'preserve_summary_sources_and_documented_locality'})
  else:
   p,f,_,records=repo.records(e);i=next(i for i,x in enumerate(records) if str(x['id'])==m['candidate_id'])
   row['variants'].append({'role':'reviewed_public_export','ref':repo.observation(p,f'/{f}/{i}')['ref'],'decision':'preserve_typed_claims_or_sourced_summary_without_new_synthesis'})
  rows.append(row)
 return rows

def copy_dependencies(root,out,pages,protected=()):
 """Copy public page dependencies only, not raw research archives or fonts."""
 queue=list(pages);seen=set()
 while queue:
  p=queue.pop()
  if p in seen:continue
  seen.add(p);source=(root/p).resolve()
  if not source.is_relative_to(root.resolve()) or not source.is_file():continue
  if source.suffix.lower() in ('.woff','.woff2','.otf','.ttf'):continue
  dest=out/p;dest.parent.mkdir(parents=True,exist_ok=True)
  if p not in protected:shutil.copyfile(source,dest)
  if source.suffix not in ('.html','.css','.js'):continue
  raw=source.read_text(encoding='utf-8');refs=[]
  if source.suffix=='.html':
   s=BeautifulSoup(raw,'html.parser')
   refs=[n.get(a) for a in ('src','href','poster') for n in s.select('['+a+']')]
  refs+=re.findall(r'url\([\'\"]?([^\)\'\"]+)',raw)
  for ref in refs:
   if not ref or ref.startswith(('#','//','data:')):continue
   u=urlsplit(ref)
   if u.scheme:continue
   resolved=posixpath.normpath(posixpath.join(posixpath.dirname(p),unquote(u.path)))
   if resolved.startswith('../') or resolved.startswith('/'):continue
   if (root/resolved).is_dir():resolved=resolved.rstrip('/')+'/index.html'
   if (root/resolved).is_file():queue.append(resolved)
 return sorted(seen)

def build(out, root=ROOT):
 root=Path(root).resolve();out=Path(out).resolve()
 if out==root or out.is_relative_to(root):raise ValueError('Prototype must be outside repository')
 out.mkdir(parents=True,exist_ok=True)
 repo=Repository(root);inventory=[];all_models=[];reconciliation=[];samples=[];inputs={};rendered=[]
 for e in repo.editions():
  doc,models=repo.models(e);labels=topic_labels(root,e);byid={m['candidate_id']:m for m in models}
  blocks=Counter();signatures={}
  for card in doc.select('article.candidate'):
   cid=card['id'].removeprefix('candidato-');signatures[cid]=original_signature(card)
   for node in card.find_all(recursive=False):blocks[' '.join(node.get('class',[])) or node.name]+=1
   enhance_card(card,byid[cid],labels)
   after=original_signature(card);after['attrs'].pop('data-canonical-card',None)
   if signatures[cid]!=after:raise AssertionError('Original card changed')
  # This banner cannot be confused with a new electoral update.
  banner=added('<aside class="cc-prototype-note"><strong>Protótipo editorial · D2/D3</strong> — fontes e datas da pesquisa original, sem nova atualização eleitoral. <a href="'+posixpath.relpath('prototipo.html',posixpath.dirname(e['entrypoint']))+'">Ver os casos de revisão</a></aside>')
  doc.body.insert(0,banner)
  robots=doc.select_one('meta[name="robots"]')
  if robots:robots['content']='noindex,nofollow'
  else:doc.head.append(doc.new_tag('meta',attrs={'name':'robots','content':'noindex,nofollow'}))
  style=doc.new_tag('link',attrs={'rel':'stylesheet','href':posixpath.relpath('prototype/card.css',posixpath.dirname(e['entrypoint']))});doc.head.append(style)
  script=doc.new_tag('script',attrs={'src':posixpath.relpath('prototype/card.js',posixpath.dirname(e['entrypoint'])),'defer':''});doc.body.append(script)
  dest=out/e['entrypoint'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(str(doc).replace('viewbox=','viewBox='),encoding='utf-8')
  # Round-trip serialization must preserve the original text and links too.
  roundtrip=BeautifulSoup(dest.read_bytes(),'html.parser')
  for c in roundtrip.select('article.candidate'):
   sig=original_signature(c);sig['attrs'].pop('data-canonical-card',None)
   if sig!=signatures[c['id'].removeprefix('candidato-')]:raise AssertionError('Serialization changed source')
  inventory.append({'edition_id':e['edition_id'],'cards':len(models),'current_blocks':dict(blocks),
   'coverage':dict(Counter(m['coverage']['state'] for m in models)),
   'mandate':dict(Counter(m['mandate']['state'] for m in models)),
   'history':dict(Counter(m['history']['state'] for m in models)),
   'evidence_granularity':dict(Counter(v['granularity'] for m in models for v in m['evidence'])),
   'decisions':{'narrative':'preserve_current_readable_prose','career':'move_original_nodes_into_common_disclosure','channels':'move_without_reclassifying_as_verified','sources':'keep_inline_links_and_add_dated_provenance','unknown':'explicit_not_negative','new_global_filters':'not_activated_in_this_prototype'}})
  all_models.extend(models);reconciliation.extend(editorial_variants(repo,e,models));rendered.append(e['entrypoint'])
  # The gallery chooses test coverage, never political merit. Selection is frozen in cases.json.
  cases=json.loads((root/'config/canonical-card-cases.json').read_text())['cases']
  for case in cases:
   if case['edition_id']==e['edition_id']:
    m=byid[case['candidate_id']];samples.append({**case,'name':m['identity']['name'],'path':e['entrypoint']+'#candidato-'+case['candidate_id']})
 for path in repo.cache:inputs[path]=sha((root/path).read_bytes())
 for e in repo.editions():inputs[e['entrypoint']]=sha((root/e['entrypoint']).read_bytes())
 deps=copy_dependencies(root,out,['index.html','sc/index.html','rs/index.html','pr/index.html','sp/index.html',*rendered],protected=rendered)
 runtime=out/'assets/pauta-filters-editorial.js'
 if runtime.exists():
  raw=runtime.read_text();anchor="'.candidate-copy, .candidate-index, .pauta-match, .eef-card-actions'"
  if raw.count(anchor)!=1:raise ValueError('SC search adapter changed; review prototype exclusion')
  runtime.write_text(raw.replace(anchor,"'.candidate-copy, .candidate-index, .pauta-match, .eef-card-actions, .cc-added'"))
 for name in ['card.css','card.js']:
  p=out/'prototype'/name;p.parent.mkdir(exist_ok=True);shutil.copyfile(root/'tools/canonical_cards'/name,p)
 # Supplementary model/decision files are review outputs, not a second public database.
 save(out/'audit/inventory.json',{'schema_version':'1.0.0','baseline':BASE,'editions':inventory})
 save(out/'audit/models.json',all_models);save(out/'audit/editorial-reconciliation.json',reconciliation)
 save(out/'audit/inputs.json',{'baseline':BASE,'files':inputs})
 save(out/'audit/cases.json',samples)
 gallery=''.join('<section><h2>'+html.escape(e['office_label']+' · '+e['state'])+'</h2>'+''.join(f'<p><a href="{html.escape(c["path"],quote=True)}">{html.escape(c["name"])}</a><br><span>{html.escape(c["reason"])}</span></p>' for c in samples if c['edition_id']==e['edition_id'])+'</section>' for e in repo.editions())
 page='''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>Protótipo · Fichas e transparência</title><style>body{background:#f3eee4;color:#272620;margin:0;font:17px/1.6 system-ui,sans-serif}main{max-width:1000px;margin:auto;padding:36px 20px}h1{font:44px/1.1 Georgia,serif}h2{font:24px Georgia,serif}a{color:#803b30}header{border-bottom:2px solid #8c4135;padding-bottom:20px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}section{background:#fffaf1;padding:20px}span{font-size:14px;color:#675b50}a:focus-visible{outline:3px solid #8c4135}@media(max-width:640px){.grid{grid-template-columns:1fr}h1{font-size:34px}}</style></head><body><main><header><p>ESQUERDA EM FOCO · LABORATÓRIO EDITORIAL</p><h1>A narrativa primeiro.<br>A origem ao alcance.</h1><p>Protótipo das issues #54 e #55. Os textos e as referências já publicados foram preservados. A nova organização permite ler o contexto, examinar a evidência e entender o que a pesquisa ainda não confirmou.</p><p>Os casos abaixo foram escolhidos para testar estruturas e lacunas, não para recomendar candidaturas. As seis páginas completas estão no pacote; nenhuma delas foi publicada como atualização do site.</p></header><div class="grid">'''+gallery+'</div></main></body></html>'
 (out/'prototipo.html').write_text(page,encoding='utf-8')
 (out/'robots.txt').write_text('User-agent: *\nDisallow: /\n')
 result={'baseline':BASE,'public_files_modified':False,'editions':len(inventory),'cards':len(all_models),'case_count':len(samples),
  'prose_and_original_links_preserved':True,'models_sha256':sha((out/'audit/models.json').read_bytes()),
  'inventory_sha256':sha((out/'audit/inventory.json').read_bytes()),'reconciliation_sha256':sha((out/'audit/editorial-reconciliation.json').read_bytes()),'inputs':len(inputs)}
 save(out/'audit/build.json',result);return result

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);args=p.parse_args();print(json.dumps(build(args.out),ensure_ascii=False))

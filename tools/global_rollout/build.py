"""Production integration of D1 and D2/D3, without regenerating research.
The original card is reversibly decorated. Every run removes its prior generated
layer and reads the current JSON sources; no stale-provenance fast path.
"""
from __future__ import annotations
import argparse, copy, importlib.util, json, posixpath, shutil, sys
from collections import Counter
from pathlib import Path
from bs4 import BeautifulSoup, Comment
from projection import ROOT, BASE, Repository, load, save, legacy_contract, projection
sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import sha
from render import enhance_card, original_signature as _original_signature
_spec=importlib.util.spec_from_file_location('query_markup_v1',ROOT/'tools/global04/query_build.py')
_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old)

def original_signature(card):
 clone=BeautifulSoup(str(card),'html.parser').article
 for marker in list(clone.find_all(string=lambda n:isinstance(n,Comment))):
  if str(marker).startswith('cq-slot:'):marker.extract()
 return _original_signature(clone)

ASSETS=['assets/global/rollout-core.js','assets/global/rollout.js','assets/global/canonical-card.js','assets/global/rollout.css','assets/global/canonical-card.css']

def strip_card(card):
 """Undo only this generator's ownership markers, restoring original DOM order."""
 if not card.get('data-canonical-card'):return
 slots={str(n):n for n in card.find_all(string=lambda n:isinstance(n,Comment)) if str(n).startswith('cq-slot:')}
 for node in list(card.select('[data-cq-origin]')):
  key='cq-slot:'+node['data-cq-origin'];marker=slots.get(key)
  if marker is None:raise ValueError('Missing original DOM position '+key)
  marker.replace_with(node.extract());del node['data-cq-origin']
 for node in list(card.select('.cc-added')):node.decompose()
 for node in list(card.select('.cc-wrapper')):node.unwrap()
 card['class']=[c for c in card.get('class',[]) if c!='cc-card'];card.attrs.pop('data-canonical-card',None)

def slots(card):
 # All original direct children, and the channels node that is moved from inside,
 # receive reversible slots. Unmoved nodes are harmless and reset identically.
 nodes=list(card.find_all(recursive=False))
 channels=card.select_one('.candidate-links')
 if channels is not None and all(channels is not n for n in nodes):nodes.append(channels)
 for i,n in enumerate(nodes):n.insert_before(Comment('cq-slot:'+str(i)));n['data-cq-origin']=str(i)

def markup(soup,cfg):
 def el(tag,text=None,**attrs):
  n=soup.new_tag(tag,attrs=attrs)
  if text is not None:n.string=text
  return n
 tools=el('section',id='eefQueryTools',**{'class':'cq-tools','data-global-rollout':'tools','hidden':'','aria-label':'Consulta global de candidaturas'})
 details=el('details',id='cqPanel',**{'class':'cq-panel'});tools.append(details)
 summ=el('summary');summ.append(el('span','Filtrar candidaturas'));summ.append(el('span','Busca, partidos e evidências',id='cqPanelCount',**{'class':'cq-muted'}));details.append(summ)
 body=el('div',**{'class':'cq-body'});details.append(body)
 parties=el('fieldset',**{'class':'cq-parties'});parties.append(el('legend','Partidos'));body.append(parties)
 parties.append(el('p','Escolha um ou mais. A busca inclui fichas de qualquer partido marcado.',**{'class':'cq-help'}))
 row=el('div',**{'class':'cq-chip-row'})
 counts=Counter(r['party'] for r in cfg['records'])
 for party in cfg['parties']:
  b=el('button',type='button',**{'data-cq-party':party,'aria-pressed':'false','class':'cq-chip'});b.append('PCdoB' if party=='PCDOB' else party);b.append(el('small',str(counts[party])));row.append(b)
 parties.append(row);parties.append(el('button','Todos os partidos',type='button',id='cqClearParties',**{'class':'eef-button','disabled':''}))
 themes=el('fieldset',**{'class':'cq-themes'});themes.append(el('legend','Temas e evidências'));body.append(themes)
 label=el('label','Tipo de informação ao filtrar por tema',**{'for':'cqScope'});themes.append(label)
 select=el('select',id='cqScope')
 for value,text in [('documented_topic','Posições e atuação documentadas'),('current_support','Apoios e prioridades atuais documentados'),('legacy_context','Contexto temático da pesquisa')]:select.append(el('option',text,value=value))
 themes.append(select);themes.append(el('p',id='cqScopeHint',**{'class':'cq-help','role':'status'}))
 themes.append(el('button','Ver os vínculos de contexto desta edição',type='button',id='cqContextShortcut',hidden=''))
 mode=el('fieldset',**{'class':'cq-mode'});mode.append(el('legend','Ao selecionar mais de um tema ou grupo'))
 for value,text in [('any','Qualquer um'),('all','Todos')]:
  lab=el('label');lab.append(el('input',type='radio',name='cq-mode',value=value,**({'checked':''} if value=='any' else {})));lab.append(text);mode.append(lab)
 themes.append(mode)
 themes.append(el('p','Um grupo inclui qualquer tema dentro dele. “Todos” combina os grupos e temas escolhidos, não exige cada subtema do grupo.',**{'class':'cq-help'}))
 themes.append(el('p','Os totais abaixo contam fichas neste tipo de evidência, antes dos outros filtros.',**{'class':'cq-help'}))
 group_host=el('div',id='cqGroups',**{'class':'cq-groups'});themes.append(group_host)
 bytopic={t['id']:t for t in cfg['topics']}
 for g in cfg['groups']:
  group=el('details',**{'class':'cq-group','data-cq-disclosure':g['id']});group_host.append(group)
  title=el('summary');title.append(g['label']);title.append(el('small',**{'data-cq-group-count':g['id']}));group.append(title)
  inside=el('div',**{'class':'cq-group-body'});group.append(inside)
  inside.append(el('button','Selecionar este grupo',type='button',**{'data-cq-group':g['id'],'aria-pressed':'false','class':'cq-group-button'}))
  for topic in g['members']:
   t=bytopic[topic];button=el('button',type='button',**{'data-cq-topic':topic,'aria-pressed':'false','class':'cq-topic'})
   button.append(el('span',t['label']));button.append(el('small',**{'data-cq-topic-count':topic}));inside.append(button)
   # Definitions are available as context, not exposed as a keyword classifier.
   description=t.get('includes') or t.get('definition',{}).get('includes') if isinstance(t.get('definition',{}),dict) else None
   if description:
    definition=el('details',**{'class':'cq-definition'});definition.append(el('summary','O que este tema reúne?'));definition.append(el('p',str(description)))
    if t.get('excludes'):definition.append(el('p','Limite: '+t['excludes']))
    inside.append(definition)
 advanced=el('details',**{'class':'cq-advanced'});advanced.append(el('summary','Registro, mandato e trajetória'));body.append(advanced)
 fields=el('div',**{'class':'cq-fields'});advanced.append(fields)
 names={'registration':'Situação do registro','aptitude':'Aptidão no cadastro','mandate':'Informação de mandato','history':'Histórico eleitoral','region':'Localidade com atuação documentada'}
 for dim in cfg['dimensions']:
  holder=el('div',**{'class':'cq-field'});fields.append(holder);holder.append(el('label',names[dim['id']],**{'for':'cq-'+dim['id']}))
  choices=el('select',id='cq-'+dim['id'],**{'data-cq-field':dim['id']});choices.append(el('option','Todas as fichas',value=''));holder.append(choices)
  for option in dim['options']:choices.append(el('option',option['label'],value=option['value']))
  if dim['state']!='ready':choices['disabled']='';holder.append(el('p',dim['reason'],**{'class':'cq-help'}))
 order=el('div',**{'class':'cq-field'});order.append(el('label','Ordenação',**{'for':'cq-order'}));select=el('select',id='cq-order',**{'data-cq-field':'order'})
 select.append(el('option','Rotação diária, sem ranking',value='daily'));select.append(el('option','Ordem alfabética',value='alphabetical'));order.append(select);fields.append(order)
 controls=el('div',**{'class':'cq-actions'});tools.append(controls)
 controls.append(el('p','Todas as fichas estão disponíveis.',id='eefQuerySummary',**{'role':'status','aria-live':'polite'}))
 controls.append(el('button','Compartilhar consulta',type='button',id='eefShareQuery',**{'class':'eef-button','disabled':''}))
 controls.append(el('button','Limpar consulta',type='button',id='eefQueryClear',**{'class':'eef-button','disabled':''}))
 tools.append(el('div',id='cqActive',**{'class':'cq-active','aria-label':'Filtros ativos'}))
 tools.append(el('p',id='eefQueryNotice',hidden='',**{'role':'status','aria-live':'polite','class':'cq-notice'}))
 return tools

def prepare_legacy(root):
 p=root/'config/rollout-legacy.json'
 if p.exists():return load(p)
 registry=load(root/'config/editions.json');out={}
 for e in registry['editions']:
  if e['publication_status']=='published':out[e['edition_id']]=legacy_contract(root,e,BeautifulSoup((root/e['entrypoint']).read_bytes(),'html.parser'))
 data={'baseline':BASE,'version':'1.0.0','editions':out};save(p,data);return data

def enhance(root,e,repo,legacy):
 path=root/e['entrypoint'];soup=BeautifulSoup(path.read_bytes(),'html.parser')
 for c in soup.select('article.candidate'):strip_card(c)
 # Repository models read the same source records, while the cleaned DOM provides
 # the narrative currently in this page, not a frozen prototype snapshot.
 data_path,field,dataset,records=repo.records(e);cards={c['id'].removeprefix('candidato-'):c for c in soup.select('article.candidate')}
 if set(cards)!={str(r.get('id',r.get('candidate_id'))) for r in records}:raise ValueError('Raw/HTML candidacy catalogue mismatch '+e['edition_id'])
 models=[repo.adapt(e,r,i,data_path,field,dataset,cards[str(r.get('id',r.get('candidate_id')))]) for i,r in enumerate(records)]
 cfg,ledger,rejections=projection(root,e,soup,models,repo,legacy)
 # Before any mutation, record the exact original text/link multiset and identity.
 before={cid:original_signature(c) for cid,c in cards.items()}
 namespace={'SC':'sc-v1','SP':'sp-product-v1','RS':'rs-v1','PR':'pr-v1'}[e['state']]
 native=next(c for c in load(root/'config/taxonomies.json')['catalogs'] if c['namespace']==namespace)
 labels={c['source_id']:c['label'] for c in native['concepts']}
 for m in models:slots(cards[m['candidate_id']]);enhance_card(cards[m['candidate_id']],m,labels)
 # Disable old filter runtimes rather than letting two controllers compete.
 for n in list(soup.select('script')):
  if n.get('type') in ('application/ld+json','application/json'):continue
  src=n.get('src','').split('?')[0]
  allowed=('assets/global/core.js','assets/selecionados-core.js','assets/global/selection-adapter.js','assets/global/selection.js','assets/global/navigation.js')
  if src and any(src.endswith(x) for x in allowed):continue
  n.decompose()
 # New data and controls are regenerated; native card disclosures/links are intact.
 selectors='[data-global-rollout],[data-global04-query],#eefEditionQueryData,#eefQueryTools,#eefQueryShareDialog,#cqData,#pautaPanel,#pautaDialog,#pautaToolbar,#pautaEmpty,.state-filters,.pr-filters,#filterDetails'
 for n in list(soup.select(selectors)):
  if n.parent is not None and not n.find_parent('article',class_='candidate'):n.decompose()
 for n in list(soup.select('link[rel="stylesheet"]')):
  if 'rollout' in n.get('href','') or 'canonical-card' in n.get('href',''):n.decompose()
 search=soup.select_one('#searchInput');search['maxlength']='2048';search['placeholder']='Nome, número, partido ou palavras presentes na ficha…'
 container=search.find_parent(id='searchBar') or search.find_parent(class_='toolbar-wrap')
 if container is None:raise ValueError('Search container missing')
 container.insert_after(markup(soup,cfg));soup.body.append(_old.dialog_markup(soup))
 if not soup.select_one('#eefDeepLinkNotice'):
  notice=BeautifulSoup('<div id="eefDeepLinkNotice" class="eef-sp-deeplink-notice" hidden><p id="eefDeepLinkMessage" role="status" aria-live="polite"></p><button id="eefRestoreQuery" type="button">Restaurar minha consulta</button></div>','html.parser').div
  soup.select_one('#eefQueryTools').insert_after(notice)
 for n in soup.select('.rail-note'):
  n.string='Partidos e fichas podem ser vistos em ordem alfabética ou rotação diária. Nenhuma ordem é recomendação.'
 # Preserve old control anchors as destinations without a second interactive UI.
 for old_id in ('pautaPanel','pautaToolbar','pautaDialog','filterDetails'):
  if not soup.find(id=old_id):
   alias=soup.new_tag('span',attrs={'id':old_id,'data-global-rollout':'anchor','class':'cq-anchor'});soup.select_one('#eefQueryTools').append(alias)
 runtime=soup.new_tag('script',attrs={'type':'application/json','id':'cqData','data-global-rollout':'data'})
 runtime.string=json.dumps(cfg,ensure_ascii=False,separators=(',',':')).replace('</','<\\/');soup.body.append(runtime)
 for asset in ASSETS:
  href=posixpath.relpath(asset,posixpath.dirname(e['entrypoint']))+'?v='+sha((root/asset).read_bytes())[:12]
  node=soup.new_tag('link',attrs={'rel':'stylesheet','href':href,'data-global-rollout':'asset'}) if asset.endswith('.css') else soup.new_tag('script',attrs={'src':href,'defer':'','data-global-rollout':'asset'})
  (soup.head if asset.endswith('.css') else soup.body).append(node)
 # The shared selection controller is deliberately loaded after the query adapter.
 selection=soup.select_one('script[src*="assets/global/selection.js"]')
 if selection:soup.body.append(selection.extract())
 if not soup.select_one('#emptyResults'):
  empty=BeautifulSoup('<p id="emptyResults" class="cq-empty" hidden>Nenhuma ficha corresponde aos critérios. Retire um filtro ou use outro tipo de evidência. Não localizar uma associação não significa oposição ao tema.</p>','html.parser').p
  soup.select_one('#candidaturas').insert(0,empty)
 result=str(BeautifulSoup(str(soup),'html.parser')).replace('viewbox=','viewBox=')
 roundtrip=BeautifulSoup(result,'html.parser')
 for c in roundtrip.select('article.candidate'):
  sig=original_signature(c);sig['attrs'].pop('data-canonical-card',None)
  if sig!=before[c['id'].removeprefix('candidato-')]:raise ValueError('Card preservation failed '+c['id'])
 if roundtrip.select('.cc-prototype-note') or any('noindex' in n.get('content','') for n in roundtrip.select('meta[name="robots"]')):raise ValueError('Prototype configuration cannot be deployed')
 path.write_text(result,encoding='utf-8')
 return cfg,ledger,rejections

def build(root=ROOT,edition=None,metadata=True):
 root=Path(root);legacy=prepare_legacy(root);registry=load(root/'config/editions.json');repo=Repository(root)
 # Sources of these assets are shared with the validated prototype, not copied HTML.
 for source,dest in [('tools/canonical_cards/card.css','assets/global/canonical-card.css'),('tools/canonical_cards/card.js','assets/global/canonical-card.js')]:
  raw=(root/source).read_text()
  if dest.endswith('.css'):raw+='\n/* Root filtering must override the legacy article display rule. */\narticle.cc-card[hidden]{display:none!important}\n'
  (root/dest).write_text(raw)
 reports=[];ledger=[];rejected=[]
 for e in registry['editions']:
  if e['publication_status']!='published' or (edition and e['edition_id']!=edition):continue
  cfg,entries,blocked=enhance(root,e,repo,legacy['editions'][e['edition_id']]);ledger+=entries;rejected+=blocked
  reports.append({'edition_id':e['edition_id'],'cards':len(cfg['records']),'available':cfg['available'],'dimensions':cfg['dimensions'],'projection_count':len(entries),'blocked_associations':len(blocked)})
  if metadata:
   for feature in ('canonical_filters','canonical_card','visible_provenance','global_query_v2','theme_any_all','neutral_order'):
    e['capabilities'][feature]={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04D4'}
   e['migration']['canonical_rollout']='1.0.0'
 if not reports:raise ValueError('Unknown or unpublished edition')
 if metadata:
  save(root/'config/editions.json',registry)
  save(root/'data/global-rollout/status.json',{'schema_version':'1.0.0','baseline':BASE,'issue':56,'publication':'requires_verified_release_not_implied_by_build','editions':reports,'research_refetched':False,'issue50_implemented':False})
  save(root/'data/global-rollout/projection.json',{'baseline':BASE,'evidence':ledger,'blocked':rejected,'no_keyword_classification':True})
  sourcehashes={p:sha((root/p).read_bytes()) for p in repo.cache}
  save(root/'data/global-rollout/source-hashes.json',{'baseline':BASE,'json_sources':sourcehashes})
  migration=load(root/'data/global-integration/migration-status.json')
  migration['canonical_rollout']={'version':'1.0.0','issue':56,'baseline':BASE,'publication':'requires_verified_release_not_implied_by_build','editions':reports,'completed_scope':'production_implementation','issue50_implemented':False}
  save(root/'data/global-integration/migration-status.json',migration)
 return reports

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--edition');p.add_argument('--no-metadata',action='store_true');a=p.parse_args()
 print(json.dumps(build(edition=a.edition,metadata=not a.no_metadata),ensure_ascii=False))

"""Build #53 design contracts from pinned repository sources. No public UI writes.
Usage: python tools/global_filters/build.py [--check]
Only GENERATED outputs and one additive migration-status section are owned here.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,re,sys
from collections import Counter,defaultdict
from pathlib import Path
from bs4 import BeautifulSoup
from decisions import BASE,VERSION,EXTENSIONS,RS,PR,REJECTED,GROUPS,RUNTIMES,DATASETS
ROOT=Path(__file__).resolve().parents[2]
GENERATED=('config/global-filter-taxonomy.json','data/global-integration/filter-crosswalk.json',
 'data/global-integration/filter-capabilities.json','data/global-integration/filter-inputs.json',
 'docs/GLOBAL-FILTER-CROSSWALK.md')
STATUS='data/global-integration/migration-status.json'
def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def sha(path):return hashlib.sha256((ROOT/path).read_bytes()).hexdigest()
def encode(data):return json.dumps(data,ensure_ascii=False,indent=2,sort_keys=False)+'\n'
def ref(path,pointer=''):
 return {'path':path,'commit':BASE,'sha256':sha(path),'pointer':pointer}
def requirements():
 return {
  'scope':'contract_only_not_loaded_by_public_pages','baseline':BASE,'issue':53,
  'common_interface':['query','parties','themes','registration','mandate','history','locality','order'],
  'semantics':[
   {'id':'current_support','label':'Apoios e prioridades documentados em 2026','requires':['individual_attribution','reviewed_positive_direction','explicit_current_context','specific_object','source_locator'],'excludes':['opposition_as_support','mere_activity','party_inference','consultation_date_as_event_date'],'period_policy':'Current context must be explicitly reviewed for this election; reaffirmation has its own source.'},
   {'id':'documented_topic','label':'Posições e atuação documentadas','requires':['individual_attribution','reviewed_topic_link','specific_object','source_locator'],'excludes':['topic_as_agreement','all_sources_for_every_claim'],'period_policy':'Show actual period; historical and undated are not current by default.'},
   {'id':'legacy_context','label':'Contexto temático da pesquisa','requires':['existing_individual_link','original_source'],'excludes':['automatic_upgrade_to_current_support','automatic_upgrade_to_claim_level_documented_topic'],'period_policy':'Missing nature/time stays explicit; old is not implied by the word legacy.'}],
  'view_policy':{'heading':'Temas e evidências','default_target':'documented_topic','current_support_is_positive_subset':True,
     'existing_views_preserved_until_rollout':True,'mixed_semantics_never_hidden':True,
     'legacy_context_separate_labeled_lane':True,'absence_is_not_opposition':True},
  'operators':{'across_dimensions':'all','between_parties':'any','between_themes':['any','all'],
     'new_theme_default':'any','PR_v1_import_default':'all','inside_group':'any',
     'group_is_navigation_not_evidence':True,'remove_redundant_parent_when_all':True,
     'counts':'distinct edition_id:candidate_id; never evidence count or all people in Brazil',
     'inactive_theme_counts':'unfiltered edition universe labeled; result count is full current query',
     'empty_selection':'no restriction','contradictory_metadata':'reported; never coerced to absent'},
  'activation':{'data':['ready','partial','absent','not_applicable'],
     'implementation':['active_local','migration_required','contract_only','not_applicable'],
     'blockers':['publication','field_missing','field_semantics','claim_review','implementation'],
     'zero_results_not_same_as_unavailable':True,'show_unavailable_reason_without_blocking_reading':True},
  'mandate_policy':{'states':['institutional_record','exercise_verified','declared_only','verified_not_exercising','not_confirmed'],
     'legacy_false':'not_confirmed, never proof of no mandate','institutional_listing_not_all_leave_statuses':True,
     'independent_of_history':True,'migration_SC_exclusive_control':'replace with independent dimensions only after adapter validation'},
  'history_policy':{'states':['linked_prior_race','no_prior_in_covered_snapshot','not_established'],
     'exclude_current_election_when_testing_prior':True,'missing_history_not_first_election':True,
     'vote_states':['verified_nominal','not_verified','not_collected','not_applicable','not_yet_held'],
     'zero_requires_verified_numeric_zero':True},
  'registration_policy':{'separate_dimensions':['decision_status','appeal_status','aptitude_at_snapshot'],
     'keep_original_labels_and_date':True,'no_aptitude_inference_from_decision':True,
     'unknown_not_inapt':True,'mixed_source_conflicts':'show source-specific values and flag; do not silently choose'},
  'locality_policy':{'label':'Localidade com atuação documentada','not_residence_or_electoral_base':True,'requires':['explicit_place','activity_source'],'optional_when_documented':True},
  'order_policy':{'global_target':['daily','alphabetical'],'timezone':'America/Sao_Paulo',
     'new_default':'daily','preserve_local_daily_epoch_until_explicit_migration':True,
     'filtering_never_changes_ranking':True,'never_sort_by':['evidence_quantity','topic_matches','popularity','affinity']},
  'explanation':{'minimum':['edition_id','candidate_id','source_concept_id','canonical_topic_id','matched_original_scope','claim_id_or_legacy_locator','source_id_or_url','direction','nature','period','limitations'],
     'unknown_values':'explicit null + reason, not invented metadata','phrase_template':'Aparece por {objeto ou trecho}, documentado em {fonte}; {natureza}, {periodo ou lacuna}.',
     'no_generic_support_to_group':True,'context_expandable':True,'needs_no_javascript_for_sources':True},
  'identity':{'edition':'election_year + UF + office','candidate':'edition_id:candidate_id','not_global_person_identity':True,'never_join_by_name':True},
  'transport':{'current_v1':'unchanged; old queries and collections remain in their original edition and semantic lane',
     'future_global_query_version':2,'future_required':['edition_id','taxonomy_version','scope','selectors','operators'],
     'no_silent_v1_reinterpretation':True,'share_explicit_only':True,'cross_edition_collection_issue':50,
     'issue50_excluded':True},
  'crosswalk_relations':{'equivalent':'Compared explicit definitions have the same scope; not candidate evidence.',
     'related':'Bounded/overlapping topic correspondence with native scope kept; not identical assertions.',
     'specific':'A donor-specific domain retained in the global vocabulary.',
     'not_comparable':'Rejected shortcut; other independently sourced links may exist.',
     'review_required':'No automatic conversion; original statement must resolve the scope.'}}

def source_usage():
 out=defaultdict(list)
 # SC audit describes ALL reviewed associations, not only those admitted to support.
 for i,a in enumerate(load('data/sc-semantic-v2/association-audit.json')['associations']):
  out['sc-v1:'+a['family_id']].append({'candidate_id':a['candidate_id'],'path':'data/sc-semantic-v2/association-audit.json','pointer':f'/associations/{i}',
   'scope':a['original_target'],'source_ids_or_urls':a['source_ids'],'direction':a.get('original_direction'),
   'period':a.get('original_period'),'locator':a.get('rationale_and_locator'),'active_membership':a.get('eligible_v2',False)})
 for eid,(path,key) in DATASETS.items():
  if eid.startswith('2026-sc-'):continue
  rows=load(path)[key];ns='rs-v1' if '-rs-' in eid else 'pr-v1' if '-pr-' in eid else 'sp-product-v1'
  field='topics' if ns=='rs-v1' else 'themes' if ns=='pr-v1' else 'themes_2026'
  for i,c in enumerate(rows):
   for j,t in enumerate(c.get(field,[])):
    src=t.get('sources',t.get('source_ids',[t.get('evidence_url')]))
    out[ns+':'+t['id']].append({'candidate_id':c['id'],'edition_id':eid,'path':path,'pointer':f'/{key}/{i}/{field}/{j}',
       'scope':t.get('summary',t.get('label',t['id'])),'source_ids_or_urls':[x for x in src if x],
       'direction':None,'period':None,'locator':None,'active_membership':ns!='rs-v1',
       'metadata_note':'Null here means not present on the theme link itself; related claims/sources must be inspected, not discarded.'})
 return out

def build_crosswalk(cats):
 maps={}
 for ns,text in [('rs-v1',RS),('pr-v1',PR)]:
  for line in text.splitlines():
   sid,target,relation,extent,reason=line.split('|',4);maps[ns+':'+sid]=(target,relation,extent,reason)
 usage=source_usage();rows=[]
 for cat in cats:
  ns=cat['namespace']
  for i,c in enumerate(cat['concepts']):
   ident=c['id'];native=c['source_id']
   if ns=='sc-v1':decision=(native,'equivalent','same','Definição explícita SC adotada como domínio compartilhado; inclui e exclui preservados.')
   elif ns=='sp-product-v1' and native!='ciencia-tecnologia-inovacao':decision=(native,'equivalent','same','Inclusões/exclusões SP comparadas às da base SC: idênticas; igualdade de domínio não iguala natureza/tempo das evidências.')
   elif ns=='sp-product-v1':decision=(native,'specific','same','Extensão explícita de ciência, tecnologia e inovação de SP incorporada; formação profissional não comprova pauta.')
   else:decision=maps[ident]
   target,relation,extent,reason=decision;u=usage.get(ident,[])
   rows.append({'source_concept_id':ident,'source_label':c['label'],'target_concept_id':target,
     'relation':relation,'scope_relation':extent,'decision':'accepted_for_design','reason':reason,
     'definition_basis':'explicit_definition' if 'includes' in c['definition'] else 'bounded_label_with_individual_source_links',
     'source':ref(cat['source'],f'/topics/{i}' if ns=='sc-v1' else f'/taxonomy/{i}' if ns=='sp-product-v1' else '/topics/'+native if ns=='rs-v1' else '/themes/'+native),
     'source_definition':c['definition'],'native_scope_required':True,'automatic_candidate_mapping':False,
     'activation_requirement':'individual_object_review' if extent=='overlap' else 'reviewed_individual_evidence_and_lane_preservation',
     'usage':{'associations':len(u),'distinct_candidate_keys':len({(v.get('edition_id','2026-sc-federais'),v['candidate_id']) for v in u}),
        'filter_member_keys_at_baseline':None if ns=='rs-v1' else len({(v.get('edition_id','2026-sc-federais'),v['candidate_id']) for v in u if v['active_membership']}),
        'examples':u[:3],'examples_policy':'first three source-order records; technical locators, not recommendations'}})
 aliases=[]
 for cat in cats:
  for old,new in cat.get('legacy_aliases',{}).items():
   aliases.append({'namespace':cat['namespace'],'old_id':old,'target_source_id':new,'kind':'declared_id_alias','changes_evidence':False,'source':ref(cat['source'],'/provenance/topic_id_migration')})
 return {'schema_version':VERSION,'baseline':BASE,'issue':53,'ui_active':False,'scope':'concept_design_not_candidate_reclassification',
     'entries':rows,'aliases':aliases,'rejected_or_review_required':[{'source_concept_id':s,'target_concept_id':t,'relation':rel,'reason':why,'automatic_candidate_mapping':False} for s,t,rel,why in REJECTED],
     'legacy_group_queries':[{'source_namespace':'sc-macro-v2','source_id':g['id'],'label':g['label'],
       'frozen_any_of_topics':g['family_ids'],'source':ref('data/sc-semantic-v2/macrogroups.json',f'/groups/{i}'),
       'rule':'One original group remains one OR-clause, even inside an ALL query; never substitute an expanded new group.',
       'automatic_expansion':False} for i,g in enumerate(load('data/sc-semantic-v2/macrogroups.json')['groups'])],
     'summary':{'source_entries':len(rows),'relations':dict(Counter(x['relation'] for x in rows))}}

def facts(e):
 eid=e['edition_id'];path,key=DATASETS[eid];rows=load(path)[key]
 s=BeautifulSoup((ROOT/e['entrypoint']).read_text(),'html.parser');cards=s.select('article.candidate')
 f={'records':len(rows),'cards':len(cards),'sources':[ref(path,'/'+key),ref(e['entrypoint'])],
    'party_count':len({c['party'] for c in rows}),
    'prior_history_records':sum(any(str(h.get('year','')).isdigit() and int(h['year'])<e['election_year'] for h in c.get('history',[])) for c in rows),
    'mandate_object_with_source':sum(bool((c.get('current_office') or c.get('current_role_observation') or {}).get('source')) for c in rows),
    'locality_object_with_source':sum(bool((c.get('region') or {}).get('source')) for c in rows),
    'history_not_collected_explicit':sum(c.get('history_state')=='not_collected_for_scope_addition' for c in rows),
    'status_fields':sorted({k for c in rows for k in ['status','status_id','registration_status','registration_group','apt_api','status_api','status_group'] if k in c}),
    'selectors':{n['id']:[{'value':o.get('value',o.get_text()),'label':o.get_text()} for o in n.select('option')] for n in s.select('select[id]')},
    'meaning':'Counts of available fields, not current political research or comparable scores.'}
 if eid=='2026-sc-federais':
  f['prior_history_records']=None
  f['mandate_object_with_source']=None
  f['history_not_collected_explicit']=None
  f['mandate_dom_true']=sum(c.get('data-current-office')=='true' for c in cards)
  f['prior_history_dom_false_rookie']=sum(c.get('data-rookie')=='false' for c in cards)
  f['structured_source_note']='Career/registration presentation lives in HTML; DOM flags alone do not verify exercise or absent mandate.'
 if not any('region' in c for c in rows):f['locality_object_with_source']=None
 if eid=='2026-sc-estaduais':
  f['mandate_object_with_source']=None
  f['institutional_mandate_records']=sum(c.get('mandate_documented') is True and bool(c.get('mandate_source')) for c in rows)
 f['documented_topics_records']=sum(bool(c.get('themes_2026',c.get('themes',c.get('topics')))) for c in rows) if not eid.startswith('2026-sc-') else None
 return f

def capabilities(reg):
 result=[]
 for e in reg['editions']:
  eid=e['edition_id']
  if e['publication_status']!='published':
   result.append({'edition_id':eid,'publication_status':e['publication_status'],'facts':None,
      'dimensions':[],'blockers':['publication'],'note':'No active UI inferred from a branch or the state hub; independent release gates.'});continue
  f=facts(e);runtime,semantic,modes,orders=RUNTIMES[eid];dims=[]
  def add(id,data,active,blocker,note):dims.append({'id':id,'data_readiness':data,'current_implementation':'active_local' if active else 'migration_required',
      'target':'common_global_dimension','blockers':blocker,'reason':note,'evidence':[ref(runtime),*f['sources']]})
  for id in ['query','parties']:add(id,'ready',True,[],'Contrato comum já ativo; manter termos normalizados e OU entre partidos, sem classificação de pauta por texto.')
  add('themes','partial' if semantic else 'partial' if eid=='2026-rs-federais' else 'absent',bool(semantic),
    ['claim_review','implementation'] if eid!='2026-sc-federais' else ['implementation'],
    'RS possui vínculos documentais, mas faltam claims tipificados para ativar o novo filtro.' if eid=='2026-rs-federais' else 'SC Estadual tem sínteses, não matriz temática individual revisada.' if eid=='2026-sc-estaduais' else 'Preservar '+str(semantic)+'; mover domínio não promove evidência nem preenche período.')
  add('registration','partial' if eid=='2026-sc-federais' else 'ready',bool(f['selectors'].get('registrationFilter') or f['selectors'].get('statusFilter')),
     ['field_semantics','implementation'],'Separar decisão, recurso e aptidão; RS possui status estruturado, não faltam todos os dados. SC Federal requer adapter de sua apresentação e fonte.')
  add('mandate','partial',bool(f['selectors'].get('mandateFilter') or f['selectors'].get('trajectoryFilter')),
     ['field_semantics','implementation'],'Campos documentados já existem em SC Estadual, RS, PR e SP. Null/false não significa ausência; registro institucional não prova todas as licenças.')
  add('history','partial' if eid in ['2026-sc-federais','2026-sp-federais'] else 'ready',bool(f['selectors'].get('historyFilter') or f['selectors'].get('trajectoryFilter')),
     ['field_semantics','implementation'],'Filtrar apenas pleitos anteriores, sem converter não coletado em estreante. SP tem 15 registros com coleta histórica não realizada nesta versão.' if eid=='2026-sp-federais' else 'Dados/histórico já disponíveis; separar falta de UI de falta de dados e preservar votos nulos/zero/não aplicável.')
  add('locality','partial' if f['locality_object_with_source'] else 'absent',bool(f['selectors'].get('regionFilter')),
     ['implementation'] if f['locality_object_with_source'] else ['field_missing'],
     'PR tem localidade ligada a uma fonte de atuação; ampliar o componente, não inventar residência ou base eleitoral.')
  add('order','ready',True,[] if len(orders)>1 else ['implementation'],'Ordem alfabética é migração de UI, não bloqueio por falta de pesquisa; conservar regra diária enquanto os links antigos a usarem.')
  dims.append({'id':'theme_operators','data_readiness':'ready' if semantic else 'partial' if eid=='2026-rs-federais' else 'absent',
    'current_implementation':'active_local' if semantic else 'migration_required','target':'common_global_dimension',
    'blockers':['implementation'] if semantic else ['claim_review','implementation'],
    'current':modes,'canonical_target':['any','all'],
    'reason':'OU e E são possíveis sobre vínculos existentes sem criar associações. PR precisa implementação/importação compatível, não novos fatos para adicionar OU.',
    'evidence':[ref(runtime)]})
  result.append({'edition_id':eid,'publication_status':'published','current_semantic':semantic,'current_order':orders,
    'facts':f,'dimensions':dims,'runtime':ref(runtime),'public_changes_in_D1':False})
 return {'schema_version':VERSION,'baseline':BASE,'issue':53,'activation':'design_only','editions':result,
     'no_false_parity':'ready data can still need implementation; partial research does not disable every independent dimension'}

def outputs():
 catalogs=load('config/taxonomies.json')['catalogs'];sc=load('config/topics-v1.json')['topics'];sp=load('sp/deputados-federais/dados.json')['taxonomy']
 topics=[{'id':t['id'],'label':t['label'],'includes':t['includes'],'excludes':t['excludes'],
          'origin_concepts':['sc-v1:'+t['id'],'sp-product-v1:'+t['id']],'synonyms_are_not_classifiers':True} for t in sc]
 sci=next(t for t in sp if t['id']=='ciencia-tecnologia-inovacao')
 topics.append({'id':sci['id'],'label':sci['label'],'includes':sci['includes'],'excludes':sci['excludes'],
     'origin_concepts':['sp-product-v1:'+sci['id']],'synonyms_are_not_classifiers':True})
 for id,label,inc,exc,origin in EXTENSIONS:topics.append({'id':id,'label':label,'includes':inc,'excludes':exc,'origin_concepts':[origin],'synonyms_are_not_classifiers':True})
 taxonomy={'schema_version':VERSION,'taxonomy_version':VERSION,'status':'specified_not_activated','ui_active':False,
    **requirements(),'topics':topics,'groups':[{'id':id,'label':label,'members':members,'membership_rule':'union_of_reviewed_individual_matches_only'} for id,label,members in GROUPS],
    'not_exhaustive':True,'extension_policy':'Never recycle IDs; additions minor, changed meaning major; explicit review and migration. No silently expanded old group queries.'}
 crosswalk=build_crosswalk(catalogs);cap=capabilities(load('config/editions.json'))
 source_paths={'config/taxonomies.json','config/topics-v1.json','data/pr/taxonomy.json','data/rs/topics.json','config/editions.json',
    'data/sc-semantic-v2/association-audit.json','data/sc-semantic-v2/macrogroups.json','data/sc-semantic-v2/source-review.json',
    'assets/sc-federais-filters-v2-data.js','data/sc-federais-topics-v1/matrix.json'}
 source_paths.update(p for p,k in DATASETS.values());source_paths.update(p for p,*_ in RUNTIMES.values());source_paths.update(e['entrypoint'] for e in load('config/editions.json')['editions'] if e['publication_status']=='published')
 inventory={'schema_version':VERSION,'baseline':BASE,'issue':53,'sources':[ref(p) for p in sorted(source_paths)],
    'counts':{'catalog_entries':len(crosswalk['entries']),'canonical_topics':len(topics),'navigation_groups':len(GROUPS),
       'public_editions':sum(e['publication_status']=='published' for e in cap['editions']),'public_cards':sum(e['facts']['cards'] for e in cap['editions'] if e['facts'])},
    'baseline_policy':'A changed input invalidates regeneration until an explicit updated review; no live collection.'}
 md=['# Crosswalk global de filtros — #53','',f'Baseline `{BASE}`. Contrato {VERSION}; **não ativado na interface**.','',
     'As relações abaixo são entre conceitos. Nunca são prova de posição de candidatura. `related` conserva o recorte nativo e não permite distribuir evidências entre assuntos vizinhos.','',
     '| Conceito de origem | Destino global | Relação / escopo | Decisão |','|---|---|---|---|']
 for m in crosswalk['entries']:md.append(f"| `{m['source_concept_id']}` | `{m['target_concept_id']}` | {m['relation']} / {m['scope_relation']} | {m['reason']} |")
 md+=['','## Atalhos rejeitados ou dependentes de revisão individual','']
 for m in crosswalk['rejected_or_review_required']:md.append(f"- `{m['source_concept_id']}` → `{m['target_concept_id']}`: **{m['relation']}**. {m['reason']}")
 md+=['','O JSON `filter-crosswalk.json` inclui fonte, commit, hash, localizador de conceito e exemplos dos vínculos existentes. Exemplos seguem ordem da fonte, não relevância política. `filter-capabilities.json` distingue disponibilidade de dados de trabalho de implementação.','']
 status=load(STATUS);status['canonical_filter_contract']={'issue':53,'version':VERSION,'baseline':BASE,'status':'specified_not_activated',
    'taxonomy':GENERATED[0],'crosswalk':GENERATED[1],'capabilities':GENERATED[2],'inputs':GENERATED[3],
    'next_issues':[54,55,56,57],'not_in_scope':[50],'whole_issue_43_completed':False}
 return {GENERATED[0]:encode(taxonomy),GENERATED[1]:encode(crosswalk),GENERATED[2]:encode(cap),GENERATED[3]:encode(inventory),GENERATED[4]:'\n'.join(md),STATUS:encode(status)}

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args()
 # This is a pinned design build, not a silent updater for future research.
 lock=ROOT/'data/global-integration/filter-inputs.json'
 if lock.exists():
  for s in load(str(lock.relative_to(ROOT)))['sources']:
   if sha(s['path'])!=s['sha256']:raise ValueError('Source changed: explicit D1 review required: '+s['path'])
 changed=[]
 for path,text in outputs().items():
  target=ROOT/path
  if target.exists() and target.read_text(encoding='utf-8')==text:continue
  changed.append(path)
  if not a.check:target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text,encoding='utf-8')
 if a.check and changed:raise SystemExit('Stale contract output: '+', '.join(changed))
 print(json.dumps({'check':a.check,'changed':changed,'scope':'No public UI or candidate-data changes'}))
if __name__=='__main__':main()

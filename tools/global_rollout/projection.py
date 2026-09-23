"""Explicit projection of existing, attributed records; never classify free text.
A crosswalk alone creates no candidacy membership. Every output requires an
existing individual association, source and exact original scope. Legacy synthesis
locators are explicitly marked as research-record locators, not external quotes.
"""
from __future__ import annotations
import copy, hashlib, importlib.util, json, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import Repository, safe_url, jsha, MANDATE_LABELS, HISTORY_LABELS
_spec=importlib.util.spec_from_file_location('canonical_eligibility',ROOT/'tools/global_filters/contract.py')
_contract=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_contract)
SCOPES=('documented_topic','current_support','legacy_context')
BASE='51eb9195d836b984e73f05a845cf414ac1798e35'

def load(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
def slug(value):
 import unicodedata
 folded=''.join(c for c in unicodedata.normalize('NFD',str(value)) if not unicodedata.combining(c)).lower()
 return re.sub('[^a-z0-9]+','-',folded).strip('-')
def sc_filters(root):
 text=(root/'assets/sc-federais-filters-v2-data.js').read_text()
 return json.loads(text.split('Object.freeze(',1)[1].rsplit(');',1)[0])
def native_values(doc, selector):return [n.get('value','') for n in doc.select(selector+' option') if n.get('value')]

def legacy_contract(root,e,doc):
 eid=e['edition_id'];parties=sorted({c['data-party'] for c in doc.select('article.candidate')})
 v=dict(edition_id=eid,parties=parties,topics=[],statuses=[],regions=[],mandates=[''],histories=[''],modes=['any'],orders=['daily'],semantic=None)
 labels={};dialect=None
 if eid=='2026-sc-federais':
  data=sc_filters(root);v.update(topics=[t['id'] for t in data['topics']],modes=['any','all'],semantic='current_support');labels={t['id']:t['label'] for t in data['topics']}
 elif eid=='2026-sc-estaduais':
  v.update(statuses=native_values(doc,'#registrationFilter'),mandates=['','true'],histories=['','true','false'],exclusive=[['mandate','history']])
 elif e['state']=='PR':
  v.update(topics=sorted({b['data-theme'] for b in doc.select('[data-theme]')}),statuses=native_values(doc,'#statusFilter'),regions=native_values(doc,'#regionFilter'),mandates=['','true','false'],histories=['','true','false'],modes=['all'],semantic='legacy_context');dialect='PR'
  labels={b['data-theme']:b.get_text(' ',strip=True) for b in doc.select('[data-theme]')}
 elif e['state']=='SP':
  meta=json.loads(doc.select_one('#pageData').get_text());v.update(parties=meta['parties'],topics=[x['id'] for x in meta['topics']],statuses=[x['id'] for x in meta['statuses']],modes=['any','all'],orders=['daily','alphabetical'],semantic='documented_topic')
  v['aliases']=load(root/'sp/deputados-federais/dados.json').get('provenance',{}).get('topic_id_migration',{});dialect='SP';labels={x['id']:x['label'] for x in meta['topics']}
 controls={}
 for name,selector in [('status','#registrationFilter' if eid=='2026-sc-estaduais' else '#statusFilter'),('mandate','#mandateFilter'),('history','#historyFilter'),('region','#regionFilter')]:
  controls[name]={o['value']:o.get_text(' ',strip=True) for o in doc.select(selector+' option') if o.get('value')}
 return {'valid':v,'dialect':dialect,'topic_labels':labels,'control_labels':controls, 'topic_members':{t['id']:t.get('familyIds',t.get('members',[])) for t in sc_filters(root)['topics']} if eid=='2026-sc-federais' else {}}

def projection(root,e,doc,models,repo,legacy):
 taxonomy=load(root/'config/global-filter-taxonomy.json');crosswalk=load(root/'data/global-integration/filter-crosswalk.json')
 cw={x['source_concept_id']:x for x in crosswalk['entries']};topicids={x['id'] for x in taxonomy['topics']}
 overrides=load(root/'config/rollout-object-decisions.json')['decisions']
 namespace={'SC':'sc-v1','SP':'sp-product-v1','RS':'rs-v1','PR':'pr-v1'}[e['state']]
 path,field,dataset,raws=repo.records(e);byraw={str(r.get('id',r.get('candidate_id'))):(i,r) for i,r in enumerate(raws)}
 cards={c['id'].removeprefix('candidato-'):c for c in doc.select('article.candidate')};legacy_sc={x['id']:x for x in sc_filters(root)['candidates']} if e['edition_id']=='2026-sc-federais' else {}
 items=[];ledger=[];recordlist=[];rejections=[];all_fields={x:{} for x in ('registration','aptitude','mandate','history','region')}
 for m in models:
  cid=m['candidate_id'];idx,raw=byraw[cid];card=cards[cid];key=m['key'];prefix=f'/{field}/{idx}'
  if e['edition_id']=='2026-sc-federais':
   career=card.select_one('.career-band');current=card.select_one('.career-current .career-status.is-current')
   if card.get('data-current-office')=='true' and current is not None and career is not None:
    urls=list(dict.fromkeys(a['href'] for a in career.select('.career-sources a[href],.mandate-origin-source[href]') if safe_url(a['href'])))
    if urls:
     m['mandate'].update(state='source_backed_observation',label=MANDATE_LABELS['source_backed_observation'],sources=urls,
      note='Indicação preservada na ficha de origem: '+current.get_text(' ',strip=True)+'. Não representa nova confirmação de exercício ou licença.',observed_at=None)
   count=card.get('data-pleito-tse','');tag=card.select_one('.tag-pleito')
   if count.isdigit() and int(count)>=1 and tag is not None and 'TSE' in (tag.get('title','')+' '+tag.get_text()):
    m['history']['state']='linked_prior_race' if int(count)>1 else 'no_prior_in_covered_snapshot'
    m['history']['source_coverage']='published_TSE_linked_count_includes_current_election'
    m['coverage']['limitations']=list(m['coverage']['limitations'])+['O histórico filtrável usa a contagem de pleitos vinculados ao TSE já publicada nesta ficha, incluindo 2026. Os detalhes e fontes originais permanecem no histórico; não foi feita nova coleta.']

  candidates=[]
  if e['edition_id']=='2026-sc-federais':
   for ev in m['evidence']:
    a=ev['provenance'][0]['value'];native=a['family_id'];sources=[]
    # Preserve the reviewed atomic wording, not the broader pre-review target.
    ev['object']=a['match_text']
    for s in ev['sources']:
     if s['url']:sources.append({'url':s['url'],'locator':a['rationale_and_locator'],'locator_kind':'reviewed_document_passage','published_at':s['published_at'],'consulted_at':s['consulted_at']})
    candidates.append((native,ev['native_id'],ev['semantic'],a['match_text'],sources,a['nature'],a['original_direction'],a['original_period'],ev['provenance'][0]['ref'],a['eligible_v2']))
  elif e['state']=='SP':
   for ev in m['evidence']:
    for native in ev['native_topics']:
     sources=[{'url':s['url'],'locator':s['locator'] or (ev['provenance'][0]['ref']['path']+'#'+ev['provenance'][0]['ref']['pointer']),
      'locator_kind':'external_document' if s['locator'] else 'research_record_not_external_passage',
      'external_locator_missing':not bool(s['locator']),'published_at':s['published_at'],'consulted_at':s['consulted_at']} for s in ev['sources'] if s['url']]
     candidates.append((native,ev['native_id'],'documented_topic',ev['object'] or ev['text'],sources,ev['nature'],ev['direction'],ev['period'],ev['provenance'][0]['ref'],False))
  elif e['state'] in ('RS','PR'):
   nativefield='topics' if e['state']=='RS' else 'themes'
   for j,t in enumerate(raw.get(nativefield,[])):
    if not isinstance(t,dict) or not t.get('id'):continue
    loc=prefix+f'/{nativefield}/{j}';urls=t.get('sources',[]) if e['state']=='RS' else [t.get('evidence_url')]
    sources=[{'url':u,'locator':f'{path}#{loc}','locator_kind':'research_record_not_external_passage','published_at':None,'consulted_at':raw.get('editorial_checked_at') or raw.get('review_date')} for u in urls if safe_url(u)]
    candidates.append((t['id'],'synthesis','legacy_context',t.get('summary') or raw.get('pautas'),sources,raw.get('summary_kind'),None,None,repo.observation(path,loc)['ref'],False))
  recordev=[]
  for native,nativeid,semantic,obj,sources,nature,direction,period,ref,current in candidates:
   mapping=cw.get(namespace+':'+native)
   if not mapping:rejections.append({'key':key,'source_id':native,'reason':'unmapped_concept','ref':ref});continue
   target=mapping['target_concept_id'];review=None
   if mapping['activation_requirement']=='individual_object_review':
    review=overrides.get(key+':'+native)
    if not review or review['object_sha256']!=jsha(obj):rejections.append({'key':key,'source_id':native,'reason':'individual_object_review_required','ref':ref});continue
    target=review['target']
   if target not in topicids:raise ValueError('Unknown reviewed target')
   member={'edition_id':e['edition_id'],'candidate_id':cid,'association_reviewed':True,'individual_attribution':True,'evidence_id':key+':'+nativeid+':'+native,'object':obj,'topic_id':target,'sources':sources,'semantic':semantic,'claim_id':nativeid if semantic!='legacy_context' else None,'nature':nature,'direction':direction,'currentness_reviewed':current,'current_context_year':e['election_year'] if current else None,'current_context_sources':sources if current else []}
   scopes=[scope for scope in SCOPES if _contract.eligible(member,e['edition_id'],scope)]
   if not scopes:rejections.append({'key':key,'source_id':native,'reason':'missing_required_evidence_metadata','ref':ref});continue
   entry={'topic':target,'scopes':scopes,'native_topic':native,'native_label':mapping['source_label'],'native_id':nativeid,'object':obj,'direction':direction,'nature':nature,'period':period,'semantic':semantic,'sources':sources,'relation':mapping['relation'],'anchor':f'cc-{cid}-evidencias','granularity':'whole_synthesis' if semantic=='legacy_context' and e['state'] in ('RS','PR') else 'claim','ref':ref,'individual_review':review}
   recordev.append(entry);ledger.append({'key':key,**entry})
  original=copy.copy(card)
  # Keep the established free-text scope. Added provenance/UI never classify candidates.
  from bs4 import BeautifulSoup
  clone=BeautifulSoup(str(card),'html.parser').article
  for n in clone.select('.candidate-copy,.candidate-index,.pauta-match,.eef-card-actions,.cc-added'):n.decompose()
  search=clone.get_text()+ ' '+card.get('data-search','') if e['edition_id']=='2026-sc-federais' else card.get('data-search','')
  state=raw.get('registration_status') or raw.get('status')
  registration=slug(state) if state else 'unknown'
  all_fields['registration'][registration]=state or 'Situação não estruturada nesta base'
  apt=m['registration']['apt'];aptitude='yes' if apt is True else 'no' if apt is False else 'unknown'
  all_fields['aptitude'][aptitude]={'yes':'Apta no registro consultado','no':'Inapta no registro consultado','unknown':'Aptidão não confirmada neste conjunto'}[aptitude]
  mandate=m['mandate']['state'];all_fields['mandate'][mandate]=MANDATE_LABELS[mandate]
  history=m['history']['state'];all_fields['history'][history]=HISTORY_LABELS[history]
  region=raw.get('region');region=region.get('label') if isinstance(region,dict) and safe_url(region.get('source')) else ''
  if region:all_fields['region'][region]=region
  native_topics=legacy_sc.get(cid,{}).get('topicIds',[]) if legacy_sc else (card.get('data-themes') or card.get('data-topics','')).split()
  old={'topics':native_topics,'status':card.get('data-registration') or card.get('data-status-group') or card.get('data-status',''),'mandate':card.get('data-current-office',''),'history':card.get('data-has-history') or ('false' if card.get('data-rookie')=='true' else 'true' if card.get('data-rookie')=='false' else ''),'region':card.get('data-region','')}
  recordlist.append({'id':cid,'name':m['identity']['name'],'party':card['data-party'],'search':search,'registration':registration,'aptitude':aptitude,'mandate':mandate,'history':history,'region':region or '', 'evidence':recordev,'legacy':old})
 available={scope:sorted({v['topic'] for r in recordlist for v in r['evidence'] if scope in v['scopes']}) for scope in SCOPES}
 dim=[]
 for field,labels in all_fields.items():
  ready=(field=='registration' and any(x!='unknown' for x in labels)) or (field=='aptitude' and any(x!='unknown' for x in labels)) or (field=='mandate' and any(x not in ('legacy_context','not_confirmed') for x in labels)) or (field=='history' and any(x not in ('not_collected','not_established') for x in labels)) or (field=='region' and bool(labels))
  dim.append({'id':field,'state':'ready' if ready else 'blocked_data','options':[{'value':v,'label':labels[v]} for v in sorted(labels)],'reason':{'registration':'A situação não foi estruturada nesta base; o contexto original permanece na ficha.','aptitude':'Não deduzimos aptidão a partir do nome da situação cadastral.','mandate':'O contexto original permanece disponível, mas falta confirmação estruturada para este filtro.','history':'O histórico desta edição ainda não foi estruturado para comparação.','region':'A localidade precisa ter vínculo de atuação e fonte; não é inferida por nome ou residência.'}[field]})
 return {'schema_version':'1.0.0','edition_id':e['edition_id'],'label':f"{e['state']} · {e['office_label']} · {e['election_year']}",'taxonomy_version':taxonomy['taxonomy_version'],'topics':taxonomy['topics'],'groups':taxonomy['groups'],'records':recordlist,'parties':legacy['valid']['parties'],'dimensions':dim,'available':available,'legacy_contract':legacy,'epochs':{'daily':'2026-09-21'},'baseline':BASE},ledger,rejections

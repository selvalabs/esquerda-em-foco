"""D2/D3: loss-preserving adapters of already-reviewed public exports.
No network, inferred political tags, universal person IDs or research updates.
Every new displayed fact resolves to a frozen JSON pointer or a source DOM node.
"""
from __future__ import annotations
import copy, hashlib, json, re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT = Path(__file__).resolve().parents[2]
BASE = '9dbb26d506a01ddc2dab01bb70611095f1d5a3f8'
VERSION = '1.0.0'
SPECS = {
 '2026-sc-federais': ('data/sc-semantic-v2/candidate-content.json','candidates'),
 '2026-sc-estaduais': ('deputados-estaduais/data/candidaturas.json','candidates'),
 '2026-rs-federais': ('rs/deputados-federais/dados.json','candidates'),
 '2026-pr-federais': ('pr/deputados-federais/dados.json','candidates'),
 '2026-pr-estaduais': ('pr/deputados-estaduais/dados.json','candidates'),
 '2026-sp-federais': ('sp/deputados-federais/dados.json','records'),
}
HISTORY_LABELS = {'linked_prior_race':'Há disputas anteriores vinculadas',
 'no_prior_in_covered_snapshot':'Sem disputa anterior no histórico consultado',
 'not_collected':'Histórico ainda não coletado nesta edição',
 'not_established':'Cobertura do histórico não estabelecida'}
MANDATE_LABELS = {'not_confirmed':'Exercício de mandato não confirmado',
 'institutional_record':'Registro institucional de mandato',
 'source_backed_observation':'Situação de mandato descrita em fonte',
 'self_declared':'Mandato declarado pela candidatura',
 'dated_activity':'Atividade institucional datada',
 'leave_documented':'Licença documentada',
 'substitute_documented':'Suplência documentada',
 'legacy_context':'Situação descrita no contexto original'}
COVERAGE_LABELS = {'documented':'Há conteúdo individual documentado',
 'not_consolidated':'Síntese individual ainda não consolidada',
 'not_reviewed':'Revisão individual ainda pendente',
 'insufficient':'Material revisto insuficiente para uma síntese',
 'blocked':'Acesso à fonte limitado nesta revisão',
 'not_established':'Cobertura detalhada não registrada',
 'not_located':'Material individual não localizado nesta busca',
 'not_applicable':'Dimensão não aplicável a este registro'}
SOURCE_DATE_FIELDS = ('publication_date','published_at','original_published_at')
READ_DATE_FIELDS = ('consulted_at','checked_at','checked_on_local','read_at','retrieved_at')

def load(p: Path): return json.loads(p.read_text(encoding='utf-8'))
def save(p: Path, data):
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
def sha(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()
def jsha(value) -> str: return sha(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())
def safe_url(value):
 if not isinstance(value,str):return None
 try:u=urlsplit(value)
 except ValueError:return None
 return value if u.scheme in ('https','http') and u.netloc and not u.username and not u.password else None

def resolve(value, pointer):
 for part in pointer.split('/')[1:]:
  part=part.replace('~1','/').replace('~0','~')
  value=value[int(part)] if isinstance(value,list) else value[part]
 return value

def observed(root, path, pointer='', selector=None):
 raw=(root/path).read_bytes();ref={'path':path,'sha256':sha(raw),'kind':'html' if selector else 'json'}
 if selector:
  n=BeautifulSoup(raw,'html.parser').select_one(selector)
  if n is None:raise ValueError('Unresolved selector '+selector)
  value=n.get_text(' ',strip=True);ref['selector']=selector
 else:value=resolve(json.loads(raw),pointer);ref['pointer']=pointer
 ref['value_sha256']=jsha(value)
 return {'value':copy.deepcopy(value),'ref':ref}

def validate_observation(root, o):
 ref=o['ref'];p=(root/ref['path']).resolve()
 if not p.is_relative_to(root.resolve()):raise ValueError('Provenance escapes root')
 if sha(p.read_bytes())!=ref['sha256']:raise ValueError('Source changed: '+ref['path'])
 if ref['kind']=='json':v=resolve(load(p),ref['pointer'])
 else:
  n=BeautifulSoup(p.read_bytes(),'html.parser').select_one(ref['selector'])
  if n is None:raise ValueError('Missing original node')
  v=n.get_text(' ',strip=True)
 if jsha(v)!=ref['value_sha256'] or v!=o['value']:raise ValueError('Observation mutated')

def first_value(raw, keys):
 return next((raw[k] for k in keys if raw.get(k) not in (None,'')),None)

def vote(row):
 """Expose verification only when an existing verification/source supports it."""
 n=row.get('votes');status=row.get('votes_status',row.get('vote_status'))
 if status=='verified_nominal':
  if type(n) is not int or n<0:raise ValueError('Nominal verification without valid total')
  state='verified_nominal'
 elif status:
  state={'not_collected_in_round_b':'not_collected','not_published_inapt':'not_published_inapt',
   'not_verified':'not_verified','not_applicable':'not_applicable','not_yet_held':'not_yet_held'}.get(status,'unmapped')
  if n is not None:raise ValueError('Unverified/NA total must remain null')
 elif n is not None:
  if type(n) is not int or n<0:raise ValueError('Invalid vote count')
  # A number alone does not establish a verification process.
  state='documented_nominal' if (row.get('vote_type')=='nominal' and safe_url(row.get('votes_source'))) or row.get('votes_provenance') else 'reported_unclassified'
 else:state='not_established'
 return {'value':n,'state':state,'source_status':status,'raw':copy.deepcopy(row)}

def history_state(rows, coverage, year):
 if coverage=='not_collected':return 'not_collected'
 if coverage!='covered' or rows is None or any(type(r.get('year')) is not int for r in rows):return 'not_established'
 return 'linked_prior_race' if any(r['year']<year for r in rows) else 'no_prior_in_covered_snapshot'

def mandate(raw, eid):
 state='not_confirmed';label=MANDATE_LABELS[state];note=None;sources=[];date=None
 if eid=='2026-sc-estaduais':
  status=raw.get('mandate_state');note=raw.get('mandate_note')
  source=safe_url(raw.get('mandate_source'))
  state={'titular':'institutional_record','declarado':'self_declared','atividade_datada':'dated_activity',
    'licenciado':'leave_documented','suplencia_documentada':'substitute_documented'}.get(status,'not_confirmed')
  if state!='not_confirmed' and not source:state='not_confirmed'
  if source:sources=[source]
  label=raw.get('mandate_label') or MANDATE_LABELS[state]
  date=raw.get('consulted_at') # provenance below explicitly identifies this as record consultation
 else:
  current=raw.get('current_role_observation') or raw.get('current_office')
  if isinstance(current,dict):
   source=safe_url(current.get('source'))
   if source:state='source_backed_observation';sources=[source]
   label=current.get('label') or MANDATE_LABELS[state]
   note=current.get('detail') or current.get('scope');date=current.get('checked_at')
 return {'state':state,'label':label,'note':note,'sources':sources,'observed_at':date}

def source_view(source, key):
 url=safe_url(source.get('url') or source.get('source'))
 return {'source_key':key,'url':url,'title':source.get('title') or source.get('label') or 'Consultar documento',
  'published_at':first_value(source,SOURCE_DATE_FIELDS),'consulted_at':first_value(source,READ_DATE_FIELDS),
  'locator':source.get('locator'),'publisher':source.get('publisher'),
  'nature':source.get('type') or source.get('kind') or source.get('source_type'),
  'limitation':source.get('availability_note') or source.get('finding'),
  'raw':copy.deepcopy(source)}

def evidence_record(key, native_id, text, semantic, topics, sources, obs, **fields):
 return {'evidence_key':key+':'+native_id,'native_id':native_id,'text':text,'semantic':semantic,
  'native_topics':list(dict.fromkeys(topics)),'sources':sources,'provenance':[obs],
  'nature':fields.get('nature'),'direction':fields.get('direction'),'period':fields.get('period'),
  'object':fields.get('object'),'attribution':fields.get('attribution'),
  'granularity':fields.get('granularity','claim'), 'missing':[k for k in ('nature','direction','period','object','attribution') if not fields.get(k)],
  'global_filter_activation':False}

class Repository:
 def __init__(self, root=ROOT):
  self.root=Path(root);self.registry=load(self.root/'config/editions.json')
  self.cache={};self.hashes={}
  self.sc_editorial=self.read('data/sc-editorial-selected-r1/editorial.json')
  self.sc_sources=self.sc_editorial['sources']
  self.sc_audit=self.read('data/sc-semantic-v2/association-audit.json')['associations']
  self.sc_review=self.read('data/sc-semantic-v2/source-review.json')['sources']
 def read(self,path):
  if path not in self.cache:
   self.cache[path]=load(self.root/path);self.hashes[path]=sha((self.root/path).read_bytes())
  return self.cache[path]
 def observation(self,path,pointer):
  data=self.read(path);v=resolve(data,pointer)
  return {'value':copy.deepcopy(v),'ref':{'path':path,'sha256':self.hashes[path],'kind':'json','pointer':pointer,'value_sha256':jsha(v)}}
 def editions(self):return [e for e in self.registry['editions'] if e['publication_status']=='published']
 def records(self,e):
  path,field=SPECS[e['edition_id']];data=self.read(path)
  return path,field,data,data[field]
 def models(self,e):
  path,field,data,rows=self.records(e)
  doc=BeautifulSoup((self.root/e['entrypoint']).read_bytes(),'html.parser')
  cards={c['id'].removeprefix('candidato-'):c for c in doc.select('article.candidate')}
  if set(cards)!=set(str(x.get('id',x.get('candidate_id'))) for x in rows):raise ValueError('Catalog mismatch '+e['edition_id'])
  return doc,[self.adapt(e,r,idx,path,field,data,cards[str(r.get('id',r.get('candidate_id')))]) for idx,r in enumerate(rows)]
 def adapt(self,e,raw,idx,path,field,data,card):
  eid=e['edition_id'];cid=str(raw.get('id',raw.get('candidate_id')))
  if not re.fullmatch(r'\d{4}-[a-z]{2}-(federais|estaduais)',eid) or not re.fullmatch(r'\d{12}',cid):raise ValueError('Invalid contextual identity')
  if raw.get('state',e['state'])!=e['state'] or raw.get('office_code',e['office_code'])!=e['office_code'] or raw.get('election_year',e['election_year'])!=e['election_year']:raise ValueError('Foreign identity')
  key=eid+':'+cid;prefix=f'/{field}/{idx}';facts={}
  for name in ['name','number','party','status','status_api','status_group','status_date','apt_api','profile_checked_at','registration_status','registration_group','registration_details','consulted_at','reviewed_at','research_state','research_status','research_date','editorial_checked_at','review_date','history_state','mandate_state','mandate_label','mandate_note','mandate_source','mandate_verification','mandate_source_kind','current_role_observation','current_office','topics_kind','topics_material_date','topics_review_status','source_limitation','documentation_note','gap_review_scope','sources_and_context','limitations','region','review_completed_in_round','corrections']:
   if name in raw:facts[name]=self.observation(path,prefix+'/'+name)
  for name in ['as_of','collected_at','updated_at','review_date']:
   if name in data:facts['dataset_'+name]=self.observation(path,'/'+name)
  before=json.dumps(raw,sort_keys=True,ensure_ascii=False)
  registration={'label':raw.get('registration_status') or raw.get('status'),
   'date':raw.get('status_date') or raw.get('profile_checked_at') or raw.get('consulted_at') or data.get('as_of') or data.get('collected_at'),
   'date_scope':'candidate' if any(raw.get(x) for x in ['status_date','profile_checked_at','consulted_at']) else 'dataset',
   'apt':raw.get('apt_api'),'source':safe_url(raw.get('tse_url')),
   'raw_fields':copy.deepcopy(raw.get('registration_details') or raw.get('status_fields') or {}),
   'inference':'none'}
  hrows=raw.get('history');coverage='not_collected' if str(raw.get('history_state','')).startswith('not_collected') else ('covered' if hrows is not None else 'not_established')
  history={'state':history_state(hrows,coverage,e['election_year']), 'entries':[], 'source_coverage':raw.get('history_state'), 'provenance':[]}
  if hrows is not None:
   history['provenance']=[self.observation(path,prefix+'/history')]
   for i,h in enumerate(hrows):
    v=vote(h);hkey=key+':history:'+jsha([h.get(k) for k in ['year','round','candidate_id','historical_candidate_id','election_id','office','place','electoral_unit','uf']])[:20]
    history['entries'].append({'key':hkey,'year':h.get('year'),'prior':type(h.get('year')) is int and h['year']<e['election_year'],
     'office':h.get('office'),'place':h.get('place') or h.get('electoral_unit'),'votes':v,
     'provenance':self.observation(path,prefix+f'/history/{i}')})
  m=mandate(raw,eid);ev=[];limitations=[]
  edate=raw.get('reviewed_at') or raw.get('research_date') or raw.get('editorial_checked_at') or raw.get('review_date')
  cov='not_established'
  if eid=='2026-sc-federais':
   ei=next(i for i,x in enumerate(self.sc_editorial['candidates']) if x['candidate_id']==cid);editorial=self.sc_editorial['candidates'][ei]
   facts['editorial_review']=self.observation('data/sc-editorial-selected-r1/editorial.json',f'/candidates/{ei}')
   edate=self.sc_editorial['evidence_date'];facts['evidence_date']=self.observation('data/sc-editorial-selected-r1/editorial.json','/evidence_date')
   facts['wording_date']=self.observation('data/sc-editorial-selected-r1/editorial.json','/editorial_date')
   limitations=editorial['retained_limitations'];cov='documented' if editorial['sections'] else 'insufficient'
   for ai,a in enumerate(self.sc_audit):
    if a['candidate_id']!=cid:continue
    sources=[]
    for sid in a['source_ids']:
     si=next((j for j,s in (self.sc_sources.items() if isinstance(self.sc_sources,dict) else enumerate(self.sc_sources)) if s['source_id']==sid),None)
     if si is None:raise ValueError('Orphan SC source '+sid)
     s=source_view(self.sc_sources[si],key+':source:'+sid)
     s['provenance']=self.observation('data/sc-editorial-selected-r1/editorial.json',f'/sources/{si}')
     # Reconfirmation records enrich provenance; never override publication dates.
     ri=next((j for j,r in enumerate(self.sc_review) if r['source_id']==sid),None)
     if ri is not None:
      review=self.sc_review[ri];s['consulted_at']=review.get('checked_on_local');s['limitation']=review.get('availability_note') if not review.get('content_reconfirmed') else None
      s['review_provenance']=self.observation('data/sc-semantic-v2/source-review.json',f'/sources/{ri}')
     sources.append(s)
    semantic='current_support' if a['eligible_v2'] else ('legacy_context' if not a['all_sources_reconfirmed'] or a['section']=='contexto' else 'documented_topic')
    ev.append(evidence_record(key,a['association_id'],a['match_text'],semantic,[a['family_id']],sources,
      self.observation('data/sc-semantic-v2/association-audit.json',f'/associations/{ai}'),nature=a['nature'],direction=a['original_direction'],period=a['original_period'],object=a['original_target'],attribution=a['candidate_name']))
   # SC career is still HTML-only: preserve the exact statement, do not reconstruct structured votes from prose.
   career=card.select_one('.career-band')
   if career:
    facts['legacy_career']={'value':career.get_text(' ',strip=True),'ref':{'kind':'html','path':e['entrypoint'],'selector':'#'+card['id']+' .career-band','sha256':sha((self.root/e['entrypoint']).read_bytes()),'value_sha256':jsha(career.get_text(' ',strip=True))}}
    m={'state':'legacy_context','label':MANDATE_LABELS['legacy_context'],'note':'A descrição original e suas referências foram mantidas abaixo. Não foi feita nova confirmação de exercício.','sources':[],'observed_at':None}
  elif eid=='2026-sp-federais':
   limitations=raw.get('limitations',[])
   cov='not_reviewed' if raw.get('research_state')=='canonical_scope_addition_not_reviewed' else ('documented' if raw.get('claims_2026') or raw.get('claims_other') else 'not_consolidated')
   for group in ['claims_2026','claims_other']:
    for ci,claim in enumerate(raw.get(group,[])):
     sources=[]
     for sid in claim.get('source_ids',[]):
      si=next((j for j,s in enumerate(raw.get('sources',[])) if s.get('source_id',s.get('id'))==sid),None)
      if si is None:raise ValueError('Orphan SP source '+sid)
      s=source_view(raw['sources'][si],key+':source:'+sid);s['provenance']=self.observation(path,prefix+f'/sources/{si}');sources.append(s)
     ev.append(evidence_record(key,claim['claim_id'],claim['text'],'documented_topic',claim.get('theme_ids',[]),sources,
      self.observation(path,prefix+f'/{group}/{ci}'),nature=claim.get('evidence_type'),direction=claim.get('direction'),period=claim.get('period'),object=claim.get('object') or claim.get('position_target'),attribution=raw['name']))
  else:
   text=raw.get('topics') if eid=='2026-sc-estaduais' else raw.get('pautas')
   if not isinstance(text,str):text=None
   has_content=(raw.get('topics_review_status') in ('documented','documented_individual_source')) if eid=='2026-sc-estaduais' else bool(text)
   cov='documented' if has_content else ('not_reviewed' if raw.get('research_status')=='pendente' else 'not_consolidated')
   if raw.get('source_limitation'):limitations.append(raw['source_limitation'])
   if has_content and text:
    # Whole synthesis: do not distribute its sources onto invented sentence-level claims.
    sources=[];topics=[]
    if eid=='2026-sc-estaduais':
     if raw.get('topics_source'):
      s=source_view({'url':raw['topics_source'],'title':'Publicação usada na síntese','type':raw.get('topics_kind'),'consulted_at':raw.get('reviewed_at')},key+':source:synthesis')
      s['provenance']=self.observation(path,prefix+'/topics_source');sources.append(s)
    else:
     for si,source in enumerate(raw.get('editorial_sources',[])):
      s=source_view(source,key+f':source:{si}');s['provenance']=self.observation(path,prefix+f'/editorial_sources/{si}');sources.append(s)
     for t in raw.get('themes',raw.get('topics',[])):
      if isinstance(t,dict) and t.get('id'):topics.append(t['id'])
    ev.append(evidence_record(key,'synthesis',text,'legacy_context',topics,sources,
     self.observation(path,prefix+('/topics' if eid=='2026-sc-estaduais' else '/pautas')),nature=raw.get('summary_kind') or raw.get('topics_kind'),period=raw.get('topics_material_date'),attribution=raw['name'],granularity='whole_synthesis'))
  if before!=json.dumps(raw,sort_keys=True,ensure_ascii=False):raise ValueError('Adapter mutated source')
  return {'schema_version':VERSION,'edition_id':eid,'candidate_id':cid,'key':key,
   'identity':{'name':raw['name'],'party':raw['party'],'state':e['state'],'office':e['office_label'],'year':e['election_year']},
   'registration':registration,'mandate':m,'history':history,'coverage':{'state':cov,'review_date':edate,'limitations':limitations,'completion_inferred':False},
   'observations':facts,'evidence':ev,'original_card':{'path':e['entrypoint'],'selector':'#'+card['id'],'text_sha256':sha(card.get_text(' ',strip=True).encode()),'file_sha256':sha((self.root/e['entrypoint']).read_bytes())},
   'corrections':copy.deepcopy(raw.get('corrections',[])),
   'activation':'prototype_only','new_political_assertions':False}


def explicit_coverage(status):
 return {'research_pending':'not_reviewed','not_started':'not_reviewed',
  'source_access_blocked':'blocked','individual_sources_reviewed_insufficient':'insufficient',
  'not_located':'not_located','not_consolidated':'not_consolidated',
  'not_applicable':'not_applicable','documented':'documented'}.get(status,'not_established')

def correction_view(raw, candidate_id):
 if raw.get('candidate_id')!=candidate_id:raise ValueError('Correction belongs to another candidacy')
 if not raw.get('reason') or not raw.get('action'):raise ValueError('Correction lacks reason or action')
 # Keep withdrawal as withdrawal; never turn the old paragraph into a live assertion.
 return {'candidate_id':candidate_id,'action':raw['action'],'reason':raw['reason'],
  'checked_at':raw.get('checked_at'),'previous_record':copy.deepcopy(raw.get('previous_record')),
  'sources':copy.deepcopy(raw.get('sources',[])),'unresolved':raw.get('unresolved'),
  'counts_as_current_evidence':False}

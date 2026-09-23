"""JSON Schema for the review model, complemented by source/parity validators."""
from model import ROOT,save
STR={'type':'string'}
REF={'type':'object','required':['path','sha256','kind','value_sha256'],'properties':{
 'path':STR,'sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'kind':{'enum':['json','html']},'value_sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'pointer':STR,'selector':STR},'additionalProperties':False,
 'allOf':[{'if':{'properties':{'kind':{'const':'json'}}},'then':{'required':['pointer']},'else':{'required':['selector']}}]}
OBS={'type':'object','required':['value','ref'],'properties':{'value':{},'ref':REF},'additionalProperties':False}
EVIDENCE={'type':'object','required':['evidence_key','native_id','text','semantic','native_topics','sources','provenance','nature','direction','period','object','attribution','granularity','missing','global_filter_activation'],
 'properties':{'evidence_key':STR,'native_id':STR,'text':STR,'semantic':{'enum':['current_support','documented_topic','legacy_context']},'native_topics':{'type':'array','items':STR,'uniqueItems':True},'sources':{'type':'array','items':{'type':'object','required':['source_key','url','title','published_at','consulted_at','locator','provenance']}},'provenance':{'type':'array','minItems':1,'items':OBS},'nature':{},'direction':{},'period':{},'object':{},'attribution':{},'granularity':{'enum':['claim','whole_synthesis']},'missing':{'type':'array','items':STR},'global_filter_activation':{'const':False}},'additionalProperties':False}
def schema():
 props={'schema_version':{'const':'1.0.0'},'edition_id':{'type':'string','pattern':'^[0-9]{4}-[a-z]{2}-(federais|estaduais)$'},'candidate_id':{'type':'string','pattern':'^[0-9]{12}$'},'key':STR,
  'identity':{'type':'object','required':['name','party','state','office','year'],'additionalProperties':False,'properties':{'name':STR,'party':STR,'state':STR,'office':STR,'year':{'type':'integer'}}},
  'registration':{'type':'object','required':['label','date','date_scope','apt','source','raw_fields','inference'],'properties':{'apt':{'type':['boolean','null']},'inference':{'const':'none'}}},
  'mandate':{'type':'object','required':['state','label','note','sources','observed_at']},
  'history':{'type':'object','required':['state','entries','source_coverage','provenance'],'properties':{'state':{'enum':['linked_prior_race','no_prior_in_covered_snapshot','not_collected','not_established']},'provenance':{'type':'array','items':OBS},'entries':{'type':'array'}}},
  'coverage':{'type':'object','required':['state','review_date','limitations','completion_inferred'],'properties':{'completion_inferred':{'const':False}}},
  'observations':{'type':'object','additionalProperties':OBS},'evidence':{'type':'array','items':EVIDENCE},'original_card':{'type':'object','required':['path','selector','text_sha256','file_sha256']},'activation':{'const':'prototype_only'},'new_political_assertions':{'const':False},'corrections':{'type':'array'}}
 return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'EEF canonical card review model D2/D3','type':'object','required':list(props),'properties':props,'additionalProperties':False}
if __name__=='__main__':save(ROOT/'config/canonical-card.schema.json',schema())

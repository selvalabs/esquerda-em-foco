"""Strict structural schemas for D1 artifacts; semantic integrity is tested separately."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
S={'type':'string','minLength':1}; BOOL={'type':'boolean'}; NONNEG={'type':'integer','minimum':0}
SHA={'type':'string','pattern':'^[a-f0-9]{64}$'}; COMMIT={'type':'string','pattern':'^[a-f0-9]{40}$'}
def obj(properties,required=None):return {'type':'object','properties':properties,'required':list(properties) if required is None else required,'additionalProperties':False}
def arr(item):return {'type':'array','items':item}
def typed_shape(value):
    if isinstance(value,dict):return obj({k:typed_shape(v) for k,v in value.items()})
    if isinstance(value,list):return arr(typed_shape(value[0])) if value else {'type':'array'}
    if value is None:return {'type':['null','string']}
    if isinstance(value,bool):return {'const':value}
    if isinstance(value,int):return {'type':'integer'}
    return {'type':'string'}
def schema():
    taxonomy=json.loads((ROOT/'config/global-filter-taxonomy.json').read_text())
    tax=typed_shape(taxonomy)
    tax['properties']['schema_version']={'const':'1.0.0'}
    tax['properties']['taxonomy_version']={'const':'1.0.0'}
    tax['properties']['status']={'const':'specified_not_activated'}
    tax['properties']['topics']['minItems']=1
    tax['properties']['groups']['minItems']=1
    source=obj({'path':S,'commit':COMMIT,'sha256':SHA,'pointer':{'type':'string'}})
    example=obj({'candidate_id':S,'edition_id':S,'path':S,'pointer':S,'scope':{'type':['string','null']},'source_ids_or_urls':arr(S),
       'direction':{'type':['string','null']},'period':{'type':['string','null']},'locator':{'type':['string','null']},'active_membership':BOOL,'metadata_note':S},
       ['candidate_id','path','pointer','scope','source_ids_or_urls','direction','period','locator','active_membership'])
    relation={'enum':['equivalent','related','specific','not_comparable','review_required']}
    mapping=obj({'source_concept_id':S,'source_label':S,'target_concept_id':S,'relation':relation,
       'scope_relation':{'enum':['same','narrower','bounded_label','overlap']},'decision':{'const':'accepted_for_design'},'reason':S,
       'definition_basis':{'enum':['explicit_definition','bounded_label_with_individual_source_links']},'source':source,
       'source_definition':{'type':'object'},'native_scope_required':{'const':True},'automatic_candidate_mapping':{'const':False},
       'activation_requirement':S,'usage':obj({'associations':NONNEG,'distinct_candidate_keys':NONNEG,'filter_member_keys_at_baseline':{'type':['integer','null'],'minimum':0},'examples':arr(example),'examples_policy':S})})
    cross=obj({'schema_version':{'const':'1.0.0'},'baseline':COMMIT,'issue':{'const':53},'ui_active':{'const':False},'scope':{'const':'concept_design_not_candidate_reclassification'},
      'entries':arr(mapping),'aliases':arr(obj({'namespace':S,'old_id':S,'target_source_id':S,'kind':{'const':'declared_id_alias'},'changes_evidence':{'const':False},'source':source})),
      'rejected_or_review_required':arr(obj({'source_concept_id':S,'target_concept_id':S,'relation':relation,'reason':S,'automatic_candidate_mapping':{'const':False}})),
      'legacy_group_queries':arr(obj({'source_namespace':S,'source_id':S,'label':S,'frozen_any_of_topics':arr(S),'source':source,'rule':S,'automatic_expansion':{'const':False}})),
      'summary':obj({'source_entries':NONNEG,'relations':{'type':'object','additionalProperties':NONNEG}})})
    # Field-derived counts are immutable observations, not policy enums.
    cap=json.loads((ROOT/'data/global-integration/filter-capabilities.json').read_text())
    dim=obj({'id':S,'data_readiness':{'enum':['ready','partial','absent','not_applicable']},
      'current_implementation':{'enum':['active_local','migration_required','contract_only','not_applicable']},
      'target':{'const':'common_global_dimension'},'blockers':arr({'enum':['publication','field_missing','field_semantics','claim_review','implementation']}),
      'reason':S,'evidence':arr(source),'current':arr(S),'canonical_target':arr(S)},
      ['id','data_readiness','current_implementation','target','blockers','reason','evidence'])
    edition=obj({'edition_id':{'type':'string','pattern':'^[0-9]{4}-[a-z]{2}-(federais|estaduais)$'},
      'publication_status':{'enum':['published','branch_only']},'facts':{'type':['object','null']},'dimensions':arr(dim),'blockers':arr(S),'note':S,
      'current_semantic':{'enum':[None,'current_support','documented_topic','legacy_context']},'current_order':arr(S),'runtime':source,'public_changes_in_D1':{'const':False}},
      ['edition_id','publication_status','facts','dimensions'])
    caps=obj({'schema_version':{'const':'1.0.0'},'baseline':COMMIT,'issue':{'const':53},'activation':{'const':'design_only'},'editions':arr(edition),'no_false_parity':S})
    return {'$schema':'https://json-schema.org/draft/2020-12/schema','title':'GLOBAL-04D1 design contracts',
       '$defs':{'taxonomy':tax,'crosswalk':cross,'capabilities':caps},'oneOf':[{'$ref':'#/$defs/taxonomy'},{'$ref':'#/$defs/crosswalk'},{'$ref':'#/$defs/capabilities'}]}
if __name__=='__main__':
    import argparse
    a=argparse.ArgumentParser();a.add_argument('--check',action='store_true');args=a.parse_args()
    p=ROOT/'config/global-filter-taxonomy.schema.json';text=json.dumps(schema(),ensure_ascii=False,indent=2)+'\n'
    if args.check:
        if not p.exists() or p.read_text()!=text:raise SystemExit('Schema output differs')
    else:p.write_text(text)

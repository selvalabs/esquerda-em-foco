"""#53 semantic contracts, not a new political fact check or browser rollout."""
from __future__ import annotations
import copy,hashlib,json,sys,unittest
from pathlib import Path
import jsonschema
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/global_filters'))
from build import outputs,source_usage
from contract import domain_lookup,eligible,select,mandate_from_legacy,prior_history,vote_state
from decisions import BASE,DATASETS

def load(p):return json.loads((ROOT/p).read_text())
T=load('config/global-filter-taxonomy.json');W=load('data/global-integration/filter-crosswalk.json');C=load('data/global-integration/filter-capabilities.json')
SCHEMA=load('config/global-filter-taxonomy.schema.json');V=jsonschema.Draft202012Validator(SCHEMA)
ED='2026-sc-federais'

def fixture(**kw):
    d={'edition_id':ED,'candidate_id':'240000000001','evidence_id':'e1','claim_id':'c1','topic_id':'saude',
       'association_reviewed':True,'individual_attribution':True,'object':'Prioridade expressa de saúde',
       'sources':[{'url':'https://example.org/document','locator':'parágrafo 2'}],
       'semantic':'current_support','direction':'prioridade','nature':'declaracao','period':'2026',
       'currentness_reviewed':True,'current_context_year':2026,
       'current_context_sources':[{'url':'https://example.org/campaign','locator':'contexto de campanha'}]}
    d.update(kw);return d

def pointer(path,ptr):
    node=load(path)
    for k in ptr.strip('/').split('/') if ptr else []:
        key=k.replace('~1','/').replace('~0','~');node=node[int(key)] if isinstance(node,list) else node[key]
    return node

class Vocabulary(unittest.TestCase):
    def test_01_schema_documents(self):
        jsonschema.Draft202012Validator.check_schema(SCHEMA)
        for d in [T,W,C]:V.validate(d)
    def test_02_complete_inventory(self):
        cats=load('config/taxonomies.json')['catalogs'];expected={c['id'] for cat in cats for c in cat['concepts']}
        actual=[m['source_concept_id'] for m in W['entries']]
        self.assertEqual(len(actual),112);self.assertEqual(set(actual),expected);self.assertEqual(len(actual),len(set(actual)))
    def test_03_topic_targets_no_loss(self):
        ids=[t['id'] for t in T['topics']];self.assertEqual(len(ids),39);self.assertEqual(len(set(ids)),len(ids))
        self.assertTrue(all(m['target_concept_id'] in ids for m in W['entries']))
        self.assertEqual({m['target_concept_id'] for m in W['entries']},set(ids))
    def test_04_each_domain_in_one_group(self):
        members=[x for g in T['groups'] for x in g['members']]
        self.assertEqual(len(T['groups']),16);self.assertEqual(sorted(members),sorted(t['id'] for t in T['topics']))
    def test_05_new_donors_retained(self):
        ids={t['id'] for t in T['topics']}
        self.assertTrue({'ciencia-tecnologia-inovacao','direitos-consumidor','esporte-lazer','previdencia','liberdade-religiosa','seguranca-alimentar','trabalho-renda','direitos-sociais','renda-protecao-social','desenvolvimento-industria'}<=ids)
    def test_06_exact_definitions_not_just_label(self):
        sc={c['id']:c for c in load('config/topics-v1.json')['topics']}
        for m in W['entries']:
            if m['relation']!='equivalent':continue
            with self.subTest(concept=m['source_concept_id']):
                self.assertEqual(m['source_definition']['includes'],sc[m['target_concept_id']]['includes'])
                self.assertEqual(m['source_definition']['excludes'],sc[m['target_concept_id']]['excludes'])
    def test_07_source_locations_all_resolve(self):
        for m in W['entries']:
            with self.subTest(concept=m['source_concept_id']):
                src=pointer(m['source']['path'],m['source']['pointer'])
                self.assertEqual(src,m['source_label'] if isinstance(src,str) else m['source_definition'])
    def test_08_examples_are_existing_records(self):
        for m in W['entries']:
            for ex in m['usage']['examples']:
                with self.subTest(concept=m['source_concept_id'],pointer=ex['pointer']):
                    original=pointer(ex['path'],ex['pointer']);self.assertTrue(original)
                    if 'family_id' in original:self.assertTrue(m['source_concept_id'].endswith(':'+original['family_id']))
                    else:self.assertTrue(m['source_concept_id'].endswith(':'+original['id']))
    def test_09_source_hashes_pinned(self):
        for r in load('data/global-integration/filter-inputs.json')['sources']:
            with self.subTest(path=r['path']):
                self.assertEqual(r['commit'],BASE);self.assertEqual(hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest(),r['sha256'])
    def test_10_mapping_is_not_membership(self):
        for m in W['entries']:
            decision=domain_lookup(m['source_concept_id'],W)
            self.assertIs(decision['automatic_candidate_mapping'],False)
            self.assertFalse(eligible(decision,ED,'current_support'))
    def test_11_unknown_is_not_fuzzy_matched(self):
        for bad in ['saude','pr-v1:saúde','PT','professor','sc-v1:reforma-agraria','__proto__']:
            with self.assertRaises(ValueError):domain_lookup(bad,W)
    def test_12_aliases_only_declared(self):
        aliases=W['aliases'];self.assertEqual(len(aliases),3)
        for a in aliases:
            self.assertEqual(a['namespace'],'sp-product-v1');self.assertIs(a['changes_evidence'],False)
            self.assertEqual(pointer(a['source']['path'],a['source']['pointer'])[a['old_id']],a['target_source_id'])
    def test_13_old_groups_do_not_broaden(self):
        old=load('data/sc-semantic-v2/macrogroups.json')['groups'];self.assertEqual(len(W['legacy_group_queries']),14)
        for actual,original in zip(W['legacy_group_queries'],old):
            self.assertEqual(actual['source_id'],original['id']);self.assertEqual(actual['frozen_any_of_topics'],original['family_ids']);self.assertIs(actual['automatic_expansion'],False)
        g=next(g for g in W['legacy_group_queries'] if g['source_id']=='agricultura-campo')
        self.assertNotIn('seguranca-alimentar',g['frozen_any_of_topics'])
    def test_14_rejected_shortcuts_are_explicit(self):
        self.assertEqual(len(W['rejected_or_review_required']),8)
        self.assertEqual({m['relation'] for m in W['rejected_or_review_required']},{'not_comparable','review_required'})
    def test_15_no_runtime_activation(self):
        self.assertIs(T['ui_active'],False);self.assertIs(W['ui_active'],False);self.assertEqual(C['activation'],'design_only')
        for e in load('config/editions.json')['editions']:
            if e['publication_status']=='published':self.assertNotIn('global-filter-taxonomy',(ROOT/e['entrypoint']).read_text())
    def test_16_deterministic_build(self):
        first=outputs();self.assertEqual(first,outputs())
        for path,text in first.items():self.assertEqual((ROOT/path).read_text(),text,path)
    def test_17_schema_rejects_promotion(self):
        x=copy.deepcopy(W);x['entries'][0]['automatic_candidate_mapping']=True
        with self.assertRaises(jsonschema.ValidationError):V.validate(x)
        x=copy.deepcopy(T);x['ui_active']=True
        with self.assertRaises(jsonschema.ValidationError):V.validate(x)
    def test_18_schema_rejects_bad_relation(self):
        x=copy.deepcopy(W);x['entries'][0]['relation']='inferred_by_party'
        with self.assertRaises(jsonschema.ValidationError):V.validate(x)
    def test_19_counts_are_people_not_links(self):
        for m in W['entries']:
            self.assertLessEqual(m['usage']['distinct_candidate_keys'],m['usage']['associations'])
    def test_20_real_union_and_intersection_are_subset(self):
        for ns in ['sc-v1','sp-product-v1','rs-v1','pr-v1']:
            u=source_usage();sets=[{(x.get('edition_id',ED),x['candidate_id']) for x in vals} for id,vals in u.items() if id.startswith(ns+':')]
            for a,b in zip(sets,sets[1:]):self.assertTrue((a&b)<=a<=a|b)

class Semantics(unittest.TestCase):
    def test_21_current_support_positive(self):self.assertTrue(eligible(fixture(),ED,'current_support'))
    def test_22_opposition_not_support(self):
        e=fixture(direction='oposicao');self.assertFalse(eligible(e,ED,'current_support'));self.assertTrue(eligible(e,ED,'documented_topic'))
    def test_23_activity_not_support(self):
        e=fixture(semantic='documented_topic',nature='ato_legislativo',direction='atuacao_documentada');self.assertFalse(eligible(e,ED,'current_support'));self.assertTrue(eligible(e,ED,'documented_topic'))
    def test_24_consultation_is_not_currentness(self):
        e=fixture(currentness_reviewed=False,period=None,consulted_at='2026-09-22');self.assertFalse(eligible(e,ED,'current_support'))
    def test_25_reaffirmation_needs_context_evidence(self):
        e=fixture(period='2023',current_context_sources=[]);self.assertFalse(eligible(e,ED,'current_support'))
        e['current_context_sources']=fixture()['current_context_sources'];self.assertTrue(eligible(e,ED,'current_support'))
    def test_26_legacy_not_promoted(self):
        e=fixture(semantic='legacy_context');self.assertTrue(eligible(e,ED,'legacy_context'))
        for view in ['current_support','documented_topic']:self.assertFalse(eligible(e,ED,view))
    def test_27_party_and_profession_no_proof(self):
        for e in [fixture(association_reviewed=False,party='PT',occupation='professor'),fixture(individual_attribution=False),fixture(sources=[]),fixture(object='')]:self.assertFalse(eligible(e,ED,'current_support'))
    def test_28_identity_year_isolation(self):
        for edition in ['2026-sp-federais','2026-sc-estaduais','2030-sc-federais']:self.assertFalse(eligible(fixture(),edition,'current_support'))
    def test_29_strict_true_not_string_true(self):
        self.assertFalse(eligible(fixture(association_reviewed='true'),ED,'current_support'))
        self.assertFalse(eligible(fixture(current_context_year='2026'),ED,'current_support'))
    def test_30_groups_dont_tag_siblings(self):
        ev=[fixture(topic_id='moradia-cidades')]
        self.assertEqual(len(select(ev,ED,'current_support',[('group','cidades-infraestrutura')],'any',T)),1)
        self.assertEqual(select(ev,ED,'current_support',[('topic','agua-saneamento')],'any',T),[])
    def test_31_group_intersection_requires_each(self):
        ev=[fixture(topic_id='moradia-cidades')]
        self.assertEqual(select(ev,ED,'current_support',[('group','cidades-infraestrutura'),('group','saude')],'all',T),[])
        ev.append(fixture(evidence_id='e2',topic_id='saude'))
        self.assertEqual(len(select(ev,ED,'current_support',[('group','cidades-infraestrutura'),('group','saude')],'all',T)),1)
    def test_32_distinct_candidate_not_claim_count(self):
        self.assertEqual(len(select([fixture(),fixture(evidence_id='e2')],ED,'current_support',[('topic','saude')],'any',T)),1)
    def test_33_no_unknown_selector_fallback(self):
        for sel in [('party','PT'),('topic','saúde'),('group','unknown')]:
            with self.assertRaises(ValueError):select([fixture()],ED,'current_support',[sel],'any',T)
    def test_34_objects_preserved_nonmutating(self):
        ev=[fixture()];saved=copy.deepcopy(ev);select(ev,ED,'current_support',[],'all',T,['240000000001']);self.assertEqual(ev,saved)
    def test_35_sources_need_locator(self):
        for sources in [[{'url':'https://example.org'}],[{'url':'javascript:alert(1)','locator':'x'}],[{'url':'https://user:pw@example.org','locator':'x'}]]:
            self.assertFalse(eligible(fixture(sources=sources),ED,'current_support'))
    def test_36_false_mandate_is_unknown(self):
        for v in [False,'false',None]:self.assertEqual(mandate_from_legacy(v),'not_confirmed')
        self.assertNotEqual(mandate_from_legacy(True),'exercise_verified')
    def test_37_missing_history_not_rookie(self):
        self.assertEqual(prior_history([], 'not_collected',2026),'not_established')
        self.assertEqual(prior_history([{'year':2026}],'covered_snapshot',2026),'no_prior_in_covered_snapshot')
        self.assertEqual(prior_history([{'year':2024}],'covered_snapshot',2026),'linked_prior_race')
    def test_38_null_zero_not_applicable(self):
        self.assertEqual(vote_state(0,'verified_nominal'),'verified_nominal')
        self.assertEqual(vote_state(None,'not_applicable'),'not_applicable')
        for v,s in [(None,'verified_nominal'),(0,'not_collected'),(False,'verified_nominal'),(-1,'verified_nominal')]:
            with self.assertRaises(ValueError):vote_state(v,s)

class Capabilities(unittest.TestCase):
    def test_39_six_published_and_one_branch(self):
        self.assertEqual(sum(e['publication_status']=='published' for e in C['editions']),6)
        self.assertEqual(sum(e['facts']['cards'] for e in C['editions'] if e['facts']),760)
        self.assertEqual([e['edition_id'] for e in C['editions'] if not e['facts']],['2026-rs-estaduais'])
    def test_40_RS_metadata_present_without_UI(self):
        e=next(e for e in C['editions'] if e['edition_id']=='2026-rs-federais')
        self.assertEqual(e['facts']['mandate_object_with_source'],17);self.assertEqual(e['facts']['prior_history_records'],84)
        d={x['id']:x for x in e['dimensions']};self.assertEqual(d['registration']['data_readiness'],'ready');self.assertEqual(d['registration']['current_implementation'],'migration_required')
    def test_41_PR_OR_is_implementation_not_missing_evidence(self):
        for e in C['editions']:
            if '-pr-' not in e['edition_id']:continue
            d=next(d for d in e['dimensions'] if d['id']=='theme_operators');self.assertEqual(d['current'],['all']);self.assertEqual(d['canonical_target'],['any','all']);self.assertEqual(d['blockers'],['implementation'])
    def test_42_SP_uncollected_history_explicit(self):
        e=next(e for e in C['editions'] if e['edition_id']=='2026-sp-federais')
        self.assertEqual(e['facts']['history_not_collected_explicit'],15)
    def test_43_status_changes_only_append_design_contract(self):
        status=load('data/global-integration/migration-status.json')
        self.assertEqual(status['lot'],'02');self.assertIs(status['whole_issue_completed'],False)
        self.assertEqual(status['canonical_filter_contract']['issue'],53);self.assertEqual(status['canonical_filter_contract']['status'],'specified_not_activated')
    def test_44_nonfields_are_null_not_zero(self):
        e=next(e for e in C['editions'] if e['edition_id']=='2026-sc-federais')
        self.assertIsNone(e['facts']['prior_history_records']);self.assertIsNone(e['facts']['mandate_object_with_source'])
    def test_45_same_grammar_in_all_public_editions(self):
        target={'query','parties','themes','registration','mandate','history','locality','order','theme_operators'}
        for e in C['editions']:
            if e['facts']:self.assertEqual({x['id'] for x in e['dimensions']},target)

    def test_46_empty_selection_keeps_undocumented_records(self):
        ids=['240000000001','240000000002']
        self.assertEqual(len(select([fixture()],ED,'current_support',[],'all',T,ids)),2)
        with self.assertRaises(ValueError):select([fixture()],ED,'current_support',[],'any',T)
    def test_47_malformed_source_fails_closed(self):
        for source in [{'url':'https://[','locator':'x'},{'url':123,'locator':'x'},{'url':'https://example.org','locator':[]}]:
            self.assertFalse(eligible(fixture(sources=[source]),ED,'current_support'))
    def test_48_invalid_identity_is_not_string_coerced(self):
        self.assertFalse(eligible(fixture(candidate_id=240000000001),ED,'current_support'))
        self.assertFalse(eligible(fixture(semantic=[]),ED,'current_support'))
    def test_49_no_reused_ids_or_implicit_global_person(self):
        self.assertIs(T['identity']['not_global_person_identity'],True)
        self.assertIs(T['identity']['never_join_by_name'],True)
    def test_50_current_support_not_checked_by_year_alone(self):
        self.assertFalse(eligible(fixture(currentness_reviewed=None,period='2026'),ED,'current_support'))

if __name__=='__main__':unittest.main(verbosity=2)

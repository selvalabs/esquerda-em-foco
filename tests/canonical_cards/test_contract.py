"""Contract and source-preservation tests. Fictional fixtures stay in tests."""
import copy,json,sys,tempfile,unittest
from pathlib import Path
from bs4 import BeautifulSoup
import jsonschema
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/canonical_cards'))
from model import Repository,history_state,vote,mandate,safe_url,explicit_coverage,correction_view,sha,validate_observation,observed,jsha
from schema import schema
from render import enhance_card,original_signature,source_html,date_text
from build import editorial_variants,topic_labels

class Contracts(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.repo=Repository(ROOT);cls.data={e['edition_id']:(e,*cls.repo.models(e)) for e in cls.repo.editions()}
 def test_all_editions_are_public_only(self):
  self.assertEqual(len(self.data),6);self.assertNotIn('2026-rs-estaduais',self.data)
 def test_760_contextual_identities(self):
  models=[m for _,_,ms in self.data.values() for m in ms]
  self.assertEqual(len(models),760);self.assertEqual(len({m['key'] for m in models}),760)
  for m in models:self.assertEqual(m['key'],m['edition_id']+':'+m['candidate_id'])
 def test_schema_all_models(self):
  validator=jsonschema.Draft202012Validator(schema())
  for _,_,ms in self.data.values():
   for m in ms:validator.validate(m)
 def test_schema_no_new_activation(self):
  m=copy.deepcopy(self.data['2026-sc-federais'][2][0]);m['activation']='public'
  with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(m,schema())
 def test_no_global_political_membership_inferred(self):
  for _,_,ms in self.data.values():
   for m in ms:
    self.assertFalse(m['new_political_assertions']);self.assertFalse(m['coverage']['completion_inferred'])
    for ev in m['evidence']:self.assertFalse(ev['global_filter_activation'])
 def test_all_original_text_and_links_preserved(self):
  for e,doc,models in self.data.values():
   cards={c['id']:c for c in doc.select('article.candidate')};labels=topic_labels(ROOT,e)
   for m in models:
    c=cards['candidato-'+m['candidate_id']];before=original_signature(c)
    enhance_card(c,m,labels);after=original_signature(c);after['attrs'].pop('data-canonical-card',None)
    self.assertEqual(before,after,m['key'])
 def test_renderer_idempotence(self):
  e,doc,models=self.data['2026-sc-federais'];m=models[0];c=doc.select_one(m['original_card']['selector'])
  enhance_card(c,m,topic_labels(ROOT,e));before=str(c);enhance_card(c,m,topic_labels(ROOT,e));self.assertEqual(before,str(c))
 def test_sp_uncollected_is_not_first_election(self):
  ms=self.data['2026-sp-federais'][2]
  self.assertEqual(sum(m['history']['state']=='not_collected' for m in ms),15)
 def test_no_prior_requires_covered_snapshot(self):
  self.assertEqual(history_state([],'not_established',2026),'not_established')
  self.assertEqual(history_state([],'covered',2026),'no_prior_in_covered_snapshot')
 def test_current_election_is_not_prior(self):
  self.assertEqual(history_state([{'year':2026}],'covered',2026),'no_prior_in_covered_snapshot')
 def test_prior_race(self):
  self.assertEqual(history_state([{'year':2024}],'covered',2026),'linked_prior_race')
 def test_invalid_history_year_unknown(self):
  self.assertEqual(history_state([{'year':'2024'}],'covered',2026),'not_established')
 def test_verified_zero_is_zero(self):
  self.assertEqual(vote({'votes':0,'votes_status':'verified_nominal'})['state'],'verified_nominal')
 def test_null_not_coerced(self):
  self.assertIsNone(vote({'votes':None,'votes_status':'not_verified'})['value'])
 def test_na_not_coerced(self):
  self.assertEqual(vote({'votes':None,'votes_status':'not_applicable'})['state'],'not_applicable')
 def test_unverified_zero_rejected(self):
  with self.assertRaises(ValueError):vote({'votes':0,'votes_status':'not_applicable'})
 def test_verified_null_rejected(self):
  with self.assertRaises(ValueError):vote({'votes':None,'votes_status':'verified_nominal'})
 def test_negative_votes_rejected(self):
  with self.assertRaises(ValueError):vote({'votes':-1,'votes_status':'verified_nominal'})
 def test_bool_votes_rejected(self):
  with self.assertRaises(ValueError):vote({'votes':False,'votes_status':'verified_nominal'})
 def test_number_alone_not_verification(self):
  self.assertEqual(vote({'votes':0})['state'],'reported_unclassified')
 def test_source_backed_nominal(self):
  self.assertEqual(vote({'votes':0,'vote_type':'nominal','votes_source':'https://example.org/x'})['state'],'documented_nominal')
 def test_not_published_not_inapt_zero(self):
  self.assertEqual(vote({'votes':None,'votes_status':'not_published_inapt'})['state'],'not_published_inapt')
 def test_false_mandate_is_unknown(self):
  self.assertEqual(mandate({'mandate_documented':False},'2026-sc-estaduais')['state'],'not_confirmed')
 def test_self_declared_mandate_kept(self):
  self.assertEqual(mandate({'mandate_state':'declarado','mandate_source':'https://example.org'},'2026-sc-estaduais')['state'],'self_declared')
 def test_leave_is_not_exercise(self):
  self.assertEqual(mandate({'mandate_state':'licenciado','mandate_source':'https://example.org'},'2026-sc-estaduais')['state'],'leave_documented')
 def test_mandate_without_source_not_verified(self):
  self.assertEqual(mandate({'current_office':{'label':'Exemplo'}},'2026-rs-federais')['state'],'not_confirmed')
 def test_role_observation_not_universal_exercise(self):
  self.assertEqual(mandate({'current_role_observation':{'source':'https://example.org','label':'Titular'}},'2026-sp-federais')['state'],'source_backed_observation')
 def test_status_coverage_not_completion(self):
  for status,result in [('research_pending','not_reviewed'),('source_access_blocked','blocked'),('individual_sources_reviewed_insufficient','insufficient'),('not_located','not_located'),('not_applicable','not_applicable'),('strange','not_established')]:self.assertEqual(explicit_coverage(status),result)
 def test_sc_wording_and_research_dates_separate(self):
  m=self.data['2026-sc-federais'][2][0];self.assertEqual(m['coverage']['review_date'],'2026-09-21');self.assertEqual(m['observations']['wording_date']['value'],'2026-09-22')
 def test_source_consultation_never_becomes_publication(self):
  from model import source_view
  s=source_view({'url':'https://example.org','consulted_at':'2026-09-21'},'test');self.assertIsNone(s['published_at'])
 def test_sp_act_not_current_support(self):
  for m in self.data['2026-sp-federais'][2]:
   for ev in m['evidence']:self.assertEqual(ev['semantic'],'documented_topic')
 def test_rs_pr_summary_not_sentence_level(self):
  for eid,(e,doc,ms) in self.data.items():
   if e['state'] not in ('RS','PR'):continue
   for m in ms:
    for ev in m['evidence']:self.assertEqual(ev['granularity'],'whole_synthesis');self.assertEqual(ev['semantic'],'legacy_context')
 def test_sources_resolve_per_claim(self):
  for _,_,ms in self.data.values():
   for m in ms:
    for ev in m['evidence']:
     self.assertTrue(ev['provenance'])
     for s in ev['sources']:self.assertTrue(s['source_key'].startswith(m['key']+':source:'));self.assertIn('ref',s['provenance'])
 def test_unsafe_urls_rejected(self):
  for s in ['javascript:alert(1)','data:text/html,foo','https://a:b@example.org','//example.org',None]:self.assertIsNone(safe_url(s))
 def test_safe_urls_preserve_value(self):self.assertEqual(safe_url('https://example.org/a#b'),'https://example.org/a#b')
 def test_html_escaping_source_title(self):
  s={'url':'https://example.org','title':'<script>x</script>','published_at':None,'consulted_at':None,'locator':None}
  self.assertNotIn('<script>',source_html(s));self.assertIn('&lt;script&gt;',source_html(s))
 def test_date_display_no_new_day(self):self.assertEqual(date_text('2026-09-21T01:00:00+00:00'),'21/09/2026')
 def test_variant_ledger_exists_for_each_card(self):
  for e,_,ms in self.data.values():self.assertEqual(len(editorial_variants(self.repo,e,ms)),len(ms))
 def test_sc_versions_both_preserved(self):
  e,_,ms=self.data['2026-sc-federais']
  for row in editorial_variants(self.repo,e,ms):self.assertEqual(len(row['variants']),2)
 def test_rs_superseded_not_reinstated(self):
  e,_,ms=self.data['2026-rs-federais'];rows=editorial_variants(self.repo,e,ms)
  changed=[v for r in rows for v in r['variants'] if v.get('changed_in_later_review')]
  self.assertTrue(changed)
  for v in changed:self.assertEqual(v['decision'],'do_not_reinstate_superseded_assertions_without_individual_review')
 def test_correction_cannot_restore_withdrawn_claim(self):
  raw={'candidate_id':'999999999991','action':'withdraw_unconfirmed_individual_activity','reason':'Exemplo sintético de vínculo insuficiente','previous_record':{'text':'Texto anterior de teste'},'checked_at':'2026-09-21'}
  c=correction_view(raw,'999999999991');self.assertFalse(c['counts_as_current_evidence']);self.assertEqual(c['previous_record'],raw['previous_record'])
 def test_foreign_correction_rejected(self):
  with self.assertRaises(ValueError):correction_view({'candidate_id':'999999999991'},'999999999992')
 def test_tampered_observation_rejected(self):
  o=copy.deepcopy(self.data['2026-sc-estaduais'][2][0]['observations']['name']);o['value']='wrong'
  with self.assertRaises(ValueError):validate_observation(ROOT,o)
 def test_one_real_source_locator(self):
  o=self.data['2026-sc-estaduais'][2][0]['observations']['name'];validate_observation(ROOT,o)
 def test_observation_no_raw_sensitive_fields(self):
  # Exports already public; the envelope does not introduce raw private fields.
  for _,_,ms in self.data.values():
   for m in ms:self.assertNotIn('cpf',m);self.assertNotIn('email',m['identity'])

if __name__=='__main__':unittest.main()

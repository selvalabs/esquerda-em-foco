"""Round-three regression tests; documentary coverage is not a political rating."""
import collections,copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/rs'))
from fed03_support import new_editorial,extend_history,validate_registry
from fed03_install import run as install

def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
class Fed03Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cs=read('rs/deputados-federais/dados.json')['candidates'];cls.by={c['id']:c for c in cls.cs};cls.report=read('docs/rs/fed03/final-report.json');cls.additions=new_editorial()
 def test_target_research_is_not_total_completeness(self):
  target={t['id'] for t in read('data/rs/rs-fed-03-targets.json')['targets']};log=read('docs/rs/fed03/research-log.json')
  self.assertEqual(len(target),63);self.assertEqual(set(log),target);self.assertEqual(sum(len(r['queries']) for r in log.values()),120)
  self.assertFalse(self.report['editorial_complete']);self.assertFalse(self.report['all_profiles_complete'])
 def test_new_summary_and_policy_counts_are_distinct(self):
  self.assertEqual(len(self.additions),20);self.assertEqual(self.report['with_summary'],65);self.assertEqual(self.report['with_documented_policy_or_action'],64)
  self.assertEqual(self.report['without_summary'],42);self.assertEqual(self.report['without_policy_or_action'],43);self.assertEqual(self.report['trajectory_only_summaries'],1)
  before=read('docs/rs/review/final-report.json');self.assertEqual(before['with_summary'],46);self.assertEqual(before['with_documented_policy_or_action'],44)
  self.assertEqual(self.report['with_summary']-before['with_summary'],19)
 def test_biographies_do_not_automatically_create_policies(self):
  for cid in ('210002534605','210002533916'):
   self.assertTrue(self.by[cid]['biography']);self.assertFalse(self.by[cid]['pautas']);self.assertFalse(self.by[cid]['topics'])
  self.assertEqual(self.report['with_biography'],24)
 def test_csv_and_profile_refresh_are_not_conflated(self):
  self.assertEqual(len(validate_registry()),107);self.assertEqual(self.report['registry_csv_reconciled'],107)
  self.assertEqual(self.report['individual_tse_profiles_rechecked'],0);self.assertEqual(self.report['profile_access_failures'],107)
  self.assertFalse(any(r['profile_rechecked_this_round'] for r in read('docs/rs/fed03/candidate-matrix.json')))
 def test_vicente_reviewed_particle_exception_only(self):
  h=next(h for h in self.by['210002535917']['history'] if h['year']==2006 and h['candidate_id']=='10178')
  self.assertEqual(h['votes'],15473);self.assertEqual(h['votes_status'],'verified_nominal');self.assertIn('152',h['votes_match_method']);self.assertNotIn('votes_note',h)
 def test_claudia_conflicts_do_not_assign_other_records_votes(self):
  for year in (2004,2008):
   h=next(h for h in self.by['210002537042']['history'] if h['year']==year)
   self.assertIsNone(h['votes']);self.assertEqual(h['votes_status'],'not_verified');self.assertIn('divergência',h['votes_note'])
 def test_inapt_historical_absences_are_not_zero_or_current_status(self):
  rows=[(c,h) for c in self.cs for h in c['history'] if h['votes_status']=='not_published_inapt'];self.assertEqual(len(rows),5)
  for c,h in rows:
   self.assertIsNone(h['votes']);self.assertLess(h['year'],2026);self.assertIn('não equivale a zero',h['votes_note']);self.assertEqual(c['status'],'Deferido')
   self.assertTrue(h['votes_context_source'].startswith('https://cdn.tse.jus.br/'));self.assertTrue(h['votes_absence_source'].startswith('https://cdn.tse.jus.br/'))
 def test_vote_resolution_counts_are_not_eight_values_recovered(self):
  r=read('docs/rs/fed03/votes-resolution.json');self.assertEqual(len(r['records']),8)
  self.assertEqual(r['counts'],{'nominal_value_recovered':1,'historical_inapt_no_nominal_row':5,'identity_conflict_pending':2})
  counts=collections.Counter(h['votes_status'] for c in self.cs for h in c['history'])
  self.assertEqual(counts,{'verified_nominal':277,'not_published_inapt':5,'not_verified':2,'not_applicable':21,'not_yet_held':107})
 def test_new_sources_have_explicit_period_and_locator(self):
  for cid,e in self.additions.items():
   self.assertEqual(e['pautas'],self.by[cid]['pautas']);self.assertNotEqual(e['summary_kind'],'trajectory')
   for s in e['sources']:
    for key in ('url','label','period','locator','source_type','checked_at'):self.assertTrue(s.get(key),(cid,key))
 def test_rafa_directory_is_distinct_from_historical_profile(self):
  e=self.by['210002535907']['current_office'];self.assertEqual(e['source_updated_at'],'2025-01-16');self.assertTrue(e['identity_source'].endswith('/69'));self.assertEqual(e['supporting_source_date'],'2026-04-14')
  self.assertEqual(self.report['with_current_office'],17)
 def test_original_editorial_sources_and_biographies_preserved(self):
  before=read('data/rs/editorial-baseline.json');after=read('data/rs/editorial.json')
  for cid,e in before.items():
   self.assertIn(cid,after)
   if cid not in self.additions and e.get('biography'):self.assertTrue(after[cid].get('biography'))
 def test_old_round_reports_remain_historical(self):
  before=read('docs/rs/review/final-report.json');self.assertEqual(before['with_summary'],46);self.assertEqual(before['vote_rows']['verified_nominal'],276)
  sources=read('rs/deputados-federais/fontes.json');self.assertEqual(sources['round_two_review'],before);self.assertEqual(sources['round_three_review'],self.report)
 def test_install_is_idempotent(self):
  ps=[ROOT/p for p in ('tools/rs/review_support.py','tests/rs/test_review.py','tests/rs/test_build.py')];before={p:p.read_bytes() for p in ps};install();self.assertTrue(all(p.read_bytes()==before[p] for p in ps))
 def test_history_layer_is_idempotent(self):
  hs={c['id']:copy.deepcopy(c['history']) for c in self.cs};before=copy.deepcopy(hs);extend_history(hs);self.assertEqual(hs,before)
 def test_report_counts_match_actual_records(self):
  self.assertEqual(self.report['with_verified_votes'],sum(any(h['votes_status']=='verified_nominal' for h in c['history']) for c in self.cs))
  self.assertEqual(self.report['with_summary'],sum(bool(c['pautas']) for c in self.cs));self.assertEqual(self.report['candidate_count'],len(self.cs))
if __name__=='__main__':unittest.main()

"""Operational reconciliation rules, including deliberately absent research."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('d5',ROOT/'tools/global_reconciliation/reconcile.py');d5=importlib.util.module_from_spec(spec);spec.loader.exec_module(d5)
class Contract(unittest.TestCase):
 def setUp(self):
  self.report=json.loads((ROOT/d5.REPORT).read_text());self.registry=json.loads((ROOT/'config/editions.json').read_text())
 def test_all_original_capabilities_reconciled(self):
  self.assertEqual(len(self.report['rows']),6)
  for r in self.report['rows']:self.assertEqual({c['id'] for c in r['capabilities']},set(d5.REASONS))
 def test_registry_matches_operational_decisions(self):
  for row in self.report['rows']:
   e=next(e for e in self.registry['editions'] if e['edition_id']==row['edition_id'])
   for c in row['capabilities']:self.assertEqual(e['capabilities'][c['id']]['state'],c['state'])
   for scope in d5.SCOPES:self.assertEqual(e['capabilities'][scope]['state'],row['scopes'][scope]['state'])
 def test_source_panels_do_not_invent_sc_state_membership(self):
  row=next(r for r in self.report['rows'] if r['edition_id']=='2026-sc-estaduais')
  self.assertGreater(row['evidence_panels'],0)
  self.assertTrue(all(s['state']=='blocked_data' for s in row['scopes'].values()))
 def test_rs_pr_context_not_current_support(self):
  for row in self.report['rows']:
   if row['edition_id'].startswith(('2026-rs-','2026-pr-')):
    self.assertEqual(row['scopes']['current_support']['state'],'blocked_data')
    self.assertEqual(row['scopes']['legacy_context']['state'],'ready')
 def test_ready_dimension_has_no_blocking_reason(self):
  for row in self.report['rows']:
   for d in row['dimensions']:
    if d['state']=='ready':self.assertIsNone(d['blocking_reason'])
    else:self.assertTrue(d['blocking_reason'])
 def test_locality_only_where_source_exists(self):
  for row in self.report['rows']:
   dim=next(d for d in row['dimensions'] if d['id']=='region')
   self.assertEqual(dim['state']=='ready',row['edition_id'].startswith('2026-pr-'))
 def test_global05_not_claimed_complete(self):
  for row in self.report['rows']:
   caps={c['id']:c for c in row['capabilities']}
   for code in ('Q02','Q04'):
    self.assertEqual(caps[code]['disposition'],'pending_global05');self.assertEqual(caps[code]['followup_issue'],44)
 def test_identity_count_and_unpublished_excluded(self):
  self.assertEqual(sum(r['cards'] for r in self.report['rows']),760)
  self.assertEqual(self.report['unpublished'],['2026-rs-estaduais'])
 def test_policy_without_any_evidence_is_blocked(self):
  cfg={'dimensions':[{'id':k,'state':'blocked_data'} for k in d5.LABELS],
       'available':{k:[] for k in d5.SCOPES}}
  s=d5.states(cfg);self.assertEqual(s['D05'],'blocked_data');self.assertEqual(s['E03'],'blocked_data')
  self.assertEqual(s['D07'],'ready')
 def test_fifty_remains_outside_scope(self):
  self.assertTrue(any(x['issue']==50 for x in self.report['deferred']))
 def test_real_html_matches_capability_inspection(self):
  for row in self.report['rows']:
   e=next(e for e in self.registry['editions'] if e['edition_id']==row['edition_id'])
   actual=d5.inspect(ROOT,e,e)
   self.assertEqual(actual['html_sha256'],row['html_sha256']);self.assertEqual(actual['scopes'],row['scopes'])
if __name__=='__main__':unittest.main()

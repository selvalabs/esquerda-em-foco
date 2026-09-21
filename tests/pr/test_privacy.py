"""Public contacts are minimized without changing the electoral population."""
import importlib.util,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('privacy',ROOT/'tools/pr/privacy.py');privacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(privacy)
class ContactMinimization(unittest.TestCase):
 def test_declared_fields_have_no_direct_emails(self):
  rows=json.loads((ROOT/'data/pr/social-official.json').read_text());profiles=json.loads((ROOT/'data/pr/profiles-official.json').read_text())
  values=[r.get('DS_URL','')for r in rows]+[s for p in profiles.values() for s in p.get('data',{}).get('sites',[])]
  self.assertFalse(any(privacy.EMAIL.search(s) for s in values if isinstance(s,str)))
  self.assertEqual(len(profiles),249)
 def test_redaction_ledger_contains_only_hashes(self):
  report=json.loads((ROOT/'docs/pr/privacy.json').read_text())
  self.assertEqual(set(report['files']),{'social-official.json','profiles-official.json'})
  for file in report['files'].values():
   for digest in file['removed_value_sha256']:self.assertRegex(digest,r'^[a-f0-9]{64}$')

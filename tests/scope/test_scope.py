from __future__ import annotations
import json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class Scope(unittest.TestCase):
    def test_canonical_scope_is_single_for_both_offices(self):
        c=json.loads((ROOT/'config/party-scope-2026.json').read_text())
        self.assertEqual(c['parties'],['PCB','PCdoB','PCO','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP'])
        self.assertEqual(set(c['offices']),{'6','7'})
    def test_audit_covers_all_states_and_offices(self):
        a=json.loads((ROOT/'docs/methodology/party-scope-audit.json').read_text())
        self.assertEqual(set(a['states']),{'SC','RS','PR'})
        for state in a['states'].values():
            self.assertEqual(set(state['offices']),{'6','7'})
            for office in state['offices'].values():
                self.assertEqual(set(office['official_by_party']),set(a['canonical_scope']['parties']))
                self.assertEqual(set(office['project_by_party']),set(a['canonical_scope']['parties']))
                self.assertEqual(office['official_canonical_total'],sum(office['official_by_party'].values()))
    def test_zero_is_explicit(self):
        a=json.loads((ROOT/'docs/methodology/party-scope-audit.json').read_text())
        for state in a['states'].values():
            for office in state['offices'].values():
                self.assertEqual(len(office['official_by_party']),11)
if __name__=='__main__':unittest.main(verbosity=2)

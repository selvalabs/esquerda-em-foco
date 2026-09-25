"""Do not confuse a vote-table municipality with a statewide constituency."""
from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

class ElectoralUnits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=ROOT/'tools/rs-estaduais/phase2_votes.py'
        spec=importlib.util.spec_from_file_location('unit_mapping_tests',path)
        cls.module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_identical_electoral_units_need_no_compatibility_rule(self):
        actual=self.module.source_electoral_unit({'SG_UE':'88013'},{'SG_UE':'88013'})
        self.assertEqual(actual,('88013','same_electoral_unit'))

    def test_2010_statewide_deputy_rows_keep_state_constituency(self):
        row={'ANO_ELEICAO':'2010','SG_UE':'88986','CD_MUNICIPIO':'88986','SG_UF':'RS','CD_CARGO':'7'}
        expected={'SG_UE':'RS','CD_CARGO':'7'}
        self.assertEqual(self.module.source_electoral_unit(row,expected),('RS','municipal_grain_2010_statewide_deputy'))

    def test_compatibility_rule_does_not_cross_year_office_or_uf(self):
        row={'ANO_ELEICAO':'2010','SG_UE':'88986','CD_MUNICIPIO':'88986','SG_UF':'RS','CD_CARGO':'7'}
        expected={'SG_UE':'RS','CD_CARGO':'7'}
        for patch in ({'ANO_ELEICAO':'2004'},{'SG_UF':'SC'},{'CD_CARGO':'13'},{'CD_MUNICIPIO':'85014'},{'SG_UE':'XX'}):
            with self.subTest(patch=patch):
                self.assertIsNone(self.module.source_electoral_unit({**row,**patch},expected)[0])
        self.assertIsNone(self.module.source_electoral_unit(row,{'SG_UE':'88013','CD_CARGO':'7'})[0])

    def test_real_source_retains_raw_municipality_and_effective_constituency(self):
        source=json.loads((ROOT/'data/rs-estaduais/votes-phase2.json').read_text())['2010']
        self.assertGreater(source['source_unit_basis_counts']['municipal_grain_2010_statewide_deputy'],0)
        self.assertTrue(source['source_unit_examples'])
        for example in source['source_unit_examples']:
            self.assertEqual(example['raw_sg_ue'],example['cd_municipio'])
            self.assertEqual(example['sg_uf'],'RS')
            self.assertEqual(example['effective_constituency'],'RS')
            self.assertIn(example['office_code'],('6','7'))

if __name__=='__main__':unittest.main()

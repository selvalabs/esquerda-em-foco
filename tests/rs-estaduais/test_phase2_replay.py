"""Regression tests for replaying phase-1 additions after phase-2 enrichment."""
from __future__ import annotations
import copy
import importlib.util
import json
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'

def mod(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value

class Replay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.legacy=mod('legacy_replay_test',ROOT/'tools/rs-estaduais/finalize_sources.py')
        cls.phase2=mod('phase2_replay_test',ROOT/'tools/rs-estaduais/phase2_apply.py')

    def test_earlier_null_preserves_later_verified_text(self):
        base={'example':{'pautas':'Texto posteriormente revisado','sources':[]}}
        patch={'example':{'pautas':None,'reviewed':True,'checked_at':'2026-09-21','sources':[{'url':'https://example.org/review-fixture'}]}}
        retained=self.legacy.apply(base,patch,{'example'})
        self.assertEqual(base['example']['pautas'],'Texto posteriormente revisado')
        self.assertEqual(retained[0]['field'],'pautas')

    def test_conflicting_nonempty_text_still_fails(self):
        base={'example':{'pautas':'Texto posteriormente revisado','sources':[]}}
        patch={'example':{'pautas':'Texto divergente','reviewed':True,'checked_at':'2026-09-21','sources':[{'url':'https://example.org/review-fixture'}]}}
        with self.assertRaisesRegex(ValueError,'Conflicting reviewed text'):
            self.legacy.apply(base,patch,{'example'})

    def test_full_editorial_replay_preserves_current_record(self):
        editorial=json.loads((D/'editorial.json').read_text())
        offices=json.loads((D/'offices-verified.json').read_text())
        expected=copy.deepcopy((editorial,offices))
        identities={r['SQ_CANDIDATO']:r for r in json.loads((D/'candidates-official.json').read_text())}
        old=json.loads((D/'editorial-additions.json').read_text())
        patches,_=self.phase2.batches('phase2-editorial')
        office_patches,_=self.phase2.batches('phase2-offices')
        for _ in range(2):
            self.legacy.apply(editorial,old,set(identities))
            self.phase2.apply(editorial,offices,patches,office_patches,identities)
        self.assertEqual((editorial,offices),expected)

if __name__=='__main__':unittest.main()

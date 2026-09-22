"""Offline integrity and negative-case tests for the SP documentary dataset."""
from __future__ import annotations
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('sp_round_b_build', Path('tools/sp/round_b/build.py'))
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

class RoundBTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = build.load('data/sp/normalized.json')
        cls.data = build.load(build.OUT/'normalized.json')
        cls.sources = build.load(build.OUT/'sources.json')
        cls.evidence = build.load(build.OUT/'evidence.json')
        cls.records = build.read_editorial(build.OUT/'inputs')
        cls.ids = {c['id'] for c in cls.base['candidates']}
        cls.topics = {t['id'] for t in build.load(build.OUT/'taxonomy.json')['topics']}
        cls.example_id = next(cid for cid,r in cls.records.items() if r.get('biography') and r.get('claims'))
        cls.example = cls.records[cls.example_id]

    def mutation_rejected(self, edit):
        record = copy.deepcopy(self.example)
        edit(record)
        with self.assertRaises(ValueError):
            build.validate_editorial({self.example_id:record},self.ids,self.topics)

    def test_real_editorial_inputs(self):
        build.validate_editorial(self.records,self.ids,self.topics)

    def test_unknown_candidate_rejected(self):
        with self.assertRaises(ValueError):
            build.validate_editorial({'000000000000':self.example},self.ids,self.topics)

    def test_unknown_topic_rejected(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(topic_id='invented-topic'))

    def test_unsourced_claim_rejected(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(source_id='missing-source'))

    def test_unknown_direction_rejected(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(position='best-candidate'))

    def test_current_date_required(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(temporal='dated_2026',event_date=None))

    def test_historical_date_is_not_current(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(temporal='dated_historical',event_date='2026-01-01'))

    def test_no_automatic_support_filter(self):
        self.mutation_rejected(lambda r:r['claims'][0].update(current_support_filter_eligible=True))

    def test_unsourced_biography_rejected(self):
        self.mutation_rejected(lambda r:r['biography'].update(source_ids=[]))

    def test_unresolved_identity_rejected(self):
        self.mutation_rejected(lambda r:r.update(identity_status='needs_confirmation'))

    def test_future_source_date_rejected(self):
        self.mutation_rejected(lambda r:r['sources'][0].update(publication_date='2027-01-01'))

    def test_duplicate_source_ids_rejected(self):
        self.mutation_rejected(lambda r:r['sources'].append(copy.deepcopy(r['sources'][0])))

    def test_duplicate_input_candidate_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            d=Path(folder)
            value={'as_of':build.AS_OF,'candidates':{self.example_id:self.example}}
            for name in ['a.json','b.json']:(d/name).write_text(json.dumps(value))
            with self.assertRaises(ValueError):build.read_editorial(d)

    def test_null_markers_not_zero(self):
        for marker in ['#NE','#NE#','#NULO','#NULO#','-1','-3','-4',None,'']:
            self.assertIsNone(build.meaningful(marker))
        self.assertEqual(build.meaningful('0'),'0')

    def test_history_excludes_current_election(self):
        history=build.load(build.OUT/'history-official.json')
        metadata=build.load(build.OUT/'collection.json')['sources']['history']
        result,current=build.normalize_history(history,metadata)
        self.assertEqual(current,81)
        self.assertEqual(len(result),176)
        self.assertEqual(sum(map(len,result.values())),555)
        self.assertTrue(all(h['year']<2026 and h['votes'] is None for group in result.values() for h in group))

    def test_duplicate_history_rejected(self):
        rows=build.load(build.OUT/'history-official.json')
        row=next(r for r in rows if int(r['ANO_ELEICAO'])<2026)
        metadata=build.load(build.OUT/'collection.json')['sources']['history']
        with self.assertRaises(ValueError):build.normalize_history([row,row],metadata)

    def test_official_photos_have_matching_hashes(self):
        photos=build.load(build.OUT/'photos.json')
        self.assertEqual(set(photos),self.ids)
        for cid,photo in photos.items():
            raw=Path(photo['path']).read_bytes()
            self.assertEqual(build.digest(raw),photo['sha256'])
            self.assertTrue(raw.startswith(b'\xff\xd8\xff') or raw.startswith(b'\x89PNG\r\n\x1a\n'))

    def test_dataset_relations_and_core_preservation(self):
        self.assertTrue(build.audit_dataset(self.data,self.base,self.evidence,self.sources,self.topics))

    def test_mutated_candidate_number_rejected(self):
        value=copy.deepcopy(self.data);value['candidates'][0]['number']='9999'
        with self.assertRaises(ValueError):build.audit_dataset(value,self.base,self.evidence,self.sources,self.topics)

    def test_unsourced_documentary_topic_rejected(self):
        value=copy.deepcopy(self.data);value['candidates'][0]['documented_topic_ids'].append('tributacao')
        with self.assertRaises(ValueError):build.audit_dataset(value,self.base,self.evidence,self.sources,self.topics)

    def test_all_individual_tse_identities_checked(self):
        profiles=build.load(build.OUT/'divulgacand-profiles.json')
        self.assertEqual(set(profiles),self.ids)
        for c in self.base['candidates']:
            profile=profiles[c['id']]
            self.assertTrue(profile['identity_verified'])
            self.assertEqual(str(profile['numero']),c['number'])
            self.assertEqual(build.fold(profile['nomeCompleto']),build.fold(c['full_name']))

    def test_partial_editorial_is_not_technical_completion(self):
        audit=build.load(build.DOC/'audit.json')
        self.assertEqual(audit['technical_gate'],'PASS')
        self.assertEqual(audit['editorial_gate'],'PARTIAL')
        self.assertEqual(audit['publication_gate'],'NOT_READY')
        self.assertEqual(audit['counts']['individual_research_entries'],len(self.records))
        self.assertEqual(audit['counts']['candidates_without_individual_editorial_review'],234-len(self.records))

    def test_renunciations_preserved(self):
        self.assertEqual(sum(c['status']=='RENÚNCIA' for c in self.data['candidates']),6)

    def test_source_and_evidence_ids_unique(self):
        self.assertEqual(len({s['id'] for s in self.sources}),len(self.sources))
        self.assertEqual(len({e['id'] for e in self.evidence}),len(self.evidence))

if __name__ == '__main__':
    unittest.main(verbosity=2)

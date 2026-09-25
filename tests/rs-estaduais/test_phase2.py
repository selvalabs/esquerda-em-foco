"""Regression tests for A-D enrichment; not a claim of final E/F review."""
from __future__ import annotations
import copy,importlib.util,json,subprocess,unittest
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais/phase2'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
class PhaseTwo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=load(D/'normalized.json')['candidates'];cls.raw={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json')}
        cls.history=load(D/'history-normalized.json');cls.baseline=load(A/'baseline.json')
        cls.apply_module=module('phase2_apply_test',ROOT/'tools/rs-estaduais/phase2_apply.py')
        cls.votes_module=module('phase2_votes_test',ROOT/'tools/rs-estaduais/phase2_votes.py')
    def test_original_census_unchanged(self):
        additions={'210002533927','210002533932','210002544838','210002544839'}
        self.assertEqual(len(self.records),self.baseline['candidate_count']+len(additions))
        self.assertTrue(additions.issubset({c['id'] for c in self.records}))
        # The canonical correction initially lacked policy evidence. Later research
        # may fill that gap, but must carry a reviewed individual source.
        editorial=load(D/'editorial.json')
        for cid in additions:
            c=next(c for c in self.records if c['id']==cid)
            if c['pautas']:
                self.assertTrue(editorial[cid]['reviewed']);self.assertTrue(c['editorial_sources']);self.assertTrue(c['editorial_checked_at'])
        self.assertEqual({c['id'] for c in self.records},set(self.raw))
        self.assertEqual(len(self.baseline['policy_gap_ids']),115);self.assertEqual(self.baseline['policy_summaries'],30);self.assertEqual(self.baseline['historical_vote_rows'],326)
    def test_all_old_year_sources_have_context_revalidation(self):
        sources=load(D/'votes-phase2.json');self.assertEqual(set(sources),{'2004','2006','2008','2010'})
        for year,source in sources.items():
            self.assertEqual(source['matching_version'],2,year);self.assertIsNone(source['archive_sha256'])
            self.assertRegex(source['member_sha256'],r'^[a-f0-9]{64}$');self.assertGreater(source['member_bytes'],0)
            self.assertEqual(set(source['totals']),set(source['contexts']))
    def test_old_votes_match_linked_electoral_unit_and_office(self):
        raw={(r['SQ_CANDIDATO_ATUAL'],int(r['ANO_ELEICAO']),r['SQ_CANDIDATO'],int(r['NR_TURNO'])):r for r in load(D/'history-official.json')}
        sources=load(D/'votes-phase2.json')
        for cid,rows in self.history.items():
            for h in rows:
                if str(h['year']) not in sources or h.get('votes') is None:continue
                expected=raw[(cid,h['year'],h['candidate_id'],h['round'])];source=sources[str(h['year'])]
                key=h['candidate_id']+':'+str(h['round']);ctx=source['contexts'][key]
                self.assertEqual(ctx['electoral_unit'],expected['SG_UE']);self.assertEqual(ctx['office_code'],expected['CD_CARGO'])
                self.assertEqual(ctx['ballot_number'],expected['NR_CANDIDATO']);self.assertEqual(ctx['year'],h['year']);self.assertEqual(ctx['round'],h['round'])
                self.assertEqual(ctx['uf'],'RS');self.assertEqual(source['totals'][key],h['votes'])
    def test_reused_2004_ids_excluded(self):
        source=load(D/'votes-phase2.json')['2004'];self.assertGreater(source['excluded_reused_id_rows'],0);self.assertEqual(len(source['totals']),19)
    def test_every_past_row_has_explicit_vote_status(self):
        allowed={'verified_nominal','source_has_no_matching_record','source_collection_failed_or_unavailable','not_applicable_vice_ticket','not_applicable_supplemental_ticket','national_or_other_uf_not_collected','round_not_confirmed','office_not_mapped'}
        rows=[h for hs in self.history.values() for h in hs if h['year']<2026]
        self.assertEqual(len(rows),sum(load(A/'votes-summary.json')['by_status'].values()))
        for h in rows:
            self.assertIn(h['votes_status'],allowed);self.assertEqual(h['votes_status']=='verified_nominal',h.get('votes') is not None)
        self.assertEqual(dict(Counter(h['votes_status'] for h in rows)),load(A/'votes-summary.json')['by_status'])
    def test_ticket_and_other_population_votes_never_assigned(self):
        extra=load(D/'ad2-vote-index.json') if (D/'ad2-vote-index.json').exists() else {}
        for cid,hs in self.history.items():
            for h in hs:
                if h['year']>=2026:self.assertIsNone(h.get('votes'));continue
                reason=self.votes_module.reason(h)
                if not reason:continue
                if h.get('votes_evidence_id'):
                    evidence=extra[h['votes_evidence_id']];ctx=evidence['context']
                    self.assertEqual(reason,'national_or_other_uf_not_collected')
                    self.assertEqual(evidence['current_candidate_id'],cid);self.assertEqual(ctx['office_code'],'1')
                    self.assertEqual(ctx['electoral_unit'],'BR');self.assertEqual(h['uf'],'BR')
                    self.assertTrue(evidence['member'].upper().endswith('_BR.CSV'))
                    self.assertEqual(ctx['year'],h['year']);self.assertEqual(ctx['round'],h['round']);self.assertEqual(ctx['candidate_id'],h['candidate_id'])
                    self.assertEqual(h['votes'],evidence['votes'])
                else:self.assertIsNone(h.get('votes'),(h['year'],h['office']))
    def test_coverage_report_matches_real_history(self):
        report=load(ROOT/'docs/rs-estaduais/votes-coverage.json')
        self.assertEqual(report['historical_rows_with_votes'],sum(h['year']<2026 and h.get('votes') is not None for rows in self.history.values() for h in rows))
        self.assertEqual(report['candidates_with_past_votes'],sum(any(h['year']<2026 and h.get('votes') is not None for h in rows) for rows in self.history.values()))
    def test_phase2_identities_and_source_dates(self):
        patches,_=self.apply_module.batches('phase2-editorial')
        for cid,patch in patches.items():
            self.assertEqual(self.apply_module.norm(patch['expected_name']),self.apply_module.norm(self.raw[cid]['NM_URNA_CANDIDATO']))
            self.assertTrue(patch['reviewed']);self.apply_module.valid_date(patch['checked_at'])
            for source in patch['sources']:
                self.assertTrue(source['locator']);self.assertTrue(source['type']);self.apply_module.valid_url(source['url'])
                if source.get('published_at'):self.apply_module.valid_date(source['published_at'])
    def test_phase2_merge_is_idempotent(self):
        editorial=load(D/'editorial.json');offices=load(D/'offices-verified.json');original=copy.deepcopy((editorial,offices))
        patches,_=self.apply_module.batches('phase2-editorial');office_patches,_=self.apply_module.batches('phase2-offices')
        self.apply_module.apply(editorial,offices,patches,office_patches,self.raw);self.apply_module.apply(editorial,offices,patches,office_patches,self.raw)
        self.assertEqual((editorial,offices),original)
    def test_wrong_candidate_identity_rejected(self):
        patches,_=self.apply_module.batches('phase2-editorial');cid=next(iter(patches));patch=copy.deepcopy(patches[cid]);patch['expected_name']='IDENTIDADE DIVERGENTE PARA TESTE'
        with self.assertRaisesRegex(ValueError,'identity mismatch'):self.apply_module.apply({}, {}, {cid:patch}, {}, self.raw)
    def test_future_source_rejected(self):
        patches,_=self.apply_module.batches('phase2-editorial');cid=next(iter(patches));patch=copy.deepcopy(patches[cid]);patch['sources'][0]['published_at']='2026-09-22'
        with self.assertRaisesRegex(ValueError,'beyond declared cutoff'):self.apply_module.apply({}, {}, {cid:patch}, {}, self.raw)
    def test_conflicting_summary_rejected(self):
        patches,_=self.apply_module.batches('phase2-editorial');cid=next(k for k,v in patches.items() if v.get('pautas'))
        with self.assertRaisesRegex(ValueError,'Conflicting reviewed pautas'):self.apply_module.apply({cid:{'pautas':'Conteúdo de teste que deve ser preservado.'}}, {}, {cid:patches[cid]}, {}, self.raw)
    def test_unreviewed_input_rejected(self):
        patches,_=self.apply_module.batches('phase2-editorial');cid=next(iter(patches));patch=copy.deepcopy(patches[cid]);patch['reviewed']=False
        with self.assertRaisesRegex(ValueError,'not been reviewed'):self.apply_module.apply({}, {}, {cid:patch}, {}, self.raw)
    def test_no_private_or_script_source_urls(self):
        for value in ('javascript:alert(1)','data:text/plain,example','https://user:password@example.org/'):
            with self.assertRaises(ValueError):self.apply_module.valid_url(value)
    def test_all_current_office_inputs_have_primary_scope(self):
        patches,_=self.apply_module.batches('phase2-offices')
        for patch in patches.values():
            self.assertIn(patch['verification'],('current_directory','current_individual_profile'));self.assertTrue(patch['directory_scope'].startswith('current'))
            self.assertIn('2026',patch['checked_at']);self.assertTrue(patch['detail'])
    def test_reviewed_phase1_content_preserved(self):
        if not (ROOT/'.git').exists():self.skipTest('Git history unavailable in standalone artifact')
        old=json.loads(subprocess.check_output(['git','show',self.baseline['source_head']+':data/rs-estaduais/normalized.json'],cwd=ROOT))['candidates']
        current={c['id']:c for c in self.records}
        for c in old:
            if c['pautas']:self.assertEqual(c['pautas'],current[c['id']]['pautas'])
            if c['current_office']:self.assertEqual(c['current_office'],current[c['id']]['current_office'])
if __name__=='__main__':unittest.main()

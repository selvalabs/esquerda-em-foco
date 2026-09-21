"""A-D.2 regression tests; a searched queue is not exhaustive political research."""
from __future__ import annotations
import copy
import importlib.util
import json
import unittest
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais/ad2';P=ROOT/'rs/deputados-estaduais'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
def module():
    spec=importlib.util.spec_from_file_location('ad2_test_apply',ROOT/'tools/rs-estaduais/ad2_apply.py')
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
class ADTwo(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod=module();cls.helper=cls.mod.helpers()
        cls.records=load(D/'normalized.json')['candidates'];cls.current={c['id']:c for c in cls.records}
        cls.raw={c['SQ_CANDIDATO']:c for c in load(D/'candidates-official.json')}
        cls.history=load(D/'history-normalized.json');cls.baseline=load(A/'baseline.json')
        cls.votes=load(D/'ad2-votes.json');cls.patches=load(D/'ad2-editorial.json')
        cls.offices=load(D/'ad2-offices.json');cls.searches=load(D/'ad2-searches.json')
    def test_corrected_149_cohort_preserved(self):
        self.assertEqual(len(self.records),149);self.assertEqual(set(self.current),set(self.baseline['candidate_ids']))
        for cid in ('210002533927','210002533932','210002544838','210002544839'):self.assertIn(cid,self.current)
    def test_all_99_baseline_gaps_have_real_nominal_queries(self):
        self.assertEqual(len(self.searches['queries']),99);self.assertEqual(set(self.searches['queries']),set(self.baseline['gap_ids']))
        for cid,queries in self.searches['queries'].items():
            self.assertIn(cid,self.raw);self.assertTrue(queries)
            for query,reference in queries:self.assertTrue(query.strip());self.assertTrue(reference.startswith('turn'))
    def test_ledger_does_not_claim_exhaustiveness(self):
        rows=load(D/'ad2-research-ledger.json');self.assertEqual(len(rows),99)
        self.assertEqual({r['candidate_id'] for r in rows},set(self.searches['queries']))
        self.assertTrue(all(r['exhaustive'] is False for r in rows))
        self.assertFalse(load(A/'applied.json')['all_gaps_exhaustively_researched'])
    def test_earlier_50_summaries_unchanged(self):
        self.assertEqual(len(self.baseline['policy_summaries']),50)
        for cid,text in self.baseline['policy_summaries'].items():self.assertEqual(text,self.current[cid]['pautas'])
    def test_each_added_summary_has_its_own_evidence(self):
        expected={cid for cid,p in self.patches.items() if p.get('pautas')}
        actual={cid for cid in self.baseline['gap_ids'] if self.current[cid]['pautas']}
        self.assertEqual(actual,expected)
        for cid in actual:
            p=self.patches[cid];self.assertTrue(p['reviewed']);self.assertTrue(p['sources'])
            self.assertEqual(p['pautas'],self.current[cid]['pautas'])
            self.assertEqual(self.helper.norm(p['expected_name']),self.helper.norm(self.raw[cid]['NM_URNA_CANDIDATO']))
            for s in p['sources']:self.assertTrue(s['locator']);self.helper.valid_date(s['checked_at'])
    def test_editorial_merge_can_replay_twice(self):
        editorial=load(D/'editorial.json');offices=load(D/'offices-verified.json');before=copy.deepcopy((editorial,offices))
        for _ in range(2):self.helper.apply(editorial,offices,self.patches,self.offices,self.raw)
        self.assertEqual((editorial,offices),before)
    def test_earlier_offices_preserved_and_bruno_not_current_president(self):
        self.assertEqual(len(self.baseline['offices']),15)
        for cid,office in self.baseline['offices'].items():self.assertEqual(office,self.current[cid]['current_office'])
        self.assertEqual(self.current['210002539801']['current_office']['label'],'Vereador de Carazinho')
        self.assertNotIn('presidente',self.current['210002539801']['current_office']['label'].lower())
    def test_temporary_and_past_possessions_do_not_become_current(self):
        for cid in ('210002534014','210002539805'):
            self.assertIsNone(self.current[cid]['current_office'])
            self.assertTrue(any(a['kind'] in ('inaugural_speech','historical_mandate_assumption') for a in self.current[cid]['activities']))
    def test_failed_municipal_requests_are_not_confirmed_offices(self):
        failures=load(D/'ad2-source-checks.json')['municipal_api_attempts']['sources']
        self.assertEqual(sum(len(x['resources']) for x in failures),12)
        for row in failures:self.assertNotIn(row['candidate_id'],self.offices)
    def test_original_392_votes_are_preserved(self):
        self.assertEqual(len(self.baseline['verified_votes']),392)
        actual={self.mod.row_key(cid,h):h['votes'] for cid,rows in self.history.items() for h in rows if h['year']<2026 and h.get('votes') is not None}
        for key,total in self.baseline['verified_votes'].items():self.assertEqual(actual[key],total)
    def test_new_nominal_evidence_replays_without_changes(self):
        history=copy.deepcopy(self.history)
        self.mod.apply_vote_evidence(history,self.votes,self.raw,self.helper)
        self.mod.apply_vote_evidence(history,self.votes,self.raw,self.helper)
        self.assertEqual(history,self.history)
    def test_presidential_source_is_national_and_round_confirmed(self):
        rows=[h for h in self.history['210002533936'] if h['year']==2014 and h['candidate_id']=='280000000043']
        self.assertEqual(len(rows),1);h=rows[0]
        self.assertEqual(h['uf'],'BR');self.assertEqual(h['place'],'BRASIL');self.assertEqual(h['round'],1)
        self.assertEqual(h['votes'],1612186);self.assertFalse(h.get('round_note'));self.assertTrue(h['prior_source_round_note'])
        source=load(D/'ad2-vote-index.json')[h['votes_evidence_id']]
        self.assertTrue(source['member'].endswith('_BR.csv'));self.assertEqual(source['rows_per_total'],6439)
    def test_national_total_cannot_use_a_state_member(self):
        evidence=copy.deepcopy(self.votes)
        national=next(x for x in evidence if x['target']['unit']=='BR');national['member']=national['member'].replace('_BR.csv','_RS.csv')
        with self.assertRaises(ValueError):self.mod.apply_vote_evidence(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_wrong_vote_identity_is_rejected(self):
        evidence=copy.deepcopy(self.votes);evidence[0]['target']['name']='IDENTIDADE ERRADA'
        with self.assertRaisesRegex(ValueError,'identity mismatch'):self.mod.apply_vote_evidence(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_wrong_office_unit_or_turn_is_rejected(self):
        for key,value in [('office_code','13'),('electoral_unit','SC'),('round',2)]:
            evidence=copy.deepcopy(self.votes);evidence[1]['contexts']['1'][key]=value
            with self.assertRaises(ValueError):self.mod.apply_vote_evidence(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_unknown_future_or_unread_votes_rejected(self):
        for key,value in [('year',2026),('read',False)]:
            evidence=copy.deepcopy(self.votes);evidence[0][key]=value
            with self.assertRaises(ValueError):self.mod.apply_vote_evidence(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_negative_total_and_empty_match_rejected(self):
        for key,value in [('totals',{'1':-1}),('rows_per_total',{'1':0})]:
            evidence=copy.deepcopy(self.votes);evidence[0][key]=value
            with self.assertRaises(ValueError):self.mod.apply_vote_evidence(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_past_registration_is_not_a_nominal_total(self):
        reviews=load(D/'ad2-historical-status.json');self.assertEqual(len(reviews),14)
        self.assertTrue(all(r['vote_total_verified_by_this_record'] is False for r in reviews))
        history=copy.deepcopy(self.history);before={self.mod.row_key(cid,h):h.get('votes') for cid,rows in history.items() for h in rows}
        self.mod.apply_past_status(history,reviews,self.raw,self.helper)
        self.assertEqual(before,{self.mod.row_key(cid,h):h.get('votes') for cid,rows in history.items() for h in rows})
        for c in self.records:self.assertEqual(c['status'],load(D/'profiles-official.json')[c['id']]['data']['descricaoSituacao'])
    def test_current_year_cannot_enter_past_registration_review(self):
        evidence=copy.deepcopy(load(D/'ad2-historical-status.json'));evidence[0]['year']=2026
        with self.assertRaises(ValueError):self.mod.apply_past_status(copy.deepcopy(self.history),evidence,self.raw,self.helper)
    def test_sensitive_unneeded_registration_fields_absent(self):
        text=(D/'ad2-historical-status.json').read_text().lower()
        for forbidden in ('cpf','titulo_eleitoral','st_motivo_compra_voto','email','telefone','nascimento'):self.assertNotIn(forbidden,text)
    def test_public_research_export_and_separate_history_controls(self):
        self.assertEqual(len(load(P/'pesquisa.json')['candidates']),99)
        soup=BeautifulSoup((P/'index.html').read_text(),'html.parser')
        self.assertIsNotNone(soup.select_one('#ad2-research-method'))
        self.assertGreater(len(soup.select('[data-ad2-note="history"]')),0)
        self.assertEqual(len(soup.select('.rs-history summary')),len(self.records))
        self.assertIn('circunscrição nacional (Brasil)',soup.find(id='candidato-210002533936').get_text())
if __name__=='__main__':unittest.main()

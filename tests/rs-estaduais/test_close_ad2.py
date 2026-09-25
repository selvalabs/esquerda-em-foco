"""Recovery and research-status contracts; pending evidence cannot become certainty."""
from __future__ import annotations
import collections
import csv
import hashlib
import importlib.util
import json
import tempfile
import unittest
import urllib.request
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais/ad2-close';P=ROOT/'rs/deputados-estaduais'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
spec=importlib.util.spec_from_file_location('close_ad2_test',ROOT/'tools/rs-estaduais/close_ad2.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
class RecoveryClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load(D/'normalized.json');cls.records=cls.data['candidates']
        cls.ledger=load(A/'candidate-coverage.json')
        cls.byid={c['id']:c for c in cls.records}
        cls.soup=BeautifulSoup((P/'index.html').read_text(encoding='utf-8'),'html.parser')
    def test_every_candidate_has_one_status(self):
        self.assertEqual(len(self.ledger),len(self.records))
        self.assertEqual({x['candidate_id'] for x in self.ledger},set(self.byid))
        self.assertTrue(all(x['research_status'] in mod.STATUSES for x in self.ledger))
    def test_summary_status_means_sourced_summary_only(self):
        for row in self.ledger:
            c=self.byid[row['candidate_id']]
            self.assertEqual(row['research_status']=='policy_summary_verified',bool(c['pautas']))
            if c['pautas']:self.assertTrue(row['policy_sources'])
    def test_no_status_claims_exhaustive_research(self):
        self.assertTrue(all(x['research_exhaustive'] is False for x in self.ledger))
        self.assertFalse(load(A/'closure-metrics.json')['editorial_research_complete'])
    def test_all_unresolved_have_recovered_nominal_queries(self):
        for row in self.ledger:
            if not row['policy_summary']:self.assertTrue(row['searches'])
    def test_nonpending_gap_has_specific_review(self):
        for row in self.ledger:
            if row['research_status'] not in ('research_pending','policy_summary_verified'):
                decision=row['source_review'];self.assertTrue(decision['reason'])
                self.assertTrue(decision['source_urls']);self.assertTrue(decision['source_locators'])
                self.assertEqual(decision['expected_name'],self.byid[row['candidate_id']]['official_name'])
    def test_unknown_candidate_defaults_to_pending_not_insufficient(self):
        self.assertEqual(mod.choose_status({'pautas':None}),'research_pending')
    def test_status_requires_actual_source_not_query_only(self):
        with self.assertRaises(ValueError):mod.choose_status({'pautas':None},{'status':'individual_sources_reviewed_insufficient','checked_at':'2026-09-21','reason':'query only'})
    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):mod.choose_status({'pautas':None},{'status':'candidate_has_no_policies'})
    def test_unsourced_summary_rejected(self):
        with self.assertRaises(ValueError):mod.choose_status({'pautas':'example','editorial_sources':[],'editorial_checked_at':'2026-09-21'})
    def test_negative_decision_cannot_erase_reviewed_summary(self):
        with self.assertRaises(ValueError):mod.choose_status({'pautas':'example'}, {'status':'source_access_blocked'})
    def test_future_source_classification_rejected(self):
        with self.assertRaises(ValueError):mod.choose_status({'pautas':None},{'status':'source_access_blocked','source_urls':['https://example.org/'],'checked_at':'2027-01-01','reason':'example'})
    def test_unsafe_review_urls_rejected(self):
        for address in ('javascript:alert(1)','file:///etc/passwd','https://user:password@example.org/','http://127.0.0.1/','http://192.168.1.1/','http://metadata.google.internal/','https://example.org:8000/','https://example.org/a b'):
            self.assertFalse(mod.public_url(address),address)
    def test_offline_replay_has_two_matching_hash_sets(self):
        r=load(A/'reproducibility.json')
        self.assertFalse(r['network_used']);self.assertEqual(r['clean_output_passes'],2)
        self.assertEqual(r['passes'][0]['hashes'],r['passes'][1]['hashes'])
        self.assertTrue(r['frozen_inputs_unchanged'])
    def test_network_blocker_really_rejects_request(self):
        with mod.deny_network():
            with self.assertRaisesRegex(RuntimeError,'Network forbidden'):urllib.request.urlopen('https://example.org/')
    def test_recovery_numbers_are_not_unverified_chat_numbers(self):
        r=load(A/'recovery-audit.json')
        self.assertEqual(r['recovered_counts']['policy_summaries'],61)
        self.assertEqual(r['recovered_counts']['historical_vote_rows'],395)
        self.assertEqual(r['correction_to_unverified_chat_summary']['summaries_claimed'],71)
        self.assertTrue(r['local_only_work_not_preserved_cannot_be_confirmed'])
    def test_eleven_canonical_parties_and_zero_entries(self):
        r=load(A/'scope-reconciliation.json')
        self.assertEqual(len(r['by_party']),11)
        self.assertEqual(set(r['empty_parties']),{'PCB','PCO'})
        self.assertEqual(r['selected'],r['published'])
        self.assertEqual(r['config_sha256'],hashlib.sha256((ROOT/'config/party-scope-2026.json').read_bytes()).hexdigest())
    def test_research_exports_match_published_data(self):
        self.assertEqual(load(P/'dados.json'),self.data)
        out=load(P/'pesquisa-status.json');self.assertEqual(out['candidates'],self.ledger)
        self.assertEqual(out['status_counts'],dict(collections.Counter(x['research_status'] for x in self.ledger)))
    def test_each_card_has_one_expandable_research_note(self):
        nodes=self.soup.select('[data-close-status]');self.assertEqual(len(nodes),len(self.records))
        for row in self.ledger:
            article=self.soup.find(id='candidato-'+row['candidate_id'])
            node=article.select_one('details[data-close-status]');self.assertEqual(node['data-close-status'],row['research_status'])
            self.assertIsNotNone(node.find('summary'));self.assertIn('pesquisa-status.json',str(node))
    def test_history_nulls_are_explained_and_never_zeros(self):
        rows=load(A/'historical-vote-pendencies.json')
        self.assertEqual(len(rows),37)
        self.assertEqual(sum(x['requires_nominal_research'] for x in rows),11)
        self.assertTrue(all(x['votes'] is None for x in rows))
    def test_current_office_unknown_does_not_mean_absent(self):
        offices=load(D/'offices-verified.json')
        for row in self.ledger:
            self.assertEqual(row['current_office_status']=='confirmed_in_preserved_source',row['candidate_id'] in offices)
            if row['candidate_id'] in offices:self.assertEqual(row['current_office_source'],offices[row['candidate_id']])
    def test_electoral_snapshot_dates_preserved(self):
        obj=load(A/'closure-metrics.json');self.assertFalse(obj['electoral_snapshot_refreshed'])
        self.assertEqual(load(D/'manifest.json')['snapshot_generated_at'],'21/09/2026 12:31:37')
        self.assertIn('cadastro eleitoral continua',self.soup.find(id='close-research-method').text)
    def test_new_source_readings_are_not_new_programs(self):
        reviews=load(D/'close-source-review.json')['verified_restored_sources']
        self.assertEqual(len(reviews),11)
        for r in reviews:
            self.assertIn(r['candidate_id'],self.byid);self.assertFalse(r['new_policy_added']);self.assertTrue(r['locator'])
    def test_csv_formula_injection_is_neutralized(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'out.csv';mod.csv_file(p,[{'name':'=1+2'}],['name'])
            with p.open(encoding='utf-8-sig') as f:row=list(csv.DictReader(f,delimiter=';'))[0]
            self.assertEqual(row['name'],"'=1+2")
    def test_structured_page_modification_not_electoral_refresh(self):
        ld=json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertEqual(ld['dateModified'],'2026-09-22')
        self.assertFalse(load(P/'cobertura.json')['electoral_snapshot_refreshed'])
    def test_research_details_are_idempotent(self):
        self.assertEqual(len(self.soup.select('#close-research-method')),1)
        self.assertEqual(len(self.soup.select('#close-research-style')),1)
        self.assertEqual(load(A/'closure-metrics.json')['html_sha256'],hashlib.sha256((P/'index.html').read_bytes()).hexdigest())
if __name__=='__main__':unittest.main()

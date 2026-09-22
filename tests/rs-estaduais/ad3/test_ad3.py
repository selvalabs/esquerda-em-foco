"""Current-edition invariants; historical fixed-count tests run at the frozen commit."""
from __future__ import annotations
import collections, copy, csv, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[3];D=ROOT/'data/rs-estaduais';I=D/'ad3';A=ROOT/'docs/rs-estaduais/ad3';P=ROOT/'rs/deputados-estaduais'
spec=importlib.util.spec_from_file_location('ad3_current_tests',ROOT/'tools/rs-estaduais/ad3.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
def load(p):return json.loads(p.read_text(encoding='utf-8'))
class AD3Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load(D/'normalized.json');cls.records=cls.data['candidates'];cls.byid={c['id']:c for c in cls.records}
        cls.before=mod.base('data/rs-estaduais/normalized.json')['candidates'];cls.old={c['id']:c for c in cls.before}
        cls.patches=load(I/'editorial.json');cls.officepatches=load(I/'offices.json');cls.corrections=load(I/'corrections.json')
        cls.identities={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json')}
        cls.ledger=load(A/'candidate-coverage.json');cls.report=load(A/'report.json')
        cls.soup=BeautifulSoup((P/'index.html').read_text(encoding='utf-8'),'html.parser')
    def apply(self,patches=None,offices=None,corrections=None):
        return mod.apply_patches(mod.base('data/rs-estaduais/editorial.json'),mod.base('data/rs-estaduais/offices-verified.json'),self.identities,patches if patches is not None else self.patches,offices if offices is not None else self.officepatches,corrections if corrections is not None else self.corrections)
    def test_exact_population_preserved(self):
        self.assertEqual(set(self.byid),set(self.old));self.assertEqual(len(self.records),len(self.before))
        self.assertEqual(len(self.byid),len(self.records))
    def test_canonical_projection_matches_all_ids(self):
        scope={p.upper() for p in load(ROOT/'config/party-scope-2026.json')['parties']}
        with (D/'raw/universo-rs-estaduais-2026.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f,delimiter=';'))
        expected={r['SQ_CANDIDATO'] for r in rows if r['SG_PARTIDO'].upper() in scope}
        self.assertEqual(expected,set(self.byid))
    def test_official_snapshot_bytes_unchanged(self):
        for filename in mod.FROZEN:self.assertEqual((D/filename).read_bytes(),mod.baseline_bytes('data/rs-estaduais/'+filename),filename)
    def test_previous_summaries_unchanged(self):
        for cid,c in self.old.items():
            if c['pautas']:self.assertEqual(self.byid[cid]['pautas'],c['pautas'])
    def test_new_summary_count_comes_from_patches(self):
        actual=sum(bool(c['pautas']) for c in self.records)-sum(bool(c['pautas']) for c in self.before)
        self.assertEqual(actual,len(self.patches));self.assertGreater(actual,0)
    def test_all_new_summaries_are_rendered(self):
        for cid,p in self.patches.items():
            self.assertEqual(self.byid[cid]['pautas'],p['pautas'])
            self.assertIn(p['pautas'],self.soup.find(id='candidato-'+cid).get_text())
    def test_new_sources_have_identity_locator_date(self):
        for p in self.patches.values():
            self.assertTrue(p['reviewed']);self.assertEqual(p['checked_at'],'2026-09-22')
            for s in p['sources']:
                mod.valid_source(s);self.assertTrue(s['identity_basis']);self.assertTrue(s['read_method'])
    def test_old_office_dates_preserved(self):
        for cid,v in mod.base('data/rs-estaduais/offices-verified.json').items():self.assertEqual(self.byid[cid]['current_office'],v)
    def test_new_offices_are_current_primary_directories(self):
        for cid,p in self.officepatches.items():
            office=self.byid[cid]['current_office'];self.assertEqual(office['verification'],'current_directory')
            self.assertIn('2025',office['legislature']);self.assertIn('2028',office['legislature'])
            self.assertRegex(office['directory_rendered_sha256'],r'^[0-9a-f]{64}$')
            self.assertTrue(urlsplit(office['directory_source']).hostname.endswith('.leg.br'))
    def test_nominal_values_and_context_are_unchanged(self):
        for cid,c in self.old.items():self.assertEqual(self.byid[cid]['history'],c['history'])
    def test_historical_reread_does_not_claim_votes(self):
        rows=load(I/'historical-follow-up.json')['records']
        self.assertEqual(len(rows),11)
        self.assertTrue(all(not r['nominal_total_verified'] for r in rows))
        self.assertEqual(self.report['new_nominal_totals'],0)
    def test_ticket_positions_are_not_missing_own_votes(self):
        rows=load(A/'historical-vote-pendencies.json')
        self.assertEqual(sum(not r['requires_nominal_research'] for r in rows),26)
        self.assertEqual(sum(r['requires_nominal_research'] for r in rows),11)
    def test_research_queue_matches_original_gaps(self):
        q=load(I/'research-ledger.json');self.assertEqual(set(q),{c['id'] for c in self.before if not c['pautas']})
        self.assertTrue(all(r['queries'] for r in q.values()))
    def test_queries_are_preserved_not_inferred_from_names(self):
        q=load(I/'queries.json');ledger=load(I/'research-ledger.json')
        for cid,values in q.items():self.assertEqual(values,[v['query'] for v in ledger[cid]['queries']])
        self.assertEqual(sum(len(x) for x in q.values()),self.report['executed_queries'])
    def test_partial_coverage_is_not_claimed_complete(self):
        self.assertFalse(self.report['full_88_review_gate'])
        self.assertLess(self.report['review_completed_in_round'],self.report['research_queue_size'])
        self.assertEqual(self.report['status'],'substantive_increment_partial')
    def test_completion_and_source_status_are_distinct(self):
        for r in self.ledger:
            self.assertFalse(r['research_exhaustive'])
            if r['review_completed_in_round']:self.assertIn(r['candidate_id'],self.patches)
        self.assertGreater(sum(r['policy_summary'] for r in self.ledger),sum(r['review_completed_in_round'] for r in self.ledger))
    def test_all_research_states_have_one_candidate(self):
        self.assertEqual({r['candidate_id'] for r in self.ledger},set(self.byid));self.assertEqual(len(self.ledger),len(self.records))
        self.assertTrue(all(r['research_status'] in mod.LABELS for r in self.ledger))
    def test_status_totals_are_computed(self):
        export=load(P/'pesquisa-status.json')
        self.assertEqual(export['status_counts'],dict(collections.Counter(r['research_status'] for r in self.ledger)))
        self.assertEqual(sum(export['status_counts'].values()),len(self.records))
    def test_electoral_and_editorial_dates_stay_distinct(self):
        self.assertFalse(self.report['electoral_snapshot_refreshed'])
        self.assertEqual(load(D/'manifest.json')['snapshot_generated_at'],'21/09/2026 12:31:37')
        self.assertIn('21/09/2026',self.soup.find(id='ad3-research-method').text)
    def test_structured_data_uses_unordered_list(self):
        ld=json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertEqual(ld['mainEntity']['numberOfItems'],len(self.records))
        self.assertEqual(ld['mainEntity']['itemListOrder'],'https://schema.org/ItemListUnordered')
        self.assertEqual(ld['dateModified'],'2026-09-22')
    def test_exactly_one_disclosure_per_candidate(self):
        self.assertEqual(len(self.soup.select('[data-close-status]')),len(self.records))
        self.assertEqual(len(self.soup.select('#ad3-research-method')),1)
    def test_research_json_equals_current_ledger(self):
        self.assertEqual(load(P/'pesquisa-status.json')['candidates'],self.ledger)
        self.assertEqual(load(P/'dados.json'),self.data)
    def test_new_acts_and_withdrawal_reconcile(self):
        before=sum(len(c['activities']) for c in self.before);after=sum(len(c['activities']) for c in self.records)
        self.assertEqual(after-before,sum(len(p.get('activities_append',[])) for p in self.patches.values())-len(self.corrections))
    def test_withdrawn_listing_no_longer_counts_as_act(self):
        for correction in self.corrections:
            self.assertFalse(any(a['source']==correction['matched_source'] for a in self.byid[correction['candidate_id']]['activities']))
            self.assertIn('Nota de revisão documental',self.soup.find(id='candidato-'+correction['candidate_id']).text)
    def test_withdrawal_preserves_prior_record_and_sources(self):
        for c in self.corrections:
            self.assertEqual(mod.digest(c['previous_record']),c['expected_before_sha256'])
            self.assertGreaterEqual(len(c['sources']),2);self.assertTrue(c['reason'])
    def test_unexpected_prior_record_blocks_correction(self):
        bad=copy.deepcopy(self.corrections);bad[0]['expected_before_sha256']='0'*64
        with self.assertRaises(ValueError):self.apply(corrections=bad)
    def test_wrong_candidate_identity_blocks_addition(self):
        bad=copy.deepcopy(self.patches);next(iter(bad.values()))['expected_name']='WRONG PERSON'
        with self.assertRaises(ValueError):self.apply(patches=bad)
    def test_future_publication_blocks_addition(self):
        bad=copy.deepcopy(self.patches);next(iter(bad.values()))['sources'][0]['published_at']='2027-01-01'
        with self.assertRaises(ValueError):self.apply(patches=bad)
    def test_empty_locator_blocks_addition(self):
        bad=copy.deepcopy(self.patches);next(iter(bad.values()))['sources'][0]['locator']=''
        with self.assertRaises(ValueError):self.apply(patches=bad)
    def test_unreviewed_text_blocks_addition(self):
        bad=copy.deepcopy(self.patches);next(iter(bad.values()))['reviewed']=False
        with self.assertRaises(ValueError):self.apply(patches=bad)
    def test_wrong_office_identity_blocks_confirmation(self):
        bad=copy.deepcopy(self.officepatches);next(iter(bad.values()))['expected_name']='WRONG PERSON'
        with self.assertRaises(ValueError):self.apply(offices=bad)
    def test_patch_replay_is_idempotent(self):
        first=self.apply();second=mod.apply_patches(*first,self.identities,self.patches,self.officepatches,self.corrections)
        self.assertEqual(first,second)
    def test_text_conflicts_remain_blocked(self):
        first=self.apply();bad=copy.deepcopy(self.patches);next(iter(bad.values()))['pautas']='Different reviewed text'
        with self.assertRaises(ValueError):mod.apply_patches(*first,self.identities,bad,self.officepatches,self.corrections)
    def test_bots_are_not_counted_as_readable_content(self):
        rows=load(I/'follow-source-audit.json')['sources']
        flagged=[r for r in rows if r.get('manual_classification_correction')]
        self.assertTrue(flagged);self.assertTrue(all(not r['read'] and r['outcome']=='access_interstitial' for r in flagged))
    def test_raw_campaign_text_is_not_in_source_audit(self):
        for filename in ('source-access.json','follow-source-audit.json'):
            self.assertNotIn('review_text',(I/filename).read_text())
    def test_csv_formula_injection_neutralized(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'test.csv';mod.csv_write(path,[{'name':'=1+2'}],['name'])
            with path.open(encoding='utf-8-sig') as f:self.assertEqual(next(csv.DictReader(f,delimiter=';'))['name'],"'=1+2")
    def test_public_data_has_no_private_registration_fields(self):
        text=(P/'dados.json').read_text().lower()
        for field in ('nr_cpf','nr_titulo_eleitoral','email_candidato','endereco_residencial','dt_nascimento'):self.assertNotIn(field,text)
    def test_export_files_and_photos_exist(self):
        for filename in ('pesquisa-status.json','revisoes.json','dados.json','fontes.json','cobertura.json','candidaturas.csv'):self.assertTrue((P/filename).is_file())
        for c in self.records:
            photo=c['photo'];self.assertEqual(hashlib.sha256((P/photo['path']).read_bytes()).hexdigest(),photo['sha256'])
    def test_no_duplicate_html_ids_or_missing_anchors(self):
        ids=[n['id'] for n in self.soup.select('[id]')];self.assertEqual(len(ids),len(set(ids)))
        for c in self.records:self.assertIsNotNone(self.soup.find(id='candidato-'+c['id']))
    def test_hash_and_legacy_counters_are_synchronized(self):
        checksum=hashlib.sha256((P/'index.html').read_bytes()).hexdigest()
        for path in (A/'report.json',ROOT/'docs/rs-estaduais/build-report.json',P/'cobertura.json'):
            r=load(path);self.assertEqual(r['html_sha256'],checksum);self.assertEqual(r['policy_summaries'],sum(bool(c['pautas']) for c in self.records))
    def test_no_merge_or_release_claim(self):
        self.assertFalse(self.report['merge_performed']);self.assertFalse(self.report['deployment_performed']);self.assertFalse(self.report['E_F_completed'])
if __name__=='__main__':unittest.main()

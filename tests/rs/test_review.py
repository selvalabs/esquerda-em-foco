from __future__ import annotations
import collections,hashlib,json,sys,unittest,urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/rs'))
from review_support import TOPICS,safe_url,apply_editorial
class ReviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.public=json.loads((ROOT/'rs/deputados-federais/dados.json').read_text());cls.cs=cls.public['candidates'];cls.report=json.loads((ROOT/'docs/rs/fed03/final-report.json').read_text());cls.soup=BeautifulSoup((ROOT/'rs/deputados-federais/index.html').read_text(),'html.parser')
 def test_schema_and_audit_coverage(self):
  self.assertEqual(self.public['schema_version'],3);matrix=json.loads((ROOT/'docs/rs/fed03/candidate-matrix.json').read_text());self.assertEqual({c['id'] for c in self.cs},{c['id'] for c in matrix});self.assertEqual(len(matrix),107)
 def test_summary_counts_are_honest(self):
  n=sum(bool(c['pautas']) for c in self.cs);self.assertGreater(n,28);self.assertEqual(n,self.report['with_summary']);self.assertEqual(107-n,self.report['without_summary']);self.assertEqual(self.report['editorial_complete'],n==107)
 def test_topics_have_specific_sources(self):
  for c in self.cs:
   sources={s['url'] for s in c['editorial_sources']}
   for t in c['topics']:
    self.assertIn(t['id'],TOPICS);self.assertTrue(t['sources']);self.assertTrue(set(t['sources']).issubset(sources))
 def test_topic_dom_matches_data(self):
  for c in self.cs:self.assertEqual(set(self.soup.find(id='candidato-'+c['id']).get('data-topics','').split()),{t['id'] for t in c['topics']})
 def test_no_automatic_party_topics(self):
  self.assertTrue(any(not c['topics'] for c in self.cs));self.assertTrue(any(c['topics'] for c in self.cs))
  for c in self.cs:
   if c['topics']:self.assertTrue(c['editorial_sources'])
 def test_ticket_votes_are_not_individual(self):
  hs=[h for c in self.cs for h in c['history'] if h['votes_status']=='not_applicable'];self.assertEqual(len(hs),21)
  for h in hs:self.assertIsNone(h['votes']);self.assertNotIn('votes_source',h);self.assertIn('Não se aplica',h['votes_note'])
 def test_legacy_votes_survive_rebuild(self):
  counts=collections.Counter(h['votes_status'] for c in self.cs for h in c['history']);self.assertEqual(counts['verified_nominal'],277);self.assertEqual(counts['not_verified'],2);self.assertEqual(counts['not_yet_held'],107)
  self.assertEqual(counts,self.report['vote_rows'])
 def test_legacy_evidence_all_present(self):
  legacy=json.loads((ROOT/'data/rs/votes-legacy-reviewed.json').read_text());found={f'{c["id"]}:{h["year"]}:{h["candidate_id"]}:{h.get("round",1)}':h for c in self.cs for h in c['history']}
  for year,e in legacy.items():
   self.assertEqual(len(e['member_sha256']),64)
   for key,n in e['totals'].items():self.assertEqual(found[key]['votes'],n);self.assertEqual(found[key]['votes_source'],e['url'])
 def test_unverified_is_not_zero(self):
  for c in self.cs:
   for h in c['history']:
    if h['votes_status']=='not_verified':self.assertIsNone(h['votes']);self.assertIn('não equivale a zero',h['votes_note'])
 def test_future_election_has_no_result(self):
  for c in self.cs:
   for h in c['history']:
    if h['year']==2026:self.assertIsNone(h['votes']);self.assertEqual(h['votes_status'],'not_yet_held')
 def test_userinfo_url_rejected(self):
  for address in ['https://@braz.ivan/','https://user@example.com','https://u:p@example.com','javascript:alert(1)','https://exam ple.com']:self.assertFalse(safe_url(address))
 def test_public_links_no_credentials(self):
  for a in self.soup.select('a[href]'):
   if a['href'].startswith(('https://','http://')):self.assertTrue(safe_url(a['href']),a['href'])
  for c in self.cs:
   for source in c['socials']+c['sites']:self.assertTrue(safe_url(source['url']),source)
 def test_nonfederal_offices_are_institutional(self):
  offices=[c['current_office'] for c in self.cs if c['current_office']];self.assertGreater(len(offices),9)
  for e in offices:
   host=urllib.parse.urlsplit(e['source']).hostname;self.assertTrue(host.endswith(('.gov.br','.leg.br')));self.assertTrue(e.get('checked_at'))
 def test_no_exhaustive_office_claim(self):self.assertFalse(self.report['current_office_audit_exhaustive'])
 def test_final_html_hash(self):self.assertEqual(hashlib.sha256((ROOT/'rs/deputados-federais/index.html').read_bytes()).hexdigest(),self.report['html_sha256'])
 def test_official_refresh_matches_population(self):
  r=json.loads((ROOT/'docs/rs/review/official-refresh.json').read_text());self.assertEqual(r['profiles_refreshed'],107);self.assertEqual(r['added_ids'],[]);self.assertEqual(r['removed_ids'],[]);self.assertEqual(r['errors'],[])
 def test_editorial_apply_is_idempotent(self):
  p=ROOT/'data/rs/editorial.json';before=p.read_bytes();apply_editorial();self.assertEqual(p.read_bytes(),before)
 def test_no_new_filter_ui(self):
  self.assertIsNone(self.soup.select_one('#partyFilter'));self.assertIsNone(self.soup.select_one('#topicFilters'));self.assertIsNone(self.soup.select_one('.rs-topics'));self.assertFalse(self.report['new_filter_ui'])
 def test_research_log_population(self):
  log=json.loads((ROOT/'data/rs/review-search-log.json').read_text());self.assertEqual({c['id'] for c in self.cs},set(log))
  for row in log.values():self.assertTrue(row.get('queries') or row.get('sources'))
 def test_raw_bad_addresses_are_not_in_public_dataset(self):
  for c in self.cs:self.assertNotIn('invalid_declared_urls',c)
 def test_no_live_update_claim(self):self.assertTrue(self.report['snapshot_not_live'])
if __name__=='__main__':unittest.main()

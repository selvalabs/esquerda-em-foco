"""Frozen-census, provenance, privacy, source and static-route acceptance checks."""
from __future__ import annotations
import collections,csv,hashlib,json,re,unittest
from pathlib import Path
from urllib.parse import urlsplit,unquote
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
def read(path):return json.loads((ROOT/path).read_text())
class ParanáBase(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=read('data/pr/candidates-official.json');cls.all=read('data/pr/normalized.json')['candidates'];cls.manifest=read('data/pr/manifest.json');cls.byid={c['id']:c for c in cls.all}
 def test_01_census_reconciliation(self):
  self.assertEqual({c['SQ_CANDIDATO'] for c in self.raw},set(self.byid));self.assertEqual(len(self.all),255)
  self.assertEqual(collections.Counter(c['office_code']for c in self.all),{6:115,7:140})
 def test_02_identity_and_scope(self):
  self.assertEqual(len(self.byid),len(self.all))
  self.assertTrue(all(c['state']=='PR' and c['election_year']==2026 for c in self.all))
  self.assertTrue(all(c['party'] in self.manifest['scope_by_office'][str(c['office_code'])] for c in self.all))
  self.assertFalse(read('docs/pr/reconciliation.json')['identity_discrepancies'])
 def test_03_all_individual_profiles_read(self):
  p=read('data/pr/profiles-official.json');self.assertEqual(set(p),set(self.byid));self.assertTrue(all('data'in v for v in p.values()))
  self.assertEqual(self.manifest['profiles_failed'],0)
 def test_04_status_not_inferred_from_appeal(self):
  self.assertEqual(sum(collections.Counter(c['status_group']for c in self.all).values()),255)
  for c in self.all:
   if c['apt_api'] is True:self.assertEqual(c['status_group'],'apta')
   if c['apt_api'] is False:self.assertEqual(c['status_group'],'inapta')
 def test_05_renunciations_are_retained(self):
  self.assertGreaterEqual(sum(c['status']=='Renúncia'for c in self.all),8)
  for c in self.all:
   if c['status']=='Renúncia':self.assertEqual(c['status_group'],'inapta')
 def test_06_same_name_is_not_deduplicated(self):
  self.assertIn('160002547723',self.byid);self.assertIn('160002554272',self.byid)
  self.assertNotEqual(self.byid['160002547723']['office_code'],self.byid['160002554272']['office_code'])
 def test_07_photos_and_hashes(self):
  photos=read('data/pr/photos-official.json');self.assertEqual(set(photos),set(self.byid))
  for cid,photo in photos.items():
   file=ROOT/'pr/assets/photos'/(cid+'.webp');self.assertTrue(file.is_file());self.assertEqual(hashlib.sha256(file.read_bytes()).hexdigest(),photo['sha256'])
 def test_08_theme_sources_are_individual(self):
  taxonomy=read('data/pr/taxonomy.json')['themes'];editorial=read('data/pr/editorial.json')
  for c in self.all:
   if c['pautas']:self.assertIn(c['id'],editorial);self.assertTrue(c['editorial_sources'])
   else:self.assertFalse(c['themes'])
   urls={s['url']for s in c['editorial_sources']}
   for theme in c['themes']:
    self.assertIn(theme['id'],taxonomy);self.assertIn(theme['evidence_url'],urls);self.assertTrue(theme['summary'])
 def test_09_historical_votes_have_exact_provenance(self):
  count=0
  for c in self.all:
   for h in c['history']:
    self.assertLess(h['year'],2026)
    if h.get('votes') is not None:
     count+=1;self.assertIsInstance(h['votes'],int);self.assertGreaterEqual(h['votes'],0)
     self.assertTrue(h.get('votes_source'));p=h['votes_provenance'];self.assertRegex(p['member_sha256'],r'^[a-f0-9]{64}$');self.assertIsNone(p['archive_sha256']);self.assertGreater(h['votes_rows'],0)
  self.assertGreater(count,250)
 def test_10_mandates_and_regions_need_sources(self):
  for c in self.all:
   if c['current_office']:self.assertTrue(c['current_office']['source']);self.assertTrue(c['current_office']['checked_at'])
   if c['region']:self.assertTrue(c['region']['source']);self.assertIn('documentada',c['region']['meaning'])
 def test_11_no_private_identifiers(self):
  banned={'NR_CPF_CANDIDATO','NM_EMAIL','NR_TITULO_ELEITORAL_CANDIDATO','cpf','tituloEleitor','numeroProcesso','endereco','DT_NASCIMENTO'}
  def walk(x):
   if isinstance(x,dict):
    self.assertFalse(banned.intersection(x));[walk(v)for v in x.values()]
   elif isinstance(x,list):[walk(v)for v in x]
  walk(self.raw);walk(self.all)
 def test_12_source_manifest_is_auditable(self):
  for k,s in self.manifest['sources'].items():self.assertRegex(s['sha256'],r'^[a-f0-9]{64}$');self.assertTrue(s['url'].startswith('https://'));self.assertTrue(s['checked_at'])
  self.assertFalse(self.manifest['errors'])
 def test_13_static_pages_and_local_assets(self):
  for code,slug in [(6,'deputados-federais'),(7,'deputados-estaduais')]:
   folder=ROOT/'pr'/slug;soup=BeautifulSoup((folder/'index.html').read_text(),'html.parser');cards=soup.select('article.candidate')
   expected={6:115,7:140}[code]
   self.assertEqual(len(cards),expected);self.assertEqual({c['data-tse-id']for c in cards},{c['id']for c in self.all if c['office_code']==code})
   ids=[x['id']for x in soup.select('[id]')];self.assertEqual(len(ids),len(set(ids)))
   for tag in soup.select('img[src],script[src]'):
    src=tag['src'];self.assertFalse(src.startswith(('javascript:','data:text/html')))
    if not urlsplit(src).scheme:self.assertTrue((folder/src).resolve().is_file(),src)
   self.assertEqual(len(soup.select('link[rel="canonical"]')),1)
   self.assertTrue(soup.select_one('link[rel="canonical"]')['href'].endswith('/pr/'+slug+'/'))
   with (folder/'candidaturas.csv').open(encoding='utf-8-sig') as stream:self.assertEqual(len(list(csv.DictReader(stream))),expected)
   for script in soup.select('script[type="application/ld+json"]'):self.assertEqual(json.loads(script.string)['mainEntity']['numberOfItems'],expected)
 def test_14_substitution_links_are_reciprocal(self):
  self.assertGreaterEqual(sum(c['replaced_flag']for c in self.all),5)
  for c in self.all:
   for rel in c['substitution_links']:
    other=self.byid[rel['id']];self.assertTrue(any(x['id']==c['id']for x in other['substitution_links']))
    self.assertEqual(c['office_code'],other['office_code'])
 def test_15_sc_rs_unchanged(self):
  audit=read('docs/pr/isolation.json');self.assertTrue(audit['all_unchanged']);self.assertGreater(audit['protected_file_count'],0)
  for path,sha in audit['sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),sha)
 def test_16_editorial_gaps_not_hidden(self):
  b=read('docs/pr/build-report.json');self.assertTrue(b['census_complete']);self.assertFalse(b['editorial_complete'])
  for slug in ('deputados-federais','deputados-estaduais'):
   audit=read('docs/pr/'+slug+'-audit.json');self.assertEqual(audit['selected_total'],audit['with_documented_themes']+sum('pautas_individuais'in p['fields']for p in audit['pending']))
 def test_17_no_auto_theme_from_party(self):
  for c in self.all:
   if c['id'] not in read('data/pr/editorial.json'):self.assertEqual(c['themes'],[])
 def test_18_canonical_scope_applies_to_both_offices(self):
  expected=['PCB','PCdoB','PCO','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP']
  self.assertEqual(self.manifest['scope_by_office']['6'],expected);self.assertEqual(self.manifest['scope_by_office']['7'],expected)
  state=self.manifest['census']['deputados-estaduais'];fed=self.manifest['census']['deputados-federais']
  self.assertEqual(fed['selected_by_party'].get('REDE'),6);self.assertEqual(state['selected_by_party'].get('REDE'),29);self.assertEqual(state['selected_by_party'].get('PSTU'),2)
  self.assertIn('PCB',fed['scope_parties_without_record']);self.assertIn('PSTU',fed['scope_parties_without_record']);self.assertIn('PCB',state['scope_parties_without_record']);self.assertIn('PSB',state['scope_parties_without_record'])
if __name__=='__main__':unittest.main(verbosity=2)

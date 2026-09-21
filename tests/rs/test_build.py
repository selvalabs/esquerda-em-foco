"""Deterministic checks for the frozen RS edition."""
from __future__ import annotations
import collections, hashlib, json, re, unittest, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/rs'))
from fed03_baseline import expected_sc_sha256
ROOT=Path(__file__).resolve().parents[2];DEST=ROOT/'rs/deputados-federais';D=ROOT/'data/rs'
class EditionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.raw=(DEST/'index.html').read_text();cls.soup=BeautifulSoup(cls.raw,'html.parser');cls.rows=json.loads((D/'candidates-official.json').read_text());cls.data=json.loads((DEST/'dados.json').read_text())['candidates']
 def test_sc_unchanged(self):
  self.assertEqual(hashlib.sha256((ROOT/'index.html').read_bytes()).hexdigest(),expected_sc_sha256(ROOT))
 def test_complete_official_ids(self):
  ids={r['SQ_CANDIDATO'] for r in self.rows};rendered=[a['data-tse-id'] for a in self.soup.select('article.candidate')]
  self.assertEqual(len(ids),111);self.assertEqual(len(rendered),111);self.assertEqual(ids,set(rendered));self.assertEqual(ids,{c['id'] for c in self.data})
 def test_state_office_and_parties(self):
  for r in self.rows:self.assertEqual((r['SG_UF'],r['CD_CARGO'],r['ANO_ELEICAO']),('RS','6','2026'))
  self.assertEqual(collections.Counter(c['party'] for c in self.data),{'PCdoB':2,'PDT':32,'PSB':23,'PSOL':23,'PSTU':2,'PT':21,'PV':3,'REDE':2,'UP':3})
 def test_registration_status(self):
  statuses=collections.Counter(c['status'] for c in self.data);self.assertEqual(sum(statuses.values()),111);self.assertTrue(all(c['status'] for c in self.data))
  withdrawn=next(c for c in self.data if c['id']=='210002535928');self.assertEqual(withdrawn['status'],'Renúncia')
  self.assertIn('Renúncia',self.soup.find(id='candidato-'+withdrawn['id']).get_text())
 def test_numbers_match_source(self):
  raw={r['SQ_CANDIDATO']:r for r in self.rows}
  for c in self.data:self.assertEqual((c['number'],c['official_name']),(raw[c['id']]['NR_CANDIDATO'],raw[c['id']]['NM_URNA_CANDIDATO']))
 def test_official_photo_integrity(self):
  for c in self.data:
   p=c['photo'];self.assertIsNotNone(p);self.assertEqual(hashlib.sha256((DEST/p['path']).read_bytes()).hexdigest(),p['sha256'])
  self.assertEqual(len(self.soup.select('img.candidate-photo')),111)
 def test_ids_and_fragment_links(self):
  ids=[e['id'] for e in self.soup.select('[id]')];self.assertEqual(len(ids),len(set(ids)))
  for a in self.soup.select('a[href^="#"]'):
   self.assertIn(urllib.parse.unquote(a['href'][1:]),ids)
 def test_sources_and_missing_fields(self):
  for c in self.data:
   self.assertIn(c['id'],c['tse_url'])
   if c['pautas']:self.assertTrue(c['editorial_sources'])
   else:self.assertIn('não documentada',self.soup.find(id='candidato-'+c['id']).get_text())
   if c['current_office']:self.assertIn(urllib.parse.urlsplit(c['current_office']['source']).hostname, {'www.camara.leg.br','www.camarapoa.rs.gov.br','www.cmsantabarbaradosul.rs.gov.br','www.camarafarroupilha.rs.gov.br','www.camarajaguarao.rs.gov.br','www.santanadolivramento.rs.leg.br'});self.assertTrue(c['current_office'].get('checked_at'))
 def test_history_and_votes(self):
  for c in self.data:
   keys=[(h['year'],h['candidate_id'],h.get('round',1)) for h in c['history']];self.assertEqual(len(keys),len(set(keys)))
   self.assertTrue(any(h['year']==2026 and h['candidate_id']==c['id'] for h in c['history']))
   for h in c['history']:
    self.assertLessEqual(h['year'],2026)
    if h.get('votes') is not None:self.assertLess(h['year'],2026);self.assertTrue(h['votes_source'].startswith('https://cdn.tse.jus.br/'));self.assertGreaterEqual(h['votes'],0)
 def test_seo_is_rs_specific(self):
  canonical='https://selvalabs.github.io/esquerda-em-foco/rs/deputados-federais/'
  self.assertIn('no RS 2026',self.soup.title.string);self.assertEqual(self.soup.h1.get_text(),'Rio Grande do Sul');self.assertEqual(self.soup.select_one('link[rel="canonical"]')['href'],canonical)
  ld=json.loads(self.soup.select_one('script[type="application/ld+json"]').string);self.assertEqual(ld['@type'],'CollectionPage');self.assertEqual(ld['mainEntity']['numberOfItems'],111);self.assertEqual(ld['mainEntity']['itemListOrder'],'https://schema.org/ItemListUnordered');self.assertEqual(len(ld['mainEntity']['itemListElement']),111)
  self.assertEqual(self.soup.select_one('meta[property="og:image"]')['content'],canonical+'assets/og-rs.png');self.assertTrue((DEST/'assets/og-rs.png').is_file())
 def test_no_sc_fiches_or_positional_ranking(self):
  self.assertNotIn('240002',self.soup.body.get_text());self.assertFalse(self.soup.select('.candidate-index'))
  self.assertNotIn('catarinense',self.soup.body.get_text().lower());self.assertNotIn('Santa Catarina',self.soup.h1.get_text())
 def test_valid_local_assets(self):
  for element,attr in [('img','src'),('link','href')]:
   for e in self.soup.select(element+'['+attr+']'):
    address=e[attr]
    if address.startswith(('data:','http:','https:','#')):continue
    self.assertTrue((DEST/urllib.parse.unquote(address.split('?')[0])).is_file(),address)
 def test_runtime_contract(self):
  js=self.soup.select('script:not([type])')[-1].get_text();self.assertIn("getElementById('searchInput')",js);self.assertIn("getElementById('siteNavMenu')",js);self.assertIn('America/Sao_Paulo',js);self.assertNotIn('Math.random',js);self.assertNotIn('localStorage',js)
 def test_no_private_registration_fields(self):
  forbidden=('CPF','TITULO_ELEITOR','EMAIL','CNPJ','DT_NASCIMENTO','ENDERECO','TELEFONE')
  def inspect(value):
   if isinstance(value,dict):
    for key,child in value.items():
     self.assertFalse(any(s in key.upper() for s in forbidden),key);inspect(child)
   elif isinstance(value,list):
    for child in value:inspect(child)
  for name in ['candidates-official.json','profiles-official.json','history-official.json','status-official.json']:
   inspect(json.loads((D/name).read_text()))
if __name__=='__main__':unittest.main()

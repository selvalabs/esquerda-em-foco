"""Round C data/HTML/security/isolation checks. Uses only frozen local inputs."""
import copy, hashlib, importlib.util, json, re, subprocess, unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[3]
SPEC=importlib.util.spec_from_file_location('sp_c_build',ROOT/'tools/sp/round_c/build.py')
B=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(B)
BASE='89092b6192f5b06acba3fcb1ac7adef1af99b266'

def load(p):return json.loads((ROOT/p).read_text())
class ProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load('sp/deputados-federais/dados.json');cls.rows=cls.data['records']
        cls.by={r['id']:r for r in cls.rows};cls.html=(ROOT/'sp/deputados-federais/index.html').read_text()
        cls.soup=BeautifulSoup(cls.html,'html.parser')
        cls.old=load('data/sp/research/records.json')['records']
        cls.idx=load('data/sp/research/theme-evidence-2026.json')['records']
    def test_canonical_population(self):
        allowed={x.upper() for x in load('config/party-scope-2026.json')['parties']}
        expected={r['SQ_CANDIDATO'] for r in load('data/sp/all-candidates-official.json') if r['SG_PARTIDO'].upper() in allowed}
        self.assertEqual(set(self.by),expected);self.assertEqual(len(expected),249)
    def test_all_parties_and_zero_pcb(self):
        buttons={b['data-party-filter'] for b in self.soup.select('[data-party-filter]')}
        self.assertEqual(buttons,set(self.data['party_scope'])|{''})
        self.assertFalse(any(r['party']=='PCB' for r in self.rows))
    def test_preserved_234_ids(self):
        self.assertEqual({r['candidate_id'] for r in self.old},{r['id'] for r in self.rows if r['research_state']=='round_b_imported'})
    def test_new_scope_no_inferred_claims(self):
        extra=[r for r in self.rows if r['research_state']=='canonical_scope_addition_not_reviewed']
        self.assertEqual(len(extra),15)
        for c in extra:self.assertFalse(c['claims_2026'] or c['claims_other'] or c['themes_2026'] or c['biography'])
    def test_current_index_exact(self):
        expected={(r['candidate_id'],B.ALIASES.get(t['theme_id'],t['theme_id'])):set(t['claim_ids']) for r in self.idx for t in r['themes']}
        actual={(r['id'],t['id']):set(t['claim_ids']) for r in self.rows for t in r['themes_2026']}
        self.assertEqual(actual,expected);self.assertEqual(len(actual),218)
    def test_claims_not_rewritten(self):
        for rec in self.old:
            original={c['claim_id']:c for c in rec['claims']}
            dest=self.by[rec['candidate_id']]
            self.assertEqual(len(original),len(dest['claims_2026'])+len(dest['claims_other']))
            for c in dest['claims_2026']+dest['claims_other']:
                old=original[c['claim_id']]
                for key in ['text','source_ids','period','direction','evidence_type']:self.assertEqual(c[key],old[key])
    def test_temporal_separation(self):
        other={c['claim_id'] for r in self.rows for c in r['claims_other']}
        selected={i for r in self.rows for t in r['themes_2026'] for i in t['claim_ids']}
        self.assertFalse(other&selected);self.assertEqual(len(other),10)
        self.assertTrue(all(c['period']=='2026' for r in self.rows for c in r['claims_2026']))
    def test_directions_retained_in_html(self):
        for r in self.rows:
            for c in r['claims_2026']+r['claims_other']:
                tag=self.soup.select_one('[data-claim-id="'+c['claim_id']+'"]')
                self.assertEqual(tag['data-direction'],c['direction']);self.assertEqual(tag['data-period'],c['period'])
    def test_no_2026_results(self):
        for r in self.rows:self.assertIsNone(r['registration_election']['votes']);self.assertIsNone(r['registration_election']['result'])
    def test_statuses_preserved(self):
        old={r['id']:r for r in load('data/sp/round-b/normalized.json')['candidates']}
        for k,r in old.items():self.assertEqual(self.by[k]['status'],r['status'])
        self.assertEqual(sum(r['status']=='RENÚNCIA' for r in self.rows),6)
    def test_photos_copied_by_identifier(self):
        for r in self.rows:
            p=ROOT/'sp/deputados-federais'/r['photo'];self.assertIn(r['id'],p.name)
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),r['photo_source']['sha256'])
    def test_photo_alt_and_dimensions(self):
        imgs=self.soup.select('.portrait img');self.assertEqual(len(imgs),249)
        for img in imgs:self.assertTrue(img.get('alt'));self.assertTrue(img.get('width'));self.assertTrue(img.get('height'))
    def test_history_only_previous_years(self):
        histories=[h for r in self.rows for h in r['history']]
        self.assertEqual(len(histories),555);self.assertTrue(all(h['year']<2026 for h in histories))
    def test_unique_html_ids(self):
        ids=[tag['id'] for tag in self.soup.select('[id]')];self.assertEqual(len(ids),len(set(ids)))
        self.assertEqual(len(self.soup.select('article.candidate')),249)
    def test_reference_integrity(self):
        for r in self.rows:
            sources={s['source_id'] for s in r['sources']}
            for c in r['claims_2026']+r['claims_other']:self.assertTrue(set(c['source_ids'])<=sources)
    def test_http_warning_counts(self):
        c=self.data['provenance']['upstream_source_link_check'];self.assertEqual(c['total'],75)
        self.assertEqual(c['accessible']+c['warning_count'],75)
        self.assertTrue(self.soup.select('.source-warning'))
    def test_url_validation(self):
        for u in ['javascript:alert(1)','data:text/html,evil','https://user:secret@evil.example/a','@handle','https://white space.example','file:///etc/passwd']:self.assertIsNone(B.safe_url(u))
        self.assertEqual(B.safe_url('HTTPS://EXAMPLE.ORG/CaseSensitive'),'https://example.org/CaseSensitive')
    def test_escaping(self):
        self.assertEqual(B.esc('<script>"&'), '&lt;script&gt;&quot;&amp;')
        self.assertNotIn('onclick=',self.html);self.assertNotIn('onerror=',self.html)
    def test_all_internal_targets(self):
        for path in ['sp/index.html','sp/deputados-federais/index.html']:
            file=ROOT/path;sp=BeautifulSoup(file.read_text(),'html.parser')
            for tag in sp.select('[href],[src]'):
                value=tag.get('href',tag.get('src'));u=urlsplit(value)
                if u.scheme or u.netloc:continue
                dest=(file.parent/unquote(u.path)).resolve() if u.path else file
                if dest.is_dir():dest=dest/'index.html'
                self.assertTrue(dest.exists(),str((value,dest)))
                if u.fragment:
                    target=sp if dest==file else BeautifulSoup(dest.read_text(),'html.parser')
                    self.assertIsNotNone(target.find(id=unquote(u.fragment)),value)
    def test_semantic_jsonld(self):
        data=json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertEqual(data['mainEntity']['numberOfItems'],249)
        self.assertTrue(data['mainEntity']['itemListOrder'].endswith('Unordered'))
        self.assertTrue(all('position' not in r for r in data['mainEntity']['itemListElement']))
    def test_no_api_dependency_runtime(self):
        js=(ROOT/'sp/deputados-federais/assets/app.js').read_text()
        self.assertNotIn('fetch(',js);self.assertNotIn('localStorage',js);self.assertNotIn('sessionStorage',js)
    def test_home_bounded_edit(self):
        before=subprocess.check_output(['git','show',BASE+':index.html'],cwd=ROOT).decode()
        after=(ROOT/'index.html').read_text()
        self.assertEqual(after.count(B.NAV_LINK),1);self.assertEqual(after.replace(B.NAV_LINK,''),before)
    def test_other_editions_byte_identical(self):
        for path in ['deputados-estaduais/index.html','rs/deputados-federais/index.html','pr/deputados-federais/index.html','pr/deputados-estaduais/index.html']:
            self.assertEqual((ROOT/path).read_bytes(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT),path)
    def test_source_inputs_unchanged(self):
        for path in ['data/sp/normalized.json','data/sp/research/records.json','data/sp/research/theme-evidence-2026.json','data/sp/round-b/normalized.json']:
            before=subprocess.check_output(['git','show','a2689717850d451b02e2ab8a3570d5acf204546c:'+path],cwd=ROOT)
            self.assertEqual((ROOT/path).read_bytes(),before,path)
    def test_zzz_deterministic_build(self):
        paths=list((ROOT/'sp').rglob('*'))+[ROOT/'index.html',ROOT/'sitemap.xml',ROOT/'data/sp/round-c/product.json']
        before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        subprocess.run(['python',str(ROOT/'tools/sp/round_c/build.py')],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()}
        self.assertEqual(before,after)
if __name__=='__main__':unittest.main(verbosity=2)

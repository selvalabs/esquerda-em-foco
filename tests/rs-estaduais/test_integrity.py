"""Data/editorial invariants. Coverage gaps are reported, not passed as research."""
from __future__ import annotations
import collections,csv,hashlib,json,re,unittest
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais';P=ROOT/'rs/deputados-estaduais'
def load(path):return json.loads(path.read_text(encoding='utf-8'))
class Integrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=load(D/'manifest.json');cls.raw=load(D/'candidates-official.json')
        cls.dataset=load(P/'dados.json');cls.records=cls.dataset['candidates']
        cls.soup=BeautifulSoup((P/'index.html').read_text(),'html.parser')
        cls.report=load(A/'build-report.json');cls.profiles=load(D/'profiles-official.json')
    def test_exact_census_projection(self):
        with (D/'raw/universo-rs-estaduais-2026.csv').open(encoding='utf-8',newline='') as f:universe=list(csv.DictReader(f,delimiter=';'))
        scope={p.upper() for p in self.manifest['scope']['parties']}
        expected={r['SQ_CANDIDATO'] for r in universe if r['SG_PARTIDO'].upper() in scope}
        self.assertEqual(len(universe),self.manifest['all_rs_state_count'])
        self.assertEqual(expected,{c['id'] for c in self.records});self.assertEqual(expected,{r['SQ_CANDIDATO'] for r in self.raw})
        self.assertEqual(len(self.records),self.manifest['selected_count'])
    def test_canonical_scope_not_reinvented(self):
        reference=load(ROOT/'config/party-scope-2026.json')['parties']
        self.assertEqual(self.manifest['scope']['parties'],reference)
        self.assertEqual(reference,['PCB','PCdoB','PCO','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP'])
    def test_scope_state_office_year(self):
        self.assertEqual(self.dataset['office_code'],7);self.assertEqual(self.dataset['state'],'RS');self.assertEqual(self.dataset['election_year'],2026)
        self.assertTrue(all(r['SG_UF']=='RS' and r['CD_CARGO']=='7' and r['ANO_ELEICAO']=='2026' for r in self.raw))
    def test_identifiers_and_numbers(self):
        self.assertEqual(len({c['id'] for c in self.records}),len(self.records));self.assertEqual(len({c['number'] for c in self.records}),len(self.records))
        raw={r['SQ_CANDIDATO']:r for r in self.raw}
        for c in self.records:self.assertRegex(c['number'],r'^\d{5}$');self.assertTrue(c['number'].startswith(raw[c['id']]['NR_PARTIDO']))
    def test_counters(self):
        self.assertEqual(dict(collections.Counter(c['party'] for c in self.records)),self.report['parties'])
        self.assertEqual(dict(collections.Counter(c['status'] for c in self.records)),self.report['statuses'])
        self.assertEqual(len(self.records),int(self.soup.select_one('.meta b').text))
    def test_all_individual_profiles_read(self):
        self.assertEqual(len(self.profiles),len(self.records))
        for c in self.records:
            p=self.profiles[c['id']];self.assertEqual(str(p['data']['id']),c['id']);self.assertEqual(str(p['data']['numero']),c['number'])
            self.assertEqual(str(p['data']['cargo']['codigo']),'7');self.assertEqual(p['data']['partido']['sigla'].upper(),c['party'].upper())
            self.assertEqual(p['data']['descricaoSituacao'],c['status']);self.assertTrue(c['status_checked_at'])
    def test_reconciliation_and_format_notes(self):
        audit=load(A/'reconciliation.json');self.assertEqual(audit['identity_mismatches'],[])
        self.assertTrue(all(x['identity_fields_match'] for x in audit['identity_checks']))
        self.assertTrue(all(x['classification']=='punctuation_or_whitespace_only' for x in audit.get('source_format_differences',[])))
    def test_source_hashes(self):
        for source in self.manifest['sources']:
            if 'sha256' in source:self.assertRegex(source['sha256'],r'^[a-f0-9]{64}$')
            for member in source.get('members',[]):self.assertRegex(member['sha256'],r'^[a-f0-9]{64}$')
    def test_photos_are_official_and_local(self):
        for c in self.records:
            self.assertIsNotNone(c['photo']);p=c['photo'];path=P/p['path'];self.assertTrue(path.is_file())
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),p['sha256'])
            self.assertIn(c['id'],p['source_member']);self.assertIn('cdn.tse.jus.br',p['source_url'])
    def test_all_candidates_rendered_exactly_once(self):
        cards=self.soup.select('article.candidate');self.assertEqual({c['data-tse-id'] for c in cards},{c['id'] for c in self.records})
        self.assertEqual(len(cards),len(self.records));ids=[n['id'] for n in self.soup.select('[id]')];self.assertEqual(len(ids),len(set(ids)))
    def test_no_current_election_results_or_votes(self):
        for c in self.records:
            for h in c['history']:
                if h['year']==2026:self.assertIsNone(h['votes']);self.assertNotIn(str(h.get('result','')).lower(),('eleito','suplente','nao eleito'))
    def test_historical_vote_population(self):
        sources=load(D/'votes-official.json')
        extra=load(D/'ad2-vote-index.json') if (D/'ad2-vote-index.json').exists() else {}
        offices={'presidente':'1','deputado estadual':'7','deputado federal':'6'}
        for c in self.records:
            for h in c['history']:
                if h.get('votes') is None:continue
                self.assertLess(h['year'],2026);self.assertFalse(h.get('round_note'))
                self.assertFalse(str(h.get('office','')).upper().startswith(('VICE','SUPLENTE')))
                if h.get('votes_evidence_id'):
                    source=extra[h['votes_evidence_id']];ctx=source['context']
                    self.assertEqual(source['current_candidate_id'],c['id'])
                    self.assertEqual(ctx['candidate_id'],h['candidate_id']);self.assertEqual(ctx['year'],h['year']);self.assertEqual(ctx['round'],h['round'])
                    self.assertEqual(ctx['office_code'],offices[h['office'].lower()]);self.assertEqual(h['votes'],source['votes'])
                    self.assertEqual(h['votes_source'],source['source_url']);self.assertEqual(h['votes_electoral_unit'],ctx['electoral_unit'])
                    self.assertEqual(h['uf'],ctx['electoral_unit'])
                    if ctx['electoral_unit']=='BR':
                        self.assertEqual(ctx['office_code'],'1');self.assertEqual(h['place'],'BRASIL')
                        self.assertTrue(source['member'].upper().endswith('_BR.CSV'));self.assertNotIn('_RS.',source['member'].upper())
                    else:self.assertEqual(ctx['electoral_unit'],'RS');self.assertTrue(source['member'].upper().endswith('_RS.CSV'))
                else:
                    self.assertEqual(h['uf'],'RS');source=sources[str(h['year'])]
                    self.assertEqual(h['votes'],source['totals'][h['candidate_id']+':'+str(h['round'])])
                self.assertIsNone(source['archive_sha256']);self.assertRegex(source['member_sha256'],r'^[a-f0-9]{64}$')
    def test_agendas_and_acts_require_reviewed_sources(self):
        editorial=load(D/'editorial.json') if (D/'editorial.json').exists() else {}
        for c in self.records:
            if c['pautas'] or c['activities']:
                self.assertTrue(editorial[c['id']]['reviewed']);self.assertTrue(c['editorial_sources']);self.assertTrue(c['editorial_checked_at'])
            for activity in c['activities']:self.assertTrue(activity['source']);self.assertTrue(activity['text'])
    def test_offices_require_current_institutional_evidence(self):
        for c in self.records:
            if c['current_office']:
                office=c['current_office'];self.assertTrue(office['checked_at']);self.assertTrue(office['source'])
                self.assertNotIn('tse.jus.br',office['source']);self.assertIn(office['verification'],('current_directory','current_individual_profile'))
    def test_unknown_office_is_not_claimed_absent(self):
        for c in self.records:
            if not c['current_office']:
                article=self.soup.find(id='candidato-'+c['id']);self.assertIn('Não confirmado nesta edição',article.get_text())
                self.assertIn('não equivale à ausência de mandato',article.get_text())
    def test_all_records_have_explicit_checks(self):
        for c in self.records:
            self.assertTrue(c['checks']['registro_validado']);self.assertTrue(c['checks']['historico_fonte_consultada'])
            self.assertTrue(c['checks']['links_declarados_auditados']);self.assertEqual(c['checks']['pautas_com_fonte_revisada'],bool(c['pautas']))
    def test_private_registration_fields_not_exported(self):
        serialized=(P/'dados.json').read_text().lower()
        for key in ('nr_cpf','cpf_candidato','nr_titulo_eleitoral','email_candidato','nr_cnpj','dt_nascimento','ds_cor_raca','ds_genero','endereco_residencial'):self.assertNotIn(key,serialized)
        for c in self.records:
            for x in c['sites']+c['socials']:
                p=urlsplit(x['url']);self.assertIsNone(p.username);self.assertIsNone(p.password)
    def test_no_scores_or_rankings_in_data(self):
        prohibited={'score','rank','ranking','electability','probability','recommended','ideological_score','overall_verdict','tier'}
        def walk(obj):
            if isinstance(obj,dict):
                self.assertFalse(prohibited.intersection(obj))
                for value in obj.values():walk(value)
            elif isinstance(obj,list):
                for item in obj:walk(item)
        walk(self.dataset)
    def test_links_safe_and_internal_targets_exist(self):
        for a in self.soup.select('a[href]'):
            href=a['href'];self.assertFalse(href.lower().startswith(('javascript:','data:')))
            if href.startswith('#') and len(href)>1:self.assertIsNotNone(self.soup.find(id=href[1:]),href)
            if a.get('target')=='_blank':self.assertIn('noopener',a.get('rel',[]))
        for image in self.soup.select('img[src]'):
            self.assertTrue(image.get('alt'));src=image['src']
            if not src.startswith(('http','data:')):self.assertTrue((P/src).exists(),src)
    def test_canonical_and_structured_data(self):
        canonical='https://selvalabs.github.io/esquerda-em-foco/rs/deputados-estaduais/'
        self.assertEqual(self.soup.select_one('link[rel="canonical"]')['href'],canonical);self.assertIn('Deputado Estadual',self.soup.title.text)
        self.assertEqual(self.soup.select_one('.office-title').text,'Deputado(a) Estadual')
        ld=json.loads(self.soup.select_one('script[type="application/ld+json"]').string)
        self.assertEqual(ld['mainEntity']['numberOfItems'],len(self.records));self.assertEqual(ld['mainEntity']['itemListOrder'],'https://schema.org/ItemListUnordered')
        self.assertNotIn('position',json.dumps(ld));self.assertEqual(ld['url'],canonical)
    def test_exports_and_opengraph_exist(self):
        from PIL import Image
        for name in ('dados.json','fontes.json','cobertura.json','candidaturas.csv','site.webmanifest','sitemap.xml','favicon.svg','assets/app.js'):self.assertTrue((P/name).is_file(),name)
        with Image.open(P/'assets/og-rs-estaduais.png') as im:self.assertEqual(im.size,(1200,630))
    def test_editorial_gaps_are_quantified(self):
        gaps=[c['id'] for c in self.records if not c['pautas']];self.assertEqual(gaps,self.report['editorial_gap_ids'])
        self.assertEqual(self.report['with_editorial_summary'],len(self.records)-len(gaps));self.assertEqual(self.report['editorial_gate'],'complete' if not gaps else 'documented_gaps')
    def test_template_unchanged(self):
        self.assertEqual(hashlib.sha256((ROOT/'rs/deputados-federais/index.html').read_bytes()).hexdigest(),self.report['template_sha256'])
        self.assertEqual(hashlib.sha256((P/'index.html').read_bytes()).hexdigest(),self.report['html_sha256'])
if __name__=='__main__':unittest.main()

"""Verifica a publicação do commit integrado; não trata sucesso do build como deploy.
Não faz nova pesquisa eleitoral. Repetições são limitadas à propagação do Pages.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
import json, os, subprocess, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
BASE='https://selvalabs.github.io/esquerda-em-foco/'
ENTRYPOINT='index.html'
EDITION_URL=BASE
registry_path=ROOT/'config/editions.json'
if registry_path.exists():
    registry=json.loads(registry_path.read_text())
    if registry['root_mode']=='global_home':
        edition=next(e for e in registry['editions'] if e['edition_id']=='2026-sc-federais')
        if edition['publication_status']!='published' or edition['current_path']!='/sc/deputados-federais/' or edition['entrypoint']!='sc/deputados-federais/index.html':
            raise RuntimeError('Rota publicada SC/Federais incompatível com o catálogo global')
        ENTRYPOINT=edition['entrypoint']
        EDITION_URL=BASE+edition['current_path'].lstrip('/')
EDITORIAL_PARAGRAPHS='data-eef-paragraph=' in (ROOT/ENTRYPOINT).read_text()
FILES=[ENTRYPOINT,'assets/pauta-filter-core.js','assets/pauta-filters.css','assets/pauta-v2.css',
       'assets/pauta-filters-v2.js','assets/sc-federais-filters-v2-data.js',
       'data/sc-semantic-v2-ui/payload.json','data/sc-semantic-v2-ui/manifest.json',
       'data/sc-semantic-v2/candidate-content.json','data/sc-semantic-v2/association-audit.json',
       'data/sc-semantic-v2/macrogroups.json']
if EDITORIAL_PARAGRAPHS:
    FILES+=['assets/pauta-filters-editorial.js','assets/editorial-selected.css']
if 'id="cqData"' in (ROOT/ENTRYPOINT).read_text():
    FILES=list(dict.fromkeys(FILES+[x['path'] for x in json.loads((ROOT/'data/global03/publication-files.json').read_text())['files']]))
OUT=Path('/tmp/sc-semantic-v2-ui-live');OUT.mkdir(parents=True,exist_ok=True)
SHA=os.environ.get('EXPECTED_SHA') or subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()


def match_text(card):
    """Read the specific matches, not the whole paragraph or a generic summary.
    PR #38 moved the same evidence into expandable notes alongside paragraphs.
    The expected UI variant comes from the checked-out HTML, not a test fallback.
    """
    if not EDITORIAL_PARAGRAPHS:
        return card.locator('.pauta-match').inner_text()
    notes=card.locator('.eef-filter-note')
    notes.first.wait_for(state='attached')
    if notes.count()==0: raise RuntimeError('Motivos específicos dos filtros não renderizados')
    for note in notes.all():
        if not note.evaluate('(e)=>e.open'):
            note.locator('summary').click()
        if note.locator('.eef-filter-exact a[href^="#pauta-fonte-"]').count()==0:
            raise RuntimeError('Correspondência sem referência de fonte')
    texts=card.locator('.eef-filter-note .eef-filter-exact').all_inner_texts()
    if not texts: raise RuntimeError('Correspondência sem texto específico')
    return '\n'.join(texts)


rows=[]
for attempt in range(1,25):
    rows=[]
    for path in FILES:
        url=(EDITION_URL if path==ENTRYPOINT else BASE+path)+'?verify='+SHA
        expected=sha256((ROOT/path).read_bytes()).hexdigest()
        row={'path':path,'url':url,'expected_sha256':expected,'matched':False}
        try:
            with urlopen(Request(url,headers={'Cache-Control':'no-cache','User-Agent':'EEF-PublicationCheck/2'}),timeout=15) as r:
                actual=sha256(r.read()).hexdigest()
                row.update(http_status=r.status,actual_sha256=actual,matched=r.status==200 and actual==expected)
        except Exception as e: row['error']=str(e)[:300]
        rows.append(row)
    print(json.dumps({'attempt':attempt,'matched':sum(r['matched'] for r in rows),'pending':[r['path'] for r in rows if not r['matched']]}),flush=True)
    if all(r['matched'] for r in rows): break
    time.sleep(10)
report={'status':'pending','expected_commit':SHA,'edition_url':EDITION_URL,'editorial_paragraphs':EDITORIAL_PARAGRAPHS,'checked_at':datetime.now(timezone.utc).isoformat(),'files':rows,'browser':[]}
try:
    if not all(r['matched'] for r in rows): raise RuntimeError('Bytes publicados ainda não correspondem ao commit')
    with sync_playwright() as p:
        browser=p.chromium.launch()
        if 'id="cqData"' in (ROOT/ENTRYPOINT).read_text():
            import sys
            sys.path.insert(0,str(ROOT/'tests/global_rollout'))
            import legacy_browser
            report['browser']=legacy_browser.sc(browser,BASE,OUT)
        else:
            for width in (390,1440):
                page=browser.new_page(viewport={'width':width,'height':900},locale='pt-BR',reduced_motion='reduce')
                errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                page.route('**/*',lambda r:r.continue_() if urlsplit(r.request.url).hostname=='selvalabs.github.io' else r.abort())
                page.goto(EDITION_URL+'?verify='+SHA,wait_until='networkidle')
                page.wait_for_function('Boolean(window.EEFTopicFilters)')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                initial=page.locator('.candidate:not([hidden])').count()
                chips=page.locator('[data-pauta-topic]').count()
                if initial!=48 or chips!=13: raise RuntimeError('Universo ou painel publicado não é v2')
                if width==390: page.locator('#pautaOpen').click()
                page.locator('[data-pauta-topic="economia-estado"]').click()
                if width==390:
                    page.screenshot(path=str(OUT/'390-painel.png'))
                    page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open && document.activeElement.id === "pautaOpen"')
                count=page.locator('.candidate:not([hidden])').count()
                ju=page.locator('#candidato-240002533832')
                specific_text=match_text(ju)
                correct=count==4 and 'Defende impostos proporcionais à renda e ao patrimônio.' in specific_text and 'Apoio declarado:' not in specific_text
                if not correct: raise RuntimeError('Correspondência de tributação incorreta na publicação')
                ju.evaluate('(e)=>e.scrollIntoView()');page.wait_for_timeout(80)
                page.screenshot(path=str(OUT/f'{width}-economia.png'))
                # Search covers all authored summaries, not just candidate names.
                # "Jú" also matches "jurídica" and "justiça" after accent normalization.
                search_query='impostos proporcionais'
                page.locator('#searchInput').fill(search_query)
                found=page.locator('.candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)')
                if found!=['240002533832']: raise RuntimeError('Busca textual inequívoca e filtro não combinam: '+str(found))
                page.locator('#searchInput').fill('')
                if width==390: page.locator('#pautaOpen').click()
                page.locator('[data-pauta-topic="economia-estado"]').click()
                page.locator('[data-pauta-topic="trabalho-renda"]').click()
                if width==390: page.keyboard.press('Escape');page.wait_for_function('!document.getElementById("pautaDialog").open && document.activeElement.id === "pautaOpen"')
                ana=page.locator('#candidato-240002533824')
                if '6×1' in match_text(ana) or '6×1' not in ana.locator('[data-pauta-section="historico"]').inner_text():
                    raise RuntimeError('Relato de voto foi misturado ao motivo de apoio')
                ana.evaluate('(e)=>e.scrollIntoView()');page.screenshot(path=str(OUT/f'{width}-blocos.png'))
                overflow=page.evaluate('document.documentElement.scrollWidth>innerWidth')
                if errors or overflow: raise RuntimeError(str({'errors':errors,'overflow':overflow}))
                report['browser'].append({'width':width,'initial_candidates':initial,'macro_buttons':chips,'economia_results':count,
                    'taxation_text_verified':True,'search_combined':True,'search_query':search_query,'search_candidate_ids':found,
                    'history_not_used_as_support':True,'specific_match_sources_checked':EDITORIAL_PARAGRAPHS,'js_errors':errors,'overflow':overflow})
                page.close()
        browser.close()
    report['status']='passed'
except Exception as e:
    report.update(status='failed',error=str(e));raise
finally:
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('LIVE_VERIFICATION '+json.dumps(report,ensure_ascii=False),flush=True)

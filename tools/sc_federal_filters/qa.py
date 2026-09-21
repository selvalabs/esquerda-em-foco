"""QA estático, combinatório e Chromium. Não afirma ensaio em aparelho físico/leitor de tela.
PRESERVATION_BASE deve ser a base efetiva do PR; por padrão usa o início do Round 2.
"""
from __future__ import annotations
from functools import partial
from hashlib import sha256
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import traceback
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from build import ROOT, OUT, MATRIX, TAXONOMY, build, strip_integration

BASE = os.environ.get('PRESERVATION_BASE', '89092b6192f5b06acba3fcb1ac7adef1af99b266')
SHOTS = Path('/tmp/eef-sc-federal-filters-screenshots')
SHOTS.mkdir(exist_ok=True, parents=True)
checks = []

def check(name: str, passed: bool, detail=None) -> None:
    checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    if not passed:
        raise AssertionError(name + ': ' + str(detail))


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def static_tests() -> tuple[dict, dict]:
    payload = json.loads((OUT / 'payload.json').read_text())
    matrix = json.loads(MATRIX.read_text())
    source = (ROOT / 'index.html').read_text()
    old = git('show', f'{BASE}:index.html').decode()
    check('HTML limitado às inserções e ao adaptador autorizados', strip_integration(source) == strip_integration(old))
    paths = git('ls-tree', '-r', '--name-only', BASE).decode().splitlines()
    allowed = ('tools/sc_federal_filters/', 'data/sc-federais-filters-v1/', 'docs/SC-FEDERAIS-FILTERS', 'tests/sc_federais_filters')
    explicit = {'index.html', 'assets/pauta-filter-core.js', 'assets/pauta-filters.js', 'assets/pauta-filters.css', 'assets/sc-federais-filters-data.js', '.github/workflows/sc-federais-filters.yml'}
    protected = [p for p in paths if p not in explicit and not p.startswith(allowed)]
    changed = [p for p in protected if not (ROOT / p).is_file() or (ROOT / p).read_bytes() != git('show', f'{BASE}:{p}')]
    check('Todos os demais arquivos da base preservados byte a byte', not changed, {'base': BASE, 'files': len(protected), 'changed': changed})
    soup, prior = BeautifulSoup(source, 'html.parser'), BeautifulSoup(old, 'html.parser')
    current_cards = {el['data-tse-id']: str(el) for el in soup.select('article.candidate')}
    prior_cards = {el['data-tse-id']: str(el) for el in prior.select('article.candidate')}
    check('48 cards com conteúdo e dados eleitorais intactos', len(current_cards) == 48 and current_cards == prior_cards)
    check('Navbar, rodapé, hero e configuração de métricas preservados', all(str(soup.select_one(sel)) == str(prior.select_one(sel)) for sel in ('#siteNav', '.persistent-footer', '.masthead')) and (ROOT / 'assets/metrics-config.js').read_bytes() == git('show', f'{BASE}:assets/metrics-config.js'))
    ids = [el['id'] for el in soup.select('[id]')]
    check('IDs de documento únicos', len(ids) == len(set(ids)))
    check('Todos os IDs antigos permanecem disponíveis', {el['id'] for el in prior.select('[id]')} <= set(ids))
    check('Um painel e um diálogo, sem duplicação mobile/desktop', len(soup.select('#pautaPanel')) == len(soup.select('#pautaDialog')) == 1)
    assoc = {a['association_id']: a for a in matrix['associations']}
    observed = []
    for candidate in payload['candidates']:
        for match in candidate['matches']:
            a = assoc[match['associationId']]
            check('Associação íntegra: ' + match['associationId'], a['eligible_current_support'] and a['direction'] == match['direction'] and a['candidate_id'] == candidate['id'] and a['topic_id'] == match['topicId'] and a['position_target'] == match['target'] and a['source_ids'] == match['sourceIds'] and a['period'] == match['period'])
            observed.append(match['associationId'])
    check('Conjunto filtrável exato, sem oposição/debate/histórico incluídos', len(observed) == len(set(observed)) and set(observed) == {a['association_id'] for a in matrix['associations'] if a['eligible_current_support']})
    for name in ('pauta-filter-core.js', 'pauta-filters.js', 'sc-federais-filters-data.js'):
        result = subprocess.run(['node', '--check', str(ROOT / 'assets' / name)], capture_output=True, text=True)
        check('Sintaxe JavaScript: ' + name, result.returncode == 0, result.stderr)
    unit = subprocess.run(['node', '--test', 'tests/sc_federais_filters.test.cjs'], cwd=ROOT, capture_output=True, text=True)
    (OUT / 'unit-tests.txt').write_text(unit.stdout + unit.stderr)
    check('Testes combinatórios Node contra a matriz', unit.returncode == 0, unit.stdout[-2500:])
    generated = [ROOT / 'index.html', ROOT / 'assets/sc-federais-filters-data.js', OUT / 'payload.json', OUT / 'manifest.json']
    before = {str(p): sha256(p.read_bytes()).hexdigest() for p in generated}
    build()
    check('Reconstrução idempotente', before == {str(p): sha256(p.read_bytes()).hexdigest() for p in generated})
    check('Catálogo e matriz canônicos não foram modificados', MATRIX.read_bytes() == git('show', f'{BASE}:data/sc-federais-topics-v1/matrix.json') and TAXONOMY.read_bytes() == git('show', f'{BASE}:config/topics-v1.json'))
    return payload, matrix


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def browser_tests(payload: dict, matrix: dict) -> None:
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/'
    records = {c['candidate_id']: c for c in matrix['candidates']}
    totals = {t['id']: t['count'] for t in payload['topics']}
    def expected(selected, mode='any'):
        return {c['candidate_id'] for c in records.values() if not selected or (all(t in c['current_support_topic_ids'] for t in selected) if mode == 'all' else any(t in c['current_support_topic_ids'] for t in selected))}
    def visible(page):
        return page.locator('.candidate:not([hidden])').evaluate_all('(els) => els.map(el => el.dataset.tseId)')
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for width in (320, 360, 390, 430, 768, 1024, 1440):
                label = str(width) + 'px: '
                context = browser.new_context(viewport={'width': width, 'height': 900}, locale='pt-BR', reduced_motion='reduce')
                context.add_init_script("""{ const D=Date; class FixedDate extends D { constructor(...a) { super(...(a.length?a:['2026-09-21T15:00:00Z'])); } static now(){return new D('2026-09-21T15:00:00Z').getTime();} } window.Date=FixedDate; }""")
                page = context.new_page()
                errors, requests = [], []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: requests.append(r.url))
                page.route('**/*', lambda route: route.continue_() if urlsplit(route.request.url).hostname == '127.0.0.1' else route.abort())
                page.goto(url, wait_until='networkidle')
                page.wait_for_function('Boolean(window.EEFTopicFilters)')
                page.add_style_tag(content='html{scroll-behavior:auto!important}')
                original_order = visible(page)
                check(label + '48 fichas visíveis sem filtros', len(original_order) == 48)
                check(label + 'Um painel, IDs únicos', page.locator('#pautaPanel').count() == 1 and page.evaluate('(()=>{const a=[...document.querySelectorAll("[id]")].map(e=>e.id);return a.length===new Set(a).size})()'))
                check(label + 'Sem overflow horizontal inicial', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                check(label + 'Botões apenas com categorias elegíveis', page.locator('[data-pauta-topic]').count() == len(payload['topics']))
                if width <= 980:
                    check(label + 'Entrada mobile junto à busca', page.locator('#pautaOpen').is_visible())
                    check(label + 'Painel fechado por padrão', not page.locator('#pautaPanel').is_visible())
                else:
                    check(label + 'Painel abaixo dos partidos', page.locator('#pautaPanel').is_visible() and page.evaluate('document.querySelector(".party-nav").compareDocumentPosition(document.getElementById("pautaPanel")) & Node.DOCUMENT_POSITION_FOLLOWING'))
                    check(label + 'Sidebar cabe entre navbar e rodapé', page.locator('.rail').evaluate('(el)=>el.clientHeight<=innerHeight-document.getElementById("siteNav").getBoundingClientRect().height-document.querySelector(".persistent-footer").getBoundingClientRect().height'))
                def open_panel():
                    if width <= 980 and not page.locator('#pautaDialog').is_visible():
                        page.locator('#pautaOpen').click()
                        page.wait_for_function('document.getElementById("pautaDialog").open')
                def close_panel():
                    if page.locator('#pautaDialog').is_visible():
                        page.locator('#pautaClose').click()
                        page.wait_for_function('!document.getElementById("pautaDialog").open')
                def choose(topic):
                    open_panel()
                    page.locator(f'[data-pauta-topic="{topic}"]').click()
                def verify(selected, mode='any'):
                    actual = visible(page)
                    exp = expected(selected, mode)
                    check(label + 'Resultado ' + mode + ' ' + ','.join(selected), set(actual) == exp, {'actual': actual, 'expected': sorted(exp)})
                    check(label + 'Filtro conserva a rotação', actual == [cid for cid in original_order if cid in exp])
                    chips = page.locator('[data-pauta-topic]').evaluate_all('(els)=>Object.fromEntries(els.map(e=>[e.dataset.pautaTopic,Number(e.querySelector(".pauta-chip__count").textContent)]))')
                    check(label + 'Contagens estáticas e corretas', chips == totals)
                choose('saude')
                verify(['saude'])
                check(label + 'Estado de seleção acessível', page.locator('[data-pauta-topic="saude"]').get_attribute('aria-pressed') == 'true')
                choose('educacao')
                verify(['saude', 'educacao'])
                page.locator('input[name="pauta-mode"][value="all"]').check()
                verify(['saude', 'educacao'], 'all')
                check(label + 'Objeto e sentido explícitos no resultado', all(page.locator(f'#candidato-{cid} .pauta-match').is_visible() if width > 980 else page.locator(f'#candidato-{cid} .pauta-match').count() == 1 for cid in expected(['saude','educacao'],'all')))
                if width <= 980:
                    check(label + 'Foco dentro do diálogo', page.evaluate('document.getElementById("pautaDialog").contains(document.activeElement)'))
                    page.locator('#pautaShowResults').focus()
                    page.keyboard.press('Tab')
                    check(label + 'Tab não escapa do diálogo', page.evaluate('document.getElementById("pautaDialog").contains(document.activeElement)'))
                    page.locator('#pautaClose').focus()
                    page.keyboard.press('Shift+Tab')
                    check(label + 'Shift Tab não escapa do diálogo', page.evaluate('document.getElementById("pautaDialog").contains(document.activeElement)'))
                    page.keyboard.press('Escape')
                    page.wait_for_function('!document.getElementById("pautaDialog").open')
                    page.wait_for_timeout(40)
                    check(label + 'Escape devolve foco ao botão', page.evaluate('document.activeElement.id === "pautaOpen"'))
                    open_panel()
                    check(label + 'Reabrir preserva as seleções', page.locator('[data-pauta-topic="saude"]').get_attribute('aria-pressed') == 'true' and page.locator('input[value="all"]').is_checked())
                    page.screenshot(path=str(SHOTS / f'{width}-painel.png'))
                    close_panel()
                else:
                    page.screenshot(path=str(SHOTS / f'{width}-filtro.png'))
                page.locator('#searchInput').fill('caren')
                check(label + 'Busca e AND combinados', visible(page) == ['240002533828'])
                page.locator('#searchInput').fill('jessica')
                check(label + 'Busca encontra outra ficha anteriormente oculta sem mudar temas', set(visible(page)) == (expected(['saude','educacao'],'all') & {'240002537838'}))
                page.locator('#searchInput').fill('zzz-inexistente')
                check(label + 'Estado sem resultados', not visible(page) and page.locator('#pautaEmpty').is_visible())
                page.locator('#pautaEmpty [data-pauta-reset="topics"]').click()
                check(label + 'Limpar pautas preserva texto buscado', page.locator('#searchInput').input_value() == 'zzz-inexistente' and not visible(page))
                page.locator('#pautaEmpty [data-pauta-reset="all"]').click()
                check(label + 'Limpar tudo restaura 48 na mesma ordem', visible(page) == original_order)
                choose('saude')
                close_panel()
                page.evaluate("location.hash='#candidato-240002533818'")
                page.wait_for_function('!document.getElementById("candidato-240002533818").hidden')
                check(label + 'Deep link revela ficha sem associação', len(visible(page)) == 48 and page.locator('#pautaNotice').is_visible())
                check(label + 'Deep link permanece na URL', page.url.endswith('#candidato-240002533818'))
                page.evaluate("location.hash='#pauta-contexto-240002533824'")
                page.wait_for_function('document.getElementById("pauta-contexto-240002533824").open')
                check(label + 'Link abre Fontes e contexto', page.locator('#pauta-contexto-240002533824').get_attribute('open') is not None)
                page.evaluate('window.scrollTo(0,1400)')
                page.wait_for_timeout(40)
                check(label + 'Navbar continua sticky', abs(page.locator('#siteNav').bounding_box()['y']) <= 1)
                if width <= 760:
                    page.locator('#siteNavMenu').click()
                    check(label + 'Menu hambúrguer preservado', page.locator('#siteNavMenu').get_attribute('aria-expanded') == 'true')
                    page.keyboard.press('Escape')
                    check(label + 'Menu fecha com Escape', page.locator('#siteNavMenu').get_attribute('aria-expanded') == 'false')
                check(label + 'Nenhuma preferência persistida ou enviada à API', page.evaluate('localStorage.length===0 && sessionStorage.length===0 && document.cookie===""') and not any('/api/metrics/' in u for u in requests))
                check(label + 'Sem overflow após interação', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
                check(label + 'Sem erro JavaScript', not errors, errors)
                if width == 390:
                    open_panel()
                    page.set_viewport_size({'width':1440,'height':900})
                    page.wait_for_function('!document.getElementById("pautaDialog").open && document.getElementById("pautaSidebarHost").contains(document.getElementById("pautaPanel"))')
                    check('Resize mobile → desktop não duplica painel', page.locator('#pautaPanel').count() == 1)
                    page.set_viewport_size({'width':390,'height':900})
                    open_panel()
                    page.locator('#pautaShowResults').click()
                    page.wait_for_function('!document.getElementById("pautaDialog").open')
                    check('Ver resultados fecha painel e foca conteúdo', page.evaluate('document.activeElement.matches(".candidate, #searchInput")'))
                    open_panel()
                    page.mouse.click(3, 3)
                    page.wait_for_function('!document.getElementById("pautaDialog").open')
                    check('Toque fora fecha painel', not page.locator('#pautaDialog').is_visible())
                context.close()
            context = browser.new_context(java_script_enabled=False, viewport={'width':390,'height':900})
            page = context.new_page()
            page.route('**/*', lambda route: route.continue_() if urlsplit(route.request.url).hostname == '127.0.0.1' else route.abort())
            page.goto(url, wait_until='domcontentloaded')
            check('Sem JavaScript: 48 fichas legíveis e controles inativos ocultos', len(visible(page)) == 48 and not page.locator('#pautaPanel').is_visible() and not page.locator('#pautaToolbar').is_visible())
            context.close()
            context = browser.new_context(viewport={'width':390,'height':900})
            page = context.new_page()
            page.route('**/*', lambda route: route.abort() if 'sc-federais-filters-data.js' in route.request.url or urlsplit(route.request.url).hostname != '127.0.0.1' else route.continue_())
            page.goto(url, wait_until='networkidle')
            check('Falha no asset de dados: conteúdo não desaparece', len(visible(page)) == 48 and not page.locator('#pautaToolbar').is_visible())
            page.locator('#searchInput').fill('caren')
            check('Falha no asset de filtros não quebra busca original', '240002533828' in visible(page))
            context.close()
        finally:
            browser.close()
            server.shutdown()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        data, matrix = static_tests()
        browser_tests(data, matrix)
    except Exception as error:
        checks.append({'name':'Execução', 'passed':False, 'detail':str(error), 'trace':traceback.format_exc()})
    result = {'status':'passed' if all(c['passed'] for c in checks) else 'failed', 'base_commit':BASE,
              'checked_commit':git('rev-parse','HEAD').decode().strip(), 'checks_count':len(checks),
              'failed_count':sum(not c['passed'] for c in checks), 'checks':checks,
              'test_scope':'Chromium em sete larguras; imagens externas bloqueadas. Sem aparelho físico nem leitor de tela real. Sem nova pesquisa eleitoral.'}
    (OUT / 'qa.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'}, ensure_ascii=False))
    if result['failed_count']:
        print(json.dumps([c for c in checks if not c['passed']], ensure_ascii=False))
        sys.exit(1)


if __name__ == '__main__':
    main()

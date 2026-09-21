"""QA reproduzível da alteração documental. Não valida mérito nem previsão eleitoral."""
from __future__ import annotations
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import threading
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from build_review import main as build

ROOT = Path('data/sc-federais-pautas')
OUT = Path('artifacts/sc-federais-pautas')
OUT.mkdir(parents=True, exist_ok=True)
BASE = '810a7896b3355254d50852761a41bae31ce3f567'
checks = []
warnings = []
report = {'status': 'running', 'scope': 'SC/Federais', 'checks': checks, 'warnings': warnings, 'browser': 'Chromium via Playwright', 'limitations': ['Não é teste em aparelho físico nem em Safari/Firefox.', 'Recursos externos são bloqueados no teste de interface; disponibilidade das fontes é registrada separadamente.']}


def check(name: str, condition: bool, details: object = None) -> None:
    item = {'name': name, 'passed': bool(condition)}
    if details is not None:
        item['details'] = details
    checks.append(item)
    assert condition, f'{name}: {details}'


def canonical_shell(html: str) -> str:
    html = re.sub(r'<!-- sc-federal-pautas:method:start -->[\s\S]*?<!-- sc-federal-pautas:method:end -->\n?', '', html)
    html = re.sub(r'<link[^>]*data-sc-federal-pautas="1"[^>]*>\n?', '', html)
    html = re.sub(r'\n?<details class="pauta-evidence"[\s\S]*?</details>', '', html)
    def clean_card(m: re.Match) -> str:
        card = re.sub(r'<p class="pauta">[\s\S]*?</p>', '<p class="pauta">REVIEWED</p>', m.group())
        card = re.sub(r'data-has-pauta="[^"]*"', 'data-has-pauta="REVIEWED"', card)
        return re.sub(r'data-search="[^"]*"', 'data-search="REVIEWED"', card)
    return re.sub(r'<article class="candidate"[\s\S]*?</article>', clean_card, html)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run() -> None:
    original = subprocess.check_output(['git','show', f'{BASE}:index.html']).decode('utf-8')
    current = Path('index.html').read_text(encoding='utf-8')
    baseline = json.loads((ROOT / 'baseline.json').read_text(encoding='utf-8'))
    records = json.loads((ROOT / 'review.json').read_text(encoding='utf-8'))['candidates']
    check('48 registros individuais completos', len(records) == 48 and len({r['id'] for r in records}) == 48)
    check('Alteração HTML limitada aos blocos autorizados', canonical_shell(original) == canonical_shell(current))
    protected_bad = [name for name, digest in baseline['protected_sha256'].items() if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest() != digest]
    check('Arquivos protegidos preservados byte a byte', not protected_bad, {'count':len(baseline['protected_sha256']), 'changed':protected_bad})
    soup = BeautifulSoup(current, 'html.parser')
    check('48 resumos e 48 contextos acessíveis', len(soup.select('.candidate .pauta')) == 48 and len(soup.select('.candidate .pauta-evidence')) == 48)
    check('Um único método e stylesheet da revisão', len(soup.select('#metodo-pautas')) == 1 and len(soup.select('[data-sc-federal-pautas]')) == 1)
    ids = [n.get('id') for n in soup.select('[id]')]
    check('IDs de documento únicos', len(ids) == len(set(ids)))
    check('Nenhum filtro ativado', not soup.select('[data-topics], .topic-filter, #topicFilters'))
    for record in records:
        card = soup.select_one(f'article[data-tse-id="{record["id"]}"]')
        check(f'Identidade e fontes: {record["id"]}', card.select_one('h3').get_text(' ',strip=True) == record['name'] and len(card.select('.pauta-evidence__sources li')) == len(record['sources']))
    generated = [Path('index.html'), ROOT/'review.json', ROOT/'coverage.json', ROOT/'audit.csv', ROOT/'taxonomy-proposal.json', Path('docs/SC-FEDERAIS-PAUTAS-RESULTADOS.md'), Path('docs/SC-FEDERAIS-PAUTAS-TAXONOMIA.md')]
    hashes = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in generated}
    build()
    check('Compilação idempotente', hashes == {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in generated})
    (OUT / 'baseline.html').write_text(original, encoding='utf-8')
    server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(Path.cwd())))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    root_url = f'http://127.0.0.1:{server.server_port}'
    report['viewports'] = []
    def only_local(route):
        if route.request.url.startswith(root_url) or route.request.url.startswith('data:'):
            route.continue_()
        else:
            route.abort()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            report['browser_version'] = browser.version
            for width in [320, 360, 390, 768, 1280, 1440]:
                context = browser.new_context(viewport={'width':width,'height':900}, timezone_id='America/Sao_Paulo')
                context.route('**/*', only_local)
                context.add_init_script("""{ const D = Date; const t = D.parse('2026-09-21T15:00:00Z'); window.Date = class extends D { constructor(...args) { super(...(args.length ? args : [t])); } static now() { return t; } }; }""")
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda err: errors.append(str(err)))
                page.goto(root_url + '/artifacts/sc-federais-pautas/baseline.html', wait_until='domcontentloaded')
                page.wait_for_timeout(100)
                baseline_width = page.evaluate('document.documentElement.scrollWidth')
                errors.clear()
                page.goto(root_url + '/', wait_until='domcontentloaded')
                page.wait_for_timeout(150)
                check(f'{width}px: sem erro JavaScript', not errors, errors)
                check(f'{width}px: todas as fichas visíveis inicialmente', page.locator('.candidate:visible').count() == 48)
                current_width = page.evaluate('document.documentElement.scrollWidth')
                check(f'{width}px: sem novo overflow horizontal', current_width <= max(width, baseline_width) + 1, {'before':baseline_width,'after':current_width,'viewport':width})
                if current_width > width + 1:
                    warnings.append(f'Overflow preexistente de {current_width-width}px na largura {width}px; não introduzido pela revisão.')
                search = page.locator('#searchInput')
                search.fill('Nandja')
                check(f'{width}px: busca individual', page.locator('.candidate:visible').count() == 1 and 'Nandja' in page.locator('.candidate:visible h3').inner_text())
                search.fill('zzzz-pauta-sem-resultado')
                check(f'{width}px: busca sem resultado', page.locator('.candidate:visible').count() == 0)
                search.fill('')
                check(f'{width}px: busca limpa restaura população', page.locator('.candidate:visible').count() == 48)
                expected = page.evaluate("""() => { const a=[...document.querySelectorAll('.party-section')].map(e=>e.dataset.partySection); return [...a].sort((a,b)=>a.localeCompare(b,'pt-BR',{sensitivity:'base'})); }""")
                actual = page.locator('.party-section').evaluate_all('(els)=>els.map(e=>e.dataset.partySection)')
                nav = page.locator('.party-nav [data-nav-party]').evaluate_all('(els)=>els.map(e=>e.dataset.navParty)')
                check(f'{width}px: ordem inicial e índice de partidos sincronizados', actual == expected == nav)
                page.evaluate('window.scrollTo({top:900,behavior:"instant"})')
                page.wait_for_timeout(60)
                nav_top = page.locator('#siteNav').bounding_box()['y']
                check(f'{width}px: navbar sticky preservada', abs(nav_top) < 2, nav_top)
                if width <= 760:
                    button = page.locator('#siteNavMenu')
                    button.click()
                    check(f'{width}px: hambúrguer abre', button.get_attribute('aria-expanded') == 'true' and page.locator('#siteNavLinks').is_visible())
                    page.keyboard.press('Escape')
                    check(f'{width}px: hambúrguer fecha com Escape', button.get_attribute('aria-expanded') == 'false')
                details = page.locator('#pauta-contexto-240002533833')
                summary = details.locator('summary')
                summary.focus()
                summary.press('Enter')
                check(f'{width}px: evidências abrem por teclado', details.get_attribute('open') is not None)
                bounds = details.bounding_box()
                check(f'{width}px: contexto contido no viewport', bounds['x'] >= -1 and bounds['x'] + bounds['width'] <= width + 1)
                page.screenshot(path=str(OUT / f'contexto-{width}.png'))
                summary.press('Enter')
                check(f'{width}px: evidências fecham por teclado', details.get_attribute('open') is None)
                page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
                page.screenshot(path=str(OUT / f'topo-{width}.png'))
                report['viewports'].append({'width':width,'height':900,'document_width':current_width,'baseline_document_width':baseline_width})
                context.close()
            context = browser.new_context(viewport={'width':1280,'height':900}, timezone_id='America/Sao_Paulo')
            context.route('**/*', only_local)
            context.add_init_script("""{ const D = Date; const t = D.parse('2026-09-22T15:00:00Z'); window.Date = class extends D { constructor(...args) { super(...(args.length ? args : [t])); } static now() { return t; } }; }""")
            page = context.new_page()
            page.goto(root_url + '/', wait_until='domcontentloaded')
            result = page.evaluate("""() => { const cmp=(a,b)=>a.localeCompare(b,'pt-BR',{sensitivity:'base'}); const rotate=a=>a.slice(1).concat(a.slice(0,1)); const sections=[...document.querySelectorAll('.party-section')]; const parties=sections.map(e=>e.dataset.partySection); const expected=rotate([...parties].sort(cmp)); const candidates=sections.every(s=>{const names=[...s.querySelectorAll('.candidate h3')].map(e=>e.textContent.trim()); return JSON.stringify(names)===JSON.stringify(rotate([...names].sort(cmp)));}); const nav=[...document.querySelectorAll('.party-nav [data-nav-party]')].map(e=>e.dataset.navParty); return {parties:JSON.stringify(parties)===JSON.stringify(expected),candidates,nav:JSON.stringify(nav)===JSON.stringify(expected)}; }""")
            check('Rotação em 22/09: partidos, candidaturas e índice avançam uma posição', all(result.values()), result)
            context.close()
            browser.close()
    finally:
        server.shutdown()
    report['status'] = 'passed'
    report['passed_checks'] = sum(c['passed'] for c in checks)
    report['index_sha256'] = hashlib.sha256(Path('index.html').read_bytes()).hexdigest()


if __name__ == '__main__':
    try:
        run()
    except Exception as error:
        report['status'] = 'failed'
        report['error'] = str(error)
        raise
    finally:
        (ROOT / 'qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'qa': report['status'], 'checks':len(checks), 'warnings':warnings, 'error':report.get('error')}, ensure_ascii=False))

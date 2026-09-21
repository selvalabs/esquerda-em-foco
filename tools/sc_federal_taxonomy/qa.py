"""QA da integração atual, independente do qa.json histórico da pesquisa."""
from __future__ import annotations
import hashlib
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from build import eligibility, run as build_matrix
from prepare import run as prepare_review, INTEGRATION_BASE

OUT = Path('data/sc-federais-topics-v1')
CHECKS = []


def check(name, condition, details=None):
    CHECKS.append({'name': name, 'passed': bool(condition), 'details': details})
    if not condition:
        print('FAIL ' + name + ': ' + str(details), flush=True)


def git(*args):
    return subprocess.check_output(['git', *args])


def skeleton(text):
    text = re.sub(r'<!-- sc-federal-pautas:method:start -->[\s\S]*?<!-- sc-federal-pautas:method:end -->\n?', '', text)
    text = re.sub(r'<link[^>]*data-sc-federal-pautas="1"[^>]*>\n?', '', text)
    text = re.sub(r'\n?<details class="pauta-evidence"[\s\S]*?</details>', '', text)
    text = re.sub(r'<p class="pauta">[\s\S]*?</p>', '<p class="pauta">ALLOWED</p>', text)
    text = re.sub(r'data-search="[^"]*"', 'data-search="ALLOWED"', text)
    return re.sub(r'data-has-pauta="(?:true|false)"', 'data-has-pauta="ALLOWED"', text)


def protected(base):
    rows = git('ls-tree', '-r', '-z', base).split(b'\0')
    changed, count = [], 0
    for raw in rows:
        if not raw:
            continue
        info, path_raw = raw.split(b'\t', 1)
        mode, kind, expected = info.decode().split()
        path = path_raw.decode()
        if kind != 'blob' or path == 'index.html':
            continue
        count += 1
        p = Path(path)
        content = p.read_bytes() if p.is_file() else b''
        actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
        if actual != expected:
            changed.append(path)
    return count, changed


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass


def browser_checks():
    server = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    url = f'http://127.0.0.1:{server.server_port}/index.html'
    screenshots = Path('/tmp/sc-federais-round1-screenshots')
    screenshots.mkdir(exist_ok=True)
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            for width in (320, 360, 390, 430, 768, 1024, 1440):
                context = browser.new_context(viewport={'width': width, 'height': 900})
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith('http://127.0.0.1:') else route.abort())
                page = context.new_page()
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(url, wait_until='domcontentloaded')
                check(f'{width}px: 48 fichas e 48 contextos', page.locator('.candidate').count() == 48 and page.locator('.pauta-evidence').count() == 48)
                check(f'{width}px: sem scroll horizontal', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                check(f'{width}px: nenhum filtro visual', page.locator('[data-topic-filter],#topicFilters,#topic-filter').count() == 0)
                page.locator('#searchInput').fill('Kerexu')
                check(f'{width}px: busca isolada', page.locator('.candidate:not([hidden])').count() == 1)
                page.locator('#searchInput').fill('zzzz-sem-correspondencia-zzzz')
                check(f'{width}px: busca sem resultado', page.locator('.candidate:not([hidden])').count() == 0)
                page.locator('#searchInput').fill('')
                check(f'{width}px: limpar busca restaura 48', page.locator('.candidate:not([hidden])').count() == 48)
                card = page.locator('.candidate').first
                summary = card.locator('.pauta-evidence > summary')
                summary.click()
                check(f'{width}px: fontes e contexto abrem', card.locator('.pauta-evidence').get_attribute('open') is not None)
                summary.click()
                check(f'{width}px: contexto fecha', card.locator('.pauta-evidence').get_attribute('open') is None)
                page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,1200)")
                page.wait_for_timeout(100)
                nav = page.locator('#siteNav').bounding_box()
                check(f'{width}px: navbar permanece sticky', nav is not None and abs(nav['y']) <= 1, nav)
                if width <= 760:
                    page.locator('#siteNavMenu').click()
                    check(f'{width}px: hamburger abre', page.locator('#siteNavMenu').get_attribute('aria-expanded') == 'true')
                    page.keyboard.press('Escape')
                    check(f'{width}px: Escape fecha', page.locator('#siteNavMenu').get_attribute('aria-expanded') == 'false')
                else:
                    check(f'{width}px: links desktop visíveis', page.locator('#siteNavLinks').is_visible())
                page.evaluate('window.scrollTo(0,0)')
                page.wait_for_timeout(100)
                page.screenshot(path=str(screenshots / f'{width}.png'))
                check(f'{width}px: sem erro JavaScript', not errors, errors)
                context.close()
            orders = []
            for day in (21, 22):
                context = browser.new_context(viewport={'width': 1440, 'height': 900})
                context.route('**/*', lambda route: route.continue_() if route.request.url.startswith('http://127.0.0.1:') else route.abort())
                stamp = f'2026-09-{day:02d}T15:00:00-03:00'
                context.add_init_script(f"{{ const NativeDate=Date; const fixed=new NativeDate('{stamp}').getTime(); globalThis.Date=class extends NativeDate{{constructor(...a){{super(...(a.length?a:[fixed]));}}static now(){{return fixed;}}}}; }}")
                page = context.new_page()
                page.goto(url, wait_until='domcontentloaded')
                orders.append(page.evaluate("""() => ({parties:[...document.querySelectorAll('.party-section')].map(s=>s.dataset.partySection), nav:[...document.querySelectorAll('.party-nav [data-nav-party]')].map(a=>a.dataset.navParty), candidates:Object.fromEntries([...document.querySelectorAll('.party-section')].map(s=>[s.dataset.partySection,[...s.querySelectorAll('.candidate')].map(c=>({id:c.dataset.tseId,name:c.querySelector('h3').textContent.trim()}))]))})"""))
                if day == 21:
                    check('Época: partidos e nomes alfabéticos', page.evaluate("""() => {const cmp=(a,b)=>a.localeCompare(b,'pt-BR',{sensitivity:'base'});const eq=a=>JSON.stringify(a)===JSON.stringify([...a].sort(cmp));return eq([...document.querySelectorAll('.party-section')].map(s=>s.dataset.partySection))&&[...document.querySelectorAll('.candidate-list')].every(l=>eq([...l.querySelectorAll('h3')].map(e=>e.textContent.trim())));} """))
                context.close()
            check('Rotação de um partido por dia', orders[1]['parties'] == orders[0]['parties'][1:] + orders[0]['parties'][:1])
            check('Índice acompanha a rotação', all(o['nav'] == o['parties'] for o in orders))
            for party, before in orders[0]['candidates'].items():
                check(f'Rotação dos candidatos: {party}', orders[1]['candidates'][party] == before[1:] + before[:1])
            browser.close()
    finally:
        server.shutdown()
        server.server_close()


def run():
    base = os.getenv('PRESERVATION_BASE') or INTEGRATION_BASE
    before = git('show', f'{base}:index.html').decode('utf-8')
    after = Path('index.html').read_text(encoding='utf-8')
    count, changed = protected(base)
    check('Demais arquivos do main preservados byte a byte', not changed, {'base': base, 'count': count, 'changed': changed})
    check('HTML alterado somente nos blocos autorizados', skeleton(before) == skeleton(after))
    soup = BeautifulSoup(after, 'html.parser')
    ids = [n['id'] for n in soup.select('[id]')]
    check('IDs únicos', len(ids) == len(set(ids)))
    missing = sorted({a['href'] for a in soup.select('a[href^="#"]') if len(a['href']) > 1 and a['href'][1:] not in ids})
    check('Âncoras internas preservadas', not missing, missing)
    matrix = json.loads((OUT / 'matrix.json').read_text())
    check('Todas as 48 fichas na matriz', len(matrix['candidates']) == 48)
    check('19 lacunas não recebem associações', sum(not c['association_ids'] for c in matrix['candidates']) == 19)
    check('29 fichas mantêm rastreabilidade', sum(bool(c['association_ids']) for c in matrix['candidates']) == 29)
    for a in matrix['associations']:
        check('Fonte/objeto: ' + a['association_id'], bool(a['source_ids']) and bool(a['position_target']))
        if a['direction'] not in ('apoio', 'prioridade'):
            check('Sem apoio inferido: ' + a['association_id'], not a['eligible_current_support'])
        if a['period'] != '2026' or a['attribution'] == 'joint_pending':
            check('Temporalidade/atribuição: ' + a['association_id'], not a['eligible_current_position'] and not a['eligible_current_support'])
    for coverage, period, direction in [('material_eleitoral','2026','oposicao'),('registro_historico','2023','apoio'),('material_conjunto','2026','apoio'),('apresentacao_eleitoral_sem_data','sem_data','apoio')]:
        check(f'Regra negativa {coverage}/{direction}', not eligibility(coverage, period, None, direction)[1])
    outputs = ['index.html', str(OUT / 'matrix.json'), str(OUT / 'coverage.json'), 'docs/SC-FEDERAIS-TOPICS-V1.md']
    hashes = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in outputs}
    prepare_review()
    build_matrix()
    check('Reconstrução idempotente', hashes == {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in outputs})
    browser_checks()
    result = {'status': 'passed' if all(c['passed'] for c in CHECKS) else 'failed', 'base_commit': base,
              'checked_commit': git('rev-parse', 'HEAD').decode().strip(), 'checks_count': len(CHECKS),
              'failed_count': sum(not c['passed'] for c in CHECKS), 'checks': CHECKS,
              'index_sha256': hashlib.sha256(Path('index.html').read_bytes()).hexdigest(),
              'matrix_sha256': hashlib.sha256((OUT / 'matrix.json').read_bytes()).hexdigest(),
              'browser_note': 'Chromium; imagens externas bloqueadas. Capturas no artifact do workflow; não equivale a ensaio em aparelho físico.'}
    (OUT / 'integration-qa.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'}, ensure_ascii=False))
    return result['failed_count'] == 0


if __name__ == '__main__':
    sys.exit(0 if run() else 1)

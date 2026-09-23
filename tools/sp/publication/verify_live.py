"""Verify the actual GitHub Pages deployment against this exact checkout.
No political research, no user tracking, no changes to repository files.
"""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(os.environ.get('SP_LIVE_OUTPUT', '/tmp/sp-publication-live'))
OUT.mkdir(parents=True, exist_ok=True)
SITE = 'https://selvalabs.github.io/esquerda-em-foco/'
SHA = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
DATA = json.loads((ROOT / 'sp/deputados-federais/dados.json').read_text())
ROWS = DATA['records']
REGISTRY_PATH = ROOT / 'config/editions.json'
REGISTRY = json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else None
GLOBAL_HOME = REGISTRY is not None and REGISTRY['root_mode'] == 'global_home'
SC_EDITION = None
if GLOBAL_HOME:
    SC_EDITION = next(e for e in REGISTRY['editions'] if e['edition_id'] == '2026-sc-federais')
    assert SC_EDITION['publication_status'] == 'published'
    assert SC_EDITION['current_path'] == '/sc/deputados-federais/'
    assert SC_EDITION['entrypoint'] == 'sc/deputados-federais/index.html'


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def verify_file(path: str, attempts: int = 3) -> dict:
    expected = digest((ROOT / path).read_bytes())
    public_path = path[:-10] if path.endswith('index.html') else path
    url = SITE + public_path
    error = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(url + '?spverify=' + SHA[:12], headers={'User-Agent': 'EsquerdaEmFoco-SP-PublicationVerification/1.0', 'Accept-Encoding': 'identity', 'Cache-Control': 'no-cache'})
            with urllib.request.urlopen(req, timeout=25) as response:
                raw = response.read()
                status = response.status
                final_url = response.geturl()
            actual = digest(raw)
            assert status == 200 and actual == expected, f'HTTP {status}; sha256 {actual}; expected {expected}'
            return {'path': path, 'url': url, 'final_url': final_url, 'status': status, 'sha256': actual, 'matches_commit': True, 'bytes': len(raw), 'attempt': attempt + 1}
        except Exception as exc:
            error = str(exc)
            if attempt + 1 < attempts:
                time.sleep(8)
    raise RuntimeError(path + ': ' + str(error))


def browser_checks() -> list[dict]:
    if 'id="cqData"' in (ROOT/'sp/deputados-federais/index.html').read_text():
        import sys
        sys.path.insert(0,str(ROOT/'tests/global_rollout'))
        import legacy_browser
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:return legacy_browser.sp(browser,SITE,OUT,ROWS)
            finally:browser.close()
    checks = []
    url = SITE + 'sp/deputados-federais/'
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in (1440, 390):
            ctx = browser.new_context(viewport={'width': width, 'height': 1000 if width == 1440 else 844}, locale='pt-BR', timezone_id='America/Sao_Paulo', reduced_motion='reduce')
            ctx.route('**/*', lambda route: route.continue_() if route.request.url.startswith(SITE) or route.request.url.startswith('data:') else route.abort())
            page = ctx.new_page()
            errors, assets = [], []
            page.on('pageerror', lambda err: errors.append(str(err)))
            page.on('response', lambda response: assets.append({'url': response.url, 'status': response.status}) if response.url.startswith(SITE) and response.status >= 400 else None)
            page.set_default_timeout(20000)
            def go(address):
                response = page.goto(address, wait_until='domcontentloaded')
                assert response and response.status == 200
                page.wait_for_function("document.documentElement.classList.contains('js')")
            def count(n):
                expect(page.locator('#resultCount')).to_have_text(f'{n} de {len(ROWS)} registros')
                assert page.locator('article.candidate:not([hidden])').count() == n
            def width_ok():
                size = page.evaluate('({width:innerWidth,scroll:document.documentElement.scrollWidth})')
                assert size['scroll'] <= size['width'] + 1, size
            go(url + '?spverify=' + SHA[:12])
            count(249)
            assert page.locator('[data-party-filter]').count() == 12
            assert page.locator('[data-topic-filter]').count() == 30
            width_ok()
            page.screenshot(path=str(OUT / f'sp-published-{width}.png'))
            checks.append({'name': 'initial_page', 'width': width, 'records': 249, 'result': 'PASS'})
            if width == 390:
                page.locator('#filterDetails > summary').click()
            page.locator('[data-party-filter="PT"]').click()
            count(49)
            page.locator('[data-topic-filter="saude"]').click()
            expected = sum(r['party'] == 'PT' and any(t['id'] == 'saude' for t in r['themes_2026']) for r in ROWS)
            count(expected)
            if page.locator('#eefShareQuery').count():
                # New query choices are not automatically persisted in the address.
                assert not __import__('urllib.parse',fromlist=['urlsplit']).urlsplit(page.url).query
                page.locator('#eefShareQuery').click()
                shared=page.locator('#eefQueryShareUrl').input_value()
                assert '#eef=query&v=1&edition=2026-sp-federais&state=' in shared
                page.locator('#eefQueryShareClose').click()
                # Leave the current document so goto must perform a real HTTP load.
                # A fragment-only goto is otherwise same-document and returns None.
                page.goto('about:blank', wait_until='domcontentloaded')
                go(shared)
                count(expected)
            else:
                assert 'partidos=PT' in page.url and 'pautas=saude' in page.url
            page.reload(wait_until='domcontentloaded')
            count(expected)
            width_ok()
            checks.append({'name': 'party_topic_and_reload', 'width': width, 'records': expected, 'result': 'PASS'})
            go(url + '?partidos=PSTU')
            count(5)
            assert page.locator('article.candidate:not([hidden]) [data-show-evidence]').count() == 0
            go(url + '?partidos=REDE')
            count(10)
            assert page.locator('article.candidate:not([hidden]) [data-show-evidence]').count() == 0
            go(url + '?partidos=PCB')
            count(0)
            expect(page.locator('#emptyResults')).to_be_visible()
            checks.append({'name': 'canonical_parties_without_inferred_topics', 'width': width, 'result': 'PASS'})
            go(url + '?q=5070')
            count(1)
            card = page.locator('#candidato-250002539612')
            card.locator('.current-evidence > summary').click()
            assert card.locator('.current-evidence').evaluate('(e)=>e.open')
            assert card.locator('[data-claim-id]').count() >= 1
            assert card.locator('a[href^="https://www.camara.leg.br/"]').count() >= 1
            width_ok()
            page.screenshot(path=str(OUT / f'sp-evidence-{width}.png'))
            checks.append({'name': 'search_and_documented_evidence', 'width': width, 'result': 'PASS'})
            go(url)
            page.locator('.portrait img').evaluate_all("xs=>xs.forEach(x=>x.loading='eager')")
            page.wait_for_function("[...document.querySelectorAll('.portrait img')].every(x=>x.complete)")
            broken = page.locator('.portrait img').evaluate_all('xs=>xs.filter(x=>!x.naturalWidth).map(x=>x.src)')
            assert not broken, broken
            assert not errors and not assets, {'page_errors': errors, 'failed_assets': assets}
            checks.append({'name': 'all_portraits_and_runtime', 'width': width, 'decoded_photos': 249, 'page_errors': 0, 'asset_failures': 0, 'result': 'PASS'})
            if width == 1440:
                response = page.goto(SITE, wait_until='domcontentloaded')
                assert response and response.status == 200
                if GLOBAL_HOME:
                    assert page.locator('.global-state').count() == 4
                    assert page.locator('article.candidate').count() == 0
                    page.locator('#global-estado-sc h3 a').click()
                    page.wait_for_url(SITE + 'sc/')
                    page.locator('.global-office-card a[href*="deputados-federais"]').click()
                    page.wait_for_url(SITE + SC_EDITION['current_path'].lstrip('/'))
                assert page.locator('article.candidate').count() == 48
                assert page.locator('[data-pauta-topic]').count() == 13
                if GLOBAL_HOME:
                    page.locator('#global-edition-menu>summary').click()
                    page.locator('#global-edition-menu a[href*="sp/deputados-federais"]').click()
                    page.wait_for_url(url)
                else:
                    page.locator('a.edition-sp-link').click()
                count(249)
                assert not errors and not assets, {'page_errors': errors, 'failed_assets': assets}
                checks.append({'name': 'global_home_SC_hub_SC_edition_to_SP' if GLOBAL_HOME else 'current_SC_home_links_to_SP', 'width': width, 'result': 'PASS'})
            ctx.close()
        ctx = browser.new_context(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        page = ctx.new_page()
        response = page.goto(url, wait_until='domcontentloaded')
        assert response and response.status == 200
        assert page.locator('article.candidate').count() == 249
        page.locator('.current-evidence > summary').first.click()
        assert page.locator('.current-evidence').first.evaluate('(e)=>e.open')
        checks.append({'name': 'readable_without_javascript', 'result': 'PASS'})
        ctx.close()
        browser.close()
    return checks


def main() -> None:
    report = {'gate': 'BLOCKED', 'started_at': datetime.now(timezone.utc).isoformat(), 'commit': SHA, 'base_url': SITE, 'scope': 'Published bytes and browser behavior, not a new factual validation of political claims', 'files': [], 'browser': []}
    try:
        # Wait for the existing Pages deployment, never accept an old HTML as success.
        verify_file('sp/deputados-federais/index.html', attempts=12)
        verify_file('index.html', attempts=12)
        paths = {str(p.relative_to(ROOT)) for p in (ROOT / 'sp').rglob('*') if p.is_file()}
        paths.update(['index.html', 'sitemap.xml', 'favicon.svg', 'deputados-estaduais/index.html', 'rs/deputados-federais/index.html', 'rs/deputados-estaduais/index.html', 'pr/index.html', 'pr/deputados-federais/index.html', 'pr/deputados-estaduais/index.html'])
        paths.update(['assets/pauta-filter-core.js', 'assets/pauta-filters.css', 'assets/pauta-v2.css', 'assets/pauta-filters-v2.js', 'assets/sc-federais-filters-v2-data.js'])
        if GLOBAL_HOME:
            # Add, do not replace, the original SP files and local portrait checks.
            paths.update(item['path'] for item in json.loads((ROOT / 'data/global03/publication-files.json').read_text())['files'])
        paths = sorted(p for p in paths if (ROOT / p).is_file())
        with ThreadPoolExecutor(max_workers=4) as pool:
            report['files'] = list(pool.map(verify_file, paths))
        report['browser'] = browser_checks()
        report['gate'] = 'PASS'
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        report['file_count'] = len(report['files'])
        report['browser_scenarios'] = len(report['browser'])
        (OUT / 'publication.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({k: v for k, v in report.items() if k != 'files'}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()

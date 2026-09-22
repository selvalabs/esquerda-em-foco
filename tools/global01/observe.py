"""GLOBAL-01: read-only observations; failures are findings, not silently repaired.
Run against two immutable git archives. Does not collect political evidence or
change any edition. External browser requests are blocked; no message is sent.
"""
from __future__ import annotations
import argparse
import functools
import hashlib
import json
import threading
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def hashes(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}


class Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *_args: object) -> None:
        pass


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--main-root', type=Path, required=True)
    parser.add_argument('--rs-root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    shots = args.out / 'screenshots'
    shots.mkdir(exist_ok=True)
    before = {'main': hashes(args.main_root), 'rs_branch': hashes(args.rs_root)}
    servers = []
    for root in [args.main_root, args.rs_root]:
        server = ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(root)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
    ports = [s.server_port for s in servers]
    editions = [
        ('sc-federais', 0, '/'), ('sc-estaduais', 0, '/deputados-estaduais/'),
        ('rs-federais', 0, '/rs/deputados-federais/'), ('rs-estaduais', 1, '/rs/deputados-estaduais/'),
        ('pr-federais', 0, '/pr/deputados-federais/'), ('pr-estaduais', 0, '/pr/deputados-estaduais/'),
        ('sp-federais', 0, '/sp/deputados-federais/')]
    checks, observations, static = [], [], []

    def record(edition: str, name: str, passed: bool, detail: object = None) -> None:
        checks.append({'edition': edition, 'check': name, 'passed': bool(passed), 'detail': detail})

    def block_external(route) -> None:
        if any(route.request.url.startswith(f'http://127.0.0.1:{port}/') for port in ports):
            route.continue_()
        else:
            route.abort()

    def context(browser, **kwargs):
        ctx = browser.new_context(locale='pt-BR', timezone_id='America/Sao_Paulo', **kwargs)
        ctx.route('**/*', block_external)
        return ctx

    for ed, root_index, route in editions:
        root = [args.main_root, args.rs_root][root_index]
        path = root / route.strip('/') / 'index.html'
        soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
        cards = soup.select('article.candidate')
        static.append({
            'edition': ed, 'source': ['main', 'rs_branch'][root_index],
            'entrypoint': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'html_bytes': path.stat().st_size, 'card_count': len(cards),
            'title': soup.title.get_text() if soup.title else None,
            'canonical': [a.get('href') for a in soup.select('link[rel="canonical"]')],
            'scripts': [a.get('src', '(inline)') for a in soup.select('script')],
            'stylesheets': [a.get('href') for a in soup.select('link[rel="stylesheet"]')],
            'controls': [{'id': e.get('id'), 'tag': e.name, 'type': e.get('type')}
                         for e in soup.select('input,select')],
            'navigation': [{'text': e.get_text(' ', strip=True), 'href': e.get('href')}
                           for nav in soup.select('nav') for e in nav.select('a')],
            'details_classes': sorted({c for e in soup.select('details') for c in e.get('class', [])}),
            'all_ids_unique': len(soup.select('[id]')) == len({e['id'] for e in soup.select('[id]')})})

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        browser_version = browser.version
        for ed, root_index, route in editions:
            url = f'http://127.0.0.1:{ports[root_index]}{route}'
            info = {'edition': ed, 'viewports': []}
            ctx = context(browser, viewport={'width': 1440, 'height': 900})
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda error, sink=errors: sink.append(str(error)))
            response = page.goto(url, wait_until='load')
            page.wait_for_timeout(180)
            total = page.locator('article.candidate').count()
            ids = page.locator('article.candidate').evaluate_all('(xs)=>xs.map(x=>x.id)')
            info['card_count'] = total
            record(ed, 'html_loaded', response.status == 200)
            record(ed, 'unique_card_ids', len(ids) == len(set(ids)), total)
            for width in [320, 360, 390, 430, 768, 1024, 1440]:
                page.set_viewport_size({'width': width, 'height': 844 if width < 768 else 900})
                page.evaluate('window.scrollTo(0,0)')
                page.wait_for_timeout(100)
                geom = page.evaluate('()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})')
                info['viewports'].append(geom)
                record(ed, f'no_horizontal_overflow_{width}', geom['scrollWidth'] <= width + 1, geom)
                if width in [390, 1440]:
                    page.screenshot(path=str(shots / f'{ed}-{width}.png'))
            page.set_viewport_size({'width': 390, 'height': 844})
            page.evaluate('window.scrollTo(0,0)')
            page.wait_for_timeout(100)
            menu = page.locator('#siteNavMenu')
            if menu.count() and menu.is_visible():
                menu.click()
                record(ed, 'mobile_menu_open', menu.get_attribute('aria-expanded') == 'true')
                page.keyboard.press('Escape')
                record(ed, 'mobile_menu_escape', menu.get_attribute('aria-expanded') == 'false')
            page.set_viewport_size({'width': 1440, 'height': 900})
            search = page.locator('#searchInput')
            search.fill('zzz-auditoria-sem-correspondencia-zzz')
            page.wait_for_timeout(400)
            record(ed, 'search_empty', page.locator('article.candidate:visible').count() == 0)
            info['url_after_search'] = page.url.split(f':{ports[root_index]}', 1)[1]
            search.fill('')
            page.wait_for_timeout(400)
            record(ed, 'search_clear_restores', page.locator('article.candidate:visible').count() == total)
            if page.locator('#partyFilter').count():
                options = page.locator('#partyFilter option').evaluate_all('(xs)=>xs.map(x=>x.value).filter(Boolean)')
                page.select_option('#partyFilter', options[0])
                parties = page.locator('article.candidate:visible').evaluate_all('(xs)=>[...new Set(xs.map(x=>x.dataset.party))]')
                record(ed, 'party_filter_exact', parties == [options[0]], parties)
                page.select_option('#partyFilter', '')
            elif page.locator('[data-party-filter]').count():
                key = page.locator('[data-party-filter]').evaluate_all('(xs)=>xs.find(x=>x.dataset.partyFilter && !x.disabled)?.dataset.partyFilter')
                if key:
                    page.locator(f'[data-party-filter="{key}"]').click()
                    parties = page.locator('article.candidate:visible').evaluate_all('(xs)=>[...new Set(xs.map(x=>x.dataset.party))]')
                    record(ed, 'party_filter_exact', len(parties) <= 1 and (not parties or parties == [key]), parties)
                    page.locator('[data-party-filter=""]').click()
            search.fill('zzz-auditoria-sem-correspondencia-zzz')
            page.wait_for_timeout(400)
            page.evaluate('(id)=>{location.hash=id}', ids[0])
            page.wait_for_timeout(200)
            record(ed, 'hidden_candidate_anchor_reveals', page.locator(f'[id="{ids[0]}"]').is_visible())
            page.goto(url, wait_until='load')
            page.wait_for_timeout(100)
            selector = 'button[data-pauta-topic]' if ed == 'sc-federais' else ('button[data-theme]' if ed.startswith('pr-') else ('button[data-topic-filter]' if ed.startswith('sp-') else None))
            if selector and page.locator(selector).count():
                button = page.locator(selector).first
                button.click()
                page.wait_for_timeout(120)
                count = page.locator('article.candidate:visible').count()
                record(ed, 'topic_toggle_and_result', button.get_attribute('aria-pressed') == 'true' and 0 < count <= total, count)
                info['url_after_topic'] = page.url.split(f':{ports[root_index]}', 1)[1]
                page.reload(wait_until='load')
                info['topic_state_survives_reload'] = page.locator(selector).first.get_attribute('aria-pressed') == 'true'
            if ed == 'sc-federais':
                page.goto(url, wait_until='load')
                toggles = page.locator('[data-eef-toggle]')
                chosen = [toggles.nth(i).get_attribute('data-eef-toggle') for i in [0, 1]]
                for cid in chosen:
                    page.locator(f'[data-eef-toggle="{cid}"]').click()
                search.fill('zzz-auditoria-sem-correspondencia-zzz')
                page.wait_for_timeout(100)
                page.locator('#eefSelectedNav').click()
                reader = page.locator('#eefCollectionDialog')
                # The reader ID is checked against the actual DOM instead of assuming a duplicate card view.
                opened = page.locator('dialog[open]').filter(has=page.locator('#eefPager'))
                record(ed, 'selected_reader_one_original_card', opened.locator('article.candidate').count() == 1)
                record(ed, 'selected_reader_order_first', opened.locator('article.candidate').get_attribute('data-tse-id') == chosen[0])
                page.locator('#eefNext').click()
                record(ed, 'selected_reader_order_next', opened.locator('article.candidate').get_attribute('data-tse-id') == chosen[1])
                page.locator('#eefShareCollection').click()
                share_url = page.locator('#eefShareUrl').input_value()
                info['selected_fragment'] = share_url.split('#', 1)[1]
                record(ed, 'selected_share_preserves_edition', 'edicao=sc-federais' in share_url)
                other = context(browser, viewport={'width': 390, 'height': 844})
                other_page = other.new_page()
                other_page.goto(share_url, wait_until='load')
                other_page.wait_for_timeout(150)
                record(ed, 'selected_link_reconstructs', other_page.locator('#eefPager').inner_text() == 'Ficha 2 de 2', other_page.locator('#eefPager').inner_text())
                other.close()
            info['page_errors'] = errors
            record(ed, 'no_page_errors', not errors, errors)
            observations.append(info)
            ctx.close()
            nojs = context(browser, java_script_enabled=False, viewport={'width': 390, 'height': 844})
            page = nojs.new_page()
            page.goto(url, wait_until='load')
            record(ed, 'nojs_cards_readable', page.locator('article.candidate:visible').count() == total)
            record(ed, 'nojs_source_links_present', page.locator('article.candidate a[href^="http"]').count() > 0)
            nojs.close()
        for hub in ['/pr/', '/sp/']:
            ctx = context(browser)
            page = ctx.new_page()
            page.goto(f'http://127.0.0.1:{ports[0]}{hub}', wait_until='load')
            for width in [320, 390, 1440]:
                page.set_viewport_size({'width': width, 'height': 844})
                geom = page.evaluate('()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})')
                record(hub, f'no_horizontal_overflow_{width}', geom['scrollWidth'] <= width + 1, geom)
            ctx.close()
        browser.close()
    for server in servers:
        server.shutdown()
    after = {'main': hashes(args.main_root), 'rs_branch': hashes(args.rs_root)}
    record('isolation', 'both_archives_unchanged', before == after)
    report = {'observed_at_utc': datetime.now(timezone.utc).isoformat(), 'browser': browser_version,
              'scope': 'Immutable git archives; not a new live-site verification or editorial recertification.',
              'external_requests': 'blocked; no WhatsApp delivery or real screen-reader test',
              'checks': checks, 'editions': observations,
              'passed': sum(c['passed'] for c in checks), 'failed': sum(not c['passed'] for c in checks)}
    save(args.out / 'browser-audit.json', report)
    save(args.out / 'static-inventory.json', static)
    save(args.out / 'source-file-hashes.json', before)
    print(json.dumps({'passed': report['passed'], 'failed': report['failed'],
                      'findings': [c for c in checks if not c['passed']]}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Regression checks for implicit card columns found during screenshot review."""
from __future__ import annotations
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(ROOT.parent)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    checks = []
    shots = ROOT / 'audit/screenshots'
    shots.mkdir(exist_ok=True)
    try:
        with sync_playwright() as pw:
            options = {'headless': True, 'args': ['--no-sandbox']}
            if os.path.isfile('/usr/bin/chromium'):
                options['executable_path'] = '/usr/bin/chromium'
            browser = pw.chromium.launch(**options)
            for width, height in ((360, 800), (390, 844), (768, 1024), (1440, 1000)):
                page = browser.new_page(viewport={'width': width, 'height': height}, reduced_motion='reduce')
                page.goto(f'http://127.0.0.1:{server.server_port}/deputados-estaduais/', wait_until='networkidle')
                rows = page.locator('.candidate').evaluate_all('''els => els.map(e => {
                    const career = e.querySelector('.career-band').getBoundingClientRect();
                    const history = e.querySelector('.state-history').getBoundingClientRect();
                    const link = e.querySelector('.profile-link').getBoundingClientRect();
                    return {id:e.id, columns:getComputedStyle(e).gridTemplateColumns.trim().split(/\\s+/).length,
                        ordered:history.top >= career.bottom - 1 && link.top >= history.bottom - 1};
                })''')
                for name, bad in (
                    ('single parent card column', [r['id'] for r in rows if r['columns'] != 1]),
                    ('history and permalink below career', [r['id'] for r in rows if not r['ordered']]),
                ):
                    checks.append({'name':f'{name} {width}', 'passed':len(rows) == 97 and not bad, 'detail':bad})
                page.locator('.candidate').first.screenshot(path=str(shots / f'review2-layout-{width}.png'))
                page.close()
            browser.close()
    finally:
        server.shutdown()
    report = {'passed':all(x['passed'] for x in checks), 'checks':checks, 'viewports':[360, 390, 768, 1440]}
    (ROOT / 'audit/review2/layout-qa.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False), flush=True)
    if not report['passed']:
        raise SystemExit('Card layout regression; do not publish')

if __name__ == '__main__':
    main()

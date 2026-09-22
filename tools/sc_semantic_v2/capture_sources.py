"""Leitura pública pontual, sem login, sem OCR e sem contornar bloqueios.
Saída temporária para auditoria humana; jamais transforma texto em tags.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright

M = json.loads(Path('data/sc-federais-topics-v1/matrix.json').read_text())
TARGETS = {'240002533831-s1', '240002537841-s1', '240002533827-s1',
           '240002543042-s1', '240002533829-s1', '240002537839-s1',
           '240002533838-s1', '240002537826-s1', '240002537827-s1',
           '240002537827-s2', '240002537840-s1', '240002537833-s1'}
rows = []
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(locale='pt-BR')
    for s in M['sources']:
        if s['source_id'] not in TARGETS:
            continue
        page = context.new_page()
        page.route('**/*', lambda r: r.abort() if r.request.resource_type in ('image', 'media', 'font') else r.continue_())
        row = {'source_id': s['source_id'], 'url': s['url'], 'checked_at': datetime.now(timezone.utc).isoformat()}
        try:
            response = page.goto(s['url'], wait_until='domcontentloaded', timeout=20000)
            page.wait_for_timeout(2500)
            text = page.locator('body').inner_text(timeout=8000)
            row.update(final_url=page.url, http_status=response.status if response else None,
                       title=page.title(), text=text[:26000], text_sha256=hashlib.sha256(text.encode()).hexdigest())
        except Exception as e:
            row['error'] = str(e)[:500]
        rows.append(row)
        print(json.dumps({k:v for k,v in row.items() if k!='text'}, ensure_ascii=False), flush=True)
        page.close()
    browser.close()
out = Path('/tmp/sc-semantic-inputs/rendered-sources.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2))

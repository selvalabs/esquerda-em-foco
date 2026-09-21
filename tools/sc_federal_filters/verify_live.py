"""Confere a publicação real por SHA-256 e faz smoke test Chromium no Pages."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
BASE = 'https://selvalabs.github.io/esquerda-em-foco/'
SHA = os.environ.get('EXPECTED_SHA') or subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
FILES = ['index.html', 'assets/pauta-filter-core.js', 'assets/pauta-filters.js', 'assets/pauta-filters.css',
         'assets/sc-federais-filters-data.js', 'data/sc-federais-filters-v1/payload.json',
         'data/sc-federais-filters-v1/manifest.json', 'config/topics-v1.json', 'data/sc-federais-topics-v1/matrix.json']
OUT = Path('/tmp/eef-sc-federal-filters-live.json')

def probe(path):
    expected = sha256((ROOT / path).read_bytes()).hexdigest()
    url = BASE + ('' if path == 'index.html' else path) + '?verify=' + SHA
    row = {'path':path, 'url':url, 'expected_sha256':expected}
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'Cache-Control':'no-cache', 'User-Agent':'EsquerdaEmFoco-PublicationCheck/2.0'}), timeout=20) as r:
            digest = sha256(r.read()).hexdigest()
            return {**row, 'http_status':r.status, 'actual_sha256':digest, 'matched':r.status==200 and digest==expected}
    except Exception as e:
        return {**row, 'matched':False, 'error':str(e)[:300]}

rows = []
for attempt in range(1, 25):
    with ThreadPoolExecutor(max_workers=5) as ex:
        rows = list(ex.map(probe, FILES))
    pending = [r['path'] for r in rows if not r['matched']]
    print(json.dumps({'attempt':attempt,'matched':len(rows)-len(pending),'pending':pending}), flush=True)
    if not pending: break
    time.sleep(12)

result = {'status':'passed' if all(r['matched'] for r in rows) else 'failed', 'commit':SHA,
          'checked_at':datetime.now(timezone.utc).isoformat(), 'files':rows, 'browser':[]}
if result['status']=='passed':
    data = json.loads((ROOT / 'data/sc-federais-filters-v1/payload.json').read_text())
    expected = {c['id'] for c in data['candidates'] if 'saude' in c['topicIds']}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for width in (390, 1440):
                page = browser.new_page(viewport={'width':width,'height':900}, locale='pt-BR', reduced_motion='reduce')
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.route('**/*', lambda route: route.abort() if route.request.resource_type=='image' else route.continue_())
                page.goto(BASE+'?verify='+SHA, wait_until='domcontentloaded', timeout=45000)
                page.wait_for_function('Boolean(window.EEFTopicFilters)', timeout=30000)
                assert page.locator('.candidate:not([hidden])').count()==48
                if width==390: page.locator('#pautaOpen').click()
                page.locator('[data-pauta-topic="saude"]').click()
                actual = set(page.locator('.candidate:not([hidden])').evaluate_all('(els)=>els.map(e=>e.dataset.tseId)'))
                assert actual == expected
                if width==390:
                    page.keyboard.press('Escape')
                    page.wait_for_function('!document.getElementById("pautaDialog").open')
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
                assert not errors, errors
                result['browser'].append({'width':width,'status':'passed','initial_candidates':48,'saude_results':len(actual),'js_errors':errors})
                page.close()
            browser.close()
    except Exception as e:
        result['status']='failed'
        result['browser_error']=str(e)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print('LIVE_FILTERS '+json.dumps(result, ensure_ascii=False))
if result['status'] != 'passed': raise SystemExit(1)

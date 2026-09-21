"""Snapshot imutável da frente SC federal; não altera o site."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import subprocess
from bs4 import BeautifulSoup

BASE = '810a7896b3355254d50852761a41bae31ce3f567'
OUT = Path('data/sc-federais-pautas')
OUT.mkdir(parents=True, exist_ok=True)
html = subprocess.check_output(['git', 'show', f'{BASE}:index.html']).decode('utf-8')
soup = BeautifulSoup(html, 'html.parser')
rows = []
for card in soup.select('article.candidate'):
    rows.append({
        'id': card.get('data-tse-id'),
        'anchor': card.get('id'),
        'name': card.select_one('h3').get_text(' ', strip=True),
        'party': card.get('data-party'),
        'number': card.select_one('.number').get_text(' ', strip=True),
        'previous_summary': card.select_one('.pauta').get_text(' ', strip=True),
        'previous_has_pauta': card.get('data-has-pauta'),
        'website': [a.get('href') for a in card.select('a.site-btn')],
        'social': [{'label': a.get('aria-label'), 'url': a.get('href')} for a in card.select('.socials a')],
        'previous_card_sha256': hashlib.sha256(str(card).encode()).hexdigest()
    })
assert len(rows) == 48, f'Baseline inesperado: {len(rows)} fichas'
assert len({r['id'] for r in rows}) == 48
paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], text=True).splitlines()
protected = {}
for path in paths:
    if path.startswith(('rs/', 'data/rs/', 'deputados-estaduais/')) or path in ('sitemap.xml', 'assets/metrics-config.js'):
        data = subprocess.check_output(['git', 'show', f'{BASE}:{path}'])
        protected[path] = hashlib.sha256(data).hexdigest()
result = {'baseline_commit': BASE, 'review_date': '2026-09-21', 'count': len(rows), 'html_sha256': hashlib.sha256(html.encode()).hexdigest(), 'candidates': rows, 'protected_sha256': protected}
(OUT / 'baseline.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
compact = [{k: r[k] for k in ('id', 'name', 'party', 'website', 'social')} for r in rows]
(OUT / 'research-targets.json').write_text(json.dumps(compact, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
print(json.dumps({'snapshot': 'ok', 'candidates': len(rows), 'protected_files': len(protected)}, ensure_ascii=False))

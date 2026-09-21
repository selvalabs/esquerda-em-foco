#!/usr/bin/env python3
"""Collect public electoral records. Never write to the federal application.
Raw archives stay outside the repository; private identifiers are not exported.
"""
from __future__ import annotations
import csv, hashlib, io, json, re, sys, time, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
AUDIT = ROOT / 'audit'
DATA.mkdir(parents=True, exist_ok=True)
AUDIT.mkdir(parents=True, exist_ok=True)
BASE = 'https://cdn.tse.jus.br/estatistica/sead/odsele/'
SOURCES = {
 'candidatos': BASE + 'consulta_cand/consulta_cand_2026.zip',
 'historico': BASE + 'historico_candidatura/historico_candidatura_2026.zip',
 'redes': BASE + 'consulta_cand/rede_social_candidato_2026.zip',
}
PRIVATE = ('CPF', 'TITULO_ELEITOR', 'EMAIL', 'NASCIMENTO', 'PROCESSO', 'ENDERECO', 'TELEFONE')
manifest = {'consulted_at': datetime.now(timezone.utc).isoformat(), 'year': 2026, 'uf': 'SC', 'office': 'DEPUTADO ESTADUAL', 'sources': {}, 'errors': []}

def save(path: Path, value: object) -> None:
 path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def download(url: str) -> bytes:
 error = None
 for attempt in range(3):
  try:
   with urlopen(Request(url, headers={'User-Agent': 'EsquerdaEmFoco/1.0 public-data-audit', 'Accept': '*/*'}), timeout=180) as r:
    return r.read()
  except Exception as exc:
   error = exc
   time.sleep(2 * (attempt + 1))
 raise RuntimeError(f'Download failed: {url}: {error}')

def archive_rows(key: str):
 raw = download(SOURCES[key])
 z = zipfile.ZipFile(io.BytesIO(raw))
 files = [n for n in z.namelist() if n.lower().endswith('.csv')]
 sc = [n for n in files if re.search(r'_SC\.csv$', n, re.I)]
 brazil = [n for n in files if re.search(r'_BRASIL\.csv$', n, re.I)]
 chosen = sc or brazil or files
 manifest['sources'][key] = {'url': SOURCES[key], 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw), 'files': files, 'read_files': chosen}
 for name in chosen:
  with z.open(name) as f:
   text = io.TextIOWrapper(f, encoding='utf-8-sig' if f.peek(3)[:3] == b'\xef\xbb\xbf' else 'latin-1', newline='')
   reader = csv.DictReader(text, delimiter=';')
   manifest['sources'][key]['columns'] = reader.fieldnames
   for row in reader:
    yield row

def public(row: dict) -> dict:
 return {k: v for k, v in row.items() if not any(p in k for p in PRIVATE)}

# Federal file is read only. Keep its original digest for regression checks.
federal = ROOT.parent / 'index.html'
original = federal.read_bytes()
soup = BeautifulSoup(original.decode('utf-8'), 'html.parser')
manifest['federal_sha256'] = hashlib.sha256(original).hexdigest()
manifest['federal_git_blob'] = hashlib.sha1(b'blob ' + str(len(original)).encode() + b'\0' + original).hexdigest()
(AUDIT / 'federal-reference.txt').write_text(soup.get_text('\n', strip=True), encoding='utf-8')
structure = BeautifulSoup(str(soup.body), 'html.parser')
for tag in structure.find_all('script'):
 tag.decompose()
for tag in structure.find_all('img'):
 if (tag.get('src') or '').startswith('data:'):
  tag['src'] = '[embedded-image]'
(AUDIT / 'federal-structure.html.txt').write_text(str(structure), encoding='utf-8')
(AUDIT / 'federal-css.txt').write_text('\n'.join(x.get_text() for x in soup.find_all('style')), encoding='utf-8')
manifest['federal_data_attributes'] = {k: sorted({str(t.attrs[k]) for t in soup.find_all(attrs={k: True})})[:100] for k in ['data-party', 'data-partido', 'data-status']}

try:
 candidates = [public(r) for r in archive_rows('candidatos') if r.get('SG_UF') == 'SC' and r.get('CD_CARGO') == '7' and r.get('ANO_ELEICAO') == '2026']
 if not candidates:
  raise ValueError('No SC state-deputy records in official archive; refusing to invent a list.')
 ids = {r['SQ_CANDIDATO'] for r in candidates}
 save(DATA / 'universo-sc-2026.json', candidates)
 manifest['universe_count'] = len(candidates)
 manifest['parties'] = dict(Counter(r['SG_PARTIDO'] for r in candidates))
 manifest['statuses'] = dict(Counter(r.get('DS_SITUACAO_CANDIDATURA', '') for r in candidates))
 for key in ['historico', 'redes']:
  try:
   rows = []
   for r in archive_rows(key):
    id_keys = [k for k in r if 'SQ_CANDIDATO' in k or 'SQ_CANDIDATURA' in k]
    if any(r[k] in ids for k in id_keys):
     rows.append(public(r))
   save(DATA / f'{key}-sc-2026.json', rows)
   manifest['sources'][key]['matched_rows'] = len(rows)
   manifest['sources'][key]['sample_public_rows'] = rows[:2]
  except Exception as e:
   manifest['errors'].append(str(e))
except Exception as e:
 manifest['errors'].append(str(e))
finally:
 save(AUDIT / 'collection.json', manifest)
 print(json.dumps(manifest, ensure_ascii=False, indent=2))
 if hashlib.sha256(federal.read_bytes()).hexdigest() != manifest['federal_sha256']:
  raise RuntimeError('Federal file changed')
 if 'universe_count' not in manifest:
  sys.exit(1)

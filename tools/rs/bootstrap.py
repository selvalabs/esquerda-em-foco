"""Read-only source collection; only RS directories are written. No private fields are exported."""
from __future__ import annotations
import collections, csv, hashlib, io, json, re, subprocess, time, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone
from bs4 import BeautifulSoup

BASELINE = '71d123b909cdbf3d84bd1cdca89511890759d395'
OUT = Path('data/rs')
DOC = Path('docs/rs')
for directory in (OUT, DOC):
    directory.mkdir(parents=True, exist_ok=True)

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def download(url):
    errors = []
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'EsquerdaEmFoco/1.0 (public electoral data audit)', 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=90) as response:
                raw = response.read()
            if not raw:
                raise ValueError('Empty response')
            return raw
        except Exception as exc:
            errors.append(str(exc))
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(url + ': ' + '; '.join(errors))

raw_sc = subprocess.check_output(['git', 'show', BASELINE + ':index.html'])
soup = BeautifulSoup(raw_sc, 'html.parser')
parties = sorted({c.get('data-party') for c in soup.select('article.candidate') if c.get('data-party')})
reference = {
    'baseline_commit': BASELINE,
    'sc_sha256': hashlib.sha256(raw_sc).hexdigest(),
    'party_counts': dict(collections.Counter(c.get('data-party') for c in soup.select('article.candidate'))),
    'ids': [x['id'] for x in soup.select('[id]') if not x['id'].startswith('candidato-')],
    'styles': [{'id': x.get('id'), 'length': len(x.get_text())} for x in soup.select('style')],
    'scripts': [{'id': x.get('id'), 'src': x.get('src'), 'type': x.get('type'), 'length': len(x.get_text())} for x in soup.select('script')],
    'fragments': {}
}
for selector in ['.site-nav', '.masthead', '.toolbar-wrap', '.rail', '.intro', '.independent-notice', '#sobre-levantamento', '#criterio-eleitoral', '#fontes', '.method', '.persistent-footer', 'footer']:
    node = soup.select_one(selector)
    if node:
        text = str(node)
        text = re.sub(r'data:image/[^\s\"\)]+', '[embedded image]', text)
        reference['fragments'][selector] = text
save(DOC / 'baseline-inspection.json', reference)
for i, script in enumerate(soup.select('script')):
    if script.get('type') != 'application/ld+json':
        (DOC / f'baseline-script-{i:02d}.txt').write_text(script.get_text(), encoding='utf-8')

manifest = {'collected_at': datetime.now(timezone.utc).isoformat(), 'baseline_commit': BASELINE, 'parties_from_sc': parties, 'sources': [], 'errors': []}
url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip'
keep = ['DT_GERACAO','HH_GERACAO','ANO_ELEICAO','CD_ELEICAO','DS_ELEICAO','SG_UF','CD_CARGO','DS_CARGO','SQ_CANDIDATO','NR_CANDIDATO','NM_CANDIDATO','NM_URNA_CANDIDATO','SG_PARTIDO','NM_PARTIDO','NR_PARTIDO','NR_FEDERACAO','NM_FEDERACAO','SG_FEDERACAO','DS_SITUACAO_CANDIDATURA','DS_DETALHE_SITUACAO_CAND','DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CASSACAO','DS_SITUACAO_SUBSTITUICAO','DS_OCUPACAO','ST_REELEICAO','NM_MUNICIPIO_NASCIMENTO','SG_UF_NASCIMENTO']
try:
    raw = download(url)
    archive = zipfile.ZipFile(io.BytesIO(raw))
    members = [n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
    if len(members) != 1:
        raise ValueError('Expected one RS CSV: ' + str(archive.namelist()))
    member = members[0]
    csv_raw = archive.read(member)
    rows = list(csv.DictReader(io.StringIO(csv_raw.decode('utf-8-sig') if csv_raw.startswith(b'\xef\xbb\xbf') else csv_raw.decode('latin-1')), delimiter=';'))
    federal = [r for r in rows if r.get('SG_UF') == 'RS' and r.get('CD_CARGO') == '6' and r.get('ANO_ELEICAO') == '2026']
    selected = [{k: r.get(k, '') for k in keep} for r in federal if r.get('SG_PARTIDO') in parties]
    assert federal and selected, 'No matching federal candidates'
    assert len({r['SQ_CANDIDATO'] for r in selected}) == len(selected), 'Duplicate candidate IDs'
    save(OUT / 'candidates-official.json', selected)
    manifest['all_rs_federal_count'] = len(federal)
    manifest['all_rs_federal_by_party'] = dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in federal).items()))
    manifest['selected_count'] = len(selected)
    manifest['selected_by_party'] = dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in selected).items()))
    manifest['sources'].append({'url': url, 'sha256': hashlib.sha256(raw).hexdigest(), 'member': member, 'member_sha256': hashlib.sha256(csv_raw).hexdigest(), 'generated_at': selected[0]['DT_GERACAO'] + ' ' + selected[0]['HH_GERACAO']})
    ids = {r['SQ_CANDIDATO'] for r in selected}
    social_url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip'
    try:
        social_raw = download(social_url)
        social_zip = zipfile.ZipFile(io.BytesIO(social_raw))
        social_rows = []
        names = [n for n in social_zip.namelist() if n.upper().endswith('_RS.CSV')]
        if not names:
            names = [n for n in social_zip.namelist() if n.lower().endswith('.csv') and ('BRASIL' in n.upper() or len([m for m in social_zip.namelist() if m.lower().endswith('.csv')]) == 1)]
        for name in names:
            payload = social_zip.read(name)
            text = payload.decode('utf-8-sig') if payload.startswith(b'\xef\xbb\xbf') else payload.decode('latin-1')
            for row in csv.DictReader(io.StringIO(text), delimiter=';'):
                if row.get('SQ_CANDIDATO') in ids:
                    social_rows.append({k:v for k,v in row.items() if k in ['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO']})
        save(OUT / 'social-official.json', social_rows)
        manifest['sources'].append({'url': social_url, 'sha256': hashlib.sha256(social_raw).hexdigest(), 'members': names, 'selected_rows': len(social_rows)})
    except Exception as exc:
        manifest['errors'].append({'source':'social','error':str(exc)})
except Exception as exc:
    manifest['errors'].append({'source':'candidates','error':str(exc)})

try:
    map_url = 'https://servicodados.ibge.gov.br/api/v3/malhas/estados/43?formato=image/svg&qualidade=minima'
    map_raw = download(map_url)
    assert b'<svg' in map_raw, 'Map is not SVG'
    directory = Path('rs/deputados-federais/assets')
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'rs-ibge.svg').write_bytes(map_raw)
    manifest['sources'].append({'url':map_url,'sha256':hashlib.sha256(map_raw).hexdigest(),'kind':'state_map'})
except Exception as exc:
    manifest['errors'].append({'source':'map','error':str(exc)})
save(OUT / 'manifest.json', manifest)
print(json.dumps(manifest, ensure_ascii=False, indent=2))

"""SP federal 2026 / Round A. Public official records only; no frontend writes.

Run: python tools/sp/round_a.py --self-test
     python tools/sp/round_a.py
Only data/sp and docs/sp are written. Downloads are never exported wholesale.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import io
import json
import re
import subprocess
import time
import unicodedata
import unittest
import urllib.request
import zipfile
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

BASELINE = '810a7896b3355254d50852761a41bae31ce3f567'
PARTIES = ['PCO', 'PCdoB', 'PDT', 'PSB', 'PSOL', 'PT', 'PV', 'UP']
PARTY_LOOKUP = {p.upper(): p for p in PARTIES}
DATA = Path('data/sp')
DOCS = Path('docs/sp')
PORTAL = 'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
SOURCE_URL = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip'
COMPLEMENT_URL = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip'
MISSING = {'', '#NULO', '#NULO#', '#NE', '#NE#', '-1', '-3', '-4'}
KEEP = '''DT_GERACAO HH_GERACAO ANO_ELEICAO CD_TIPO_ELEICAO NM_TIPO_ELEICAO NR_TURNO CD_ELEICAO DS_ELEICAO DT_ELEICAO SG_UF SG_UE NM_UE CD_CARGO DS_CARGO SQ_CANDIDATO NR_CANDIDATO NM_CANDIDATO NM_URNA_CANDIDATO NR_PARTIDO SG_PARTIDO NM_PARTIDO TP_AGREMIACAO NR_FEDERACAO NM_FEDERACAO SG_FEDERACAO DS_COMPOSICAO_FEDERACAO SQ_COLIGACAO NM_COLIGACAO DS_COMPOSICAO_COLIGACAO CD_SITUACAO_CANDIDATURA DS_SITUACAO_CANDIDATURA CD_DETALHE_SITUACAO_CAND DS_DETALHE_SITUACAO_CAND CD_SITUACAO_JULGAMENTO DS_SITUACAO_JULGAMENTO CD_SITUACAO_CASSACAO DS_SITUACAO_CASSACAO CD_SITUACAO_SUBSTITUICAO DS_SITUACAO_SUBSTITUICAO ST_REELEICAO DS_OCUPACAO'''.split()
COMP_KEEP = '''DT_GERACAO HH_GERACAO ANO_ELEICAO CD_ELEICAO SQ_CANDIDATO CD_DETALHE_SITUACAO_CAND DS_DETALHE_SITUACAO_CAND ST_REELEICAO CD_SITUACAO_CANDIDATO_PLEITO DS_SITUACAO_CANDIDATO_PLEITO CD_SITUACAO_CANDIDATO_URNA DS_SITUACAO_CANDIDATO_URNA ST_CANDIDATO_INSERIDO_URNA NM_TIPO_DESTINACAO_VOTOS CD_SITUACAO_CANDIDATO_TOT DS_SITUACAO_CANDIDATO_TOT ST_SUBSTITUIDO SQ_SUBSTITUIDO CD_SITUACAO_JULGAMENTO DS_SITUACAO_JULGAMENTO CD_SITUACAO_JULGAMENTO_PLEITO DS_SITUACAO_JULGAMENTO_PLEITO CD_SITUACAO_JULGAMENTO_URNA DS_SITUACAO_JULGAMENTO_URNA CD_SITUACAO_CASSACAO DS_SITUACAO_CASSACAO'''.split()
RS_KEYS = '''id name official_name full_name number party federation occupation status current_office history photo socials sites invalid_declared_urls pautas biography editorial_sources editorial_checked_at tse_url source_record'''.split()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], stderr=subprocess.PIPE)


def meaningful(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return None if text.upper() in MISSING else text


def fold(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', value) if not unicodedata.combining(c)).upper().strip()


def normalize_party(value: str) -> str:
    return PARTY_LOOKUP.get(value.strip().upper(), value.strip())


def is_federal_sp(row: dict[str, str]) -> bool:
    return row.get('SG_UF') == 'SP' and row.get('ANO_ELEICAO') == '2026' and row.get('CD_CARGO') == '6'


def selected(row: dict[str, str]) -> bool:
    return is_federal_sp(row) and row.get('SG_PARTIDO', '').strip().upper() in PARTY_LOOKUP


def sanitize(row: dict[str, str], keys: list[str]) -> dict[str, str]:
    return {key: row[key] for key in keys if key in row}


def status_class(value: str | None) -> str:
    statuses = {
        'DEFERIDO': 'deferida', 'DEFERIDO COM RECURSO': 'deferida_com_recurso',
        'INDEFERIDO': 'indeferida', 'INDEFERIDO COM RECURSO': 'indeferida_com_recurso',
        'INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO': 'indeferida_em_prazo_recursal_ou_com_recurso',
        'DEFERIDO EM PRAZO RECURSAL OU COM RECURSO': 'deferida_em_prazo_recursal_ou_com_recurso',
        'RENUNCIA': 'renuncia', 'RENUNCIADO': 'renuncia',
        'CANCELADO': 'cancelada', 'CANCELAMENTO': 'cancelada',
        'FALECIDO': 'falecimento', 'FALECIMENTO': 'falecimento',
        'SUBSTITUIDO': 'substituida', 'AGUARDANDO JULGAMENTO': 'pendente',
        'PENDENTE DE JULGAMENTO': 'pendente', 'CADASTRADO': 'pendente',
        'PEDIDO NAO CONHECIDO': 'pedido_nao_conhecido',
    }
    return statuses.get(fold(value or ''), 'nao_mapeada')


def download(url: str) -> tuple[bytes, dict[str, Any]]:
    errors = []
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'EsquerdaEmFoco-SP-RoundA/1.0 public-data-audit', 'Accept': '*/*'})
            with urllib.request.urlopen(request, timeout=90) as response:
                raw = response.read()
                meta = {'url': url, 'final_url': response.geturl(), 'retrieved_at': utc_now(), 'http_status': response.status, 'etag': response.headers.get('ETag'), 'last_modified': response.headers.get('Last-Modified'), 'bytes': len(raw), 'sha256': digest(raw)}
            if not raw:
                raise ValueError('Empty response')
            return raw, meta
        except Exception as exc:
            errors.append(str(exc))
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    raise RuntimeError(url + ': ' + '; '.join(errors))


def decode_csv(payload: bytes) -> tuple[str, str]:
    try:
        return payload.decode('utf-8-sig'), 'utf-8-sig'
    except UnicodeDecodeError:
        return payload.decode('latin-1'), 'latin-1'


def source_zip(url: str) -> tuple[list[dict[str, str]], dict[str, Any], zipfile.ZipFile]:
    raw, meta = download(url)
    archive = zipfile.ZipFile(io.BytesIO(raw))
    names = [n for n in archive.namelist() if n.upper().endswith('_SP.CSV')]
    if len(names) != 1:
        raise ValueError('Expected exactly one SP CSV; found ' + repr(names))
    payload = archive.read(names[0])
    text, encoding = decode_csv(payload)
    reader = csv.DictReader(io.StringIO(text), delimiter=';')
    rows = []
    for record, row in enumerate(reader, start=2):
        if None in row:
            raise ValueError('Malformed CSV record ' + str(record))
        row['_source_record'] = str(record)
        rows.append(row)
    meta.update({'member': names[0], 'member_sha256': digest(payload), 'member_bytes': len(payload), 'encoding': encoding, 'delimiter': ';', 'headers': reader.fieldnames, 'member_records': len(rows), 'locator': 'CSV record ordinal; header is record 1; not physical line number', 'generated_at_values': sorted({(r.get('DT_GERACAO', '') + ' ' + r.get('HH_GERACAO', '')).strip() for r in rows})})
    return rows, meta, archive


class PartyParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parties: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == 'article' and 'candidate' in (values.get('class') or '').split() and values.get('data-party'):
            self.parties.add(normalize_party(values['data-party'] or ''))


def inspect_baseline() -> dict[str, Any]:
    parser = PartyParser()
    baseline_html = git('show', BASELINE + ':index.html')
    parser.feed(baseline_html.decode('utf-8'))
    if sorted(parser.parties) != sorted(PARTIES):
        raise ValueError('SC baseline parties differ from the locked scope: ' + repr(parser.parties))
    reference = json.loads(git('show', BASELINE + ':data/rs/normalized.json'))
    if reference['scope_parties'] != PARTIES or reference['office_code'] != 6 or reference['election_year'] != 2026:
        raise ValueError('RS baseline contract differs')
    missing_keys = sorted(set(RS_KEYS) - set(reference['candidates'][0]))
    if missing_keys:
        raise ValueError('RS compatibility keys absent: ' + repr(missing_keys))
    refs = {}
    for label, branch in [('sc_pautas', 'feat/sc-federais-pautas-review-20260921'), ('pr', 'feat/parana-base-2026'), ('rs_review', 'feat/rs-federais-revisao-editorial')]:
        try:
            ref = git('rev-parse', 'origin/' + branch).decode().strip()
            files = git('ls-tree', '-r', '--name-only', ref).decode().splitlines()
            relevant = [p for p in files if any(w in p.lower() for w in ['taxonomy', 'taxonomia', 'pautas', '/pr/', 'parana']) and p.endswith(('.json', '.md', '.py'))]
            refs[label] = {'branch': branch, 'commit': ref, 'relevant_files': relevant}
        except subprocess.CalledProcessError:
            refs[label] = {'branch': branch, 'status': 'not_available_in_checkout'}
    baseline = {'commit': BASELINE, 'html_sha256': digest(baseline_html), 'sc_parties': sorted(parser.parties), 'rs_schema_version': reference['schema_version'], 'rs_compatible_candidate_fields': RS_KEYS, 'upstream': refs}
    dump(DOCS / 'baseline.json', baseline)
    return baseline


def make_candidate(row: dict[str, str], comp: dict[str, str], source: dict[str, Any], comp_source: dict[str, Any], collected: str) -> dict[str, Any]:
    cid = row['SQ_CANDIDATO']
    party = normalize_party(row['SG_PARTIDO'])
    detail = meaningful(comp.get('DS_DETALHE_SITUACAO_CAND')) or meaningful(row.get('DS_DETALHE_SITUACAO_CAND')) or meaningful(comp.get('DS_SITUACAO_JULGAMENTO')) or meaningful(row.get('DS_SITUACAO_CANDIDATURA'))
    clean_name = row['NM_URNA_CANDIDATO'].strip()
    slug = re.sub(r'[^a-z0-9]+', '-', fold(clean_name).lower()).strip('-') + '-' + cid
    statuses = {k: meaningful(v) for k, v in {**row, **comp}.items() if ('SITUACAO' in k or k in ['ST_SUBSTITUIDO', 'SQ_SUBSTITUIDO', 'ST_CANDIDATO_INSERIDO_URNA'])}
    return {
        'id': cid, 'name': clean_name, 'official_name': clean_name, 'full_name': row['NM_CANDIDATO'].strip(), 'number': row['NR_CANDIDATO'], 'party': party,
        'federation': meaningful(row.get('NM_FEDERACAO')), 'occupation': meaningful(row.get('DS_OCUPACAO')), 'status': detail,
        'current_office': None, 'history': [], 'photo': None, 'socials': [], 'sites': [], 'invalid_declared_urls': [], 'pautas': None, 'biography': None, 'editorial_sources': [], 'editorial_checked_at': None,
        'tse_url': 'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/2026/20322002026/SP/' + cid,
        'source_record': {'url': SOURCE_URL, 'id': cid, 'member': source['member'], 'csv_record': int(row['_source_record']), 'generated_at': row.get('DT_GERACAO', '') + ' ' + row.get('HH_GERACAO', ''), 'retrieved_at': source['retrieved_at'], 'member_sha256': source['member_sha256']},
        'complement_source_record': {'url': COMPLEMENT_URL, 'member': comp_source['member'], 'csv_record': int(comp['_source_record']) if comp else None, 'generated_at': comp.get('DT_GERACAO', '') + ' ' + comp.get('HH_GERACAO', ''), 'member_sha256': comp_source['member_sha256']},
        'state': 'SP', 'office_code': 6, 'election_year': 2026, 'slug': slug, 'status_code': status_class(detail), 'official_status_fields': statuses,
        'electoral_district': {'uf': 'SP', 'code': row.get('SG_UE'), 'name': row.get('NM_UE')},
        'municipality': None, 'municipality_note': 'Circunscrição estadual. Município de residência/atuação não foi inferido de naturalidade.',
        'registration_election': {'year': 2026, 'id': row.get('CD_ELEICAO'), 'round': meaningful(row.get('NR_TURNO')), 'date': meaningful(row.get('DT_ELEICAO')), 'votes': None, 'result': None, 'result_status': 'not_yet_held_at_snapshot'},
        'pauta_ids': [], 'research_status': {key: 'not_researched_round_a' for key in ['biography', 'pautas', 'history', 'current_office', 'socials', 'photo', 'municipality']},
        'link_validation': {'tse_url': 'constructed_using_existing_project_route_not_individually_http_verified'},
        'as_of': collected,
    }


def build_schema() -> dict[str, Any]:
    election = {'type': 'object', 'required': ['year', 'votes', 'result'], 'properties': {'year': {'const': 2026}, 'votes': {'type': 'null'}, 'result': {'type': 'null'}}}
    candidate = {'type': 'object', 'required': RS_KEYS + ['registration_election', 'research_status', 'status_code'], 'properties': {'id': {'type': 'string', 'pattern': '^[0-9]+$'}, 'number': {'type': 'string', 'pattern': '^[0-9]{4}$'}, 'party': {'enum': PARTIES}, 'pautas': {'type': 'null'}, 'biography': {'type': 'null'}, 'registration_election': election}}
    return {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'title': 'SP Round A — RS schema v1 compatible electoral core', 'type': 'object', 'required': ['schema_version', 'state', 'office_code', 'election_year', 'scope_parties', 'candidates'], 'properties': {'schema_version': {'const': 1}, 'state': {'const': 'SP'}, 'office_code': {'const': 6}, 'election_year': {'const': 2026}, 'scope_parties': {'const': PARTIES}, 'candidates': {'type': 'array', 'minItems': 1, 'items': candidate}}}


def run() -> None:
    collected = utc_now()
    DATA.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    existing = git('ls-files').decode().splitlines()
    protected = {p: digest(Path(p).read_bytes()) for p in existing if not p.startswith(('data/sp/', 'docs/sp/', 'tools/sp/', 'tests/sp/')) and p != '.github/workflows/sp-round-a.yml' and Path(p).is_file()}
    baseline = inspect_baseline()
    rows, source, archive = source_zip(SOURCE_URL)
    comp_rows, comp_source, comp_archive = source_zip(COMPLEMENT_URL)
    federal = [r for r in rows if is_federal_sp(r)]
    chosen = [r for r in rows if selected(r)]
    if not federal or not chosen:
        raise ValueError('No SP federal candidates; source/scope invalid')
    if any(r.get('NR_TURNO') not in [None, '', '1'] for r in federal):
        raise ValueError('Unexpected round in 2026 federal source')
    federal_ids = {r['SQ_CANDIDATO'] for r in federal}
    chosen_ids = {r['SQ_CANDIDATO'] for r in chosen}
    grouped_comp: dict[str, list[dict[str, str]]] = collections.defaultdict(list)
    for row in comp_rows:
        if row.get('ANO_ELEICAO') == '2026' and row.get('SQ_CANDIDATO') in federal_ids:
            grouped_comp[row['SQ_CANDIDATO']].append(row)
    problems: list[dict[str, Any]] = []
    for name, records in [('all_federal', federal), ('selected', chosen)]:
        duplicate_ids = [cid for cid, count in collections.Counter(r['SQ_CANDIDATO'] for r in records).items() if count > 1]
        if duplicate_ids:
            problems.append({'kind': 'duplicate_ids', 'collection': name, 'ids': duplicate_ids})
    missing_comp = sorted(federal_ids - set(grouped_comp))
    multiple_comp = sorted(cid for cid, group in grouped_comp.items() if len(group) != 1)
    if missing_comp:
        problems.append({'kind': 'missing_complement', 'ids': missing_comp})
    if multiple_comp:
        problems.append({'kind': 'duplicate_complement', 'ids': multiple_comp})
    required = ['SQ_CANDIDATO', 'NR_CANDIDATO', 'NM_CANDIDATO', 'NM_URNA_CANDIDATO', 'SG_PARTIDO', 'CD_ELEICAO']
    for row in federal:
        for key in required:
            if meaningful(row.get(key)) is None:
                problems.append({'kind': 'required_field_missing', 'id': row['SQ_CANDIDATO'], 'field': key})
        if not re.fullmatch(r'\d+', row['SQ_CANDIDATO']) or not re.fullmatch(r'\d{4}', row['NR_CANDIDATO']):
            problems.append({'kind': 'invalid_identifier_or_number', 'id': row['SQ_CANDIDATO']})
        group = grouped_comp.get(row['SQ_CANDIDATO'], [])
        if len(group) == 1:
            other = group[0]
            for key in ['CD_ELEICAO', 'DS_DETALHE_SITUACAO_CAND', 'DS_SITUACAO_JULGAMENTO', 'DS_SITUACAO_CASSACAO']:
                a, b = meaningful(row.get(key)), meaningful(other.get(key))
                if a and b and fold(a) != fold(b):
                    problems.append({'kind': 'cross_source_conflict', 'id': row['SQ_CANDIDATO'], 'field': key, 'candidates': a, 'complement': b})
    national_check: dict[str, Any] = {'status': 'not_available_in_archive', 'note': 'Complement reconciliation and exact scope partition remain required.'}
    national = [n for n in archive.namelist() if n.upper().endswith('_BRASIL.CSV')]
    if len(national) == 1:
        payload = archive.read(national[0])
        text, encoding = decode_csv(payload)
        national_sp = [r for r in csv.DictReader(io.StringIO(text), delimiter=';') if is_federal_sp(r)]
        national_map = {r['SQ_CANDIDATO']: sanitize(r, KEEP) for r in national_sp}
        local_map = {r['SQ_CANDIDATO']: sanitize(r, KEEP) for r in federal}
        def stable(records: dict[str, Any]) -> dict[str, Any]:
            return {cid: {k: v for k, v in row.items() if k not in ['DT_GERACAO', 'HH_GERACAO']} for cid, row in records.items()}
        same = stable(national_map) == stable(local_map) and len(national_sp) == len(federal)
        national_check = {'status': 'pass' if same else 'fail', 'member': national[0], 'member_sha256': digest(payload), 'encoding': encoding, 'sp_federal_count': len(national_sp)}
        if not same:
            problems.append({'kind': 'regional_vs_national_mismatch'})
    def export(records: list[dict[str, str]], keys: list[str]) -> list[dict[str, Any]]:
        return [{**sanitize(r, keys), '_source_record': int(r['_source_record'])} for r in sorted(records, key=lambda x: x['SQ_CANDIDATO'])]
    dump(DATA / 'all-candidates-official.json', export(federal, KEEP))
    dump(DATA / 'candidates-official.json', export(chosen, KEEP))
    selected_comp = [r for r in comp_rows if r.get('ANO_ELEICAO') == '2026' and r.get('SQ_CANDIDATO') in chosen_ids]
    dump(DATA / 'status-official.json', export(selected_comp, COMP_KEEP))
    outside = [r for r in federal if r['SQ_CANDIDATO'] not in chosen_ids]
    dump(DATA / 'out-of-scope.json', [{'id': r['SQ_CANDIDATO'], 'official_name': r['NM_URNA_CANDIDATO'], 'party': r['SG_PARTIDO'], 'reason': 'party_not_in_locked_project_scope', 'source_record': int(r['_source_record'])} for r in sorted(outside, key=lambda x: x['SQ_CANDIDATO'])])
    candidates = [make_candidate(r, grouped_comp.get(r['SQ_CANDIDATO'], [{}])[0], source, comp_source, collected) for r in chosen]
    candidates.sort(key=lambda c: (fold(c['party']), fold(c['name']), c['id']))
    for c in candidates:
        if c['status_code'] == 'nao_mapeada':
            problems.append({'kind': 'unmapped_selected_status', 'id': c['id'], 'value': c['status']})
        if not set(RS_KEYS).issubset(c):
            problems.append({'kind': 'rs_compatibility_keys_missing', 'id': c['id']})
    normalized = {'schema_version': 1, 'stage': 'round_a', 'state': 'SP', 'office_code': 6, 'election_year': 2026, 'as_of': collected[:10], 'collected_at': collected, 'scope_parties': PARTIES, 'candidates': candidates}
    dump(DATA / 'normalized.json', normalized)
    by_party = dict(sorted(collections.Counter(normalize_party(r['SG_PARTIDO']) for r in federal).items()))
    selected_by_party = {p: sum(c['party'] == p for c in candidates) for p in PARTIES}
    status_counts = dict(sorted(collections.Counter(c['status'] for c in candidates).items()))
    exceptional = [{'id': c['id'], 'name': c['name'], 'number': c['number'], 'party': c['party'], 'status': c['status'], 'status_code': c['status_code'], 'official_status_fields': c['official_status_fields'], 'source_record': c['source_record'], 'complement_source_record': c['complement_source_record']} for c in candidates if c['status_code'] != 'deferida']
    dump(DATA / 'exceptional-statuses.json', exceptional)
    duplicate_numbers = {number: [c['id'] for c in candidates if c['number'] == number] for number, count in collections.Counter(c['number'] for c in candidates).items() if count > 1}
    substitutions = []
    all_sp_ids = {r['SQ_CANDIDATO'] for r in rows}
    for c in candidates:
        fields = c['official_status_fields']
        target = meaningful(fields.get('SQ_SUBSTITUIDO'))
        if target or fields.get('ST_SUBSTITUIDO') in {'S', 'SIM'}:
            substitutions.append({'id': c['id'], 'ST_SUBSTITUIDO': fields.get('ST_SUBSTITUIDO'), 'SQ_SUBSTITUIDO': target, 'reference_resolution': 'same_selected_scope' if target in chosen_ids else 'other_sp_record' if target in all_sp_ids else 'no_reference' if target is None else 'unresolved', 'note': 'Official columns preserved; no direction or identity merge inferred.'})
            if target and target not in all_sp_ids:
                problems.append({'kind': 'unresolved_substitution_reference', 'id': c['id'], 'reference': target})
    protected_changes = [p for p, sha in protected.items() if not Path(p).exists() or digest(Path(p).read_bytes()) != sha]
    if protected_changes:
        problems.append({'kind': 'protected_files_changed', 'paths': protected_changes})
    new_paths = [p for p in git('ls-files', '--others', '--exclude-standard').decode().splitlines() if not p.startswith(('data/sp/', 'docs/sp/'))]
    if new_paths:
        problems.append({'kind': 'unexpected_output_paths', 'paths': new_paths})
    source.update({'sp_federal_count': len(federal), 'selected_count': len(chosen), 'all_sp_count': len(rows)})
    comp_source.update({'matched_federal_ids': len(grouped_comp), 'matched_selected_rows': len(selected_comp)})
    manifest = {'schema_version': 1, 'stage': 'round_a', 'state': 'SP', 'office_code': 6, 'election_year': 2026, 'collected_at': collected, 'completed_at': utc_now(), 'baseline_commit': BASELINE, 'pipeline_commit': git('rev-parse', 'HEAD').decode().strip(), 'scope_parties': PARTIES, 'sources': [source, comp_source], 'all_sp_federal_count': len(federal), 'all_sp_federal_by_party': by_party, 'selected_count': len(chosen), 'selected_by_party': selected_by_party, 'empty_parties': [p for p, n in selected_by_party.items() if n == 0], 'selected_by_status': status_counts, 'privacy': {'mode': 'explicit_field_allowlist', 'excluded': ['CPF', 'voter_registration', 'birth_date', 'personal_address', 'personal_email', 'gender', 'race', 'ethnicity', 'assets']}, 'editorial_enrichment': 'not_started', 'frontend_changed': False}
    dump(DATA / 'manifest.json', manifest)
    taxonomy = {'status': 'upstream_review_dependency', 'assignments_created': 0, 'policy': 'Do not create a SP-specific taxonomy or infer candidate positions from party membership. Freeze upstream IDs only after SC taxonomy is explicitly available and reviewed.', 'upstream': baseline['upstream'].get('sc_pautas'), 'blocks': 'Round B candidate-to-topic assignments, not official electoral reconciliation'}
    dump(DATA / 'taxonomy.lock.json', taxonomy)
    dump(DATA / 'schema.json', build_schema())
    audit = {'gate': 'PASS' if not problems else 'BLOCKED', 'scope': 'official electoral snapshot only', 'collected_at': collected, 'all_sp_records': len(rows), 'all_sp_federal_count': len(federal), 'selected_count': len(chosen), 'out_of_scope_count': len(outside), 'scope_partition_exact': chosen_ids.isdisjoint({r['SQ_CANDIDATO'] for r in outside}) and len(chosen) + len(outside) == len(federal), 'selected_by_party': selected_by_party, 'selected_by_status': status_counts, 'unique_selected_ids': len(chosen_ids), 'unique_slugs': len({c['slug'] for c in candidates}), 'missing_complement_ids': missing_comp, 'multiple_complement_ids': multiple_comp, 'national_crosscheck': national_check, 'reused_ballot_numbers': duplicate_numbers, 'substitutions': substitutions, 'exceptional_status_count': len(exceptional), 'protected_files_checked': len(protected), 'protected_files_changed': protected_changes, 'protected_files_sha256': protected, 'problems': problems, 'limitations': ['Snapshot subject to subsequent official updates.', 'Candidacy and complementary files are different exports of TSE systems, not independent institutions.', 'No current or past office, biography, social links, images or policy position researched in Round A.', 'SP frontend is not created or published.', 'SC topic taxonomy remains an explicit upstream dependency; no taxonomy approval asserted.', 'DivulgaCand profile links follow the project route; individual endpoints not HTTP-verified.']}
    dump(DOCS / 'reconciliation.json', audit)
    report = ['# SP · Deputados federais · Round A', '', '**Gate eleitoral: ' + audit['gate'] + '**', '', '- Coleta: ' + collected, '- Baseline: `' + BASELINE + '`.', '- Universo federal SP: **' + str(len(federal)) + '** registros.', '- Recorte do projeto: **' + str(len(chosen)) + '** registros.', '- Fora do recorte partidário: **' + str(len(outside)) + '** registros, preservados na auditoria.', '', '## Recorte por partido', '', '| Partido | Registros |', '|---|---:|']
    report += ['| ' + party + ' | ' + str(count) + ' |' for party, count in selected_by_party.items()]
    report += ['', '## Situação oficial', '', '| Situação | Registros |', '|---|---:|'] + ['| ' + str(status) + ' | ' + str(count) + ' |' for status, count in status_counts.items()]
    report += ['', '## Critérios e limites', '', 'Ano 2026, UF SP, cargo 6. Oito siglas herdadas de SC/RS, comparação sem distinção de caixa. Nenhuma candidatura é retirada devido à situação do registro. O recorte é operacional e não classifica ideologicamente siglas externas.', '', 'Nomes e números são preservados da fonte. Identificadores são strings. Localidade estadual não é tratada como município de residência. Resultado e votos de 2026 permanecem nulos; listas históricas vazias significam pesquisa não iniciada, não ausência de participação anterior.', '', 'O contrato mantém os campos do schema v1 do RS e acrescenta proveniência, situação detalhada e estados explícitos de pesquisa. CPF, título, data de nascimento e outros campos desnecessários não são exportados.', '', '## Taxonomia e dependência upstream', '', 'A taxonomia revisada de SC não é declarada homologada nesta rodada. `data/sp/taxonomy.lock.json` registra a referência upstream. Nenhuma tag individual foi atribuída. Essa dependência deve ser resolvida antes da classificação do Round B.', '', '## Auditoria', '', '- Identificadores únicos no recorte: ' + str(len(chosen_ids)) + '.', '- Informações complementares ausentes: ' + str(len(missing_comp)) + '.', '- Complementos duplicados: ' + str(len(multiple_comp)) + '.', '- Registros com situação diferente de deferido: ' + str(len(exceptional)) + '.', '- Arquivos protegidos conferidos: ' + str(len(protected)) + '.', '- Arquivos protegidos alterados: ' + str(len(protected_changes)) + '.', '- Problemas bloqueantes: ' + str(len(problems)) + '.', '', 'Consulte `reconciliation.json` para conflitos, substituições, números reutilizados e prova de isolamento. Consulte `manifest.json` para URLs, hashes completos e horários de geração de cada fonte. Os localizadores usam ordinal de registro CSV (cabeçalho = 1), não número de linha física.', '', '## Fontes', '', '- [Portal de Dados Abertos do TSE](' + PORTAL + ').', '- [Candidaturas 2026](' + SOURCE_URL + ').', '- [Informações complementares 2026](' + COMPLEMENT_URL + ').', '', '## Próximas etapas (não executadas)', '', 'Round B: reconciliar a taxonomia upstream, pesquisar perfis em lotes e atribuir pautas com evidências. Round C: integração, regressão de interface e publicação. Nenhum frontend, rota, navbar ou arquivo de SC/RS/PR foi modificado por este pipeline.', '']
    (DOCS / 'ROUND-A.md').write_text('\n'.join(report), encoding='utf-8')
    with (DATA / 'candidates.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=['id', 'number', 'official_name', 'full_name', 'party', 'federation', 'status', 'status_code', 'tse_url'], delimiter=';')
        writer.writeheader()
        writer.writerows({key: c.get(key) for key in writer.fieldnames} for c in candidates)
    inventory = {str(p): digest(p.read_bytes()) for root in [DATA, DOCS] for p in root.rglob('*') if p.is_file() and p.name not in {'checksums.json', 'execution.log', 'dataset-tests.txt'}}
    dump(DOCS / 'checksums.json', inventory)
    summary = {k: v for k, v in audit.items() if k not in ['protected_files_sha256']}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    archive.close()
    comp_archive.close()
    if problems or not audit['scope_partition_exact']:
        raise SystemExit('Official reconciliation blocked; inspect docs/sp/reconciliation.json')


class UnitTests(unittest.TestCase):
    def test_party_case(self) -> None:
        self.assertEqual(normalize_party('PCDOB'), 'PCdoB')
        self.assertEqual(normalize_party(' pcdoB '), 'PCdoB')
    def test_non_scope_party(self) -> None:
        self.assertNotIn('PSTU', PARTY_LOOKUP)
        self.assertNotIn('REDE', PARTY_LOOKUP)
    def test_scope_is_not_status_filter(self) -> None:
        row = {'SG_UF': 'SP', 'ANO_ELEICAO': '2026', 'CD_CARGO': '6', 'SG_PARTIDO': 'PT', 'DS_DETALHE_SITUACAO_CAND': 'RENÚNCIA'}
        self.assertTrue(selected(row))
    def test_other_year_rejected(self) -> None:
        self.assertFalse(selected({'SG_UF': 'SP', 'ANO_ELEICAO': '2022', 'CD_CARGO': '6', 'SG_PARTIDO': 'PT'}))
    def test_other_office_rejected(self) -> None:
        self.assertFalse(selected({'SG_UF': 'SP', 'ANO_ELEICAO': '2026', 'CD_CARGO': '7', 'SG_PARTIDO': 'PT'}))
    def test_other_state_rejected(self) -> None:
        self.assertFalse(selected({'SG_UF': 'RS', 'ANO_ELEICAO': '2026', 'CD_CARGO': '6', 'SG_PARTIDO': 'PT'}))
    def test_sentinels_not_zero(self) -> None:
        for value in [None, '', '#NULO', '#NULO#', '#NE', '#NE#', '-1', '-3', '-4']:
            self.assertIsNone(meaningful(value))
        self.assertEqual(meaningful('0'), '0')
    def test_status_mapping(self) -> None:
        self.assertEqual(status_class('RENÚNCIA'), 'renuncia')
        self.assertEqual(status_class('DEFERIDO'), 'deferida')
        self.assertEqual(status_class('INDEFERIDO COM RECURSO'), 'indeferida_com_recurso')
    def test_status_source_variants(self) -> None:
        self.assertEqual(status_class('INDEFERIDO EM PRAZO RECURSAL OU COM RECURSO'), 'indeferida_em_prazo_recursal_ou_com_recurso')
        self.assertEqual(status_class('DEFERIDO EM PRAZO RECURSAL OU COM RECURSO'), 'deferida_em_prazo_recursal_ou_com_recurso')
    def test_missing_marker_falls_back_to_judgment(self) -> None:
        values = {'DS_DETALHE_SITUACAO_CAND': '#NE', 'DS_SITUACAO_JULGAMENTO': 'DEFERIDO'}
        detail = meaningful(values['DS_DETALHE_SITUACAO_CAND']) or meaningful(values['DS_SITUACAO_JULGAMENTO'])
        self.assertEqual(detail, 'DEFERIDO')
    def test_unknown_status_not_invented(self) -> None:
        self.assertEqual(status_class('NOVA SITUAÇÃO'), 'nao_mapeada')
    def test_explicit_allowlist(self) -> None:
        source = {'SQ_CANDIDATO': '123456789012', 'NR_CPF_CANDIDATO': 'NOT-EXPORTED', 'NM_CANDIDATO': 'TEST'}
        self.assertNotIn('NR_CPF_CANDIDATO', sanitize(source, KEEP))
        self.assertEqual(sanitize(source, KEEP)['SQ_CANDIDATO'], '123456789012')
    def test_decode(self) -> None:
        self.assertEqual(decode_csv('São Paulo'.encode('utf-8'))[0], 'São Paulo')
        self.assertEqual(decode_csv('São Paulo'.encode('latin-1'))[0], 'São Paulo')
    def test_html_scope_parser(self) -> None:
        parser = PartyParser()
        parser.feed('<article class="candidate" data-party="PCDOB"></article>')
        self.assertEqual(parser.parties, {'PCdoB'})
    def test_schema_builds(self) -> None:
        schema = build_schema()
        self.assertEqual(schema['properties']['state']['const'], 'SP')
        self.assertEqual(schema['properties']['candidates']['items']['properties']['registration_election']['properties']['votes']['type'], 'null')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        unittest.main(argv=['round_a'], verbosity=2)
    else:
        try:
            run()
        except Exception as exc:
            dump(DOCS / 'execution-error.json', {'status': 'BLOCKED', 'time': utc_now(), 'error': str(exc)})
            raise

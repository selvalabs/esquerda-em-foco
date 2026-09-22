"""RS-EST-AD2-CLOSE: frozen-source replay, individual coverage and recovery QA.

A failed request or a named query never becomes evidence of no political agenda.
This closes the recoverable increment, not the outstanding editorial research.
No automatic policy, office or nominal-vote inference is performed.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import contextlib
import csv
import hashlib
import html
import importlib.util
import io
import ipaddress
import json
import re
import runpy
import socket
import subprocess
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / 'data/rs-estaduais'
DOC = ROOT / 'docs/rs-estaduais'
A = DOC / 'ad2-close'
P = ROOT / 'rs/deputados-estaduais'
RECOVERED_HEAD = 'b73e18867d2d11c08a0c466fa3c55f3f15398184'
AD_HEAD = '449630a113e6166dec3b1ae49ebe6f9b29c84892'
RECOVERED_HTML = '7030db0e88de345dd7b1726ffbae437fd56d27c5b30dcab0fb0ff8b6d2832a50'
RECOVERED_ARTIFACT = {'run_id': 35648445765, 'artifact_id': 10660708420,
    'sha256': '8ea0f3e115e3363057b0e6d9955be91fb3a2fa416a5d57fedfeed946b2fcabed'}
STATUSES = {'policy_summary_verified', 'individual_sources_reviewed_insufficient',
    'source_access_blocked', 'identity_ambiguity', 'research_pending'}
LABELS = {'policy_summary_verified': 'Síntese com fonte individual',
    'individual_sources_reviewed_insufficient': 'Fontes consultadas: material insuficiente',
    'source_access_blocked': 'Leitura de fonte relevante bloqueada',
    'identity_ambiguity': 'Identidade da fonte ainda não conciliada',
    'research_pending': 'Pesquisa complementar pendente'}
NEXT = {'policy_summary_verified': 'Revisão editorial independente E; conferir atribuição, período e alcance das fontes.',
    'individual_sources_reviewed_insufficient': 'Buscar entrevista, proposta ou manifestação individual complementar; não presumir ausência de propostas.',
    'source_access_blocked': 'Procurar outra fonte pública equivalente ou tentar novamente sem contornar autenticação.',
    'identity_ambiguity': 'Conciliar nome civil, partido, território e contexto antes de atribuir a fonte.',
    'research_pending': 'Aprofundar a busca nominal com leitura de fontes individuais; não tratar consulta inicial como pesquisa exaustiva.'}
INPUT_NAMES = ['candidates-official.json', 'manifest.json', 'profiles-official.json',
    'history-official.json', 'social-official.json', 'status-official.json',
    'photos-official.json', 'election-api.json', 'editorial-additions.json',
    'ad2-editorial.json', 'ad2-offices.json', 'ad2-searches.json', 'ad2-source-checks.json',
    'ad2-votes.json', 'ad2-historical-status.json', 'votes-phase2.json']
STABLE_EXPORTS = ['rs/deputados-estaduais/index.html', 'rs/deputados-estaduais/dados.json',
    'rs/deputados-estaduais/candidaturas.csv', 'rs/deputados-estaduais/pesquisa.json',
    'data/rs-estaduais/history-normalized.json', 'data/rs-estaduais/editorial.json',
    'data/rs-estaduais/offices-verified.json']


def load(path, default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def stamp():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def counts(records):
    return {'candidates': len(records), 'policy_summaries': sum(bool(c['pautas']) for c in records),
        'policy_gaps': sum(not c['pautas'] for c in records),
        'current_offices': sum(bool(c['current_office']) for c in records),
        'with_activity': sum(bool(c['activities']) for c in records),
        'acts': sum(len(c['activities']) for c in records),
        'past_history_rows': sum(h['year'] < 2026 for c in records for h in c['history']),
        'historical_vote_rows': sum(h['year'] < 2026 and h.get('votes') is not None for c in records for h in c['history'])}


def input_hashes():
    paths = {D / name for name in INPUT_NAMES}
    paths.update(D.glob('phase2-editorial*.json'))
    paths.update(D.glob('phase2-offices*.json'))
    paths.update((D / 'raw').glob('*.csv'))
    paths.add(ROOT / 'config/party-scope-2026.json')
    for path in paths:
        if not path.is_file():
            raise ValueError('Required frozen input missing: ' + str(path))
    return {str(p.relative_to(ROOT)): sha(p) for p in sorted(paths)}


def check_scope():
    config = load(ROOT / 'config/party-scope-2026.json')
    manifest = load(D / 'manifest.json')
    if config['parties'] != manifest['scope']['parties']:
        raise ValueError('Manifest must use the shared canonical scope')
    scope = {p.upper(): p for p in config['parties']}
    if len(scope) != len(config['parties']):
        raise ValueError('Duplicate canonical party')
    with (D / 'raw/universo-rs-estaduais-2026.csv').open(encoding='utf-8', newline='') as f:
        universe = list(csv.DictReader(f, delimiter=';'))
    if any((r['SG_UF'], r['CD_CARGO'], r['ANO_ELEICAO']) != ('RS', '7', '2026') for r in universe):
        raise ValueError('Universe includes another state, office or election')
    selected = [r for r in universe if r['SG_PARTIDO'].upper() in scope]
    raw = load(D / 'candidates-official.json')
    profiles = load(D / 'profiles-official.json')
    normalized = load(D / 'normalized.json')['candidates']
    expected = {r['SQ_CANDIDATO'] for r in selected}
    if len(expected) != len(selected) or expected != {r['SQ_CANDIDATO'] for r in raw} or expected != {c['id'] for c in normalized}:
        raise ValueError('Universe, selected CSV and published candidates disagree')
    for row in raw:
        cid = row['SQ_CANDIDATO']; obj = profiles[cid]['data']
        if str(obj['id']) != cid or str(obj['numero']) != row['NR_CANDIDATO'] or str(obj['cargo']['codigo']) != '7' or obj['partido']['sigla'].upper() != row['SG_PARTIDO'].upper():
            raise ValueError('Frozen individual profile mismatch: ' + cid)
    current = {c['id']: c for c in normalized}
    statuses = collections.Counter(current[cid]['status'] for cid in expected)
    rows = [{'party': party, 'belongs_to_scope': True,
        'count': sum(r['SG_PARTIDO'].upper() == party.upper() for r in selected)} for party in config['parties']]
    report = {'checked_at': stamp(), 'source': 'config/party-scope-2026.json',
        'config_sha256': sha(ROOT / 'config/party-scope-2026.json'),
        'official_universe': len(universe), 'selected': len(expected), 'published': len(normalized),
        'by_party': rows, 'frozen_statuses': dict(statuses),
        'empty_parties': [r['party'] for r in rows if not r['count']],
        'status_as_of': manifest['snapshot_generated_at'], 'electoral_snapshot_refreshed': False,
        'correction_from_original_145': {'added_ids': ['210002533927', '210002533932', '210002544838', '210002544839'],
            'note': 'Correção canônica anterior ao fechamento; duas candidaturas REDE e duas PSTU. PCB e PCO também pertencem ao critério, com contagem zero neste snapshot.'}}
    save(A / 'scope-reconciliation.json', report)
    return report


def capture_recovery():
    A.mkdir(parents=True, exist_ok=True)
    records = load(D / 'normalized.json')['candidates']
    hashes = input_hashes()
    report = {'recovered_head': RECOVERED_HEAD, 'last_AD_head': AD_HEAD,
        'artifact_verified_locally': RECOVERED_ARTIFACT, 'recovered_counts': counts(records),
        'correction_to_unverified_chat_summary': {'summaries_claimed': 71, 'summaries_in_recovered_data': 61,
            'votes_claimed': 394, 'votes_in_recovered_data': 395},
        'source_inputs': hashes, 'recovered_html_sha256': RECOVERED_HTML,
        'local_only_work_not_preserved_cannot_be_confirmed': True,
        'recovery_basis': 'Arquivos versionados e artefato de CI identificado por SHA-256. Não se presumem dez sínteses locais ausentes da branch.'}
    if (ROOT / '.git').exists():
        report['closure_source_commit'] = git('rev-parse', 'HEAD')
        report['recovered_commit_subject'] = git('show', '-s', '--format=%s', RECOVERED_HEAD)
        report['changes_since_AD'] = git('diff', '--name-status', AD_HEAD, RECOVERED_HEAD).splitlines()
        matches = []
        for path, checksum in hashes.items():
            raw = subprocess.check_output(['git', 'show', RECOVERED_HEAD + ':' + path], cwd=ROOT)
            matches.append({'path': path, 'recovered_sha256': hashlib.sha256(raw).hexdigest(),
                'matches_recovery_head': hashlib.sha256(raw).hexdigest() == checksum})
        if not all(x['matches_recovery_head'] for x in matches):
            raise ValueError('Frozen inputs changed before recovery reconciliation')
        report['input_git_comparison'] = matches
        original_html = subprocess.check_output(['git', 'show', RECOVERED_HEAD + ':rs/deputados-estaduais/index.html'], cwd=ROOT)
        if hashlib.sha256(original_html).hexdigest() != RECOVERED_HTML:
            raise ValueError('Recovered generated HTML does not match the audited artifact')
    else:
        report['git_comparison'] = 'unavailable_in_standalone_package; verified by CI with full history'
    save(A / 'recovery-audit.json', report)
    return hashes


@contextlib.contextmanager
def deny_network():
    old_open, old_connect = urllib.request.urlopen, socket.socket.connect
    def blocked(*args, **kwargs):
        raise RuntimeError('Network forbidden in frozen-input replay')
    urllib.request.urlopen = blocked
    socket.socket.connect = blocked
    try:
        yield
    finally:
        urllib.request.urlopen, socket.socket.connect = old_open, old_connect


def replay():
    """Delete only derived exports; preserve frozen sources and official portraits."""
    frozen = capture_recovery()
    logs = []
    def script(name):
        with contextlib.redirect_stdout(io.StringIO()) as output:
            runpy.run_path(str(ROOT / 'tools/rs-estaduais' / name), run_name='__main__')
        logs.append({'script': name, 'stdout_sha256': hashlib.sha256(output.getvalue().encode()).hexdigest()})
    outputs = []
    with deny_network():
        for pass_number in (1, 2):
            for name in ('index.html', 'dados.json', 'fontes.json', 'cobertura.json', 'pesquisa.json', 'candidaturas.csv'):
                (P / name).unlink(missing_ok=True)
            script('collect.py')
            script('research.py')
            script('build.py')
            for name in ('votes.py', 'phase2_votes.py', 'finalize_sources.py', 'phase2_apply.py', 'ad2_apply.py', 'build.py', 'ad2_views.py'):
                script(name)
            outputs.append({'pass': pass_number, 'hashes': {name: sha(ROOT / name) for name in STABLE_EXPORTS}})
    if outputs[0]['hashes'] != outputs[1]['hashes']:
        raise ValueError('Two clean-output replays are not byte-identical')
    if input_hashes() != frozen:
        raise ValueError('Replay changed a frozen official or reviewed source')
    save(A / 'reproducibility.json', {'network_used': False, 'clean_output_passes': 2,
        'byte_identical_stable_exports': True, 'passes': outputs, 'script_executions': logs,
        'frozen_inputs_unchanged': True,
        'timestamp_note': 'Datas de conciliação interna em fontes.json podem variar; exportações listadas foram comparadas byte a byte. Datas originais das consultas permanecem nos inputs imutáveis.'})
    print('Two offline clean-output replays passed; frozen inputs unchanged.')


def public_url(value):
    try:
        p = urlsplit(str(value)); host = p.hostname or ''
        if host.endswith(('.local', '.internal', '.localhost')) or host == 'localhost':
            return False
        try:
            if not ipaddress.ip_address(host).is_global:
                return False
        except ValueError:
            pass
        return p.scheme in ('https', 'http') and '.' in host and not p.username and not p.password and p.port in (None, 80, 443) and not re.search(r'[\x00-\x20]', str(value))
    except ValueError:
        return False


def probe_sources():
    """Availability only: no text-to-policy, office or nominal-total inference."""
    safe = module('closure_safe_http', ROOT / 'tools/rs-estaduais/research.py')
    records = load(D / 'normalized.json')['candidates']
    tasks = collections.defaultdict(set)
    for c in records:
        urls = [s['url'] for s in c['editorial_sources']] + [a['source'] for a in c['activities']]
        if c['current_office']:
            urls += [c['current_office']['source']]
        if not c['pautas']:
            urls += [s['url'] for s in c['sites']]
        for url in urls:
            if public_url(url) and not url.lower().endswith(('.zip', '.pdf')):
                tasks[url].add(c['id'])
    for c in load(D / 'ad2-source-checks.json')['checks']:
        if c.get('url') and public_url(c['url']):
            tasks[c['url']].add(c['candidate_id'])
    for cid, decision in load(D / 'close-source-review.json', {'decisions': {}})['decisions'].items():
        for url in decision.get('source_urls', []):
            if public_url(url):
                tasks[url].add(cid)
    for row in load(D / 'ad2-historical-status.json'):
        tasks[row['source_url']].add(row['current_candidate_id'])
    def inspect(item):
        url, ids = item
        result = {'url': url, 'candidate_ids': sorted(ids), 'checked_at': stamp(),
            'automated_availability_only': True, 'new_content_fact_checked': False}
        try:
            raw, final, status, mime = safe.read(url, 8)
            result.update({'http_status': status, 'final_url': final, 'sha256': hashlib.sha256(raw).hexdigest()})
            if 'json' in mime or urlsplit(url).path.startswith('/divulga/rest/'):
                obj = json.loads(raw)
                result.update({'outcome': 'json_read', 'historical_candidate_id': str(obj.get('id')),
                    'note': 'Disponibilidade de cadastro histórico; não confirma total de votos e não atualiza 2026.'})
                return result
            soup = BeautifulSoup(raw, 'html.parser')
            title = soup.title.get_text(' ', strip=True) if soup.title else ''
            for node in soup.select('script,style,nav,header,footer,form'):
                node.decompose()
            text = soup.get_text(' ', strip=True)
            if re.search(r'access denied|verify you are human|just a moment|verifica.{0,30}rob[oô]|acesso negado|captcha|security check', text[:2500] + title, re.I):
                result['outcome'] = 'access_interstitial'
            elif len(text.split()) < 35:
                result['outcome'] = 'no_readable_body'
            else:
                result['outcome'] = 'html_body_read'
            result['title'] = ' '.join(title.split()[:20])
            result['word_count'] = len(text.split())
        except Exception as exc:
            result.update({'outcome': 'request_failed', 'error_type': type(exc).__name__, 'http_status': getattr(exc, 'code', None)})
        return result
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(inspect, sorted(tasks.items())))
    save(A / 'source-availability.json', {'checked_at': stamp(), 'attempted_urls': len(results),
        'outcomes': dict(collections.Counter(x['outcome'] for x in results)), 'sources': results,
        'limits': 'HTTP 200 e página legível não provam identidade, pauta, execução ou mandato. Nenhuma restrição foi contornada. A coleta não altera texto editorial, total nominal nem cadastro de 2026.'})
    print(json.dumps({'source_urls_attempted': len(results), 'outcomes': dict(collections.Counter(x['outcome'] for x in results))}, ensure_ascii=False))


def choose_status(candidate, decision=None):
    if candidate['pautas']:
        if decision and decision.get('status') != 'policy_summary_verified':
            raise ValueError('A source decision cannot erase a published summary')
        if not candidate['editorial_sources'] or not candidate['editorial_checked_at']:
            raise ValueError('A summary requires individual reviewed sources')
        return 'policy_summary_verified'
    if not decision:
        return 'research_pending'
    status = decision['status']
    if status not in STATUSES - {'policy_summary_verified'}:
        raise ValueError('Invalid research status')
    if status != 'research_pending' and (not decision.get('source_urls') or not decision.get('reason') or not decision.get('checked_at')):
        raise ValueError('A non-pending status requires explicit source review')
    if status != 'research_pending':
        if not all(public_url(u) for u in decision['source_urls']):
            raise ValueError('Unsafe review source URL')
        if date.fromisoformat(decision['checked_at'][:10]) > date(2026, 9, 22):
            raise ValueError('Future source review date')
    return status


def validate_editorial(records):
    reviewed = load(D / 'editorial.json'); issues = []; acts = []
    for c in records:
        if c['pautas']:
            e = reviewed[c['id']]
            if not e.get('reviewed') or e.get('pautas') != c['pautas'] or not c['editorial_sources']:
                raise ValueError('Summary is not tied to its reviewed source: ' + c['id'])
        for s in c['editorial_sources']:
            if not public_url(s.get('url')) or not (s.get('locator') or s.get('label')):
                raise ValueError('Source without URL or locator: ' + c['id'])
            if s.get('published_at') and s['published_at'][:10] > '2026-09-21':
                raise ValueError('Post-cutoff source in frozen edition: ' + c['id'])
        if c['current_office']:
            office = c['current_office']; host = urlsplit(office['source']).hostname or ''
            if not public_url(office['source']) or not host.endswith(('.gov.br', '.leg.br')) or not office.get('checked_at'):
                raise ValueError('Current office lacks dated institutional source: ' + c['id'])
        for index, act in enumerate(c['activities']):
            host = urlsplit(act['source']).hostname or ''
            if not public_url(act['source']) or not host.endswith(('.gov.br', '.leg.br')) or not act.get('kind'):
                raise ValueError('Act without institutional primary reference: ' + c['id'])
            number = act.get('bill_number') or act.get('proposal_number')
            if not number:
                match = re.search(r'\b(?:PLCL|PLL|PL|REQ|VT)\s+\d+(?:/\d+)?', act.get('text', ''))
                number = match.group(0) if match else None
            if not number and act['kind'] in ('bill_authorship', 'bill_coauthorship', 'bill_list_record', 'bill_rapporteur'):
                issues.append({'candidate_id': c['id'], 'field': 'act_identifier', 'act_index': index,
                    'reason': 'Número não explicitado na fonte preservada; não foi inventado.', 'source': act['source']})
            acts.append({'candidate_id': c['id'], 'name': c['name'], 'kind': act['kind'], 'identifier': number,
                'date': act.get('date'), 'year': act.get('year'), 'date_basis': act.get('date_basis', 'unspecified_in_previous_review'),
                'source': act['source'], 'statement': act['text']})
    save(A / 'editorial-structure-audit.json', {'candidate_count': len(records),
        'reviewed_summary_count': sum(bool(c['pautas']) for c in records), 'published_act_count': len(acts),
        'missing_source_errors': 0, 'acts': acts, 'follow_up': issues,
        'independent_final_editorial_review_E_completed': False,
        'note': 'Rastreabilidade e consistência da edição recuperada; não substitui leitura independente E de todas as afirmações.'})


def csv_file(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore', delimiter=';', quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            out = {}
            for key in fields:
                value = row.get(key)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False)
                if isinstance(value, str) and value.startswith(('=', '+', '-', '@', '\t', '\r')):
                    value = "'" + value
                out[key] = value
            writer.writerow(out)


def publish_audit():
    check_scope()
    data = load(D / 'normalized.json'); records = data['candidates']
    original = {c['candidate_id']: c for c in load(D / 'ad2-research-ledger.json')}
    reviews = load(D / 'close-source-review.json', {'decisions': {}})
    decisions = reviews['decisions']
    if set(decisions) - {c['id'] for c in records}:
        raise ValueError('Unknown identity in closure research review')
    ledger = []
    for c in records:
        cid = c['id']; old = original.get(cid, {}); decision = decisions.get(cid)
        if decision and decision.get('expected_name') != c['official_name']:
            raise ValueError('Closure research identity mismatch: ' + cid)
        status = choose_status(c, decision)
        row = {'candidate_id': cid, 'name': c['name'], 'number': c['number'], 'party': c['party'],
            'research_status': status, 'status_label': LABELS[status], 'research_exhaustive': False,
            'policy_summary': bool(c['pautas']), 'source_review': decision,
            'searches': old.get('searches', []), 'previous_source_checks': old.get('source_checks', []),
            'policy_sources': c['editorial_sources'], 'institutional_activity_count': len(c['activities']),
            'current_office_status': 'confirmed_in_preserved_source' if c['current_office'] else 'not_confirmed',
            'current_office_source': c['current_office'], 'next_action': NEXT[status], 'tse_url': c['tse_url']}
        if not c['pautas'] and not row['searches']:
            raise ValueError('Missing recorded nominal search in unresolved candidature: ' + cid)
        ledger.append(row)
        c['research_status'] = {'status': status, 'label': LABELS[status], 'exhaustive': False,
            'evidence_cutoff': '2026-09-21', 'closure_recorded_on': '2026-09-22',
            'search_count': len(row['searches']), 'details_url': 'pesquisa-status.json'}
        c['current_office_verification_status'] = row['current_office_status']
    validate_editorial(records)
    save(D / 'research-status.json', ledger)
    save(A / 'candidate-coverage.json', ledger)
    fields = ['candidate_id', 'name', 'number', 'party', 'research_status', 'policy_summary',
        'institutional_activity_count', 'current_office_status', 'research_exhaustive', 'next_action', 'tse_url']
    csv_file(A / 'candidate-coverage.csv', ledger, fields)
    save(P / 'pesquisa-status.json', {'phase': 'RS-EST-AD2-CLOSE', 'candidate_count': len(ledger),
        'status_counts': dict(collections.Counter(r['research_status'] for r in ledger)),
        'definitions': LABELS, 'candidates': ledger,
        'note': 'Status descreve cobertura da pesquisa, não a candidatura. Consulta nominal não prova inexistência de propostas. Datas eleitorais continuam no snapshot de 21/09/2026.'})
    save(D / 'normalized.json', data); save(P / 'dados.json', data)
    histories = [(c, h) for c in records for h in c['history'] if h['year'] < 2026]
    missing = []
    for c, h in histories:
        if h.get('votes') is not None:
            continue
        nonapp = str(h.get('votes_status')).startswith('not_applicable')
        missing.append({'candidate_id': c['id'], 'name': c['name'], 'historical_id': h['candidate_id'],
            'year': h['year'], 'round': h['round'], 'office': h['office'],
            'electoral_unit': h.get('electoral_unit'), 'votes': None, 'status': h.get('votes_status'),
            'requires_nominal_research': not nonapp, 'historical_registration_review': h.get('historical_registration_review')})
    save(A / 'historical-vote-pendencies.json', missing)
    csv_file(A / 'historical-vote-pendencies.csv', missing, ['candidate_id', 'name', 'historical_id', 'year', 'round', 'office', 'electoral_unit', 'status', 'requires_nominal_research'])
    soup = BeautifulSoup((P / 'index.html').read_text(encoding='utf-8'), 'html.parser')
    for node in soup.select('[data-close-status],#close-research-method,#close-research-style'):
        node.decompose()
    for c in records:
        article = soup.find(id='candidato-' + c['id'])
        if article is None:
            raise ValueError('Missing rendered candidature')
        status = c['research_status']['status']
        markup = '<details data-close-status="' + status + '" class="close-research-note"><summary>Estado da pesquisa: ' + html.escape(LABELS[status]) + '</summary><p>' + html.escape(NEXT[status]) + ' Este estado descreve a pesquisa, não uma avaliação da candidatura. <a href="pesquisa-status.json">Fontes e pendências individuais</a>.</p></details>'
        (article.select_one('.candidate-copy') or article).append(BeautifulSoup(markup, 'html.parser').details)
    styles = soup.new_tag('style', id='close-research-style')
    styles.string = '.close-research-note{margin-top:14px;font-size:.79rem;line-height:1.5;overflow-wrap:anywhere}.close-research-note summary{cursor:pointer;padding:10px 0;min-height:44px}.close-research-note p{margin:.5em 0 1em}.close-research-note a:focus-visible,.close-research-note summary:focus-visible{outline:3px solid #647b59;outline-offset:3px}'
    soup.head.append(styles)
    method = soup.select_one('#fontes')
    if method:
        method.append(BeautifulSoup('<p id="close-research-method" class="rs-data-links">Fechamento técnico de recuperação: 22/09/2026. O cadastro eleitoral continua referido ao snapshot de 21/09/2026; não houve atualização silenciosa da situação. Todas as fichas possuem <a href="pesquisa-status.json">estado explícito da pesquisa</a>. A revisão final E–F permanece pendente.</p>', 'html.parser'))
    for node in soup.select('script[type="application/ld+json"]'):
        structured = json.loads(node.string)
        structured['dateModified'] = '2026-09-22'
        node.string = json.dumps(structured, ensure_ascii=False).replace('</', '<\\/')
    text = str(soup).replace('viewbox=', 'viewBox=')
    (P / 'index.html').write_text(text, encoding='utf-8')
    checksum = sha(P / 'index.html')
    status_counts = dict(collections.Counter(r['research_status'] for r in ledger))
    for path in (A / 'closure-metrics.json', DOC / 'build-report.json', P / 'cobertura.json'):
        obj = load(path, {})
        obj.update({'current_phase': 'RS-EST-AD2-CLOSE', 'html_sha256': checksum,
            'research_status_count': len(ledger), 'research_status_counts': status_counts,
            'counts': counts(records), 'electoral_snapshot_refreshed': False,
            'evidence_cutoff': '2026-09-21', 'closure_date': '2026-09-22',
            'editorial_research_complete': False, 'E_F_complete': False})
        save(path, obj)
    provenance = load(P / 'fontes.json', {})
    provenance['ad2_close'] = {'research_status_url': 'pesquisa-status.json',
        'recovery_head': RECOVERED_HEAD, 'source_availability': load(A / 'source-availability.json', {}),
        'reviewed_source_checks': reviews.get('verified_restored_sources', []),
        'fresh_electoral_snapshot': False}
    save(P / 'fontes.json', provenance)
    print(json.dumps({'counts': counts(records), 'statuses': status_counts}, ensure_ascii=False))


def final_report():
    records = load(D / 'normalized.json')['candidates']
    current = counts(records); metrics = load(A / 'closure-metrics.json')
    browser = load(DOC / 'browser-qa.json', {})
    tests = (DOC / 'unit-tests.txt').read_text(encoding='utf-8')
    match = re.search(r'Ran (\d+) tests', tests)
    if not match or not tests.rstrip().endswith('OK') or not browser.get('passed'):
        raise ValueError('Full Git-backed unit tests and browser QA must pass without skips')
    repro = load(A / 'reproducibility.json')
    if not repro['byte_identical_stable_exports'] or not repro['frozen_inputs_unchanged']:
        raise ValueError('Frozen-source replay has not passed')
    isolation = []
    if (ROOT / '.git').exists():
        changed = git('diff', '--name-only', RECOVERED_HEAD).splitlines()
        untracked = git('ls-files', '--others', '--exclude-standard').splitlines()
        allowed = ('data/rs-estaduais/', 'docs/rs-estaduais/', 'tools/rs-estaduais/', 'tests/rs-estaduais/', 'rs/deputados-estaduais/', '.github/workflows/rs-estaduais')
        if any(name and not name.startswith(allowed) for name in changed + untracked):
            raise ValueError('Change outside the isolated edition')
        for name in ('index.html', 'deputados-estaduais', 'rs/deputados-federais', 'data/rs', 'tools/rs', 'assets', 'server', 'sitemap.xml', 'config'):
            subprocess.run(['git', 'diff', '--exit-code', RECOVERED_HEAD, '--', name], cwd=ROOT, check=True, capture_output=True)
            isolation.append({'path': name, 'unchanged_against_recovered_head': True})
    else:
        raise ValueError('Final closure requires real Git history, not just an extracted ZIP')
    missing = load(A / 'historical-vote-pendencies.json')
    ledger = load(A / 'candidate-coverage.json')
    party_rows = []
    for entry in load(A / 'scope-reconciliation.json')['by_party']:
        group = [c for c in records if c['party'] == entry['party']]
        party_rows.append({'party': entry['party'], 'candidates': len(group),
            'summaries': sum(bool(c['pautas']) for c in group), 'remaining_summaries': sum(not c['pautas'] for c in group)})
    report = {'task': 'RS-EST-AD2-CLOSE', 'recorded_at': stamp(),
        'status': 'technical_recovery_closed_editorial_gaps_open',
        'recovered_head': RECOVERED_HEAD, 'source_commit': git('rev-parse', 'HEAD'),
        'before_AD': {'candidates': 145, 'policy_summaries': 50, 'current_offices': 15,
            'with_activity': 26, 'historical_vote_rows': 392},
        'recovered_AD2': load(A / 'recovery-audit.json')['recovered_counts'],
        'after_closure': current, 'by_party': party_rows,
        'research_status_counts': metrics['research_status_counts'],
        'every_candidate_has_status': len(ledger) == len(records),
        'historical_nominal_totals_pending': sum(x['requires_nominal_research'] for x in missing),
        'ticket_positions_without_own_nominal_total': sum(not x['requires_nominal_research'] for x in missing),
        'unit_tests': int(match.group(1)), 'unit_tests_skipped': 0,
        'browser_checks': browser['check_count'], 'browser_passed': True,
        'network_free_replays': 2, 'replay_passed': True, 'isolation': isolation,
        'technical_gate': 'passed', 'editorial_gate': 'not_complete',
        'merge_performed': False, 'deployment_performed': False, 'issue_closed': False,
        'E_F_completed': False, 'electoral_snapshot_refreshed': False,
        'electoral_snapshot_generated_at': load(D / 'manifest.json')['snapshot_generated_at'],
        'html_sha256': sha(P / 'index.html'),
        'remaining_scope': ['Pesquisa temática das fichas sem síntese e das pendências de acesso.',
            'Confirmação institucional mais abrangente de mandatos e identificação dos processos ainda não numerados.',
            'Totais históricos ainda sem correspondência segura.',
            'E: auditoria editorial independente. F: nova coleta eleitoral, delta e gate de publicação.']}
    save(A / 'report.json', report)
    save(A / 'isolation.json', {'recovered_head': RECOVERED_HEAD, 'checks': isolation, 'passed': True})
    recovery = load(A / 'recovery-audit.json')
    recovery.update({'reproduced': True, 'external_temporary_inputs_required': False,
        'git_history_checks_passed': True, 'frozen_inputs_unchanged': True})
    save(A / 'recovery-audit.json', recovery)
    delivery = load(DOC / 'delivery-report.json', {})
    delivery.update({'current_phase': 'RS-EST-AD2-CLOSE', 'technical_gate': 'passed',
        'editorial_gate': 'partial_with_explicit_gaps', 'scope_census': current['candidates'],
        'policy_summaries': current['policy_summaries'], 'policy_gaps': current['policy_gaps'],
        'current_offices_confirmed': current['current_offices'], 'documented_acts_candidates': current['with_activity'],
        'past_vote_rows': current['historical_vote_rows'], 'unit_test_count': int(match.group(1)),
        'browser_checks': browser['check_count'], 'close_report': 'ad2-close/report.json',
        'research_status_counts': metrics['research_status_counts'], 'html_sha256': report['html_sha256']})
    save(DOC / 'delivery-report.json', delivery)
    lines = ['# RS-EST-AD2-CLOSE — fechamento de recuperação', '',
        '**Fechamento técnico concluído; pesquisa editorial integral permanece aberta.**', '',
        '## Recuperação e correção dos números', '',
        f'O commit `{RECOVERED_HEAD}` e o artefato {RECOVERED_ARTIFACT["artifact_id"]} contêm 149 candidaturas, 61 sínteses e 395 linhas históricas com votos. As referências anteriores a 71 sínteses e 394 votos não foram reproduzidas. Não se presume a existência de dez sínteses locais ausentes do GitHub.', '',
        'A configuração canônica contém onze siglas, incluindo PCB, PSTU e REDE. PCB e PCO têm zero registros neste snapshot; REDE e PSTU acrescentaram duas candidaturas cada na correção anterior. A configuração compartilhada foi somente lida.', '',
        '## Resultado reproduzido', '',
        f'- {current["candidates"]} candidaturas representadas e conciliadas com o cadastro preservado.',
        f'- {current["policy_summaries"]} sínteses; {current["policy_gaps"]} fichas ainda sem síntese.',
        f'- {current["current_offices"]} mandatos confirmados nas fontes datadas preservadas; {current["with_activity"]} fichas com {current["acts"]} atos documentados.',
        f'- {current["historical_vote_rows"]} votos conferidos em {current["past_history_rows"]} linhas históricas; {report["historical_nominal_totals_pending"]} totais pendentes e {report["ticket_positions_without_own_nominal_total"]} posições de vice/suplência sem voto nominal próprio.', '',
        '## Estado individual da pesquisa', '']
    for status, amount in sorted(metrics['research_status_counts'].items()):
        lines.append(f'- {LABELS[status]}: {amount}.')
    lines += ['', 'Cada candidatura tem status, fontes, tentativas recuperadas e próximo passo. Pendência não virou pesquisa concluída nem ausência de propostas. Link bloqueado identifica dificuldade de acesso, não uma conclusão sobre a pessoa. As buscas nominais anteriores foram preservadas sem alegar exaustividade.', '',
        '## Reprodutibilidade e testes', '',
        f'Duas reconstruções com rede bloqueada produziram os mesmos bytes nos arquivos comparados. {int(match.group(1))} testes unitários passaram sem skips e {browser["check_count"]} verificações de navegador passaram. A verificação com histórico Git foi executada no CI.', '',
        'O controle de fontes registra disponibilidade e hashes sem transformar HTTP 200 em validação de conteúdo. Nenhum corpo integral de campanha ou dado de doador foi copiado para o relatório. As confirmações de mandato preservadas não foram redatadas como novas confirmações.', '',
        '## Isolamento e GitHub', '',
        'Mesma branch `feat/rs-deputados-estaduais`, issue #5 e PR #9. Sem merge, deploy ou encerramento da issue. Nenhuma modificação nesta execução à homepage, SC, RS/federais, navegação global, servidor, sitemap global ou configuração canônica.', '',
        '## Próximos gates', '',
        'E continua sendo a auditoria editorial independente da edição consolidada. F deve coletar novamente TSE/DivulgaCand, produzir o delta e decidir a liberação. A situação eleitoral mostrada pertence ao snapshot de 21/09/2026 às 12:31:37. O fechamento técnico de 22/09/2026 não atualiza silenciosamente esse dado.', '',
        '## Arquivos', '',
        '`recovery-audit.json`, `reproducibility.json`, `scope-reconciliation.json`, `source-availability.json`, `editorial-structure-audit.json`, `candidate-coverage.*`, `historical-vote-pendencies.*`, `isolation.json` e `report.json` documentam o fechamento. O export público de status está em `pesquisa-status.json`.', '']
    text = '\n'.join(lines)
    (A / 'ENTREGA-A-D2.md').write_text(text, encoding='utf-8')
    (DOC / 'ENTREGA-A-D2.md').write_text(text, encoding='utf-8')
    path = DOC / 'SOURCE-REVIEW.md'; content = path.read_text(encoding='utf-8')
    if '## Fechamento de recuperação — 22/09/2026' not in content:
        note = '\n\n## Fechamento de recuperação — 22/09/2026\n\nO relatório atual é `ad2-close/ENTREGA-A-D2.md`. Foram reproduzidas 61 sínteses, não 71, e 395 linhas com votos, não 394. Todos os 149 registros têm estado explícito da pesquisa. E/F e lacunas temáticas permanecem abertos. O cadastro eleitoral não foi atualizado por este fechamento.\n'
        path.write_text(content + note, encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['replay', 'probe', 'publish', 'report'])
    args = parser.parse_args()
    {'replay': replay, 'probe': probe_sources, 'publish': publish_audit, 'report': final_report}[args.stage]()


if __name__ == '__main__':
    main()

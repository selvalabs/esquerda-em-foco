"""Build the SP Round B checkpoint from frozen official and reviewed sources.

Standard library only. Unknowns never become negative political assertions.
Editorial coverage is measured separately from successful technical checks.
"""
from __future__ import annotations
import collections
import copy
import csv
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from urllib.parse import urlsplit

OUT = Path('data/sp/round-b')
DOC = Path('docs/sp/round-b')
AS_OF = '2026-09-21'
ROUND_A = 'b42f2e1f108185c7f9c3d5af7e5e92e893aef574'
POSITIONS = {'supports_measure', 'opposes_measure', 'authorship', 'coauthorship', 'documented_activity', 'statement_only'}
PERIODS = {'dated_2026', 'dated_historical', 'undated'}
MISSING = {'', '#NE', '#NE#', '#NULO', '#NULO#', '-1', '-3', '-4'}
CORE = ['id', 'name', 'official_name', 'full_name', 'number', 'party', 'status', 'registration_election', 'source_record']

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def fold(value):
    return ''.join(x for x in unicodedata.normalize('NFKD', str(value or '')) if not unicodedata.combining(x)).upper().strip()

def meaningful(value):
    return None if value is None or str(value).strip().upper() in MISSING else str(value).strip()

def require(condition, message):
    if not condition:
        raise ValueError(message)

def read_editorial(directory):
    records = {}
    for path in sorted(directory.glob('*.json')):
        document = load(path)
        require(document.get('as_of') == AS_OF, f'Unexpected editorial date: {path}')
        for cid, record in document.get('candidates', {}).items():
            require(cid not in records, f'Duplicate editorial input: {cid}')
            require(cid == record.get('id'), f'Editorial key differs from record id: {cid}')
            records[cid] = record
    return records

def validate_editorial(records, valid_ids, topics):
    for cid, record in records.items():
        require(cid in valid_ids, f'Out-of-scope editorial id: {cid}')
        sources = record.get('sources', [])
        source_ids = {s['id'] for s in sources}
        require(len(source_ids) == len(sources), f'Duplicate source IDs in {cid}')
        for source in sources:
            u = urlsplit(source['url'])
            require(u.scheme in ['https', 'http'] and bool(u.hostname), f'Invalid source URL: {cid}')
            require(bool(source.get('locator')), f'Missing source locator: {cid}')
            require(source.get('read_at') == AS_OF, f'Unexpected source read date: {cid}')
            pub = source.get('publication_date')
            require(not pub or pub <= AS_OF, f'Future publication: {cid}')
        bio = record.get('biography')
        if bio:
            require(bool(bio.get('text')) and bool(bio.get('source_ids')), f'Unsourced biography: {cid}')
            require(set(bio['source_ids']).issubset(source_ids), f'Unknown biography source: {cid}')
            require(record.get('identity_status') != 'needs_confirmation', f'Unresolved biography identity: {cid}')
        for claim in record.get('claims', []):
            require(claim.get('topic_id') in topics, f'Unknown topic in {cid}')
            require(claim.get('source_id') in source_ids, f'Unsourced claim in {cid}')
            require(bool(claim.get('text')), f'Empty claim in {cid}')
            require(claim.get('position') in POSITIONS, f'Unknown attribution/direction in {cid}')
            require(claim.get('temporal') in PERIODS, f'Unknown temporal status in {cid}')
            require(claim.get('current_support_filter_eligible') is False, f'Unreviewed active filter in {cid}')
            require(record.get('identity_status') != 'needs_confirmation', f'Unresolved claim identity: {cid}')
            date = claim.get('event_date')
            if claim['temporal'] == 'dated_2026':
                require(bool(date) and date.startswith('2026') and date <= AS_OF, f'Invalid 2026 event date: {cid}')
            if claim['temporal'] == 'dated_historical':
                require(bool(date) and re.match(r'^\d{4}', date) and int(date[:4]) < 2026, f'Invalid historical date: {cid}')
        office = record.get('office')
        if office:
            require(office.get('source_id') in source_ids, f'Unsourced current-office observation: {cid}')
            require(office.get('checked_at') == AS_OF, f'Stale current-office observation: {cid}')

def normalize_history(rows, metadata):
    groups = collections.defaultdict(list)
    seen = set()
    current_rows = 0
    for row in rows:
        year = int(row['ANO_ELEICAO'])
        if year >= 2026:
            current_rows += 1
            continue
        cid = row['SQ_CANDIDATO_ATUAL']
        key = (cid, year, row['NR_TURNO'], row['CD_ELEICAO'], row['SQ_CANDIDATO'])
        require(key not in seen, f'Duplicate history identity: {key}')
        seen.add(key)
        groups[cid].append({
            'year': year, 'round': int(row['NR_TURNO']), 'candidate_id': row['SQ_CANDIDATO'],
            'election_id': row['CD_ELEICAO'], 'office': row['DS_CARGO'], 'place': row['NM_UE'],
            'uf': row['SG_UF'], 'party': row['SG_PARTIDO'], 'result': meaningful(row['DS_SIT_TOT_TURNO']),
            'votes': None, 'votes_status': 'not_collected_in_round_b',
            'source': metadata['url'], 'source_record': {
                'member': metadata['member'], 'member_sha256': metadata['member_sha256'],
                'csv_record': row['_csv_record'], 'generated_at': row['DT_GERACAO'] + ' ' + row['HH_GERACAO'],
                'retrieved_at': metadata['retrieved_at']}})
    for history in groups.values():
        history.sort(key=lambda h: (h['year'], h['round'], h['election_id'], h['candidate_id']), reverse=True)
    return groups, current_rows

def link_kind(url):
    host = (urlsplit(url).hostname or '').lower().removeprefix('www.')
    platforms = {'instagram.com': 'Instagram', 'facebook.com': 'Facebook', 'fb.com': 'Facebook',
                 'x.com': 'X', 'twitter.com': 'X', 'youtube.com': 'YouTube', 'youtu.be': 'YouTube',
                 'tiktok.com': 'TikTok', 'linkedin.com': 'LinkedIn', 'threads.net': 'Threads',
                 'threads.com': 'Threads', 'wa.me': 'WhatsApp', 'api.whatsapp.com': 'WhatsApp',
                 't.me': 'Telegram'}
    return platforms.get(host), host

def audit_dataset(document, original, evidence, sources, topics):
    old = {c['id']: c for c in original['candidates']}
    candidates = document['candidates']
    require(len(candidates) == len(old), 'Candidate count differs from Round A')
    require({c['id'] for c in candidates} == set(old), 'Candidate universe differs from Round A')
    require(len({c['id'] for c in candidates}) == len(candidates), 'Duplicate candidate IDs')
    source_ids = {s['id'] for s in sources}
    ev_ids = {e['id'] for e in evidence}
    require(len(ev_ids) == len(evidence), 'Duplicate evidence IDs')
    for e in evidence:
        require(e['candidate_id'] in old and e['topic_id'] in topics and e['source_id'] in source_ids, 'Broken evidence relation')
    for c in candidates:
        for key in CORE:
            require(c[key] == old[c['id']][key], f'Round A field mutated: {c["id"]}/{key}')
        require(c['registration_election']['votes'] is None and c['registration_election']['result'] is None, '2026 results invented')
        require(all(h['year'] < 2026 for h in c['history']), 'Current election mixed into historical results')
        require(all(h['votes'] is None for h in c['history']), 'Historical votes invented')
        require(not c['pauta_ids'], 'Product filters must remain inactive')
        actual = [e for e in evidence if e['candidate_id'] == c['id']]
        require(set(c['evidence_ids']) == {e['id'] for e in actual}, 'Candidate/evidence mismatch')
        require(set(c['documented_topic_ids']) == {e['topic_id'] for e in actual}, 'Unsubstantiated documentary topic')
    return True

def main():
    base_path = Path('data/sp/normalized.json')
    raw = base_path.read_bytes()
    base = json.loads(raw)
    collection = load(OUT / 'collection.json')
    require(digest(raw) == collection['round_a_sha256'], 'Round A bytes changed')
    taxonomy = load(OUT / 'taxonomy.json')
    topics = {t['id'] for t in taxonomy['topics']}
    records = read_editorial(OUT / 'inputs')
    valid_ids = {c['id'] for c in base['candidates']}
    require(len(valid_ids) == 234, 'Unexpected locked universe')
    validate_editorial(records, valid_ids, topics)
    targets = {r['id']: r for r in load(OUT / 'research-targets.json')}
    histories, current_rows = normalize_history(load(OUT / 'history-official.json'), collection['sources']['history'])
    profiles = load(OUT / 'divulgacand-profiles.json')
    photos = load(OUT / 'photos.json')
    supplement = load(OUT / 'supplement.json')
    all_sources = []
    all_evidence = []
    output = copy.deepcopy(base)
    output.update(stage='round_b_checkpoint', round_a_commit=ROUND_A, editorial_as_of=AS_OF,
                  taxonomy_version=taxonomy['version'], product_filters_enabled=False)
    queue = []
    status_differences = []
    for c in output['candidates']:
        cid = c['id']; target = targets[cid]; review = records.get(cid)
        profile = profiles.get(cid, {})
        require(profile.get('identity_verified') is True, f'Official profile identity unverified: {cid}')
        require(str(profile.get('numero')) == c['number'], f'Official candidate number mismatch: {cid}')
        require(fold(profile.get('nomeCompleto')) == fold(c['full_name']), f'Official civil-name mismatch: {cid}')
        if fold(profile.get('descricaoSituacao')) != fold(c['status']):
            status_differences.append({'id': cid, 'round_a_status': c['status'], 'divulgacand_status': profile.get('descricaoSituacao'),
                                       'resolution': 'both_source_strings_preserved_no_change_to_round_a', 'profile_source': profile['source']})
        c['history'] = histories.get(cid, [])
        c['photo'] = photos.get(cid)
        if c['photo']:
            require(digest(Path(c['photo']['path']).read_bytes()) == c['photo']['sha256'], f'Photo hash mismatch: {cid}')
        c['socials'] = []; c['sites'] = []
        for link in target['links']:
            platform, host = link_kind(link['url'])
            destination = c['socials'] if platform else c['sites']
            destination.append({**link, 'label': platform or host, 'link_status': 'syntax_checked_not_individually_http_verified'})
        c['invalid_declared_urls'] = target['invalid_declared_urls']
        c['official_profile_verification'] = {'identity_verified': True, 'source': profile['source'], 'source_name': profile.get('nomeUrna'), 'source_status': profile.get('descricaoSituacao')}
        c['biography'] = None; c['current_office'] = None; c['pautas'] = None; c['pauta_ids'] = []
        c['documented_topic_ids'] = []; c['evidence_ids'] = []; c['editorial_sources'] = []
        c['editorial_review'] = copy.deepcopy(review) if review else {'id': cid, 'status': 'not_reviewed', 'search_queries': [], 'notes': []}
        if review:
            local_sources = {}
            for source in review['sources']:
                sid = 'src-' + digest((cid + ':' + source['id']).encode())[:20]
                local_sources[source['id']] = sid
                item = {**source, 'id': sid, 'local_source_id': source['id'], 'candidate_id': cid}
                all_sources.append(item); c['editorial_sources'].append(item)
            if review.get('biography'):
                c['biography'] = review['biography']['text']
                c['biography_evidence'] = {**review['biography'], 'source_ids': [local_sources[s] for s in review['biography']['source_ids']]}
            if review.get('office'):
                c['current_office'] = copy.deepcopy(review['office'])
                c['current_office']['source_id'] = local_sources[review['office']['source_id']]
            for claim in review.get('claims', []):
                ev = {**claim, 'candidate_id': cid, 'source_id': local_sources[claim['source_id']], 'reviewed_at': review['reviewed_at']}
                ev['id'] = 'ev-' + digest(json.dumps(ev, ensure_ascii=False, sort_keys=True).encode())[:24]
                all_evidence.append(ev); c['evidence_ids'].append(ev['id'])
            c['documented_topic_ids'] = sorted({x['topic_id'] for x in review.get('claims', [])})
            c['editorial_checked_at'] = review['reviewed_at']
        c['research_status'] = {
            'official_identity': 'verified_against_individual_tse_api',
            'biography': 'source_reviewed' if c['biography'] else 'identity_pending' if review and review.get('identity_status') == 'needs_confirmation' else 'no_accepted_biography_in_limited_review' if review else 'not_reviewed',
            'pautas': 'some_evidence_reviewed_not_exhaustive' if c['evidence_ids'] else 'no_accepted_evidence_in_limited_review' if review else 'not_reviewed',
            'history': 'prior_records_located_in_tse_export' if c['history'] else 'no_prior_record_in_this_tse_export',
            'historical_votes': 'not_collected',
            'current_office': 'institutional_observation_reviewed' if c['current_office'] else 'not_verified',
            'socials': 'declared_urls_collected' if c['socials'] or c['sites'] else 'none_in_examined_declarations',
            'photo': 'official_id_and_hash_verified' if c['photo'] else 'not_located',
            'municipality': 'not_inferred_from_birthplace_or_historical_district'}
        pending = []
        if not review: pending.append('individual_editorial_research_not_started')
        if not c['biography']: pending.append('biography_not_accepted')
        if not c['evidence_ids']: pending.append('no_accepted_topic_evidence')
        if review: pending.append('deepen_and_reconcile_non_exhaustive_review')
        if not c['current_office']: pending.append('current_public_role_not_verified')
        pending.extend(['individual_social_link_check', 'historical_votes_not_collected'])
        queue.append({'id': cid, 'name': c['name'], 'party': c['party'], 'review_status': c['editorial_review']['status'], 'biography': bool(c['biography']), 'evidence_count': len(c['evidence_ids']), 'pending': pending})
    audit_dataset(output, base, all_evidence, all_sources, topics)
    reviewed = sum(bool(c['editorial_sources']) for c in output['candidates'])
    counts = {
        'candidate_records': len(valid_ids), 'official_profiles_verified': len(profiles), 'official_photos': len(photos),
        'social_declaration_candidates': collection['coverage']['social_candidates'],
        'prior_election_candidates': len(histories), 'prior_election_records': sum(len(h) for h in histories.values()),
        'current_year_rows_excluded_from_history': current_rows,
        'individual_research_entries': len(records), 'candidates_with_reviewed_editorial_sources': reviewed,
        'candidates_with_biography': sum(bool(c['biography']) for c in output['candidates']),
        'candidates_with_topic_evidence': sum(bool(c['evidence_ids']) for c in output['candidates']),
        'topic_evidence_records': len(all_evidence), 'reviewed_source_records': len(all_sources),
        'unique_reviewed_urls': len({s['url'] for s in all_sources}),
        'candidates_without_individual_editorial_review': len(valid_ids) - len(records),
        'current_role_observations_reviewed': sum(bool(c['current_office']) for c in output['candidates']),
        'documentary_topics': len(topics), 'active_product_topic_assignments': 0}
    batches = []
    order = sorted(output['candidates'], key=lambda c: (fold(c['party']), fold(c['name']), c['id']))
    for start in range(0, len(order), 25):
        batch = order[start:start+25]
        batches.append({'batch': len(batches)+1, 'candidate_ids': [c['id'] for c in batch], 'count': len(batch),
                        'with_individual_research_entry': sum(c['id'] in records for c in batch),
                        'with_biography': sum(bool(c['biography']) for c in batch),
                        'with_topic_evidence': sum(bool(c['evidence_ids']) for c in batch),
                        'editorial_gate': 'PARTIAL'})
    by_party = {}
    for party in base['scope_parties']:
        group = [c for c in output['candidates'] if c['party'] == party]
        by_party[party] = {'records': len(group), 'individual_research_entries': sum(c['id'] in records for c in group),
                           'biographies': sum(bool(c['biography']) for c in group), 'with_topic_evidence': sum(bool(c['evidence_ids']) for c in group)}
    report = {'technical_gate': 'PASS', 'editorial_gate': 'PARTIAL', 'publication_gate': 'NOT_READY',
              'as_of': AS_OF, 'counts': counts, 'by_party': by_party, 'batches': batches,
              'round_a_sha256_unchanged': digest(raw), 'round_a_commit': ROUND_A,
              'status_string_differences': status_differences,
              'source_failures': {'initial_collection': collection['errors'], 'supplementary_attempts': supplement['attempts']},
              'limitations': ['Technical PASS is not editorial completion.', 'Reviewed sources are not an exhaustive record of anyone’s positions.',
                  'No accepted topic evidence is not opposition to the topic.', 'Prior election results do not establish current exercise of office.',
                  'Social links are candidate declarations, not individual HTTP verifications.', 'Historical vote totals were not collected.',
                  'Câmara API timed out even after retry; observations from public pages are separately attributed.',
                  'Taxonomy is fixed for documentary research; no filters or changes in other states were activated.',
                  'One official status wording differs between the export and profile; both strings are preserved without silently redefining it.']}
    dump(OUT/'normalized.json', output); dump(OUT/'evidence.json', all_evidence); dump(OUT/'sources.json', all_sources)
    dump(OUT/'research-queue.json', queue); dump(DOC/'audit.json', report)
    schema = {'$schema': 'https://json-schema.org/draft/2020-12/schema', 'type': 'object',
              'required': ['state','office_code','election_year','candidates','product_filters_enabled'],
              'properties': {'state': {'const':'SP'}, 'office_code': {'const':6}, 'election_year': {'const':2026},
                  'product_filters_enabled': {'const':False}, 'candidates': {'type':'array', 'minItems':234, 'maxItems':234,
                      'items': {'type':'object', 'required': CORE+['evidence_ids','documented_topic_ids','research_status'],
                          'properties': {'id': {'type':'string','pattern':'^[0-9]+$'}, 'pauta_ids': {'type':'array','maxItems':0},
                              'evidence_ids': {'type':'array','items':{'type':'string'}}, 'biography': {'type':['string','null']}}}}}}
    dump(OUT/'schema.json', schema)
    with (OUT/'coverage.csv').open('w', encoding='utf-8-sig', newline='') as h:
        writer=csv.DictWriter(h,fieldnames=['id','name','party','review_status','biography','evidence_count','pending'],delimiter=';')
        writer.writeheader()
        for q in queue: writer.writerow({**q,'pending':' | '.join(q['pending'])})
    text = ['# SP federais — Round B: checkpoint documental', '', '**Validação técnica: PASS. Revisão editorial: PARCIAL. Publicação: NÃO LIBERADA.**', '',
            'Esta entrega não encerra a pesquisa individual dos 234 registros. Coleta oficial, identidade, conteúdo revisado e pendências são contabilizados separadamente.', '',
            '## Cobertura', '']
    text += [f'- {key}: **{value}**.' for key,value in counts.items()]
    text += ['', '## Cobertura por partido', '', '| Sigla | Registros | Entradas de pesquisa | Biografias | Com evidência temática |', '|---|---:|---:|---:|---:|']
    text += [f'| {p} | {v["records"]} | {v["individual_research_entries"]} | {v["biographies"]} | {v["with_topic_evidence"]} |' for p,v in by_party.items()]
    text += ['', 'As diferenças de cobertura são lacunas de pesquisa, não avaliações de candidaturas. A ordem é a do recorte do projeto, não de preferência política.', '',
        '## Proveniência e interpretação', '',
        'Os 234 registros continuam sendo os do Round A. Nenhum foi removido por renúncia ou julgamento. O histórico separa eleições anteriores de linhas do próprio pleito de 2026. Votos históricos ausentes não são zero. A identidade foi conferida no DivulgaCand por ID e nome civil; o número também foi comparado no build.', '',
        'Cada evidência temática registra candidato, tema, medida, autoria/declaração, direção, temporalidade e fonte. Menção a tema não implica apoio a toda medida associada. Conteúdo sem data não ganhou uma data de publicação inventada. As associações documentais não foram ativadas como filtros de apoio atual.', '',
        'A proposta de SC foi fixada como versão documental reutilizável, com Saúde separada de apoio específico ao SUS. Nenhum arquivo de taxonomia ou associação de SC/RS/PR foi alterado. O erro inicial de parser do DivulgaCand foi corrigido e a verificação individual repetida; o arquivo de tentativas anteriores foi preservado.', '',
        'Uma formulação de situação difere entre o extrato e o perfil: o extrato abrange prazo recursal ou recurso, enquanto o perfil usa uma descrição mais curta. Ambos os textos estão disponíveis em audit.json e nos dados, sem alteração retroativa da fotografia A.', '',
        '## Pendências de encerramento', '',
        'research-queue.json e coverage.csv identificam cada candidato e cada lacuna. Ainda é necessário concluir as pesquisas individuais pendentes, aprofundar as fichas parciais, confirmar cargos atuais não verificados e conferir links sociais individualmente. A API da Câmara não respondeu no runner após tentativas registradas; fatos obtidos no portal público foram atribuídos à fonte específica.', '',
        '## Arquivos', '',
        '`normalized.json`: base enriquecida; `sources.json`: fontes editoriais; `evidence.json`: relações documentadas; `research-queue.json`: fila nominal; `audit.json`: testes e contagens; `taxonomy.json`: contrato documental; `inputs/`: pesquisa revisada versionada.', '',
        'As fontes oficiais e seus hashes ficam em collection.json e supplement.json. As fontes individuais, com URLs e localizadores, ficam em sources.json. Não houve frontend, merge ou deploy.', '']
    (DOC/'REPORT.md').write_text('\n'.join(text), encoding='utf-8')
    inventory = {str(p):digest(p.read_bytes()) for root in [OUT,DOC] for p in sorted(root.rglob('*'))
                 if p.is_file() and p.name not in ['checksums.json','unit-tests.txt'] and p.suffix != '.log'}
    dump(DOC/'checksums.json', inventory)
    require(base_path.read_bytes() == raw, 'Round A was overwritten')
    print(json.dumps({'technical_gate':'PASS','editorial_gate':'PARTIAL','counts':counts},ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()

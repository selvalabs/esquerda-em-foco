"""Compilador determinístico de decisões humanas para a matriz de pautas v1.
Não pesquisa palavras, não pontua pessoas e não ativa filtros na interface.
"""
from __future__ import annotations
from collections import Counter
import hashlib
import json
from pathlib import Path
import unicodedata

OUT = Path('data/sc-federais-topics-v1')
REVIEW = Path('data/sc-federais-pautas/review.json')
CONFIG = Path('config/topics-v1.json')
DECISIONS = OUT / 'decisions.json'
DIRECTIONS = {'apoio', 'prioridade', 'oposicao', 'debate', 'atuacao_documentada', 'autodefinicao'}


def load(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def sha(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alpha(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def eligibility(coverage, period, claim_eligible, direction):
    blocked = []
    if coverage == 'material_conjunto':
        blocked.append('atribuicao_conjunta_pendente')
    if period == 'sem_data':
        blocked.append('sem_data')
    elif period != '2026':
        blocked.append('historico')
    if claim_eligible is False:
        blocked.append('afirmacao_excluida_do_filtro_na_revisao')
    position = not blocked
    support = position and direction in ('apoio', 'prioridade')
    support_reasons = list(blocked)
    if direction not in ('apoio', 'prioridade'):
        support_reasons.append('direcao_nao_equivale_a_apoio_ou_prioridade')
    return position, support, blocked, support_reasons


def run():
    taxonomy = load(CONFIG)
    review = load(REVIEW)
    decisions = load(DECISIONS)['candidates']
    topics = {t['id']: t for t in taxonomy['topics']}
    legacy = {t['legacy_label']: t['id'] for t in taxonomy['topics']}
    assert len(topics) == len(legacy) == 29
    assert all(t.get('includes') and t.get('excludes') for t in topics.values())
    records = review['candidates']
    assert len(records) == len({r['id'] for r in records}) == 48
    assert set(decisions) == {r['id'] for r in records if r['claims']}
    associations, candidates, source_registry = [], [], {}
    for record in sorted(records, key=lambda r: alpha(r['name'])):
        cid = record['id']
        authored = decisions.get(cid, {})
        assert set(authored) == {str(i + 1) for i in range(len(record['claims']))}, cid
        for source in record['sources']:
            source_registry[source['source_id']] = {
                **source, 'candidate_id': cid,
                'provenance': 'data/sc-federais-pautas/review.json',
                'verification_scope': 'fonte_da_revisao_editorial_21_09_2026'
            }
        own = []
        for n, claim in enumerate(record['claims'], start=1):
            entries = authored[str(n)]
            assert set(entries) == {legacy[label] for label in claim['themes']}, (cid, n, 'tema não revisado')
            for topic_id, values in sorted(entries.items()):
                assert len(values) in (3, 4)
                direction, target, indices = values[:3]
                period = values[3] if len(values) == 4 else claim['period']
                assert direction in DIRECTIONS and target and indices
                assert set(indices).issubset(set(claim['sources'])), (cid, n, indices)
                assert len(indices) == len(set(indices))
                sources = [record['sources'][i] for i in indices]
                assert all(s['period'] == period for s in sources), (cid, n, period)
                position, support, blocked, support_reasons = eligibility(record['coverage'], period, claim.get('filter_eligible'), direction)
                row = {
                    'association_id': f'{cid}-c{n}--{topic_id}',
                    'candidate_id': cid, 'topic_id': topic_id, 'claim_id': claim['claim_id'],
                    'claim_text': claim['text'], 'direction': direction, 'position_target': target,
                    'period': period,
                    'period_basis': 'publication_date' if all(s.get('published_at') for s in sources) else ('undated' if period == 'sem_data' else 'context_documented_in_review'),
                    'source_ids': [s['source_id'] for s in sources],
                    'attribution': 'joint_pending' if record['coverage'] == 'material_conjunto' else 'individual_or_identified_electoral_collective',
                    'eligible_current_position': position, 'eligible_current_support': support,
                    'position_exclusion_reasons': blocked, 'support_exclusion_reasons': support_reasons,
                    'reviewed_at': '2026-09-21', 'taxonomy_version': taxonomy['taxonomy_version'],
                    'decision_source': 'data/sc-federais-topics-v1/decisions.json'
                }
                associations.append(row)
                own.append(row)
        candidates.append({
            'candidate_id': cid, 'name': record['name'], 'party': record['party'], 'anchor': record['anchor'],
            'coverage': record['coverage'], 'coverage_label': record['coverage_label'],
            'association_ids': [a['association_id'] for a in own],
            'documented_topic_ids': sorted({a['topic_id'] for a in own}),
            'current_position_topic_ids': sorted({a['topic_id'] for a in own if a['eligible_current_position']}),
            'current_support_topic_ids': sorted({a['topic_id'] for a in own if a['eligible_current_support']}),
            'limitations': record['limitations'],
            'empty_means': 'Associação não documentada neste recorte; não implica oposição nem ausência de pauta.'
        })
    assert len({a['association_id'] for a in associations}) == len(associations)
    assert len({a['claim_id'] for a in associations}) == 52
    assert all(set(a['source_ids']).issubset(source_registry) for a in associations)
    stats = {
        'candidate_records': len(candidates),
        'candidates_with_documented_claim': sum(bool(c['association_ids']) for c in candidates),
        'candidates_without_documented_claim': sum(not c['association_ids'] for c in candidates),
        'candidates_with_2026_individual_position': sum(bool(c['current_position_topic_ids']) for c in candidates),
        'candidates_with_2026_explicit_support_or_priority': sum(bool(c['current_support_topic_ids']) for c in candidates),
        'claim_groups': len({a['claim_id'] for a in associations}),
        'associations': len(associations), 'sources': len(source_registry), 'topics': len(topics),
        'eligible_current_position_associations': sum(a['eligible_current_position'] for a in associations),
        'eligible_current_support_associations': sum(a['eligible_current_support'] for a in associations),
        'directions': dict(sorted(Counter(a['direction'] for a in associations).items()))
    }
    matrix = {
        'schema_version': '1.0.0', 'taxonomy_version': taxonomy['taxonomy_version'],
        'reviewed_at': '2026-09-21', 'evidence_window': '2026; referências históricas e sem data são mantidas, mas não habilitadas como posição atual.',
        'filters_active': False, 'rules_source': 'config/topics-v1.json',
        'inputs_sha256': {str(p): sha(p) for p in (CONFIG, REVIEW, DECISIONS)},
        'stats': stats, 'candidates': candidates, 'associations': associations,
        'sources': list(source_registry.values()),
        'warning': 'Família temática não é apoio indiscriminado às medidas que abrange. Não pontuar nem ordenar candidaturas por número de associações.'
    }
    dump(OUT / 'matrix.json', matrix)
    coverage = []
    for topic in sorted(topics.values(), key=lambda t: alpha(t['label'])):
        rows = [a for a in associations if a['topic_id'] == topic['id']]
        coverage.append({'topic_id': topic['id'], 'label': topic['label'],
            'documented_candidate_ids': sorted({a['candidate_id'] for a in rows}),
            'current_position_candidate_ids': sorted({a['candidate_id'] for a in rows if a['eligible_current_position']}),
            'current_support_candidate_ids': sorted({a['candidate_id'] for a in rows if a['eligible_current_support']})})
    dump(OUT / 'coverage.json', {'stats': stats, 'topics': coverage, 'filters_active': False})
    lines = ['# SC Federais — matriz temática v1', '',
        'Recorte documental de 21/09/2026. Não é recenso eleitoral nem avaliação de candidaturas.', '',
        f"{stats['candidate_records']} fichas; {stats['candidates_with_documented_claim']} com alguma evidência; {stats['candidates_without_documented_claim']} com lacuna documental.",
        f"{stats['associations']} associações revisadas, {stats['claim_groups']} grupos de afirmações, {stats['sources']} fontes e {stats['topics']} famílias.",
        f"{stats['candidates_with_2026_individual_position']} fichas contêm posições individuais situadas em 2026; {stats['candidates_with_2026_explicit_support_or_priority']} possuem ao menos um apoio ou prioridade explícitos elegíveis no recorte.", '',
        'A diferença entre esses dois últimos números decorre da distinção entre apoio, oposição, debate e atuação. Não representa mérito ou qualidade.', '',
        '| Família | Alguma evidência | Posição individual em 2026 | Apoio/prioridade explícitos em 2026 |', '|---|---:|---:|---:|']
    for item in coverage:
        lines.append(f"| {item['label']} | {len(item['documented_candidate_ids'])} | {len(item['current_position_candidate_ids'])} | {len(item['current_support_candidate_ids'])} |")
    lines += ['', '## Rastreabilidade', '',
        'Matriz: `data/sc-federais-topics-v1/matrix.json`. Cada associação aponta para uma afirmação identificada e apenas para as fontes correspondentes. Texto anterior, sínteses e limitações continuam na revisão original.', '',
        'Regras: `config/topics-v1.json`. Decisões explícitas: `data/sc-federais-topics-v1/decisions.json`. As colunas são conjuntos que se sobrepõem; não devem ser somadas.', '',
        'O índice eleitoral, os números de urna, as fotos e a ordenação diária não são modificados. Nenhum filtro visual está ativo.', '']
    Path('docs/SC-FEDERAIS-TOPICS-V1.md').write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == '__main__':
    run()

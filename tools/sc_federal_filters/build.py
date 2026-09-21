"""Compila somente a interface SC/Federais; não pesquisa nem reclassifica pautas.
Execute na raiz: python tools/sc_federal_filters/build.py
A reaplicação é idempotente e pode ser revertida para comparação byte a byte.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / 'data/sc-federais-topics-v1/matrix.json'
TAXONOMY = ROOT / 'config/topics-v1.json'
OUT = ROOT / 'data/sc-federais-filters-v1'
OLD_SENTENCE = 'A taxonomia para os futuros filtros continua em revisão e nenhum filtro por pauta foi ativado nesta etapa.'
NEW_SENTENCE = 'Os filtros usam associações revisadas entre pautas e fontes. O bloco “Como funcionam os filtros de pautas” explica quais registros entram na seleção.'
SEARCH_ADAPTER = '''    /* eef-filters:search:start */
    if (window.EEFTopicFilters) { window.EEFTopicFilters.apply(); return; }
    /* eef-filters:search:end */
'''


def dump(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def alpha(value: str) -> str:
    return ''.join(ch for ch in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(ch))


def block(name: str, body: str) -> str:
    return f'<!-- eef-filters:{name}:start -->\n{body}\n<!-- eef-filters:{name}:end -->'


def strip_integration(text: str) -> str:
    text = re.sub(r'<!-- eef-filters:([a-z-]+):start -->[\s\S]*?<!-- eef-filters:\1:end -->', '', text)
    return text.replace(SEARCH_ADAPTER, '').replace(NEW_SENTENCE, OLD_SENTENCE)


def payload() -> tuple[dict, dict]:
    matrix = json.loads(MATRIX.read_text(encoding='utf-8'))
    taxonomy = json.loads(TAXONOMY.read_text(encoding='utf-8'))
    assert matrix['taxonomy_version'] == taxonomy['taxonomy_version'] == '1.0.0'
    topics = {topic['id']: topic for topic in taxonomy['topics']}
    sources = {source['source_id']: source for source in matrix['sources']}
    grouped = defaultdict(list)
    for association in matrix['associations']:
        if not association['eligible_current_support']:
            continue
        assert association['direction'] in ('apoio', 'prioridade')
        assert association['period'] == '2026' and not association['support_exclusion_reasons']
        assert association['topic_id'] in topics and association['position_target']
        for sid in association['source_ids']:
            source = sources[sid]
            assert source['candidate_id'] == association['candidate_id']
            parsed = urlsplit(source['url'])
            assert parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password
        grouped[association['candidate_id']].append({
            'associationId': association['association_id'],
            'topicId': association['topic_id'],
            'claimId': association['claim_id'],
            'direction': association['direction'],
            'target': association['position_target'],
            'period': association['period'],
            'sourceIds': association['source_ids']
        })
    candidates = []
    for candidate in matrix['candidates']:
        matches = grouped[candidate['candidate_id']]
        ids = sorted({match['topicId'] for match in matches})
        assert ids == sorted(candidate['current_support_topic_ids'])
        candidates.append({'id': candidate['candidate_id'], 'topicIds': ids, 'matches': matches})
    assert len(candidates) == 48 and len({c['id'] for c in candidates}) == 48
    used_sources = {sid for c in candidates for match in c['matches'] for sid in match['sourceIds']}
    eligible_topics = []
    for topic in sorted(topics.values(), key=lambda t: alpha(t['label'])):
        count = sum(topic['id'] in candidate['topicIds'] for candidate in candidates)
        if count:
            eligible_topics.append({'id': topic['id'], 'label': topic['label'], 'count': count, 'includes': topic['includes'], 'excludes': topic['excludes']})
    result = {
        'schemaVersion': '1.0.0', 'taxonomyVersion': taxonomy['taxonomy_version'],
        'edition': 'sc-federais', 'reviewedAt': matrix['reviewed_at'],
        'eligibility': 'eligible_current_support', 'countScope': 'total_edition_unconditioned',
        'topics': eligible_topics, 'candidates': candidates,
        'sources': {sid: {'url': sources[sid]['url'], 'title': sources[sid]['title']} for sid in sorted(used_sources)}
    }
    manifest = {
        'edition': 'sc-federais', 'filters_active': True, 'taxonomy_version': taxonomy['taxonomy_version'],
        'reviewed_at': matrix['reviewed_at'], 'candidate_count': len(candidates),
        'eligible_candidates': sum(bool(c['matches']) for c in candidates),
        'catalog_topics': len(topics), 'visible_topics': len(eligible_topics),
        'eligible_associations': sum(len(c['matches']) for c in candidates),
        'policy': 'eligible_current_support; apoio ou prioridade individual documentados em 2026',
        'counts': {t['id']: t['count'] for t in eligible_topics},
        'not_displayed_zero_support_topics': sorted(set(topics) - {t['id'] for t in eligible_topics}),
        'source_sha256': {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in (MATRIX, TAXONOMY)},
        'no_tracking': 'Seleções em memória; sem cookies, localStorage, querystring ou envio de pautas à API de métricas.',
        'source_flags_note': 'filters_active=false nos arquivos do Round 1 descreve aquela entrega documental. Esta configuração habilita somente a interface SC/Federais.'
    }
    return result, manifest


def render_panel(data: dict, manifest: dict) -> str:
    chips = []
    for topic in data['topics']:
        label = escape(topic['label'])
        aria = escape(f"{topic['label']}: {topic['count']} candidaturas no total de SC", quote=True)
        title = escape(topic['includes'] + ' ' + topic['excludes'], quote=True)
        chips.append(f'<button type="button" class="pauta-chip" data-pauta-topic="{topic["id"]}" aria-pressed="false" aria-label="{aria}" title="{title}"><span class="pauta-chip__label">{label}</span><span class="pauta-chip__count" aria-hidden="true">{topic["count"]}</span></button>')
    return f'''<section class="pauta-panel" id="pautaPanel" aria-labelledby="pautaPanelTitle" hidden>
<h2 class="pauta-panel__title" id="pautaPanelTitle">Filtrar por pautas</h2>
<p class="pauta-panel__intro">Apoios e prioridades documentados em 2026. Veja no resultado o que cada candidatura defende.</p>
<fieldset class="pauta-mode"><legend>Ao marcar várias pautas</legend><div class="pauta-mode__options">
<label><input type="radio" name="pauta-mode" value="any" checked> Pelo menos uma</label>
<label><input type="radio" name="pauta-mode" value="all"> Todas</label>
</div></fieldset>
<p class="pauta-panel__counts">Os números são do total de SC, sem considerar a busca ou as pautas selecionadas.</p>
<div class="pauta-list" role="group" aria-label="Pautas disponíveis">{''.join(chips)}</div>
<span class="pauta-panel__selection" data-pauta-selection>Nenhuma pauta selecionada</span>
<button class="pauta-clear" type="button" data-pauta-clear disabled>Limpar pautas</button>
<p class="pauta-panel__note">{manifest['eligible_candidates']} de {manifest['candidate_count']} fichas têm apoios ou prioridades que atendem a este recorte. Sem tag não significa sem proposta. <a href="#metodo-filtros">Entenda os filtros</a>.</p>
</section>'''


def build() -> dict:
    data, manifest = payload()
    path = ROOT / 'index.html'
    text = strip_integration(path.read_text(encoding='utf-8'))
    original = text
    soup = BeautifulSoup(text, 'html.parser')
    assert {c.get('data-tse-id') for c in soup.select('article.candidate')} == {c['id'] for c in data['candidates']}
    assert len(soup.select('.party-nav')) == 1
    assert text.count('  function applySearch() {\n') == 1
    assert text.count(OLD_SENTENCE) == 1
    assert not soup.select('[data-pauta-topic]')
    text = text.replace('  function applySearch() {\n', '  function applySearch() {\n' + SEARCH_ADAPTER, 1)
    assets = '\n'.join([
        '<link rel="stylesheet" href="assets/pauta-filters.css?v=1"/>',
        '<script defer src="assets/pauta-filter-core.js?v=1"></script>',
        '<script defer src="assets/sc-federais-filters-data.js?v=1"></script>',
        '<script defer src="assets/pauta-filters.js?v=1"></script>'
    ])
    text = text.replace('</head>', block('assets', assets) + '</head>', 1)
    panel = '<div id="pautaSidebarHost" class="pauta-sidebar-host">' + render_panel(data, manifest) + '</div>'
    text, n = re.subn(r'(<nav class="party-nav"[\s\S]*?</nav>)', lambda m: m.group(1) + block('sidebar', panel), text, count=1)
    assert n == 1
    toolbar = '''<div class="pauta-toolbar" id="pautaToolbar" hidden>
<button type="button" class="pauta-open" id="pautaOpen" aria-haspopup="dialog" aria-controls="pautaDialog" aria-expanded="false"><svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M3 6h18M6 12h12M9 18h6"/></svg><span id="pautaOpenLabel">Pautas · Filtrar</span></button>
<div id="pautaInline"></div>
<div class="pauta-active" id="pautaActive" hidden><span class="pauta-active__label">Pautas selecionadas</span><div class="pauta-active__list" id="pautaActiveList"></div><button type="button" class="pauta-clear" data-pauta-reset="topics">Limpar pautas</button><span class="pauta-active__mode" id="pautaActiveMode"></span></div>
<p class="pauta-notice" id="pautaNotice" role="status" hidden></p>
</div>'''
    main = '<main class="layout" id="candidaturas">'
    assert text.count(main) == 1
    text = text.replace(main, block('toolbar', toolbar) + main, 1)
    empty = '''<section class="pauta-empty" id="pautaEmpty" hidden aria-labelledby="pautaEmptyTitle"><h2 id="pautaEmptyTitle">Nenhuma candidatura corresponde a esta seleção.</h2><p>Experimente retirar uma pauta, escolher “Pelo menos uma” ou mudar a busca. Uma associação não localizada não significa que a candidatura seja contrária ao tema.</p><div class="pauta-empty__actions"><button type="button" class="pauta-button" data-pauta-reset="topics">Limpar pautas</button><button type="button" class="pauta-button" data-pauta-reset="all">Limpar tudo</button></div></section>'''
    text = text.replace('<section class="party-section"', block('empty', empty) + '<section class="party-section"', 1)
    method = f'''<details class="electoral-method-toggle" id="metodo-filtros"><summary><span class="method-number" aria-hidden="true">04</span><span class="method-summary-copy"><span class="section-kicker">Navegar por pautas</span><strong>Como funcionam os filtros de pautas</strong></span><span class="method-chevron" aria-hidden="true">＋</span></summary><div class="method-toggle-body">
<p>Os filtros mostram candidaturas com apoio ou prioridade explicitamente documentados em 2026, na revisão de <time datetime="2026-09-21">21 de setembro de 2026</time>. O tema é uma categoria de navegação: no bloco <strong>Neste filtro</strong>, cada resultado informa o objeto específico do apoio e suas fontes. Saúde, por exemplo, não significa apoio a toda proposta relacionada ao SUS ou à cannabis.</p>
<p>Ao selecionar várias pautas, <strong>Pelo menos uma</strong> mostra quem corresponde a qualquer uma delas. <strong>Todas</strong> exige correspondência em cada pauta selecionada. A busca é aplicada junto com essas escolhas. Os números nos botões contam pessoas no total desta edição, não fontes, e não mudam com a busca. As categorias ficam em ordem alfabética.</p>
<p>Oposição a uma medida, participação em um debate e atuação registrada sem declaração de apoio não entram como apoio. Fontes históricas, de período indeterminado e atribuições conjuntas ainda pendentes permanecem nos cards, mas não alimentam estes filtros. A rotação diária muda apenas a ordem de apresentação; não atualiza a pesquisa.</p>
<p>Neste recorte, {manifest['eligible_candidates']} das {manifest['candidate_count']} fichas têm ao menos um apoio ou prioridade elegível. <strong>Ausência de tag não significa ausência de pauta nem posição contrária.</strong> A documentação disponível é desigual. Sem pautas selecionadas e com a busca vazia, todas as fichas reaparecem; posição e quantidade de temas não são nota, recomendação ou ranking.</p>
<p>As escolhas dos filtros ficam apenas na memória desta página. Não são salvas no navegador nem enviadas ao contador de acessos.</p>
</div></details>'''
    marker = '<section aria-label="Aviso sobre o levantamento" class="independent-notice">'
    assert text.count(marker) == 1
    text = text.replace(marker, block('method', method) + marker, 1).replace(OLD_SENTENCE, NEW_SENTENCE)
    dialog = '''<dialog class="pauta-dialog" id="pautaDialog" aria-labelledby="pautaDialogTitle"><div class="pauta-dialog__header"><h2 id="pautaDialogTitle" tabindex="-1">Filtrar por pautas</h2><button type="button" class="pauta-dialog__close" id="pautaClose" aria-label="Fechar filtros">×</button></div><div class="pauta-dialog__body" id="pautaDialogBody"></div><div class="pauta-dialog__footer"><p id="pautaDialogCount" role="status" aria-live="polite" aria-atomic="true"></p><button type="button" class="pauta-button pauta-button--primary" id="pautaShowResults">Ver resultados</button></div></dialog>'''
    text = text.replace('</body>', block('dialog', dialog) + '</body>', 1)
    assert strip_integration(text) == original, 'Alteração fora dos blocos autorizados'
    path.write_text(text, encoding='utf-8')
    dump(OUT / 'payload.json', data)
    dump(OUT / 'manifest.json', manifest)
    js = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (ROOT / 'assets/sc-federais-filters-data.js').write_text('/* Gerado por tools/sc_federal_filters/build.py; não editar manualmente. */\nwindow.EEF_SC_FEDERAIS_FILTERS = Object.freeze(' + js + ');\n', encoding='utf-8')
    print(json.dumps(manifest, ensure_ascii=False))
    return manifest


if __name__ == '__main__':
    build()

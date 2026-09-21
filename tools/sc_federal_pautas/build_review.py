"""Compila revisão editorial manual; não pesquisa nem infere posições.
Altera somente o bloco de pautas dos 48 cards e inclui método/CSS próprios.
Executar a partir da raiz. Reexecução é idempotente. Nenhum filtro é ativado.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from datetime import date
from html import escape
import csv
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path('data/sc-federais-pautas')
DOCS = Path('docs')
REVIEW_DATE = '2026-09-21'
COVERAGE = {
    'material_eleitoral': 'Material de campanha de 2026',
    'prioridades_declaradas': 'Prioridades declaradas em ficha de 2026',
    'manifestacoes_publicas': 'Manifestações públicas de 2026',
    'registro_historico': 'Registro histórico, sem confirmação de plataforma atual',
    'manifestacoes_e_historico': 'Manifestações de 2026 e registros históricos separados',
    'apresentacao_eleitoral_sem_data': 'Apresentação eleitoral sem data original informada',
    'material_conjunto': 'Material conjunto com atribuição nominal',
    'documentacao_insuficiente': 'Documentação acessível insuficiente para uma síntese'
}
GAP = ('Não foi possível confirmar pautas individuais com a documentação acessível nesta revisão, '
       'concluída em 21/09/2026. Isso não significa ausência de propostas ou de posicionamento da candidatura.')
METHOD = '''<!-- sc-federal-pautas:method:start -->
<details class="electoral-method-toggle pauta-method" id="metodo-pautas">
<summary><span class="method-number" aria-hidden="true">03</span><span class="method-summary-copy"><span class="section-kicker">Pesquisa de pautas</span><strong>De onde vêm as pautas de cada candidatura</strong></span><span aria-hidden="true" class="method-chevron">＋</span></summary>
<div class="method-toggle-body">
<p>Esta revisão, concluída em <time datetime="2026-09-21">21 de setembro de 2026</time>, examinou individualmente as 48 fichas de deputados federais por Santa Catarina já incluídas neste levantamento. Consultamos páginas de campanha, manifestações das próprias candidaturas, registros institucionais e entrevistas com declarações identificadas.</p>
<p>Os números junto às frases levam às fontes. Em <strong>Fontes e contexto</strong>, cada ficha informa o período, a origem da evidência e os limites da pesquisa. Proposta eleitoral, manifestação pública e atuação histórica não são a mesma coisa: materiais antigos ou sem data são identificados e não apresentados automaticamente como plataforma atual.</p>
<p>Não atribuímos posições pela legenda, profissão, nome de urna ou identidade da pessoa. Comentários de terceiros e sugestões de publicações relacionadas também não substituem uma declaração da candidatura. Nos casos sem evidência suficiente, fizemos uma segunda busca e registramos as dificuldades de acesso ou de identificação.</p>
<p><strong>Uma lacuna de documentação não significa ausência de pauta.</strong> As descrições de cobertura se referem apenas ao material que conseguimos consultar, não à qualidade de uma candidatura. A quantidade de temas ou fontes não funciona como nota, recomendação ou previsão eleitoral.</p>
<p>As fontes estão resumidas, não reproduzidas integralmente. Manifestações e propostas são atribuídas a seus autores; sua eficácia ou realização não é presumida. A taxonomia para os futuros filtros continua em revisão e nenhum filtro por pauta foi ativado nesta etapa.</p>
</div></details>
<!-- sc-federal-pautas:method:end -->
'''
LINK = '<link rel="stylesheet" href="assets/sc-federais-pautas.css" data-sc-federal-pautas="1"/>\n'


def dump(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def alpha(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold()) if not unicodedata.combining(c))


def safe_url(value: str) -> str:
    p = urlsplit(value)
    assert p.scheme in ('http', 'https') and p.netloc and not p.username, value
    return escape(value, quote=True)


def compile_records() -> tuple[dict, list[dict]]:
    baseline = json.loads((ROOT / 'baseline.json').read_text(encoding='utf-8'))
    old = {r['id']: r for r in baseline['candidates']}
    inputs = []
    for path in sorted((ROOT / 'inputs').glob('*.json')):
        inputs.extend(json.loads(path.read_text(encoding='utf-8')))
    assert len(inputs) == 48 and len({r['id'] for r in inputs}) == 48, 'Revisão deve cobrir exatamente 48 IDs únicos'
    assert set(old) == {r['id'] for r in inputs}, 'Mudança indevida de população'
    records = []
    for record in inputs:
        assert record['coverage'] in COVERAGE
        assert len(record['research_paths']) >= 2, record['id']
        assert record['identity_check'] and record['limitations']
        for index, source in enumerate(record['sources']):
            safe_url(source['url'])
            assert source['locator'] and source['type'] and source['period']
            if source.get('published_at'):
                assert date.fromisoformat(source['published_at']) <= date.fromisoformat(REVIEW_DATE)
            source['source_id'] = f"{record['id']}-s{index + 1}"
            source['consulted_at'] = REVIEW_DATE
        for index, claim in enumerate(record['claims']):
            assert claim['text'] and claim['themes'] and claim['period']
            assert claim['sources'] and all(isinstance(i, int) and 0 <= i < len(record['sources']) for i in claim['sources'])
            claim['claim_id'] = f"{record['id']}-c{index + 1}"
            claim['source_ids'] = [record['sources'][i]['source_id'] for i in claim['sources']]
            claim['direction'] = claim.get('direction', 'apoio_ou_prioridade')
            claim['taxonomy_review'] = 'preliminar_nao_ativada'
        if record['coverage'] == 'documentacao_insuficiente':
            assert not record['claims'] and not record['sources']
        else:
            assert record['claims'] and record['sources']
        initial = old[record['id']]
        record = {
            **record,
            'name': initial['name'], 'party': initial['party'], 'number': initial['number'],
            'anchor': initial['anchor'], 'reviewed_at': REVIEW_DATE,
            'previous_summary': initial['previous_summary'],
            'previous_has_pauta': initial['previous_has_pauta'],
            'summary': ' '.join(c['text'] for c in record['claims']) if record['claims'] else GAP,
            'coverage_label': COVERAGE[record['coverage']],
            'review_result': 'revisado_com_evidencia' if record['claims'] else 'revisado_com_lacuna',
        }
        records.append(record)
    return baseline, sorted(records, key=lambda r: alpha(r['name']))


def render_pauta(record: dict) -> str:
    if not record['claims']:
        return '<p class="pauta">' + escape(record['summary']) + '</p>'
    parts = []
    for claim in record['claims']:
        refs = []
        for index in claim['sources']:
            source = record['sources'][index]
            label = escape(f"Fonte {index + 1}: {source['title']}", quote=True)
            refs.append(f'<a class="pauta-ref" href="{safe_url(source["url"])}" target="_blank" rel="noopener noreferrer" aria-label="{label}">[{index + 1}]</a>')
        parts.append(escape(claim['text']) + ' ' + ' '.join(refs))
    return '<p class="pauta">' + ' '.join(parts) + '</p>'


def render_context(record: dict) -> str:
    source_items = []
    for source in record['sources']:
        publication = source.get('published_at')
        when = f'Publicado em {date.fromisoformat(publication).strftime("%d/%m/%Y")}' if publication else 'Data original não informada ou não confirmada'
        meta = f'{source["publisher"]} · período: {source["period"]} · {when} · consulta: 21/09/2026.'
        source_items.append(f'<li><a href="{safe_url(source["url"])}" target="_blank" rel="noopener noreferrer">{escape(source["title"])}</a><span class="pauta-evidence__meta">{escape(meta)}</span><span class="pauta-evidence__meta">{escape(source["locator"])}</span></li>')
    refs = '<ol class="pauta-evidence__sources">' + ''.join(source_items) + '</ol>' if source_items else ''
    limits = ''.join('<p>' + escape(item) + '</p>' for item in record['limitations'])
    return (f'\n<details class="pauta-evidence" id="pauta-contexto-{record["id"]}"><summary>Fontes e contexto</summary>'
            f'<div class="pauta-evidence__body"><p><strong>{escape(record["coverage_label"])}</strong><br>Revisão: <time datetime="2026-09-21">21/09/2026</time>.</p>'
            f'{refs}<div class="pauta-evidence__limits">{limits}</div></div></details>')


def update_site(records: list[dict]) -> None:
    path = Path('index.html')
    text = path.read_text(encoding='utf-8')
    by_id = {r['id']: r for r in records}
    visited = set()
    def patch_card(match: re.Match) -> str:
        card = match.group(0)
        cid = re.search(r'data-tse-id="([^"]+)"', card).group(1)
        record = by_id[cid]
        assert cid not in visited
        visited.add(cid)
        card = re.sub(r'\n?<details class="pauta-evidence"[\s\S]*?</details>', '', card)
        card, n = re.subn(r'<p class="pauta">[\s\S]*?</p>', lambda _: render_pauta(record) + render_context(record), card)
        assert n == 1, f'Bloco de pauta inesperado: {cid}'
        has_pauta = 'true' if record['claims'] else 'false'
        card, n = re.subn(r'data-has-pauta="(?:true|false)"', f'data-has-pauta="{has_pauta}"', card, count=1)
        assert n == 1
        search_text = f'{record["party"]} {record["name"]} {record["number"]} {record["summary"]}'.lower()
        card = re.sub(r'data-search="[^"]*"', lambda _: f'data-search="{escape(search_text, quote=True)}"', card, count=1)
        return card
    text, n = re.subn(r'<article class="candidate"[\s\S]*?</article>', patch_card, text)
    assert n == 48 and visited == set(by_id)
    text = re.sub(r'<!-- sc-federal-pautas:method:start -->[\s\S]*?<!-- sc-federal-pautas:method:end -->\n?', '', text)
    notice = '<section aria-label="Aviso sobre o levantamento" class="independent-notice">'
    assert text.count(notice) == 1, 'Limite de inserção metodológica inesperado'
    text = text.replace(notice, METHOD + notice, 1)
    text = re.sub(r'<link[^>]*data-sc-federal-pautas="1"[^>]*>\n?', '', text)
    assert text.count('</head>') == 1
    text = text.replace('</head>', LINK + '</head>', 1)
    path.write_text(text, encoding='utf-8')


def evidence_period(record: dict, claim: dict) -> str:
    if record['coverage'] == 'material_conjunto':
        return 'atribuicao_conjunta_pendente'
    if claim['period'] == 'sem_data':
        return 'sem_data_original'
    if claim['period'] == '2026':
        return 'evidencia_2026'
    return 'historico'


def write_reports(baseline: dict, records: list[dict]) -> dict:
    DOCS.mkdir(exist_ok=True)
    states = Counter(r['coverage'] for r in records)
    with_sources = sum(bool(r['claims']) for r in records)
    unique_sources = {s['url'] for r in records for s in r['sources']}
    coverage = {
        'reviewed_at': REVIEW_DATE,
        'population': '48 fichas SC/Federais preservadas do baseline; não é novo censo ou revalidação do registro eleitoral',
        'baseline_commit': baseline['baseline_commit'], 'reviewed_candidates': len(records),
        'with_some_documented_claim': with_sources,
        'with_insufficient_accessible_documentation': len(records) - with_sources,
        'coverage_states': dict(sorted(states.items())),
        'individual_source_records': sum(len(r['sources']) for r in records),
        'distinct_source_urls': len(unique_sources),
        'claim_groups': sum(len(r['claims']) for r in records),
        'filters_implemented': False,
        'caveat': 'Contagens documentais; não são medidas de mérito político nem ausência de posição.'
    }
    dump(ROOT / 'review.json', {'schema_version': '1.0', 'reviewed_at': REVIEW_DATE, 'baseline_commit': baseline['baseline_commit'], 'candidates': records})
    dump(ROOT / 'coverage.json', coverage)
    columns = ['id','name','party','number','previous_has_pauta','coverage_label','previous_summary','summary','source_urls','research_paths','limitations','review_result']
    with (ROOT / 'audit.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        for r in records:
            row = {key: r.get(key, '') for key in columns}
            row['source_urls'] = ' | '.join(s['url'] for s in r['sources'])
            row['research_paths'] = ' | '.join(r['research_paths'])
            row['limitations'] = ' | '.join(r['limitations'])
            writer.writerow(row)
    result = [
        '# SC federais — revisão documental de pautas', '',
        f'Revisão encerrada em **21/09/2026**. Baseline: `{baseline["baseline_commit"]}`.', '',
        f'**{len(records)} fichas examinadas; {with_sources} com ao menos uma pauta documentada em algum período; {len(records)-with_sources} com documentação acessível insuficiente para uma síntese.**', '',
        'Esses números descrevem a pesquisa. Não medem a qualidade das candidaturas. Uma ficha pode conter material histórico, sem data original ou atribuição conjunta; não se deve apresentar todos esses casos como programas atuais completos.', '',
        '## Cobertura por tipo de evidência', '',
        '| Tipo de material | Fichas |', '|---|---:|',
    ]
    result.extend(f'| {COVERAGE[state]} | {amount} |' for state, amount in sorted(states.items()))
    result.extend(['', f'Foram registrados {coverage["individual_source_records"]} registros de fonte e {coverage["claim_groups"]} grupos de afirmações vinculados a fontes. As consultas e seus limites estão em `data/sc-federais-pautas/review.json`.', '',
        '## Mudanças editoriais e limites', '',
        'As sínteses foram reescritas a partir das evidências que puderam ser conferidas. Listas amplas da versão anterior não foram simplesmente conservadas quando a revisão não sustentou cada associação. O texto anterior de cada ficha permanece no baseline e na auditoria CSV.', '',
        'Páginas com JavaScript foram lidas em navegador quando a extração simples não mostrou as propostas. Em redes sociais, foram conferidos autor, legenda e endereço final. Conteúdos de outras pessoas, comentários e recomendações foram descartados. O acesso posterior pode variar por bloqueios, login ou remoção.', '',
        'Foram separadas propostas de campanha, manifestações públicas, documentos históricos e material conjunto. Não se inferiram propostas pela legenda, nome de urna, identidade ou profissão. Filtros não foram implementados.', '',
        'A taxonomia é apenas uma proposta documental. Registros históricos, páginas sem data original e atribuições conjuntas precisam de tratamento próprio antes da ativação de filtros de apoio. Tema e sentido da posição não são intercambiáveis: uma oposição a uma medida não equivale a apoio genérico ao tema.', '',
        '## Entregáveis', '',
        '- `index.html`: sínteses, referências por frase e bloco Fontes e contexto nas 48 fichas; explicação metodológica específica.',
        '- `data/sc-federais-pautas/review.json` e `audit.csv`: antes/depois, fontes, períodos, percursos de busca e limitações.',
        '- `data/sc-federais-pautas/taxonomy-proposal.json`: famílias temáticas preliminares, separadas por período e atribuição.',
        '- `data/sc-federais-pautas/qa.json`: testes de preservação e navegação; `link-check.json`: disponibilidade observada dos links, sem confundir bloqueio com inexistência.', '',
        '## Auditoria individual — ordem alfabética', ''
    ])
    for r in records:
        result.extend([f'### {r["name"]} — {r["party"]}', '', f'**Cobertura documental:** {r["coverage_label"]}.', '', r['summary'], ''])
        if r['sources']:
            for index, s in enumerate(r['sources'], 1):
                result.append(f'{index}. [{s["title"]}]({s["url"]}) — {s["publisher"]}; período {s["period"]}; data original: {s.get("published_at") or "não informada/confirmada"}; consulta 21/09/2026.')
            result.append('')
        result.extend(['**Percursos da pesquisa:** ' + ' / '.join(r['research_paths']) + '.', '', '**Limites:** ' + ' '.join(r['limitations']), ''])
    (DOCS / 'SC-FEDERAIS-PAUTAS-RESULTADOS.md').write_text('\n'.join(result), encoding='utf-8')
    topics = defaultdict(lambda: defaultdict(set))
    for r in records:
        for c in r['claims']:
            bucket = evidence_period(r, c)
            for label in c['themes']:
                topics[label][bucket].add(r['id'])
    proposed = []
    for label in sorted(topics, key=alpha):
        proposed.append({'label': label, 'status': 'preliminar', 'documentary_coverage': {
            bucket: {'count': len(ids), 'candidate_ids': sorted(ids)} for bucket, ids in sorted(topics[label].items())
        }})
    dump(ROOT / 'taxonomy-proposal.json', {
        'status':'proposta_documental_nao_ativada', 'filters_implemented':False,
        'reviewed_at':REVIEW_DATE,
        'rules':[
            'A taxonomia deriva de associações editoriais explícitas das fontes, nunca de regex sobre o texto público.',
            'Frequência documental não é ranking de candidaturas.',
            'Uma categoria ampla não autoriza atribuir toda medida específica nela compreendida.',
            'Saúde pública e SUS deve ser revisada como Saúde, com subtemas explícitos: menção a saúde não comprova toda posição sobre o SUS.',
            'Temas de grupos de frases exigem validação tema a tema e do sentido de apoio/oposição antes de virar tags.',
            'Histórico, data desconhecida e atribuição conjunta não entram automaticamente em filtros de apoio atual.',
            'Ausência de tema documentado deve ser mostrada como não documentado, não como oposição.'
        ], 'topics':proposed
    })
    table = ['# Taxonomia preliminar — SC federais', '',
             'Não há filtros ativados. As frequências abaixo são documentais, não notas. A ordem é alfabética. Uma ficha pode aparecer em mais de um período; as colunas não devem ser somadas como total de pessoas.', '',
             '| Família temática | Evidência de 2026 | Sem data original | Histórica | Atribuição conjunta pendente |', '|---|---:|---:|---:|---:|']
    for item in proposed:
        counts = item['documentary_coverage']
        amounts = [str(counts.get(bucket, {}).get('count', 0)) for bucket in ('evidencia_2026','sem_data_original','historico','atribuicao_conjunta_pendente')]
        table.append('| ' + item['label'] + ' | ' + ' | '.join(amounts) + ' |')
    table.extend(['', '## Decisões para a etapa de filtros', '',
        'Consolidar nomes e fronteiras das categorias; Saúde deve separar a menção ampla do apoio explícito ao SUS ou a medidas específicas. Educação para jovens trabalhadores não implica uma pauta trabalhista geral. A palavra deficiência não é evidência de ciência. Cuidados, direitos das mulheres e infância podem se cruzar sem serem sinônimos.', '',
        'Manter o sentido das posições: a oposição a bets, redução da maioridade penal ou determinada modalidade escolar não pode ser transformada em apoio à medida. Validar cada associação de tema e frase; nenhuma proposta de taxonomia deste arquivo deve ser ativada mecanicamente.', '',
        'Revisar temporalidade: referências exclusivamente históricas não devem preencher automaticamente o filtro de pautas atuais. Nas apresentações sem data e no material conjunto, conservar a atribuição e buscar confirmação adicional.', '',
        'Só após essas decisões implementar a navegação por pauta, preservando a rotação diária e informando a cobertura documental. As outras frentes deverão passar pelo mesmo protocolo, sem copiar associações entre pessoas ou legendas.', ''])
    (DOCS / 'SC-FEDERAIS-PAUTAS-TAXONOMIA.md').write_text('\n'.join(table), encoding='utf-8')
    return coverage


def main() -> None:
    baseline, records = compile_records()
    update_site(records)
    coverage = write_reports(baseline, records)
    print(json.dumps(coverage, ensure_ascii=False))


if __name__ == '__main__':
    main()

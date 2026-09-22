"""Compila decisões explícitas da #32, Round 1. Não pesquisa nem infere pautas.
Somente escreve data/sc-semantic-v2/ e o relatório próprio em docs/.
Reprodução: python tools/sc_semantic_v2/build.py
"""
from __future__ import annotations
from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import unicodedata
from urllib.parse import urlsplit
from decisions import BASE, D, EXTRA_CONTEXT, REVIEW_DATE
from catalog import MACROS, FAMILY_NOTES, EXTENSION_QUEUE, POLICY
from card_copy import COPY
from source_review import SOURCES, RENDERED_HASHES, RENDER_RUN, RENDER_ARTIFACT, RENDER_ZIP_SHA256

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/sc-semantic-v2'
PINS = {
'data/sc-federais-topics-v1/matrix.json':'6c6153a081bbdda250ebff97b23798e8c896c1e999461a44968f5b913e1a55fb',
'config/topics-v1.json':'c042916a25c2e8a25eea0b735421630e13385183e4d66e56510e2680c8bfdaf4',
'data/sc-federais-pautas/review.json':'63c82e77928937230f63c3d5f0ce8b96d516447487522e690c2a021859d9bf6b'
}
NATURE = {
'A':('apoio_atual_a_medida','pautas',True),
'P':('prioridade_atual_explicita','pautas',True),
'C':('posicao_publica_atual','posicoes',False),
'O':('oposicao_atual','posicoes',False),
'T':('atuacao_parlamentar_ou_publica','historico',False),
'H':('registro_historico','historico',False),
'U':('periodo_nao_confirmado','contexto',False),
'J':('atribuicao_conjunta_pendente','contexto',False)
}
LABELS = {'pautas':'Pautas defendidas','posicoes':'Posições públicas','historico':'Histórico de atuação','contexto':'Contexto documental'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def alpha(text):
    return ''.join(c for c in unicodedata.normalize('NFD', text.casefold()) if not unicodedata.combining(c))


def build():
    for path, digest in PINS.items():
        require(sha256((ROOT/path).read_bytes()).hexdigest() == digest, f'Insumo mudou e exige reconciliação: {path}')
    matrix = load('data/sc-federais-topics-v1/matrix.json')
    taxonomy = load('config/topics-v1.json')
    review = load('data/sc-federais-pautas/review.json')
    old = {a['association_id']:a for a in matrix['associations']}
    people = {c['candidate_id']:c for c in matrix['candidates']}
    previous = {c['id']:c for c in review['candidates']}
    sources = {s['source_id']:s for s in matrix['sources']}
    families = {t['id']:t for t in taxonomy['topics']}
    require(len(people)==48 and len(old)==156 and len(families)==29, 'Baseline inesperado')
    require(set(SOURCES)==set(sources), 'Toda fonte precisa de registro de reconferência')
    require(set(COPY)==set(D), 'Textos editoriais e decisões devem ter as mesmas candidaturas')

    groups = []
    by_family = {}
    for mid, label, members, reason in MACROS:
        member_ids = members.split()
        for tid in member_ids:
            require(tid in families and tid not in by_family, f'Família ausente ou repetida: {tid}')
            by_family[tid] = mid
        groups.append({'id':mid,'label':label,'family_ids':member_ids,'description':reason})
    groups.sort(key=lambda g:alpha(g['label']))
    require(set(by_family)==set(families)==set(FAMILY_NOTES), 'As 29 famílias devem ser mantidas e revisadas')

    source_audit = []
    for sid, source in sorted(sources.items()):
        mode, locator, finding = SOURCES[sid]
        require(mode in {'W','R','X'}, f'Modo de fonte inválido: {sid}')
        require(urlsplit(source['url']).scheme in ('https','http'), 'URL inválida')
        row = {'source_id':sid, 'candidate_id':source['candidate_id'], 'url':source['url'],
               'title':source['title'], 'publisher':source['publisher'],
               'original_published_at':source.get('published_at'), 'original_period':source['period'],
               'checked_on_local':REVIEW_DATE, 'timezone':'America/Sao_Paulo',
               'method':{'W':'leitura_textual_publica','R':'leitura_publica_renderizada','X':'reabertura_sem_conteudo_acessivel'}[mode],
               'content_reconfirmed':mode!='X', 'locator':locator, 'finding':finding,
               'scope':'autoria, contexto, temporalidade e sentido das associações; não auditoria de resultados ou de veracidade de todas as alegações da fonte'}
        if mode=='R':
            require(sid in RENDERED_HASHES, f'Proveniência renderizada ausente: {sid}')
            row.update(render_run=RENDER_RUN, render_artifact=RENDER_ARTIFACT, rendered_text_sha256=RENDERED_HASHES[sid])
            if 'instagram.com' in source['url'] or 'facebook.com' in source['url']:
                row['date_note'] = 'A interface pode mostrar dia/mês ou tempo relativo. O ano depende também do contexto eleitoral registrado; não foi inferido do rodapé da plataforma.'
        if mode=='X':
            row['availability_note'] = 'A indisponibilidade atual não apaga a proveniência da revisão anterior nem prova inexistência de pauta. Não habilitar filtro com base neste registro.'
        source_audit.append(row)
    source_by_id = {s['source_id']:s for s in source_audit}

    audit = []
    sections = defaultdict(lambda:defaultdict(list))
    visited = set()
    for cid, rows in sorted(D.items()):
        require(cid in people, f'Candidatura não reconhecida: {cid}')
        for index, (claim, code, topic_text, text, rationale) in enumerate(rows,1):
            require(code in NATURE and text and rationale, 'Decisão incompleta')
            nature, section, eligible = NATURE[code]
            aids, sids = [], set()
            for tid in topic_text.split():
                aid = f'{cid}-{claim}--{tid}'
                require(aid in old and aid not in visited, f'Associação ausente ou duplicada: {aid}')
                visited.add(aid)
                origin = old[aid]
                require(origin['candidate_id']==cid and origin['topic_id']==tid, 'Cruzamento indevido de identidade')
                require(all(sid in sources and sources[sid]['candidate_id']==cid for sid in origin['source_ids']), 'Fonte de outra candidatura')
                require(not eligible or all(source_by_id[sid]['content_reconfirmed'] for sid in origin['source_ids']), 'Pauta ativa exige fonte reconferida')
                require(not eligible or origin['period']=='2026', 'Não promover material sem temporalidade corrente')
                change = 'permanece_elegivel_com_texto_revisado' if eligible else ('reclassificada_fora_do_filtro' if origin['eligible_current_support'] else 'permanece_fora_do_filtro')
                row = {
                    'association_id':aid, 'candidate_id':cid, 'candidate_name':people[cid]['name'],
                    'claim_id':origin['claim_id'], 'family_id':tid, 'macro_id':by_family[tid],
                    'original_target':origin['position_target'], 'original_direction':origin['direction'],
                    'original_period':origin['period'], 'eligible_v1':origin['eligible_current_support'],
                    'nature':nature, 'section':section, 'eligible_v2':eligible, 'decision':change,
                    'match_text':text, 'rationale_and_locator':rationale,
                    'source_ids':origin['source_ids'], 'all_sources_reconfirmed':all(source_by_id[s]['content_reconfirmed'] for s in origin['source_ids']),
                    'temporal_rule':'defesa_atual_explicita' if eligible else ('periodo_indeterminado' if code=='U' else 'nao_promover_ao_filtro_atual'),
                    'event_date':None,
                    'event_date_note':'Não copiar automaticamente a data da publicação para a data do ato; detalhes estão na fonte e no texto.',
                    'reviewed_on_local':REVIEW_DATE, 'decision_input':'tools/sc_semantic_v2/decisions.py'
                }
                audit.append(row)
                aids.append(aid)
                sids.update(origin['source_ids'])
            sections[cid][section].append({'item_id':f'{cid}-item{index}', 'text':text, 'association_ids':aids,
                                           'source_ids':sorted(sids), 'eligible':eligible, 'is_supplement':False})
    require(visited==set(old), 'Toda associação original deve ter decisão explícita')

    for cid, extras in EXTRA_CONTEXT.items():
        for index, (claim, section, text, sid) in enumerate(extras,1):
            require(section in ('historico','posicoes') and sid in sources and sources[sid]['candidate_id']==cid, 'Suplemento inválido')
            sections[cid][section].append({'item_id':f'{cid}-extra{index}', 'text':text,
                'association_ids':[], 'origin_claim_id':f'{cid}-{claim}', 'source_ids':[sid],
                'eligible':False, 'is_supplement':True,
                'note':'Desmembramento contextual do grupo original; não cria associação elegível nova.'})

    audit.sort(key=lambda a:a['association_id'])
    modeled = []
    for cid, person in sorted(people.items(),key=lambda kv:alpha(kv[1]['name'])):
        own = [a for a in audit if a['candidate_id']==cid]
        own_sections = sections[cid]
        require(set(COPY.get(cid,{}))==set(own_sections), f'Blocos de texto divergentes: {cid}')
        contents = []
        for section in LABELS:
            if section not in own_sections:
                continue
            contents.append({'id':section,'title':LABELS[section], 'summary':COPY[cid][section],
                             'items':own_sections[section], 'filter_source':section=='pautas',
                             'render_location':'fontes_e_contexto' if section=='contexto' else 'candidate_body'})
        eligible_rows = [a for a in own if a['eligible_v2']]
        modeled.append({'candidate_id':cid,'name':person['name'],'party':person['party'],'anchor':person['anchor'],
            'identity_check_from_review':previous[cid]['identity_check'],
            'identity_scope':'identidade preservada e conferida nas fontes utilizadas; sem novo censo eleitoral',
            'sections':contents, 'has_current_defended_pautas':bool(eligible_rows),
            'current_family_ids':sorted({a['family_id'] for a in eligible_rows}),
            'current_macro_ids':sorted({a['macro_id'] for a in eligible_rows}),
            'association_ids':[a['association_id'] for a in own],
            'documentation_note':None if own else 'Não há evidência individual suficiente na revisão disponível para uma síntese responsável. Isso não significa ausência de propostas.',
            'gap_review_scope':None if own else 'Lacuna do levantamento anterior preservada; este round não refez a pesquisa dos 19 casos sem afirmações.',
            'sources_and_context':{'source_ids':[s['source_id'] for s in source_audit if s['candidate_id']==cid],
                                   'previous_limitations':previous[cid]['limitations'],
                                   'not_reconfirmed_source_ids':[s['source_id'] for s in source_audit if s['candidate_id']==cid and not s['content_reconfirmed']]},
            'electoral_career':'preservar_sem_alteracao_na_integracao_visual', 'display_empty_sections':False})

    family_audit = []
    for tid, family in sorted(families.items(),key=lambda kv:alpha(kv[1]['label'])):
        own = [a for a in audit if a['family_id']==tid]
        family_audit.append({'id':tid,'label':family['label'],'preserved':True,'primary_macro_id':by_family[tid],
            'original_includes':family['includes'],'original_excludes':family['excludes'],
            'review_note':FAMILY_NOTES[tid], 'association_ids':[a['association_id'] for a in own],
            'documented_candidates':len({a['candidate_id'] for a in own}),
            'eligible_v1_candidates':len({a['candidate_id'] for a in own if a['eligible_v1']}),
            'eligible_v2_candidates':len({a['candidate_id'] for a in own if a['eligible_v2']}),
            'disposition':'preservada_na_camada_documental_interna'})
    for group in groups:
        group['current_candidate_ids'] = sorted(c['candidate_id'] for c in modeled if group['id'] in c['current_macro_ids'])
        group['current_candidate_count'] = len(group['current_candidate_ids'])
        group['suggested_visible_in_round2'] = bool(group['current_candidate_ids'])
    moved = [a for a in audit if a['eligible_v1'] and not a['eligible_v2']]
    promoted = [a for a in audit if not a['eligible_v1'] and a['eligible_v2']]
    coverage = {
        'baseline_commit':BASE,'reviewed_on_local':REVIEW_DATE,'timezone':'America/Sao_Paulo',
        'round':1,'ui_changed':False,'filters_v2_active':False,
        'candidate_models':len(modeled),'original_claim_groups':len({a['claim_id'] for a in audit}),
        'associations_audited':len(audit),'previously_eligible_audited':sum(a['eligible_v1'] for a in audit),
        'eligible_v2_associations':sum(a['eligible_v2'] for a in audit),'reclassified_from_v1':len(moved),
        'promoted_from_v1':len(promoted),'candidates_with_current_defended_pautas':sum(c['has_current_defended_pautas'] for c in modeled),
        'candidates_with_prior_documentary_gap':sum(not c['association_ids'] for c in modeled),
        'internal_families_preserved':len(family_audit),'macro_groups':len(groups),
        'macro_groups_with_matches':sum(g['current_candidate_count']>0 for g in groups),
        'sources_reviewed':len(source_audit),'sources_reconfirmed':sum(s['content_reconfirmed'] for s in source_audit),
        'sources_not_reconfirmed':[s['source_id'] for s in source_audit if not s['content_reconfirmed']],
        'nature_counts':dict(sorted(Counter(a['nature'] for a in audit).items())),
        'reclassified_association_ids':[a['association_id'] for a in moved],
        'not_a_ranking':'Cobertura e elegibilidade documental não são mérito político, ausência de posição ou completude de programa.'
    }
    metadata = {'schema_version':'2.0.0-round1','baseline_commit':BASE,'inputs_sha256':PINS,'ui_active':False}
    dump(OUT/'association-audit.json',{**metadata,'associations':audit})
    dump(OUT/'candidate-content.json',{**metadata,'candidates':modeled})
    dump(OUT/'source-review.json',{**metadata,'sources':source_audit,'render_archive_sha256':RENDER_ZIP_SHA256})
    dump(OUT/'family-audit.json',{**metadata,'families':family_audit,'extension_queue':EXTENSION_QUEUE})
    dump(OUT/'macrogroups.json',{**metadata,'policy':POLICY,'groups':groups})
    dump(OUT/'coverage.json',coverage)

    lines = ['# SC Federais — auditoria semântica v2, Round 1','',
        '**Modelo editorial e dados revisados; interface publicada ainda não alterada.**','',
        f'Baseline: `{BASE}`. Revisão local: {REVIEW_DATE}, America/Sao_Paulo. Issue #32.','',
        '## Resultado','',
        f"Foram auditadas as {len(audit)} associações, incluindo todas as {coverage['previously_eligible_audited']} usadas pelos filtros v1. O novo recorte mantém {coverage['eligible_v2_associations']} associações atuais em {coverage['candidates_with_current_defended_pautas']} candidaturas e reclassifica {len(moved)} associações para atuação ou posições públicas. Nenhuma associação antes inelegível foi promovida automaticamente.", '',
        'As 48 fichas estão modeladas. As 19 lacunas anteriores continuam explícitas; não foi feita uma nova pesquisa de todas essas candidaturas. A auditoria fecha decisões sobre o material disponível, não declara programas completos.', '',
        'Prioridades amplas declaradas continuam válidas. Não se exige projeto de lei ou detalhamento para uma pauta de Saúde ou Educação. O que não vale é deduzir uma pauta pela profissão, pelo partido, por comentário de terceiro ou pelo assunto de uma reunião passada.', '',
        '## Separação editorial','',
        'Pautas defendidas contém apoios e prioridades atuais. Posições públicas conserva críticas e oposições. Histórico de atuação registra iniciativas e eventos, inclusive de 2026, sem convertê-los em promessa. Material sem período e atribuição conjunta pendente ficam em Contexto documental, dentro de Fontes e contexto: sem data não significa necessariamente antigo.', '',
        'Cada resultado futuro tem uma frase completa, objeto e fontes próprios; o renderer não deve acrescentar “apoia + categoria”. A trajetória eleitoral permanece intocada.', '',
        '## Reclassificações propostas para o Round 2','',
        '| Candidatura | Família | Novo bloco | Motivo |','|---|---|---|---|']
    for a in moved:
        lines.append(f"| {a['candidate_name']} | {families[a['family_id']]['label']} | {LABELS[a['section']]} | {a['rationale_and_locator']} |")
    lines.extend(['','Além das reclassificações, foram reescritos os motivos de correspondência. No caso de Jú, a entrevista sustenta impostos proporcionais à renda e ao patrimônio; não se trata de regularidade fiscal ou declaração de bens. Na ficha de Ana Paula Lima, a defesa atual do salário mínimo foi separada do relato de voto sobre 6×1.','','## Destino das 29 famílias','',
        'Nenhuma família foi excluída ou renomeada no catálogo v1. Cada uma recebe um grupo primário. O agrupamento não cria apoio às outras famílias do mesmo grupo.','','| Grupo amplo proposto | Famílias internas | Pessoas com associação atual |','|---|---|---:|'])
    for group in groups:
        labels = '; '.join(families[t]['label'] for t in group['family_ids'])
        lines.append(f"| {group['label']} | {labels} | {group['current_candidate_count']} |")
    lines.extend(['',f"São {len(groups)} grupos no catálogo de navegação e {coverage['macro_groups_with_matches']} com correspondências neste recorte. Relações internacionais tem entrada própria e permanece preservada, sem um botão vazio obrigatório. Cultura não foi artificialmente fundida com relações internacionais.",'',
        'Economia e Estado reúne tributação, serviços/empresas públicas e regulação econômica, liberando uma entrada coerente para relações internacionais. Meio ambiente e proteção animal explicita os animais no rótulo; Direitos e igualdade conserva LGBTQIA+, igualdade racial, deficiência e envelhecimento na descrição e nos detalhes. Não é necessário somar suas contagens: a mesma pessoa pode estar em vários grupos.','','## Fontes e limites','',
        f"As {len(source_audit)} fontes têm resultado de reconferência. {coverage['sources_reconfirmed']} tiveram o conteúdo pertinente relido; uma fonte histórica de Ivan Marques não pôde ser reconfirmada. Ela permanece com ressalva e sem elegibilidade. HTTP, data de consulta e texto do rodapé não são substitutos para autoria e contexto.", '',
        f'As 12 leituras renderizadas estão rastreadas no [run de fontes]({RENDER_RUN}), artifact {RENDER_ARTIFACT}. O repositório conserva os hashes e localizadores, não cópias integrais de páginas ou comentários. Não houve login, OCR nem contorno de restrições.', '',
        'O registro de fonte confirma o que a pessoa declarou ou o documento relata, não a eficácia de propostas nem toda alegação sobre autoria, aprovação, dinheiro ou votação. Testes estruturais não substituem revisão semântica.', '',
        '## Pontos a ampliar futuramente','',
        'Ciência/tecnologia e política digital têm pistas nas fontes e estão na fila de extensão. Previdência, esporte/lazer, energia e direitos do consumidor também exigem avaliação. Não foram criadas associações automáticas nem feita uma varredura exaustiva de todas as políticas possíveis.','','## Arquivos e reprodução','',
        '`data/sc-semantic-v2/association-audit.json`, `candidate-content.json`, `source-review.json`, `family-audit.json`, `macrogroups.json`, `coverage.json` e `qa.json`.','',
        '```sh','python tools/sc_semantic_v2/build.py','python tools/sc_semantic_v2/qa.py','```','',
        'As decisões editoriais estão em `decisions.py`; os textos dos blocos em `card_copy.py`; as famílias e grupos em `catalog.py`; as reconferências em `source_review.py`. A compilação é determinística e não acessa a rede.', '',
        '## Continuidade','',
        'O Round 2 deve integrar o novo modelo, atualizar a cópia e os macrofiltros desktop/mobile, manter busca e rotação e executar QA visual e funcional sobre o main efetivo. Este Round 1 não habilita filtros v2, não modifica index/assets nem replica para outras frentes. A issue #32 permanece aberta até a publicação validada do Round 2.',''])
    report = ROOT/'docs/SC-FEDERAIS-SEMANTICA-V2-ROUND1.md'
    report.write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(coverage,ensure_ascii=False))
    return coverage


if __name__=='__main__':
    build()

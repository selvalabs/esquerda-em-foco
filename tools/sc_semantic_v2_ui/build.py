"""Integra o modelo aprovado na #32, Round 1. Não pesquisa nem classifica textos.
Escreve somente index, assets v2 gerados e data/sc-semantic-v2-ui/.
Os arquivos v1 e o modelo auditado são preservados como proveniência.
"""
from __future__ import annotations
from collections import defaultdict
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'data/sc-semantic-v2-ui'
BASE = 'a815c909fa8551ed351e637ab0efb63390af6e19'
INPUTS = ('data/sc-semantic-v2/association-audit.json', 'data/sc-semantic-v2/candidate-content.json',
          'data/sc-semantic-v2/macrogroups.json', 'data/sc-semantic-v2/source-review.json',
          'config/topics-v1.json')
RUNTIME_SHA256 = 'abfc2ccace108740df9db71a62b0ecc1f5ad818964473f502b918c9f6eaf853a'

def require(ok, message):
    if not ok:
        raise ValueError(message)

def load(path):
    return json.loads((ROOT/path).read_text(encoding='utf-8'))

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def block(name, text):
    return f'<!-- eef-filters:{name}:start -->\n{text}\n<!-- eef-filters:{name}:end -->'

def replace_block(text, name, value):
    pattern = rf'<!-- eef-filters:{name}:start -->[\s\S]*?<!-- eef-filters:{name}:end -->'
    result, count = re.subn(pattern, lambda _:block(name, value), text)
    require(count == 1, f'Bloco ausente ou duplicado: {name}')
    return result

def date_label(value):
    if value and re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        y,m,d = value.split('-')
        return f'{d}/{m}/{y}'
    return 'data original não confirmada'

def prepare_payload():
    audits = load(INPUTS[0])['associations']
    candidates = load(INPUTS[1])['candidates']
    catalog = load(INPUTS[2])
    sources = {s['source_id']:s for s in load(INPUTS[3])['sources']}
    families = {f['id']:f['label'] for f in load(INPUTS[4])['topics']}
    groups = catalog['groups']
    require(len(audits)==156 and len(candidates)==48, 'Modelo exige reconciliação de universo')
    require(len(groups)==14 and len(families)==29, 'Catálogo inesperado')
    family_map = {fid:g['id'] for g in groups for fid in g['family_ids']}
    require(set(family_map)==set(families) and sum(len(g['family_ids']) for g in groups)==29, 'Família sem grupo ou repetida')
    associations = {a['association_id']:a for a in audits}
    require(len(associations)==156, 'Associação duplicada')
    resolved_sources = {}
    for c in candidates:
        for index,sid in enumerate(c['sources_and_context']['source_ids'],1):
            source = sources[sid]
            require(source['candidate_id']==c['candidate_id'], 'Fonte de outra candidatura')
            url = urlsplit(source['url'])
            require(url.scheme in ('http','https') and url.hostname and not url.username and not url.password, 'URL inválida')
            resolved_sources[sid] = {'url':source['url'],'title':source['title'],'publisher':source['publisher'],
                                    'date':source['original_published_at'],'number':index}
    rows = []
    for c in candidates:
        matches = []
        item_associations = set()
        for section in c['sections']:
            require(section['id'] in ('pautas','posicoes','historico','contexto'), 'Bloco desconhecido')
            require(bool(section['items']) and bool(section['summary']), 'Bloco vazio')
            for item in section['items']:
                require(set(item['source_ids'])<=set(resolved_sources), 'Fonte do item ausente')
                for aid in item['association_ids']:
                    require(aid not in item_associations, 'Associação repetida em blocos')
                    item_associations.add(aid)
                    a = associations[aid]
                    require(a['candidate_id']==c['candidate_id'] and a['section']==section['id'], 'Bloco/identidade divergente')
                    require(a['eligible_v2']==item['eligible']==section['filter_source'], 'Elegibilidade divergente')
                    if not a['eligible_v2']:
                        continue
                    require(a['section']=='pautas' and a['all_sources_reconfirmed'], 'Sem defesa atual reconfirmada')
                    require(a['match_text']==item['text'], 'Frase alterada fora da auditoria')
                    require(family_map[a['family_id']]==a['macro_id'], 'Macrogrupo divergente')
                    matches.append({'associationId':aid,'topicId':a['macro_id'],'familyId':a['family_id'],
                                    'text':a['match_text'],'nature':a['nature'], 'sourceIds':a['source_ids']})
        require(item_associations==set(c['association_ids']), 'Associação omitida no conteúdo')
        topic_ids = sorted({a['topicId'] for a in matches})
        require(topic_ids==c['current_macro_ids'], 'Conjunto filtrável diferente do aprovado')
        rows.append({'id':c['candidate_id'],'topicIds':topic_ids,'matches':sorted(matches,key=lambda a:a['associationId'])})
    topics = []
    for g in groups:
        count = sum(g['id'] in c['topicIds'] for c in rows)
        require(count==g['current_candidate_count'], 'Contagem de grupo divergente')
        if count:
            topics.append({'id':g['id'],'label':g['label'],'count':count,'familyIds':g['family_ids'],
                           'includes':'; '.join(families[fid] for fid in g['family_ids'])})
    data = {'schemaVersion':'2.0.0','edition':'sc-federais','reviewedAt':'2026-09-21',
            'eligibility':'eligible_v2','countScope':'total_edition_unconditioned',
            'topics':topics,'families':families,'candidates':rows,'sources':resolved_sources}
    require(len(topics)==13 and sum(len(c['matches']) for c in rows)==112 and sum(bool(c['matches']) for c in rows)==19, 'Contagens v2 inesperadas')
    manifest = {'schema_version':'2.0.0','edition':'sc-federais','ui_version':2,'filters_active':True,
                'reviewed_at':data['reviewedAt'],'implemented_at':'2026-09-22','baseline_commit':BASE,
                'candidate_count':len(rows),'eligible_candidates':19,'eligible_associations':112,
                'internal_families':29,'catalog_macrogroups':14,'visible_macrogroups':len(topics),
                'counts':{g['id']:g['count'] for g in topics},
                'no_current_matches':[g['id'] for g in groups if not g['current_candidate_count']],
                'source_sha256':{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},
                'privacy':'Somente memória da página; sem armazenamento ou envio de escolhas; métricas não habilitadas.',
                'legacy':'Os arquivos v1 e o Round 1 permanecem inalterados; seus flags não ativam esta interface.'}
    return data,manifest,candidates,groups,sources

def refs(sids, data, external=False):
    result = []
    for sid in sorted(set(sids),key=lambda s:data['sources'][s]['number']):
        s = data['sources'][sid]
        href = s['url'] if external else '#pauta-fonte-'+sid
        extra = ' target="_blank" rel="noopener noreferrer"' if external else ''
        result.append(f'<a class="pauta-ref" href="{escape(href,quote=True)}"{extra} aria-label="Fonte {s["number"]}: {escape(s["title"],quote=True)}">[{s["number"]}]</a>')
    return ' '.join(result)

def render_candidate(c, data, sources):
    cid = c['candidate_id']
    visible = [s for s in c['sections'] if s['id']!='contexto']
    sections = []
    for s in visible:
        title_id = f'pauta-bloco-{cid}-{s["id"]}'
        ids = [sid for item in s['items'] for sid in item['source_ids']]
        sections.append(f'<section class="pauta-block pauta-block--{s["id"]}" data-pauta-section="{s["id"]}" aria-labelledby="{title_id}"><h4 id="{title_id}" class="pauta-block__title">{escape(s["title"])}</h4><p class="pauta pauta-v2-copy">{escape(s["summary"])} {refs(ids,data)}</p></section>')
    if c['documentation_note']:
        sections.append(f'<p class="pauta-v2-gap">{escape(c["documentation_note"])}</p>')
    elif not visible:
        sections.append('<p class="pauta-v2-gap">Há material com período ou atribuição ainda não confirmados. Ele está disponível em <a href="#pauta-contexto-'+cid+'">Fontes e contexto</a> e não alimenta os filtros de pautas atuais.</p>')
    result = '<div class="candidate-editorial" data-pauta-model="2">'+''.join(sections)+'</div>'
    body = ['<p class="pauta-v2-review">Revisão documental: <time datetime="2026-09-21">21/09/2026</time>. A organização dos blocos não é uma avaliação da candidatura.</p>']
    for s in c['sections']:
        if s['id']=='contexto':
            body.append(f'<section class="pauta-block pauta-block--contexto" data-pauta-section="contexto" aria-labelledby="pauta-bloco-{cid}-contexto"><h4 class="pauta-block__title" id="pauta-bloco-{cid}-contexto">Contexto documental</h4><p class="pauta-v2-copy">{escape(s["summary"])} {refs([sid for i in s["items"] for sid in i["source_ids"]],data)}</p></section>')
    source_list=[]
    for sid in c['sources_and_context']['source_ids']:
        s=sources[sid]
        warning = '<p class="pauta-v2-warning">Fonte não reconfirmada na revisão semântica. Registro anterior preservado com ressalva, sem alimentar filtros atuais.</p>' if not s['content_reconfirmed'] else ''
        source_list.append(f'<li id="pauta-fonte-{sid}"><a href="{escape(s["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(s["title"])}</a><span class="pauta-evidence__meta">{escape(s["publisher"])} · {date_label(s["original_published_at"])} · período registrado: {escape(s["original_period"])}</span><span class="pauta-evidence__meta">{escape(s["locator"])}</span>{warning}</li>')
    if source_list:
        body.append('<ol class="pauta-evidence__sources">'+''.join(source_list)+'</ol>')
    else:
        body.append('<p>Não há fonte programática individual suficiente associada a esta ficha na revisão disponível.</p>')
    if c['sources_and_context']['previous_limitations']:
        body.append('<div class="pauta-evidence__limits">'+''.join('<p>'+escape(x)+'</p>' for x in c['sources_and_context']['previous_limitations'])+'</div>')
    if c['sections']:
        details=[]
        for s in c['sections']:
            items=''.join(f'<li data-evidence-item="{i["item_id"]}">{escape(i["text"])} {refs(i["source_ids"],data)}</li>' for i in s['items'])
            details.append('<h5>'+escape(s['title'])+'</h5><ul>'+items+'</ul>')
        body.append('<details class="pauta-v2-items"><summary>Ver evidências por bloco</summary>'+''.join(details)+'</details>')
    result += f'<details class="pauta-evidence" id="pauta-contexto-{cid}"><summary>Fontes e contexto</summary><div class="pauta-evidence__body">'+''.join(body)+'</div></details>'
    return '<div class="candidate-copy">\n'+result+'\n</div>'

# Only these parts of an existing candidate card may be replaced.
COPY_RE = r'<div class="candidate-copy">[\s\S]*?</div>(?=\n<div class="candidate-links">)'

def normalize_index(text):
    """Remove authorized editorial/filter areas for a byte-level preservation check."""
    text = re.sub(r'<!-- eef-filters:([a-z-]+):start -->[\s\S]*?<!-- eef-filters:\1:end -->','',text)
    text = re.sub(COPY_RE,'<div class="candidate-copy">EDITORIAL</div>',text)
    text = re.sub(r' data-search="[^"]*"','',text)
    text = re.sub(r'<details class="electoral-method-toggle pauta-method" id="metodo-pautas">[\s\S]*?</details>','METHOD',text)
    return text

def panel(data, groups):
    chips=[]
    for topic in data['topics']:
        n=topic['count']
        aria=f'{topic["label"]}: {n} candidatura'+('' if n==1 else 's')+' em SC/Federais'
        chips.append(f'<button type="button" class="pauta-chip" data-pauta-topic="{topic["id"]}" aria-pressed="false" aria-label="{escape(aria,quote=True)}" title="{escape(topic["includes"],quote=True)}"><span class="pauta-chip__label">{escape(topic["label"])}</span><span class="pauta-chip__count" aria-hidden="true">{n}</span></button>')
    glossary=[]
    for g in groups:
        labels='; '.join(data['families'][fid] for fid in g['family_ids'])
        suffix=' Nenhuma pauta atual elegível neste grupo no recorte revisado; o material registrado continua nas fichas.' if not g['current_candidate_count'] else ''
        glossary.append('<dt>'+escape(g['label'])+'</dt><dd>'+escape(labels+'.'+suffix)+'</dd>')
    return '''<div id="pautaSidebarHost" class="pauta-sidebar-host"><section class="pauta-panel" id="pautaPanel" data-version="2" aria-labelledby="pautaPanelTitle" hidden>
<h2 class="pauta-panel__title" id="pautaPanelTitle">Filtrar por pautas</h2>
<p class="pauta-panel__intro">Escolha áreas de interesse. Cada resultado mostra a pauta concreta que justifica a seleção.</p>
<fieldset class="pauta-mode"><legend>Ao marcar várias áreas</legend><div class="pauta-mode__options"><label><input type="radio" name="pauta-mode" value="any" checked> Pelo menos uma</label><label><input type="radio" name="pauta-mode" value="all"> Todas</label></div></fieldset>
<p class="pauta-panel__counts">Números: candidaturas no total de SC/Federais, independentemente da busca.</p>
<div class="pauta-list" role="group" aria-label="Áreas de pautas disponíveis">'''+''.join(chips)+'''</div>
<span class="pauta-panel__selection" data-pauta-selection>Nenhuma área selecionada</span><button class="pauta-clear" type="button" data-pauta-clear disabled>Limpar pautas</button>
<details class="pauta-v2-glossary"><summary>O que cada filtro reúne</summary><p>As 29 famílias de pautas continuam registradas. Os botões apenas as agrupam para facilitar a navegação.</p><dl>'''+''.join(glossary)+'''</dl></details>
<p class="pauta-panel__note">19 das 48 fichas têm pautas atuais documentadas neste recorte. Sem correspondência não significa sem proposta. <a href="#metodo-filtros">Entenda o critério</a>.</p>
</section></div>'''

MATCHING = '''  function matchingEvidence(record) {
    let box = record.card.querySelector('.pauta-match');
    if (!selected.size || record.card.hidden) {
      if (box) { box.hidden = true; box.replaceChildren(); }
      return;
    }
    const defended = record.card.querySelector('[data-pauta-section="pautas"]');
    if (!defended) return; // No fallback to the old single paragraph or historical text.
    if (!box) {
      box = node('div', 'pauta-match');
      defended.insertAdjacentElement('afterend', box);
    }
    const groups = new Map();
    record.candidate.matches.filter(match => selected.has(match.topicId)).forEach(match => {
      const key = JSON.stringify([match.text, match.sourceIds]);
      if (!groups.has(key)) groups.set(key, {...match, topicIds: new Set(), familyIds: new Set()});
      groups.get(key).topicIds.add(match.topicId);
      groups.get(key).familyIds.add(match.familyId);
    });
    box.replaceChildren(node('p', 'pauta-match__heading', 'Por que aparece neste filtro'));
    const list = node('ul', 'pauta-match__list');
    groups.forEach(match => {
      const item = node('li');
      const labels = [...match.topicIds].map(id => topicMap.get(id).label).join(' · ');
      item.append(node('strong', '', labels));
      const families = [...match.familyIds].map(id => data.families[id]).join(' · ');
      if (families !== labels) item.append(node('small', 'pauta-match__family', families));
      item.append(node('span', 'pauta-match__text', match.text));
      const refs = node('span', 'pauta-match__sources');
      match.sourceIds.forEach(id => {
        const source = data.sources[id];
        if (!source) return;
        const a = node('a', '', `Fonte ${source.number} ↗`);
        a.href = source.url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.setAttribute('aria-label', `Fonte ${source.number}: ${source.title}`);
        a.title = source.title;
        refs.append(a);
      });
      item.append(refs); list.append(item);
    });
    box.append(list); box.hidden = !groups.size;
  }
'''

def runtime():
    original=(ROOT/'assets/pauta-filters.js').read_text(encoding='utf-8')
    require(sha256(original.encode()).hexdigest()==RUNTIME_SHA256, 'Runtime v1 mudou; revisar a integração')
    result=original.replace('window.EEF_SC_FEDERAIS_FILTERS;', 'window.EEF_SC_FEDERAIS_FILTERS_V2;')
    result=result.replace('if (!data || !core ||', 'if (!data || data.schemaVersion !== "2.0.0" || !core ||')
    start=result.index('  function matchingEvidence(record) {')
    end=result.index('  function render()',start)
    result=result[:start]+MATCHING+'\n'+result[end:]
    # Search all authored summaries, including indeterminate context, but not source metadata.
    result=result.replace("copy.querySelectorAll('details, .candidate-index, .pauta-match').forEach(node => node.remove());", "copy.querySelectorAll('.candidate-copy, .candidate-index, .pauta-match').forEach(node => node.remove());")
    result=result.replace('text: copy.textContent, card, candidate', 'text: copy.textContent + " " + (card.dataset.search || ""), card, candidate')
    result=result.replace('`${selected.size} pauta${selected.size === 1 ? \'\' : \'s\'} selecionada${selected.size === 1 ? \'\' : \'s\'}`', '`${selected.size} área${selected.size === 1 ? \'\' : \'s\'} selecionada${selected.size === 1 ? \'\' : \'s\'}`')
    result=result.replace('Nenhuma pauta selecionada','Nenhuma área selecionada')
    require('Apoio declarado:' not in result and 'Prioridade declarada:' not in result, 'Prefixo v1 persistente')
    return '/* Gerado por tools/sc_semantic_v2_ui/build.py; modelo v2, motor e navegação v1 preservados. */\n'+result

def build():
    data,manifest,candidates,groups,sources = prepare_payload()
    index=ROOT/'index.html'
    text=index.read_text(encoding='utf-8')
    prior=text
    records={c['candidate_id']:c for c in candidates}
    seen=set()
    def update_card(m):
        card=m.group(0)
        cid=re.search(r'data-tse-id="(\d+)"',card).group(1)
        require(cid in records and cid not in seen,'Ficha ausente/duplicada')
        seen.add(cid); c=records[cid]
        card,n=re.subn(COPY_RE,lambda _:render_candidate(c,data,sources),card)
        require(n==1, f'Estrutura editorial inesperada {cid}')
        search=' '.join([c['party'], c['name']]+[s['summary'] for s in c['sections']])
        card,n=re.subn(r' data-search="[^"]*"',lambda _:' data-search="'+escape(search,quote=True)+'"',card,count=1)
        require(n==1, 'Índice textual ausente')
        return card
    text=re.sub(r'<article class="candidate"[^>]*>[\s\S]*?</article>', update_card,text)
    require(len(seen)==48,'Universo de cards divergente')
    method='''<details class="electoral-method-toggle pauta-method" id="metodo-pautas"><summary><span class="method-number" aria-hidden="true">03</span><span class="method-summary-copy"><span class="section-kicker">Pesquisa de pautas</span><strong>De onde vêm as pautas de cada candidatura</strong></span><span aria-hidden="true" class="method-chevron">＋</span></summary><div class="method-toggle-body">
<p>O levantamento das 48 fichas foi revisado documentalmente em <time datetime="2026-09-21">21 de setembro de 2026</time>. As fontes incluem páginas individuais, manifestações das candidaturas, entrevistas e registros institucionais. A revisão semântica separa o que é defendido hoje do que é posição pública, relato de atuação ou material de período indeterminado.</p>
<p><strong>Pautas defendidas</strong> reúne apoios e prioridades atuais expressos. <strong>Posições públicas</strong> conserva críticas, oposições e outras manifestações. <strong>Histórico de atuação</strong> registra iniciativas, projetos, reuniões e relatos de voto, sem os transformar automaticamente em promessas. Uma pauta antiga pode ser atual quando reafirmada explicitamente.</p>
<p>Os números junto aos textos levam às fontes. <strong>Fontes e contexto</strong> informa origem, período e limites, inclusive material sem data ou de atribuição ainda pendente. Sem data não significa necessariamente antigo. Relatar autoria de um projeto não comprova sua aprovação, assim como uma convocação não comprova que um encontro aconteceu.</p>
<p>Não atribuímos posições pela legenda, profissão, identidade ou comentários de terceiros. Uma prioridade ampla expressa é válida; não exigimos um projeto de lei detalhado. As 19 lacunas do levantamento anterior permanecem identificadas e não foram objeto de uma nova pesquisa exaustiva nesta etapa.</p>
<p><strong>Uma lacuna documental não significa ausência de pauta.</strong> A cobertura não mede mérito, e o número de temas não é uma nota ou recomendação. A rotação diária muda a ordem, não atualiza a pesquisa.</p>
</div></details>'''
    text,n=re.subn(r'<details class="electoral-method-toggle pauta-method" id="metodo-pautas">[\s\S]*?</details>',lambda _:method,text)
    require(n==1,'Metodologia de pautas ausente')
    text=replace_block(text,'sidebar',panel(data,groups))
    filter_method='''<details class="electoral-method-toggle" id="metodo-filtros"><summary><span class="method-number" aria-hidden="true">04</span><span class="method-summary-copy"><span class="section-kicker">Navegar por pautas</span><strong>Como funcionam os filtros de pautas</strong></span><span class="method-chevron" aria-hidden="true">＋</span></summary><div class="method-toggle-body">
<p>Os botões reúnem pautas em <strong>áreas amplas</strong>. As 29 famílias de temas continuam registradas em 14 grupos; 13 têm correspondências neste recorte. Nenhum assunto foi apagado para reduzir a lista. Em <strong>O que cada filtro reúne</strong>, no painel, você encontra a composição de todos os grupos, inclusive o que ainda não tem correspondência atual.</p>
<p>O resultado aparece porque há uma pauta defendida e documentada naquela área. O bloco <strong>Por que aparece neste filtro</strong> mostra a frase concreta e a fonte. Estar em Economia e Estado por uma proposta de impostos não significa apoiar todas as posições sobre serviços públicos ou empresas estatais.</p>
<p><strong>Pelo menos uma</strong> aceita qualquer área selecionada; <strong>Todas</strong> exige uma pauta em cada área. A busca funciona junto com a seleção. Os números dos botões são pessoas distintas no total de SC/Federais, não fontes; não variam com a busca. Os filtros não reordenam as fichas nem criam ranking.</p>
<p>Posições públicas, oposições e registros de atuação continuam disponíveis, mas não alimentam automaticamente o filtro de pautas defendidas. Uma oposição pode ser uma posição política importante; separá-la aqui não é um juízo de mérito. Material sem período ou atribuição confirmados permanece em Fontes e contexto.</p>
<p><strong>19 das 48 fichas</strong> têm pautas atuais que atendem ao recorte revisado de 21/09/2026. As 48 continuam acessíveis com os critérios limpos. Ausência de correspondência não significa oposição ou ausência de propostas. Não é uma verificação contínua de campanha.</p>
<p>As escolhas ficam somente na memória desta página: não são salvas no navegador, na URL ou enviadas ao contador de acessos.</p>
</div></details>'''
    text=replace_block(text,'method',filter_method)
    runtime_text=runtime()
    (ROOT/'assets/pauta-filters-v2.js').write_text(runtime_text,encoding='utf-8')
    encoded=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    (ROOT/'assets/sc-federais-filters-v2-data.js').write_text('/* Gerado; somente associações eligible_v2. */\nwindow.EEF_SC_FEDERAIS_FILTERS_V2 = Object.freeze('+encoded+');\n',encoding='utf-8')
    def version(path):
        return path+'?v='+sha256((ROOT/path).read_bytes()).hexdigest()[:12]
    css=['assets/pauta-filters.css','assets/pauta-v2.css']
    js=['assets/pauta-filter-core.js','assets/sc-federais-filters-v2-data.js','assets/pauta-filters-v2.js']
    assets='\n'.join(f'<link rel="stylesheet" href="{version(p)}"/>' for p in css)+'\n'+'\n'.join(f'<script defer src="{version(p)}"></script>' for p in js)
    text=replace_block(text,'assets',assets)
    require(normalize_index(text)==normalize_index(prior),'HTML alterado fora das áreas autorizadas')
    index.write_text(text,encoding='utf-8')
    write_json(OUT/'payload.json',data);write_json(OUT/'manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=False))
    return manifest

if __name__=='__main__':
    build()

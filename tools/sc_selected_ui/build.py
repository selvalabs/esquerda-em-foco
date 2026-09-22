"""Round 2 #36: integração estática, sem pesquisa ou reclassificação.
Entradas aprovadas do Round 1 são somente leitura. Saídas são reproduzíveis.
"""
from __future__ import annotations
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
OUT=ROOT/'data/sc-selected-ui'
BASE='d8bf0ae43a24f0f8f297316bb366e497dc3dfc8c'
COPY_RE=r'<div class="candidate-copy">[\s\S]*?</div>(?=\n<div class="candidate-links">)'
INPUTS=['data/sc-editorial-selected-r1/editorial.json','data/sc-editorial-selected-r1/paragraph-locations.json',
        'data/sc-semantic-v2/candidate-content.json','data/sc-semantic-v2/association-audit.json',
        'data/sc-semantic-v2-ui/payload.json','assets/pauta-filters-v2.js','tools/sc_editorial_selected/selection-core.cjs']

def require(ok,message):
    if not ok: raise ValueError(message)

def load(p): return json.loads((ROOT/p).read_text(encoding='utf-8'))

def dump(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def marked(name,content): return f'<!-- eef-selected:{name}:start -->\n{content}\n<!-- eef-selected:{name}:end -->'

def strip_selected(text):
    return re.sub(r'<!-- eef-selected:([a-z-]+):start -->[\s\S]*?<!-- eef-selected:\1:end -->\n?','',text)

def normalize(text):
    text=strip_selected(text)
    text=re.sub(COPY_RE,'<div class="candidate-copy">EDITORIAL</div>',text)
    text=re.sub(r' data-search="[^"]*"','',text)
    text=re.sub(r'<!-- eef-filters:assets:start -->[\s\S]*?<!-- eef-filters:assets:end -->','ASSETS',text)
    for mid in ['metodo-pautas','metodo-filtros']:
        text=re.sub(r'<details[^>]* id="'+mid+r'">[\s\S]*?</details>','METHOD-'+mid,text)
    return text

def ref_links(sids,source_map,numbers,seen):
    links=[]
    for sid in sorted(set(sids),key=lambda x:numbers[x]):
        s=source_map[sid];n=numbers[sid]
        caption=s['caption'].replace(' · sem data original informada','')
        label=f'[{n}]' if sid in seen else caption+f' [{n}]'
        seen.add(sid)
        links.append(f'<a href="#pauta-fonte-{sid}" class="eef-source-ref" aria-label="Fonte {n}: {escape(s["title"],quote=True)}" title="{escape(s["caption"],quote=True)}">{escape(label)}</a>')
    return '<span class="eef-paragraph-sources">'+' '.join(links)+'</span>'

def render(c,data,original):
    cid=c['candidate_id'];sources=data['sources'];numbers={sid:n for n,sid in enumerate(c['source_ids'],1)}
    action=f'<div class="eef-card-actions" hidden><button type="button" class="eef-button" data-eef-toggle="{cid}" aria-pressed="false">Selecionar</button><button type="button" class="eef-button" data-eef-share="{cid}">Compartilhar ficha</button></div>'
    def section(s):
        seen=set();parts=[]
        for p in s['paragraphs']:
            aids=' '.join(p['association_ids'])
            parts.append(f'<div class="eef-editorial-paragraph" id="eef-texto-{p["paragraph_id"]}" data-eef-paragraph="{p["paragraph_id"]}" data-eef-associations="{aids}"><p class="pauta pauta-v2-copy">{escape(p["text"])}</p>{ref_links(p["source_ids"],sources,numbers,seen)}</div>')
        if s['notice']:parts.append('<p class="eef-editorial-notice">'+escape(s['notice'])+'</p>')
        return f'<section class="pauta-block pauta-block--{s["id"]}" data-pauta-section="{s["id"]}" aria-labelledby="pauta-bloco-{cid}-{s["id"]}"><h4 class="pauta-block__title" id="pauta-bloco-{cid}-{s["id"]}">{escape(s["title"])}</h4>'+''.join(parts)+'</section>'
    visible=[section(s) for s in c['sections'] if s['id']!='contexto']
    if c['gap_text']:visible.append('<p class="pauta-v2-gap">'+escape(c['gap_text'])+'</p>')
    elif not visible:visible.append('<p class="pauta-v2-gap">Há material com data ou autoria ainda não confirmadas. Consulte <a href="#pauta-contexto-'+cid+'">Fontes e contexto</a>; esse material não entra nos filtros de pautas atuais.</p>')
    body=['<p class="pauta-v2-review">Levantamento revisado em <time datetime="2026-09-21">21/09/2026</time>. A redação foi reorganizada em 22/09/2026, sem nova pesquisa de posições.</p>']
    body.extend(section(s) for s in c['sections'] if s['id']=='contexto')
    li=[]
    for sid in c['source_ids']:
        s=sources[sid]
        warning='' if s['content_reconfirmed'] else '<p class="eef-editorial-notice">Fonte não reconfirmada na revisão semântica. O registro permanece com ressalva e não alimenta filtros atuais.</p>'
        li.append(f'<li id="pauta-fonte-{sid}"><a href="{escape(s["url"],quote=True)}" target="_blank" rel="noopener noreferrer">{escape(s["title"])}</a><span class="pauta-evidence__meta">{escape(s["publisher"])} · {escape(s["caption"])}</span><span class="pauta-evidence__meta">{escape(s["locator"])}</span>{warning}</li>')
    body.append('<ol class="pauta-evidence__sources">'+''.join(li)+'</ol>' if li else '<p>Não há fonte programática individual suficiente associada à ficha neste levantamento.</p>')
    notes=c['retained_limitations']+[s['context_note'] for s in c['sections'] if s['context_note']]
    if notes:body.append('<div class="pauta-evidence__limits">'+''.join('<p>'+escape(n)+'</p>' for n in dict.fromkeys(notes))+'</div>')
    details=[]
    for old_section in original['sections']:
        title=next(s['title'] for s in c['sections'] if s['id']==old_section['id'])
        items=[]
        for item in old_section['items']:
            links=ref_links(item['source_ids'],sources,numbers,set(c['source_ids']))
            items.append(f'<li data-evidence-item="{item["item_id"]}">{escape(item["text"])} {links}</li>')
        details.append('<h5>'+escape(title)+'</h5><ul>'+''.join(items)+'</ul>')
    if details:body.append('<details class="pauta-v2-items"><summary>Consultar os registros usados no texto</summary>'+''.join(details)+'</details>')
    return '<div class="candidate-copy">\n'+action+f'<p class="eef-reader-party">{escape(c["party"])} · SC · Deputado federal</p><div class="candidate-editorial" data-pauta-model="editorial-r2">'+''.join(visible)+f'</div><details class="pauta-evidence" id="pauta-contexto-{cid}"><summary>Fontes e contexto</summary><div class="pauta-evidence__body">'+''.join(body)+'</div></details>\n</div>'

MATCHING=r'''  function matchingEvidence(record) {
    record.card.querySelectorAll('.eef-filter-note, .pauta-match').forEach(el => el.remove());
    if (!selected.size || record.card.hidden) return;
    const byParagraph = new Map();
    record.candidate.matches.filter(m => selected.has(m.topicId)).forEach(m => {
      const p = record.card.querySelector(`[data-eef-associations~="${m.associationId}"]`);
      if (!p || p.closest('[data-pauta-section]')?.dataset.pautaSection !== 'pautas') return;
      if (!byParagraph.has(p)) byParagraph.set(p, []);
      byParagraph.get(p).push(m);
    });
    byParagraph.forEach((matches, paragraph) => {
      const detail = node('details', 'eef-filter-note');
      const labels = [...new Set(matches.map(m => topicMap.get(m.topicId).label))];
      detail.append(node('summary', '', 'Neste trecho: ' + labels.join(' · ')));
      detail.append(node('p', 'eef-filter-help', 'A correspondência é com os registros abaixo, não com todos os assuntos do parágrafo.'));
      const seen = new Set();
      matches.forEach(m => {
        const key = JSON.stringify([m.text,m.sourceIds]);
        if (seen.has(key)) return;
        seen.add(key);
        const p = node('p', 'eef-filter-exact', m.text + ' ');
        m.sourceIds.forEach(id => {
          const source = data.sources[id];
          if (!source) return;
          const a = node('a', '', `[${source.number}]`);
          a.href = '#pauta-fonte-' + id;
          a.setAttribute('aria-label', 'Fonte: ' + source.title);
          p.append(a);
        });
        detail.append(p);
      });
      paragraph.append(detail);
    });
  }
'''

METHODS={
'metodo-pautas':('03','Pesquisa de pautas','Como reunimos as informações',[
'O levantamento foi revisado em 21 de setembro de 2026. Os textos se baseiam em páginas individuais, declarações das candidaturas, entrevistas e registros institucionais. A revisão de linguagem não atualiza automaticamente essa pesquisa.',
'<strong>Pautas atuais</strong> reúne apoios e prioridades expressos no período documentado. <strong>Outras posições</strong> traz críticas, oposições e outras manifestações. <strong>Atuação registrada</strong> mostra iniciativas, projetos e relatos — inclusive de 2026 — sem transformá-los automaticamente em propostas de campanha.',
'As referências junto aos parágrafos levam às fontes. Em <strong>Fontes e contexto</strong> ficam as datas, as limitações e os registros que sustentam cada texto. Quando a data ou a autoria não foram confirmadas, isso permanece indicado. Um relato de autoria de projeto não comprova aprovação da lei.',
'Não atribuímos pautas pela legenda, profissão, identidade ou comentários de terceiros. Uma prioridade ampla explicitamente declarada é válida; não é necessário haver um projeto de lei detalhado. Quando faltam informações, não completamos por suposição.']),
'metodo-filtros':('04','Navegar por pautas','Como usar os filtros',[
'Escolha uma ou mais áreas para encontrar fichas com pautas atuais documentadas nesses assuntos. <strong>Pelo menos uma</strong> aceita qualquer área escolhida; <strong>Todas</strong> exige correspondência em cada área. A busca por texto funciona junto com os filtros.',
'Nos parágrafos relacionados aparece <strong>Neste trecho</strong>. Abra essa indicação para consultar o registro específico e sua fonte, sem repetir toda a explicação na leitura inicial. Uma proposta sobre impostos não significa apoio a todos os assuntos de Economia e Estado.',
'As 29 famílias de pautas permanecem registradas em 14 grupos; 13 têm correspondências neste recorte. <strong>O que cada filtro reúne</strong>, no painel, explica onde cada assunto ficou. Os números nos botões representam pessoas no total desta edição, não fontes, e não mudam com a busca.',
'Outras posições e registros de atuação continuam acessíveis, mas não alimentam automaticamente o filtro de pautas atuais. Das 48 fichas, 19 têm correspondências neste recorte. Ausência de tag não significa oposição ou ausência de propostas. Limpe os critérios para consultar todas.',
'<strong>Selecionados</strong> reúne fichas na ordem em que você as adiciona, para leitura individual. Os filtros não apagam sua coleção nem alteram a rotação diária da listagem. A coleção fica só nesta visita; um link compartilhado pode reabri-la. Quem receber o link poderá ver os itens incluídos. Não há envio de escolhas ao contador de acessos.'])}

def method_html(mid,values):
    n,kicker,title,paras=values
    return f'<details class="electoral-method-toggle'+(' pauta-method' if mid=='metodo-pautas' else '')+f'" id="{mid}"><summary><span class="method-number" aria-hidden="true">{n}</span><span class="method-summary-copy"><span class="section-kicker">{kicker}</span><strong>{title}</strong></span><span class="method-chevron" aria-hidden="true">＋</span></summary><div class="method-toggle-body">'+''.join('<p>'+p+'</p>' for p in paras)+'</div></details>'

DIALOGS='''<div class="eef-selection-bar" id="eefSelectionBar" hidden><span><strong data-eef-count>0</strong> selecionados</span><button type="button" class="eef-button" data-eef-open>Ver selecionados</button></div>
<p class="sr-only" id="eefSelectionStatus" role="status" aria-live="polite"></p>
<dialog class="eef-dialog eef-reader" id="eefCollection" aria-labelledby="eefCollectionTitle">
<header class="eef-reader-header"><div><p class="eef-kicker">Fichas para consulta</p><h2 id="eefCollectionTitle" tabindex="-1">Selecionados <span data-eef-count>0</span></h2></div><button type="button" class="eef-button" id="eefCollectionClose">Voltar à lista</button></header>
<div class="eef-reader-controls" id="eefReaderControls"><button type="button" class="eef-button" id="eefPrevious" aria-label="Ficha anterior">← Anterior</button><span id="eefPager" role="status" aria-live="polite"></span><button type="button" class="eef-button" id="eefNext" aria-label="Próxima ficha">Próxima →</button></div>
<p class="eef-reader-help">Uma ficha por vez, na ordem da sua seleção. O conteúdo e as fontes são os mesmos da listagem.</p>
<section id="eefCollectionEmpty" class="eef-empty"><h3>Nenhuma ficha selecionada</h3><p>Volte à lista e use Selecionar nas fichas que deseja reunir para consulta.</p></section>
<div id="eefReaderHost"></div>
<div id="eefCollectionActions" class="eef-collection-actions"><a class="eef-button" id="eefOpenFull" href="#candidaturas">Ir à ficha na lista</a><button type="button" class="eef-button" id="eefShareCollection">Compartilhar selecionados</button><button type="button" class="eef-button" id="eefClearCollection">Limpar selecionados</button></div>
<p class="eef-reader-privacy">A coleção não é salva no navegador. Ao recarregar, ela só é recuperada quando o link contém os itens. Qualquer pessoa com o link poderá abrir a coleção, com o conteúdo disponível no momento da consulta.</p>
</dialog>
<dialog class="eef-dialog eef-share-dialog" id="eefShareDialog" aria-labelledby="eefShareTitle"><header class="eef-dialog-header"><h2 id="eefShareTitle">Compartilhar</h2><button type="button" class="eef-button" id="eefShareClose">Fechar</button></header><p id="eefShareMessage"></p><label for="eefShareUrl">Link para consulta</label><textarea id="eefShareUrl" readonly rows="3"></textarea><div class="eef-share-actions"><button type="button" class="eef-button" id="eefCopy">Copiar link</button><a class="eef-button" id="eefWhatsapp" target="_blank" rel="noopener noreferrer">WhatsApp</a><button type="button" class="eef-button" id="eefNativeShare" hidden>Outros aplicativos</button></div><p id="eefShareStatus" role="status" aria-live="polite"></p><p class="eef-reader-privacy">Você escolhe o contato e confirma o envio no aplicativo. Esta página não acessa seus contatos nem envia mensagens automaticamente. O link mostra os itens incluídos; não é privado.</p></dialog>
<dialog class="eef-dialog eef-confirm" id="eefConfirm" aria-labelledby="eefConfirmTitle"><h2 id="eefConfirmTitle">Limpar selecionados?</h2><p>As fichas continuam disponíveis na lista. Apenas esta coleção será esvaziada.</p><div class="eef-share-actions"><button type="button" class="eef-button" id="eefCancelClear">Cancelar</button><button type="button" class="eef-button" id="eefConfirmClear">Limpar coleção</button></div></dialog>'''

NAV='''<button type="button" class="eef-button eef-nav-selection" id="eefSelectedNav" data-eef-open aria-label="Abrir selecionados: 0 fichas" hidden><svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18"><path d="M6 3h12v18l-6-4-6 4z" fill="none" stroke="currentColor" stroke-width="1.7"/></svg><span class="eef-nav-label">Selecionados</span><span data-eef-count>0</span></button>'''

def build():
    data=load(INPUTS[0]);old=load('data/sc-semantic-v2/candidate-content.json')['candidates']
    mapping={c['candidate_id']:c for c in data['candidates']};original={c['candidate_id']:c for c in old}
    require(len(mapping)==48 and set(mapping)==set(original),'Universo divergente')
    require(data['comparison_enabled'] is False,'Coleção não comparativa')
    html=(ROOT/'index.html').read_text(encoding='utf-8');before=html;html=strip_selected(html)
    seen=set()
    def card(m):
        text=m.group(0);cid=re.search(r'data-tse-id="(\d+)"',text).group(1)
        require(cid in mapping and cid not in seen,'Identidade duplicada/ausente');seen.add(cid)
        c=mapping[cid]
        text,n=re.subn(COPY_RE,lambda _:render(c,data,original[cid]),text);require(n==1,'Área editorial não encontrada')
        search=' '.join([c['party'],c['name'],c['number']]+[p['text'] for s in c['sections'] for p in s['paragraphs']])
        text,n=re.subn(r' data-search="[^"]*"',lambda _:' data-search="'+escape(search,quote=True)+'"',text,count=1);require(n==1,'Busca ausente')
        return text
    html=re.sub(r'<article class="candidate"[^>]*>[\s\S]*?</article>',card,html);require(len(seen)==48,'Cards ausentes')
    for mid,values in METHODS.items():
        html,n=re.subn(r'<details[^>]* id="'+mid+r'">[\s\S]*?</details>',lambda _:method_html(mid,values),html);require(n==1,'Metodologia ausente')
    runtime=(ROOT/'assets/pauta-filters-v2.js').read_text()
    start=runtime.index('  function matchingEvidence(record) {');end=runtime.index('  function render()',start)
    runtime=runtime[:start]+MATCHING+'\n'+runtime[end:]
    runtime=runtime.replace("'.candidate-copy, .candidate-index, .pauta-match'","'.candidate-copy, .candidate-index, .pauta-match, .eef-card-actions'")
    (ROOT/'assets/pauta-filters-editorial.js').write_text(runtime,encoding='utf-8')
    (ROOT/'assets/selecionados-core.js').write_bytes((ROOT/'tools/sc_editorial_selected/selection-core.cjs').read_bytes())
    require('id="accessCounter"' in html,'Navbar inesperada')
    at=re.search(r'<span[^>]*id="accessCounter"',html).start()
    html=html[:at]+marked('nav',NAV)+'\n'+html[at:]
    html=html.replace('</body>',marked('dialogs',DIALOGS)+'\n</body>',1)
    css=['assets/pauta-filters.css','assets/pauta-v2.css','assets/editorial-selected.css']
    js=['assets/pauta-filter-core.js','assets/sc-federais-filters-v2-data.js','assets/pauta-filters-editorial.js','assets/selecionados-core.js','assets/selecionados.js']
    def version(p):return p+'?v='+sha256((ROOT/p).read_bytes()).hexdigest()[:12]
    assets='<!-- eef-filters:assets:start -->\n'+'\n'.join(f'<link rel="stylesheet" href="{version(p)}"/>' for p in css)+'\n'+'\n'.join(f'<script defer src="{version(p)}"></script>' for p in js)+'\n<!-- eef-filters:assets:end -->'
    html,n=re.subn(r'<!-- eef-filters:assets:start -->[\s\S]*?<!-- eef-filters:assets:end -->',lambda _:assets,html);require(n==1,'Assets ausentes')
    require(normalize(before)==normalize(html),'Mudança fora das áreas autorizadas')
    (ROOT/'index.html').write_text(html,encoding='utf-8')
    manifest={'version':'1.0.0','edition':'sc-federais','production_enabled':True,'comparison_enabled':False,
        'candidate_count':48,'paragraph_count':sum(len(s['paragraphs']) for c in mapping.values() for s in c['sections']),
        'evidence_date':data['evidence_date'],'editorial_date':data['editorial_date'],'selection_order':'explicit_user_insertion',
        'persistence':'memory_only; shared_fragment_import_on_navigation','copies_of_candidate_cards':0,
        'source_sha256':{p:sha256((ROOT/p).read_bytes()).hexdigest() for p in INPUTS},
        'ui_assets':css+js,'note':'As fichas originais são movidas e devolvidas à posição original ao fechar o leitor. Filtros e seleção são estados distintos.'}
    dump(OUT/'manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=False))
    return manifest

if __name__=='__main__':build()

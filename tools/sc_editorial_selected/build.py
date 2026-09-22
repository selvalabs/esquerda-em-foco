"""Round 1 #36: compila apenas dados editoriais, contrato e prévia isolada.
Não modifica index.html, assets publicados, taxonomias nem fontes de origem.
Execute na raiz. A prévia gerada fica fora da árvore versionada do site.
"""
from __future__ import annotations
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from copy import deepcopy
# The module is named copy.py for editorial content; import explicitly to avoid stdlib shadowing.
import importlib.util

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
OUT = ROOT / 'data/sc-editorial-selected-r1'
PREVIEW = Path('/tmp/eef-editorial-selected-r1')
spec=importlib.util.spec_from_file_location('editorial_decisions',HERE/'copy.py')
COPY_MODULE=importlib.util.module_from_spec(spec);spec.loader.exec_module(COPY_MODULE)
COPY=COPY_MODULE.COPY;LABELS=COPY_MODULE.LABELS;BASE=COPY_MODULE.BASE
PINS={
'data/sc-semantic-v2/candidate-content.json':'a547de0cd21cdce7ab57307f99fdd924b377ba8387230fe1c453a76420089d83',
'data/sc-semantic-v2/association-audit.json':'41bd9a6fbdb08abe6ff44bcf65fe3c9ce46294a190e1114c01373b537ddf9d1b',
'data/sc-semantic-v2/source-review.json':'d1869685d428376d450519c37a2e6778d345f09a4f82fe24144dbf7ef679153c',
'data/sc-semantic-v2-ui/payload.json':'ac3b31e47daf45b090fff9f5a7e25a20eaf03f40f14a03836b4857d784841f2b'
}
TYPES={'campanha':'Apresentação da candidatura','apresentacao_partidaria_individual':'Apresentação individual',
'post_autoral':'Publicação da candidatura','manifestacao_autoral':'Texto da candidatura','entrevista_declaracoes_diretas':'Entrevista',
'registro_institucional':'Registro institucional','declaracoes_diretas_publicadas':'Declarações publicadas','entrevista_partidaria_individual':'Entrevista',
'ficha_de_prioridades':'Ficha de prioridades','post_autoral_coletiva':'Publicação da coletiva','registro_de_manifestacao':'Registro de manifestação',
'carta_autoral_reproduzida':'Carta publicada','proposicao_legislativa':'Requerimento','documento_autoral':'Documento do mandato',
'registro_autoral_historico':'Registro do mandato','material_conjunto_atribuido':'Material conjunto','post_autoral_de_campanha':'Publicação de campanha'}
MONTHS=['jan','fev','mar','abr','mai','jun','jul','ago','set','out','nov','dez']

def require(ok,message):
    if not ok:raise ValueError(message)

def load(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))

def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def safe_url(value):
    u=urlsplit(value)
    require(u.scheme in ('https','http') and u.netloc and not u.username and not u.password,'URL externa inválida')
    return value

def source_caption(kind,date):
    require(kind in TYPES,'Tipo de fonte sem rótulo editorial: '+kind)
    if date:
        require(re.fullmatch(r'\d{4}-\d{2}-\d{2}',date),'Data original não padronizada')
        year,month,_=date.split('-');suffix=MONTHS[int(month)-1]+'/'+year
    else:suffix='sem data original informada'
    return TYPES[kind]+' · '+suffix

def build():
    for p,h in PINS.items():require(sha256((ROOT/p).read_bytes()).hexdigest()==h,'Insumo mudou: reconciliar '+p)
    model=load('data/sc-semantic-v2/candidate-content.json')['candidates']
    associations=load('data/sc-semantic-v2/association-audit.json')['associations']
    source_review=load('data/sc-semantic-v2/source-review.json')['sources']
    matrix=load('data/sc-federais-topics-v1/matrix.json')
    original_sources={s['source_id']:s for s in matrix['sources']}
    by_association={a['association_id']:a for a in associations}
    require(len(model)==48 and len(associations)==156,'Universo inesperado')
    require(set(COPY)=={c['candidate_id'] for c in model if c['sections']},'Candidatura documentada sem revisão explícita')
    soup=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
    html_cards={c['data-tse-id']:c for c in soup.select('article.candidate')}
    require(len(html_cards)==48,'Cards do site divergentes')
    sources={}
    for s in source_review:
        sid=s['source_id'];origin=original_sources[sid]
        require(s['original_published_at']==origin.get('published_at'),'Datas de proveniência divergentes')
        sources[sid]={'source_id':sid,'candidate_id':s['candidate_id'],'url':safe_url(s['url']),'title':s['title'],
            'publisher':s['publisher'],'caption':source_caption(origin['type'],s['original_published_at']),
            'publication_date':s['original_published_at'],'period':s['original_period'],'locator':s['locator'],
            'content_reconfirmed':s['content_reconfirmed'],'review_scope':'proveniência herdada da auditoria; não nova reconferência integral nesta rodada'}
    candidates=[];audit=[];all_items=[];association_locations={};block_count=0
    for c in model:
        cid=c['candidate_id'];html_card=html_cards[cid]
        require(c['name']==html_card.select_one('h3').get_text(' ',strip=True),'Nome divergente')
        rewritten=[]
        require(set(COPY.get(cid,{}))=={s['id'] for s in c['sections']},'Blocos divergentes: '+cid)
        for section in c['sections']:
            sid=section['id'];decision=COPY[cid][sid];block_count+=1
            items={i['item_id']:i for i in section['items']};used=[];paragraphs=[]
            for n,(short_ids,text) in enumerate(decision['p'],1):
                item_ids=[cid+'-'+i for i in short_ids.split()]
                require(item_ids and len(set(item_ids))==len(item_ids) and set(item_ids)<=set(items),'Item de outro bloco ou duplicado: '+cid+' '+sid)
                require(text and not any(x in text for x in ['<script','Apoio declarado:','Prioridade declarada:']),'Texto público inválido')
                used.extend(item_ids);source_ids=sorted({v for iid in item_ids for v in items[iid]['source_ids']})
                aids=sorted({v for iid in item_ids for v in items[iid]['association_ids']})
                require(all(sources[x]['candidate_id']==cid for x in source_ids),'Fonte de outra pessoa')
                pid=f'{cid}-{sid}-p{n}'
                paragraph={'paragraph_id':pid,'text':text,'item_ids':item_ids,'association_ids':aids,'source_ids':source_ids}
                paragraphs.append(paragraph)
                for aid in aids:
                    require(aid not in association_locations,'Associação duplicada em parágrafos')
                    a=by_association[aid]
                    require(a['candidate_id']==cid and a['section']==sid,'Natureza da evidência alterada')
                    association_locations[aid]={'candidate_id':cid,'paragraph_id':pid,'eligible_v2':a['eligible_v2'],
                        'source_item_ids':[iid for iid in item_ids if aid in items[iid]['association_ids']],
                        'macro_id':a['macro_id'],'family_id':a['family_id'],
                        'exact_evidence':a['match_text'],'evidence_source_ids':a['source_ids'],
                        'display_policy':'localizador_do_trecho; não destacar todas as afirmações do parágrafo como se fossem a mesma associação'}
                audit.append({'candidate_id':cid,'section_id':sid,'paragraph_id':pid,'item_ids':item_ids,'source_ids':source_ids,
                    'approved_items':[{'item_id':iid,'text':items[iid]['text'],'source_ids':items[iid]['source_ids']} for iid in item_ids],
                    'revised_text':text,'decision':'reescrita_editorial_sem_mudar_natureza_ou_elegibilidade'})
            require(len(used)==len(set(used))==len(items) and set(used)==set(items),'Item omitido/duplicado: '+cid+' '+sid)
            all_items.extend(used)
            rewritten.append({'id':sid,'title':LABELS[sid],'original_title':section['title'], 'paragraphs':paragraphs,
                'notice':decision.get('notice'),'context_note':decision.get('note'),'filter_source':section['filter_source']})
        source_ids=c['sources_and_context']['source_ids']
        require(all(s in sources for s in source_ids),'Fonte ausente')
        candidates.append({'candidate_id':cid,'name':c['name'],'party':c['party'],'number':html_card.select_one('.number').get_text(' ',strip=True),
            'anchor':c['anchor'],'sections':rewritten,'source_ids':source_ids,
            'retained_limitations':c['sources_and_context']['previous_limitations'],
            'gap_text':COPY_MODULE.GAP if not c['sections'] else None,
            'review_result':'texto_revisado' if c['sections'] else 'aviso_de_lacuna_revisado_sem_nova_pesquisa',
            'current_macro_ids':c['current_macro_ids'],'current_family_ids':c['current_family_ids'],
            'has_current_defended_pautas':c['has_current_defended_pautas'],
            'association_ids':c['association_ids']})
    require(len(all_items)==len(set(all_items))==145 and block_count==39,'Cobertura editorial incompleta')
    require(set(association_locations)==set(by_association),'Associação sem localizador editorial')
    ui=dict(COPY_MODULE.UI_COPY);ui['context_intro']=COPY_MODULE.CONTEXT_INTRO
    output={'schema_version':'1.0.0-round1','edition':'sc-federais','editorial_date':'2026-09-22','evidence_date':'2026-09-21',
        'baseline_commit':BASE,'source_hashes':PINS,'site_base':'https://selvalabs.github.io/esquerda-em-foco/',
        'production_enabled':False,'research_changed':False,'comparison_enabled':False,'ui':ui,'candidates':candidates,'sources':sources}
    manifest={'baseline_commit':BASE,'candidate_records':len(candidates),'reviewed_sections':block_count,'reviewed_items':len(all_items),
        'paragraphs':len(audit),'documented_candidate_records':sum(bool(c['sections']) for c in candidates),
        'gap_candidate_records':sum(bool(c['gap_text']) for c in candidates),'source_records':len(sources),
        'association_records':len(associations),'eligible_associations_preserved':sum(a['eligible_v2'] for a in associations),
        'source_hashes':PINS,'production_enabled':False,'research_changed':False,'selection_scope':'colecao_de_consulta_individual',
        'scope_change':'Não implementa comparação lado a lado ou seções sincronizadas entre candidaturas.',
        'preview_isolation':'Artefato em /tmp; não é adicionado ao index nem aos assets publicados.'}
    dump(OUT/'editorial.json',output)
    dump(OUT/'parity-audit.json',{'baseline_commit':BASE,'scope':'revisão de formulação; os testes de links não certificam automaticamente equivalência de sentido','paragraphs':audit})
    dump(OUT/'paragraph-locations.json',{'associations':association_locations})
    dump(OUT/'decisions.json',{'decisions':COPY_MODULE.EDITORIAL_DECISIONS})
    dump(OUT/'manifest.json',manifest)
    PREVIEW.mkdir(parents=True,exist_ok=True)
    html=(HERE/'preview.html').read_text(encoding='utf-8')
    data_json=json.dumps(output,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    for token,content in [('__CSS__',(HERE/'preview.css').read_text()),('__CORE__',(HERE/'selection-core.cjs').read_text()),('__APP__',(HERE/'preview.js').read_text()),('__DATA__',data_json)]:
        require(html.count(token)==1,'Marcador da prévia ausente ou duplicado');html=html.replace(token,content)
    (PREVIEW/'index.html').write_text(html,encoding='utf-8')
    (PREVIEW/'LEIA-ME.txt').write_text('Prévia não publicada — issue #36 / Round 1\n\nAbra index.html para ler os textos e testar Selecionados. Para testar links locais da coleção, sirva esta pasta com:\npython -m http.server 8765\nAbra http://localhost:8765/\n\nUma ficha é mostrada por vez. Não há comparação entre candidaturas. A coleção fica somente em memória. Links de coleção desta prévia não devem ser divulgados como links do site público. O compartilhamento de uma ficha usa o link já existente no site. Nenhuma mensagem é enviada automaticamente.\n\nA publicação e integração ao site pertencem ao Round 2.\n',encoding='utf-8')
    report=['# SC/Federais — revisão editorial e coleção, Round 1','',
        '**Preparação em branch, sem alteração do site publicado.**','',
        '## Entrega','',
        f'Revisadas as {len(candidates)} fichas: {block_count} blocos documentados em 29 fichas e o aviso de lacuna em outras 19. Os 145 itens, 156 associações, 112 elegibilidades e 36 fontes permanecem vinculados ao material de origem. Não foi realizada nova pesquisa integral de candidaturas.','',
        'A camada pública agora é organizada em parágrafos com referências próprias. Pautas atuais e Outras posições permanecem separadas. O título escolhido para histórico é Atuação registrada, pois o bloco também contém iniciativas de 2026. As ressalvas que mudam a leitura permanecem junto do texto; o detalhamento fica em Fontes e contexto.','',
        'Cada parágrafo aponta para os itens exatos de origem. As 156 associações têm um localizador, permitindo reduzir a repetição do motivo dos filtros no Round 2 sem classificar o texto novamente. Um localizador não transforma todas as frases do parágrafo em justificativa de um mesmo tema.','',
        '## Selecionados: delimitação da entrega','',
        'O protótipo permite reunir fichas, removê-las, navegar na ordem de seleção e abrir uma ficha individual de cada vez. Não implementa o comparativo lado a lado ou as seções sincronizadas descritos no escopo inicial. Compartilhamento nativo, WhatsApp e cópia são preparados sem acesso a contatos ou envio automático.','',
        'A produção ainda não interpreta links de coleção. Por isso, no protótipo, a cópia de um link local de coleção é identificada como teste; envio da coleção para aplicativos externos fica desativado. O compartilhamento individual aponta para a âncora já existente no site.','',
        '## Arquivos','',
        '`data/sc-editorial-selected-r1/editorial.json`: camada pública e referências por parágrafo.','',
        '`parity-audit.json`: vínculo entre a redação revisada e os itens originais. `paragraph-locations.json`: localizadores das associações. `decisions.json`: escolhas editoriais. `manifest.json`: cobertura e isolamento.','',
        '`tools/sc_editorial_selected/`: entradas editoriais, compilação, núcleo de seleção e protótipo. A prévia HTML autocontida é gerada somente em `/tmp/eef-editorial-selected-r1/` e entregue como artifact, não publicada pelo Pages.','',
        '## Limites e próxima etapa','',
        'Testes de estrutura não certificam automaticamente a equivalência política das frases. A revisão de redação foi feita sobre os itens aprovados; fontes, datas, natureza e elegibilidade originais foram mantidas. Falta de fonte suficiente não foi preenchida com suposições.','',
        'O Round 2 integra a camada pública à listagem existente, conecta Selecionados à navegação sem alterar os filtros e habilita os links de coleção no endereço publicado. Exige QA do merge efetivo, revisão visual e teste do compartilhamento real nos aplicativos disponíveis. Nenhuma comparação, avaliação ou recomendação entre candidaturas faz parte da implementação.','']
    (ROOT/'docs/SC-EDITORIAL-SELECTED-ROUND1.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps(manifest,ensure_ascii=False))
    return manifest

if __name__=='__main__':build()

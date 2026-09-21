"""Render RS state deputies from public evidence using the approved visual shell.
The federal renderer is imported only for pure HTML helpers. Its build/enrichment
entry points are never called; all writable paths belong to the new edition.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import html
import importlib.util
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais'
DEST=ROOT/'rs/deputados-estaduais'
CANONICAL='https://selvalabs.github.io/esquerda-em-foco/rs/deputados-estaduais/'
TSE='https://dadosabertos.tse.jus.br/dataset/candidatos-2026'

def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def helper():
    spec=importlib.util.spec_from_file_location('federal_pure_renderer',ROOT/'tools/rs/build.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.DEST=DEST
    return module


def normalized(r):
    manifest=load(D/'manifest.json',{})
    candidates=load(D/'candidates-official.json',[])
    profiles=load(D/'profiles-official.json',{})
    histories=load(D/'history-normalized.json',{})
    photos=load(D/'photos-official.json',{})
    editorials=load(D/'editorial.json',{})
    offices=load(D/'offices-verified.json',{})
    research=load(D/'web-research.json',{})
    audit=load(A/'reconciliation.json',{})
    checks={x['candidate_id']:x for x in audit.get('identity_checks',[])}
    election=load(D/'election-api.json',[])[0]['id']
    output=[]
    for record in candidates:
        cid=record['SQ_CANDIDATO']
        if record['CD_CARGO']!='7' or record['SG_UF']!='RS' or record['ANO_ELEICAO']!='2026':
            raise ValueError('Wrong state, office or election in normalized record')
        profile=profiles.get(cid,{})
        api=profile.get('data',{})
        history=histories.get(cid,[])
        past=[h for h in history if h['year']<2026]
        disputes={(h['year'],h['candidate_id']) for h in past}
        name=r.label(record['NM_URNA_CANDIDATO'])
        occupation=r.label(record.get('DS_OCUPACAO'))
        biography=f'{name} declara a ocupação de {occupation.lower()} no cadastro eleitoral de 2026.' if occupation else f'{name} tem registro de candidatura a deputado estadual no RS em 2026.'
        if past:
            years=sorted({h['year'] for h in past})
            span=str(years[0]) if len(years)==1 else f'{years[0]} a {years[-1]}'
            biography+=f' O TSE vincula {len(disputes)} disputa'+('s anteriores' if len(disputes)!=1 else ' anterior')+f', de {span}. Os cargos e resultados constam no histórico abaixo.'
        else:
            biography+=' O histórico consultado não vincula disputa anterior; isso não comprova ausência de experiência política.'
        e=editorials.get(cid,{})
        networks=[];sites=[]
        declared=research.get(cid,{}).get('valid_links',[])
        if not declared:
            declared=sorted({r.url(u) for u in api.get('sites',[]) if r.url(u)})
        for address in declared:
            host=(urlsplit(address).hostname or '').removeprefix('www.')
            platform=next((label for domain,label in r.SOCIAL.items() if host==domain or host.endswith('.'+domain)),None)
            if host=='bsky.app':platform='Bluesky'
            item={'label':platform or host,'url':address,'source':profile.get('url')}
            if platform:
                networks.append(item)
            elif host not in ('bit.ly','tinyurl.com') and not any(x in host for x in ('queroapoiar','apoia.se','vaquinha')):
                sites.append(item)
        own_office=offices.get(cid)
        if own_office and (not own_office.get('source') or not own_office.get('checked_at')):
            raise ValueError('Current office requires dated institutional evidence: '+cid)
        reviewed=bool(e.get('reviewed') and e.get('sources'))
        pautas=e.get('pautas') if reviewed else None
        activities=e.get('activities',[]) if reviewed else []
        entry={'id':cid,'name':name,'official_name':record['NM_URNA_CANDIDATO'],'full_name':r.label(record['NM_CANDIDATO']),'number':record['NR_CANDIDATO'],'party':record['SG_PARTIDO'],'federation':r.clean(record.get('NM_FEDERACAO')),'occupation':occupation,'status':api.get('descricaoSituacao') or r.clean(record.get('DS_SITUACAO_JULGAMENTO')) or r.clean(record.get('DS_SITUACAO_CANDIDATURA')),'status_checked_at':profile.get('checked_at'),'current_office':own_office,'history':history,'photo':photos.get(cid),'socials':networks,'sites':sites,'pautas':pautas,'pautas_type':e.get('pautas_type') if pautas else None,'biography':e.get('biography') if reviewed and e.get('biography') else biography,'biography_basis':'reviewed_sources' if reviewed and e.get('biography') else 'official_electoral_record','activities':activities,'editorial_sources':e.get('sources',[]) if reviewed else [],'editorial_checked_at':e.get('checked_at') if reviewed else None,'tse_url':f'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/2026/{election}/RS/{cid}','source_record':{'url':TSE,'detail_url':profile.get('url'),'id':cid,'generated_at':record['DT_GERACAO']+' '+record['HH_GERACAO']},'checks':{'registro_validado':bool(checks.get(cid,{}).get('identity_fields_match')),'foto_validada':bool(photos.get(cid)),'historico_fonte_consultada':cid in histories,'historico_anterior_disponivel':bool(past),'mandato_confirmado_institucionalmente':bool(own_office),'pautas_com_fonte_revisada':bool(pautas),'atuacao_com_fonte_revisada':bool(activities),'links_declarados_auditados':cid in research,'redes_com_link_valido':bool(networks),'biografia_eleitoral_documentada':bool(profile.get('data'))},'source_format_note':'Diferença apenas de pontuação/espaçamento no nome civil entre fontes; identidade confirmada por identificador, número, partido e cargo.' if checks.get(cid,{}).get('formatting_difference') else None}
        output.append(entry)
    return sorted(output,key=lambda c:(r.norm(c['party']),r.norm(c['name']),c['id'])),manifest


def card(record,icons,r):
    node=BeautifulSoup(r.card(record,icons),'html.parser').article
    node['data-status']=record['status'] or ''
    node['data-has-history']=str(any(h['year']<2026 for h in record['history'])).lower()
    copy=node.select_one('.candidate-copy')
    if record.get('pautas_type')=='candidate_declaration':
        copy.select_one('.eyebrow').string='Pautas declaradas pela candidatura'
    elif record.get('pautas_type')=='institutional_record':
        copy.select_one('.eyebrow').string='Temas da atuação documentada'
    bio=copy.select_one('.rs-biography')
    if bio and record['biography_basis']=='official_electoral_record':
        bio.append(BeautifulSoup(' '+r.link(record['source_record']['detail_url'],'TSE · trajetória eleitoral ↗','source-link'),'html.parser'))
    for activity in record.get('activities',[]):
        if not activity.get('source') or not activity.get('text'):raise ValueError('Unsourced activity')
        markup='<div class="rs-activity"><p class="eyebrow">Atuação institucional documentada</p><p>'+r.esc(activity['text'])+'</p>'+r.link(activity['source'],r.esc(activity.get('label','Fonte institucional'))+' ↗','source-link')+'</div>'
        copy.append(BeautifulSoup(markup,'html.parser'))
    current=record.get('current_office')
    if current:
        node.select_one('.career-current').append(BeautifulSoup('<p class="empty">Consulta institucional: '+r.esc(current['checked_at'][:10])+' · '+r.esc(current.get('detail',''))+'</p>','html.parser'))
    context=node.select_one('.career-ref')
    context.append(' Data da consulta individual: '+str(record.get('status_checked_at') or '')[:10]+'.')
    if record.get('source_format_note'):
        node.select_one('.rs-card-footer').append(BeautifulSoup('<span class="empty">Nome civil: variação de pontuação conciliada entre as fontes.</span>','html.parser'))
    # REST-only historical rows with unknown turn are marked explicitly.
    if any(h.get('round_note') for h in record['history']):
        node.select_one('.rs-history').append(BeautifulSoup('<p class="empty">Alguns resumos históricos do DivulgaCand não informam o turno. Nenhum voto foi atribuído a esses registros sem conciliação.</p>','html.parser'))
    return str(node)


def og_image():
    image=Image.new('RGB',(1200,630),'#f2eadf')
    draw=ImageDraw.Draw(image)
    def font(size,bold=False):
        family='DejaVuSerif-Bold.ttf' if bold else 'DejaVuSans.ttf'
        try:return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/'+family,size)
        except OSError:return ImageFont.load_default(size=size)
    draw.rectangle((0,0,1200,12),fill='#43634f')
    draw.text((72,64),'ESQUERDA EM FOCO',font=font(28),fill='#43634f')
    draw.text((70,162),'Rio Grande',font=font(88,True),fill='#243d31')
    draw.text((70,258),'do Sul',font=font(88,True),fill='#243d31')
    draw.line((76,399,1124,399),fill='#c8c5b5',width=2)
    draw.text((76,436),'DEPUTADOS ESTADUAIS · 2026',font=font(32),fill='#243d31')
    draw.text((76,518),'Candidaturas, trajetórias e fontes públicas',font=font(25),fill='#536154')
    (DEST/'assets').mkdir(parents=True,exist_ok=True)
    image.save(DEST/'assets/og-rs-estaduais.png',optimize=True)


def build():
    r=helper()
    records,manifest=normalized(r)
    assert records and len({c['id'] for c in records})==len(records)
    for directory in (DEST,A):directory.mkdir(parents=True,exist_ok=True)
    template=ROOT/'rs/deputados-federais/index.html'
    frozen=template.read_bytes()
    soup=BeautifulSoup(frozen,'html.parser')
    icons={}
    for a in soup.select('.social-link--icon'):
        svg=a.select_one('svg')
        if svg:icons[a.get('aria-label','').split(' ')[0]]=str(svg).replace('viewbox=','viewBox=')
    counts=collections.Counter(c['party'] for c in records)
    statuses=collections.Counter(c['status'] for c in records)
    checked=sum(c['checks']['registro_validado'] for c in records)
    mandate=sum(bool(c['current_office']) for c in records)
    previous=sum(c['checks']['historico_anterior_disponivel'] for c in records)
    agendas=sum(bool(c['pautas']) for c in records)
    activities=sum(bool(c['activities']) for c in records)
    snapshot=manifest['collected_at'][:10]
    title='Candidatos a Deputado Estadual no RS 2026 | Esquerda em foco'
    description='Candidaturas a deputado estadual no Rio Grande do Sul em 2026: registros do TSE, histórico eleitoral, atuação documentada, redes declaradas e fontes.'
    soup.title.string=title
    for meta in soup.select('meta'):
        key=meta.get('name',meta.get('property',''))
        if key in ('description','og:description','twitter:description'):meta['content']=description
        if key in ('og:title','twitter:title'):meta['content']=title
        if key=='og:url':meta['content']=CANONICAL
        if key in ('og:image','twitter:image'):meta['content']=CANONICAL+'assets/og-rs-estaduais.png'
        if key in ('og:image:alt','twitter:image:alt'):meta['content']='Esquerda em foco — Rio Grande do Sul — Deputados estaduais 2026'
    soup.select_one('link[rel="canonical"]')['href']=CANONICAL
    soup.select_one('link[rel="manifest"]')['href']='site.webmanifest'
    soup.select_one('link[rel="icon"]')['href']='favicon.svg'
    soup.select_one('.site-nav__edition').string='RS · Estaduais · 2026'
    soup.select_one('h1.title').string='Rio Grande do Sul'
    office=soup.select_one('.office-title')
    if office:office.string='Deputado(a) Estadual'
    issue=soup.select_one('.issue')
    if issue:issue.string='Eleições 2026 · Caderno eleitoral independente'
    soup.select_one('.dek').string='Nomes, trajetórias e pautas das candidaturas reunidas neste levantamento. Cada ficha traz suas fontes para que você possa conferir as informações.'
    r.sethtml(soup.select_one('.meta'),f'<div><b>{len(records)}</b><span>registros no recorte</span></div><div><b>{len(counts):02}</b><span>partidos representados</span></div><div><b>{mandate:02}</b><span>mandatos confirmados</span></div><div><b>{previous}</b><span>históricos anteriores</span></div>')
    soup.select_one('.rs-date').string='Consulta de '+datetime.fromisoformat(snapshot).strftime('%d/%m/%Y')+' · '+ ' · '.join(str(n)+' '+('deferidos' if st=='Deferido' else str(st).lower()) for st,n in sorted(statuses.items()))
    nav=soup.select_one('.party-nav');nav.clear()
    for party in sorted(counts,key=r.norm):nav.append(BeautifulSoup(f'<a data-nav-party="{r.esc(party)}" href="#partido-{r.norm(party)}"><span>{r.esc(party)}</span><small>{counts[party]:02}</small></a>','html.parser').a)
    for section in soup.select('.party-section'):section.decompose()
    content=soup.select_one('.content')
    for index,party in enumerate(sorted(counts,key=r.norm)):
        group=[c for c in records if c['party']==party]
        markup=f'<section class="party-section" data-party-section="{r.esc(party)}" id="partido-{r.norm(party)}"><span aria-hidden="true" class="v28-party-bg v28-party-bg-{index%3+1}"></span><header class="party-header"><div aria-hidden="true" class="party-mark"></div><div><p class="section-kicker">Partido</p><h2>{r.esc(party)}</h2></div><p class="party-count">{len(group)} registros</p><span aria-hidden="true" class="v28-party-divider"></span></header><div class="candidate-list">'+''.join(card(c,icons,r) for c in group)+'</div></section>'
        content.append(BeautifulSoup(markup,'html.parser').section)
    filters=soup.select_one('#stateFilters')
    if filters:filters.decompose()
    filter_html='<div id="stateFilters" class="rs-filter-grid"><label>Partido<select id="partyFilter"><option value="">Todos os partidos do recorte</option>'+''.join('<option value="'+r.esc(p)+'">'+r.esc(p)+'</option>' for p in sorted(counts,key=r.norm))+'</select></label><label>Situação na consulta<select id="statusFilter"><option value="">Todas as situações</option>'+''.join('<option value="'+r.esc(s)+'">'+r.esc(s)+'</option>' for s in sorted(statuses))+'</select></label><label>Histórico vinculado<select id="historyFilter"><option value="">Todos os registros</option><option value="true">Com eleição anterior vinculada</option><option value="false">Sem eleição anterior vinculada</option></select></label><button type="button" id="clearFilters">Limpar filtros</button></div>'
    soup.select_one('.toolbar-wrap').append(BeautifulSoup(filter_html,'html.parser'))
    search=soup.select_one('#searchInput')
    search['placeholder']='Busque nome, número, partido, ocupação ou pauta'
    soup.select_one('#resultCount').string=f'{len(records)} resultados'
    scope=', '.join(manifest['scope']['parties'])
    empties=', '.join(manifest['empty_parties']) or 'nenhuma'
    about=f'<p>Este caderno reúne <strong>{len(records)} registros</strong> para deputado estadual no Rio Grande do Sul em 2026. O arquivo oficial contém {manifest["all_rs_state_count"]} registros para o cargo no estado; esta página cobre o recorte partidário indicado abaixo, não o universo inteiro.</p><p>O recorte é o mesmo da frente RS/federais: <strong>{r.esc(scope)}</strong>. Siglas do recorte sem registro na extração: {r.esc(empties)}. A presença ou ausência nesta lista não constitui avaliação individual ou recomendação de voto.</p><p>Os {checked} registros foram conciliados com as fichas individuais do DivulgaCand. A situação eleitoral é datada e pode mudar. Registros que venham a ter renúncia, indeferimento ou outra situação não devem ser apagados silenciosamente do histórico.</p><p>Há {previous} candidaturas com eleição anterior vinculada pelo TSE, {mandate} cargos eletivos atuais confirmados por fontes institucionais e {agendas} sínteses de pautas ou temas documentados. Atos institucionais específicos estão registrados em {activities} fichas. As demais lacunas aparecem nas próprias fichas; ausência de informação não significa ausência de atuação.</p><p>Cadastros e fotos provêm do TSE. Textos de campanha são tratados como declarações; ações institucionais e resultados eleitorais permanecem separados. Uma página encontrada não é, por si só, uma pauta verificada.</p>'
    r.sethtml(soup.select_one('#sobre-levantamento .overview-toggle-body'),'<div class="rs-overview-copy">'+about+'</div>')
    r.sethtml(soup.select_one('#criterio-eleitoral .method-toggle-body'),'<div class="method-toggle-intro"><p>Registro, resultado eleitoral, exercício de mandato e proposta são informações diferentes. Cada uma exige sua própria fonte.</p></div><div class="method-toggle-grid"><div><p class="eyebrow">Cadastro e situação</p><p>O número identifica a candidatura no pleito. A situação aparece com a data da consulta ao TSE. Confira a ficha oficial para alterações posteriores.</p></div><div><p class="eyebrow">Histórico e votos</p><p>O TSE vincula candidaturas anteriores pelo identificador eleitoral. Uma eleição anterior não comprova mandato atual. Votos nominais conferidos indicam ano e turno; valor ausente não significa zero. Totais apenas do RS não são apresentados como totais nacionais.</p></div><div><p class="eyebrow">Pautas e atuação</p><p>Declarações da candidatura e atos legislativos são identificados separadamente. Não presumimos pautas individuais com base no partido, na ocupação ou em um link de rede social. Não atribuímos pontuação nem fazemos previsões eleitorais.</p></div></div><div class="method-toggle-note"><p>A ordem visual muda diariamente por rotação determinística, conforme o fuso de São Paulo, sem alterar os dados ou produzir classificação.</p></div>')
    sources=[('Cadastro oficial','UF RS, cargo 7, eleição 2026. Cada registro do recorte tem identificador, número e fonte individual.',TSE,'TSE · candidaturas 2026'),('Situação e histórico','Situações são fotografias da consulta. Históricos vinculados não equivalem a mandatos exercidos.',TSE,'TSE · arquivos e metodologia'),('Atuação estadual','Perfis, proposições e registros institucionais da Assembleia Legislativa são consultados para confirmar atos e mandatos.', 'https://ww4.al.rs.gov.br/deputados','Assembleia Legislativa do RS'),('Endereços declarados','Links vêm dos registros eleitorais. Endereços malformados não são adivinhados; restrições de leitura não são contornadas.',TSE,'TSE · redes declaradas'),('Fotos e cartografia','Retratos provêm do pacote oficial do TSE. O mapa estadual reutiliza a malha do IBGE; nenhum retrato é gerado.', 'https://servicodados.ibge.gov.br/api/docs/malhas?versao=3','IBGE · malhas'),('Cobertura desta edição','Os dados estruturados e o relatório distinguem cadastro conciliado de pesquisa temática concluída. Lacunas e erros de acesso permanecem registrados.','cobertura.json','Relatório de cobertura')]
    source_cards=''.join('<article><p class="eyebrow">'+r.esc(name)+'</p><p>'+r.esc(text)+'</p>'+r.link(address,r.esc(label)+' ↗','source-link')+'</article>' for name,text,address,label in sources)
    r.sethtml(soup.select_one('#fontes'),'<div class="sources-heading"><div><p class="section-kicker">Fontes e critérios</p><h2>O caminho até cada informação</h2></div><p class="sources-dek">Dados consultados em '+r.esc(snapshot)+'. As referências individuais acompanham cada ficha.</p></div><div class="sources-grid">'+source_cards+'</div><p class="rs-data-links"><a href="dados.json" download>Dados em JSON</a> · <a href="candidaturas.csv" download>Cadastro em CSV</a> · <a href="fontes.json">Proveniência e datas</a> · <a href="cobertura.json">Cobertura e lacunas</a></p>')
    for script in soup.select('script'):script.decompose()
    js=soup.new_tag('script',src='assets/app.js',defer=True);soup.body.append(js)
    style=soup.new_tag('style',id='rs-state-only')
    style.string='''[hidden]{display:none!important}.rs-filter-grid{display:grid;grid-template-columns:1.15fr 1fr 1.3fr auto;gap:12px;padding:10px 0 14px;align-items:end}.rs-filter-grid label{font:600 .72rem/1.4 var(--sans, sans-serif);display:flex;flex-direction:column;gap:5px;min-width:0}.rs-filter-grid select,.rs-filter-grid button{font:inherit;min-height:44px;max-width:100%;min-width:0;border:1px solid var(--rule);border-radius:7px;background:var(--paper-hi);color:var(--ink);padding:8px}.rs-filter-grid button{cursor:pointer;font-size:.75rem}.rs-filter-grid select{width:100%}.rs-activity{margin-top:18px;padding-top:12px;border-top:1px solid var(--rule);font-size:.88rem;line-height:1.6}.rs-overview-copy p{margin:0 0 1rem}.candidate .identity-copy,.candidate-copy,.candidate-links,.career-cell{min-width:0}.candidate{scroll-margin-top:190px}.party-section{scroll-margin-top:190px;overflow:clip}.candidate-photo{object-fit:cover}.rs-status{white-space:normal}.rs-history-links{white-space:normal}.rs-filter-grid :focus-visible{outline:3px solid #647b59;outline-offset:3px}@media(max-width:760px){.rs-filter-grid{grid-template-columns:1fr 1fr;gap:9px}.rs-filter-grid label:last-of-type{grid-column:1}.rs-filter-grid button{width:100%}.candidate,.party-section{scroll-margin-top:270px}.site-nav__edition{font-size:.62rem}.toolbar-wrap{position:relative!important;top:auto!important}.candidate,.party-section{scroll-margin-top:80px}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto!important}*,*::before,*::after{animation:none!important;transition:none!important}}'''
    soup.head.append(style)
    ld=soup.new_tag('script',type='application/ld+json')
    ld.string=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','@id':CANONICAL+'#webpage','url':CANONICAL,'name':title,'description':description,'inLanguage':'pt-BR','dateModified':snapshot,'spatialCoverage':{'@type':'Place','name':'Rio Grande do Sul, Brasil'},'mainEntity':{'@type':'ItemList','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(records),'name':'Candidaturas a deputado estadual no RS — recorte documentado','itemListElement':[{'@type':'Person','name':c['name'],'identifier':c['id'],'url':CANONICAL+'#candidato-'+c['id'],'affiliation':{'@type':'Organization','name':c['party']}} for c in records]}},ensure_ascii=False).replace('</','<\/')
    soup.head.append(ld)
    text=str(soup).replace('viewbox=','viewBox=')
    (DEST/'index.html').write_text(text,encoding='utf-8')
    shutil.copyfile(ROOT/'favicon.svg',DEST/'favicon.svg')
    shutil.copyfile(ROOT/'tools/rs-estaduais/runtime.js',DEST/'assets/app.js')
    save(DEST/'site.webmanifest',{'name':'Esquerda em foco · Estaduais RS','short_name':'Estaduais RS','lang':'pt-BR','start_url':'./','scope':'./','display':'browser','background_color':'#f2eadf','theme_color':'#f2eadf','icons':[{'src':'favicon.svg','sizes':'any','type':'image/svg+xml'}]})
    og_image()
    data={'schema_version':1,'state':'RS','office_code':7,'election_year':2026,'as_of':snapshot,'scope_parties':manifest['scope']['parties'],'candidates':records}
    save(D/'normalized.json',data);save(DEST/'dados.json',data)
    report={'as_of':snapshot,'candidate_count':len(records),'official_universe':manifest['all_rs_state_count'],'parties':dict(sorted(counts.items())),'statuses':dict(statuses),'registration_reconciled':checked,'with_photo':sum(bool(c['photo']) for c in records),'with_previous_history':previous,'previous_history_rows':sum(h['year']<2026 for c in records for h in c['history']),'with_previous_votes':sum(any(h.get('votes') is not None for h in c['history']) for c in records),'with_verified_current_office':mandate,'with_editorial_summary':agendas,'with_documented_activity':activities,'with_declared_socials':sum(bool(c['socials']) for c in records),'with_declared_sites':sum(bool(c['sites']) for c in records),'canonical':CANONICAL,'html_sha256':hashlib.sha256(text.encode()).hexdigest(),'template_source':'rs/deputados-federais/index.html','template_sha256':hashlib.sha256(frozen).hexdigest(),'renderer_source':'tools/rs/build.py','editorial_gate':'complete' if agendas==len(records) else 'documented_gaps','editorial_gap_ids':[c['id'] for c in records if not c['pautas']],'unconfirmed_current_office_ids':[c['id'] for c in records if not c['current_office']],'notes':['Não confirmar mandato não significa afirmar que não existe.','Históricos eleitorais e biografias baseadas no TSE não substituem pesquisa de pautas individuais.','A disponibilidade de um site não equivale à validação editorial do seu conteúdo.']}
    save(A/'build-report.json',report);save(DEST/'cobertura.json',report)
    save(DEST/'fontes.json',{'official_snapshot':manifest,'reconciliation':load(A/'reconciliation.json',{}),'votes':load(A/'votes-coverage.json',{}),'individual_web_source_audit':load(A/'web-research-coverage.json',{}),'editorial':load(D/'editorial.json',{}),'institutional_offices':load(D/'offices-verified.json',{})})
    with (DEST/'candidaturas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['id','name','full_name','number','party','federation','occupation','status','status_checked_at','tse_url']
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';',quoting=csv.QUOTE_ALL,extrasaction='ignore');writer.writeheader()
        for c in records:
            safe={k:("'"+str(c[k]) if str(c.get(k) or '').startswith(('=','+','-','@','\t','\r')) else c.get(k)) for k in fields}
            writer.writerow(safe)
    (DEST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+CANONICAL+'</loc><lastmod>'+snapshot+'</lastmod></url></urlset>\n',encoding='utf-8')
    assert template.read_bytes()==frozen,'Existing federal edition must not change'
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':build()

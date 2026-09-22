"""GLOBAL-03: deterministic public entry and non-destructive edition routing.
Reads current files or an explicitly supplied pristine tree. No research fetch.
"""
from __future__ import annotations
import argparse,copy,hashlib,html,json,posixpath,re,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/global02'))
from core import validate,shell,sitemap,require,url as absolute,save,load
BASELINE='4d6ea9847f59fc6dfd52d57601b0ab19c8d3ecab'
SITE='https://selvalabs.github.io/esquerda-em-foco/'
OLD_ROUTES={'/':'/sc/deputados-federais/','/deputados-estaduais/':'/sc/deputados-estaduais/'}
E=html.escape

def sha(raw):return hashlib.sha256(raw).hexdigest()

def relative(target,page):
    t=urlsplit(target)
    if t.scheme or target.startswith('//') or not t.path:return target
    value=posixpath.relpath(t.path.lstrip('/') or '.',posixpath.dirname(page) or '.')
    if t.path.endswith('/') and not value.endswith('/'):value+='/'
    return urlunsplit(('','',value,t.query,t.fragment))

def asset(path,page):return relative('/'+path,page)+'?v='+sha((ROOT/path).read_bytes())[:12]
def page_url(base,path):return absolute(base,path)
def public_editions(reg):return [e for e in reg['editions'] if e['publication_status']=='published']
def state_items(reg,code):return [e for e in reg['editions'] if e['state']==code]

def global_parts(reg,page,edition_id=None):
    soup=BeautifulSoup(shell(reg,SITE,edition_id,'next'),'html.parser')
    menu=soup.select_one('.eef-edition-menu');menu['id']='global-edition-menu';menu['data-global03']='menu'
    menu.summary.clear();menu.summary.append('Edições');menu.summary['aria-label']='Escolher estado e cargo'
    menu.summary.append(BeautifulSoup('<span class="eef-chevron" aria-hidden="true">⌄</span>','html.parser').span)
    for a in menu.select('a[href]'):a['href']=relative('/'+a['href'].removeprefix(SITE),page)
    crumbs=soup.select_one('.eef-breadcrumb');crumbs['data-global03']='breadcrumbs'
    for a in crumbs.select('a[href]'):a['href']=relative('/'+a['href'].removeprefix(SITE),page)
    return str(menu),str(crumbs)

def navigation(reg,page,state=None):
    menu,_=global_parts(reg,page)
    links=''.join(f'<a href="{E(relative(p,page))}">{label}</a>' for p,label in [('/#global-estados','Estados'),('/#global-metodologia','Como pesquisamos'),('/#global-sobre','Sobre')])
    return f'''<a class="global-skip" href="#global-conteudo">Ir para o conteúdo</a><header class="global-nav"><div class="global-nav-inner"><a class="global-brand" href="{E(relative('/',page))}" aria-label="Esquerda em foco — início"><span class="global-mark" aria-hidden="true"><i></i><i></i><i></i></span><span>Esquerda em foco</span></a><nav class="global-links" aria-label="Navegação principal">{links}</nav>{menu}</div></header>'''

def footer(page):
    return f'''<footer class="global-footer"><div><a class="global-footer-name" href="{relative('/',page)}">Esquerda em foco</a><p>Um caderno de consulta, com fontes para continuar a leitura.</p></div><div class="global-footer-links"><a href="{relative('/#global-metodologia',page)}">Critérios e fontes</a><a href="{relative('/#global-estados',page)}">Todas as edições</a><a href="https://github.com/selvalabs/esquerda-em-foco">Código e registros do projeto ↗</a></div><p class="global-footer-note">As datas da pesquisa acompanham cada edição. A navegação não atualiza os dados eleitorais.</p></footer>'''

def ld_for_page(base,path,title,description,reg,state=None):
    webpage={'@type':'CollectionPage','@id':page_url(base,path)+'#webpage','url':page_url(base,path),'name':title,'description':description,'inLanguage':'pt-BR','isPartOf':{'@id':base+'#website'}}
    if state:
        webpage['breadcrumb']={'@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Início','item':base},{'@type':'ListItem','position':2,'name':state['name'],'item':page_url(base,path)}]}
        items=[{'@type':'WebPage','name':e['office_label']+' · '+state['name'],'url':page_url(base,e['canonical_path'])} for e in state_items(reg,state['code']) if e['publication_status']=='published']
    else:items=[{'@type':'WebPage','name':s['name'],'url':page_url(base,s['path'])} for s in reg['states']]
    webpage['mainEntity']={'@type':'ItemList','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(items),'itemListElement':items}
    return {'@context':'https://schema.org','@graph':[{'@type':'WebSite','@id':base+'#website','url':base,'name':'Esquerda em foco','inLanguage':'pt-BR'},webpage]}

def document(reg,page,path,title,description,content,base,state=None,bridge=False,robots='index,follow'):
    graph=ld_for_page(base,path,title,description,reg,state);bridge_html=''
    if bridge:
        fixtures=load(ROOT/'config/legacy-sc-links.json')
        payload=json.dumps(fixtures,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
        bridge_html=f'<script type="application/json" id="global-legacy-data">{payload}</script><script defer src="{asset("assets/global/core.js",page)}"></script><script defer src="{asset("assets/global/legacy-bridge.js",page)}"></script>'
    graph_text=json.dumps(graph,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    return f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light"><title>{E(title)}</title><meta name="description" content="{E(description,quote=True)}"><meta name="robots" content="{robots}"><meta name="theme-color" content="#f3eadc"><link rel="canonical" href="{page_url(base,path)}"><link rel="icon" href="{relative('/favicon.svg',page)}" type="image/svg+xml"><link rel="manifest" href="{relative('/site.webmanifest',page)}"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Esquerda em foco"><meta property="og:title" content="{E(title,quote=True)}"><meta property="og:description" content="{E(description,quote=True)}"><meta property="og:url" content="{page_url(base,path)}"><meta property="og:image" content="{base}assets/seo/global-home.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Esquerda em foco — estados, candidaturas e fontes — 2026"><meta name="twitter:card" content="summary_large_image"><link rel="stylesheet" href="{asset('assets/global/home.css',page)}"><link rel="stylesheet" href="{asset('assets/global/navigation.css',page)}"><script type="application/ld+json">{graph_text}</script><script defer src="{asset('assets/global/navigation.js',page)}"></script>{bridge_html}</head><body class="global-page">{navigation(reg,page,state)}{content}{footer(page)}</body></html>\n'''

def office_links(reg,state,page):
    items=[]
    for e in state_items(reg,state['code']):
        if e['publication_status']=='published':items.append(f'<a class="global-office-link" href="{relative(e["canonical_path"],page)}"><span>{E(e["office_label"])}</span><span aria-hidden="true">↗</span></a>')
        else:items.append(f'<p class="global-office-pending"><span>{E(e["office_label"])}</span><span>Em preparação</span></p>')
    return ''.join(items)

def home(reg,base):
    page='index.html';cards=[]
    for s in sorted(reg['states'],key=lambda s:s['name']):
        n=len([e for e in state_items(reg,s['code']) if e['publication_status']=='published'])
        cards.append(f'''<article class="global-state" id="global-estado-{s['code'].lower()}"><div class="global-state-heading"><span class="global-uf" aria-hidden="true">{s['code']}</span><div><p class="global-kicker">{n} {'edição disponível' if n==1 else 'edições disponíveis'}</p><h3><a href="{relative(s['path'],page)}">{E(s['name'])}</a></h3></div></div><div class="global-office-list">{office_links(reg,s,page)}</div><a class="global-state-context" href="{relative(s['path'],page)}">Conheça esta edição <span aria-hidden="true">→</span></a></article>''')
    parties=' · '.join(load(ROOT/'config/party-scope-2026.json')['parties'])
    content=f'''<main id="global-conteudo" class="global-main">
<section class="global-hero" aria-labelledby="global-title"><div class="global-hero-title"><p class="global-kicker">Caderno eleitoral <span aria-hidden="true">/</span> Eleições 2026</p><h1 id="global-title">Esquerda<br><em>em foco.</em></h1><p class="global-hero-caption">Candidaturas, trajetórias e fontes para consulta.</p></div><div class="global-hero-intro"><span class="global-edition-stamp" aria-hidden="true">2026</span><h2>Conhecer uma candidatura<br>pede mais do que um nome.</h2><p>Aqui você encontra cadastros eleitorais, trajetórias e posições documentadas — com as fontes por perto para continuar a leitura.</p><a class="global-button" href="#global-estados">Escolher um estado <span aria-hidden="true">↓</span></a><p class="global-small">Um recorte de partidos, com pesquisa em andamento.<br><a href="#global-metodologia">Entenda os critérios do projeto.</a></p></div></section>
<div class="global-coverage-line"><span><b>{len(reg['states'])}</b> estados</span><span><b>{len(public_editions(reg))}</b> edições disponíveis</span><p>A pesquisa continua. As fontes e as lacunas acompanham cada ficha.</p></div>
<section id="global-estados" class="global-section" aria-labelledby="global-estados-title"><div class="global-section-heading"><div><p class="global-kicker">Por onde começar</p><h2 id="global-estados-title">Escolha o estado.<br>Depois, o cargo.</h2></div><p>A busca por nome e os filtros ficam dentro de cada edição. Assim, você consulta candidaturas do mesmo estado e cargo.</p></div><div class="global-state-grid">{''.join(cards)}</div><p class="global-scope-note">Seu estado ainda não aparece? O levantamento está em construção. Esta página mostra somente as frentes que já têm uma edição disponível.</p></section>
<section class="global-reading global-section" aria-labelledby="global-reading-title"><div><p class="global-kicker">Dentro do caderno</p><h2 id="global-reading-title">Da ficha à fonte.</h2><p>O cadastro é o ponto de partida. Quando há documentação individual, a leitura segue pela trajetória, pelas posições públicas e pela atuação registrada.</p><a class="global-text-link" href="#global-metodologia">Veja como o levantamento é feito <span aria-hidden="true">→</span></a></div><div class="global-reading-notes"><article><span aria-hidden="true">01</span><div><h3>Quem está na página</h3><p>Nome, partido e situação do registro aparecem no contexto da edição e da data consultada.</p></div></article><article><span aria-hidden="true">02</span><div><h3>O que está documentado</h3><p>Uma declaração, uma proposta e um ato já registrado não contam a mesma história. O contexto ajuda a distinguir essas informações.</p></div></article><article><span aria-hidden="true">03</span><div><h3>Onde conferir</h3><p>As referências acompanham as fichas. Quando falta documentação, essa lacuna permanece visível.</p></div></article></div></section>
<section id="global-metodologia" class="global-method global-section" aria-labelledby="global-method-title"><div class="global-section-heading"><div><p class="global-kicker">Critérios e transparência</p><h2 id="global-method-title">Como pesquisamos.</h2></div><p>O projeto organiza informações para consulta. Não atribui notas, afinidade política ou recomendações às candidaturas.</p></div><div class="global-method-grid"><article><h3>Um recorte explícito</h3><p>O levantamento usa uma lista editorial de partidos, e não pretende representar todas as candidaturas ou esgotar as definições do campo da esquerda.</p><details><summary>Quais partidos estão no recorte?</summary><p class="global-party-scope">{E(parties)}</p><p>A presença de uma sigla no recorte não atribui posições a seus integrantes. A lista de registros pode variar por estado e cargo.</p><a href="config/party-scope-2026.json">Consultar a configuração do recorte ↗</a></details></article><article><h3>Fontes com contexto</h3><p>O cadastro eleitoral parte das fontes do TSE. A pesquisa individual usa documentos públicos, canais declarados, entrevistas e registros institucionais, conforme o material localizado.</p><p><a href="https://dadosabertos.tse.jus.br/dataset/candidatos-2026">Dados abertos do TSE ↗</a> <span aria-hidden="true">·</span> <a href="https://divulgacandcontas.tse.jus.br/divulga/">DivulgaCandContas ↗</a></p></article><article><h3>Ausência não é uma posição</h3><p>Uma ficha com menos documentação não indica menos propostas, nem oposição a um tema. A cobertura varia e a pesquisa ainda tem pendências.</p><p>Os filtros mostram o recorte documentado de cada edição. A explicação do próprio filtro informa o que ele considera.</p></article><article><h3>Datas e escolhas preservadas</h3><p>Cada edição mantém as datas das fontes e as limitações do levantamento. Uma atualização de navegação não significa uma nova consulta eleitoral.</p><p>Não é preciso criar uma conta. A home não salva o estado escolhido nem envia sua navegação entre edições a um serviço de métricas.</p></article></div></section>
<section id="global-sobre" class="global-about global-section"><div><p class="global-kicker">Sobre o projeto</p><h2>Um caderno aberto<br>à consulta.</h2></div><div><p>O Esquerda em foco reúne frentes de pesquisa por estado e cargo. Esta entrada geral aproxima as edições sem apagar seus recortes, suas fontes ou o trabalho que ainda falta fazer.</p><p>Os registros de desenvolvimento e as decisões sobre o levantamento ficam no repositório. As informações eleitorais devem ser lidas junto das fontes e das datas indicadas nas fichas.</p><a class="global-text-link" href="https://github.com/selvalabs/esquerda-em-foco">Acompanhar os registros do projeto <span aria-hidden="true">↗</span></a></div></section></main>'''
    return document(reg,page,'/','Esquerda em foco | Candidaturas, trajetórias e fontes — 2026','Consulte as edições de Santa Catarina, Rio Grande do Sul, Paraná e São Paulo: candidaturas, trajetórias, posições documentadas e fontes. Pesquisa em andamento.',content,base,bridge=True)

def human_date(value):
    if not value:return None
    m=re.match(r'^(\d{4})-(\d{2})-(\d{2})',value)
    return f'{m[3]}/{m[2]}/{m[1]}' if m else None

def hub(reg,state,base):
    page=state['path'].lstrip('/')+'index.html';items=[]
    for e in state_items(reg,state['code']):
        available=e['publication_status']=='published';d=human_date(e['snapshot'].get('electoral_data',{}).get('as_of'))
        stamp=f'Referência do cadastro: {d}.' if d else 'Datas de consulta e fontes informadas nas fichas.'
        if available:items.append(f'''<article class="global-office-card"><p class="global-kicker">Edição disponível <span aria-hidden="true">/</span> {e['election_year']}</p><h2>{E(e['office_label'])}</h2><p>Consulte os registros, use a busca da edição e acompanhe a documentação de cada candidatura.</p><p class="global-research-note"><span aria-hidden="true">○</span> Pesquisa documental em andamento.</p><a class="global-button" href="{relative(e['canonical_path'],page)}">Abrir edição <span aria-hidden="true">→</span></a><p class="global-small">{stamp}<br>Esta é uma referência datada, não uma atualização em tempo real.</p></article>''')
        else:items.append(f'''<article class="global-office-card global-office-card--pending"><p class="global-kicker">Em preparação</p><h2>{E(e['office_label'])}</h2><p>Esta frente ainda não está disponível para consulta pública. A pesquisa e a revisão seguem em uma etapa separada.</p><p class="global-research-note">O acesso será incluído quando a edição for publicada.</p></article>''')
    content=f'''<main id="global-conteudo" class="global-main"><nav class="global-hub-crumb" aria-label="Localização"><a href="{relative('/',page)}">Início</a><span aria-hidden="true">/</span><span aria-current="page">{E(state['name'])}</span></nav><header class="global-hub-hero"><div><p class="global-kicker">Eleições 2026 <span aria-hidden="true">/</span> {state['code']}</p><h1>{E(state['name'])}</h1></div><p>Escolha o cargo para entrar na edição.<br>Os cadastros e as fontes permanecem separados, com seus próprios contextos de pesquisa.</p></header><div class="global-office-cards">{''.join(items)}</div><section class="global-hub-note"><h2>Antes de consultar</h2><p>As páginas reúnem registros do recorte editorial do projeto, incluindo situações eleitorais diferentes. Estar na lista não equivale a ter registro deferido, e uma lacuna na pesquisa não significa ausência de propostas.</p><a href="{relative('/#global-metodologia',page)}">Conheça os critérios e as fontes <span aria-hidden="true">→</span></a></section><a class="global-back" href="{relative('/#global-estados',page)}">← Ver outros estados</a></main>'''
    return document(reg,page,state['path'],state['name']+' · Edições 2026 | Esquerda em foco','Escolha o cargo e consulte as edições de '+state['name']+': registros eleitorais, trajetórias e documentação individual com fontes.',content,base,state)

def content_signature(soup):
    return [{'id':c['id'],'text':c.get_text(' ',strip=True),'data':{k:v for k,v in c.attrs.items() if k.startswith('data-')},'external':[(a['href'],a.get_text(' ',strip=True)) for a in c.select('a[href]') if urlsplit(a['href']).scheme and not a['href'].startswith(SITE)]} for c in soup.select('article.candidate')]

def relocate(value,source,page,*,page_link=False):
    if not value or value.startswith(('#','//','data:','mailto:','tel:')):return value
    p=urlsplit(value)
    if p.scheme:
        if not value.startswith(SITE):return value
        logical='/'+value[len(SITE):].split('?',1)[0].split('#',1)[0]
    else:
        logical=posixpath.normpath('/'+posixpath.join(posixpath.dirname(source),p.path))
        if p.path.endswith('/') and logical!='/':logical+='/'
    if logical.endswith('/index.html'):logical=logical[:-10]
    if page_link and logical in OLD_ROUTES:logical=OLD_ROUTES[logical]
    return relative(urlunsplit(('','',logical,p.query,p.fragment)),page)

def meta_relocate(value,old_path,new_path,base):
    if isinstance(value,list):return [meta_relocate(v,old_path,new_path,base) for v in value]
    if isinstance(value,dict):
        if value.get('@type')=='WebSite':
            out=copy.deepcopy(value);out.update({'@id':base+'#website','url':base});return out
        return {k:(base+'#website' if k=='@id' and isinstance(v,str) and v==SITE+'#website' else meta_relocate(v,old_path,new_path,base)) for k,v in value.items()}
    if isinstance(value,str) and value.startswith(SITE):
        p=urlsplit(value[len(SITE):]);logical='/'+p.path
        if logical==old_path or logical==old_path+'index.html':logical=new_path
        return base+logical.lstrip('/')+('?' + p.query if p.query else '')+('#'+p.fragment if p.fragment else '')
    return value

def edition_page(raw,e,reg,source,page,base):
    soup=BeautifulSoup(raw,'html.parser');signature=content_signature(soup)
    scripts_before=[n.get_text() for n in soup.select('script:not([src])') if n.get('type') not in ('application/ld+json','application/json')]
    for n in soup.select('[data-global03]'):n.decompose()
    if source!=page or not soup.body.has_attr('data-global03-edition'):
        for n in soup.select('[href],[src],[poster]'):
            for key in ['href','src','poster']:
                if n.has_attr(key):n[key]=relocate(n[key],source,page,page_link=n.name=='a')
        for style in soup.select('style,[style]'):
            attr='style' if style.has_attr('style') else None;text=style[attr] if attr else style.get_text()
            text=re.sub(r'url\(([\'"]?)([^)\'\"]+)\1\)',lambda m:m[0] if m[2].startswith(('data:','http:','https:','#')) else 'url("'+relocate(m[2],source,page)+'")',text)
            if attr:style[attr]=text
            else:style.string=text
    soup.body['data-global03-edition']=e['edition_id'];classes=soup.body.get('class',[])
    if 'eef-global-edition' not in classes:classes.append('eef-global-edition')
    soup.body['class']=classes
    nav=soup.select_one('#siteNav');inner=nav.select_one('.site-nav__inner,.nav-inner');brand=inner.select_one('.site-nav__brand,.brand')
    brand['href']=relative('/',page);brand['aria-label']='Esquerda em foco — início geral'
    menu,crumb=global_parts(reg,page,e['edition_id'])
    for n in soup.select('.pr-editions,.editions'):
        if n.get('id'):
            n.clear();a=soup.new_tag('a',href=relative('/#global-estados',page));a.string='Ver outros estados e cargos →';n.append(a)
        else:n.decompose()
    for n in inner.select('a.edition-sp-link'):n.decompose()
    local=inner.select_one('#siteNavLinks')
    for a in local.select('a[href]'):
        if a.get_text(strip=True)=='Início':a.string='Topo da edição';a['href']='#topo'
    general=soup.new_tag('a',href=relative('/#global-metodologia',page));general.string='Critérios do projeto';general['data-global03']='method-link';local.append(general)
    brand.insert_after(BeautifulSoup(menu,'html.parser').details);nav.insert_after(BeautifulSoup(crumb,'html.parser').nav)
    css=soup.new_tag('link',rel='stylesheet',href=asset('assets/global/navigation.css',page));css['data-global03']='css';soup.head.append(css)
    js=soup.new_tag('script',src=asset('assets/global/navigation.js',page),defer='');js['data-global03']='script';soup.body.append(js)
    for n in soup.select('link[rel=canonical]'):n['href']=page_url(base,e['canonical_path'])
    for n in soup.select('meta[property="og:url"]'):n['content']=page_url(base,e['canonical_path'])
    for n in soup.select('meta[name=robots]'):n['content']='index,follow'
    old_path='/' if source=='index.html' else '/'+posixpath.dirname(source)+'/'
    for n in soup.select('script[type="application/ld+json"]'):
        graph=meta_relocate(json.loads(n.string),old_path,e['canonical_path'],base)
        if graph.get('@type')=='CollectionPage':
            graph['isPartOf']={'@id':base+'#website'};graph['breadcrumb']={'@id':page_url(base,e['canonical_path'])+'#breadcrumb'}
        for g in graph.get('@graph',[]):
            if g.get('@type')=='CollectionPage':g['breadcrumb']={'@id':page_url(base,e['canonical_path'])+'#breadcrumb'}
        n.string=json.dumps(graph,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
    state=next(s for s in reg['states'] if s['code']==e['state'])
    breadcrumb={'@context':'https://schema.org','@type':'BreadcrumbList','@id':page_url(base,e['canonical_path'])+'#breadcrumb','itemListElement':[{'@type':'ListItem','position':i+1,'name':label,'item':page_url(base,p)} for i,(label,p) in enumerate([('Início','/'),(state['name'],state['path']),(e['office_label'],e['canonical_path'])])]}
    j=soup.new_tag('script',type='application/ld+json');j['data-global03']='breadcrumb-data';j.string=json.dumps(breadcrumb,ensure_ascii=False,separators=(',',':'));soup.head.append(j)
    require(signature==content_signature(soup),'Candidate semantic content changed: '+e['edition_id'])
    require(scripts_before==[n.get_text() for n in soup.select('script:not([src])') if n.get('type') not in ('application/ld+json','application/json')],'Inline application code changed')
    return str(soup).replace('viewbox=','viewBox=').rstrip()+'\n'

def alias(reg,base):
    page='deputados-estaduais/index.html';target='/sc/deputados-estaduais/'
    content=f'<main id="global-conteudo" class="global-main global-alias"><p class="global-kicker">Santa Catarina · Deputados estaduais</p><h1>A edição está em um novo endereço.</h1><p>As fichas e suas fontes continuam disponíveis.</p><a id="global-alias-target" class="global-button" href="{relative(target,page)}">Abrir a edição →</a><script defer src="{asset("assets/global/legacy-bridge.js",page)}"></script></main>'
    return document(reg,page,target,'Novo endereço · SC estaduais | Esquerda em foco','A edição de Santa Catarina está disponível no novo endereço.',content,base,robots='noindex,follow')

def not_found(reg,base):
    content='<main id="global-conteudo" class="global-main global-alias"><p class="global-kicker">Página não encontrada</p><h1>Vamos voltar ao caderno.</h1><p>O endereço pode ter mudado. Escolha um estado no menu para encontrar a edição.</p><a class="global-button" href="'+base+'#global-estados">Ver estados e cargos →</a></main>'
    result=document(reg,'404.html','/','Página não encontrada | Esquerda em foco','Encontre uma edição do Esquerda em foco por estado e cargo.',content,base,robots='noindex,follow')
    s=BeautifulSoup(result,'html.parser');b=s.new_tag('base',href=base);s.head.insert(1,b)
    for n in s.select('link[rel=canonical],script[type="application/ld+json"]'):n.decompose()
    return str(s).rstrip()+'\n'

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,default=ROOT);parser.add_argument('--out',type=Path,default=ROOT);parser.add_argument('--base',default=SITE);args=parser.parse_args()
    source=args.source_root.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=True)
    reg=copy.deepcopy(load(source/'config/editions.json'));validate(reg)
    originals={e['edition_id']:(source/e['entrypoint']).read_text() for e in public_editions(reg)}
    inputs={e['edition_id']:e['entrypoint'] for e in public_editions(reg)}
    old_mode=reg['root_mode'];reg['root_mode']='global_home'
    for s in reg['states']:s['published']=True
    for e in public_editions(reg):
        e['current_path']=e['canonical_path'];e['entrypoint']=e['canonical_path'].lstrip('/')+'index.html'
        e['migration'].update(routes_active=True,shell_active=True);e['capabilities']['global_shell']['state']='ready'
    validate(reg);results=[]
    for e in public_editions(reg):
        key=e['edition_id'];page=e['entrypoint'];raw=originals[key];text=edition_page(raw,e,reg,inputs[key],page,args.base)
        path=out/page;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf-8')
        sig=content_signature(BeautifulSoup(raw,'html.parser'))
        results.append({'edition_id':key,'input_path':inputs[key],'output_path':page,'input_sha256':sha(raw.encode()),'output_sha256':sha(text.encode()),'cards':len(sig),'semantic_sha256':sha(json.dumps(sig,ensure_ascii=False,sort_keys=True).encode())})
    (out/'index.html').write_text(home(reg,args.base),encoding='utf-8')
    for s in reg['states']:
        p=out/s['path'].lstrip('/')/'index.html';p.parent.mkdir(parents=True,exist_ok=True);p.write_text(hub(reg,s,args.base),encoding='utf-8')
    (out/'deputados-estaduais').mkdir(exist_ok=True);(out/'deputados-estaduais/index.html').write_text(alias(reg,args.base),encoding='utf-8')
    (out/'404.html').write_text(not_found(reg,args.base),encoding='utf-8')
    (out/'sitemap.xml').write_text(sitemap(reg,args.base,'current'),encoding='utf-8')
    (out/'robots.txt').write_text('User-agent: *\nAllow: /\n\nUser-agent: OAI-SearchBot\nAllow: /\n\nUser-agent: PerplexityBot\nAllow: /\n\nUser-agent: GPTBot\nDisallow: /\n\nSitemap: '+args.base+'sitemap.xml\n',encoding='utf-8')
    manifest={'name':'Esquerda em foco','short_name':'Esquerda em foco','lang':'pt-BR','start_url':'./','scope':'./','display':'browser','background_color':'#f3eadc','theme_color':'#f3eadc','icons':[{'src':'favicon.svg','sizes':'any','type':'image/svg+xml'}]}
    save(out/'site.webmanifest',manifest);save(out/'config/editions.json',reg)
    if old_mode!='global_home':save(out/'data/global03/migration.json',{'schema_version':'1.0.0','baseline':BASELINE,'old_root_mode':old_mode,'new_root_mode':reg['root_mode'],'editions':results,'source_research_changed':False,'branch_only_edition_published':False,'note':'Route migration provenance. Run validation separately; a build is not evidence that browser tests passed.'})
    print(json.dumps({'built':True,'editions':len(results),'hubs':len(reg['states']),'base':args.base},ensure_ascii=False))
if __name__=='__main__':main()

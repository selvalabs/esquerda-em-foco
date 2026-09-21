"""Reproduce the homologated SC product without writing any existing public page."""
from __future__ import annotations
import base64, collections, hashlib, html, json, os, re, subprocess, unicodedata, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
from review_support import apply_editorial, enrich_records, decorate_card, finalize
BASELINE='71d123b909cdbf3d84bd1cdca89511890759d395'
BASELINE_HASH='4b7f82c4e8dc95e54ec3e3be2a9954f81d06b0edceb530e900aebe68cd2c36ea'
ROOT=Path(__file__).resolve().parents[2];DATA=ROOT/'data/rs';DOC=ROOT/'docs/rs';DEST=ROOT/'rs/deputados-federais'
SITE=os.getenv('EEFOCO_SITE_URL','https://selvalabs.github.io/esquerda-em-foco/').rstrip('/')+'/'
CANONICAL=SITE+'rs/deputados-federais/';DATE='2026-09-21'
PARTIES=['PCO','PCdoB','PDT','PSB','PSOL','PT','PV','UP']
TSE='https://dadosabertos.tse.jus.br/dataset/candidatos-2026';ARCHIVE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
SOURCES={
 'cadastro':(TSE,'TSE · cadastro de candidaturas 2026'),
 'situacao':(ARCHIVE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip','TSE · situação das candidaturas'),
 'historico':(ARCHIVE+'historico_candidatura/historico_candidatura_2026.zip','TSE · histórico vinculado de candidaturas'),
 'redes':(ARCHIVE+'consulta_cand/rede_social_candidato_2026.zip','TSE · endereços declarados'),
 'fotos':('https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_RS_div.zip','TSE · fotografias do RS')}
SOCIAL={'instagram.com':'Instagram','facebook.com':'Facebook','youtube.com':'YouTube','youtu.be':'YouTube','tiktok.com':'TikTok','twitter.com':'X','x.com':'X','threads.net':'Threads','threads.com':'Threads','kwai.com':'Kwai','linkedin.com':'LinkedIn','flickr.com':'Flickr','wa.me':'WhatsApp','api.whatsapp.com':'WhatsApp','whatsapp.com':'WhatsApp','t.me':'Telegram','linktr.ee':'Linktree'}
def read(name,default):
 p=DATA/name
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def write(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def esc(value):return html.escape(str(value),quote=True)
def norm(value):return ''.join(c for c in unicodedata.normalize('NFD',str(value).casefold()) if unicodedata.category(c)!='Mn')
def clean(value):return '' if value is None or str(value).strip() in ('','#NE','#NULO','-1','-3','NÃO DIVULGÁVEL') else str(value).strip()
def label(value):
 text=clean(value).title();text=re.sub(r'\b(Da|Das|De|Do|Dos|E)\b',lambda m:m[0].lower(),text)
 for word in ['MLB','CNR','RS','LGBT','PCD','PT','PSOL','UP','SUS']:text=re.sub(r'\b'+word.title()+r'\b',word,text)
 return text[:1].upper()+text[1:]
def url(value):
 value=clean(value)
 if not value or any(c.isspace() for c in value):return None
 if not re.match(r'^https?://',value,re.I):value='https://'+value
 try:
  p=urllib.parse.urlsplit(value);host=(p.hostname or '').lower()
  if p.scheme.lower() not in ('http','https') or p.username is not None or p.password is not None or '@' in p.netloc:return None
  if not re.fullmatch(r'(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}',host):return None
  if host.endswith(('.local','.localhost')) or host in ('www.tiktok','www.instagram','www.facebook'):return None
  return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path or '/',p.query,''))
 except ValueError:return None

def link(href,text,cls='',**attrs):
 extra=' '.join(f'{esc(k.replace("_","-"))}="{esc(v)}"' for k,v in attrs.items())
 return f'<a href="{esc(href)}" class="{esc(cls)}" target="_blank" rel="noopener noreferrer" {extra}>{text}</a>'
def citation(key,cid=None):
 address,title=SOURCES[key]
 return link(address,esc(title)+' ↗','source-link',title=f'{title}; SQ_CANDIDATO {cid}' if cid else title)
def fragment(markup):return BeautifulSoup(markup,'html.parser')
def sethtml(node,markup):
 node.clear()
 for item in list(fragment(markup).contents):node.append(item)
def template_bytes():
 try:return subprocess.check_output(['git','show',BASELINE+':index.html'],cwd=ROOT,stderr=subprocess.DEVNULL)
 except (OSError,subprocess.CalledProcessError):
  raw=(ROOT/'index.html').read_bytes()
  if hashlib.sha256(raw).hexdigest()!=BASELINE_HASH:raise RuntimeError('Frozen SC template unavailable')
  return raw

def normalize_records():
 records=read('candidates-official.json',[]);assert records,'Official data required'
 status={r['SQ_CANDIDATO']:r for r in read('status-official.json',[])}
 histories=read('history-normalized.json',{});photos=read('photos-official.json',{});editorial=read('editorial.json',{});offices=read('offices-verified.json',{})
 social=collections.defaultdict(list)
 for r in read('social-official.json',[]):social[r.get('SQ_CANDIDATO')].append(r.get('DS_URL',''))
 output=[]
 for r in records:
  cid=r['SQ_CANDIDATO'];party=r['SG_PARTIDO'];assert r['SG_UF']=='RS' and r['ANO_ELEICAO']=='2026' and r['CD_CARGO']=='6' and party in PARTIES
  e=editorial.get(cid,{});st=status.get(cid,{})
  state=next((clean(st.get(k)) for k in ['DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CANDIDATURA','DS_SITUACAO_CANDIDATO_PLEITO','DS_SITUACAO_CANDIDATO_URNA','DS_DETALHE_SITUACAO_CAND'] if clean(st.get(k))),clean(r.get('DS_SITUACAO_CANDIDATURA')))
  networks=[];sites=[];invalid=[];seen=set()
  for declared in social[cid]:
   address=url(declared)
   if not address:invalid.append(declared);continue
   if address.rstrip('/').lower() in seen:continue
   seen.add(address.rstrip('/').lower());host=urllib.parse.urlsplit(address).hostname.removeprefix('www.')
   platform=next((name for dom,name in SOCIAL.items() if host==dom or host.endswith('.'+dom)),None)
   if platform:networks.append({'label':platform,'url':address,'source':'redes'})
   elif not any(w in host for w in ('queroapoiar','apoiar.me','apoia.se','vaquinha')):sites.append({'label':host,'url':address,'source':'redes'})
  output.append({'id':cid,'name':label(r['NM_URNA_CANDIDATO']),'official_name':r['NM_URNA_CANDIDATO'],'full_name':label(r['NM_CANDIDATO']),'number':r['NR_CANDIDATO'],'party':party,'federation':clean(r.get('NM_FEDERACAO')),'occupation':label(r.get('DS_OCUPACAO','')),'status':label(state) or None,'current_office':offices.get(cid),'history':histories.get(cid,[]),'photo':photos.get(cid),'socials':networks,'sites':sites,'invalid_declared_urls':invalid,'pautas':e.get('pautas'),'biography':e.get('biography'),'editorial_sources':e.get('sources',[]),'editorial_checked_at':e.get('checked_at'),'tse_url':f'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/2026/20322002026/RS/{cid}','source_record':{'url':TSE,'id':cid,'generated_at':r['DT_GERACAO']+' '+r['HH_GERACAO']}})
 return sorted(enrich_records(output),key=lambda c:(norm(c['party']),norm(c['name']),c['id'])),read('manifest.json',{})

def baseline_card(c,icons):
 cid=c['id'];name=esc(c['name']);initials=''.join(w[0] for w in c['name'].split() if len(w)>2)[:2];photo=c.get('photo');history=c['history'];current=c['current_office']
 picture=f'<img src="{esc(photo["path"])}" class="candidate-photo" width="240" height="300" loading="lazy" decoding="async" alt="Foto registrada no TSE por {name} para 2026" onerror="this.classList.add(\'is-broken\')"/>' if photo and (DEST/photo['path']).is_file() else '<span class="sr-only">Fotografia não disponível nesta edição.</span>'
 tags=[]
 if current:tags.append(f'<span class="trajectory-tag tag-current">Atual · {esc(current["label"])}</span>')
 if history:
  disputes=len({(h['year'],h['candidate_id']) for h in history})
  tags.append(f'<span class="trajectory-tag tag-pleito" title="Disputas vinculadas pelo TSE, incluindo o registro de 2026; não é número de mandatos">{disputes} disputas vinculadas · TSE</span>')
 if c['status']:tags.append(f'<span class="trajectory-tag rs-status">{esc(c["status"])}</span>')
 networks=''.join(link(s['url'],icons.get(s['label'],esc(s['label']))+f'<span class="sr-only">{esc(s["label"])} · {name}</span>','social-link social-link--icon',aria_label=s['label']+' · '+c['name'],title=s['label']+' · endereço declarado ao TSE') for s in c['socials']) or '<span class="empty">Nenhuma rede válida identificada nos endereços declarados ao TSE.</span>'
 sites=''.join(link(s['url'],'<span>'+esc(s['label'])+'</span><span aria-hidden="true">↗</span>','site-btn') for s in c['sites']) or '<span class="empty">Sem site individual identificável nos endereços declarados ao TSE.</span>'
 summary=esc(c['pautas']) if c['pautas'] else 'Síntese de pautas não documentada nesta edição. Consulte os canais declarados pela candidatura. A ausência de síntese não significa ausência de propostas.'
 refs=''.join(link(s['url'],esc(s['label'])+' ↗','source-link') for s in c['editorial_sources'])
 bio=f'<p class="rs-biography">{esc(c["biography"])}</p>' if c['biography'] else ''
 current_text=esc(current['label']) if current else 'Não confirmado nesta edição'
 current_ref=link(current['source'],'Fonte institucional ↗','source-link') if current else '<span class="empty">Ausência de confirmação não equivale à ausência de mandato.</span>'
 previous=[h for h in history if int(h.get('year',2026))<2026];latest=max(previous,key=lambda h:(int(h['year']),int(h.get('round',1))),default=None)
 latest_text='Sem disputa anterior no histórico vinculado consultado' if history else 'Histórico anterior não consolidado';votes='';result=''
 if latest:
  latest_text=f'{latest["year"]} · {label(latest.get("office", "Cargo não informado"))} · {label(latest.get("place", "RS"))}'
  if latest.get('votes') is not None:
   amount=f'{int(latest["votes"]):,}'.replace(',','.')
   votes=f'<p class="career-votes">{amount} votos nominais</p>'+link(latest['votes_source'],f'TSE · {latest["year"]} · {latest.get("round",1)}º turno ↗','source-link')
  else:votes='<p class="empty">Votação nominal ainda não conferida nesta edição.</p>'
  if latest.get('result'):result=f'<span class="result-tag">{esc(label(latest["result"]))}</span>'
 items=[]
 for h in sorted(history,key=lambda x:(int(x['year']),int(x.get('round',1))),reverse=True):
  detail=f'{h["year"]} · {label(h.get("office", "Cargo não informado"))} · {label(h.get("place", "RS"))}'
  if h.get('party'):detail+=' · '+h['party']
  if h.get('result'):detail+=' · '+label(h['result'])
  if h.get('round',1)>1:detail+=f' · {h["round"]}º turno'
  if h.get('votes') is not None:detail+=' · '+f'{int(h["votes"]):,}'.replace(',','.')+' votos nominais'
  source=h.get('profile_url') or h.get('source') or SOURCES['historico'][0]
  refs_h=link(source,'Registro ↗','source-link')
  if h.get('votes_source'):refs_h+=' '+link(h['votes_source'],'Votação ↗','source-link')
  items.append('<li>'+esc(detail)+' <span class="rs-history-links">'+refs_h+'</span></li>')
 history_html='<details class="rs-history"><summary>Histórico vinculado no TSE</summary><ul>'+''.join(items)+'</ul><p class="empty">Registros de candidaturas não comprovam, isoladamente, posse, continuidade de mandato ou atuação parlamentar. Os valores, quando conferidos, são votos nominais do turno identificado.</p>'+citation('historico',cid)+'</details>' if history else ''
 search=' '.join(str(c.get(k) or '') for k in ['name','full_name','number','party','occupation','pautas','biography'])
 return f'''<article class="candidate" id="candidato-{cid}" data-tse-id="{cid}" data-party="{esc(c['party'])}" data-search="{esc(search)}" data-current-office="{str(bool(current)).lower()}" data-has-pauta="{str(bool(c['pautas'])).lower()}" data-has-site="{str(bool(c['sites'])).lower()}">
<header class="candidate-head"><div class="identity"><figure class="candidate-portrait">{picture}<span class="portrait-fallback" aria-hidden="true">{esc(initials)}</span></figure><div class="identity-copy"><div class="number">{esc(c['number'])} <span class="rs-party-label">{esc(c['party'])}</span></div><h3>{name}</h3><div class="evidence-row trajectory-tags">{''.join(tags)}</div><p class="rs-occupation">Ocupação declarada: {esc(c['occupation']) or 'não informada'}</p></div></div></header>
<div class="candidate-body"><div class="candidate-copy"><p class="eyebrow">Pautas públicas documentadas</p><p class="pauta">{summary}</p>{bio}<div class="rs-inline-sources">{refs}</div></div><div class="candidate-links"><div><p class="eyebrow">Redes declaradas</p><div class="socials socials--icons">{networks}</div></div><div><p class="eyebrow">Sites declarados</p><div class="rs-sites">{sites}</div></div></div></div>
<div class="career-band"><div class="career-cell career-current"><p class="eyebrow">Cargo eletivo atual</p><p class="career-status {'is-current' if current else 'is-unverified'}"><span class="status-dot" aria-hidden="true"></span>{current_text}</p>{current_ref}</div><div class="career-cell career-latest"><p class="eyebrow">Última disputa anterior a 2026</p><p class="career-race">{esc(latest_text)}</p>{votes}{result}</div><div class="career-context"><p class="career-ref">Situação eleitoral no recorte: <strong>{esc(c['status']) if c['status'] else 'não confirmada'}</strong>. Consulte o registro atualizado antes de utilizar a informação.</p><div class="career-sources">{link(c['tse_url'],'Ficha no DivulgaCandContas ↗','source-link')}{citation('cadastro',cid)}{citation('situacao',cid)}{citation('redes',cid)}</div></div></div>{history_html}<div class="rs-card-footer"><span>Fonte primária · TSE · registro {cid}</span><a href="#candidato-{cid}" aria-label="Link direto para {name}">Link desta ficha</a></div></article>'''

def card(c,icons):
 return decorate_card(baseline_card(c,icons),c)

def build():
 apply_editorial()
 from prepare import run as prepare
 prepare()
 if os.getenv('GITHUB_ACTIONS')=='true' and os.getenv('EEFOCO_OFFLINE_BUILD')!='1':
  from supplement import run as supplement
  supplement();prepare()
 DEST.mkdir(parents=True,exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
 raw=template_bytes();assert hashlib.sha256(raw).hexdigest()==BASELINE_HASH
 original_sc=(ROOT/'index.html').read_bytes();soup=BeautifulSoup(raw.decode('utf-8'),'html.parser');records,manifest=normalize_records();counts=collections.Counter(c['party'] for c in records);statuses=collections.Counter(c['status'] for c in records)
 write(DATA/'normalized.json',{'schema_version':1,'state':'RS','office_code':6,'election_year':2026,'as_of':DATE,'scope_parties':PARTIES,'candidates':records})
 title='Candidatos a Deputado Federal no RS 2026 | Esquerda em foco';description='Candidaturas a deputado federal no Rio Grande do Sul em 2026: cadastro eleitoral, histórico, pautas documentadas, redes declaradas e fontes para consulta.'
 soup.title.string=title
 for meta in soup.select('meta'):
  key=meta.get('name',meta.get('property',''))
  if key in ['description','og:description','twitter:description']:meta['content']=description
  if key in ['og:title','twitter:title']:meta['content']=title
  if key=='og:url':meta['content']=CANONICAL
  if key in ['og:image','twitter:image']:meta['content']=CANONICAL+'assets/og-rs.png'
  if key in ['og:image:alt','twitter:image:alt']:meta['content']='Esquerda em foco — Rio Grande do Sul — Deputado(a) Federal 2026'
 soup.select_one('link[rel="canonical"]')['href']=CANONICAL;soup.select_one('link[rel="manifest"]')['href']='site.webmanifest';soup.select_one('link[rel="icon"]')['href']='favicon.svg'
 (DEST/'favicon.svg').write_bytes((ROOT/'favicon.svg').read_bytes())
 write(DEST/'site.webmanifest',{'name':'Esquerda em foco · RS','short_name':'Em foco · RS','lang':'pt-BR','start_url':'./','scope':'./','display':'browser','background_color':'#f2eadf','theme_color':'#f2eadf','icons':[{'src':'favicon.svg','sizes':'any','type':'image/svg+xml'}]})
 soup.select_one('.site-nav__edition').string='RS · 2026';soup.select_one('h1.title').string='Rio Grande do Sul';soup.select_one('.dek').string='Candidaturas do mesmo recorte partidário da edição de SC, reunidas por sigla e acompanhadas de fontes públicas. A presença nesta página não é recomendação de voto.'
 confirmed=sum(bool(c['current_office']) for c in records);with_history=sum(any(h['year']<2026 for h in c['history']) for c in records);editorial_count=sum(bool(c['pautas']) for c in records)
 sethtml(soup.select_one('.meta'),f'<div><b>{len(records)}</b><span>registros no recorte</span></div><div><b>{len(counts):02}</b><span>partidos representados</span></div><div><b>{confirmed:02}</b><span>mandatos confirmados</span></div><div><b>{with_history:02}</b><span>históricos anteriores</span></div>')
 stamp=soup.new_tag('p',attrs={'class':'rs-date'});stamp.string='Consulta de 21 de setembro de 2026 · '+ ' · '.join(f'{n} {s.lower()}' for s,n in sorted(statuses.items()));soup.select_one('.meta').insert_after(stamp)
 soup.select_one('#resultCount').string=f'{len(records)} resultados';nav=soup.select_one('.party-nav');nav.clear()
 for party in sorted(counts,key=norm):nav.append(fragment(f'<a data-nav-party="{esc(party)}" href="#partido-{norm(party)}" title="Ir para {esc(party)}"><span>{esc(party)}</span><small>{counts[party]:02}</small></a>').a)
 icons={}
 for a in soup.select('.social-link--icon'):
  svg=a.select_one('svg')
  if svg:icons[a.get('aria-label','').split(' ')[0]]=str(svg).replace('viewbox=','viewBox=')
 for section in soup.select('.party-section'):section.decompose()
 content=soup.select_one('.content')
 for i,party in enumerate(sorted(counts,key=norm)):
  candidates=[c for c in records if c['party']==party]
  markup=f'<section class="party-section" data-party-section="{esc(party)}" id="partido-{norm(party)}"><span aria-hidden="true" class="v28-party-bg v28-party-bg-{i%3+1}"></span><header class="party-header"><div aria-hidden="true" class="party-mark"></div><div><p class="section-kicker">Partido</p><h2>{esc(party)}</h2></div><p class="party-count">{len(candidates)} registros</p><span aria-hidden="true" class="v28-party-divider"></span></header><div class="candidate-list">'+''.join(card(c,icons) for c in candidates)+'</div></section>'
  content.append(fragment(markup).section)
 sethtml(soup.select_one('#sobre-levantamento .overview-toggle-body'),f'''<div class="overview-copy"><h2>Uma trajetória eleitoral em contexto.</h2><p>Esta edição reúne {len(records)} registros de candidatura a deputado federal pelo Rio Grande do Sul, encontrados na base oficial de 2026 para as mesmas oito siglas da edição de SC: PCdoB, PCO, PDT, PSB, PSOL, PT, PV e UP. São {len(counts)} siglas com registros nesta extração; o PCO integra o recorte, mas não tem registro para este cargo e estado no arquivo consultado.</p><p>O total inclui os registros com renúncia, identificados individualmente, e não corresponde somente às candidaturas ativas. Situações podem mudar após a consulta. Outros partidos do RS não integram este recorte; a ausência não é uma classificação ou avaliação individual.</p><p>Cadastro e fotografias foram conferidos para as {len(records)} fichas. Há {editorial_count} sínteses individuais de pautas com fonte; nas demais, a lacuna aparece explicitamente. Mandatos atuais só recebem confirmação com uma fonte institucional correspondente. Uma disputa anterior ou uma declaração de campanha não prova exercício atual.</p></div>''')
 sethtml(soup.select_one('#criterio-eleitoral .method-toggle-body'),'''<div class="method-toggle-intro"><p>Os campos da ficha tratam de informações diferentes. Um registro de candidatura não prova exercício de mandato, e uma proposta publicada não demonstra sua execução.</p></div><div class="method-toggle-grid"><div><p class="eyebrow">Cadastro e situação</p><p>O número identifica a candidatura no pleito, não uma posição nesta página. Situações eleitorais podem mudar por decisões posteriores. A ficha do DivulgaCandContas permite conferir o registro atualizado.</p></div><div><p class="eyebrow">Mandato e histórico</p><p>Cargos atuais exigem confirmação institucional. As disputas vinculadas pelo TSE não equivalem ao número de mandatos. Votos nominais, quando conferidos, são identificados por ano e turno; a ausência de valor não significa zero voto. Não calculamos cortes nem chances eleitorais.</p></div><div><p class="eyebrow">Pautas e fontes</p><p>As pautas são sínteses de documentos identificados, não notas ou avaliações. Redes e sites são endereços declarados; sua inclusão não atesta todo o conteúdo publicado. A falta de síntese nesta edição não significa falta de propostas.</p></div></div><div class="method-toggle-note"><p>Esta página não estabelece classificação de candidaturas nem prevê resultados. A rotação altera somente a ordem visual.</p></div>''')
 source_cards=''.join(f'<article><p class="eyebrow">{esc(name)}</p><p>{text}</p>{citation(key)}</article>' for key,name,text in [('cadastro','Cadastro oficial','Recorte: eleição 2026, UF RS, cargo 6 (deputado federal), nas oito siglas explicitadas em Sobre. Cada ficha informa seu identificador.'),('situacao','Situação eleitoral','A situação é um retrato do arquivo consultado. Registros com renúncia permanecem identificados, não apresentados como candidaturas ativas.'),('historico','Histórico eleitoral','Disputas vinculadas são exibidas com ano, cargo e resultado quando disponíveis. Votos conferidos têm referência própria. Não inferimos posse ou mandato atual apenas a partir de eleição anterior.'),('redes','Redes e sites declarados','Endereços são normalizados tecnicamente. Entradas incompletas ou inseguras não viram links inventados. A declaração não garante disponibilidade contínua do site.'),('fotos','Fotografias oficiais','Fotografias locais provêm do pacote oficial, associadas pelo identificador TSE. Imagens ausentes teriam iniciais como alternativa, nunca retratos gerados.')])
 sethtml(soup.select_one('#fontes'),'<div class="sources-heading"><div aria-hidden="true" class="sources-emblem"></div><div><p class="section-kicker">Fontes e critérios</p><h2>O caminho até cada informação</h2></div><p class="sources-dek">Cadastro consultado em 21 de setembro de 2026. A base e a metodologia são abertas; as referências individuais acompanham as fichas.</p></div><div class="sources-grid">'+source_cards+'<article><p class="eyebrow">Mandatos e cartografia</p><p>Mandatos federais são conferidos na Câmara dos Deputados. O contorno estadual vem da malha oficial do IBGE. Textos de candidatura são atribuídos individualmente.</p>'+link('https://www.camara.leg.br/deputados/quem-sao','Câmara dos Deputados ↗')+'<br>'+link('https://servicodados.ibge.gov.br/api/docs/malhas?versao=3','IBGE · malhas territoriais ↗')+'</article></div><p class="rs-data-links"><a href="dados.json">Base estruturada desta edição</a> · <a href="fontes.json">Proveniência e datas da coleta</a> · <a href="../../">Edição SC</a></p>')
 map_soup=BeautifulSoup((DEST/'assets/rs-ibge.svg').read_text(),'xml');svg=map_soup.svg;assert svg is not None
 svg['fill']='#d6e0d5';svg['stroke']='#486f5c';svg['stroke-width']='0.016'
 for path in svg.find_all('path'):path['fill']='#d6e0d5';path['stroke']='#486f5c';path['stroke-width']='120'
 map_uri='data:image/svg+xml;base64,'+base64.b64encode(str(svg).encode()).decode()
 style=soup.new_tag('style',attrs={'id':'rs-specific'});style.string=f'''/* Only this independent edition is styled below. */
[hidden]{{display:none!important;}}
.v28-hero-map{{background-image:url("{map_uri}")!important;aspect-ratio:1/1!important;width:min(54vw,700px)!important;top:39%!important;right:1vw!important;opacity:.28!important;}}
.rs-date,.rs-occupation,.rs-card-footer,.rs-inline-sources,.rs-data-links{{font-size:.76rem;color:var(--ink-2);line-height:1.5;}}
.rs-date{{margin:12px 0 0;}}.rs-occupation{{margin:10px 0 0;}}.rs-party-label{{margin-left:12px;}}
.rs-inline-sources,.rs-sites{{display:flex;flex-wrap:wrap;gap:8px 14px;margin-top:12px;}}
.source-link{{font-size:.73rem;overflow-wrap:anywhere;}}.rs-biography{{margin:12px 0 0;font-size:.91rem;color:var(--ink-2);}}
.rs-card-footer{{grid-column:1/-1;display:flex;flex-wrap:wrap;justify-content:space-between;gap:12px;margin-top:14px;}}
.rs-history{{grid-column:1/-1;margin-top:14px;border-top:1px solid var(--rule);padding-top:10px;font-size:.83rem;}}
.rs-history summary{{cursor:pointer;min-height:36px;display:list-item;}}.rs-history li{{margin:6px 0;overflow-wrap:anywhere;}}
.career-status.is-unverified .status-dot{{background:var(--rule);}}.candidate-portrait .portrait-fallback{{z-index:0;}}.candidate-photo{{position:relative;z-index:1;}}
.site-btn{{max-width:100%;overflow-wrap:anywhere;min-width:0;}}.site-btn span{{min-width:0;}}.rs-status{{border:1px solid var(--rule);}}
.rs-data-links{{margin-top:28px;text-align:center;}}.rs-empty-results{{padding:28px 0;font-family:var(--display);font-size:1.5rem;}}
.skip-link{{position:fixed;left:12px;top:-100px;z-index:1000;background:var(--paper-hi);padding:12px;}}.skip-link:focus{{top:12px;}}
@media(max-width:760px){{.v28-hero-map{{width:90vw!important;right:-12vw!important;top:24%!important;opacity:.20!important;}}.title-state{{max-width:10ch!important;}}.rs-card-footer{{font-size:.67rem;}}.source-link{{display:inline-block;min-height:28px;}}}}
''';soup.head.append(style)
 skip=soup.new_tag('a',href='#candidaturas',attrs={'class':'skip-link'});skip.string='Ir para candidaturas';soup.body.insert(0,skip)
 empty=soup.new_tag('p',attrs={'class':'rs-empty-results','id':'emptyResults','hidden':''});empty.string='Nenhuma candidatura encontrada. Experimente outro nome, número ou termo.';soup.select_one('#sobre-levantamento').insert_before(empty)
 for script in soup.select('script'):script.decompose()
 script=soup.new_tag('script');script.string=(ROOT/'tools/rs/runtime.js').read_text();soup.body.append(script)
 item_list={'@type':'ItemList','name':'Candidaturas do recorte editorial · Deputado Federal · RS 2026','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(records),'itemListElement':[{'@type':'Person','name':c['name'],'identifier':c['id'],'url':CANONICAL+'#candidato-'+c['id'],'affiliation':{'@type':'Organization','name':c['party']}} for c in records]}
 ld=soup.new_tag('script',type='application/ld+json');ld.string=json.dumps({'@context':'https://schema.org','@type':'CollectionPage','@id':CANONICAL+'#webpage','url':CANONICAL,'name':title,'description':description,'inLanguage':'pt-BR','dateModified':DATE,'spatialCoverage':{'@type':'Place','name':'Rio Grande do Sul, Brasil'},'mainEntity':item_list},ensure_ascii=False).replace('</','<\\/');soup.head.append(ld)
 result=str(soup).replace('viewbox=','viewBox=');(DEST/'index.html').write_text(result,encoding='utf-8')
 write(DEST/'dados.json',{'schema_version':1,'state':'RS','as_of':DATE,'scope':PARTIES,'candidates':[{k:v for k,v in c.items() if k!='invalid_declared_urls'} for c in records]})
 extra={}
 for filename in ('reconciliation.json','supplement.json'):
  if (DOC/filename).exists():extra[filename]=json.loads((DOC/filename).read_text())
 write(DEST/'fontes.json',{'official_snapshot':manifest,'verification':extra,'editorial':read('editorial.json',{}),'scope_note':'Recorte de oito siglas herdado da edição SC; não é a totalidade das candidaturas do RS.'})
 (DEST/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+esc(CANONICAL)+'</loc><lastmod>'+DATE+'</lastmod></url></urlset>\n')
 assert original_sc==(ROOT/'index.html').read_bytes(),'SC must not change'
 report={'baseline':BASELINE,'sc_sha256':hashlib.sha256(original_sc).hexdigest(),'candidate_count':len(records),'parties':dict(sorted(counts.items())),'statuses':dict(statuses),'scope_empty_parties':[p for p in PARTIES if p not in counts],'with_verified_current_office':confirmed,'with_previous_history':with_history,'with_editorial_summary':editorial_count,'with_photo':sum(bool(c['photo']) for c in records),'with_status':sum(bool(c['status']) for c in records),'with_declared_sites':sum(bool(c['sites']) for c in records),'with_declared_socials':sum(bool(c['socials']) for c in records),'invalid_declared_urls':sum(len(c['invalid_declared_urls']) for c in records),'with_previous_votes':sum(any(h.get('votes') is not None for h in c['history']) for c in records),'canonical':CANONICAL,'html_sha256':hashlib.sha256(result.encode()).hexdigest()}
 write(DOC/'build-report.json',report);print(json.dumps(report,ensure_ascii=False,indent=2))
 finalize(records)
if __name__=='__main__':build()

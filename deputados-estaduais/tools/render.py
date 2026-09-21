#!/usr/bin/env python3
"""Build only deputados-estaduais/. All existing federal files are read-only."""
from __future__ import annotations
import csv, hashlib, html, io, json, re, shutil, unicodedata
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent
DATA=ROOT/'data'; ASSETS=ROOT/'assets'; AUDIT=ROOT/'audit'
ASSETS.mkdir(exist_ok=True)
URL='https://selvalabs.github.io/esquerda-em-foco/deputados-estaduais/'
TSE='https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
RESULTS='https://resultados.tse.jus.br/oficial/app/index.html#/eleicao'
DATE='2026-09-21'; DATE_PT='21 de setembro de 2026'
PARTIES=['PCDOB','PDT','PSB','PSOL','PSTU','PT','PV','REDE','UP','PCO']
LABEL={'PCDOB':'PCdoB'}

def load(path,default=None):
 p=Path(path)
 return json.loads(p.read_text(encoding='utf-8')) if p.exists() else default

def save(path,value):
 Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def esc(value): return html.escape(str(value),quote=True)
def clean(value,default='Não informado'):
 s=str(value or '').strip()
 return default if not s or s.startswith('#') or s in ['-1','-3','-4'] else s

def norm(value): return ''.join(c for c in unicodedata.normalize('NFD',str(value).lower()) if unicodedata.category(c)!='Mn')
def title(value):
 s=clean(value).title()
 return re.sub(r'\b(Da|De|Do|Das|Dos|E)\b',lambda m:m[0].lower(),s).replace('Pcd','PCD').replace('PcdoB','PCdoB')
def number(value): return f'{int(value):,}'.replace(',','.')
def link(url,text,css=''):
 if not valid_url(url): return esc(text)
 return f'<a class="{esc(css)}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text)} ↗</a>'
def valid_url(url):
 try:
  p=urlsplit(str(url))
  return p.scheme in ['http','https'] and bool(p.hostname) and not p.username
 except ValueError: return False

def tidy_url(value):
 s=str(value).strip()
 s=re.sub(r'^HTTPS?://',lambda m:m[0].lower(),s)
 if not re.match(r'^https?://',s): return None
 try:
  p=urlsplit(s); host=(p.hostname or '').lower()
  if not host or host=='insagram.com' or host.endswith('.insagram.com'): return None
  path=p.path
  if any(h in host for h in ['instagram.com','facebook.com','tiktok.com','threads.net','threads.com','x.com','twitter.com']): path=path.lower()
  if s.upper()==str(value).strip():
   if 'youtu' not in host: path=path.lower()
  return urlunsplit((p.scheme.lower(),p.netloc.lower(),path,p.query,p.fragment))
 except ValueError: return None

def office(r): return title(r.get('DS_CARGO',''))
def place(r): return 'SC' if r.get('NM_UE')=='SANTA CATARINA' else title(r.get('NM_UE',''))
def result(r): return clean(r.get('DS_SIT_TOT_TURNO'),'Resultado não informado')
def is_elected(r): return norm(result(r)).startswith('eleit')
def history_key(r): return (r['ANO_ELEICAO'],r.get('CD_TIPO_ELEICAO',''),r['SG_UE'],r['CD_CARGO'])

federal=(REPO/'index.html').read_bytes(); before=hashlib.sha256(federal).hexdigest()
soup=BeautifulSoup(federal.decode('utf-8'),'html.parser')
css='\n'.join(s.get_text() for s in soup.find_all('style'))+'\n'+(ROOT/'ui/state.css').read_text()
(ASSETS/'site.css').write_text(css,encoding='utf-8')
shutil.copyfile(ROOT/'ui/app.js',ASSETS/'app.js')
if (REPO/'favicon.svg').exists(): shutil.copyfile(REPO/'favicon.svg',ASSETS/'favicon.svg')
universe=load(DATA/'universo-sc-2026.json',[])
raw=[r for r in universe if r['SG_PARTIDO'] in PARTIES]
raw.sort(key=lambda r:(norm(LABEL.get(r['SG_PARTIDO'],r['SG_PARTIDO'])),norm(r['NM_URNA_CANDIDATO'])))
assert raw and len({r['SQ_CANDIDATO'] for r in raw})==len(raw)
notes=load(ROOT/'editorial/perfis.json',{}).get('profiles',{})
unknown_notes=set(notes)-{r['NM_URNA_CANDIDATO'] for r in raw}
if unknown_notes: raise ValueError('Editorial names missing from TSE: '+str(unknown_notes))
all_history=load(DATA/'historico-sc-2026.json',[])
histories=defaultdict(list)
for r in all_history:
 if int(r['ANO_ELEICAO'])<2026: histories[r['SQ_CANDIDATO_ATUAL']].append(r)
for sid,rows in histories.items():
 unique={json.dumps(r,sort_keys=True):r for r in rows}
 histories[sid]=sorted(unique.values(),key=lambda r:(int(r['ANO_ELEICAO']),r.get('DT_ELEICAO',''),int(r['NR_TURNO'])),reverse=True)
complement={r['SQ_CANDIDATO']:r for r in load(DATA/'situacao-sc-2026.json',[])}
portraits=load(DATA/'portraits.json',{})
votes=load(DATA/'votos-historicos.json',{})
collection=load(AUDIT/'collection.json',{})
networks=defaultdict(list)
for r in load(DATA/'redes-sc-2026.json',[]):
 u=tidy_url(r['DS_URL'])
 if u and u not in networks[r['SQ_CANDIDATO']]: networks[r['SQ_CANDIDATO']].append(u)
icons={}
for platform in ['instagram','facebook','tiktok','x','youtube','threads','linkedin']:
 icon=soup.select_one('.platform-'+platform+' svg')
 if icon: icons[platform]=str(icon).replace('viewbox=','viewBox=')

def vote_for(r):
 if r.get('CD_CARGO')=='12': key=f"{r['ANO_ELEICAO']}:chapa:{r['SG_UE']}:{r['NR_CANDIDATO']}:{r['NR_TURNO']}"
 else: key=f"{r['ANO_ELEICAO']}:{r['SQ_CANDIDATO']}:{r['NR_TURNO']}"
 return votes.get(key)

def vote_text(r):
 v=vote_for(r)
 if not v: return 'Votação não consolidada'
 return number(v['votes'])+(' votos da chapa' if v.get('type')=='chapa' else ' votos')

def social_html(sid,note):
 social=[]; sites=[]; seen=set()
 platforms=[('instagram.com','instagram','Instagram'),('facebook.com','facebook','Facebook'),('tiktok.com','tiktok','TikTok'),('youtube.com','youtube','YouTube'),('youtu.be','youtube','YouTube'),('twitter.com','x','X'),('x.com','x','X'),('threads.net','threads','Threads'),('threads.com','threads','Threads'),('linkedin.com','linkedin','LinkedIn'),('bsky.app','bluesky','Bluesky')]
 for u in networks[sid]:
  host=urlsplit(u).hostname
  match=next(((p,label) for domain,p,label in platforms if host==domain or host.endswith('.'+domain)),None)
  if match:
   platform,label=match
   if platform in seen: continue
   seen.add(platform)
   if platform in icons:
    social.append(f'<a class="social-link social-link--icon platform-{platform}" href="{esc(u)}" target="_blank" rel="noopener noreferrer" aria-label="{label}: canal declarado no TSE" title="{label}: canal declarado no TSE">{icons[platform]}<span class="sr-only">{label}</span></a>')
   else: social.append(link(u,label,'social-link--text'))
  elif not any(h in host for h in ['wa.me','whatsapp','t.me','telegram','queroapoiar','apoia.se']): sites.append(u)
 preferred=note.get('topics_source','')
 if preferred and note.get('topics_kind','').lower().startswith('site'): sites=[preferred]+sites
 if social: socials=''.join(social)
 else: socials='<p class="no-source">Sem canal válido localizado no arquivo de redes do TSE.</p>'
 site=link(sites[0],'Abrir site','site-btn') if sites else '<p class="no-source">Site não identificado nesta edição.</p>'
 return f'<div><p class="eyebrow">Redes declaradas</p><div class="socials socials--icons">{socials}</div></div><div><p class="eyebrow">Site / publicação</p>{site}</div>'

profiles=[]; groups=defaultdict(list)
for r in raw:
 sid=r['SQ_CANDIDATO']; name=title(r['NM_URNA_CANDIDATO']); note=notes.get(r['NM_URNA_CANDIDATO'],{}); history=histories[sid]
 party=r['SG_PARTIDO']; pleitos=len({history_key(h) for h in history})+1
 current=note.get('mandate_state') in ['titular','licenciado']
 latest=history[0] if history else None
 wins=[h for h in history if is_elected(h)]
 current_origin=next((h for h in history if is_elected(h) and ((h['ANO_ELEICAO']=='2022' and h['CD_CARGO']=='7') or (h['ANO_ELEICAO']=='2024' and h['CD_CARGO'] in ['11','12','13']))),None)
 comp=complement.get(sid,{})
 status_values=[]
 for key in ['DS_SITUACAO_CANDIDATURA','DS_DETALHE_SITUACAO_CAND','DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CANDIDATO_URNA']:
  v=clean(comp.get(key) or r.get(key),'')
  if v and norm(v) not in {norm(x) for x in status_values}: status_values.append(v)
 status=' · '.join(status_values) if status_values else 'Situação processual não consolidada nesta edição'
 office_label=note.get('mandate','Sem mandato atual confirmado nesta edição')
 if not note.get('mandate') and current_origin:
  office_label='Eleição no ciclo vigente · exercício a confirmar'
  mandate_note=f"O TSE registra eleição para {office(current_origin).lower()} em {place(current_origin)}, em {current_origin['ANO_ELEICAO']}. Isso, por si só, não confirma exercício atual nem eventuais licenças."
 else: mandate_note=note.get('mandate_note','O histórico abaixo registra candidaturas e resultados. A ausência de confirmação nesta ficha não comprova ausência de mandato ou de atuação pública.')
 tags=[]
 if current: tags.append(f'<span class="trajectory-tag tag-current">{esc(office_label)}</span>')
 elif note.get('mandate_state')=='suplencia_documentada': tags.append('<span class="trajectory-tag tag-held">Exercício por suplência documentado</span>')
 elif wins: tags.append(f'<span class="trajectory-tag tag-held">Eleição registrada · {esc(office(wins[0]))}</span>')
 tags.append(f'<span class="trajectory-tag tag-pleito" title="Contagem restrita ao histórico individual vinculado pelo TSE, incluindo 2026">{pleitos}º pleito · TSE</span>')
 if history:
  oldest=min(history,key=lambda h:int(h['ANO_ELEICAO']))
  places=sorted({place(h) for h in history if h['CD_CARGO'] in ['11','12','13']})
  bio=f"O histórico vinculado pelo TSE começa em {oldest['ANO_ELEICAO']}. A disputa anterior mais recente foi para {office(latest).lower()} em {place(latest)}, em {latest['ANO_ELEICAO']}."
 else:
  places=[]
  bio='Não há candidatura anterior vinculada a esta pessoa no arquivo histórico do TSE consultado. Isso não permite concluir que sua atuação pública começou em 2026.'
 topics=note.get('topics','A síntese de pautas individuais ainda não está consolidada nesta edição. Os canais declarados estão ao lado; posições gerais do partido não foram atribuídas automaticamente à candidatura.')
 topics_source=('<p class="state-source">'+link(note['topics_source'],'Consultar publicação')+f'<span class="source-kind">{esc(note.get("topics_kind","Fonte pública"))}</span></p>') if note.get('topics_source') else ''
 if note.get('additional_source'): topics_source+='<p class="state-source">'+link(note['additional_source'],'Outra fonte documentada')+'</p>'
 portrait=portraits.get(sid,{})
 if portrait and (ROOT/portrait['path']).exists():
  photo=f'<img class="candidate-photo" src="{esc(portrait["path"])}" alt="Foto de candidatura de {esc(name)}" width="240" height="300" loading="lazy" decoding="async"/>'
 else: photo=''
 initials=''.join(x[0] for x in name.split() if len(x)>2)[:2]
 origin=''
 if current and current_origin:
  origin=f'<div class="mandate-origin"><p class="mandate-origin-label">Eleição que originou o mandato</p><div class="mandate-origin-top"><span class="mandate-origin-year">{current_origin["ANO_ELEICAO"]}</span><strong class="mandate-origin-votes">{esc(vote_text(current_origin))}</strong></div><p class="mandate-origin-office">{esc(office(current_origin))} · {esc(place(current_origin))}</p>{link(RESULTS,"TSE · resultados","mandate-origin-source")}</div>'
 mandate_source=link(note['mandate_source'],'Fonte sobre o mandato') if note.get('mandate_source') else link(TSE,'Histórico oficial; exercício não confirmado')
 if note.get('mandate_source_kind'): mandate_source+=f'<span class="source-kind">{esc(note["mandate_source_kind"])}</span>'
 if latest:
  turn=f' · {latest["NR_TURNO"]}º turno' if latest['CD_CARGO'] in ['11','12'] else ''
  latest_html=f'<p class="career-race">{latest["ANO_ELEICAO"]} · {esc(office(latest))} · {esc(place(latest))}{turn}</p><p class="career-votes">{esc(vote_text(latest))}</p><span class="result-tag">{esc(result(latest))}</span>'
 else: latest_html='<p class="career-race">Sem pleito anterior vinculado</p><p class="career-votes">Primeiro registro: 2026</p><span class="result-tag">Histórico TSE consultado</span>'
 context='Resultados passados descrevem disputas anteriores; não são previsão para 2026. Suplência eleitoral não significa exercício automático de mandato.'
 if latest and latest['CD_CARGO']=='12': context='Na candidatura a vice-prefeito, a votação pertence à chapa. Ela não é uma votação nominal individual do candidato a vice.'
 if note.get('biography_note'): context=note['biography_note']
 rows=[]; normalized_history=[]
 for h in history:
  v=vote_for(h)
  rows.append(f'<tr><td>{h["ANO_ELEICAO"]}<br><small>{h["NR_TURNO"]}º turno</small></td><td>{esc(office(h))}<br><small>{esc(place(h))}</small></td><td>{esc(LABEL.get(h["SG_PARTIDO"],h["SG_PARTIDO"]))}</td><td>{esc(result(h))}</td><td>{esc(vote_text(h))}</td></tr>')
  normalized_history.append({'year':int(h['ANO_ELEICAO']),'round':int(h['NR_TURNO']),'office':office(h),'electoral_unit':place(h),'party':h['SG_PARTIDO'],'result':result(h),'historical_candidate_id':h['SQ_CANDIDATO'],'votes':v['votes'] if v else None,'vote_type':v.get('type') if v else None,'votes_source':v.get('source') if v else None})
 table='<div class="history-scroll"><table><caption class="sr-only">Histórico eleitoral de '+esc(name)+'</caption><thead><tr><th scope="col">Eleição</th><th scope="col">Cargo / local</th><th scope="col">Partido</th><th scope="col">Resultado</th><th scope="col">Votação</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div>' if rows else '<p class="history-meta">Nenhuma disputa anterior consta no histórico individual vinculado pelo TSE nesta coleta.</p>'
 federation=clean(r.get('NM_FEDERACAO'),'Sem federação informada')
 history_meta=f'Nome completo: {title(r["NM_CANDIDATO"])}. Ocupação declarada: {title(r["DS_OCUPACAO"])}. Escolaridade declarada: {title(r["DS_GRAU_INSTRUCAO"])}. Federação: {federation}.'
 search_text=' '.join([name,r['NM_CANDIDATO'],r['NR_CANDIDATO'],party,topics,office_label,' '.join(places)])
 profile={'id':sid,'name':name,'full_name':title(r['NM_CANDIDATO']),'number':r['NR_CANDIDATO'],'party':LABEL.get(party,party),'party_code':party,'occupation':title(r['DS_OCUPACAO']),'education':title(r['DS_GRAU_INSTRUCAO']),'federation':federation,'registration_status':status,'first_in_linked_history':not history,'elections_in_linked_history':pleitos,'mandate_documented':current,'mandate_state':note.get('mandate_state','not_confirmed'),'mandate_label':office_label,'mandate_note':mandate_note,'mandate_source':note.get('mandate_source'),'topics':note.get('topics'),'topics_source':note.get('topics_source'),'declared_links':networks[sid],'portrait':portrait or None,'history':normalized_history,'sources':[TSE,RESULTS],'consulted_at':DATE}
 profiles.append(profile)
 idx=len(groups[party])+1
 article=f'''<article class="candidate" id="candidato-{sid}" data-tse-id="{sid}" data-party="{party}" data-rookie="{str(not history).lower()}" data-current-office="{str(current).lower()}" data-search="{esc(search_text)}">
<div class="candidate-index" aria-hidden="true">{idx:02d}</div><header class="candidate-head"><div class="identity"><figure class="candidate-portrait">{photo}<span class="portrait-fallback" aria-hidden="true">{esc(initials)}</span></figure><div class="identity-copy"><div class="number">{r['NR_CANDIDATO']}</div><h3>{esc(name)}</h3><div class="evidence-row trajectory-tags">{''.join(tags)}</div><p class="registration-line">Cadastro 2026 · {esc(status)} · {link(TSE,'Fonte TSE')}</p></div></div></header>
<div class="candidate-body"><div class="candidate-copy"><p class="state-bio">{esc(bio)}</p><p class="eyebrow">Pautas e atuação documentadas</p><p class="pauta">{esc(topics)}</p>{topics_source}</div><div class="candidate-links">{social_html(sid,note)}</div></div>
<div class="career-band"><div class="career-cell career-current"><p class="eyebrow">Mandato: situação documentada</p><p class="career-status {'is-current' if current else ''}">{esc(office_label)}</p><p class="career-sub">{esc(mandate_note)}</p><p class="state-source">{mandate_source}</p>{origin}</div><div class="career-cell career-latest"><p class="eyebrow">Última eleição disputada</p>{latest_html}</div><div class="career-context"><p class="career-ref">{esc(context)}</p><div class="career-sources">{link(TSE,'TSE · histórico vinculado')}{link(RESULTS,'TSE · resultados')}</div></div></div>
<details class="state-history"><summary>Histórico completo e dados da candidatura</summary><p class="history-meta">{esc(history_meta)}</p>{table}<p class="history-footer">Os municípios acima identificam a circunscrição de uma disputa anterior, não o domicílio atual. A contagem reúne os turnos da mesma disputa e inclui 2026. Valores não consolidados não são tratados como zero. {link(TSE,'Arquivo de referência')}</p></details><a class="profile-link" href="#candidato-{sid}">Referência direta desta ficha · {esc(name)}</a></article>'''
 groups[party].append(article)

counts={'universe':len(universe),'candidates':len(profiles),'parties':len(groups),'mandates_documented':sum(p['mandate_documented'] for p in profiles),'first_in_linked_history':sum(p['first_in_linked_history'] for p in profiles),'history_rows':sum(len(p['history']) for p in profiles),'history_rows_with_votes':sum(h['votes'] is not None for p in profiles for h in p['history']),'portraits':sum(bool(p['portrait']) for p in profiles),'topics_with_individual_source':sum(bool(p['topics_source']) for p in profiles),'registration_statuses_consolidated':len(complement)}
nav=str(soup.select_one('.site-nav'))
hero=soup.select_one('.masthead'); hero.select_one('.office-title').string='Deputado(a) Estadual'
hero.select_one('.dek').string='Conheça as candidaturas, percorra suas trajetórias e consulte as fontes. Um levantamento por partido, com histórico eleitoral, mandatos e canais públicos.'
metrics=[(counts['candidates'],'candidaturas'),(counts['parties'],'partidos'),(counts['mandates_documented'],'mandatos titulares documentados'),(counts['first_in_linked_history'],'em 1º pleito no histórico TSE')]
meta=hero.select_one('.meta'); meta.clear()
for value,label in metrics: meta.append(BeautifulSoup(f'<div><b>{value:02d}</b><span>{label}</span></div>','html.parser'))
party_options=''.join(f'<option value="{party}">{esc(LABEL.get(party,party))} · {len(cards)}</option>' for party,cards in groups.items())
toolbar=f'''<div class="toolbar-wrap" id="buscar"><div class="toolbar"><label class="search"><span aria-hidden="true">⌕</span><span class="sr-only">Buscar candidaturas</span><input type="search" id="searchInput" autocomplete="off" placeholder="Nome, número, partido, cidade de disputa ou pauta…"/></label><span id="resultCount" class="count" aria-live="polite" aria-atomic="true">{len(raw)} de {len(raw)}</span></div><div class="state-filters"><label for="partyFilter"><span>Partido</span><select id="partyFilter"><option value="">Todos os partidos</option>{party_options}</select></label><label for="trajectoryFilter"><span>Trajetória</span><select id="trajectoryFilter"><option value="">Todas as trajetórias</option><option value="mandate">Mandato titular documentado</option><option value="first">1º pleito no histórico TSE</option><option value="history">Com eleições anteriores</option></select></label><button type="button" id="resetFilters">Limpar</button></div></div>'''
rail='<aside class="rail" aria-label="Índice de partidos"><p class="rail-label">Índice</p><nav class="party-nav">'+''.join(f'<a href="#partido-{p.lower()}" data-nav-party="{p}"><span>{esc(LABEL.get(p,p))}</span><small>{len(c):02d}</small></a>' for p,c in groups.items())+'</nav><p class="rail-note">Partidos e nomes em ordem alfabética. As etiquetas descrevem registros; não avaliam candidaturas.</p></aside>'
method=f'''<details class="overview-toggle" id="sobre-levantamento"><summary><span class="method-number">00</span><span class="method-summary-copy"><span class="section-kicker">Sobre este levantamento</span><strong>Trajetórias, fontes e limites da pesquisa</strong></span><span class="method-chevron" aria-hidden="true">＋</span></summary><div class="overview-toggle-body"><div class="overview-copy method-text"><h2>Informação para uma leitura própria.</h2><p>Esta frente reúne {len(raw)} registros de candidatura a deputado estadual em Santa Catarina, extraídos de um universo oficial de {len(universe)} registros. O recorte considera PT, PCdoB, PV, PSOL, REDE, PDT, PSB, PSTU, UP e PCO. Nesta coleta, seis dessas siglas apresentam registros para o cargo.</p><p>A inclusão segue a filiação cadastrada no TSE, não uma avaliação individual de ideologia. As pautas são atribuídas às publicações de cada candidatura; não significam concordância editorial nem comprovação de execução.</p><p>As fichas apresentam o cadastro, todos os pleitos vinculados no arquivo histórico e os canais declarados. Onde uma síntese individual ou uma confirmação de mandato ainda não está disponível, a lacuna permanece visível.</p><p>Os {counts['mandates_documented']} mandatos titulares documentados são aqueles com fonte adicional identificada nesta edição. Esse número inclui titular licenciado, com a licença indicada na ficha, e não é uma estimativa do total de pessoas em exercício. Exercícios por suplência são mostrados separadamente.</p></div></div></details>
<details class="electoral-method-toggle" id="criterio-eleitoral"><summary><span class="method-number">01</span><span class="method-summary-copy"><span class="section-kicker">Entenda os dados</span><strong>Eleição, mandato e suplência não são a mesma coisa</strong></span><span class="method-chevron" aria-hidden="true">＋</span></summary><div class="method-toggle-body method-text"><p><strong>Um retrato datado.</strong> A coleta é de {DATE_PT}. Situações de registro, licenças e substituições podem mudar. Consulte também a Justiça Eleitoral e a casa legislativa indicada na ficha.</p><p><strong>Mandato atual.</strong> Uma vitória em 2022 ou 2024 não confirma, sozinha, exercício no presente. Fontes institucionais e declarações do próprio mandato são identificadas separadamente. Suplência no resultado eleitoral não equivale a posse.</p><p><strong>Contagem de pleitos.</strong> Usamos o histórico individual vinculado pelo TSE. Dois turnos da mesma disputa não contam como duas eleições. “1º pleito” significa primeiro registro nesse arquivo, não ausência de militância, atuação comunitária ou participação em um coletivo.</p><p><strong>Votos.</strong> Os totais nominais são consolidados por ano, identificador e turno a partir dos arquivos de resultados do TSE. Para vice-prefeito, a votação é da chapa e recebe esse rótulo. Ausência de um total verificável não vira zero.</p><p><strong>Municípios e partidos anteriores.</strong> A cidade no histórico é o local da disputa daquele ano, não necessariamente o domicílio atual. A sigla histórica é preservada, mesmo quando diferente da atual.</p><p><strong>Pautas e atribuições.</strong> Sínteses de campanha descrevem posições publicadas, não resultados comprovados. A presença de um tema na agenda não significa que sua implementação dependa apenas da Assembleia Legislativa. Não há notas, rankings ou previsões eleitorais.</p></div></details>'''
sections=[]
for i,(party,cards) in enumerate(groups.items(),1):
 sections.append(f'<section class="party-section" id="partido-{party.lower()}" data-party-section="{party}"><span aria-hidden="true" class="v28-party-bg v28-party-bg-{(i-1)%8+1}"></span><header class="party-header"><div class="party-mark" aria-hidden="true"></div><div><p class="section-kicker">Partido</p><h2>{esc(LABEL.get(party,party))}</h2></div><p class="party-count">{len(cards)} candidaturas</p><span aria-hidden="true" class="v28-party-divider"></span></header><div class="candidate-list">'+''.join(cards)+'</div></section>')
empty='<div id="emptyState" class="state-empty" hidden><h2>Nenhuma candidatura encontrada</h2><p>Tente outro nome, número ou combinação de filtros.</p><button type="button" id="emptyReset">Limpar filtros</button></div>'
main='<main class="layout" id="candidaturas">'+rail+'<div class="content"><p class="state-snapshot">Deputados estaduais · SC · Coleta de '+DATE_PT+' · '+link('data/candidaturas.json' if False else URL+'data/candidaturas.json','Base e fontes')+'</p>'+method+empty+''.join(sections)+'</div></main>'
sources=f'''<section class="sources-section sources-section--refined" id="fontes"><span aria-hidden="true" class="v28-sources-bg"></span><div class="sources-heading"><div class="sources-emblem" aria-hidden="true"></div><div><p class="section-kicker">Fontes e critérios</p><h2>Da base oficial à ficha individual</h2></div><p class="sources-dek">Cada informação é vinculada à sua origem. Dados eleitorais, exercício de mandato e apresentação da candidatura são tratados separadamente.</p></div><div class="sources-grid"><article><span class="source-index">01</span><p class="eyebrow">Cadastro e histórico</p><p>Nomes, números, partidos, ocupações e histórico individual vêm dos arquivos públicos do TSE de 2026.</p>{link(TSE,'Dados Abertos do TSE')}</article><article><span class="source-index">02</span><p class="eyebrow">Resultados anteriores</p><p>Totais nominais são associados à pessoa pelo identificador oficial e ao turno correspondente. Votos de chapa recebem identificação própria.</p>{link(RESULTS,'Resultados eleitorais')}</article><article><span class="source-index">03</span><p class="eyebrow">Exercício do mandato</p><p>A ALESC, câmaras municipais e páginas dos próprios mandatos permitem verificar titularidade, exercício e licenças. O tipo da fonte é indicado em cada ficha.</p>{link('https://www.alesc.sc.gov.br/deputados/','Parlamentares da ALESC')}</article><article><span class="source-index">04</span><p class="eyebrow">Pautas individuais</p><p>As sínteses remetem às publicações consultadas. Campos ainda não consolidados permanecem identificados, sem completar propostas a partir do partido ou da profissão.</p></article></div><div class="sources-note"><p><strong>Dados abertos, sem exposição desnecessária.</strong> CPF, título eleitoral, e-mail pessoal e data de nascimento não são publicados nesta base. O acervo registra origem e data da coleta, sem rastreadores ou formulários de campanha.</p><div class="state-downloads"><a href="data/candidaturas.json" download>Base com histórico e fontes · JSON</a><a href="data/candidaturas.csv" download>Resumo das candidaturas · CSV</a><a href="audit/summary.json">Resumo da auditoria</a></div></div></section>'''
closing=str(soup.select_one('.closing-visual') or '')
footer=soup.select_one('.persistent-footer')
if footer:
 label=footer.select_one('.persistent-footer__label')
 if label: label['title']='Frente estadual independente · versão 1.0'
footer=str(footer or '')
structured={'@context':'https://schema.org','@type':'CollectionPage','name':'Deputados estaduais de Santa Catarina 2026 — Esquerda em foco','url':URL,'inLanguage':'pt-BR','dateModified':DATE,'description':'Candidaturas estaduais organizadas por partido, histórico eleitoral e fontes públicas.','mainEntity':{'@type':'ItemList','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(profiles),'itemListElement':[{'@type':'ListItem','position':i+1,'name':p['name'],'url':URL+'#candidato-'+p['id']} for i,p in enumerate(profiles)]}}
head=f'''<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="color-scheme" content="light"><meta name="theme-color" content="#f3eadc"><title>Deputados Estaduais de SC 2026 | Esquerda em foco</title><meta name="description" content="Conheça {len(profiles)} candidaturas a deputado estadual em Santa Catarina: números, partidos, histórico eleitoral, mandatos e fontes públicas."><link rel="canonical" href="{URL}"><meta name="robots" content="index,follow"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="Esquerda em foco"><meta property="og:title" content="Santa Catarina · Deputados Estaduais 2026"><meta property="og:description" content="{len(profiles)} candidaturas, histórico eleitoral e fontes para uma leitura própria."><meta property="og:url" content="{URL}"><meta property="og:image" content="{URL}assets/og-estaduais.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="Esquerda em foco: Santa Catarina, deputados estaduais, eleições 2026"><meta name="twitter:card" content="summary_large_image"><link rel="icon" type="image/svg+xml" href="assets/favicon.svg"><link rel="manifest" href="site.webmanifest"><link rel="stylesheet" href="assets/site.css"><script type="application/ld+json">{json.dumps(structured,ensure_ascii=False).replace('</','<\\/')}</script>'''
page='<!doctype html><html lang="pt-BR"><head>'+head+'</head><body><a class="skip-link" href="#candidaturas">Ir para as candidaturas</a>'+nav+'<div class="progress" aria-hidden="true"></div>'+str(hero)+toolbar+'<noscript><p class="no-js-note">Todas as fichas estão disponíveis abaixo. A busca e os filtros precisam de JavaScript.</p></noscript>'+main+closing+sources+footer+'<script src="assets/app.js" defer></script></body></html>'
(ROOT/'index.html').write_text(page,encoding='utf-8')
save(DATA/'candidaturas.json',{'schema_version':1,'updated_at':DATE,'scope':{'uf':'SC','year':2026,'office':'Deputado estadual','parties_considered':PARTIES},'counts':counts,'candidates':profiles})
with (DATA/'candidaturas.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.writer(f,delimiter=';'); w.writerow(['id_tse','nome','numero','partido','pleitos_no_historico','mandato_documentado','situacao_mandato','fonte_mandato','fonte_pautas','consulta'])
 for p in profiles:
  vals=[p['id'],p['name'],p['number'],p['party'],p['elections_in_linked_history'],p['mandate_documented'],p['mandate_label'],p['mandate_source'] or '',p['topics_source'] or '',DATE]
  w.writerow(["'"+str(v) if str(v).startswith(('=','+','-','@')) else v for v in vals])
save(AUDIT/'summary.json',{'date':DATE,'counts':counts,'federal_sha256_before':before,'federal_sha256_after':hashlib.sha256((REPO/'index.html').read_bytes()).hexdigest(),'federal_modified':False,'scope':'Only deputados-estaduais files generated','limitations':['Sínteses de pautas e confirmação de exercício de mandato não são completas para todos os registros. Campos não confirmados permanecem explícitos.','A contagem de pleitos refere-se exclusivamente ao histórico individual vinculado pelo TSE.','A fotografia e a situação cadastral dependem da disponibilidade do arquivo oficial complementar.'],'data_sources':collection.get('sources',{})})
(ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>'+URL+'</loc><lastmod>'+DATE+'</lastmod></url></urlset>')
save(ROOT/'site.webmanifest',{'name':'Esquerda em foco · Deputados Estaduais SC','short_name':'Estaduais SC','lang':'pt-BR','start_url':'./','scope':'./','display':'browser','background_color':'#f3eadc','theme_color':'#486f5c'})
image=Image.new('RGB',(1200,630),'#f3eadc'); draw=ImageDraw.Draw(image)
font_paths=['/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf','/usr/share/fonts/truetype/liberation2/LiberationSerif-Regular.ttf']
font_path=next((f for f in font_paths if Path(f).exists()),None)
def font(size): return ImageFont.truetype(font_path,size) if font_path else ImageFont.load_default()
draw.line((64,78,1136,78),fill='#486f5c',width=3); draw.text((64,106),'ESQUERDA EM FOCO / 2026',font=font(24),fill='#486f5c'); draw.text((60,175),'Santa Catarina',font=font(85),fill='#1c2829'); draw.text((64,295),'Deputados estaduais',font=font(56),fill='#486f5c'); draw.text((64,422),f'{len(profiles)} candidaturas · {len(groups)} partidos',font=font(31),fill='#1c2829'); draw.text((64,500),'Trajetórias, dados e fontes públicas.',font=font(26),fill='#455354'); image.save(ASSETS/'og-estaduais.png',optimize=True)
assert hashlib.sha256((REPO/'index.html').read_bytes()).hexdigest()==before,'Federal file was modified'
print(json.dumps(counts,ensure_ascii=False,indent=2))

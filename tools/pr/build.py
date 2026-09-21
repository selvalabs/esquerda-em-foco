"""Render Paraná from the existing presentation; all writes stay in PR paths."""
from __future__ import annotations
import collections, csv, hashlib, importlib.util, io, json, os, re, shutil, sys
from datetime import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/pr'; DOC=ROOT/'docs/pr'; PUBLIC=ROOT/'pr'
SITE=os.environ.get('EEFOCO_SITE_URL','https://selvalabs.github.io/esquerda-em-foco/').rstrip('/')+'/'
SCOPE_CONFIG=json.loads((ROOT/'config/party-scope-2026.json').read_text(encoding='utf-8'))
ALL_PARTIES=SCOPE_CONFIG['parties']; PARTIES_BY_OFFICE={code:list(ALL_PARTIES) for code in ('6','7')}
OFFICES={'6':('deputados-federais','Deputado(a) Federal'),'7':('deputados-estaduais','Deputado(a) Estadual')}
TSE='https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
THEMES={
 'educacao':'Educação pública','saude':'Saúde pública e SUS','trabalho':'Trabalho e direitos trabalhistas',
 'renda':'Renda e proteção social','moradia':'Moradia','mobilidade':'Mobilidade e transporte',
 'meio-ambiente':'Meio ambiente e clima','agricultura-familiar':'Agricultura familiar',
 'reforma-agraria':'Reforma agrária','seguranca-alimentar':'Segurança alimentar',
 'mulheres':'Direitos das mulheres','igualdade-racial':'Igualdade racial','lgbtqia':'Direitos LGBTQIA+',
 'povos-indigenas':'Povos indígenas e comunidades tradicionais','pessoa-deficiencia':'Pessoa com deficiência',
 'cultura':'Cultura','ciencia-tecnologia':'Ciência e tecnologia','juventude':'Juventude',
 'seguranca-publica':'Segurança pública','direitos-humanos':'Direitos humanos',
 'servicos-publicos':'Serviços públicos','democracia':'Participação e democracia',
 'tributacao':'Tributação','saneamento':'Água e saneamento','protecao-animal':'Proteção animal'}

def load(name,default):
 p=DATA/name;return json.loads(p.read_text()) if p.exists() else default

def save(path,value):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def helpers():
 shared=str(ROOT/'tools/rs');sys.path.insert(0,shared)
 try:
  spec=importlib.util.spec_from_file_location('eef_shared_card',ROOT/'tools/rs/build.py')
  module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 finally:
  if sys.path and sys.path[0]==shared:sys.path.pop(0)
 module.SOURCES['fotos']=('https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_PR_div.zip','TSE · fotografias do Paraná')
 return module

R=None

def normalize():
 records=load('candidates-official.json',[]);assert records,'Official PR census is required'
 profiles=load('profiles-official.json',{});statuses={r['SQ_CANDIDATO']:r for r in load('status-extended.json',load('status-official.json',[]))}
 byid={r['SQ_CANDIDATO']:r for r in records}
 successors=collections.defaultdict(list)
 for x in statuses.values():
  old=R.clean(x.get('SQ_SUBSTITUIDO'))
  if old:successors[old].append(x['SQ_CANDIDATO'])
 photos=load('photos-official.json',{});editorial=load('editorial.json',{});offices=load('offices-verified.json',{})
 api=load('election-api.json',{});election_id=str(api.get('election',{}).get('id',''))
 assert election_id and election_id!='6259','REST election identifier must be independently resolved'
 histories=collections.defaultdict(dict)
 for h in load('history-official.json',[]):
  cid=h.get('SQ_CANDIDATO_ATUAL');year=int(h['ANO_ELEICAO']);rnd=int(h.get('NR_TURNO') or 1)
  if year>=2026:continue
  key=(year,h['SQ_CANDIDATO'],rnd)
  histories[cid][key]={'year':year,'round':rnd,'candidate_id':h['SQ_CANDIDATO'],'election_id':h.get('CD_ELEICAO'),'office':h.get('DS_CARGO') or 'Cargo não informado','place':h.get('NM_UE') or 'Local não informado','uf':h.get('SG_UF'),'party':h.get('SG_PARTIDO'),'result':R.clean(h.get('DS_SIT_TOT_TURNO')),'votes':None,'source':TSE}
 social=collections.defaultdict(list)
 for s in load('social-official.json',[]):social[s['SQ_CANDIDATO']].append(s.get('DS_URL',''))
 result=[];discrepancies=[]
 for row in records:
  cid=row['SQ_CANDIDATO'];code=row['CD_CARGO'];assert row['SG_UF']=='PR' and code in OFFICES and row['ANO_ELEICAO']=='2026'
  assert row['SG_PARTIDO'] in PARTIES_BY_OFFICE[code]
  wrapped=profiles.get(cid,{});profile=wrapped.get('data',{});st=statuses.get(cid,{})
  if profile:
   for field,expected,actual in [('number',row['NR_CANDIDATO'],str(profile.get('numero',''))),('office',code,str(profile.get('cargo',{}).get('codigo',''))),('party',row['SG_PARTIDO'].upper(),str(profile.get('partido',{}).get('sigla','')).upper())]:
    if actual and expected!=actual:discrepancies.append({'id':cid,'field':field,'csv':expected,'api':actual,'source':wrapped['url']})
  state=next((R.clean(st.get(k)) for k in ['DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CANDIDATO_TOT','DS_DETALHE_SITUACAO_CAND'] if R.clean(st.get(k))),R.clean(profile.get('descricaoSituacao')) or R.clean(row.get('DS_SITUACAO_CANDIDATURA')))
  api_state=R.clean(profile.get('descricaoSituacao'))
  if state and api_state and R.norm(state)!=R.norm(api_state):discrepancies.append({'id':cid,'field':'status','csv':state,'api':api_state,'source':wrapped['url']})
  # Preserve CSV snapshot and the later individual REST observation separately.
  apt=profile.get('candidatoApto') if isinstance(profile.get('candidatoApto'),bool) else None
  status_group='apta' if apt is True else 'inapta' if apt is False else 'nao-confirmada'
  if apt is None and R.norm(state)=='deferido':status_group='deferida-sem-confirmacao-api'
  for h in profile.get('eleicoesAnteriores',[]):
   year=int(h.get('nrAno') or h.get('ano') or h.get('anoEleicao') or 2026);hid=str(h.get('id') or '')
   if year>=2026 or not hid:continue
   matches=[k for k in histories[cid] if k[0]==year and k[1]==hid]
   if matches:
    for k in matches:
     if R.url(h.get('txLink')):histories[cid][k]['profile_url']=h['txLink']
   else:
    office=h.get('cargo');office=office.get('nome') if isinstance(office,dict) else office
    histories[cid][(year,hid,1)]={'year':year,'round':1,'round_source':'not_provided_by_rest','candidate_id':hid,'election_id':h.get('idEleicao'),'office':office or 'Cargo não informado','place':h.get('local') or 'Local não informado','uf':None,'party':h.get('partido'),'result':h.get('situacaoTotalizacao'),'votes':None,'profile_url':R.url(h.get('txLink')),'source':wrapped['url']}
  vote_data=load('votes-official.json',{})
  for h in histories[cid].values():
   table=vote_data.get(str(h['year']),{});key=h['candidate_id']+':'+str(h['round'])
   if key in table.get('totals',{}) and not h.get('round_source'):
    h['votes']=table['totals'][key];h['votes_source']=table['dataset'];h['votes_provenance']={k:v for k,v in table.items() if k not in ('totals','rows_per_total')};h['votes_rows']=table.get('rows_per_total',{}).get(key)
  history=sorted(histories[cid].values(),key=lambda x:(x['year'],x['round'],x['candidate_id']))
  channels=[];sites=[];invalid=[];seen=set()
  for declared in social[cid]+(profile.get('sites') or []):
   if not isinstance(declared,str):continue
   address=R.url(declared)
   if not address:invalid.append(declared);continue
   host=urlsplit(address).hostname.removeprefix('www.');key=host+urlsplit(address).path.rstrip('/')+'?'+urlsplit(address).query
   if key.lower() in seen:continue
   seen.add(key.lower())
   platform=next((label for domain,label in R.SOCIAL.items() if host==domain or host.endswith('.'+domain)),None)
   if platform:channels.append({'label':platform,'url':address,'source':'redes'})
   else:sites.append({'label':host,'url':address,'source':'redes'})
  e=editorial.get(cid,{})
  for theme in e.get('themes',[]):
   assert theme['id'] in THEMES and theme.get('evidence_url') and theme.get('summary'),'Theme without individual evidence'
  assert not e.get('pautas') or e.get('sources'),'Editorial summary without source'
  latest=history[-1] if history else None
  identity=f"{R.label(row['NM_CANDIDATO'])} tem registro para {OFFICES[code][1].lower()} pelo {row['SG_PARTIDO']} no Paraná em 2026, com o nome de urna {R.label(row['NM_URNA_CANDIDATO'])} e o número {row['NR_CANDIDATO']}."
  if R.clean(row.get('DS_OCUPACAO')):identity+=' A ocupação declarada é '+R.label(row['DS_OCUPACAO']).lower()+'.'
  if latest:identity+=f" O histórico vinculado pelo TSE inclui candidatura em {latest['year']} a {R.label(latest['office']).lower()}, em {R.label(latest['place'])}. Registro eleitoral não comprova exercício de mandato."
  else:identity+=' Não foi localizada disputa anterior no histórico vinculado consultado; isso não permite afirmar que seja a primeira participação política.'
  sources=e.get('sources',[])
  replaces=R.clean(st.get('SQ_SUBSTITUIDO'))
  related=[]
  for rid,relation in [(replaces,'Substitui')]+[(x,'Substituída por') for x in successors[cid]]:
   if rid in byid:
    other=byid[rid];related.append({'id':rid,'relation':relation,'name':R.label(other['NM_URNA_CANDIDATO']),'office_code':int(other['CD_CARGO']),'url':'../'+OFFICES[other['CD_CARGO']][0]+'/#candidato-'+rid})
  candidate={'id':cid,'state':'PR','office_code':int(code),'election_year':2026,'name':R.label(row['NM_URNA_CANDIDATO']),'official_name':row['NM_URNA_CANDIDATO'],'full_name':R.label(row['NM_CANDIDATO']),'number':row['NR_CANDIDATO'],'party':row['SG_PARTIDO'],'federation':R.clean(row.get('NM_FEDERACAO')),'occupation':R.label(row.get('DS_OCUPACAO')),'status':R.label(state) or None,'status_api':api_state or None,'status_group':status_group,'apt_api':apt,'status_fields':st,'substitution_links':related,'replaced_flag':st.get('ST_SUBSTITUIDO')=='S','profile_checked_at':wrapped.get('checked_at'),'current_office':offices.get(cid),'history':history,'photo':photos.get(cid),'socials':channels,'sites':sites,'invalid_declared_urls':invalid,'pautas':e.get('pautas'),'biography':e.get('biography'),'official_summary':identity,'editorial_sources':sources,'themes':e.get('themes',[]),'region':e.get('region'),'editorial_checked_at':e.get('checked_at'),'research_status':'documentada' if e.get('pautas') else 'pendente','tse_url':f'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/2026/{election_id}/PR/{cid}','source_record':{'url':TSE,'id':cid,'generated_at':row['DT_GERACAO']+' '+row['HH_GERACAO']}}
  result.append(candidate)
 save(DOC/'reconciliation.json',{'identity_discrepancies':discrepancies,'profile_count':sum(bool(x.get('data')) for x in profiles.values()),'expected_profiles':len(records),'scope_by_office':PARTIES_BY_OFFICE})
 assert not any(d['field'] in ('number','office','party') for d in discrepancies),'Identity mismatch requires review'
 return sorted(result,key=lambda c:(R.norm(c['party']),R.norm(c['name']),c['id']))

def render_card(c,icons):
 node=BeautifulSoup(R.card(c,icons),'html.parser').article
 for tag in node.select('.tag-pleito'):tag['title']='Candidaturas anteriores vinculadas pelo TSE; não corresponde ao número de mandatos'
 node['data-themes']=' '.join(sorted({t['id'] for t in c['themes']}));node['data-status-group']=c['status_group'];node['data-region']=c['region']['label'] if c.get('region') else ''
 node['data-search']+=' '+c['official_summary']+' '+(node['data-region'] or '')
 node['data-has-history']=str(bool(c['history'])).lower()
 if c.get('region'):node.select_one('.identity-copy').append(BeautifulSoup('<p class="rs-occupation">Atuação municipal documentada: '+R.link(c['region']['source'],R.esc(c['region']['label']),'source-link')+'</p>','html.parser').p)
 apt_label='Apta' if c['apt_api'] is True else 'Inapta' if c['apt_api'] is False else 'Aptidão não confirmada'
 checked=(c.get('profile_checked_at') or '')[:10]
 note='<p class="empty">'+apt_label+' na consulta individual do TSE de '+R.esc(checked)+'.</p>'
 if c['current_office']:note+='<p class="empty">'+R.esc(c['current_office'].get('detail',''))+'</p>'
 for rel in c['substitution_links']:note+='<p class="empty">'+R.esc(rel['relation'])+': <a href="'+R.esc(rel['url'])+'">'+R.esc(rel['name'])+'</a> · vínculo do cadastro complementar.</p>'
 node.select_one('.career-context').append(BeautifulSoup('<div>'+note+'</div>','html.parser').div)
 bio=BeautifulSoup('<div class="pr-official-summary"><p class="eyebrow">Cadastro e trajetória eleitoral</p><p>'+R.esc(c['official_summary'])+'</p>'+R.link(c['tse_url'],'Fonte: cadastro e histórico TSE ↗','source-link')+'</div>','html.parser').div
 node.select_one('.candidate-copy').append(bio)
 if c['themes']:
  tags=''.join(R.link(t['evidence_url'],R.esc(THEMES[t['id']]),'pr-theme-tag',title=t['summary']) for t in c['themes'])
  node.select_one('.candidate-copy').append(BeautifulSoup('<div class="pr-theme-tags">'+tags+'</div>','html.parser').div)
 if c['status_api'] and R.norm(c['status_api'])!=R.norm(c['status'] or ''):
  node.select_one('.career-context').append(BeautifulSoup('<p class="empty">Consulta individual posterior: '+R.esc(c['status_api'])+'. As duas observações têm datas próprias.</p>','html.parser').p)
 return str(node)

def render(code,allrecords,manifest):
 slug,label=OFFICES[code];dest=PUBLIC/slug;dest.mkdir(parents=True,exist_ok=True);R.DEST=dest
 records=[c for c in allrecords if c['office_code']==int(code)];assert records
 template=(ROOT/'rs/deputados-federais/index.html').read_text();soup=BeautifulSoup(template,'html.parser')
 for script in soup.select('script'):script.decompose()
 icons={}
 for a in soup.select('.social-link--icon'):
  svg=a.select_one('svg')
  if svg:icons[a.get('aria-label','').split(' ')[0]]=str(svg).replace('viewbox=','viewBox=')
 for section in soup.select('.party-section'):section.decompose()
 canonical=SITE+'pr/'+slug+'/';date=manifest['sources']['candidates']['generated_at'].split(' ')[0];iso='-'.join(reversed(date.split('/')))
 title=f'Candidatos a {label.replace("(a)","")} no Paraná 2026 | Esquerda em foco'
 description=f'Candidaturas a {label.lower()} pelo Paraná em 2026: cadastro TSE, situação, histórico, canais declarados e pautas com fontes individuais.'
 soup.title.string=title
 for meta in soup.select('meta'):
  key=meta.get('name',meta.get('property',''))
  if key in ('description','og:description','twitter:description'):meta['content']=description
  if key in ('og:title','twitter:title'):meta['content']=title
  if key=='og:url':meta['content']=canonical
  if key in ('og:image','twitter:image'):meta['content']=SITE+'pr/assets/og-pr.png'
  if key in ('og:image:alt','twitter:image:alt'):meta['content']='Esquerda em foco · Paraná · Eleições 2026'
 soup.select_one('link[rel="canonical"]')['href']=canonical
 soup.select_one('link[rel="manifest"]')['href']='../site.webmanifest';soup.select_one('link[rel="icon"]')['href']='../favicon.svg'
 soup.select_one('.site-nav__edition').string='PR · 2026';soup.select_one('h1.title').string='Paraná';soup.select_one('.office-title').string=label
 soup.select_one('.dek').string='Cadastros, trajetórias eleitorais e pautas documentadas. Consulte as fontes de cada ficha e combine os filtros para explorar o levantamento.'
 counts=collections.Counter(c['party'] for c in records);states=collections.Counter(c['status'] for c in records)
 metrics=[(len(records),'registros no recorte'),(len(counts),'partidos representados'),(sum(bool(c['current_office']) for c in records),'mandatos confirmados'),(sum(bool(c['history']) for c in records),'históricos anteriores')]
 R.sethtml(soup.select_one('.meta'),''.join(f'<div><b>{n}</b><span>{R.esc(text)}</span></div>' for n,text in metrics))
 soup.select_one('.rs-date').string='Cadastro de '+date+' · '+ ' · '.join(f'{s or "Sem situação confirmada"}: {n}' for s,n in sorted(states.items(),key=lambda x:str(x[0])))
 soup.select_one('#resultCount').string=f'{len(records)} resultados'
 nav=soup.select_one('.party-nav');nav.clear()
 for p in sorted(counts,key=R.norm):nav.append(R.fragment(f'<a data-nav-party="{p}" href="#partido-{R.norm(p)}"><span>{p}</span><small>{counts[p]}</small></a>').a)
 content=soup.select_one('.content')
 for i,p in enumerate(sorted(counts,key=R.norm)):
  selected=[c for c in records if c['party']==p]
  markup=f'<section class="party-section" data-party-section="{p}" id="partido-{R.norm(p)}"><span aria-hidden="true" class="v28-party-bg v28-party-bg-{i%3+1}"></span><header class="party-header"><div aria-hidden="true" class="party-mark"></div><div><p class="section-kicker">Partido</p><h2>{p}</h2></div><p class="party-count">{len(selected)} registros</p></header><div class="candidate-list">'+''.join(render_card(c,icons) for c in selected)+'</div></section>'
  content.append(R.fragment(markup).section)
 themes_count=collections.Counter(t['id'] for c in records for t in c['themes'])
 controls='<div class="pr-filters"><label for="partyFilter">Filtrar partido</label><select id="partyFilter"><option value="">Todos os partidos</option>'+''.join(f'<option value="{p}">{p}</option>' for p in sorted(counts,key=R.norm))+'</select><label for="statusFilter">Situação na consulta individual</label><select id="statusFilter"><option value="">Todos os registros</option><option value="apta">Aptas na consulta do TSE</option><option value="inapta">Inaptas na consulta do TSE</option><option value="nao-confirmada">Aptidão não confirmada</option></select><p class="rail-label">Pautas documentadas</p><p class="pr-filter-note">Selecionar várias pautas exige todas elas. Falta de associação não significa oposição à pauta.</p><div class="pr-theme-filter">'+''.join(f'<button type="button" data-theme="{k}" aria-pressed="false">{R.esc(THEMES[k])}<small>{v}</small></button>' for k,v in sorted(themes_count.items(),key=lambda x:R.norm(THEMES[x[0]])))+'</div><button id="clearFilters" type="button">Limpar filtros</button></div>'
 extra='<label for="mandateFilter">Mandato atual</label><select id="mandateFilter"><option value="">Todos</option><option value="true">Com mandato confirmado</option><option value="false">Sem confirmação nesta edição</option></select><label for="historyFilter">Histórico eleitoral</label><select id="historyFilter"><option value="">Todos</option><option value="true">Com disputa anterior vinculada</option><option value="false">Sem disputa anterior localizada</option></select>'
 regions=sorted({c['region']['label'] for c in records if c.get('region')},key=R.norm)
 extra+='<label for="regionFilter">Atuação municipal documentada</label><select id="regionFilter"><option value="">Todas / não mapeada</option>'+''.join('<option>'+R.esc(name)+'</option>' for name in regions)+'</select>'
 controls=controls.replace('<p class="rail-label">Pautas documentadas</p>',extra+'<p class="rail-label">Pautas documentadas</p>')
 soup.select_one('.party-nav').insert_after(R.fragment(controls).div)
 localnav='<nav class="pr-editions" aria-label="Edições do levantamento"><a href="../../">SC · Federais</a><a href="../../deputados-estaduais/">SC · Estaduais</a><a href="../../rs/deputados-federais/">RS · Federais</a><a href="../deputados-federais/"'+(' aria-current="page"' if code=='6' else '')+'>PR · Federais</a><a href="../deputados-estaduais/"'+(' aria-current="page"' if code=='7' else '')+'>PR · Estaduais</a></nav>'
 soup.select_one('.masthead').insert_after(R.fragment(localnav).nav)
 summary_count=sum(bool(c['pautas']) for c in records);census=manifest['census'][slug]
 scope_text=', '.join(PARTIES_BY_OFFICE[code])
 about=f'<div class="overview-copy"><h2>O que esta edição reúne</h2><p>São {len(records)} registros para {label.lower()} no Paraná, extraídos do cadastro TSE de 2026 nas siglas {scope_text}. O arquivo completo contém {census["all_parties_total"]} registros para este cargo no estado; {census["outside_scope_total"]} pertencem a outras siglas e estão fora deste recorte.</p><p>O total inclui situações especiais e registros inaptos quando presentes. Nenhum registro é removido silenciosamente: a situação fica na ficha e pode ser filtrada. As observações do arquivo e da consulta individual têm datas próprias.</p><p>Há {summary_count} sínteses individuais de pautas nesta edição. As demais fichas mantêm a informação cadastral e indicam a pesquisa pendente. Partido, profissão, naturalidade e candidatura anterior não são usados para inferir posições pessoais, região de atuação ou mandato atual.</p><p>A exibição começa pela ordem alfabética e gira diariamente, no horário de Brasília. A posição não representa preferência, avaliação ou previsão eleitoral.</p></div>'
 R.sethtml(soup.select_one('#sobre-levantamento .overview-toggle-body'),about)
 R.sethtml(soup.select_one('#criterio-eleitoral .method-toggle-body'),'<div class="method-toggle-intro"><p>Cadastro eleitoral, mandato, proposta e voto parlamentar são informações distintas. Esta base não calcula notas, rankings ou chances eleitorais.</p><p>As tags remetem a documentos atribuíveis à pessoa. Pauta não pesquisada não significa oposição nem ausência de propostas. A profissão não gera tags automaticamente.</p><p>Histórico vinculado corresponde a candidaturas, não à duração de mandatos. Votos nominais anteriores ainda não consolidados aparecem como lacuna, nunca como zero. A naturalidade não é tratada como base eleitoral.</p><p>Na consulta individual do TSE, aptidão e situação processual são campos diferentes. O filtro utiliza o campo de aptidão observado, preservando o texto da situação e sua data.</p></div>')
 source_names={'candidates':'Cadastro eleitoral','status':'Situação das candidaturas','social':'Canais declarados','history':'Histórico vinculado','photos':'Fotografias oficiais','map':'Mapa do Paraná · IBGE'}
 source_list=''.join('<article><p class="eyebrow">'+R.esc(source_names.get(name,name))+'</p><p>Consulta: '+R.esc(source.get('checked_at','')[:10])+'</p>'+R.link(source['url'],'Abrir fonte oficial ↗','source-link')+'</article>' for name,source in manifest['sources'].items())
 R.sethtml(soup.select_one('#fontes'),'<div class="sources-heading"><div><p class="section-kicker">Fontes e critérios</p><h2>O caminho até cada informação</h2></div></div><div class="sources-grid">'+source_list+'</div><p class="rs-data-links"><a href="dados.json">Base JSON</a> · <a href="candidaturas.csv">Cadastro CSV</a> · <a href="fontes.json">Fontes e datas</a> · <a href="auditoria.json">Auditoria e pendências</a> · <a href="../">Edições do Paraná</a></p>')
 # Remove the old state map embedded by the template. Only the PR map is displayed.
 for node in soup.select('style'):
  node.string=re.sub(r'background-image:url\("data:image/svg\+xml;base64,[^"]+"\)!important','background-image:url("../assets/pr-map-display.svg")!important',node.get_text())
 style=soup.new_tag('style',id='pr-specific');style.string=(ROOT/'tools/pr/style.css').read_text();soup.head.append(style)
 for a in soup.select('a[href]'):
  if a.get('href')=='../../' and a.get_text(strip=True)=='Edição SC':a.string='SC · Federais'
 # The template contains no remaining source data from RS after the candidate and method replacements.
 script=soup.new_tag('script',src='../assets/runtime.js');script['defer']='';soup.body.append(script)
 ld={'@context':'https://schema.org','@type':'CollectionPage','url':canonical,'name':title,'description':description,'dateModified':iso,'inLanguage':'pt-BR','spatialCoverage':{'@type':'Place','name':'Paraná, Brasil'},'mainEntity':{'@type':'ItemList','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(records),'itemListElement':[{'@type':'Person','name':c['name'],'identifier':c['id'],'url':canonical+'#candidato-'+c['id']} for c in records]}}
 tag=soup.new_tag('script',type='application/ld+json');tag.string=json.dumps(ld,ensure_ascii=False).replace('</','<\\/');soup.head.append(tag)
 html=str(soup).replace('viewbox=','viewBox=');(dest/'index.html').write_text(html,encoding='utf-8')
 public_records=[{k:v for k,v in c.items() if k!='invalid_declared_urls'} for c in records]
 save(dest/'dados.json',{'schema_version':1,'state':'PR','office_code':int(code),'election_year':2026,'as_of':iso,'scope_parties':PARTIES_BY_OFFICE[code],'candidates':public_records})
 save(dest/'fontes.json',{'manifest':manifest,'editorial':{c['id']:load('editorial.json',{}).get(c['id'],{}) for c in records if c['pautas']}})
 with (dest/'candidaturas.csv').open('w',newline='',encoding='utf-8-sig') as f:
  writer=csv.DictWriter(f,fieldnames=['id','name','full_name','number','party','state','office_code','status','status_api','status_group','tse_url'],extrasaction='ignore');writer.writeheader();writer.writerows(records)
 pending=[]
 for c in records:
  fields=[]
  if not c['pautas']:fields.append('pautas_individuais')
  if not c['current_office']:fields.append('mandato_atual_nao_confirmado')
  if any(h.get('votes') is None and not str(h['office']).upper().startswith('VICE') for h in c['history']):fields.append('votos_nominais_historicos_parciais')
  if not c['region']:fields.append('regiao_de_atuacao')
  if not c['photo']:fields.append('foto')
  if fields:pending.append({'id':c['id'],'name':c['name'],'fields':fields})
 report={**census,'status_counts':dict(states),'aptitude_counts':dict(collections.Counter(c['status_group'] for c in records)),'with_photo':sum(bool(c['photo']) for c in records),'with_previous_history':sum(bool(c['history']) for c in records),'historical_records':sum(len(c['history']) for c in records),'historical_records_with_votes':sum(h.get('votes') is not None for c in records for h in c['history']),'with_documented_themes':summary_count,'with_confirmed_office':sum(bool(c['current_office']) for c in records),'with_declared_channels':sum(bool(c['socials'] or c['sites']) for c in records),'substituted_records':sum(c['replaced_flag'] for c in records),'substitution_links':sum(len(c['substitution_links']) for c in records),'with_documented_region':sum(bool(c['region']) for c in records),'theme_associations':sum(len(c['themes']) for c in records),'invalid_declared_urls':sum(len(c['invalid_declared_urls']) for c in records),'pending':pending,'canonical':canonical,'html_sha256':hashlib.sha256(html.encode()).hexdigest()}
 save(dest/'auditoria.json',report);save(DOC/(slug+'-audit.json'),report)
 (dest/'sitemap.xml').write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{canonical}</loc><lastmod>{iso}</lastmod></url></urlset>')
 return report

def build():
 global R
 R=helpers();DOC.mkdir(parents=True,exist_ok=True);PUBLIC.mkdir(parents=True,exist_ok=True)
 before={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for prefix in ('index.html','deputados-estaduais','rs','data/rs') for p in ([ROOT/prefix] if (ROOT/prefix).is_file() else (ROOT/prefix).rglob('*')) if p.is_file()}
 # Preserve the IBGE source bytes and render a separately identified colour derivative.
 raw_map=(PUBLIC/'assets/pr-ibge.svg').read_bytes();map_root=ET.fromstring(raw_map)
 for node in map_root.iter():
  if node.tag.endswith(('svg','path')):node.set('fill','#d6e0d5');node.set('stroke','#486f5c')
  if node.tag.endswith('path'):node.set('stroke-width','120')
 ET.register_namespace('','http://www.w3.org/2000/svg')
 (PUBLIC/'assets/pr-map-display.svg').write_bytes(ET.tostring(map_root))
 records=normalize();manifest=load('manifest.json',{});save(DATA/'normalized.json',{'schema_version':1,'state':'PR','candidates':records});save(DATA/'taxonomy.json',{'compatibility_note':'Reutiliza o recorte e a estrutura de fontes de SC/RS. Não havia taxonomia compartilhada publicada em main na consulta de 21/09/2026; IDs PR são explícitos, versionados e não alteram outras frentes.','version':1,'themes':THEMES,'rule':'Associação depende de evidência individual; não inferida de filiação ou profissão.'})
 reports={slug:render(code,records,manifest) for code,(slug,_) in OFFICES.items()}
 (PUBLIC/'assets').mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/'tools/pr/runtime.js',PUBLIC/'assets/runtime.js');shutil.copyfile(ROOT/'favicon.svg',PUBLIC/'favicon.svg')
 save(PUBLIC/'site.webmanifest',{'name':'Esquerda em foco · Paraná','short_name':'PR · Em foco','start_url':'./','scope':'./','display':'browser','lang':'pt-BR','icons':[{'src':'favicon.svg','sizes':'any','type':'image/svg+xml'}]})
 from PIL import Image,ImageDraw,ImageFont
 image=Image.new('RGB',(1200,630),'#f2eadf');draw=ImageDraw.Draw(image)
 font_path='/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
 font=ImageFont.truetype(font_path,76) if Path(font_path).exists() else ImageFont.load_default(size=76)
 small=ImageFont.truetype(font_path,30) if Path(font_path).exists() else ImageFont.load_default(size=30)
 draw.text((80,90),'Esquerda em foco',font=small,fill='#244b3a');draw.text((75,230),'Paraná · 2026',font=font,fill='#21372c');draw.text((80,365),'Deputados federais e estaduais',font=small,fill='#21372c');draw.text((80,490),'Cadastro · Histórico · Pautas documentadas · Fontes',font=small,fill='#244b3a');image.save(PUBLIC/'assets/og-pr.png')
 home='<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Paraná 2026 | Esquerda em foco</title><meta name="description" content="Base do Paraná para deputados federais e estaduais em 2026, com dados TSE e fontes individuais."><link rel="canonical" href="'+SITE+'pr/"><style>body{margin:0;background:#f2eadf;color:#243d31;font:20px/1.6 Georgia,serif}main{max-width:850px;margin:auto;padding:12vh 6vw}h1{font-size:clamp(48px,8vw,86px);line-height:1.1}a{color:inherit}nav{display:flex;flex-wrap:wrap;gap:20px}nav a{padding:22px;border:1px solid #809183;border-radius:5px}small{display:block;margin-top:40px}</style></head><body><main><p>Esquerda em foco · Eleições 2026</p><h1>Paraná</h1><p>Cadastros oficiais, trajetórias eleitorais e pautas acompanhadas de fontes. As duas bases mantêm as situações eleitorais e indicam o que ainda precisa de pesquisa.</p><nav>'
 for slug,report in reports.items():home+=f'<a href="{slug}/">{slug.replace("-"," ").title()}<br>{report["selected_total"]} registros no recorte</a>'
 home+='</nav><small>Recorte canônico 2026: PCB, PCdoB, PCO, PDT, PSB, PSOL, PSTU, PT, PV, REDE e UP, verificado igualmente nos dois cargos. Siglas sem registro permanecem com contagem zero na auditoria.</small><p><a href="../">Voltar à edição de Santa Catarina</a></p></main></body></html>'
 (PUBLIC/'index.html').write_text(home,encoding='utf-8')
 for path,digest in before.items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,'Protected file changed: '+path
 save(DOC/'isolation.json',{'protected_file_count':len(before),'all_unchanged':True,'sha256':before})
 save(DOC/'build-report.json',{'state':'PR','census_complete':len(records)==sum(m['selected_total'] for m in manifest['census'].values()) and manifest['profiles_read']==len(records),'editorial_complete':all(c['pautas'] for c in records),'editions':{k:{a:b for a,b in v.items() if a!='pending'} for k,v in reports.items()},'protected_file_count':len(before)})
 print(json.dumps({k:{a:b for a,b in v.items() if a not in ('pending','all_by_party')} for k,v in reports.items()},ensure_ascii=False,indent=2))
if __name__=='__main__':build()

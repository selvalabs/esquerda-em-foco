"""Round-two editorial support. No network requests and no writes outside RS paths.
Facts, source types and missing information stay distinct. Topic associations
are explicitly curated; neither party nor declared occupation assigns a topic.
"""
from __future__ import annotations
import collections, hashlib, html, json, re, unicodedata, urllib.parse
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'data/rs'; A=ROOT/'docs/rs/review'; DEST=ROOT/'rs/deputados-federais'; DATE='2026-09-21'
TOPICS={
 'agricultura-familiar':'Agricultura familiar e agroecologia','ciencia-tecnologia':'Ciência e tecnologia','consumidor':'Direitos do consumidor','cultura':'Cultura','desenvolvimento-regional':'Desenvolvimento regional e indústria','direitos-lgbtqia':'Direitos LGBTQIA+','direitos-mulheres':'Direitos das mulheres','direitos-sociais':'Direitos sociais','educacao':'Educação','esporte':'Esporte e lazer','igualdade-racial':'Igualdade racial','infancia-adolescencia':'Infância e adolescência','liberdade-religiosa':'Liberdade religiosa','meio-ambiente':'Meio ambiente e clima','mobilidade':'Mobilidade e transporte','moradia':'Moradia e regularização fundiária','pessoas-com-deficiencia':'Pessoas com deficiência','pessoas-idosas':'Pessoas idosas','povos-tradicionais':'Povos indígenas e comunidades tradicionais','previdencia':'Previdência','protecao-animal':'Proteção animal','reforma-agraria':'Reforma agrária','saneamento':'Saneamento','saude':'Saúde','seguranca-publica':'Segurança pública','servico-publico':'Serviço público','trabalho':'Trabalho e renda','tributacao':'Tributação'}
def load(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return ''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')
def safe_url(value):
 try:
  p=urllib.parse.urlsplit(value)
  return p.scheme in ('http','https') and p.hostname and '.' in p.hostname and p.username is None and p.password is None and '@' not in p.netloc and not any(c.isspace() for c in value)
 except ValueError:return False

def apply_editorial():
 changes=load(D/'review-editorial.json',{}); editorial=load(D/'editorial.json',{});offices=load(D/'offices-verified.json',{})
 ids={r['SQ_CANDIDATO'] for r in load(D/'candidates-official.json',[])}
 for cid,topics in changes.get('existing_topic_assignments',{}).items():
  assert cid in ids and editorial.get(cid,{}).get('pautas'),cid
  entry=editorial[cid];sources=[s['url'] for s in entry['sources']]
  # A topic points to the source set supporting the existing individual summary.
  entry['topics']=[{'id':topic,'sources':sources} for topic in topics]
  entry.setdefault('summary_kind','documented_mixed')
 for change in changes.get('entries',[]):
  cid=change['id'];assert cid in ids,cid
  assert safe_url(change['url']),change['url']
  entry=editorial.setdefault(cid,{'sources':[]});entry.setdefault('sources',[])
  for field in ('pautas','biography','summary_kind'):
   if field in change:entry[field]=change[field]
  source={'url':change['url'],'label':change['label'],'source_type':change['source_type'],'checked_at':DATE}
  entry['sources']=[s for s in entry['sources'] if s['url']!=change['url']]+[source]
  existing={t['id']:t for t in entry.get('topics',[])}
  for topic in change.get('topics',[]):
   assert topic in TOPICS,topic
   old=existing.get(topic,{'id':topic,'sources':[]});old['sources']=sorted(set(old['sources']+[change['url']]));existing[topic]=old
  entry['topics']=list(existing.values());entry['checked_at']=DATE
  if change.get('limitation'):entry['source_limitation']=change['limitation']
  if change.get('office'):
   assert change['source_type']=='institutional'
   offices[cid]={'label':change['office'],'source':change.get('office_source',change['url']),'checked_at':DATE,'confirmation':'Dated institutional directory; not an inference from election results.'}
 for cid,e in editorial.items():
  for topic in e.get('topics',[]):
   assert topic['id'] in TOPICS and topic['sources']
   assert set(topic['sources']).issubset({s['url'] for s in e['sources']})
 save(D/'editorial.json',editorial);save(D/'offices-verified.json',offices)
 save(D/'topics.json',{'version':1,'checked_at':DATE,'rule':'Associations have individual documentary sources. Multiple selected topics use AND, not a ranking. Historical advocacy does not establish a new 2026 proposal.','topics':TOPICS})

def reconcile_history(histories):
 legacy=load(D/'votes-legacy-reviewed.json',{})
 for cid,hs in histories.items():
  for h in hs:
   source=legacy.get(str(h['year']),{});key=f'{cid}:{h["year"]}:{h["candidate_id"]}:{h.get("round",1)}'
   if key in source.get('totals',{}):
    h.update({'votes':source['totals'][key],'votes_source':source['url'],'votes_checked_at':source['checked_at'],'votes_match_method':'Candidate ID + civil name + office + locality + round; complete RS member checksum'})
   office=norm(h.get('office',''))
   if h['year']>=2026:state='not_yet_held'
   elif office.startswith('vice') or 'suplente' in office:
    state='not_applicable';h['votes']=None;h.pop('votes_source',None)
   elif h.get('votes') is not None:state='verified_nominal'
   else:state='not_verified'
   h['votes_status']=state
   if state=='not_applicable':h['votes_note']='Não se aplica: candidatura de vice ou suplente de chapa, sem votação nominal individual.'
   elif state=='not_verified':h['votes_note']='Votação nominal não reconciliada nas fontes consultadas; não equivale a zero.'
 return histories

def enrich_records(records):
 editorial=load(D/'editorial.json',{})
 for c in records:
  entry=editorial.get(c['id'],{});c['topics']=entry.get('topics',[]);c['summary_kind']=entry.get('summary_kind')
  c['source_limitation']=entry.get('source_limitation');c['review_date']=DATE
 return records

def decorate_card(markup,c):
 soup=BeautifulSoup(markup,'html.parser');article=soup.select_one('article.candidate')
 article['data-topics']=' '.join(t['id'] for t in c.get('topics',[]))
 label=soup.select_one('.candidate-copy .eyebrow')
 kind=c.get('summary_kind','')
 if label:label.string='Trajetória documentada' if kind=='trajectory' else 'Atuação e posições anteriores' if kind in ('historical_record','historical_statement') else 'Pautas e atuação documentadas'
 if c.get('topics'):
  box=soup.new_tag('div',attrs={'class':'rs-topics','aria-label':'Temas documentados'})
  for topic in c['topics']:
   tag=soup.new_tag('span',attrs={'class':'rs-topic'});tag.string=TOPICS[topic['id']];box.append(tag)
  soup.select_one('.candidate-copy').append(box)
 if c.get('source_limitation'):
  note=soup.new_tag('p',attrs={'class':'empty rs-source-limitation'});note.string=c['source_limitation'];soup.select_one('.candidate-copy').append(note)
 previous=[h for h in c['history'] if h['year']<2026]
 latest=max(previous,key=lambda h:(h['year'],h.get('round',1)),default=None)
 if latest and latest.get('votes') is None:
  node=soup.select_one('.career-latest p.empty')
  if node:node.string=latest.get('votes_note','Votação nominal não conferida nesta edição; não equivale a zero.')
 for node,h in zip(soup.select('.rs-history li'),sorted(c['history'],key=lambda x:(int(x['year']),int(x.get('round',1))),reverse=True)):
  if h.get('votes_note'):
   note=soup.new_tag('span',attrs={'class':'empty rs-vote-note'});note.string=' '+h['votes_note'];node.append(note)
 return str(article)

def finalize(records):
 A.mkdir(parents=True,exist_ok=True);soup=BeautifulSoup((DEST/'index.html').read_text(),'html.parser');byid={c['id']:c for c in records}
 counts=collections.Counter(h['votes_status'] for c in records for h in c['history'])
 summary_count=sum(bool(c['pautas']) for c in records);biography_count=sum(bool(c['biography']) for c in records)
 theme_ids=sorted({t['id'] for c in records for t in c.get('topics',[])},key=lambda t:norm(TOPICS[t]))
 controls=soup.new_tag('section',attrs={'class':'rs-review-filters','aria-label':'Filtros documentais'})
 options=''.join('<option value="'+html.escape(p)+'">'+html.escape(p)+'</option>' for p in sorted({c['party'] for c in records},key=norm))
 choices=''.join('<label class="rs-topic-option"><input type="checkbox" name="rs-topic" value="'+t+'"> <span>'+html.escape(TOPICS[t])+'</span></label>' for t in theme_ids)
 controls.append(BeautifulSoup('<div class="rs-filter-top"><label for="partyFilter">Partido <select id="partyFilter"><option value="">Todos os partidos do recorte</option>'+options+'</select></label><button id="clearFilters" type="button">Limpar busca e filtros</button></div><details id="topicFilters"><summary>Filtrar por temas documentados</summary><p id="topicHelp">Ao marcar mais de um tema, aparecem somente as fichas com todos os temas selecionados. A classificação segue fontes individuais, inclusive registros históricos identificados nas fichas; não mede prioridade, qualidade ou apoio atual a uma proposta específica.</p><fieldset aria-describedby="topicHelp"><legend class="sr-only">Temas</legend>'+choices+'</fieldset></details>','html.parser'))
 soup.select_one('.toolbar-wrap').insert_after(controls)
 css=soup.new_tag('style',attrs={'id':'rs-review-styles'});css.string='''
.rs-review-filters{max-width:1280px;margin:0 auto;padding:16px clamp(16px,3vw,40px);font-size:.83rem;box-sizing:border-box;}
.rs-filter-top{display:flex;gap:12px;justify-content:space-between;align-items:center;flex-wrap:wrap}.rs-filter-top label{display:flex;gap:8px;align-items:center;flex-wrap:wrap;min-width:0;}
.rs-review-filters select,.rs-review-filters button{font:inherit;background:var(--paper-hi);color:var(--ink);border:1px solid var(--rule);border-radius:6px;padding:10px;max-width:100%;min-height:44px;}.rs-review-filters button{cursor:pointer;}
#topicFilters{margin-top:12px;}#topicFilters summary{cursor:pointer;min-height:44px;padding:10px 0;box-sizing:border-box;}#topicHelp{line-height:1.5;margin:8px 0 14px;max-width:85ch;color:var(--ink-2);}
#topicFilters fieldset{border:0;padding:0;display:flex;gap:8px;flex-wrap:wrap;min-width:0;}.rs-topic-option{display:flex;align-items:center;gap:7px;padding:8px 10px;border:1px solid var(--rule);border-radius:6px;min-height:44px;box-sizing:border-box;cursor:pointer;}.rs-topic-option input{flex-shrink:0;}
.rs-topics{display:flex;flex-wrap:wrap;gap:6px;margin:12px 0}.rs-topic{border:1px solid var(--rule);border-radius:4px;padding:4px 7px;font-size:.68rem;line-height:1.4;}.rs-vote-note{display:block;margin-top:3px;}.rs-review-note{line-height:1.6;}.rs-source-limitation{margin-top:10px;}@media(max-width:420px){.rs-filter-top{align-items:stretch;}.rs-filter-top label,.rs-filter-top select{width:100%;}.rs-filter-top button{width:100%;}}
''';soup.head.append(css)
 note=soup.new_tag('p',attrs={'class':'rs-review-note'});note.string=f'Revisão documental de 21 de setembro de 2026: {len(records)} cadastros individuais reconferidos, {summary_count} fichas com síntese de pautas, atuação ou trajetória e {len(records)-summary_count} sem síntese suficiente. Biografia, registro legislativo e proposta de campanha são informações distintas. A seleção por temas inclui apenas associações com fontes e não exclui propostas que ainda não foram documentadas aqui.'
 overview=soup.select_one('#sobre-levantamento .overview-copy');old=overview.find_all('p');old[-1].replace_with(note)
 for node in soup.select('#fontes p'):
  if 'Mandatos federais são conferidos' in node.get_text():node.string='Mandatos federais e municipais são vinculados aos diretórios institucionais consultados. O contorno estadual vem da malha oficial do IBGE. Declarações de campanha, entrevistas e registros históricos têm referências próprias nas fichas.'
 privacy=[]
 for a in soup.select('a[href]'):
  href=a['href']
  if href.startswith(('http://','https://')) and not safe_url(href):privacy.append(href);a.decompose()
 result=str(soup).replace('viewbox=','viewBox=');(DEST/'index.html').write_text(result,encoding='utf-8')
 data=load(DEST/'dados.json');data['schema_version']=2;data['review_date']=DATE;data['topic_vocabulary']=TOPICS;save(DEST/'dados.json',data)
 matrix=[]
 for c in records:
  missing=[{'year':h['year'],'office':h.get('office'),'historical_id':h['candidate_id'],'round':h.get('round',1)} for h in c['history'] if h.get('votes_status')=='not_verified']
  matrix.append({'id':c['id'],'name':c['name'],'party':c['party'],'registry_profile_rechecked':True,'summary_documented':bool(c['pautas']),'summary_kind':c.get('summary_kind'),'biography_documented':bool(c['biography']),'current_office_confirmed':bool(c['current_office']),'topics':c.get('topics',[]),'unresolved_nominal_rows':missing,'invalid_declared_url_count':len(c['invalid_declared_urls']),'source_limitation':c.get('source_limitation'),'remaining_editorial_work':None if c['pautas'] else 'Não há síntese individual de pautas/atuação suficientemente documentada; não significa ausência de propostas.'})
 report={'date':DATE,'candidate_count':len(records),'individual_tse_profiles_rechecked':107,'with_summary':summary_count,'without_summary':len(records)-summary_count,'with_biography':biography_count,'with_current_office':sum(bool(c['current_office']) for c in records),'with_previous_history':sum(any(h['year']<2026 for h in c['history']) for c in records),'with_verified_votes':sum(any(h['votes_status']=='verified_nominal' for h in c['history']) for c in records),'vote_rows':dict(counts),'topic_count':len(theme_ids),'with_topics':sum(bool(c.get('topics')) for c in records),'invalid_declared_url_count':sum(len(c['invalid_declared_urls']) for c in records),'removed_unsafe_rendered_urls':len(privacy),'editorial_complete':summary_count==len(records),'current_office_audit_exhaustive':False,'snapshot_not_live':True,'html_sha256':hashlib.sha256(result.encode()).hexdigest()}
 save(A/'final-report.json',report);save(A/'candidate-matrix.json',matrix);save(DEST/'revisao.json',{'report':report,'candidates':matrix})
 original=load(ROOT/'docs/rs/build-report.json',{});original.update({'with_editorial_summary':summary_count,'with_verified_current_office':report['with_current_office'],'with_previous_votes':report['with_verified_votes'],'html_sha256':report['html_sha256'],'review':report});save(ROOT/'docs/rs/build-report.json',original)
 save(ROOT/'docs/rs/candidate-audit.json',matrix)
 sources=load(DEST/'fontes.json',{});sources['round_two_review']=report;sources['official_refresh']=load(A/'official-refresh.json',{});sources['topics']=load(D/'topics.json',{});save(DEST/'fontes.json',sources)
 lines=['# RS — revisão editorial e factual','',f'Última revisão: {DATE}.', '', '## Cobertura',f'- {len(records)} cadastros oficiais reconferidos.',f'- {summary_count} sínteses documentadas; {len(records)-summary_count} sem síntese suficiente.',f'- {report["with_current_office"]} cargos eletivos confirmados institucionalmente; não é auditoria exaustiva de todos os cargos públicos.',f'- {counts["verified_nominal"]} registros de votação nominal conferidos, {counts["not_applicable"]} não aplicáveis e {counts["not_verified"]} não reconciliados.', '', '## Fichas sem síntese suficiente']
 lines += [f'- {c["name"]} ({c["party"]}; TSE {c["id"]}).' for c in records if not c['pautas']]
 lines += ['', '## Histórico nominal ainda não reconciliado']
 lines += [f'- {c["name"]}: {h["year"]}, {h["office"]}, ID histórico {h["historical_id"]}, turno {h["round"]}.' for c in matrix for h in c['unresolved_nominal_rows']]
 lines += ['', '## Limites','Ausência de fonte acessível, biografia ou cargo confirmado não permite concluir inexistência. Votos ausentes não são zero. A fotografia e o cadastro oficial não comprovam uma plataforma política. Bloqueio de acesso não torna um endereço inválido. Não foi instalada atualização recorrente.','', '## Reprodução','Executar `python tools/rs/upgrade_review.py`, depois `EEFOCO_OFFLINE_BUILD=1 python tools/rs/build.py` e os testes. O build é documental/offline; a coleta de novas fontes é uma etapa separada e explícita.']
 (A/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))

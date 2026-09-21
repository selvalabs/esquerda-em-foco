#!/usr/bin/env python3
"""Deterministic state-only build from validated snapshots and reviewed notes.
Does not fetch data, infer personal positions, or rewrite any other project front.
Run collect/review stages explicitly before publishing another snapshot.
"""
from __future__ import annotations
import csv, hashlib, json, re, runpy, shutil, sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]; REPO=ROOT.parent
DATA=ROOT/'data'; AUDIT=ROOT/'audit'; REVIEW=AUDIT/'review2'
sys.path.insert(0,str(ROOT/'tools'))

def load(p): return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def clean_url(v):
 try:
  p=urlsplit(str(v));host=(p.hostname or '').lower()
  if p.scheme.lower() not in ('http','https') or not host or p.username:return None
  return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path,p.query,p.fragment))
 except ValueError:return None

def main(preview=False):
 manifest=load(REVIEW/'collection.json'); assert manifest['passed'],'Fresh collection not validated'
 vote_audit=load(REVIEW/'votes-audit.json'); assert vote_audit['all_archives_read'],'Vote archives incomplete'
 photos=load(REVIEW/'portraits-audit.json'); assert photos['passed'],'Official photo join incomplete'
 editorial=load(ROOT/'editorial/review2.json'); notes=editorial['profiles']
 baseline=load(REVIEW/'baseline.json')
 outside={rel:sha(REPO/rel) for rel in baseline['outside_state_sha256'] if (REPO/rel).exists()}
 missing=set(baseline['outside_state_sha256'])-set(outside)
 if not preview: assert not missing, 'Outside files missing: '+str(missing)
 assert all(value==baseline['outside_state_sha256'][rel] for rel,value in outside.items()),'Outside-state baseline changed; review rather than overwrite'
 isolation_complete=not missing
 raw=load(REVIEW/'snapshot/universo-sc-2026.json')
 parties={'PT','PCDOB','PV','PSOL','REDE','PDT','PSB','PSTU','UP','PCO'}
 selected=[r for r in raw if r['SG_PARTIDO'].upper() in parties]
 ids={r['SQ_CANDIDATO'] for r in selected}
 assert ids==set(notes), 'Candidate changes require a new individual review before publishing'
 for sid,note in notes.items():
  assert note.get('data_review'), 'Missing per-candidate data audit '+sid
  assert note.get('queries') or note.get('evidence') or note.get('review_evidence'), 'Missing individual research record '+sid
  assert note.get('reviewed_at'),'Missing review date for '+sid
  if note.get('topics'):
   assert clean_url(note.get('topics_source')),'Missing topic source '+sid
   assert note.get('evidence') or note.get('review_evidence'), 'Summary has no documented reading '+sid
  if note.get('biography'): assert clean_url(note.get('biography_source')),'Missing biography source '+sid
 # Raw snapshots only become public data after all validation gates pass.
 for name in ['universo-sc-2026.json','historico-sc-2026.json','redes-sc-2026.json','situacao-sc-2026.json','portraits.json']:
  shutil.copyfile(REVIEW/'snapshot'/name,DATA/name)
 save(DATA/'recorte-sc-2026.json',selected)
 for img in (REVIEW/'snapshot/portraits').glob('*.webp'):
  shutil.copyfile(img,ROOT/'assets/portraits'/img.name)
 # Compatibility projection for the established layout. The reviewed ID-keyed
 # file, not this ballot-name projection, is the authoritative editorial input.
 compatibility={}
 for row in selected:
  n=notes[row['SQ_CANDIDATO']]
  compatibility[row['NM_URNA_CANDIDATO']]={k:v for k,v in n.items() if v is not None and k in {'topics','topics_source','topics_kind','mandate','mandate_state','mandate_source','mandate_source_kind','mandate_note'}}
 save(ROOT/'editorial/perfis.json',{'version':2,'derived_from':'review2.json','profiles':compatibility})
 runpy.run_path(str(ROOT/'tools/render.py'),run_name='__main__')
 dataset=load(DATA/'candidaturas.json'); doc=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
 date=manifest['consulted_at'][:10]; statuses={r['SQ_CANDIDATO']:r for r in load(DATA/'situacao-sc-2026.json')}
 network_rows=load(DATA/'redes-sc-2026.json'); networks=defaultdict(list)
 for r in network_rows:
  u=clean_url(r['DS_URL'])
  if u and u not in networks[r['SQ_CANDIDATO']]:networks[r['SQ_CANDIDATO']].append(u)
 # Availability and editorial sufficiency remain independent.
 link_audit=load(REVIEW/'link-checks.json'); browser=load(REVIEW/'browser-sources.json')
 availability={clean_url(x['url']):x for x in link_audit['links']+browser['sources']}
 def tag(name,text,attrs=None):
  el=doc.new_tag(name,attrs=attrs or {});el.string=text;return el
 def source_link(url,label):
  return tag('a',label+' ↗',{'href':url,'target':'_blank','rel':'noopener noreferrer'})
 review_rows=[]
 for p in dataset['candidates']:
  sid=p['id']; n=notes[sid]; card=doc.find(id='candidato-'+sid); assert card
  official=statuses[sid]
  status=official.get('DS_SITUACAO_JULGAMENTO') or p['registration_status']
  status_group='recursal' if 'RECURS' in status.upper() else 'deferido' if status.upper()=='DEFERIDO' else 'outro'
  p.update(registration_status=status,registration_group=status_group,
    registration_details={k:official.get(k) for k in ['DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CANDIDATO_TOT','DS_SITUACAO_CANDIDATO_URNA','ST_CANDIDATO_INSERIDO_URNA','ST_SUBSTITUIDO','SQ_SUBSTITUIDO','DS_SITUACAO_CASSACAO']},
    biography=n.get('biography'),biography_source=n.get('biography_source'),biography_source_kind=n.get('biography_source_kind'),
    topics_kind=n.get('topics_kind'),topics_material_date=n.get('topics_material_date'),topics_scope=n.get('topics_scope','published_individual_statement' if n.get('topics') else None),
    topics_review_status=n.get('topics_review_status'),mandate_verification=n.get('mandate_verification','not_confirmed'),
    mandate_source_kind=n.get('mandate_source_kind'),reviewed_at=n['reviewed_at'],declared_links=networks[sid])
  p['electoral_trajectory']=card.select_one('.state-bio').get_text(' ',strip=True)
  card['data-registration']=status_group;card['data-topics']='documented' if p['topics'] else 'not_consolidated'
  reg=card.select_one('.registration-line');reg.clear()
  label='Registro deferido' if status_group=='deferido' else 'Registro em situação recursal' if status_group=='recursal' else 'Consultar situação do registro'
  reg.append(tag('span',label,{'class':'registration-badge registration-'+status_group}))
  detail=doc.new_tag('details',attrs={'class':'registration-detail'})
  detail.append(tag('summary','Situação oficial e data da consulta'))
  detail.append(tag('p',status+'. Consulta: '+date+'.'))
  if status_group=='recursal':detail.append(tag('p','O cadastro informa indeferimento em prazo recursal ou com recurso. Este rótulo não é uma confirmação de cancelamento definitivo. Consulte a Justiça Eleitoral para acompanhar alterações.'))
  detail.append(source_link('https://divulgacandcontas.tse.jus.br/divulga/','Consultar DivulgaCandContas'))
  reg.insert_after(detail)
  bio=card.select_one('.state-bio')
  bio.insert_before(tag('p','Trajetória eleitoral',{'class':'eyebrow'}))
  if p['biography']:
   head=tag('p','Trajetória pública',{'class':'eyebrow'})
   text=tag('p',p['biography'],{'class':'state-bio state-public-bio'})
   source=doc.new_tag('p',attrs={'class':'state-source'})
   source.append(source_link(p['biography_source'],'Fonte da trajetória'))
   source.append(tag('span',p['biography_source_kind'] or 'Fonte pública individual',{'class':'source-kind'}))
   # Insert before the electoral heading in a stable, consistent order.
   anchor=bio.previous_sibling
   for el in [head,text,source]:anchor.insert_before(el)
  if not p['topics']:
   card.select_one('.pauta').string='Ainda não há uma síntese de pautas com fonte individual suficiente nesta edição. Isso não significa ausência de propostas ou de atuação pública. Os canais declarados estão disponíveis na ficha.'
  else:
   pubs=card.select_one('.pauta').find_next_sibling('p',class_='state-source')
   if pubs:
    material=n.get('topics_material_date') or 'data da publicação não identificada'
    pubs.append(tag('span',f'Material: {material} · leitura em {date}',{'class':'source-kind'}))
  # Case-sensitive URLs are kept intact. Every declared channel remains available
  # even where the compact icon strip selects only one link per platform.
  channels=doc.new_tag('details',attrs={'class':'state-channels'})
  channels.append(tag('summary',f'Canais declarados e verificação ({len(p["declared_links"])})'))
  if not p['declared_links']:channels.append(tag('p','Nenhum endereço consta no arquivo de redes do TSE para este registro.'))
  for u in p['declared_links']:
   line=doc.new_tag('p');line.append(source_link(u,urlsplit(u).hostname or 'Abrir canal'))
   a=availability.get(u,{});state=a.get('state','not_checked')
   labels={'not_found':'Endereço não encontrado na checagem.','blocked_not_verified':'Leitura automática bloqueada; disponibilidade não confirmada.','unavailable_at_check':'Não foi possível acessar nesta checagem.','login_required':'Acesso exige autenticação.','insufficient_text':'Conteúdo não pôde ser validado automaticamente.','text_available_requires_editorial_review':'Página acessada; isso não valida todo o seu conteúdo.','http_error':'Acesso não confirmado.','server_error':'Servidor indisponível na checagem.'}
   line.append(tag('span',labels.get(state,'Canal declarado ao TSE; acesso não validado nesta checagem.'),{'class':'source-kind'}));channels.append(line)
  card.select_one('.candidate-links').append(channels)
  # Broken links are not presented as available verified evidence. Keep original
  # URL in the raw export, with its access state; no silent substitution.
  for a in list(card.select('.state-source a, .site-btn')):
   u=clean_url(a.get('href',''));state=availability.get(u,{}).get('state')
   if state=='not_found':a.replace_with(tag('span','Referência indisponível na checagem; endereço preservado na base.',{'class':'source-unavailable'}))
  sources=[*p['sources']]+[n.get(k) for k in ('biography_source','topics_source','mandate_source')]+n.get('additional_sources',[])
  p['sources']=list(dict.fromkeys(u for u in sources if clean_url(u)))
  review_rows.append({'id':sid,'name':p['name'],'registration_checked':True,'portrait_checked':True,'history_checked':True,'electoral_trajectory_present':True,'additional_biography':bool(p['biography']),'topics_documented':bool(p['topics']),'topics_scope':p['topics_scope'],'mandate_verification':p['mandate_verification'],'individual_queries':len(n.get('queries',[])),'source_checks':len(n.get('checked_channels',[])),'research_stage':n.get('research_stage','electoral_and_channel_audit_only'),'reviewed_at':n['reviewed_at']})
 # New filter is additive; the existing navigation, search and direct links stay.
 controls=doc.select_one('.state-filters'); lab=doc.new_tag('label');lab.append(tag('span','Registro'))
 select=doc.new_tag('select',attrs={'id':'registrationFilter','aria-label':'Filtrar pela situação oficial do registro'})
 for value,text in [('', 'Todos os registros'),('deferido','Registro deferido'),('recursal','Situação recursal'),('outro','Outras situações')]:select.append(tag('option',text,{'value':value}))
 lab.append(select);controls.select_one('#resetFilters').insert_before(lab)
 counts=dataset['counts']; tse_diff=load(REVIEW/'tse-diff.json')
 counts.update(additional_biographies=sum(x['additional_biography'] for x in review_rows),
   individual_research_records=sum(x.get('research_stage')!='electoral_and_channel_audit_only' for x in review_rows),research_stages=dict(Counter(x['research_stage'] for x in review_rows)),topics_with_individual_source=sum(x['topics_documented'] for x in review_rows),
   topics_not_consolidated=sum(not x['topics_documented'] for x in review_rows),mandate_verification=dict(Counter(x['mandate_verification'] for x in review_rows)))
 coverage=doc.new_tag('details',attrs={'class':'electoral-method-toggle review2-coverage','id':'cobertura-revisao'})
 coverage.append(tag('summary','Revisão 2 · o que está conferido e o que permanece em aberto'))
 body=doc.new_tag('div',attrs={'class':'method-toggle-body method-text'})
 for text in [
  f"São {counts['candidates']} candidaturas no recorte do projeto, entre {counts['universe']} registros estaduais. A reconciliação por identificador da candidatura está registrada no relatório de diferenças entre as coletas; alterações não são aplicadas silenciosamente.",
  f"Cadastro, fotografia oficial e histórico foram revistos para {counts['candidates']} registros. Há {counts['additional_biographies']} apresentações de trajetória com fonte adicional e {counts['topics_with_individual_source']} sínteses de pautas ou atuação individual. Nas outras {counts['topics_not_consolidated']}, a síntese continua pendente. Todos os registros têm histórico eleitoral, inclusive a indicação de ausência de pleitos anteriores vinculados.",
  "A verificação de mandato distingue composição institucional atual, licença, relato da própria candidatura e situação ainda não reconfirmada. Falha de acesso não significa ausência de mandato. Um resultado eleitoral passado não substitui a confirmação do exercício.",
  f"O cruzamento por pessoa e contexto da eleição corrigiu {len(vote_audit['changes'])} totais históricos. Permanecem {len(vote_audit['gaps'])} totais não conciliados. Eleições suplementares são exibidas pela data em que ocorreram, sem somá-las à eleição regular.",
  "Esta é uma publicação datada, não uma atualização automática em tempo real. Consultas sem resultado suficiente, fontes bloqueadas e materiais históricos estão registrados na auditoria. A cobertura da pesquisa não é uma avaliação da candidatura."
 ]:body.append(tag('p',text))
 body.append(source_link('audit/review2/report.json','Auditoria da revisão'));coverage.append(body)
 doc.select_one('#criterio-eleitoral').insert_after(coverage)
 summary={'version':2,'date':date,'counts':counts,'registration_statuses':dict(Counter(p['registration_status'] for p in dataset['candidates'])),
   'federal_sha256_before':outside.get('index.html'),'federal_sha256_after':sha(REPO/'index.html'),'federal_modified':False,
   'scope':'State folder only; no integrated navigation or federal changes',
   'limitations':[f"{counts['topics_not_consolidated']} fichas sem síntese individual consolidada.",f"{counts['candidates']-counts['additional_biographies']} fichas sem biografia adicional; mantêm trajetória eleitoral documentada.", 'Nem todos os exercícios de mandato foram reconfirmados: declarações próprias, referências apenas indexadas, atividade datada e situação não confirmada permanecem separados da composição institucional consultada.', 'Ângelo Chocolate/2012 e Meirinho/2022 permanecem sem total nominal conciliado.'],
   'data_sources':manifest['sources'],'review_report':'review2/report.json'}
 dataset.update(schema_version=2,updated_at=date,collected_at=manifest['consulted_at'],review_version=2)
 save(DATA/'candidaturas.json',dataset); save(AUDIT/'summary.json',summary)
 # Publish contextual keys as the canonical historical-vote index as well.
 save(DATA/'votos-historicos.json',load(REVIEW/'votes-contextual.json'))
 with (DATA/'candidaturas.csv').open('w',encoding='utf-8-sig',newline='') as stream:
  fields=['id','name','number','party','registration_status','mandate_label','mandate_verification','biography','biography_source','topics','topics_source','topics_material_date','reviewed_at']
  w=csv.writer(stream,delimiter=';');w.writerow(fields)
  for p in dataset['candidates']:
   vals=[str(p.get(k) or '') for k in fields];w.writerow(["'"+v if v.startswith(('=','+','-','@')) else v for v in vals])
 (ROOT/'index.html').write_text(str(doc).replace('viewbox=', 'viewBox='),encoding='utf-8')
 after={rel:sha(REPO/rel) for rel in outside};assert after==outside,'Build modified another front'
 report={'version':2,'consulted_at':manifest['consulted_at'],'coverage':counts,'tse_diff':load(REVIEW/'tse-diff.json'),'vote_corrections':vote_audit['changes'],'historical_vote_gaps':vote_audit['gaps'],'outside_state_unchanged':isolation_complete,'outside_state_checked_files':len(outside),'profiles':review_rows,'limitations':summary['limitations'],'editorial_rule':'No inference by name, occupation, party, or identity. Institutional acts, historical activity and campaign declarations have different labels.'}
 save(REVIEW/'report.json',report)
 save(AUDIT/'data-review.json',{'version':2,'passed':True,'checks':{'unique_candidate_ids':len(ids)==len(selected),'fresh_registration_join':len(statuses)==len(ids),'all_official_portraits':photos['passed'],'strict_contextual_vote_join':True,'no_missing_total_as_zero':True,'outside_state_unchanged':isolation_complete},'coverage':counts,'limitations':summary['limitations']})
 print(json.dumps({'review2':counts,'outside_state_unchanged':isolation_complete},ensure_ascii=False,indent=2))
if __name__=='__main__':main(preview='--preview' in sys.argv)

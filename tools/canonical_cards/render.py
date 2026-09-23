"""Canonical-card prototype renderer; moves existing nodes, never rewrites prose."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import html, json, posixpath, re
from datetime import datetime
from bs4 import BeautifulSoup, NavigableString
from model import MANDATE_LABELS,HISTORY_LABELS,COVERAGE_LABELS,safe_url
E=html.escape
SEMANTIC={'current_support':'Apoio ou prioridade atual documentada','documented_topic':'Posição ou atuação documentada','legacy_context':'Contexto da pesquisa — sem promoção automática a apoio atual'}

def original_signature(card):
 c=BeautifulSoup(str(card),'html.parser').select_one('article')
 for x in c.select('.cc-added'):x.decompose()
 for x in list(c.select('.cc-wrapper')):x.unwrap()
 # Compare actual text atoms and original destinations, independent of rearrangement.
 texts=Counter(str(x).strip() for x in c.descendants if isinstance(x,NavigableString) and str(x).strip())
 links=Counter((x.name,x.get('href',x.get('src','')),x.get('id','')) for x in c.select('a[href],img[src]'))
 attrs={k:v for k,v in c.attrs.items() if k.startswith('data-') or k=='id'}
 return {'texts':dict(texts),'links':sorted((list(k),v) for k,v in links.items()),'attrs':attrs}

def fragment(text):return BeautifulSoup(text,'html.parser')
def added(text):
 n=fragment(text).find();n['class']=list(n.get('class',[]))+['cc-added'];return n

def text(value):
 return E(str(value)) if value not in (None,'') else 'Não informada neste registro'

LABELS = {'apoio':'Apoio declarado','prioridade':'Prioridade declarada','apoio_ou_prioridade':'Apoio ou prioridade declarada','atuacao':'Atuação','atuacao_documentada':'Atuação documentada','autodefinicao':'Autodefinição','debate':'Participação em debate','oposicao':'Oposição declarada','proposta':'Proposta',
 'apoio_atual_a_medida':'Apoio atual a uma medida','atribuicao_conjunta_pendente':'Atribuição conjunta ainda pendente','atuacao_parlamentar_ou_publica':'Atuação parlamentar ou pública','campaign_statement':'Declaração de campanha','candidate_statement':'Declaração da candidatura','documented_mixed':'Documentação de naturezas diferentes','historical_record':'Registro histórico','historical_statement':'Declaração de período anterior','legislative_record':'Registro legislativo','legislative_statement':'Declaração em contexto legislativo','trajectory':'Trajetória','campanha':'Publicação de campanha','declaracao_direta':'Declaração direta','imprensa_com_declaracao_identificada':'Imprensa com declaração atribuída','institucional':'Documento institucional','legislativo':'Documento legislativo','oposicao_atual':'Oposição atual','partidaria_individual':'Publicação partidária individual','periodo_nao_confirmado':'Período não confirmado','posicao_publica_atual':'Posição pública atual','prioridade_atual_explicita':'Prioridade atual explícita','registro_historico':'Registro histórico','historico':'Período anterior; ver o documento','sem_data':'Data não identificada'}

def human(value):return LABELS.get(value,value) if isinstance(value,str) else value

def date_text(value):
 if not value:return 'Não informada neste registro'
 try:return datetime.fromisoformat(str(value).replace('Z','+00:00')).strftime('%d/%m/%Y')
 except ValueError:return text(value)

def source_html(s):
 anchor=f'<a href="{E(s["url"],quote=True)}" rel="noopener noreferrer" target="_blank">{text(s["title"])}</a>' if s['url'] else text(s['title'])
 return '<div class="cc-source">'+anchor+f'<p>Publicação: {date_text(s["published_at"])} · Consulta: {date_text(s["consulted_at"])}</p><p>Localizador no documento: {text(s["locator"])}</p>'+ (f'<p class="cc-limit">{text(s["limitation"])}</p>' if s.get('limitation') else '')+'</div>'

def transparency(m, labels):
 identity=m['identity'];r=m['registration'];mand=m['mandate'];hist=m['history'];cov=m['coverage'];cid=m['candidate_id']
 note='A data do conjunto de dados não é confirmação individual mais recente.' if r['date_scope']=='dataset' else 'Situação registrada na consulta de origem, não uma nova consulta eleitoral.'
 facts=[('Eleição',f'{identity["year"]} · {identity["state"]} · {identity["office"]}'),('Registro eleitoral',r['label'] or 'Situação não estruturada neste conjunto'),('Consulta eleitoral',date_text(r['date']) if r['date'] else 'Data individual não estruturada'),('Revisão da pesquisa',date_text(cov['review_date']) if cov['review_date'] else 'Data de revisão individual não informada'),('Mandato',MANDATE_LABELS[mand['state']]),('Histórico eleitoral',HISTORY_LABELS[hist['state']]),('Cobertura',COVERAGE_LABELS[cov['state']])]
 body='<dl class="cc-data">'+''.join(f'<div><dt>{E(k)}</dt><dd>{text(v)}</dd></div>' for k,v in facts)+'</dl>'
 if r['apt'] is not None:body+=f'<p>Aptidão indicada no campo da API: <strong>{"sim" if r["apt"] is True else "não"}</strong>. Esse campo não foi calculado a partir do nome da situação.</p>'
 else:body+='<p>A aptidão não foi inferida do rótulo do registro. Recurso, decisão cadastral e aptidão são informações distintas.</p>'
 if r['source']:body+=f'<p><a href="{E(r["source"],quote=True)}" target="_blank" rel="noopener noreferrer">Consultar o cadastro de origem</a></p>'
 if mand['note']:body+=f'<p class="cc-mandate-note">{text(mand["note"])}</p>'
 for u in mand['sources']:body+=f'<p><a href="{E(u,quote=True)}" target="_blank" rel="noopener noreferrer">Documento usado para descrever o mandato</a></p>'
 if mand.get('observed_at'):body+=f'<p>Consulta do registro de mandato: {date_text(mand["observed_at"])}</p>'
 body+=f'<p class="cc-limit">{note} Ausência de confirmação de mandato não comprova ausência de exercício. Não localizar material suficiente também não significa ausência de propostas.</p>'
 for lim in cov['limitations']:body+=f'<p class="cc-limit">{text(lim)}</p>'
 if m['observations'].get('wording_date'):body+=f'<p>Reorganização da redação de origem: {text(m["observations"]["wording_date"]["value"])}. A data de redação não substitui a data da pesquisa.</p>'
 return added(f'<details class="cc-transparency" id="cc-{cid}-contexto"><summary>De onde vêm estas informações?</summary><div class="cc-detail-body">{body}</div></details>')

def evidence_panel(m, labels):
 if not m['evidence']:return None
 cid=m['candidate_id'];topics=list(dict.fromkeys(t for ev in m['evidence'] for t in ev['native_topics']))
 buttons='<div class="cc-evidence-controls" hidden><p>Ver os registros relacionados a um tema:</p><div>'+''.join(f'<button type="button" data-cc-topic="{E(t,quote=True)}" aria-pressed="false">{E(labels.get(t,t))}</button>' for t in topics)+'<button type="button" data-cc-reset>Ver todo o contexto</button></div></div>'
 items=[]
 for i,ev in enumerate(m['evidence']):
  caution='As fontes abaixo sustentam a síntese como conjunto. Não foi inventada uma relação de cada frase com cada fonte.' if ev['granularity']=='whole_synthesis' else 'O vínculo corresponde ao registro descrito abaixo, não a todas as medidas possíveis dentro do tema.'
  terms=' · '.join(labels.get(t,t) for t in ev['native_topics'])
  fields=[('Natureza',ev['nature']),('Sentido declarado',ev['direction']),('Período do conteúdo',ev['period']),('Objeto delimitado',ev['object'])]
  details='<dl class="cc-evidence-meta">'+''.join(f'<div><dt>{E(k)}</dt><dd>{text(human(v))}</dd></div>' for k,v in fields)+'</dl>'
  items.append(f'<li data-cc-evidence="{E(ev["native_id"],quote=True)}" data-cc-topics="{E(" ".join(ev["native_topics"]),quote=True)}"><p class="cc-kicker">{E(SEMANTIC[ev["semantic"]])}</p><p class="cc-evidence-text">{E(ev["text"])}</p>'+ (f'<p class="cc-topic-label">{E(terms)}</p>' if terms else '')+f'<p class="cc-limit">{caution}</p>{details}'+''.join(source_html(s) for s in ev['sources'])+'</li>')
 return added(f'<details class="cc-proof" id="cc-{cid}-evidencias"><summary>Ler as evidências e seus limites</summary><div class="cc-detail-body"><p>Os temas orientam a leitura. Eles não dizem, sozinhos, que a candidatura apoia todas as propostas ligadas ao assunto.</p>{buttons}<p class="cc-evidence-status" role="status" aria-live="polite"></p><ol class="cc-evidence-list">'+''.join(items)+'</ol></div></details>')

def enhance_card(card,m,labels):
 if card.get('data-canonical-card'):return card
 before=original_signature(card)
 card['data-canonical-card']='1.0.0';card['class']=list(card.get('class',[]))+['cc-card'];cid=m['candidate_id']
 ident=m['identity'];header=card.find('header',recursive=False)
 if not header:raise ValueError('Identity header missing')
 header.insert_before(added(f'<p class="cc-context">{E(ident["office"])} · {E(ident["state"])} · Eleição {ident["year"]}</p>'))
 copy_node=card.select_one('.candidate-copy')
 if not copy_node:raise ValueError('Missing narrative container')
 title=added(f'<h4 class="cc-reading-title" id="cc-{cid}-leitura">O que encontramos</h4>')
 # Leave original actions and legacy identity intact; hide duplication only in CSS.
 actions=copy_node.select_one('.eef-card-actions')
 if actions:actions.insert_after(title)
 else:copy_node.insert(0,title)
 menu=added(f'<nav class="cc-card-nav" aria-label="Seções da ficha de {E(ident["name"],quote=True)}"><a href="#cc-{cid}-leitura">Leitura</a><a href="#cc-{cid}-contexto">Origem e limites</a>'+ (f'<a href="#cc-{cid}-evidencias">Evidências</a>' if m['evidence'] else '')+'</nav>')
 header.insert_after(menu)
 career_nodes=[]
 for node in list(card.find_all(recursive=False)):
  classes=set(node.get('class',[]))
  if 'career-band' in classes or classes.intersection({'state-history','rs-history'}):career_nodes.append(node)
  elif node.name=='details' and 'card-details' in classes and 'current-evidence' not in classes:
   summary=node.find('summary')
   if summary and 'Trajetória' in summary.get_text():career_nodes.append(node)
 if career_nodes:
  wrapper=fragment('<details class="cc-history cc-wrapper"><summary class="cc-added">Mandato e histórico eleitoral</summary><div class="cc-history-inner cc-wrapper"></div></details>').details
  container=wrapper.select_one('.cc-history-inner')
  for node in career_nodes:container.append(node.extract())
  card.append(wrapper)
 # Group declared channels without losing their original labels, links or warnings.
 channels=card.select_one('.candidate-links')
 if channels:
  wrapper=fragment('<details class="cc-channels cc-wrapper"><summary class="cc-added">Canais públicos e endereços declarados</summary></details>').details
  wrapper.append(channels.extract());card.append(wrapper)
 card.append(transparency(m,labels));proof=evidence_panel(m,labels)
 if proof:card.append(proof)
 # New original-article marker is implementation metadata, not source data.
 card.attrs.pop('data-canonical-card')
 after=original_signature(card)
 if before!=after:raise ValueError('Substantive preservation failed '+m['key'])
 card['data-canonical-card']='1.0.0'
 return card

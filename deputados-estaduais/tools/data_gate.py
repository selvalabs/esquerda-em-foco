"""Publication checks and transparent coverage notes for the dated state snapshot."""
from pathlib import Path
from collections import Counter
import json
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'data/candidaturas.json').read_text()); people=data['candidates']
source=json.loads((ROOT/'audit/official.json').read_text())
# These exact records were inspected in the TSE linked history and in the
# complete corresponding SC vote file. No verifiable nominal total matched.
# Preserve null; neither registration status nor an absent row proves zero votes.
reviewed={
 ('240002537807',2012,'240000008734',1):'O histórico vinculado registra a candidatura de 2012, mas não foi conciliado um total nominal no arquivo de votação de SC.',
 ('240002537819',2022,'240001647347',1):'O histórico vinculado registra a candidatura de 2022. O índice do TRE-SC também identifica Soldado Meirinho, número 77721; o total nominal não foi conciliado. A situação histórica Inapto não foi convertida em zero votos.'
}
missing=[]
for p in people:
 for h in p['history']:
  if h['votes'] is None:
   key=(p['id'],h['year'],h['historical_candidate_id'],h['round'])
   missing.append({'candidate_id':p['id'],'name':p['name'],'year':h['year'],'historical_candidate_id':h['historical_candidate_id'],'round':h['round'],'note':reviewed.get(key,'Nova lacuna: revisão necessária.')})
checks={
 'unique_candidate_ids':len({p['id'] for p in people})==len(people),
 'all_registrations_matched':data['counts']['registration_statuses_consolidated']==len(people),
 'all_official_portraits':all(p.get('portrait') and p['portrait'].get('source_kind')=='Arquivo oficial de fotos do TSE' for p in people),
 'only_explicitly_reviewed_vote_gaps':all((x['candidate_id'],x['year'],x['historical_candidate_id'],x['round']) in reviewed for x in missing),
 'all_vote_archives_read':all(source['sources'].get('votes_'+str(y),{}).get('complete') for y in {h['year'] for p in people for h in p['history']}),
 'no_unavailable_vote_total_used_as_zero':all(h['votes'] is None or (isinstance(h['votes'],int) and h['votes']>=0 and h['votes_source']) for p in people for h in p['history'])
}
statuses=dict(Counter(p['registration_status'] for p in people))
report={'passed':all(checks.values()),'checks':checks,'registration_statuses':statuses,'historical_vote_gaps':missing,'individual_topics_with_source':sum(bool(p.get('topics_source')) for p in people),'individual_topics_pending':[{'id':p['id'],'name':p['name']} for p in people if not p.get('topics_source')],'reviewed_additional_source':'https://www.tre-sc.jus.br/eleicoes/eleicoes-gerais-2022/resultados-do-1o-turno/votacao-do-candidato-por-secao','note':'Ausência de síntese verificada não significa ausência de propostas, trajetória ou atuação pública.'}
(ROOT/'audit/data-review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
if not report['passed']: raise SystemExit('Publication data review failed: '+str(checks))
soup=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
line=soup.select_one('.state-snapshot')
notice=soup.new_tag('span'); notice['class']='registration-summary'
notice.string='Situação cadastral na coleta: '+ '; '.join(f'{n} {status.lower()}' for status,n in statuses.items())+'.'
line.append(soup.new_tag('br')); line.append(notice)
notes=soup.select_one('.sources-note')
p=soup.new_tag('p'); p.string=f"A pesquisa reúne fontes individuais de pautas ou atuação em {report['individual_topics_with_source']} das {len(people)} fichas. As demais preservam o histórico e os canais declarados, sem receber automaticamente um programa a partir do partido."
notes.append(p)
gap_text='Totais históricos não conciliados: '+', '.join(f"{x['name']} ({x['year']})" for x in missing)+'. Eles permanecem como não consolidados, nunca como zero.' if missing else 'Todos os totais históricos desta edição foram conciliados.'
p=soup.new_tag('p'); p.string='As fotografias vêm do arquivo oficial do TSE de 2026 e foram vinculadas pelo identificador de cada registro. '+gap_text
notes.append(p)
(ROOT/'index.html').write_text(str(soup),encoding='utf-8')
summary=json.loads((ROOT/'audit/summary.json').read_text())
summary['registration_statuses']=statuses
summary['limitations']=[f"Pautas individuais com fonte: {report['individual_topics_with_source']} de {len(people)}. As demais não recebem propostas inferidas.",gap_text,'Exercício por suplência e licença são distintos de titularidade; as fontes têm data e podem ser atualizadas.']
(ROOT/'audit/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
readme=ROOT/'README.md'
if readme.exists(): readme.write_text(readme.read_text().replace('artefato privado de revisão','artefato temporário de revisão'),encoding='utf-8')
print(json.dumps({'data_review':checks,'coverage':data['counts'],'registration':statuses},ensure_ascii=False,indent=2))

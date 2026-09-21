"""Individually reviewed institutional records, not inferred from party positions."""
from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
UPDATES={
 '210002534588':{
  'pautas':'Apresentou o PL 3561/24 para que a orientação sexual das mulheres seja considerada no atendimento e nos exames preventivos de câncer no SUS. Na Câmara, também integra as comissões sobre feminicídios no RS e sobre violência obstétrica, e ocupa a primeira vice-presidência da comissão que discute a redução da jornada de trabalho. São registros de atuação legislativa, não uma afirmação de que as propostas já foram executadas.',
  'sources':[{'label':'Agência Câmara · PL 3561/24 · 17/06/2026','url':'https://www.camara.leg.br/noticias/1282430-comissao-aprova-projeto-que-inclui-orientacao-sexual-em-exames-preventivos-de-cancer'},{'label':'Câmara · comissões e cargos · consulta 21/09/2026','url':'https://www.camara.leg.br/deputados/220555'}]},
 '210002537057':{
  'pautas':'Em 2026, relatou na Câmara a proposta que originou a redução temporária de tributos para a indústria química. Na Comissão de Constituição e Justiça, apresentou parecer favorável à reestruturação do quadro de pessoal do TRT da 4ª Região. As referências distinguem sua função de relator da autoria dos projetos e não constituem um programa completo de campanha.',
  'sources':[{'label':'Agência Câmara · indústria química · 20/03/2026','url':'https://www.camara.leg.br/noticias/1255997-nova-lei-reduz-aliquotas-de-tributos-para-a-industria-quimica'},{'label':'Agência Câmara · TRT-4 · 10/07/2026','url':'https://www.camara.leg.br/noticias/1290340-comissao-aprova-reestruturacao-do-quadro-de-pessoal-do-trt-da-4-regiao'}]},
 '210002537066':{
  'pautas':'Apresentou o PL 1876/26 para inclusão automática na Tarifa Social de Energia de aposentados e pensionistas do regime geral que recebem até um salário mínimo, dispensando inscrição prévia no CadÚnico. Na Câmara, atua como relator da comissão externa sobre os danos das enchentes no RS. O projeto de tarifa social é uma proposta legislativa, não um benefício já concedido por essa iniciativa.',
  'sources':[{'label':'Agência Câmara · PL 1876/26 · 15/09/2026','url':'https://www.camara.leg.br/noticias/1304561-projeto-preve-inclusao-automatica-de-aposentados-de-baixa-renda-na-tarifa-social-de-energia-eletrica'},{'label':'Câmara · comissões e cargos · consulta 21/09/2026','url':'https://www.camara.leg.br/deputados/73486'}]},
 '210002534604':{
  'pautas':'Em pronunciamento registrado pela Rádio Câmara em agosto de 2026, defendeu o cumprimento do ECA Digital e a responsabilização de plataformas diante de conteúdos que coloquem crianças e adolescentes em risco. Também apoiou a suspensão de transmissões ao vivo do Discord no Brasil. Na Câmara, é relatora da comissão externa sobre feminicídios no Rio Grande do Sul.',
  'sources':[{'label':'Rádio Câmara · pronunciamento · 20/08/2026','url':'https://www.camara.leg.br/radio/1299149-PROJETOS-DE-LEI-AMPLIAM-ALCANCE-DO-BENEFICIO-DE-PRESTACAO-CONTINUADA'},{'label':'Câmara · comissões e cargos · consulta 21/09/2026','url':'https://www.camara.leg.br/deputados/74398'}]}
}
def run():
 path=ROOT/'data/rs/editorial.json';data=json.loads(path.read_text());ids={r['SQ_CANDIDATO'] for r in json.loads((ROOT/'data/rs/candidates-official.json').read_text())}
 for cid,value in UPDATES.items():
  assert cid in ids
  data[cid]={**value,'checked_at':'2026-09-21','source_type':'institutional_record'}
 path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 readme=ROOT/'docs/rs/README.md'
 if readme.exists():
  text=readme.read_text().replace('24 sínteses individuais de pautas','28 sínteses individuais de pautas e atuação').replace('outras 83 fichas','outras 79 fichas')
  readme.write_text(text,encoding='utf-8')
if __name__=='__main__':run()

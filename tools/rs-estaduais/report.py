"""Generate a handoff that separates technical acceptance from editorial coverage."""
from __future__ import annotations
import collections
import csv
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais'
P=ROOT/'rs/deputados-estaduais'

def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def run():
    records=load(D/'normalized.json')['candidates']
    report=load(A/'build-report.json')
    browser=load(A/'browser-qa.json',{})
    research=load(D/'web-research.json',{})
    official=load(D/'manifest.json')
    votes=load(A/'votes-coverage.json',{})
    tests=(A/'unit-tests.txt').read_text(encoding='utf-8') if (A/'unit-tests.txt').exists() else ''
    unit_ok=tests.rstrip().endswith('OK')
    technical_ok=unit_ok and browser.get('passed',False) and all(c['checks']['registro_validado'] for c in records)
    parties={}
    gaps=[]
    for party in sorted({c['party'] for c in records}):
        group=[c for c in records if c['party']==party]
        parties[party]={'records':len(group),'with_policy_summary':sum(bool(c['pautas']) for c in group),'with_documented_act':sum(bool(c['activities']) for c in group),'with_current_office_confirmation':sum(bool(c['current_office']) for c in group)}
    for c in records:
        cid=c['id'];web=research.get(cid,{})
        next_actions=[]
        if not c['pautas']:next_actions.append('Localizar e revisar uma fonte individual de pautas; não presumir pelo partido.')
        if not c['current_office']:next_actions.append('Verificar, quando pertinente, se existe mandato atual em fonte institucional datada.')
        if not c['activities']:next_actions.append('Pesquisar atos institucionais quando houver experiência de mandato; não confundir ausência na pesquisa com ausência de atuação.')
        past=[h for h in c['history'] if h['year']<2026]
        if any(h.get('votes') is None for h in past):next_actions.append('Completar votos históricos com recorte correto de UF, cargo, ano e turno.')
        gaps.append({'candidate_id':cid,'name':c['name'],'party':c['party'],'number':c['number'],'registration_reconciled':c['checks']['registro_validado'],'policy_summary':bool(c['pautas']),'institutional_act':bool(c['activities']),'current_office_confirmed':bool(c['current_office']),'previous_disputes':len({(h['year'],h['candidate_id']) for h in past}),'past_vote_rows_missing':sum(h.get('votes') is None for h in past),'web_audit_status':web.get('research_status','not_audited'),'declared_public_urls':web.get('valid_links',[]),'next_actions':next_actions,'source':c['tse_url']})
    save(A/'candidate-coverage.json',gaps)
    with (A/'candidate-coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
        fields=['candidate_id','name','party','number','registration_reconciled','policy_summary','institutional_act','current_office_confirmed','previous_disputes','past_vote_rows_missing','web_audit_status','source']
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';',quoting=csv.QUOTE_ALL,extrasaction='ignore');writer.writeheader();writer.writerows(gaps)
    delivery={'technical_gate':'passed' if technical_ok else 'pending_or_failed','editorial_gate':'complete' if all(c['pautas'] for c in records) else 'partial_with_explicit_gaps','scope_issue':5,'branch':'feat/rs-deputados-estaduais','route':'/rs/deputados-estaduais/','as_of':report['as_of'],'official_census':report['official_universe'],'scope_census':len(records),'registration_reconciled':report['registration_reconciled'],'official_photos':report['with_photo'],'policy_summaries':report['with_editorial_summary'],'policy_gaps':len(records)-report['with_editorial_summary'],'documented_acts_candidates':report['with_documented_activity'],'current_offices_confirmed':report['with_verified_current_office'],'past_history_candidates':report['with_previous_history'],'past_history_rows':report['previous_history_rows'],'past_vote_rows':votes.get('historical_rows_with_votes'),'past_vote_candidates':votes.get('candidates_with_past_votes'),'browser_checks':browser.get('check_count'),'unit_tests_passed':unit_ok,'by_party':parties,'html_sha256':report['html_sha256'],'snapshot_generated_at':official['snapshot_generated_at'],'publication_note':'Este relatório valida a edição gerada; a publicação em GitHub Pages depende do merge e da execução de deploy, que devem ser conferidos separadamente.'}
    save(A/'delivery-report.json',delivery)
    lines=['# RS / Deputados estaduais 2026 — entrega técnica e cobertura','',f'**Data da pesquisa:** {report["as_of"]}. **Snapshot TSE:** {official["snapshot_generated_at"]}.', '',f'**Situação:** interface e cadastro {"aprovados nos testes" if technical_ok else "com verificação pendente"}; pesquisa editorial aprofundada parcial, com lacunas identificadas por candidatura. Não se declara encerrado o escopo editorial completo.','', '## O que foi entregue','',f'A edição reúne {len(records)} candidaturas do recorte, de um universo oficial de {report["official_universe"]} registros de deputado estadual no RS. Todos os registros foram conciliados com fichas individuais do DivulgaCand e receberam retrato oficial. A extração não remove silenciosamente situações eleitorais diferentes de deferimento.','',f'A pesquisa oferece {report["with_editorial_summary"]} sínteses individuais de pautas ou temas documentados, atos institucionais em {report["with_documented_activity"]} fichas e {report["with_verified_current_office"]} mandatos atuais confirmados institucionalmente. Existem {report["with_previous_history"]} candidaturas com histórico eleitoral anterior vinculado e votos nominais conferidos para {votes.get("candidates_with_past_votes")} candidaturas, em {votes.get("historical_rows_with_votes")} registros históricos.','', 'A página possui busca sem distinção de acentos, filtros por partido, situação e histórico anterior, ordem diária determinística no fuso de São Paulo, links diretos para fichas, histórico expansível, fontes, retratos locais e downloads JSON/CSV. Não há pontuação, preferência editorial, previsão de eleição, rastreamento ou dados privados de cadastro nos exports.', '', '## Cobertura por partido','', '| Partido | Registros | Sínteses de pautas | Atos documentados | Mandatos atuais confirmados |','|---|---:|---:|---:|---:|']
    for party,counts in parties.items():lines.append(f'| {party} | {counts["records"]} | {counts["with_policy_summary"]} | {counts["with_documented_act"]} | {counts["with_current_office_confirmation"]} |')
    lines+=['','O PCO está no recorte herdado de RS/federais, mas não tem registro selecionado neste snapshot. A tabela descreve a cobertura da pesquisa, não avalia candidaturas ou partidos.','', '## Validações','',f'- Cadastro: identificadores, cargo, UF, número, partido, situação e conciliação individual. Testes unitários: {"PASS" if unit_ok else "não confirmados"}.',f'- Navegador Chromium: {browser.get("check_count",0)} verificações; resultado {"PASS" if browser.get("passed") else "não confirmado"}. Larguras 320, 360, 390, 768, 1024 e 1440, sem overflow horizontal nas verificações.','- Retratos: correspondência ao identificador TSE, integridade SHA-256 e carregamento de todas as imagens.','- Isolamento: o workflow bloqueia mudanças em SC/federais, SC/estaduais, RS/federais, navegação global, assets compartilhados, servidor e sitemap principal.','- SEO: canonical e metadados próprios, Open Graph, coleção estruturada sem posições classificatórias, manifesto e sitemap locais.','', '## Pendências concretas','',f'Faltam sínteses de pautas verificadas para **{len(records)-report["with_editorial_summary"]} candidaturas**. Os nomes e próximos passos estão em `candidate-coverage.csv` e `candidate-coverage.json`. Cadastros e biografias eleitorais disponíveis não são apresentados como substitutos de um programa individual.', '', 'A confirmação de mandatos atuais não foi concluída para todo o recorte. Perfis de campanha, resultados antigos e votações históricas não foram usados para inferir automaticamente exercício de cargo na data da pesquisa. A indisponibilidade de algumas páginas institucionais está registrada nos arquivos de consulta.', '', 'Também restam votos de parte das disputas históricas, pesquisa mais ampla de projetos/comissões e verificação detalhada de fontes externas além dos endereços declarados. Nenhuma ausência de dado significa ausência de atuação.', '', '## Organização e reprodução','', '- `data/rs-estaduais/`: projeções oficiais, metadados de origem, fotos, histórias, votos e revisão editorial.','- `rs/deputados-estaduais/`: página e recursos públicos da edição.','- `tools/rs-estaduais/`: coleta, conciliação, pesquisa, renderização, QA e relatório.','- `tests/rs-estaduais/`: invariantes de dados, fontes, privacidade e isolamento.','- `docs/rs-estaduais/`: baseline, testes, capturas, cobertura e pendências.','', '```bash','python tools/rs-estaduais/collect.py','python tools/rs-estaduais/research.py','python tools/rs-estaduais/votes.py','python tools/rs-estaduais/finalize_sources.py','python tools/rs-estaduais/build.py',"python -m unittest discover -s tests/rs-estaduais -p 'test_*.py' -v",'python tools/rs-estaduais/qa.py','```','', 'A coleta reaproveita o snapshot congelado. Atualizações eleitorais devem gerar uma nova edição auditada, com comparação das situações; não basta alterar a data de publicação. Os dados na pasta `raw` são projeções de colunas necessárias, e não uma cópia integral de cadastros pessoais. Hashes distinguem ZIP completo recebido de membro extraído por acesso parcial.','', '## Publicação','', 'A rota preparada é `/rs/deputados-estaduais/`. Esta entrega não altera a homepage, a navegação global nem o sitemap principal. Um arquivo de página gerado e um workflow verde, isoladamente, não comprovam que o endereço já foi publicado. O merge e o deploy devem ser verificados separadamente.','']
    (A/'ENTREGA.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(delivery,ensure_ascii=False,indent=2))

if __name__=='__main__':run()

"""Report actual A-D changes without equating an attempted search with completion.

The frozen electoral snapshot remains distinct from this editorial enrichment.
Routine regression tests do not replace the separately planned final E/F review.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import json
import re
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
DOC=ROOT/'docs/rs-estaduais'
A=DOC/'phase2'
P=ROOT/'rs/deputados-estaduais'


def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def csv_export(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';',quoting=csv.QUOTE_ALL,extrasaction='ignore')
        writer.writeheader()
        for row in rows:
            out={key:row.get(key) for key in fields}
            for key,value in out.items():
                if isinstance(value,str) and value.startswith(('=','+','-','@','\t','\r')):out[key]="'"+value
            writer.writerow(out)


def run():
    A.mkdir(parents=True,exist_ok=True)
    base=load(A/'baseline.json')
    dataset=load(D/'normalized.json')
    candidates=dataset['candidates']
    by_id={c['id']:c for c in candidates}
    history=load(D/'history-normalized.json')
    old_gaps=set(base['policy_gap_ids'])
    now_gaps={c['id'] for c in candidates if not c['pautas']}
    recovered=sorted(old_gaps-now_gaps)
    vote_rows=load(A/'historical-vote-status.json')
    applied=load(A/'applied.json')
    source_review=load(D/'phase2-source-review.json',{})
    browser=load(DOC/'browser-qa.json',{})
    test_log=(DOC/'unit-tests.txt').read_text(encoding='utf-8')
    test_match=re.search(r'Ran (\d+) tests?',test_log)
    regression_ok=bool(test_log.rstrip().endswith('OK') and browser.get('passed'))
    final={
        'candidates':len(candidates),
        'policy_summaries':sum(bool(c['pautas']) for c in candidates),
        'policy_gaps':len(now_gaps),
        'current_offices':sum(bool(c['current_office']) for c in candidates),
        'with_activity':sum(bool(c['activities']) for c in candidates),
        'historical_vote_rows':sum(r['status']=='verified_nominal' for r in vote_rows),
        'candidates_with_historical_votes':len({r['candidate_id'] for r in vote_rows if r['status']=='verified_nominal'}),
        'reviewed_editorial_records':sum(bool(e.get('reviewed')) for e in load(D/'editorial.json',{}).values()),
    }
    initial={'candidates':base['candidate_count'],'policy_summaries':base['policy_summaries'],'policy_gaps':len(old_gaps),'current_offices':base['current_offices'],'with_activity':base['with_activity'],'historical_vote_rows':base['historical_vote_rows']}
    delta={key:final[key]-value for key,value in initial.items()}
    status_counts=dict(collections.Counter(r['status'] for r in vote_rows))
    checked_ids={r['candidate_id'] for r in applied.get('individual_checks',[])}
    office_input_ids=set()
    for path in D.glob('phase2-offices*.json'):office_input_ids.update(load(path,{}))
    source_attempt_ids={r['candidate_id'] for category in ('access_cases','content_cases','unresolved_named_searches') for r in source_review.get(category,[]) if r.get('candidate_id')}
    attempted_ids=checked_ids|office_input_ids|source_attempt_ids
    coverage=[]
    for c in candidates:
        cid=c['id'];past=[h for h in history.get(cid,[]) if h['year']<2026]
        nominal_unknown=[h for h in past if h.get('votes_status') in ('source_has_no_matching_record','source_collection_failed_or_unavailable','round_not_confirmed','office_not_mapped')]
        not_applicable=[h for h in past if h.get('votes_status','').startswith('not_applicable_')]
        other_scope=[h for h in past if h.get('votes_status')=='national_or_other_uf_not_collected']
        activity_missing_numbers=[x for x in c['activities'] if x.get('kind') in ('bill_authorship_report','bill_approval_report','request_authorship_report') and not x.get('proposal_number')]
        status='new_summary_reviewed' if cid in recovered else 'new_other_evidence_reviewed' if cid in checked_ids|office_input_ids else 'additional_attempt_without_verified_summary' if cid in source_attempt_ids else 'no_additional_phase2_review_recorded'
        next_steps=[]
        if not c['pautas']:next_steps.append('Localizar e ler fonte individual de pautas; não presumir pelo partido.')
        if not c['current_office']:next_steps.append('Confirmar exercício atual em fonte institucional quando houver indício de mandato; desconhecido não significa ausência de cargo.')
        if not c['activities']:next_steps.append('Pesquisar atuação institucional quando pertinente; não exigir histórico legislativo de quem não teve mandato.')
        if activity_missing_numbers:next_steps.append('Conferir número/processo das proposições relatadas em notícia institucional sem esse identificador.')
        if nominal_unknown:next_steps.append('Reconciliar os registros nominais restantes com a mesma unidade eleitoral, cargo, ano e turno.')
        if other_scope:next_steps.append('Obter total da população eleitoral correta para a disputa fora do recorte RS.')
        coverage.append({'candidate_id':cid,'name':c['name'],'party':c['party'],'ballot_number':c['number'],'summary_before':cid not in old_gaps,'summary_after':bool(c['pautas']),'summary_new':cid in recovered,'current_office_confirmed':bool(c['current_office']),'current_office_label':(c['current_office'] or {}).get('label'),'institutional_act_available':bool(c['activities']),'phase2_review_status':status,'past_verified_rows':sum(h.get('votes_status')=='verified_nominal' for h in past),'past_nominal_unknown_rows':len(nominal_unknown),'past_ticket_not_applicable_rows':len(not_applicable),'past_other_population_rows':len(other_scope),'acts_without_process_number_in_source':len(activity_missing_numbers),'next_steps':next_steps,'source':c['tse_url']})
    unresolved=[]
    for item in vote_rows:
        if item['status']=='verified_nominal':continue
        unresolved.append({**item,'name':by_id[item['candidate_id']]['name'],'party':by_id[item['candidate_id']]['party']})
    by_party={}
    for party in sorted({c['party'] for c in candidates}):
        rows=[c for c in coverage if c['party']==party]
        by_party[party]={'records':len(rows),'summary_before':sum(c['summary_before'] for c in rows),'summary_after':sum(c['summary_after'] for c in rows),'new_summaries':sum(c['summary_new'] for c in rows),'remaining_summaries':sum(not c['summary_after'] for c in rows),'current_offices_confirmed':sum(c['current_office_confirmed'] for c in rows),'with_institutional_act':sum(c['institutional_act_available'] for c in rows)}
    report={
        'reported_at':datetime.now(timezone.utc).isoformat(),
        'cutoff':'2026-09-21','branch':'feat/rs-deputados-estaduais','issue':5,'pr':9,
        'baseline_head':base['source_head'],'before':initial,'after':final,'delta':delta,
        'new_summary_ids':recovered,'remaining_summary_ids':sorted(now_gaps),
        'phase2_editorial_evidence_reviewed_candidates':len(checked_ids),
        'phase2_office_inputs':len(office_input_ids),
        'phase2_additional_attempt_or_evidence_candidates':len(attempted_ids),
        'all_initial_gaps_exhaustively_reviewed':False,
        'historical_rows_total':len(vote_rows),'historical_vote_status':status_counts,
        'by_party':by_party,
        'stages':{'A':'executed_with_remaining_individual_research','B':'executed_current_directory_coverage_incomplete','C':'expanded_primary_records_not_exhaustive','D':'recovered_older_totals_and_classified_unresolved_records','E':'not_executed_as_final_independent_review','F':'not_executed_as_final_electoral_refresh_and_release_gate'},
        'regression_gate':'passed' if regression_ok else 'failed_or_unconfirmed',
        'unit_test_count':int(test_match[1]) if test_match else None,
        'browser_check_count':browser.get('check_count'),
        'electoral_snapshot_refreshed_in_this_phase':False,
        'electoral_snapshot_generated_at':load(D/'manifest.json')['snapshot_generated_at'],
        'html_sha256':hashlib.sha256((P/'index.html').read_bytes()).hexdigest(),
        'merge_performed':False,'publication_performed':False,
        'limitations':['Sínteses de temas não equivalem a programas completos ou a fichas integralmente concluídas.','O inventário inicial de links cobre todos os registros, mas a pesquisa complementar desta fase não foi exaustiva para todas as lacunas.','Fontes institucionais indisponíveis impedem confirmação mais abrangente de mandatos estaduais e municipais.','Notícias de gabinete hospedadas em portais institucionais são identificadas e suas alegações não são adotadas como constatações independentes.','Registros de vice/suplência não têm voto nominal próprio e não são tratados como falha de pesquisa.','As regressões técnicas desta fase não substituem a revisão E/F e não autorizam merge automático.']
    }
    save(A/'report.json',report);save(A/'candidate-coverage.json',coverage);save(A/'historical-vote-pendencies.json',unresolved)
    fields=['candidate_id','name','party','ballot_number','summary_before','summary_after','summary_new','current_office_confirmed','current_office_label','institutional_act_available','phase2_review_status','past_verified_rows','past_nominal_unknown_rows','past_ticket_not_applicable_rows','past_other_population_rows','acts_without_process_number_in_source','source']
    csv_export(A/'candidate-coverage.csv',coverage,fields)
    csv_export(A/'historical-vote-pendencies.csv',unresolved,['candidate_id','name','party','historical_id','year','round','office','uf','electoral_unit','status'])
    lines=['# RS / Deputados estaduais — execução A–D','', '**Corte editorial:** 21/09/2026. **Branch:** `feat/rs-deputados-estaduais`. **Issue:** #5. **PR:** #9.','', '**Entrega incremental, sem merge ou publicação.** A–D receberam pesquisa, implementação e atualizações de dados. A pesquisa não foi encerrada para todas as candidaturas; E e F continuam reservados à revisão final.','', '## Comparativo verificável','', '| Cobertura | Antes | Depois | Variação |','|---|---:|---:|---:|',f'| Candidaturas no recorte | {initial["candidates"]} | {final["candidates"]} | {delta["candidates"]:+d} |',f'| Sínteses de pautas ou temas com fonte | {initial["policy_summaries"]} | {final["policy_summaries"]} | {delta["policy_summaries"]:+d} |',f'| Candidaturas ainda sem síntese | {initial["policy_gaps"]} | {final["policy_gaps"]} | {delta["policy_gaps"]:+d} |',f'| Mandatos atuais confirmados | {initial["current_offices"]} | {final["current_offices"]} | {delta["current_offices"]:+d} |',f'| Fichas com atos ou registros institucionais | {initial["with_activity"]} | {final["with_activity"]} | {delta["with_activity"]:+d} |',f'| Registros históricos com votos conferidos | {initial["historical_vote_rows"]} | {final["historical_vote_rows"]} | {delta["historical_vote_rows"]:+d} |','', 'As linhas medem cobertura documental, não avaliam candidaturas. Uma mesma pessoa pode estar em vários grupos. Síntese de temas, confirmação de cargo e registro de um ato são verificações diferentes.','', '## A — Pautas individuais','',f'Foram acrescentadas {len(recovered)} sínteses às {initial["policy_summaries"]} existentes. As adições usam páginas individuais, programas legíveis, entrevistas e registros institucionais identificados. Restam {len(now_gaps)} candidaturas sem síntese temática. Não se afirma busca exaustiva de todas elas. A situação de cada ficha e os próximos passos estão em `candidate-coverage.csv` e `.json`.','', 'O programa de Humberto Matos foi recuperado no HTML, sem atribuir a ele respostas de formulário. A página de propostas de Vinicius Bondan foi ligada ao site individual, para evitar atribuição por domínio genérico. Materiais que ainda se apresentam como pré-campanha não substituem a situação de registro do TSE. Relatos de atuação anterior e prioridades gerais não foram apresentados como programas completos.','', '## B — Mandatos atuais','',f'Foram acrescentadas {applied["new_current_office_inputs"]} confirmações a partir de diretórios institucionais de Santa Maria, Passo Fundo e Caxias do Sul. O total confirmado nesta base é {final["current_offices"]}. Resultados eleitorais antigos, autodescrição de campanha e uma notícia pontual não foram convertidos em confirmação de exercício atual.','', 'O diretório da ALRS continuou sem leitura utilizável nas tentativas registradas. Também houve bloqueios de acesso em diretórios municipais. Essas limitações estão em `data/rs-estaduais/phase2-source-review.json`. Não confirmar um cargo significa informação desconhecida nesta edição, não inexistência de mandato.','', '## C — Atuação institucional','',f'A cobertura passou de {initial["with_activity"]} para {final["with_activity"]} fichas com atos ou registros institucionais. As adições incluem proposições, relatorias, composição de comissões, reuniões de frentes, pronunciamentos e pedidos de informação. Cada adição tem fonte e data; notícia de gabinete é identificada como tal.','', 'Quando a notícia não informou o dia do ato, registrou-se explicitamente a data da publicação, com `event_date: null`. Quando não informou número da proposição, o campo permanece nulo e a conferência do processo continua pendente. Aprovação legislativa não foi chamada de sanção; pedidos e denúncias não foram tratados como resultados ou irregularidades comprovadas.','', '## D — Históricos e votos','',f'A recuperação de fontes de 2004, 2006, 2008 e 2010 acrescentou {delta["historical_vote_rows"]} registros nominais conferidos, totalizando {final["historical_vote_rows"]} de {len(vote_rows)} linhas históricas. Em 2004, identificadores repetidos entre municípios exigiram incluir unidade eleitoral, cargo, turno, ano, número e nome civil no cruzamento. As quatro fontes antigas passaram pela validação contextual; cópias de auditoria preservam os resultados anteriores à revalidação.','', '| Situação histórica | Registros |','|---|---:|']
    labels={'verified_nominal':'Votação nominal conferida','source_has_no_matching_record':'Sem correspondência segura na fonte','source_collection_failed_or_unavailable':'Fonte não recuperada','not_applicable_vice_ticket':'Vice: votação nominal própria não se aplica','not_applicable_supplemental_ticket':'Suplência: votação nominal própria não se aplica','national_or_other_uf_not_collected':'Disputa fora da população RS coletada','round_not_confirmed':'Turno não confirmado','office_not_mapped':'Cargo não mapeado'}
    for key,value in status_counts.items():lines.append(f'| {labels.get(key,key)} | {value} |')
    lines+=['', 'Cada linha ainda sem votação aparece em `historical-vote-pendencies.csv`, separando ausência de correspondência, população não coberta e situações não aplicáveis. Nenhum nulo foi convertido em zero. O hash nacional do ZIP permanece nulo para acesso por intervalos; o membro RS completo possui CRC e SHA-256 próprios.','', '## Regressão e preservação','',f'Testes unitários: **{report["unit_test_count"]}**. Verificações Chromium: **{report["browser_check_count"]}**. Resultado combinado: **{report["regression_gate"]}**. O workflow verifica o isolamento das frentes existentes. Esses testes são regressões do incremento A–D, não declaração de encerramento da revisão editorial independente E/F.','',f'O cadastro eleitoral conserva o snapshot **{report["electoral_snapshot_generated_at"]}**. Não houve nova coleta eleitoral nesta fase nem alteração de data para simular atualização. A nova reconciliação TSE/DivulgaCand continua na etapa F.','', '## Continuidade','',f'Prosseguir com as {len(now_gaps)} sínteses pendentes, ampliar confirmação institucional de mandatos e conferir processos/atos sem identificador completo. Revisar as linhas nominais ainda sem correspondência ou fora do recorte, sem incluir vice/suplência nessa conta. Em seguida, executar E e F sobre a versão consolidada. A issue #5 e o PR #9 permanecem abertos; não houve merge ou publicação.','']
    (A/'ENTREGA-A-D.md').write_text('\n'.join(lines),encoding='utf-8')
    parent=DOC/'ENTREGA.md'
    if parent.exists():
        text=parent.read_text(encoding='utf-8')
        marker='\n## Incremento A–D\n'
        text=text.split(marker)[0]+marker+'\nRelatório específico: `phase2/ENTREGA-A-D.md`. Comparativo: `phase2/report.json`. Pendências diferenciadas: `phase2/candidate-coverage.csv` e `phase2/historical-vote-pendencies.csv`. A revisão E/F e a nova coleta eleitoral permanecem pendentes.\n'
        parent.write_text(text,encoding='utf-8')
    print(json.dumps({key:report[key] for key in ('before','after','delta','regression_gate','unit_test_count','browser_check_count','historical_vote_status')},ensure_ascii=False,indent=2))

if __name__=='__main__':run()

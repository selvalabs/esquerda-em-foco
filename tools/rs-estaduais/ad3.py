"""AD3 incremental edition. Historical recovery and current evidence remain separate.
Only explicitly reviewed evidence is published. Queries and HTTP success do not
become policy evidence. Electoral sources keep their original snapshot dates.
"""
from __future__ import annotations
import argparse, collections, copy, csv, hashlib, html, importlib.util, json, os, re, subprocess
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';I=D/'ad3';A=ROOT/'docs/rs-estaduais/ad3';P=ROOT/'rs/deputados-estaduais'
BASE='b9ec0c352cdc0dc2a77be8ea4cf28469f1c09502';CUTOFF='2026-09-22'
LABELS={'policy_summary_verified':'Síntese com fonte individual','individual_sources_reviewed_insufficient':'Fontes consultadas: material insuficiente','source_access_blocked':'Leitura de fonte relevante bloqueada','identity_ambiguity':'Identidade da fonte ainda não conciliada','research_pending':'Pesquisa complementar pendente'}
FROZEN=['candidates-official.json','manifest.json','profiles-official.json','history-normalized.json','social-official.json','status-official.json','photos-official.json','votes-official.json','ad2-vote-index.json']
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def digest(obj):return hashlib.sha256(json.dumps(obj,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def baseline_bytes(path):
    if (ROOT/'.git').exists():return subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT)
    cache=os.environ.get('AD3_BASELINE_DIR')
    if cache:return (Path(cache)/path).read_bytes()
    raise RuntimeError('Full Git checkout or explicitly supplied frozen baseline required')
def base(path):return json.loads(baseline_bytes(path))
def valid_source(source):
    address=source.get('url',source.get('source',''));p=urlsplit(address)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.port not in (None,80,443):raise ValueError('Unsafe source URL')
    if not source.get('locator',source.get('source_locator')):raise ValueError('Source needs individual locator')
    checked=source.get('checked_at')
    if checked is None or date.fromisoformat(checked[:10])>date.fromisoformat(CUTOFF):raise ValueError('Missing or future check date')
    for field in ('published_at','event_date'):
        if source.get(field) and date.fromisoformat(source[field][:10])>date.fromisoformat(CUTOFF):raise ValueError('Future evidence')
def merge_unique(destination,additions):
    seen={digest(x) for x in destination}
    for item in additions:
        if digest(item) not in seen:destination.append(copy.deepcopy(item));seen.add(digest(item))
def apply_patches(editorial,offices,identities,patches,office_patches,corrections):
    editorial=copy.deepcopy(editorial);offices=copy.deepcopy(offices)
    for cid,patch in patches.items():
        if cid not in identities or patch['expected_name']!=identities[cid]['NM_URNA_CANDIDATO']:raise ValueError('Editorial identity mismatch: '+cid)
        if not patch.get('reviewed') or not patch.get('pautas') or not patch.get('sources'):raise ValueError('Missing reviewed individual evidence')
        for s in patch['sources']:valid_source(s)
        target=editorial.setdefault(cid,{})
        if target.get('pautas') and target['pautas']!=patch['pautas']:raise ValueError('Conflicting existing summary')
        target.update({k:patch[k] for k in ('pautas','pautas_type','checked_at','reviewed')})
        merge_unique(target.setdefault('sources',[]),patch['sources'])
        for act in patch.get('activities_append',[]):
            host=urlsplit(act['source']).hostname or ''
            if not host.endswith(('.gov.br','.leg.br')) or not act.get('kind') or not act.get('date'):raise ValueError('Act without primary dated reference')
            if act['date']>CUTOFF:raise ValueError('Future act')
        merge_unique(target.setdefault('activities',[]),patch.get('activities_append',[]))
    for cid,patch in office_patches.items():
        if cid not in identities or patch['expected_name']!=identities[cid]['NM_URNA_CANDIDATO']:raise ValueError('Office identity mismatch')
        value={k:v for k,v in patch.items() if k!='expected_name'}
        if value.get('verification')!='current_directory' or not value.get('directory_rendered_sha256') or not value.get('legislature'):raise ValueError('Office lacks current directory context')
        if not (urlsplit(value['source']).hostname or '').endswith(('.leg.br','.gov.br')):raise ValueError('Institutional source required')
        valid_source(value)
        if cid in offices and offices[cid]!=value:raise ValueError('Existing office conflict')
        offices[cid]=value
    for correction in corrections:
        cid=correction['candidate_id']
        if cid not in identities or correction['expected_name']!=identities[cid]['NM_URNA_CANDIDATO']:raise ValueError('Correction identity mismatch')
        if correction['action']!='withdraw_unconfirmed_individual_activity':raise ValueError('Unsupported correction')
        for s in correction['sources']:valid_source(s)
        activities=editorial[cid].get('activities',[]);matches=[x for x in activities if x['source']==correction['matched_source']]
        if len(matches)>1:raise ValueError('Ambiguous correction')
        if matches and digest(matches[0])!=correction['expected_before_sha256']:raise ValueError('Unexpected previous record')
        editorial[cid]['activities']=[x for x in activities if x['source']!=correction['matched_source']]
    return editorial,offices

def counts(records):
    return {'candidates':len(records),'summaries':sum(bool(c['pautas']) for c in records),'summary_gaps':sum(not c['pautas'] for c in records),'current_offices':sum(bool(c['current_office']) for c in records),'candidates_with_acts':sum(bool(c['activities']) for c in records),'acts':sum(len(c['activities']) for c in records),'historical_rows':sum(h['year']<2026 for c in records for h in c['history']),'verified_nominal_rows':sum(h['year']<2026 and h.get('votes') is not None for c in records for h in c['history'])}
def csv_write(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter=';',quoting=csv.QUOTE_ALL,extrasaction='ignore');writer.writeheader()
        for row in rows:
            out={}
            for k in fields:
                v=row.get(k)
                if isinstance(v,(dict,list)):v=json.dumps(v,ensure_ascii=False)
                if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')):v="'"+v
                out[k]=v
            writer.writerow(out)

def render():
    for name in ('research-ledger.json','follow-source-audit.json','historical-follow-up.json','offices.json','corrections.json','source-access.json'):
        if not (I/name).is_file():raise ValueError('Freeze source metadata first: '+name)
    before=base('data/rs-estaduais/normalized.json')['candidates']
    identities={r['SQ_CANDIDATO']:r for r in base('data/rs-estaduais/candidates-official.json')}
    frozen={name:hashlib.sha256(baseline_bytes('data/rs-estaduais/'+name)).hexdigest() for name in FROZEN}
    for name,checksum in frozen.items():
        if hashlib.sha256((D/name).read_bytes()).hexdigest()!=checksum:raise ValueError('Frozen electoral/history input changed: '+name)
    patches=load(I/'editorial.json');offpatch=load(I/'offices.json');corrections=load(I/'corrections.json')
    editorial,offices=apply_patches(base('data/rs-estaduais/editorial.json'),base('data/rs-estaduais/offices-verified.json'),identities,patches,offpatch,corrections)
    if (editorial,offices)!=apply_patches(editorial,offices,identities,patches,offpatch,corrections):raise ValueError('Patch replay changed result')
    save(D/'editorial.json',editorial);save(D/'offices-verified.json',offices)
    spec=importlib.util.spec_from_file_location('ad3_renderer',ROOT/'tools/rs-estaduais/build.py');builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder);builder.build()
    data=load(D/'normalized.json');records=data['candidates']
    research=load(I/'research-ledger.json');baseline_status={x['candidate_id']:x for x in base('data/rs-estaduais/research-status.json')}
    missing_before={c['id'] for c in before if not c['pautas']}
    if set(research)!=missing_before:raise ValueError('Research queue differs from baseline gaps')
    for cid,r in research.items():
        if identities[cid]['NM_URNA_CANDIDATO']!=r['expected_name']:raise ValueError('Ledger identity mismatch')
        if r['review_completed_in_round'] and cid not in patches and not r.get('completion_basis'):raise ValueError('Unsupported completion flag')
    ledger=[]
    for c in records:
        row=copy.deepcopy(baseline_status[c['id']]);r=research.get(c['id'])
        status='policy_summary_verified' if c['pautas'] else row['research_status']
        row.update({'research_status':status,'status_label':LABELS[status],'policy_summary':bool(c['pautas']),'policy_sources':c['editorial_sources'],'institutional_activity_count':len(c['activities']),'current_office_source':c['current_office'],'current_office_status':'confirmed_in_dated_institutional_source' if c['current_office'] else 'not_confirmed','review_completed_in_round':bool(r and r['review_completed_in_round']),'ad3_research':r,'research_exhaustive':False,'next_action':'Auditoria editorial independente E; manter explícitos período e atribuição.' if c['pautas'] else 'Aprofundar fontes individuais; tentativas registradas não comprovam inexistência de propostas.'})
        c['research_status']={'status':status,'label':LABELS[status],'exhaustive':False,'review_completed_in_round':row['review_completed_in_round'],'editorial_reviewed_on':c.get('editorial_checked_at'),'electoral_snapshot_as_of':'21/09/2026 12:31:37','details_url':'pesquisa-status.json'}
        ledger.append(row)
    save(D/'normalized.json',data);save(P/'dados.json',data);save(D/'research-status.json',ledger)
    export={'phase':'RS-EST-AD3','candidate_count':len(records),'status_counts':dict(collections.Counter(x['research_status'] for x in ledger)),'definitions':LABELS,'candidates':ledger,'note':'Pesquisa AD3 parcial. Consultas e leituras são separadas de revisão concluída. Snapshot eleitoral de 21/09 não atualizado.'}
    save(P/'pesquisa-status.json',export);save(P/'pesquisa.json',export);save(A/'candidate-coverage.json',ledger)
    fields=['candidate_id','name','party','number','research_status','policy_summary','review_completed_in_round','institutional_activity_count','current_office_status','research_exhaustive','next_action','tse_url']
    csv_write(A/'candidate-coverage.csv',ledger,fields);save(ROOT/'docs/rs-estaduais/candidate-coverage.json',ledger);csv_write(ROOT/'docs/rs-estaduais/candidate-coverage.csv',ledger,fields)
    soup=BeautifulSoup((P/'index.html').read_text(),'html.parser')
    for c in records:
        article=soup.find(id='candidato-'+c['id']);status=c['research_status']['status']
        note='<details data-close-status="'+status+'" class="ad3-research-note"><summary>Estado da pesquisa: '+html.escape(LABELS[status])+'</summary><p>Este estado descreve a pesquisa, não uma avaliação da candidatura. <a href="pesquisa-status.json">Fontes, consultas e pendências individuais</a>. O cadastro eleitoral continua datado de 21/09/2026.</p></details>'
        article.select_one('.candidate-copy').append(BeautifulSoup(note,'html.parser').details)
        extra=[]
        for h in c['history']:
            if h.get('votes_evidence_id'):
                scope='Brasil, circunscrição nacional' if h['votes_electoral_unit']=='BR' else 'Rio Grande do Sul'
                extra.append('<p>'+str(h['year'])+' · total nominal conferido para '+scope+', '+str(h['round'])+'º turno. <a href="'+html.escape(h['votes_source'],quote=True)+'" target="_blank" rel="noopener noreferrer">Fonte TSE</a>.</p>')
            if h.get('historical_registration_review'):
                review=h['historical_registration_review'];extra.append('<p>'+str(h['year'])+' · cadastro histórico: '+html.escape(review.get('registration_status') or 'não informado')+'. Esta é a situação da disputa antiga, não de 2026. '+('Total nominal não confirmado; não se presume zero. ' if h.get('votes') is None else '')+'<a href="'+html.escape(review['source_url'],quote=True)+'" target="_blank" rel="noopener noreferrer">Ficha histórica</a>.</p>')
        if extra:article.select_one('.rs-history').insert_after(BeautifulSoup('<details class="ad3-history-note"><summary>Conferências adicionais do histórico</summary>'+''.join(extra)+'</details>','html.parser').details)
    for correction in corrections:
        article=soup.find(id='candidato-'+correction['candidate_id'])
        article.select_one('.candidate-copy').append(BeautifulSoup('<details class="ad3-research-note"><summary>Nota de revisão documental</summary><p>A listagem do SISTCOP foi retirada da contagem de atuação individual porque o vínculo documental não confirmou autoria ou participação. Não se conclui que a pessoa nunca tenha atuado no tema. <a href="revisoes.json">Evidências da revisão</a>.</p></details>','html.parser').details)
    soup.select_one('#fontes').append(BeautifulSoup('<p class="rs-data-links" id="ad3-research-method">Pesquisa editorial AD3: 22/09/2026. O cadastro eleitoral permanece referido ao snapshot de 21/09/2026 às 12:31:37. A pesquisa complementar não está integralmente encerrada. <a href="pesquisa-status.json">Cobertura individual</a> · <a href="revisoes.json">Revisões documentais</a></p>','html.parser'))
    style=soup.new_tag('style',id='ad3-audit-style');style.string='.ad3-research-note,.ad3-history-note{margin-top:14px;font-size:.79rem;line-height:1.55;overflow-wrap:anywhere}.ad3-research-note summary,.ad3-history-note summary{cursor:pointer;min-height:44px;padding:10px 0}.ad3-research-note p,.ad3-history-note p{margin:.5em 0 1em}.ad3-research-note :focus-visible,.ad3-history-note :focus-visible{outline:3px solid currentColor;outline-offset:3px}';soup.head.append(style)
    for ld in soup.select('script[type="application/ld+json"]'):
        obj=json.loads(ld.string);obj['dateModified']=CUTOFF;ld.string=json.dumps(obj,ensure_ascii=False).replace('</','<\\/')
    text=str(soup).replace('viewbox=','viewBox=');(P/'index.html').write_text(text,encoding='utf-8');html_sha=hashlib.sha256(text.encode()).hexdigest()
    save(P/'revisoes.json',{'phase':'RS-EST-AD3','corrections':corrections})
    provenance=load(P/'fontes.json');provenance['ad3']={'baseline':BASE,'editorial_inputs':patches,'office_inputs':offpatch,'corrections_url':'revisoes.json','research_url':'pesquisa-status.json','follow_up':load(I/'historical-follow-up.json'),'nominal_vote_evidence_preserved':base('data/rs-estaduais/ad2-vote-index.json'),'new_electoral_snapshot':False};save(P/'fontes.json',provenance)
    now=counts(records);oldcounts=counts(before);completed=sum(r['review_completed_in_round'] for r in research.values());attempted=sum(bool(r['queries'] or r['source_checks']) for r in research.values())
    result={'task':'RS-EST-AD3','status':'substantive_increment_partial','baseline_commit':BASE,'editorial_cutoff':CUTOFF,'electoral_snapshot_refreshed':False,'before':oldcounts,'after':now,'delta':{k:now[k]-oldcounts[k] for k in now},'research_queue_size':len(research),'candidates_with_recorded_queries_or_reads':attempted,'review_completed_in_round':completed,'partial_investigation':attempted-completed,'not_attempted':len(research)-attempted,'full_88_review_gate':completed==len(research),'executed_queries':sum(len(r['queries']) for r in research.values()),'new_summaries':len(patches),'new_mandates':len(offpatch),'new_acts':sum(len(p.get('activities_append',[])) for p in patches.values()),'withdrawn_unconfirmed_acts':len(corrections),'new_nominal_totals':0,'historical_registration_checks':len(load(I/'historical-follow-up.json')['records']),'nominal_totals_pending':11,'ticket_positions_no_own_nominal':26,'status_counts':export['status_counts'],'html_sha256':html_sha,'frozen_source_hashes':frozen,'merge_performed':False,'deployment_performed':False,'issue_closed':False,'E_F_completed':False}
    save(A/'baseline.json',{'commit':BASE,'metrics':oldcounts,'gap_ids':sorted(missing_before),'scope':'Exact original 88 missing summaries; no popularity ordering'})
    save(A/'research-queue.json',[{k:r[k] for k in ('candidate_id','expected_name','party','batch','review_completed_in_round')} for r in research.values()])
    for batch in sorted({r['batch'] for r in research.values()}):
        rows=[r for r in research.values() if r['batch']==batch];save(A/'batches'/f'{batch:02}.json',{'batch':batch,'identities':rows,'review_completed':sum(r['review_completed_in_round'] for r in rows),'new_summary_ids':[r['candidate_id'] for r in rows if r['candidate_id'] in patches],'status':'partial' if not all(r['review_completed_in_round'] for r in rows) else 'reviewed'})
    result.update({'current_phase':'RS-EST-AD3','technical_gate':'awaiting_current_tests','editorial_gate':'partial','scope_census':now['candidates'],'policy_summaries':now['summaries'],'policy_gaps':now['summary_gaps'],'current_offices_confirmed':now['current_offices'],'documented_acts_candidates':now['candidates_with_acts'],'past_vote_rows':now['verified_nominal_rows']})
    for path in (A/'report.json',ROOT/'docs/rs-estaduais/delivery-report.json',ROOT/'docs/rs-estaduais/build-report.json',P/'cobertura.json'):save(path,{**load(path,{}),**result})
    save(A/'historical-vote-pendencies.json',base('docs/rs-estaduais/ad2-close/historical-vote-pendencies.json'))
    csv_write(A/'historical-vote-pendencies.csv',load(A/'historical-vote-pendencies.json'),['candidate_id','name','historical_id','year','round','office','electoral_unit','status','requires_nominal_research'])
    print(json.dumps({k:result[k] for k in ('before','after','review_completed_in_round','partial_investigation','new_acts','withdrawn_unconfirmed_acts')},ensure_ascii=False))

def report():
    obj=load(A/'report.json');tests=(A/'unit-tests.txt').read_text();browser=load(A/'browser-qa.json')
    m=re.search(r'Ran (\d+) tests',tests)
    if not m or not tests.rstrip().endswith('OK') or not browser['passed']:raise ValueError('Current AD3 regression failed')
    historical=load(A/'historical-baseline-qa.json')
    if historical['baseline_commit']!=BASE or not historical['passed'] or historical['skipped_tests']:raise ValueError('Historical regression incomplete')
    obj.update({'technical_gate':'passed','current_unit_tests':int(m.group(1)),'current_browser_checks':browser['check_count'],'historical_baseline_tests':historical,'editorial_gate':'partial','scope_completed':obj['full_88_review_gate'],'validated_source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()})
    isolation_spec=importlib.util.spec_from_file_location('ad3_isolation_guard',ROOT/'tools/rs-estaduais/ad3_isolation.py')
    isolation_module=importlib.util.module_from_spec(isolation_spec);isolation_spec.loader.exec_module(isolation_module)
    isolation=isolation_module.audit()
    save(A/'isolation.json',isolation)
    obj['isolation_passed']=isolation['passed']
    obj['protected_paths']=[x['path'] for x in isolation['protected_checks']]
    obj['historical_preservation_baseline']=isolation['historical_preservation_baseline']
    obj['preexisting_recovery_report_refreshes']=[x['path'] for x in isolation['preexisting_historical_changes']]
    for path in (A/'report.json',ROOT/'docs/rs-estaduais/delivery-report.json',P/'cobertura.json'):save(path,{**load(path,{}),**obj})
    lines=['# RS-EST-AD3 — incremento substantivo, execução parcial','','**Dados e interface validados; pesquisa integral das 88 fichas não concluída.**','',f'Baseline: `{BASE}`. Código validado: `{obj["validated_source_commit"]}`.','','## Conteúdo incorporado','',f'{obj["new_summaries"]} novas sínteses, {obj["new_mandates"]} confirmações institucionais e {obj["new_acts"]} atos datados. Uma listagem com vínculo individual insuficiente foi retirada da contagem e preservada como revisão documental.','','| Indicador | Antes | Depois |','|---|---:|---:|']
    names={'candidates':'Candidaturas','summaries':'Sínteses','summary_gaps':'Sem síntese','current_offices':'Mandatos confirmados nas fontes datadas','candidates_with_acts':'Fichas com atos','acts':'Atos individuais documentados','historical_rows':'Linhas históricas','verified_nominal_rows':'Votos conferidos'}
    for k,label in names.items():lines.append(f'| {label} | {obj["before"][k]} | {obj["after"][k]} |')
    lines+=['','## Cobertura da investigação','',f'A fila contém {obj["research_queue_size"]} identidades. {obj["candidates_with_recorded_queries_or_reads"]} receberam consultas ou leituras registradas; {obj["review_completed_in_round"]} obtiveram evidência suficiente para novas sínteses. Os outros {obj["partial_investigation"]} casos têm investigação parcial. Não se confunde consulta nominal, disponibilidade HTTP ou simples classificação com pesquisa completa.', '',f'Foram registrados {obj["executed_queries"]} termos de busca efetivamente executados. Páginas sem conteúdo, homônimos, bloqueios e modelos provisórios não viraram pautas.','', '## Mandatos e revisão de atribuição','','Braite, Amaral Negrito e Danrlei Massena foram confirmados em diretórios da legislatura atual 2025–2028 como ativos e titulares, com perfis e nomes civis conciliados. As confirmações anteriores não foram redatadas.','','O registro SISTCOP 331235 aparece sob blogs de vereadores diferentes e não indica autoria. Um PDF de ementa semelhante possui protocolo 30650, de 23/12/2020, e outra assinatura. Esse protocolo não foi atribuído a Bruno Berté. O vínculo individual continua não confirmado; a listagem foi retirada da contagem, sem afirmar inexistência de atuação da pessoa no tema.','','## Histórico e limites','','Onze fichas históricas foram relidas, mas não forneceram totais novos. Permanecem onze totais sem correspondência segura e 26 posições de vice/suplência sem voto próprio. Nenhum indeferimento ou renúncia virou zero. A investigação nominal desses casos ainda precisa avançar além do cadastro.','','## Validação','',f'Testes atuais AD3: {obj["current_unit_tests"]}, sem skips. Controles de navegador atuais: {obj["current_browser_checks"]}. Os 92 testes e 63 controles da recuperação anterior foram executados separadamente no commit congelado, sem enfraquecer invariantes ou aplicá-las indevidamente a contagens novas.','','A integração é incremental e reproduzível. Foram preservados IDs, recorte, votos validados e datas eleitorais. Antes da integração incremental, o workflow antigo havia atualizado metadados e consultas de disponibilidade em cinco relatórios de recuperação. Essas mudanças preexistentes foram identificadas, mantiveram as métricas substantivas e o HTML anterior, e foram preservadas como recebidas. As evidências e as duas referências de isolamento estão em `isolation.json`; a comparação das demais frentes continua no baseline original.','','## GitHub e próxima etapa','','Mesma issue #5, PR #9 e branch. Sem merge, deploy ou alteração de outras frentes. Snapshot eleitoral: 21/09/2026 12:31:37. Pesquisa nova: 22/09/2026. Aprofundamento das lacunas, auditoria E e coleta/delta F permanecem pendentes.','','Evidências em `data/rs-estaduais/ad3/` e `docs/rs-estaduais/ad3/`: cobertura individual, lotes, nulos históricos, testes e relatório quantitativo.','']
    (A/'ENTREGA-AD3.md').write_text('\n'.join(lines),encoding='utf-8')
    path=ROOT/'docs/rs-estaduais/SOURCE-REVIEW.md';text=path.read_text()
    if '## AD3 — 22/09/2026' not in text:path.write_text(text+'\n\n## AD3 — 22/09/2026\n\nOnze novas sínteses e três novos mandatos documentados. O item SISTCOP 331235 foi retirado da contagem individual por vínculo insuficiente; fontes em `data/rs-estaduais/ad3/corrections.json`. A investigação da fila permanece parcial; relatório em `ad3/ENTREGA-AD3.md`.\n',encoding='utf-8')
    print(json.dumps(obj,ensure_ascii=False,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['render','report']);args=parser.parse_args();globals()[args.stage]()
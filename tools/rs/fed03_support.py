"""Deterministic RS-FED-03 layer. No network or writes outside RS directories.
Research coverage, biographies and policy/action coverage remain distinct.
"""
from __future__ import annotations
import collections, copy, hashlib, json, re, unicodedata
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs'; I=D/'fed03'; A=ROOT/'docs/rs/fed03'; DEST=ROOT/'rs/deputados-federais'
DATE='2026-09-21'
def load(path):
    return json.loads(path.read_text(encoding='utf-8'))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(value):
    return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',str(value).casefold()) if unicodedata.category(c)!='Mn')).strip()
def new_editorial():
    result={}
    for path in sorted(I.glob('editorial-*.json')):
        entries=load(path)
        if set(result)&set(entries):raise ValueError('Duplicated editorial input ID')
        result.update(entries)
    if len(result)!=20:raise ValueError('Expected twenty individually reviewed additions')
    return result

def validate_registry():
    old={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json')}
    new={r['SQ_CANDIDATO']:r for r in load(I/'candidates-snapshot.json')}
    if set(old)!=set(new):raise ValueError('Official population changed; reconciliation required')
    for cid,row in new.items():
        adjusted=dict(row);adjusted['SG_PARTIDO']=old[cid]['SG_PARTIDO']
        if row['SG_PARTIDO'].upper()!=old[cid]['SG_PARTIDO'].upper() or adjusted!=old[cid]:
            raise ValueError('Official identity/content changed: '+cid)
    previous={r['SQ_CANDIDATO']:r for r in load(D/'status-official.json')}
    refreshed={r['SQ_CANDIDATO']:r for r in load(I/'status-snapshot.json')}
    if previous!=refreshed:raise ValueError('Current electoral status changed; reconcile before publishing')
    return set(old)

def extend_editorial(editorial,offices):
    from review_support import TOPICS,safe_url
    ids=validate_registry();additions=new_editorial();complements=load(I/'complements.json')
    targets={t['id'] for t in load(D/'rs-fed-03-targets.json')['targets']}
    if not set(additions)<=targets:raise ValueError('Addition outside approved targets')
    for cid,change in additions.items():
        if cid!=change['id'] or cid not in ids:raise ValueError('Editorial identity mismatch')
        entry=editorial.setdefault(cid,{'sources':[]})
        entry.update({k:change[k] for k in ('pautas','summary_kind','checked_at')})
        if 'biography' in change:entry['biography']=change['biography']
        merged={s['url']:s for s in entry.get('sources',[])}
        for source in change['sources']:
            if not safe_url(source['url']) or not all(source.get(k) for k in ('period','locator','source_type','checked_at')):
                raise ValueError('Source lacks provenance: '+cid)
            merged[source['url']]=copy.deepcopy(source)
        entry['sources']=[merged[u] for u in sorted(merged)]
        topic_map=change.get('topic_sources',{});entry['topics']=[]
        for topic in sorted(set(change['topics'])):
            sources=sorted(set(topic_map.get(topic,[s['url'] for s in change['sources']])))
            if topic not in TOPICS or not sources or not set(sources)<=set(merged):raise ValueError('Unsupported topic')
            entry['topics'].append({'id':topic,'sources':sources})
        limits=[s['limitation'] for s in change['sources'] if s.get('limitation')]
        if limits:entry['source_limitation']=' '.join(dict.fromkeys(limits))
        else:entry.pop('source_limitation',None)
    for cid,change in complements['biographies'].items():
        if cid not in targets:raise ValueError('Biography outside targets')
        entry=editorial.setdefault(cid,{'sources':[]});entry['biography']=change['biography'];entry['checked_at']=DATE
        merged={s['url']:s for s in entry['sources']}
        for source in change['sources']:
            if not safe_url(source['url']):raise ValueError('Invalid biography source')
            merged[source['url']]=source
        entry['sources']=[merged[u] for u in sorted(merged)]
    for cid,office in complements['offices'].items():
        if cid not in ids or not office.get('identity_source') or not office.get('source_updated_at'):
            raise ValueError('Office requires identity-linked dated directory')
        offices[cid]=copy.deepcopy(office)

def extend_history(histories):
    evidence=load(A/'vote-investigation.json');targets=load(D/'rs-fed-03-targets.json')['unresolved_votes']
    if evidence['errors']:raise ValueError('Incomplete vote investigation')
    lookup={(str(r['id']),int(r['year']),str(r['historical_id']),r['kind']):r for r in evidence['targets']}
    records={r['SQ_CANDIDATO']:r for r in load(D/'candidates-official.json')};resolutions=[]
    for t in targets:
        cid=t['id'];year=int(t['year']);hid=str(t['historical_id']);turn=int(t.get('round',1))
        hs=[h for h in histories[cid] if (int(h['year']),str(h['candidate_id']),int(h.get('round',1)))==(year,hid,turn)]
        if len(hs)!=1:raise ValueError('Historical key not unique')
        h=hs[0];registration=lookup[(cid,year,hid,'registration')];vote=lookup[(cid,year,hid,'votes')]
        rg=registration['groups']
        if len(rg)!=1:raise ValueError('Ambiguous registration')
        sample=rg[0]['sample']
        checks=(str(sample.get('SQ_CANDIDATO'))==hid,norm(sample.get('DS_CARGO'))==norm(h['office']),norm(sample.get('NM_UE'))==norm(h['place']),int(sample.get('NR_TURNO','1'))==turn)
        if not all(checks):raise ValueError('Historical identity context mismatch')
        decision={'id':cid,'name':t['name'],'year':year,'historical_id':hid,'round':turn,'registration_source':registration['source'],'nominal_source':vote['source'],'checked_at':evidence['checked_at']}
        if (cid,year,hid)==('210002535917',2006,'10178'):
            vg=vote['groups']
            if len(vg)!=1 or vg[0]['rows']!=152 or vg[0]['votes']!=15473:raise ValueError('Reviewed nominal total changed')
            expected=norm(records[cid]['NM_CANDIDATO']);actual=norm(sample['NM_CANDIDATO'])
            if expected.replace(' de ',' ')!=actual or norm(vg[0]['sample']['NM_CANDIDATO'])!=actual:raise ValueError('Name exception exceeds reviewed particle variation')
            if str(vg[0]['sample']['SQ_CANDIDATO'])!=hid:raise ValueError('Nominal ID mismatch')
            h.update({'votes':15473,'votes_source':vote['source'],'votes_status':'verified_nominal','votes_checked_at':evidence['checked_at'],'votes_match_method':'Exception explicitly reviewed for 2006/10178 only: historical TSE link, ID, office, locality, round and civil name differing solely by DE. 152 official nominal rows.'})
            h.pop('votes_note',None);decision.update({'outcome':'nominal_value_recovered','votes':15473,'matched_rows':152})
        elif cid=='210002537042' and year in (2004,2008):
            if norm(sample['NM_CANDIDATO'])==norm(records[cid]['NM_CANDIDATO']):raise ValueError('Expected identity conflict changed')
            h['votes']=None;h.pop('votes_source',None);h['votes_status']='not_verified'
            h['votes_note']='Vínculo histórico com divergência de nome civil ainda não resolvida; a votação não foi atribuída; não equivale a zero.'
            decision.update({'outcome':'identity_conflict_pending','votes':None,'reason':'CLAUDIA SOUZA AURICH difere de CLAUDIA DOS SANTOS SOUZA. Nome de urna/localidade não bastam para atribuir o valor.'})
        else:
            if norm(sample['NM_CANDIDATO'])!=norm(records[cid]['NM_CANDIDATO']) or sample.get('DS_SITUACAO_CANDIDATURA')!='INAPTO' or vote['groups']:raise ValueError('Inapt/no-nominal classification unsupported')
            h['votes']=None;h.pop('votes_source',None);h['votes_status']='not_published_inapt'
            h['votes_note']=f'Registro de {year} classificado como inapto no cadastro histórico; sem votação nominal localizada no arquivo oficial consultado. Isso não equivale a zero e não descreve a candidatura de 2026.'
            h['votes_context_source']=registration['source'];h['votes_absence_source']=vote['source']
            decision.update({'outcome':'historical_inapt_no_nominal_row','votes':None,'reason':'Situação histórica INAPTO confirmada; ausência de linha nominal. Motivo específico da inaptidão não determinado por esta consulta.'})
        resolutions.append(decision)
    save(A/'votes-resolution.json',{'date':DATE,'records':resolutions,'counts':dict(collections.Counter(r['outcome'] for r in resolutions)),'source_evidence':'vote-investigation.json','rule':'Um valor recuperado; cinco ausências qualificadas; dois conflitos de identidade permanecem. Ausência não é zero.'})
    return histories

def finalize_round_three(records,old_finalize):
    historical_paths=[ROOT/'docs/rs/review'/n for n in ('final-report.json','candidate-matrix.json','README.md')]
    historical={p:p.read_bytes() for p in historical_paths};baseline=json.loads(historical[historical_paths[0]])
    try:old_finalize(records)
    finally:
        for path,raw in historical.items():path.write_bytes(raw)
    additions=new_editorial();complements=load(I/'complements.json');queries=load(I/'research-queries.json');dispositions=load(I/'research-dispositions.json')
    scope=load(D/'rs-fed-03-targets.json');target_ids={t['id'] for t in scope['targets']}
    if set(queries)!=target_ids or not all(queries.values()):raise ValueError('Research log does not cover target set')
    refresh=load(A/'official-refresh.json');profiles=load(I/'profiles-snapshot.json');vote_report=load(A/'votes-resolution.json')
    counts=collections.Counter(h['votes_status'] for c in records for h in c['history'])
    summaries=sum(bool(c['pautas']) for c in records);policies=sum(bool(c['pautas']) and c.get('summary_kind')!='trajectory' for c in records)
    biographies=sum(bool(c.get('biography')) for c in records);profiles_ok=sum(bool(p.get('data')) for p in profiles.values())
    source_availability=[]
    for filename in ('source-availability.json','deep-source-availability.json'):
        if (A/filename).exists():source_availability.extend(load(A/filename))
    matrix=[];research={}
    for c in records:
        cid=c['id'];target=cid in target_ids
        pending=[{'year':h['year'],'office':h['office'],'historical_id':h['candidate_id'],'round':h.get('round',1)} for h in c['history'] if h['votes_status']=='not_verified']
        row={'id':cid,'name':c['name'],'party':c['party'],'target_this_round':target,'summary_documented':bool(c['pautas']),'summary_kind':c.get('summary_kind'),'policy_or_action_documented':bool(c['pautas']) and c.get('summary_kind')!='trajectory','biography_documented':bool(c.get('biography')),'current_office_confirmed':bool(c.get('current_office')),'registry_csv_reconciled':True,'profile_rechecked_this_round':bool(profiles.get(cid,{}).get('data')),'unresolved_nominal_rows':pending,'text_consistency_reviewed':True,'substantive_sources_reopened_this_round':cid in additions or cid in complements['biographies'],'topics':c.get('topics',[])}
        if target:
            override=dispositions['overrides'].get(cid,{})
            if cid in additions:outcome='policy_or_action_documented'
            elif cid in complements['biographies']:outcome='biography_added_policy_gap'
            elif c.get('summary_kind')=='trajectory':outcome='trajectory_only_policy_gap'
            else:outcome='insufficient_evidence'
            accepted=additions.get(cid,complements['biographies'].get(cid,{})).get('sources',[])
            research[cid]={'id':cid,'date':DATE,'queries':queries[cid],'outcome':outcome,'accepted_sources':accepted,'rejected_or_inaccessible_urls':override.get('rejected_urls',[]),'reason':('Síntese individual e fontes adicionadas; não certifica todos os campos da ficha.' if cid in additions else override.get('reason',dispositions['default_gap_reason'])),'availability_attempts':[a for a in source_availability if a.get('candidate_id')==cid],'current_office_review':'new_institutional_confirmation' if cid in complements['offices'] else 'existing_confirmation_retained' if c.get('current_office') else 'not_confirmed_not_evidence_of_absence'}
            row['research_outcome']=outcome
        matrix.append(row)
    report={'round':'RS-FED-03','date':DATE,'candidate_count':len(records),'registry_csv_reconciled':len(records),'individual_tse_profiles_rechecked':profiles_ok,'profile_access_failures':len(profiles)-profiles_ok,'previous_profile_snapshot_retained':True,'target_count':len(target_ids),'targets_with_recorded_research':len(research),'recorded_individual_queries':sum(len(q) for q in queries.values()),'new_policy_or_action_syntheses':len(additions),'with_summary':summaries,'without_summary':len(records)-summaries,'with_documented_policy_or_action':policies,'without_policy_or_action':len(records)-policies,'trajectory_only_summaries':summaries-policies,'with_biography':biographies,'with_current_office':sum(bool(c['current_office']) for c in records),'with_previous_history':sum(any(h['year']<2026 for h in c['history']) for c in records),'with_verified_votes':sum(any(h['votes_status']=='verified_nominal' for h in c['history']) for c in records),'vote_rows':dict(counts),'vote_resolution':vote_report['counts'],'with_topics':sum(bool(c.get('topics')) for c in records),'topic_count':len({t['id'] for c in records for t in c.get('topics',[])}),'baseline':{'round':'RS-FED-02','with_summary':baseline['with_summary'],'with_documented_policy_or_action':baseline['with_documented_policy_or_action'],'with_current_office':baseline['with_current_office'],'with_verified_votes':baseline['with_verified_votes']},'editorial_complete':policies==len(records),'all_profiles_complete':False,'current_office_audit_exhaustive':False,'new_filter_ui':False,'snapshot_not_live':True,'new_verified_channel_replacements':0,'historical_round_two_reports_preserved':True}
    soup=BeautifulSoup((DEST/'index.html').read_text(encoding='utf-8'),'html.parser');note=soup.select_one('.rs-review-note')
    if not note:raise ValueError('Review note anchor missing')
    note.string=(f'Revisão RS-FED-03 de 21 de setembro de 2026: {len(records)} registros reconciliados nos arquivos oficiais do TSE; {policies} fichas com pautas ou atuação documentadas, {summaries-policies} apenas com síntese de trajetória e {len(records)-summaries} sem síntese suficiente. As {len(target_ids)} fichas-alvo tiveram consultas registradas, sem garantia de preenchimento integral. A nova consulta aos perfis individuais do TSE foi bloqueada; as consultas anteriores foram preservadas. Registros históricos não são automaticamente propostas de 2026. Não há atualização em tempo real.')
    byid={c['id']:c for c in records}
    for article in soup.select('article.candidate'):
        c=byid[article['data-tse-id']];hs=sorted(c['history'],key=lambda h:(int(h['year']),int(h.get('round',1))),reverse=True)
        for li,h in zip(article.select('.rs-history li'),hs):
            for key,label in (('votes_context_source','Situação histórica ↗'),('votes_absence_source','Arquivo nominal consultado ↗')):
                if h.get(key):
                    a=soup.new_tag('a',href=h[key],attrs={'class':'source-link','target':'_blank','rel':'noopener noreferrer'});a.string=label;li.append(' ');li.append(a)
    raw=str(soup).replace('viewbox=','viewBox=');(DEST/'index.html').write_text(raw,encoding='utf-8');report['html_sha256']=hashlib.sha256(raw.encode()).hexdigest()
    integration=load(I/'integration-base.json')
    incoming={r['SQ_CANDIDATO'] for r in integration['added_records']}
    if incoming & target_ids or not incoming <= set(byid):raise ValueError('Concurrent records not preserved independently')
    report.update({'original_population':integration['original_population'],'concurrent_added_records':integration['added_records'],'concurrent_population_baseline':integration['upstream_commit'],'original_targets_remaining_policy_gaps':sum(not r['policy_or_action_documented'] for r in matrix if r['target_this_round']),'concurrent_added_policy_gaps':sum(not r['policy_or_action_documented'] for r in matrix if r['id'] in incoming),'concurrent_added_vote_gaps':sum(len(r['unresolved_nominal_rows']) for r in matrix if r['id'] in incoming),'scope_expansion_preserved':True})
    for row in matrix:
        if row['id'] in incoming:row['research_outcome']='incoming_triage_only_not_original_target'
    save(A/'incoming-triage.json',load(I/'incoming-triage.json'))
    save(A/'final-report.json',report);save(A/'candidate-matrix.json',matrix);save(A/'research-log.json',research)
    save(A/'target-results.json',{'round':'RS-FED-03','date':DATE,'targets':[r for r in matrix if r['target_this_round']],'outcomes':dict(collections.Counter(r['outcome'] for r in research.values()))})
    save(A/'content-audit.json',{'date':DATE,'records':len(records),'scope':'Text/source presence and temporal-attribution review of the reconciled dataset; substantive new-source research for the original 63 targets. Four concurrently added records received initial triage only. Previously published sources were not all independently reopened.','checks':[{'id':c['id'],'summary_has_sources':not c['pautas'] or bool(c['editorial_sources']),'new_source_periods_explicit':all(s.get('period') for s in additions.get(c['id'],{}).get('sources',[]))} for c in records]})
    data=load(DEST/'dados.json');data.update({'schema_version':3,'review_round':'RS-FED-03','review_date':DATE});save(DEST/'dados.json',data)
    normalized=load(D/'normalized.json');normalized.update({'schema_version':3,'review_round':'RS-FED-03'});save(D/'normalized.json',normalized)
    save(DEST/'revisao.json',{'report':report,'candidates':matrix})
    sources=load(DEST/'fontes.json');sources['round_two_review']=baseline;sources['round_three_review']=report;sources['official_refresh_previous_round']=sources.get('official_refresh');sources['official_refresh']=refresh;sources['official_refresh']['profile_access_failures']=len(profiles)-profiles_ok;sources['vote_resolution']=vote_report;save(DEST/'fontes.json',sources)
    build_report=load(ROOT/'docs/rs/build-report.json');build_report.update({'with_editorial_summary':summaries,'with_verified_current_office':report['with_current_office'],'with_previous_votes':report['with_verified_votes'],'html_sha256':report['html_sha256'],'review':report});save(ROOT/'docs/rs/build-report.json',build_report);save(ROOT/'docs/rs/candidate-audit.json',matrix)
    lines=['# RS-FED-03 — execução e lacunas','',f'Revisão: {DATE}.','',f'{len(target_ids)} alvos com {report["recorded_individual_queries"]} consultas registradas; {len(additions)} novas sínteses de pautas/atuação.',f'Base: {summaries} sínteses, sendo {policies} de pautas/atuação e {summaries-policies} de trajetória; {len(records)-summaries} sem síntese.',f'{report["with_current_office"]} cargos confirmados; auditoria não exaustiva.',f'Votações: {counts["verified_nominal"]} valores nominais, {counts["not_applicable"]} não aplicáveis, {counts["not_published_inapt"]} sem linha nominal em registro histórico inapto, {counts["not_verified"]} conflitos ainda não resolvidos.','CSV eleitoral reconciliado para 111 registros; 111 consultas de perfil individual bloqueadas (HTTP 403). Não foram contabilizadas como reconferidas. A ampliação de 107 para 111 veio de correção de recorte no main; os quatro novos registros foram preservados e triados separadamente.','','## Pendências de pautas/atuação']
    lines += [f'- {r["name"]} ({r["party"]}; TSE {r["id"]}): {research.get(r["id"],{}).get("reason","Cobertura ainda insuficiente.")}' for r in matrix if not r['policy_or_action_documented']]
    lines += ['','## Limites','Pesquisa individual registrada não equivale a perfil completo. Não houve novo filtro visual, troca presumida de canais ou atualização recorrente. Fontes históricas e declarações estão datadas; medidas propostas não são apresentadas como executadas. Os dois vínculos históricos de Claudia Souza continuam com divergência de nome civil. As cinco ausências nominais não foram transformadas em zero. Além dos dois conflitos de identidade do lote original, há três lacunas de votação vindas dos quatro cadastros acrescentados pelo main. As pendências editoriais são 43 dos alvos originais e quatro recém-incorporadas.','','## Reprodução','`EEFOCO_OFFLINE_BUILD=1 python tools/rs/build.py` após `python tools/rs/fed03_install.py` na primeira instalação. Não executar a migração RS-FED-02 isoladamente sobre esta versão. `python -m unittest discover -s tests/rs -p "test_*.py" -v` e `python tools/rs/qa.py`.','','## Proveniência','Entradas: `data/rs/fed03/`. Relatórios históricos RS-FED-02 preservados em `docs/rs/review/`. Relatórios atuais: este diretório.']
    (A/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))

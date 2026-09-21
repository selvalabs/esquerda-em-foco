"""Recover exact official historical votes; a candidate ID is not always global.

For municipal archives, the matching key includes SG_UE, office, year and round.
Only full validated RS ZIP members are hashed; the national archive hash is null
for HTTP range collection. Vice/supplemental roles never receive nominal totals.
"""
from __future__ import annotations
import collections,csv,hashlib,importlib.util,io,json,subprocess,unicodedata,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais/phase2'
OFFICES={'deputado federal':'6','deputado estadual':'7','senador':'5','prefeito':'11','vereador':'13','governador':'3'}
def load(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def save(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return ''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')
def reason(h):
    office=norm(h.get('office',''))
    if 'vice' in office:return 'not_applicable_vice_ticket'
    if 'suplente' in office:return 'not_applicable_supplemental_ticket'
    if h.get('uf')!='RS':return 'national_or_other_uf_not_collected'
    if h.get('round_note'):return 'round_not_confirmed'
    if office not in OFFICES:return 'office_not_mapped'
    return None

def run():
    A.mkdir(parents=True,exist_ok=True)
    snapshot=load(D/'normalized.json')['candidates']
    if not (A/'baseline.json').exists():
        save(A/'baseline.json',{'started_at':datetime.now(timezone.utc).isoformat(),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope_issue':5,'pr':9,'candidate_count':len(snapshot),'policy_summaries':sum(bool(c['pautas']) for c in snapshot),'policy_gap_ids':[c['id'] for c in snapshot if not c['pautas']],'current_offices':sum(bool(c['current_office']) for c in snapshot),'with_activity':sum(bool(c['activities']) for c in snapshot),'historical_vote_rows':sum(h['year']<2026 and h.get('votes') is not None for c in snapshot for h in c['history']),'normalized_sha256':hashlib.sha256((D/'normalized.json').read_bytes()).hexdigest()})
    spec=importlib.util.spec_from_file_location('rs_public_ranges',ROOT/'tools/rs/votes_ranges.py');reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    history=load(D/'history-normalized.json',{});supplemental=load(D/'votes-phase2.json',{});audit=load(A/'votes-audit.json',{'attempts':[]})
    raw_index={}
    for row in load(D/'history-official.json',[]):
        key=(row['SQ_CANDIDATO_ATUAL'],int(row['ANO_ELEICAO']),row['SQ_CANDIDATO'],int(row['NR_TURNO']))
        if key in raw_index and raw_index[key]['SG_UE']!=row['SG_UE']:raise ValueError('Ambiguous official historical link')
        raw_index[key]=row
    for year in (2010,2008,2006,2004):
        if str(year) in supplemental:continue
        targets={};by_short={}
        for cid,rows in history.items():
            for h in rows:
                if h['year']!=year or reason(h):continue
                raw=raw_index.get((cid,year,str(h['candidate_id']),int(h['round'])))
                if not raw:continue
                full=(str(h['candidate_id']),int(h['round']),str(raw['SG_UE']),str(raw['CD_CARGO']))
                short=full[0]+':'+str(full[1])
                if short in by_short and by_short[short]!=full:raise ValueError('Legacy export key collision; a qualified export schema is required')
                by_short[short]=full;targets[full]=raw
        if not targets:continue
        url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
        entry={'year':year,'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'target_count':len(targets),'matching_version':2}
        try:
            first,total=reader.segment(url,0,255);remote=reader.RangeFile(url,total)
            with zipfile.ZipFile(remote) as archive:
                names=[n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
                if len(names)!=1:raise ValueError('RS member not unique')
                info=archive.getinfo(names[0]);sums=collections.defaultdict(int);counts=collections.Counter();contexts={};generation=None;reused_ids=0
                with archive.open(info) as payload:
                    tracked=reader.DigestReader(payload)
                    with io.BufferedReader(tracked) as buffered:
                        encoding='utf-8-sig' if buffered.peek(3)[:3]==b'\xef\xbb\xbf' else 'latin-1'
                        with io.TextIOWrapper(buffered,encoding=encoding,newline='') as text:
                            rows=csv.DictReader(text,delimiter=';');entry['columns']=rows.fieldnames
                            required={'SQ_CANDIDATO','QT_VOTOS_NOMINAIS','NR_TURNO','SG_UF','SG_UE','CD_CARGO','ANO_ELEICAO','NR_CANDIDATO','NM_CANDIDATO'}
                            if not required.issubset(rows.fieldnames or []):raise ValueError('Unsupported schema; no inferred mapping')
                            for row in rows:
                                short=row['SQ_CANDIDATO']+':'+row['NR_TURNO']
                                if short not in by_short:continue
                                full=(row['SQ_CANDIDATO'],int(row['NR_TURNO']),str(row['SG_UE']),str(row['CD_CARGO']))
                                if full not in targets:reused_ids+=1;continue
                                expected=targets[full]
                                if row['SG_UF']!='RS' or int(row['ANO_ELEICAO'])!=year:raise ValueError('Year/UF mismatch')
                                if row['NR_CANDIDATO']!=expected['NR_CANDIDATO'] or norm(row['NM_CANDIDATO'])!=norm(expected['NM_CANDIDATO']):raise ValueError('Matched electoral context has conflicting identity')
                                amount=int(row['QT_VOTOS_NOMINAIS'])
                                if amount<0:raise ValueError('Negative nominal vote count')
                                context={'uf':row['SG_UF'],'electoral_unit':row['SG_UE'],'office_code':row['CD_CARGO'],'year':year,'round':full[1],'election_id':row.get('CD_ELEICAO'),'ballot_number':row['NR_CANDIDATO']}
                                if short in contexts and contexts[short]!=context:raise ValueError('Election/context collision')
                                sums[short]+=amount;counts[short]+=1;contexts[short]=context
                                if generation is None:generation=row.get('DT_GERACAO','')+' '+row.get('HH_GERACAO','')
                    if tracked.count!=info.file_size:raise ValueError('Incomplete archive member')
                if not sums:raise ValueError('No exact contextual candidate matches')
                value={'source_url':url,'dataset':f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}','member':names[0],'archive_bytes':total,'archive_sha256':None,'member_sha256':tracked.digest.hexdigest(),'member_bytes':tracked.count,'member_crc32':f'{info.CRC:08x}','http_bytes_read':remote.transferred+len(first),'totals':dict(sums),'rows_per_total':dict(counts),'contexts':contexts,'generated_at':generation,'checked_at':entry['checked_at'],'matching_version':2,'excluded_reused_id_rows':reused_ids,'method':'Official linked ID + electoral unit + year + office + UF + round; corroborated ballot number and civil name. Full RS member CRC and SHA-256, HTTP ranges.'}
                supplemental[str(year)]=value;entry.update({'success':True,'matched_totals':len(sums),'excluded_reused_id_rows':reused_ids,'member_sha256':value['member_sha256']})
        except Exception as exc:entry.update({'success':False,'error':str(exc)})
        audit['attempts'].append(entry);save(D/'votes-phase2.json',supplemental);save(A/'votes-audit.json',audit)
    votes=load(D/'votes-official.json',{})
    for year,value in supplemental.items():
        if year in votes and votes[year].get('totals')!=value['totals']:raise ValueError('Conflict with existing totals')
        votes[year]=value
    save(D/'votes-official.json',votes);coverage=[]
    for cid,rows in history.items():
        for h in rows:
            if h['year']>=2026:continue
            why=reason(h);source=votes.get(str(h['year']),{});key=str(h['candidate_id'])+':'+str(h['round']);raw=raw_index.get((cid,h['year'],str(h['candidate_id']),int(h['round'])))
            if raw:h['electoral_unit']=raw['SG_UE']
            if not why and key in source.get('totals',{}):
                context=source.get('contexts',{}).get(key,{})
                if context.get('electoral_unit') and (not raw or context['electoral_unit']!=raw['SG_UE']):raise ValueError('Application electoral-unit mismatch')
                h['votes']=source['totals'][key];h['votes_source']=source['source_url'];h['votes_population']='RS; unidade eleitoral e soma nominal por município/zona/turno; identificador TSE'
                h['votes_source_generated_at']=source.get('generated_at');h['votes_status']='verified_nominal'
            else:
                h['votes']=None;h.pop('votes_source',None)
                h['votes_status']=why or ('source_has_no_matching_record' if source else 'source_collection_failed_or_unavailable')
            coverage.append({'candidate_id':cid,'historical_id':h['candidate_id'],'year':h['year'],'round':h['round'],'office':h.get('office'),'uf':h.get('uf'),'electoral_unit':h.get('electoral_unit'),'status':h['votes_status'],'votes':h.get('votes'),'source':h.get('votes_source')})
    save(D/'history-normalized.json',history);save(A/'historical-vote-status.json',coverage)
    summary={'historical_rows':len(coverage),'by_status':dict(collections.Counter(x['status'] for x in coverage)),'by_year_verified':dict(collections.Counter(x['year'] for x in coverage if x['status']=='verified_nominal')),'supplemental_years':sorted(supplemental),'scope_note':'Not applicable differs from missing evidence; old municipal IDs are qualified by electoral unit.'}
    save(A/'votes-summary.json',summary)
    report=load(ROOT/'docs/rs-estaduais/votes-coverage.json',{})
    report.update({'checked_at':datetime.now(timezone.utc).isoformat(),'historical_rows_with_votes':sum(x['status']=='verified_nominal' for x in coverage),'candidates_with_past_votes':len({x['candidate_id'] for x in coverage if x['status']=='verified_nominal'}),'years':sorted(votes),'phase2_null_reasons':summary['by_status'],'limitation':'Cobertura nominal 2004–2024 quando conciliada; vice/suplência não recebe votação nominal própria. Um total estadual não é apresentado como nacional. Nulls têm motivo explícito.'})
    save(ROOT/'docs/rs-estaduais/votes-coverage.json',report)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__':run()

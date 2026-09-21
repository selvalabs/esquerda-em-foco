"""Phase A-D: preserve baseline, recover older RS nominal votes, classify nulls.

This collector only accepts an exact TSE ID/year/office/UF/round match. It does
not match names, infer a zero, or assign ticket votes to vice/supplemental roles.
The national ZIP hash remains null when public HTTP byte ranges are used.
"""
from __future__ import annotations
import collections
import csv
import hashlib
import importlib.util
import io
import json
import subprocess
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
A=ROOT/'docs/rs-estaduais/phase2'
OFFICES={'deputado federal':'6','deputado estadual':'7','senador':'5','prefeito':'11','vereador':'13','governador':'3'}

def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default

def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def norm(x):
    return ''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')

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
    baseline=A/'baseline.json'
    if not baseline.exists():
        save(baseline,{'started_at':datetime.now(timezone.utc).isoformat(),'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'scope_issue':5,'pr':9,'candidate_count':len(snapshot),'policy_summaries':sum(bool(c['pautas']) for c in snapshot),'policy_gap_ids':[c['id'] for c in snapshot if not c['pautas']],'current_offices':sum(bool(c['current_office']) for c in snapshot),'with_activity':sum(bool(c['activities']) for c in snapshot),'historical_vote_rows':sum(h['year']<2026 and h.get('votes') is not None for c in snapshot for h in c['history']),'normalized_sha256':hashlib.sha256((D/'normalized.json').read_bytes()).hexdigest()})
    spec=importlib.util.spec_from_file_location('rs_public_ranges',ROOT/'tools/rs/votes_ranges.py')
    reader=importlib.util.module_from_spec(spec);spec.loader.exec_module(reader)
    history=load(D/'history-normalized.json',{})
    supplemental=load(D/'votes-phase2.json',{})
    audit=load(A/'votes-audit.json',{'attempts':[]})
    for year in (2010,2008,2006,2004):
        if str(year) in supplemental:continue
        targets={}
        for rows in history.values():
            for h in rows:
                if h['year']==year and not reason(h):
                    key=(str(h['candidate_id']),int(h['round']))
                    code=OFFICES[norm(h['office'])]
                    if key in targets and targets[key]!=code:raise ValueError('Conflicting TSE office for '+str(key))
                    targets[key]=code
        if not targets:continue
        url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
        entry={'year':year,'url':url,'checked_at':datetime.now(timezone.utc).isoformat(),'target_count':len(targets)}
        try:
            first,total=reader.segment(url,0,255)
            remote=reader.RangeFile(url,total)
            with zipfile.ZipFile(remote) as archive:
                names=[n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
                if len(names)!=1:raise ValueError('RS member not unique')
                info=archive.getinfo(names[0])
                sums=collections.defaultdict(int);counts=collections.Counter();contexts={};generation=None
                with archive.open(info) as payload:
                    tracked=reader.DigestReader(payload)
                    with io.BufferedReader(tracked) as buffered:
                        encoding='utf-8-sig' if buffered.peek(3)[:3]==b'\xef\xbb\xbf' else 'latin-1'
                        with io.TextIOWrapper(buffered,encoding=encoding,newline='') as text:
                            rows=csv.DictReader(text,delimiter=';')
                            entry['columns']=rows.fieldnames
                            required={'SQ_CANDIDATO','QT_VOTOS_NOMINAIS','NR_TURNO','SG_UF','CD_CARGO','ANO_ELEICAO'}
                            if not required.issubset(rows.fieldnames or []):raise ValueError('Unsupported historical schema; no inference applied')
                            for row in rows:
                                key=(row['SQ_CANDIDATO'],int(row['NR_TURNO']))
                                if key not in targets:continue
                                if row['SG_UF']!='RS' or int(row['ANO_ELEICAO'])!=year or str(row['CD_CARGO'])!=targets[key]:raise ValueError('Historical population mismatch: '+str(key))
                                composite=key[0]+':'+str(key[1]);amount=int(row['QT_VOTOS_NOMINAIS'])
                                if amount<0:raise ValueError('Negative nominal vote count')
                                sums[composite]+=amount;counts[composite]+=1
                                context={'uf':row['SG_UF'],'office_code':row['CD_CARGO'],'year':year,'round':key[1],'election_id':row.get('CD_ELEICAO')}
                                if composite in contexts and contexts[composite]!=context:raise ValueError('Election/context collision')
                                contexts[composite]=context
                                if generation is None:generation=row.get('DT_GERACAO','')+' '+row.get('HH_GERACAO','')
                    if tracked.count!=info.file_size:raise ValueError('Incomplete archive member')
                if not sums:raise ValueError('No exact linked candidate IDs found')
                data={'source_url':url,'dataset':f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}','member':names[0],'archive_bytes':total,'archive_sha256':None,'member_sha256':tracked.digest.hexdigest(),'member_bytes':tracked.count,'member_crc32':f'{info.CRC:08x}','http_bytes_read':remote.transferred+len(first),'totals':dict(sums),'rows_per_total':dict(counts),'contexts':contexts,'generated_at':generation,'checked_at':entry['checked_at'],'method':'Exact TSE ID/year/office/UF/round; full RS member CRC and SHA-256; validated HTTP ranges'}
                supplemental[str(year)]=data
                entry.update({'success':True,'matched_totals':len(sums),'member_sha256':data['member_sha256']})
        except Exception as exc:entry.update({'success':False,'error':str(exc)})
        audit['attempts'].append(entry)
        save(D/'votes-phase2.json',supplemental);save(A/'votes-audit.json',audit)
    votes=load(D/'votes-official.json',{})
    for year,value in supplemental.items():
        if year in votes and votes[year].get('totals')!=value['totals']:raise ValueError('Existing totals conflict with phase2 collection')
        votes[year]=value
    save(D/'votes-official.json',votes)
    coverage=[]
    for cid,rows in history.items():
        for h in rows:
            if h['year']>=2026:continue
            why=reason(h);source=votes.get(str(h['year']),{});key=str(h['candidate_id'])+':'+str(h['round'])
            if not why and key in source.get('totals',{}):
                h['votes']=source['totals'][key];h['votes_source']=source['source_url'];h['votes_population']='RS; soma nominal por município/zona e turno; identificador TSE'
                h['votes_source_generated_at']=source.get('generated_at');h['votes_status']='verified_nominal'
            else:
                if why:h['votes']=None;h.pop('votes_source',None)
                h['votes_status']=why or 'source_has_no_matching_record'
            coverage.append({'candidate_id':cid,'historical_id':h['candidate_id'],'year':h['year'],'round':h['round'],'office':h.get('office'),'uf':h.get('uf'),'status':h['votes_status'],'votes':h.get('votes'),'source':h.get('votes_source')})
    save(D/'history-normalized.json',history)
    save(A/'historical-vote-status.json',coverage)
    save(A/'votes-summary.json',{'historical_rows':len(coverage),'by_status':dict(collections.Counter(x['status'] for x in coverage)),'by_year_verified':dict(collections.Counter(x['year'] for x in coverage if x['status']=='verified_nominal')),'supplemental_years':sorted(supplemental),'scope_note':'Not applicable is distinct from missing evidence. No nominal totals assigned to vice or supplemental positions.'})
    print(json.dumps(load(A/'votes-summary.json'),ensure_ascii=False,indent=2))

if __name__=='__main__':run()

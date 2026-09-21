"""Read-only source inspection for A-D.2; explicit whitelists and bounded I/O.
No scraped field automatically becomes a policy summary or a current mandate.
Historical totals require an exact candidate/year/office/constituency identity.
Outputs stay in an inspection artifact until reviewed and explicitly integrated.
"""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, importlib.util, io, json, re, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais'
OUT=Path('/tmp/rs-ad2-expanded')

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def save(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read_votes():
    reader=module('ad2_ranges',ROOT/'tools/rs/votes_ranges.py')
    matcher=module('ad2_identity',ROOT/'tools/rs-estaduais/phase2_votes.py')
    historic=load(D/'history-official.json')
    targets={}
    for cid,year in [('210000615842',2018),('210001621255',2022)]:
        found=[r for r in historic if r['SQ_CANDIDATO']==cid and int(r['ANO_ELEICAO'])==year]
        if len(found)!=1:raise ValueError('Ambiguous historical identity')
        r=found[0]
        targets[year]={'candidate_id':cid,'current_candidate_id':r['SQ_CANDIDATO_ATUAL'],'name':r['NM_CANDIDATO'],'number':r['NR_CANDIDATO'],'office':r['CD_CARGO'],'unit':r['SG_UE'],'round':int(r['NR_TURNO']),'election_code':r['CD_ELEICAO']}
    # Identity is also checked against the current TSE-linked historical summary.
    current=load(D/'normalized.json')['candidates']
    genro=next(c for c in current if c['id']=='210002533936')
    presidential=[h for h in genro['history'] if h['year']==2014 and str(h['candidate_id'])=='280000000043']
    if len(presidential)!=1 or str(presidential[0]['office']).lower()!='presidente':raise ValueError('Presidential historical linkage absent')
    targets[2014]={'candidate_id':'280000000043','current_candidate_id':genro['id'],'name':'LUCIANA KREBS GENRO','number':'50','office':'1','unit':'BR','round':None,'election_code':None}
    output=[]
    for year,target in sorted(targets.items()):
        url=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
        record={'year':year,'target':target,'source_url':url,'checked_at':datetime.now(timezone.utc).isoformat()}
        try:
            first,total=reader.segment(url,0,255);remote=reader.RangeFile(url,total)
            with zipfile.ZipFile(remote) as archive:
                suffix='_BR.CSV' if target['unit']=='BR' else '_RS.CSV'
                names=[n for n in archive.namelist() if n.upper().endswith(suffix)]
                if not names and target['unit']=='BR':names=[n for n in archive.namelist() if n.upper().endswith('_BRASIL.CSV')]
                if len(names)!=1:
                    record['available_members']=archive.namelist();raise ValueError('Unique source member not found')
                info=archive.getinfo(names[0])
                if info.file_size>350_000_000:raise ValueError('Member exceeds bounded inspection size')
                sums=collections.Counter();counts=collections.Counter();contexts={};seen=set();generation=None
                with archive.open(info) as raw:
                    tracked=reader.DigestReader(raw)
                    with io.BufferedReader(tracked) as buffered:
                        enc='utf-8-sig' if buffered.peek(3)[:3]==b'\xef\xbb\xbf' else 'latin-1'
                        with io.TextIOWrapper(buffered,encoding=enc,newline='') as text:
                            rows=csv.DictReader(text,delimiter=';')
                            required={'SQ_CANDIDATO','ANO_ELEICAO','CD_CARGO','SG_UE','SG_UF','NR_TURNO','NR_CANDIDATO','NM_CANDIDATO','CD_ELEICAO','QT_VOTOS_NOMINAIS','CD_MUNICIPIO','NR_ZONA'}
                            if not required.issubset(rows.fieldnames or []):raise ValueError('Unrecognized source schema')
                            for row in rows:
                                if row['SQ_CANDIDATO']!=target['candidate_id']:continue
                                if str(row['ANO_ELEICAO'])!=str(year) or row['CD_CARGO']!=target['office'] or row['SG_UE']!=target['unit']:raise ValueError('Matched ID has incompatible electoral context')
                                if target['unit']=='RS' and row['SG_UF']!='RS':raise ValueError('Wrong state')
                                if row['NR_CANDIDATO']!=target['number'] or matcher.norm(row['NM_CANDIDATO'])!=matcher.norm(target['name']):raise ValueError('Civil name or ballot number mismatch')
                                if target['election_code'] and row['CD_ELEICAO']!=target['election_code']:raise ValueError('Wrong historical election code')
                                turn=int(row['NR_TURNO'])
                                if target['round'] and turn!=target['round']:raise ValueError('Wrong round')
                                grain=tuple(row.get(k,'') for k in ['SQ_CANDIDATO','CD_ELEICAO','NR_TURNO','SG_UF','SG_UE','CD_MUNICIPIO','NR_ZONA','ST_VOTO_EM_TRANSITO'])
                                if grain in seen:raise ValueError('Duplicated electoral grain; do not sum twice')
                                seen.add(grain)
                                amount=int(row['QT_VOTOS_NOMINAIS'])
                                if amount<0:raise ValueError('Negative vote amount')
                                context={'candidate_id':target['candidate_id'],'year':year,'round':turn,'office_code':row['CD_CARGO'],'electoral_unit':row['SG_UE'],'election_code':row['CD_ELEICAO'],'ballot_number':row['NR_CANDIDATO'],'civil_name':row['NM_CANDIDATO'],'population':'national_including_external_vote_rows' if target['unit']=='BR' else 'RS'}
                                if turn in contexts and contexts[turn]!=context:raise ValueError('Incompatible contexts across rows')
                                contexts[turn]=context;sums[turn]+=amount;counts[turn]+=1
                                generation=row.get('DT_GERACAO','')+' '+row.get('HH_GERACAO','')
                    if tracked.count!=info.file_size:raise ValueError('Incomplete source member')
                if not sums:raise ValueError('Source read but no matching vote row; no zero inferred')
                if target['round'] is None and len(sums)!=1:raise ValueError('Unknown historical round remains ambiguous')
                record.update({'read':True,'member':names[0],'member_sha256':tracked.digest.hexdigest(),'member_crc32':f'{info.CRC:08x}','member_bytes':tracked.count,'archive_sha256':None,'archive_bytes':total,'http_bytes_read':remote.transferred+len(first),'generation':generation,'totals':dict(sums),'rows_per_total':dict(counts),'contexts':contexts,'method':'One complete source member; CRC and SHA-256; exact ID, year, office, electoral unit, ballot and civil name. A national table is never replaced by the RS subset.'})
        except Exception as exc:record.update({'read':False,'error':str(exc)})
        output.append(record);save(OUT/'votes.json',output)
    return output


def municipalities():
    safe=module('ad2_source_safety',ROOT/'tools/rs-estaduais/research.py')
    targets=[('https://sapl.saojeronimo.rs.leg.br',42),('https://sapl.esteio.rs.leg.br',150),('https://sapl.jaguari.rs.leg.br',29)]
    fields={'id','nome_completo','nome_parlamentar','ativo','titular','parlamentar','legislatura','data_inicio_mandato','data_fim_mandato','data_expedicao_diploma','numero_legislatura','data_inicio','data_fim','data_eleicao','observacao','tipo_afastamento','data_inicio_afastamento','data_fim_afastamento'}
    def read(url):
        out={'url':url,'checked_at':datetime.now(timezone.utc).isoformat()}
        try:
            raw,final,status,mime=safe.read(url,18);obj=json.loads(raw)
            if isinstance(obj,dict) and 'results' in obj:values=obj['results'];out['next']=obj.get('next');out['count']=obj.get('count')
            elif isinstance(obj,list):values=obj
            else:values=[obj]
            out.update({'read':True,'http_status':status,'sha256':hashlib.sha256(raw).hexdigest(),'data':[{k:v for k,v in r.items() if k in fields} for r in values]})
        except Exception as exc:out.update({'read':False,'error':str(exc)})
        return out
    tasks=[]
    for host,pid in targets:
        for resource in [f'parlamentar/{pid}/',f'mandato/?parlamentar={pid}',f'afastamentoparlamentar/?parlamentar={pid}','legislatura/']:
            tasks.append(host+'/api/parlamentares/'+resource)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:results=list(pool.map(read,tasks))
    save(OUT/'municipal.json',results)
    return results

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    offices=municipalities();votes=read_votes()
    print(json.dumps({'municipal_sources_read':sum(r['read'] for r in offices),'vote_sources_read':sum(r['read'] for r in votes)}))

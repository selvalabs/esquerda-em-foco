"""Reconcile 2004–2010 nominal votes and classify all unfilled history values.
Old short candidate IDs are NOT globally unique: office, civil name and locality
must also match. Never turn a missing result into zero or assign vice-ticket votes.
"""
from __future__ import annotations
import collections,csv,hashlib,importlib.util,io,json,re,unicodedata,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'data/rs';A=ROOT/'docs/rs/review';A.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('vr',ROOT/'tools/rs/votes_ranges.py');vr=importlib.util.module_from_spec(spec);spec.loader.exec_module(vr)
def save(path,x):path.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(x):return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')).strip()
def ticket(office):return norm(office).startswith('vice') or 'suplente' in norm(office)
def pick(r,*names):return next((r[n] for n in names if n in r),'')
def key(cid,h):return ':'.join([cid,str(h['year']),str(h['candidate_id']),str(h.get('round',1))])
def run():
 marker=A/'history-review.json'
 if marker.exists():return
 histories=json.loads((D/'history-normalized.json').read_text());records={r['SQ_CANDIDATO']:r for r in json.loads((D/'candidates-official.json').read_text())}; now=datetime.now(timezone.utc).isoformat()
 report={'checked_at':now,'method':'RS member CRC and SHA-256; match candidate ID + civil name + office + electoral locality + round; only nominal votes','years':{},'errors':[]}; evidence={}
 for year in (2010,2008,2006,2004):
  targets=[(cid,h) for cid,hs in histories.items() for h in hs if h['year']==year and h.get('votes') is None and not ticket(h.get('office',''))]
  if not targets:continue
  address=f'https://cdn.tse.jus.br/estatistica/sead/odsele/votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip'
  try:
   initial,size=vr.segment(address,0,255);remote=vr.RangeFile(address,size);totals=collections.defaultdict(int);counts=collections.Counter();name_conflicts=collections.Counter()
   with zipfile.ZipFile(remote) as archive:
    names=[n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
    if len(names)!=1:raise ValueError('Unique RS member required')
    info=archive.getinfo(names[0]);digest=hashlib.sha256()
    with archive.open(info) as payload:
     tracked=vr.DigestReader(payload)
     with io.TextIOWrapper(io.BufferedReader(tracked),encoding='latin-1',newline='') as text:
      reader=csv.DictReader(text,delimiter=';');headers=reader.fieldnames
      if not any(n in headers for n in ['QT_VOTOS_NOMINAIS','QTDE_VOTOS']):raise ValueError('No recognized nominal-votes column: '+str(headers))
      lookup=collections.defaultdict(list)
      for cid,h in targets:lookup[str(h['candidate_id'])].append((cid,h))
      for r in reader:
       seq=pick(r,'SQ_CANDIDATO','SEQUENCIAL_CANDIDATO');matches=lookup.get(seq,[])
       if not matches:continue
       if pick(r,'SG_UF','SIGLA_UF')!='RS':continue
       yr=pick(r,'ANO_ELEICAO');turn=pick(r,'NR_TURNO','NUM_TURNO')
       if int(yr or year)!=year:raise ValueError('Year mismatch')
       cargo=norm(pick(r,'DS_CARGO','DESCRICAO_CARGO'));name=norm(pick(r,'NM_CANDIDATO','NOME_CANDIDATO'))
       for cid,h in matches:
        if int(turn or 1)!=int(h.get('round',1)) or cargo!=norm(h.get('office','')):continue
        place=norm(h.get('place',''));local=norm(pick(r,'NM_UE','DESCRICAO_UE','NOME_MUNICIPIO','NM_MUNICIPIO'))
        if place not in ('rio grande do sul','rs') and place!=local:continue
        expected=norm(records[cid]['NM_CANDIDATO'])
        if not name or name!=expected:name_conflicts[key(cid,h)]+=1;continue
        amount=int(pick(r,'QT_VOTOS_NOMINAIS','QTDE_VOTOS'))
        if amount<0:raise ValueError('Negative nominal count')
        k=key(cid,h);totals[k]+=amount;counts[k]+=1
     if tracked.count!=info.file_size:raise ValueError('Incomplete CSV read')
   source={'url':address,'member':names[0],'member_sha256':tracked.digest.hexdigest(),'member_crc32':f'{info.CRC:08x}','archive_sha256':None,'checked_at':now,'totals':dict(totals),'matched_rows':dict(counts),'headers':headers,'identity_conflicts':dict(name_conflicts)}
   evidence[str(year)]=source
   for cid,h in targets:
    k=key(cid,h)
    if k in totals:h.update({'votes':totals[k],'votes_source':address,'votes_checked_at':now,'votes_match_method':'ID + civil name + office + locality + turn'})
   report['years'][str(year)]={'targets':len(targets),'resolved':len(totals),'member_sha256':source['member_sha256'],'identity_conflicts':dict(name_conflicts)}
  except Exception as e:report['errors'].append({'year':year,'error':str(e)})
 counts=collections.Counter();gaps=[]
 for cid,hs in histories.items():
  for h in hs:
   if h['year']>=2026:state='not_yet_held'
   elif ticket(h.get('office','')):state='not_applicable';h['votes']=None;h.pop('votes_source',None)
   elif h.get('votes') is not None:state='verified_nominal'
   else:state='not_verified';gaps.append({'id':cid,'name':records[cid]['NM_URNA_CANDIDATO'],'year':h['year'],'office':h.get('office'),'historical_id':h['candidate_id'],'round':h.get('round',1),'reason':'No reconciled nominal result; this is not a zero'})
   h['votes_status']=state;counts[state]+=1
   if state=='not_applicable':h['votes_note']='Não se aplica: candidatura de vice ou suplente de chapa, sem votação nominal individual.'
   elif state=='not_verified':h['votes_note']='Valor nominal não reconciliado nas fontes consultadas; não equivale a zero.'
 report.update({'counts':dict(counts),'unresolved_nominal_rows':gaps,'candidates_with_verified_votes':sum(any(h['votes_status']=='verified_nominal' for h in hs) for hs in histories.values())})
 save(D/'history-normalized.json',histories);save(D/'votes-legacy-reviewed.json',evidence);save(marker,report);print(json.dumps(report,ensure_ascii=False,indent=2))
if __name__=='__main__':run()

"""RS-FED-03 collection: public records only, bounded requests, no editorial inference.
Writes exclusively to data/rs/fed03 and docs/rs/fed03. Existing inputs stay intact.
"""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, importlib.util, io, json, re, sys, unicodedata, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; D=ROOT/'data/rs'; OUT=D/'fed03'; A=ROOT/'docs/rs/fed03'
for p in (OUT,A):p.mkdir(parents=True,exist_ok=True)
NOW=datetime.now(timezone.utc).isoformat(); BASE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def norm(v):return re.sub(r'[^a-z0-9]+',' ',''.join(c for c in unicodedata.normalize('NFD',str(v).casefold()) if unicodedata.category(c)!='Mn')).strip()
spec=importlib.util.spec_from_file_location('ranges',ROOT/'tools/rs/votes_ranges.py');vr=importlib.util.module_from_spec(spec);spec.loader.exec_module(vr)
def csv_rows(address):
 initial,size=vr.segment(address,0,255);remote=vr.RangeFile(address,size)
 with zipfile.ZipFile(remote) as z:
  names=[n for n in z.namelist() if n.upper().endswith('_RS.CSV')]
  if len(names)!=1:raise ValueError('Exactly one RS member required')
  raw=z.read(names[0]);text=raw.decode('utf-8-sig') if raw.startswith(b'\xef\xbb\xbf') else raw.decode('latin-1')
  return list(csv.DictReader(io.StringIO(text),delimiter=';')),{'url':address,'member':names[0],'member_sha256':hashlib.sha256(raw).hexdigest(),'checked_at':NOW,'method':'Complete RS CSV, ZIP CRC verification, HTTP ranges','http_bytes':remote.transferred+len(initial)}
def get(address):
 req=urllib.request.Request(address,headers={'User-Agent':'EsquerdaEmFoco-public-record-audit','Accept':'application/json'})
 with urllib.request.urlopen(req,timeout=20) as r:
  raw=r.read(6000001)
  if len(raw)>6000000:raise ValueError('Response too large')
  return json.loads(raw),hashlib.sha256(raw).hexdigest()
def run():
 records=load(D/'candidates-official.json');by={r['SQ_CANDIDATO']:r for r in records};ids=set(by);scope=load(D/'rs-fed-03-targets.json');hist=load(D/'history-normalized.json')
 refresh={'checked_at':NOW,'expected_count':len(ids),'sources':[],'errors':[]}
 for name,address in [('candidates',BASE+'consulta_cand/consulta_cand_2026.zip'),('status',BASE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip')]:
  try:
   rows,evidence=csv_rows(address)
   if name=='candidates':
    parties={r['SG_PARTIDO'].upper() for r in records}|{'PCO'}
    chosen=[r for r in rows if r.get('SG_UF')=='RS' and r.get('CD_CARGO')=='6' and r.get('ANO_ELEICAO')=='2026' and r.get('SG_PARTIDO','').upper() in parties]
    found={r['SQ_CANDIDATO'] for r in chosen};refresh.update({'added_ids':sorted(found-ids),'removed_ids':sorted(ids-found)})
    allowed=set(records[0])
   else:
    chosen=[r for r in rows if r.get('SQ_CANDIDATO') in ids];allowed=set(load(D/'status-official.json')[0])
   sanitized=[{k:r.get(k,'') for k in sorted(allowed)} for r in chosen]
   save(OUT/(name+'-snapshot.json'),sanitized);evidence['selected_count']=len(chosen);refresh['sources'].append(evidence)
  except Exception as exc:refresh['errors'].append({'stage':name,'error':str(exc)})
 def profile(cid):
  address=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/RS/20322002026/candidato/{cid}'
  try:
   p,digest=get(address)
   if str(p.get('id'))!=cid:raise ValueError('Candidate ID mismatch')
   allowed=('id','nomeUrna','numero','nomeCompleto','descricaoSituacao','descricaoTotalizacao','cargo','partido','candidatoApto','isCandidatoInapto','descricaoSituacaoCandidato')
   return cid,{'url':address,'checked_at':NOW,'sha256':digest,'data':{k:p.get(k) for k in allowed}}
  except Exception as exc:return cid,{'url':address,'checked_at':NOW,'error':str(exc)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:profiles=dict(pool.map(profile,sorted(ids)))
 refresh['profiles_success']=sum('data' in p for p in profiles.values());save(OUT/'profiles-snapshot.json',profiles);save(A/'official-refresh.json',refresh)
 # Missing vote records require identity inspection. Do not silently overwrite votes.
 pending=scope['unresolved_votes'];report={'checked_at':NOW,'targets':[],'sources':[],'errors':[]}
 for year in sorted({int(p['year']) for p in pending}):
  ts=[p for p in pending if int(p['year'])==year]
  for kind,address in [('registration',BASE+f'consulta_cand/consulta_cand_{year}.zip'),('votes',BASE+f'votacao_candidato_munzona/votacao_candidato_munzona_{year}.zip')]:
   try:
    rows,proof=csv_rows(address);proof['kind']=kind;report['sources'].append(proof)
    def pick(r,*ks):return next((r[k] for k in ks if k in r),'')
    for t in ts:
     name=norm(by[t['id']]['NM_CANDIDATO']);sid=str(t['historical_id']);office=norm(t.get('office',''));old=next((h for h in hist[t['id']] if str(h['year'])==str(year) and str(h['candidate_id'])==sid),{})
     groups=collections.defaultdict(lambda:{'rows':0,'votes':0,'sample':None})
     for r in rows:
      rid=pick(r,'SQ_CANDIDATO','SEQUENCIAL_CANDIDATO');rn=pick(r,'NM_CANDIDATO','NOME_CANDIDATO');ro=pick(r,'DS_CARGO','DESCRICAO_CARGO');place=pick(r,'NM_UE','DESCRICAO_UE','NM_MUNICIPIO','NOME_MUNICIPIO')
      if rid!=sid and norm(rn)!=name:continue
      if norm(ro)!=office:continue
      turn=pick(r,'NR_TURNO','NUM_TURNO') or '1'
      if int(turn)!=int(t.get('round',1)):continue
      if norm(old.get('place','RS')) not in ('rs','rio grande do sul',norm(place)):continue
      allowed=('SQ_CANDIDATO','SEQUENCIAL_CANDIDATO','NM_CANDIDATO','NOME_CANDIDATO','NM_URNA_CANDIDATO','NOME_URNA_CANDIDATO','NR_CANDIDATO','NUMERO_CANDIDATO','DS_CARGO','DESCRICAO_CARGO','NM_UE','DESCRICAO_UE','NR_TURNO','NUM_TURNO','SG_PARTIDO','SIGLA_PARTIDO','DS_SITUACAO_CANDIDATURA','DS_DETALHE_SITUACAO_CAND','DES_SITUACAO_CANDIDATURA','DS_SIT_TOT_TURNO','DESC_SIT_CAND_TOT')
      key=(rid,rn,ro,place,turn);g=groups[key];g['rows']+=1;g['sample']={k:r[k] for k in allowed if k in r}
      amount=pick(r,'QT_VOTOS_NOMINAIS','QTDE_VOTOS')
      if amount:
       n=int(amount)
       if n<0:raise ValueError('Negative nominal amount')
       g['votes']+=n
     report['targets'].append({'id':t['id'],'name':t['name'],'year':year,'historical_id':sid,'kind':kind,'expected_name':by[t['id']]['NM_CANDIDATO'],'office':t.get('office'),'place':old.get('place'),'groups':list(groups.values()),'source':address})
   except Exception as exc:report['errors'].append({'year':year,'kind':kind,'error':str(exc)})
 save(A/'vote-investigation.json',report)
 print(json.dumps({'refresh':refresh,'vote_target_checks':len(report['targets']),'vote_errors':report['errors']},ensure_ascii=False,indent=2))
if __name__=='__main__':run()

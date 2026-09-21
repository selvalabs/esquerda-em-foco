"""PR 2026: frozen, public-only official census. Never writes SC/RS paths."""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, io, json, re, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/pr'; DOC=ROOT/'docs/pr'; ASSETS=ROOT/'pr/assets'
SCOPE_CONFIG=json.loads((ROOT/'config/party-scope-2026.json').read_text(encoding='utf-8'))
ALL_PARTIES=SCOPE_CONFIG['parties']; PARTIES_BY_OFFICE={code:list(ALL_PARTIES) for code in ('6','7')}
PARTY={p.upper():p for p in ALL_PARTIES}; PARTY_BY_OFFICE={code:{p.upper() for p in parties} for code,parties in PARTIES_BY_OFFICE.items()}
SCOPE_VERSION=3
ARCHIVE='https://cdn.tse.jus.br/estatistica/sead/odsele/'
URLS={'candidates':ARCHIVE+'consulta_cand/consulta_cand_2026.zip','status':ARCHIVE+'consulta_cand_complementar/consulta_cand_complementar_2026.zip','social':ARCHIVE+'consulta_cand/rede_social_candidato_2026.zip','history':ARCHIVE+'historico_candidatura/historico_candidatura_2026.zip','photos':'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_PR_div.zip','map':'https://servicodados.ibge.gov.br/api/v3/malhas/estados/41?formato=image/svg&qualidade=minima'}
KEEP='DT_GERACAO HH_GERACAO ANO_ELEICAO CD_ELEICAO DS_ELEICAO SG_UF CD_CARGO DS_CARGO SQ_CANDIDATO NR_CANDIDATO NM_CANDIDATO NM_URNA_CANDIDATO SG_PARTIDO NM_PARTIDO NR_PARTIDO NR_FEDERACAO NM_FEDERACAO SG_FEDERACAO DS_SITUACAO_CANDIDATURA DS_DETALHE_SITUACAO_CAND DS_SITUACAO_JULGAMENTO DS_SITUACAO_CASSACAO DS_SITUACAO_SUBSTITUICAO DS_OCUPACAO ST_REELEICAO NM_MUNICIPIO_NASCIMENTO SG_UF_NASCIMENTO'.split()
HISTORY_KEEP='DT_GERACAO HH_GERACAO SQ_CANDIDATO_ATUAL SQ_CANDIDATO ANO_ELEICAO CD_ELEICAO DS_ELEICAO NR_TURNO SG_UF SG_UE NM_UE CD_CARGO DS_CARGO NR_CANDIDATO NM_URNA_CANDIDATO NR_PARTIDO SG_PARTIDO DS_SIT_TOT_TURNO CD_SIT_TOT_TURNO'.split()
for p in (DATA,DOC,ASSETS):p.mkdir(parents=True,exist_ok=True)
def now():return datetime.now(timezone.utc).isoformat()
def save(path,obj):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def read(path,default):return json.loads(path.read_text()) if path.exists() else default
def get(url,timeout=60,attempts=3):
 errors=[]
 for attempt in range(attempts):
  try:
   req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (EsquerdaEmFoco; public electoral census)','Accept':'*/*'})
   with urllib.request.urlopen(req,timeout=timeout) as response:raw=response.read()
   if not raw:raise ValueError('Empty response')
   return raw
  except Exception as exc:errors.append(str(exc));time.sleep(attempt+1)
 raise RuntimeError('; '.join(errors))
def ziprows(raw):
 archive=zipfile.ZipFile(io.BytesIO(raw));names=[n for n in archive.namelist() if n.upper().endswith('_PR.CSV')]
 if not names:
  csvnames=[n for n in archive.namelist() if n.lower().endswith('.csv')];names=[n for n in csvnames if 'BRASIL' in n.upper()] or (csvnames if len(csvnames)==1 else [])
 if len(names)!=1:raise ValueError('Expected unique PR or national CSV: '+str(names))
 blob=archive.read(names[0])
 try:text=blob.decode('utf-8-sig')
 except UnicodeDecodeError:text=blob.decode('latin-1')
 rows=list(csv.DictReader(io.StringIO(text),delimiter=';'))
 if not rows:raise ValueError('Empty official CSV')
 return rows,{'member':names[0],'member_sha256':hashlib.sha256(blob).hexdigest(),'generated_at':rows[0].get('DT_GERACAO','')+' '+rows[0].get('HH_GERACAO',''),'headers':list(rows[0])}
def collect():
 manifest=read(DATA/'manifest.json',{}) or {'schema_version':1,'state':'PR','election_year':2026,'collected_at':now(),'sources':{},'errors':[]}
 refresh=manifest.get('scope_version')!=SCOPE_VERSION or not (DATA/'candidates-official.json').exists()
 manifest['scope_version']=SCOPE_VERSION;manifest['scope']=ALL_PARTIES;manifest['scope_by_office']=PARTIES_BY_OFFICE;manifest['scope_rule']=SCOPE_CONFIG['rule']
 if refresh:
  raw=get(URLS['candidates'],180);rows,meta=ziprows(raw)
  universe=[r for r in rows if r.get('SG_UF')=='PR' and r.get('ANO_ELEICAO')=='2026' and r.get('CD_CARGO') in ('6','7')]
  selected=[r for r in universe if r.get('CD_CARGO') in PARTY_BY_OFFICE and r.get('SG_PARTIDO','').upper() in PARTY_BY_OFFICE[r['CD_CARGO']]]
  assert selected and len({r['SQ_CANDIDATO'] for r in selected})==len(selected),'Empty or duplicate official census'
  public=[{k:r.get(k,'') for k in KEEP} for r in selected]
  for r in public:r['SG_PARTIDO']=PARTY[r['SG_PARTIDO'].upper()]
  save(DATA/'candidates-official.json',public)
  manifest['sources']['candidates']={'url':URLS['candidates'],'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':now(),**meta};manifest['census']={}
  for code,slug in [('6','deputados-federais'),('7','deputados-estaduais')]:
   allrows=[r for r in universe if r['CD_CARGO']==code];chosen=[r for r in public if r['CD_CARGO']==code]
   manifest['census'][slug]={'office_code':code,'all_parties_total':len(allrows),'selected_total':len(chosen),'outside_scope_total':len(allrows)-len(chosen),'all_by_party':dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in allrows).items())),'selected_by_party':dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in chosen).items())),'scope_parties_without_record':[p for p in PARTIES_BY_OFFICE[code] if not any(r['SG_PARTIDO']==p for r in chosen)]}
  save(DATA/'manifest.json',manifest)
 records=read(DATA/'candidates-official.json',[]);ids={r['SQ_CANDIDATO'] for r in records}
 for kind in ('status','social','history'):
  target=DATA/(kind+'-official.json')
  if target.exists() and not refresh:continue
  try:
   raw=get(URLS[kind],180);rows,meta=ziprows(raw)
   if kind=='history':
    selected=[r for r in rows if r.get('SQ_CANDIDATO_ATUAL') in ids];allowed=HISTORY_KEEP
    assert 'SQ_CANDIDATO_ATUAL' in rows[0],'Historical identity link missing'
   else:
    selected=[r for r in rows if r.get('SQ_CANDIDATO') in ids];allowed=['SQ_CANDIDATO','DT_GERACAO','HH_GERACAO']
    allowed+=['DS_URL','NR_ORDEM'] if kind=='social' else [k for k in rows[0] if k.startswith(('DS_SIT','CD_SIT','DS_DETALHE_SIT','CD_DETALHE_SIT'))]
   save(target,[{k:r[k] for k in allowed if k in r} for r in selected]);manifest['sources'][kind]={'url':URLS[kind],'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':now(),'selected_rows':len(selected),**meta}
  except Exception as exc:manifest['errors'].append({'stage':kind,'at':now(),'error':str(exc)})
  save(DATA/'manifest.json',manifest)
 if refresh or not (DATA/'photos-official.json').exists():
  try:
   raw=get(URLS['photos'],240);archive=zipfile.ZipFile(io.BytesIO(raw));matched={}
   for member in archive.namelist():
    if not member.lower().endswith(('.jpg','.jpeg','.png')):continue
    found=[s for s in re.findall(r'(?<!\d)\d{12}(?!\d)',Path(member).name) if s in ids]
    if len(found)!=1:continue
    cid=found[0];blob=archive.read(member);dest=ASSETS/'photos'/(cid+'.webp');dest.parent.mkdir(parents=True,exist_ok=True)
    with Image.open(io.BytesIO(blob)) as image:
     image=image.convert('RGB');image.thumbnail((320,400));image.save(dest,'WEBP',quality=85,method=6)
    matched[cid]={'path':'../assets/photos/'+cid+'.webp','source_member':member,'source_sha256':hashlib.sha256(blob).hexdigest(),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
   save(DATA/'photos-official.json',matched);manifest['sources']['photos']={'url':URLS['photos'],'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':now(),'matched':len(matched)}
  except Exception as exc:manifest['errors'].append({'stage':'photos','at':now(),'error':str(exc)})
 if not (ASSETS/'pr-ibge.svg').exists():
  try:
   raw=get(URLS['map']);assert b'<svg' in raw;(ASSETS/'pr-ibge.svg').write_bytes(raw);manifest['sources']['map']={'url':URLS['map'],'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':now()}
  except Exception as exc:manifest['errors'].append({'stage':'map','at':now(),'error':str(exc)})
 save(DATA/'manifest.json',manifest)
 # CSV CD_ELEICAO and the REST election identifier belong to different namespaces.
 election_url='https://divulgacandcontas.tse.jus.br/divulga/rest/v1/eleicao/ordinarias'
 election_data=json.loads(get(election_url));matches=[e for e in election_data if e.get('ano')==2026 and e.get('tipoEleicao')=='O']
 assert len(matches)==1,'Ambiguous 2026 REST election'
 election_id=str(matches[0]['id']);save(DATA/'election-api.json',{'url':election_url,'checked_at':now(),'election':matches[0]})
 profiles=read(DATA/'profiles-official.json',{})
 def profile(row):
  cid=row['SQ_CANDIDATO'];url=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/PR/{election_id}/candidato/{cid}'
  try:
   raw=get(url,20,attempts=1);data=json.loads(raw);assert str(data.get('id'))==cid
   allowed=['id','nomeUrna','numero','nomeCompleto','descricaoSituacao','descricaoTotalizacao','ocupacao','cargo','partido','eleicao','sites','eleicoesAnteriores','candidatoApto','isCandidatoInapto','descricaoSituacaoCandidato','descricaoSituacaoComplementar']
   return cid,{'data':{k:data[k] for k in allowed if k in data},'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':now()}
  except Exception as exc:return cid,{'url':url,'error':str(exc),'checked_at':now()}
 missing=[r for r in records if not profiles.get(r['SQ_CANDIDATO'],{}).get('data')]
 with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
  for cid,value in pool.map(profile,missing):profiles[cid]=value
 save(DATA/'profiles-official.json',profiles)
 manifest['profiles_read']=sum('data' in p for p in profiles.values());manifest['profiles_failed']=sum('error' in p for p in profiles.values());manifest['finished_at']=now();save(DATA/'manifest.json',manifest)
 print(json.dumps({'census':manifest['census'],'profiles_read':manifest['profiles_read'],'photos':len(read(DATA/'photos-official.json',{})),'errors':manifest['errors']},ensure_ascii=False,indent=2))
if __name__=='__main__':collect()

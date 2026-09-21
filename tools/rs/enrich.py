"""Frozen, public-only RS enrichment; source errors remain visible in the manifest."""
from __future__ import annotations
import collections, csv, hashlib, io, json, os, re, time, urllib.request, zipfile
from pathlib import Path
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
OUT = ROOT/'data/rs'; DOC = ROOT/'docs/rs'; ASSETS = ROOT/'rs/deputados-federais/assets'
SCOPE_CONFIG=json.loads((ROOT/'config/party-scope-2026.json').read_text(encoding='utf-8')); SCOPE=SCOPE_CONFIG['parties']
PARTY = {p.upper():p for p in SCOPE}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def get(url, timeout=100):
    last = None
    for attempt in range(2):
        try:
            req = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0 (compatible; EsquerdaEmFoco/1.0; public data audit)','Accept':'*/*'})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return response.read()
        except Exception as exc:
            last = exc; time.sleep(2)
    raise RuntimeError(str(last))

def rows_from_zip(raw, suffix='_RS.CSV'):
    archive = zipfile.ZipFile(io.BytesIO(raw))
    names = [n for n in archive.namelist() if n.upper().endswith(suffix)]
    if not names:
        names = [n for n in archive.namelist() if n.lower().endswith('.csv') and ('BRASIL' in n.upper() or len([m for m in archive.namelist() if m.lower().endswith('.csv')]) == 1)]
    if not names:
        raise ValueError('No matching CSV: '+str(archive.namelist()))
    result = []
    for name in names:
        data = archive.read(name)
        try: text = data.decode('utf-8-sig')
        except UnicodeDecodeError: text = data.decode('latin-1')
        result.extend(csv.DictReader(io.StringIO(text), delimiter=';'))
    return result, names

manifest = json.loads((OUT/'manifest.json').read_text())
if manifest.get('enrichment_version') == 2:
    print('Using frozen enrichment snapshot'); raise SystemExit(0)
manifest['enrichment_started_at'] = datetime.now(timezone.utc).isoformat()
manifest['scope'] = {'parties':SCOPE,'rule':SCOPE_CONFIG['rule']}

base_url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/consulta_cand_2026.zip'
raw = get(base_url)
rows, members = rows_from_zip(raw)
federal = [r for r in rows if r.get('SG_UF')=='RS' and r.get('CD_CARGO')=='6' and r.get('ANO_ELEICAO')=='2026']
selected = [r for r in federal if r.get('SG_PARTIDO','').upper() in PARTY]
assert selected and len({r['SQ_CANDIDATO'] for r in selected}) == len(selected)
keep = ['DT_GERACAO','HH_GERACAO','ANO_ELEICAO','CD_ELEICAO','DS_ELEICAO','SG_UF','CD_CARGO','DS_CARGO','SQ_CANDIDATO','NR_CANDIDATO','NM_CANDIDATO','NM_URNA_CANDIDATO','SG_PARTIDO','NM_PARTIDO','NR_PARTIDO','NR_FEDERACAO','NM_FEDERACAO','SG_FEDERACAO','DS_SITUACAO_CANDIDATURA','DS_DETALHE_SITUACAO_CAND','DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CASSACAO','DS_SITUACAO_SUBSTITUICAO','DS_OCUPACAO','ST_REELEICAO','NM_MUNICIPIO_NASCIMENTO','SG_UF_NASCIMENTO']
public = [{k:r.get(k,'') for k in keep} for r in selected]
for r in public: r['SG_PARTIDO'] = PARTY[r['SG_PARTIDO'].upper()]
write(OUT/'candidates-official.json', public)
write(DOC/'source-schema.json', {'candidate_headers':list(rows[0])})
manifest['selected_count'] = len(public)
manifest['selected_by_party'] = dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in public).items()))
manifest['empty_parties'] = [p for p in SCOPE if p not in manifest['selected_by_party']]
manifest['all_rs_federal_count'] = len(federal)
manifest['sources'].append({'url':base_url,'sha256':hashlib.sha256(raw).hexdigest(),'members':members,'generated_at':public[0]['DT_GERACAO']+' '+public[0]['HH_GERACAO'],'stage':'case-normalized definitive scope'})
ids = {r['SQ_CANDIDATO'] for r in public}

def record_error(stage, exc):
    manifest.setdefault('errors', []).append({'source':stage,'error':str(exc)})

social_url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip'
try:
    social_raw = get(social_url); social, names = rows_from_zip(social_raw)
    social = [{k:v for k,v in r.items() if k in ['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO']} for r in social if r.get('SQ_CANDIDATO') in ids]
    write(OUT/'social-official.json',social)
    manifest['sources'].append({'url':social_url,'sha256':hashlib.sha256(social_raw).hexdigest(),'members':names,'selected_rows':len(social)})
except Exception as exc: record_error('social',exc)

complement_url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip'
try:
    complementary_raw = get(complement_url); complementary, names = rows_from_zip(complementary_raw)
    headers = list(complementary[0]) if complementary else []
    allowed = [k for k in headers if k.startswith(('DS_SIT','CD_SIT','DS_DETALHE_SIT','CD_DETALHE_SIT')) or k in ['SQ_CANDIDATO','DT_GERACAO','HH_GERACAO','ST_REELEICAO']]
    records = [{k:r.get(k,'') for k in allowed} for r in complementary if r.get('SQ_CANDIDATO') in ids]
    write(OUT/'status-official.json',records)
    write(DOC/'complement-schema.json',{'headers':headers,'selected_count':len(records)})
    manifest['sources'].append({'url':complement_url,'sha256':hashlib.sha256(complementary_raw).hexdigest(),'members':names,'selected_rows':len(records)})
except Exception as exc: record_error('complementary',exc)

history_url = 'https://cdn.tse.jus.br/estatistica/sead/odsele/historico_candidatura/historico_candidatura_2026.zip'
try:
    history_raw = get(history_url); history, names = rows_from_zip(history_raw)
    headers = list(history[0]) if history else []
    id_keys = [k for k in headers if 'SQ_CANDIDATO' in k]
    historical = [r for r in history if any(r.get(k) in ids for k in id_keys)]
    allowed = [k for k in headers if not any(s in k for s in ['CPF','TITULO_ELEITORAL','CNPJ','EMAIL','TELEFONE','NASCIMENTO','ESTADO_CIVIL','COR_RACA','GENERO','SEXO','ENDERECO'])]
    records = [{k:r.get(k,'') for k in allowed} for r in historical]
    write(OUT/'history-official.json',records)
    write(DOC/'history-schema.json',{'headers':headers,'id_keys':id_keys,'selected_rows':len(records),'sample':records[:3]})
    manifest['sources'].append({'url':history_url,'sha256':hashlib.sha256(history_raw).hexdigest(),'members':names,'selected_rows':len(records)})
except Exception as exc: record_error('history',exc)

photos_url = 'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_RS_div.zip'
try:
    photo_raw = get(photos_url,180); archive = zipfile.ZipFile(io.BytesIO(photo_raw)); photo_dir = ASSETS/'photos'; photo_dir.mkdir(parents=True, exist_ok=True)
    matches = {}
    for name in archive.namelist():
        match = re.search(r'(2100\d{8})',name)
        if match and match[1] in ids and name.lower().endswith(('.jpg','.jpeg','.png')):
            candidate_id=match[1]; ext=Path(name).suffix.lower(); filename=candidate_id+ext
            data=archive.read(name); (photo_dir/filename).write_bytes(data)
            matches[candidate_id]={'path':'assets/photos/'+filename,'source_member':name,'sha256':hashlib.sha256(data).hexdigest()}
    write(OUT/'photos-official.json',matches)
    manifest['sources'].append({'url':photos_url,'sha256':hashlib.sha256(photo_raw).hexdigest(),'matched_photos':len(matches)})
except Exception as exc: record_error('photos',exc)

try:
    url = 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/eleicao/ordinarias'
    elections = json.loads(get(url))
    current = [e for e in elections if e.get('ano')==2026 and e.get('tipoEleicao')=='O']
    write(OUT/'election-api.json',current)
    if current:
        election_id = current[0]['id']; sample_id=public[0]['SQ_CANDIDATO']
        detail_url=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/RS/{election_id}/candidato/{sample_id}'
        detail=json.loads(get(detail_url,40))
        allowed=['id','nomeUrna','nomeCompleto','numero','cargo','partido','eleicao','situacaoCandidato','descricaoSituacao','descricaoTotalizacao','descricaoSituacaoComplementar','fotoUrl','redesSociais','eleicoesAnteriores','candidaturasAnteriores','stReeleicao','ocupacao','sites']
        write(DOC/'detail-schema.json', {'url':detail_url,'keys':list(detail),'public_sample':{k:detail[k] for k in allowed if k in detail}})
except Exception as exc: record_error('divulgacand_detail',exc)

if os.getenv('EEFOCO_SKIP_CAMARA_REFRESH')=='1':
    manifest['sources'].append({'kind':'camara_current_profiles','refresh':'preserved_existing_snapshot','reason':'scope-only reconciliation'})
else:
    try:
        url='https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=RS&itens=100&ordem=ASC&ordenarPor=nome'
        listing=json.loads(get(url))['dados']; profiles=[]
        for deputy in listing:
            detail=json.loads(get(deputy['uri'],30))['dados']
            status=detail.get('ultimoStatus',{})
            profiles.append({'id':detail['id'],'nomeCivil':detail.get('nomeCivil'),'nome':status.get('nome',deputy.get('nome')),'nomeEleitoral':status.get('nomeEleitoral'),'situacao':status.get('situacao'),'condicaoEleitoral':status.get('condicaoEleitoral'),'siglaPartido':status.get('siglaPartido'),'siglaUf':status.get('siglaUf'),'urlFoto':status.get('urlFoto'),'redeSocial':detail.get('redeSocial',[]),'source_url':deputy['uri'],'public_url':'https://www.camara.leg.br/deputados/'+str(detail['id']),'collected_at':datetime.now(timezone.utc).isoformat()})
        write(OUT/'camara-current.json',profiles)
        manifest['sources'].append({'url':url,'records':len(profiles),'kind':'camara_current_profiles'})
    except Exception as exc: record_error('camara_current',exc)
    
manifest['enrichment_version']=2
manifest['enrichment_finished_at']=datetime.now(timezone.utc).isoformat()
write(OUT/'manifest.json',manifest)
print(json.dumps({'count':len(public),'parties':manifest['selected_by_party'],'errors':manifest.get('errors')},ensure_ascii=False,indent=2))

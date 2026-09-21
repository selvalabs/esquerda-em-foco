"""Collect the RS state-deputy edition without changing any existing edition.

Public exports are explicit column projections, not copies of private registration
fields. SHA-256 identifies the original source bytes; no full-archive hash is
claimed for a partial download. Re-running uses the frozen successful snapshot.
"""
from __future__ import annotations
import collections
import concurrent.futures
import csv
import hashlib
import io
import json
import re
import subprocess
import time
import unicodedata
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / 'data/rs-estaduais'
DOC = ROOT / 'docs/rs-estaduais'
DEST = ROOT / 'rs/deputados-estaduais'
TSE = 'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
CDN = 'https://cdn.tse.jus.br/estatistica/sead/'
API = 'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/'
COLUMNS = ['DT_GERACAO','HH_GERACAO','ANO_ELEICAO','CD_ELEICAO','DS_ELEICAO','SG_UF','CD_CARGO','DS_CARGO','SQ_CANDIDATO','NR_CANDIDATO','NM_CANDIDATO','NM_URNA_CANDIDATO','SG_PARTIDO','NM_PARTIDO','NR_PARTIDO','NR_FEDERACAO','NM_FEDERACAO','SG_FEDERACAO','DS_SITUACAO_CANDIDATURA','DS_DETALHE_SITUACAO_CAND','DS_SITUACAO_JULGAMENTO','DS_SITUACAO_CASSACAO','DS_SITUACAO_SUBSTITUICAO','DS_OCUPACAO','ST_REELEICAO','NM_MUNICIPIO_NASCIMENTO','SG_UF_NASCIMENTO']
PRIVATE = ('CPF','TITULO_ELEITORAL','CNPJ','EMAIL','TELEFONE','NASCIMENTO','ESTADO_CIVIL','COR_RACA','GENERO','SEXO','ENDERECO')


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load(path, default):
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFD',str(value).casefold()) if unicodedata.category(c) != 'Mn')


def clean(value):
    return '' if value is None or str(value).strip() in ('','#NE','#NULO','-1','-3') else str(value).strip()


def get(url, timeout=60):
    errors = []
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent':'EsquerdaEmFoco/1.0 (public electoral source audit)','Accept':'*/*'})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                raw = response.read(240_000_001)
            if not raw or len(raw) > 240_000_000:
                raise ValueError('Empty or oversized response')
            return raw
        except Exception as exc:
            errors.append(str(exc))
            if attempt < 2:
                time.sleep(1 + attempt)
    raise RuntimeError('; '.join(errors))


def zip_rows(url):
    raw = get(url, 90)
    source = {'url':url,'checked_at':now(),'sha256':digest(raw),'bytes':len(raw),'members':[]}
    rows = []
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names = [n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
        if not names:
            all_csv = [n for n in archive.namelist() if n.lower().endswith('.csv')]
            names = [n for n in all_csv if 'BRASIL' in n.upper()] or (all_csv if len(all_csv) == 1 else [])
        if not names:
            raise ValueError('RS CSV absent in archive')
        for name in names:
            payload = archive.read(name)
            try:
                text = payload.decode('utf-8-sig')
            except UnicodeDecodeError:
                text = payload.decode('latin-1')
            reader = csv.DictReader(io.StringIO(text), delimiter=';')
            source['members'].append({'name':name,'sha256':digest(payload),'bytes':len(payload),'columns':reader.fieldnames})
            rows.extend(reader)
    return rows, source


def project_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f,fieldnames=columns,delimiter=';',quoting=csv.QUOTE_ALL,extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def collect():
    for directory in (DATA,DOC,DEST):
        directory.mkdir(parents=True,exist_ok=True)
    reference_path = ROOT / 'data/rs/manifest.json'
    reference = load(reference_path,{})
    parties = reference.get('scope',{}).get('parties')
    if not parties or len(parties) != len(set(p.upper() for p in parties)):
        raise ValueError('An explicit unambiguous RS/federal party scope is required')
    canonical_party = {p.upper():p for p in parties}
    manifest = load(DATA/'manifest.json',{})
    if manifest.get('collection_version') == 1:
        print('Reusing frozen RS/state official snapshot')
        reconcile()
        return
    baseline = subprocess.check_output(['git','merge-base','HEAD','origin/main'],cwd=ROOT,text=True).strip()
    protected = {}
    for name in ['index.html','deputados-estaduais','rs/deputados-federais','data/rs','tools/rs','assets','server','sitemap.xml']:
        protected[name] = subprocess.check_output(['git','rev-parse',f'{baseline}:{name}'],cwd=ROOT,text=True).strip()
    save(DOC/'baseline.json',{'commit':baseline,'protected_git_objects':protected,'scope_source':'data/rs/manifest.json','scope_source_sha256':digest(reference_path.read_bytes()),'parties':parties})
    manifest = {'schema_version':1,'state':'RS','office_code':7,'election_year':2026,'collected_at':now(),'baseline_commit':baseline,'scope':{'parties':parties,'source':'data/rs/manifest.json','rule':'Recorte explícito herdado da frente RS/federais. Não representa todos os partidos do estado nem uma classificação individual.'},'sources':[],'errors':[],'public_projection_note':'Arquivos raw preservam somente colunas públicas necessárias, com valores originais. Os hashes das fontes correspondem aos bytes integrais recebidos; CPF, título, contatos privados e demais campos pessoais não são publicados.'}
    rows, source = zip_rows(CDN+'odsele/consulta_cand/consulta_cand_2026.zip')
    required = {'SG_UF','CD_CARGO','ANO_ELEICAO','SQ_CANDIDATO','SG_PARTIDO','NR_CANDIDATO'}
    if not rows or not required.issubset(rows[0]):
        raise ValueError('Unexpected official candidacy schema')
    universe = [r for r in rows if r['SG_UF']=='RS' and r['CD_CARGO']=='7' and r['ANO_ELEICAO']=='2026']
    selected = [r for r in universe if r['SG_PARTIDO'].upper() in canonical_party]
    if not selected or len({r['SQ_CANDIDATO'] for r in universe}) != len(universe):
        raise ValueError('Empty selection or duplicate official identifiers')
    project_csv(DATA/'raw/candidaturas-rs-estaduais-2026.csv',selected,COLUMNS)
    project_csv(DATA/'raw/universo-rs-estaduais-2026.csv',universe,COLUMNS)
    public = [{k:r.get(k,'') for k in COLUMNS} for r in selected]
    for row in public:
        row['SG_PARTIDO'] = canonical_party[row['SG_PARTIDO'].upper()]
    save(DATA/'candidates-official.json',public)
    ids = {r['SQ_CANDIDATO'] for r in public}
    source['generated_at'] = public[0]['DT_GERACAO']+' '+public[0]['HH_GERACAO']
    source['kind'] = 'candidates'
    manifest['sources'].append(source)
    manifest.update({'all_rs_state_count':len(universe),'all_rs_state_by_party':dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in universe).items())),'selected_count':len(public),'selected_by_party':dict(sorted(collections.Counter(r['SG_PARTIDO'] for r in public).items())),'empty_parties':[p for p in parties if not any(r['SG_PARTIDO']==p for r in public)],'snapshot_generated_at':source['generated_at']})
    save(DATA/'manifest.json',manifest)
    jobs = [('status','odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip'),('social','odsele/consulta_cand/rede_social_candidato_2026.zip'),('history','odsele/historico_candidatura/historico_candidatura_2026.zip')]
    for kind, path in jobs:
        try:
            records, meta = zip_rows(CDN+path)
            if kind == 'history':
                relevant = [r for r in records if r.get('SQ_CANDIDATO_ATUAL') in ids and r.get('ANO_ELEICAO_ATUAL')=='2026']
                columns = [k for k in records[0] if not any(p in k for p in PRIVATE)]
            elif kind == 'social':
                relevant = [r for r in records if r.get('SQ_CANDIDATO') in ids]
                columns = ['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO']
            else:
                relevant = [r for r in records if r.get('SQ_CANDIDATO') in ids]
                columns = [k for k in records[0] if k.startswith(('DS_SIT','CD_SIT','DS_DETALHE_SIT','CD_DETALHE_SIT')) or k in ['SQ_CANDIDATO','DT_GERACAO','HH_GERACAO','ST_REELEICAO']]
            result = [{k:r.get(k,'') for k in columns} for r in relevant]
            save(DATA/f'{kind}-official.json',result)
            project_csv(DATA/f'raw/{kind}-rs-estaduais-2026.csv',relevant,columns)
            meta.update({'kind':kind,'selected_rows':len(result)})
            manifest['sources'].append(meta)
        except Exception as exc:
            manifest['errors'].append({'source':kind,'error':str(exc),'checked_at':now()})
        save(DATA/'manifest.json',manifest)
    try:
        photo_url = CDN+'eleicoes/eleicoes2026/fotos/foto_cand2026_RS_div.zip'
        raw = get(photo_url,120)
        photos = {}
        from PIL import Image, ImageOps
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            for name in archive.namelist():
                match = re.search(r'(?<!\d)(2100\d{8})(?!\d)',name)
                if not match or match[1] not in ids or not name.lower().endswith(('.jpg','.jpeg','.png')):
                    continue
                cid = match[1]
                original = archive.read(name)
                with Image.open(io.BytesIO(original)) as im:
                    image = ImageOps.exif_transpose(im).convert('RGB')
                    image.thumbnail((320,400))
                    output = io.BytesIO()
                    image.save(output,format='WEBP',quality=88,method=6)
                optimized = output.getvalue()
                path = DEST/'assets/photos'/f'{cid}.webp'
                path.parent.mkdir(parents=True,exist_ok=True)
                path.write_bytes(optimized)
                photos[cid] = {'path':f'assets/photos/{cid}.webp','source_member':name,'source_sha256':digest(original),'sha256':digest(optimized),'source_url':photo_url,'width':image.width,'height':image.height}
        save(DATA/'photos-official.json',photos)
        manifest['sources'].append({'kind':'photos','url':photo_url,'sha256':digest(raw),'bytes':len(raw),'matched_photos':len(photos),'checked_at':now()})
    except Exception as exc:
        manifest['errors'].append({'source':'photos','error':str(exc),'checked_at':now()})
    map_path = ROOT/'rs/deputados-federais/assets/rs-ibge.svg'
    (DEST/'assets').mkdir(parents=True,exist_ok=True)
    if map_path.exists():
        (DEST/'assets/rs-ibge.svg').write_bytes(map_path.read_bytes())
        manifest['sources'].append({'kind':'map','reused_from':'rs/deputados-federais/assets/rs-ibge.svg','sha256':digest(map_path.read_bytes()),'original_url':'https://servicodados.ibge.gov.br/api/v3/malhas/estados/43?formato=image/svg&qualidade=minima'})
    manifest['collection_version'] = 1
    manifest['finished_at'] = now()
    save(DATA/'manifest.json',manifest)
    reconcile()
    print(json.dumps(manifest,ensure_ascii=False,indent=2))


def reconcile():
    records = load(DATA/'candidates-official.json',[])
    profiles = load(DATA/'profiles-official.json',{})
    elections = load(DATA/'election-api.json',[])
    if not elections:
        raw = get(API+'eleicao/ordinarias',25)
        elections = [e for e in json.loads(raw) if e.get('ano')==2026 and e.get('tipoEleicao')=='O']
        save(DATA/'election-api.json',elections)
    if len(elections) != 1:
        raise ValueError('2026 ordinary election API identifier is ambiguous')
    election_id = elections[0]['id']
    def profile(row):
        cid = row['SQ_CANDIDATO']
        address = API+f'candidatura/buscar/2026/RS/{election_id}/candidato/{cid}'
        stamp = now()
        try:
            raw = get(address,25)
            obj = json.loads(raw)
            if str(obj.get('id')) != cid:
                raise ValueError('DivulgaCand identifier mismatch')
            allowed = ['id','nomeUrna','numero','nomeCompleto','descricaoSituacao','descricaoTotalizacao','ocupacao','cargo','partido','eleicao','sites','eleicoesAnteriores','st_REELEICAO','candidatoApto','isCandidatoInapto','descricaoSituacaoCandidato']
            data = {k:obj[k] for k in allowed if k in obj}
            return cid,{'data':data,'url':address,'sha256':digest(raw),'checked_at':stamp}
        except Exception as exc:
            return cid,{'url':address,'error':str(exc),'checked_at':stamp}
    missing = [r for r in records if not profiles.get(r['SQ_CANDIDATO'],{}).get('data')]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for cid, result in pool.map(profile,missing):
            profiles[cid] = result
    save(DATA/'profiles-official.json',profiles)
    histories = collections.defaultdict(dict)
    ids = {r['SQ_CANDIDATO'] for r in records}
    for row in load(DATA/'history-official.json',[]):
        cid = row.get('SQ_CANDIDATO_ATUAL')
        year = int(row['ANO_ELEICAO'])
        if cid not in ids or year >= 2026:
            continue
        turn = int(row.get('NR_TURNO') or 1)
        old_id = row['SQ_CANDIDATO']
        key = (year,old_id,turn)
        histories[cid][key] = {'year':year,'round':turn,'candidate_id':old_id,'election_id':row.get('CD_ELEICAO'),'office':row.get('DS_CARGO'),'place':row.get('NM_UE'),'uf':row.get('SG_UF'),'party':row.get('SG_PARTIDO'),'result':clean(row.get('DS_SIT_TOT_TURNO')),'votes':None,'source':CDN+'odsele/historico_candidatura/historico_candidatura_2026.zip','identity_method':'TSE SQ_CANDIDATO_ATUAL linkage'}
    discrepancies = []
    checks = []
    for row in records:
        cid = row['SQ_CANDIDATO']
        p = profiles.get(cid,{})
        obj = p.get('data',{})
        mismatches = []
        if obj:
            comparisons = [('number',str(obj.get('numero')),row['NR_CANDIDATO']),('party',str(obj.get('partido',{}).get('sigla','')).upper(),row['SG_PARTIDO'].upper()),('office',str(obj.get('cargo',{}).get('codigo')),row['CD_CARGO']),('civil_name',norm(obj.get('nomeCompleto','')),norm(row['NM_CANDIDATO']))]
            mismatches = [{'field':k,'api':a,'csv':b} for k,a,b in comparisons if a != b]
            if mismatches:
                discrepancies.append({'candidate_id':cid,'mismatches':mismatches})
        checks.append({'candidate_id':cid,'api_read':bool(obj),'identity_fields_match':bool(obj) and not mismatches,'api_status':obj.get('descricaoSituacao'),'checked_at':p.get('checked_at'),'source':p.get('url')})
        for old in obj.get('eleicoesAnteriores',[]):
            year = int(old.get('nrAno') or old.get('ano') or old.get('anoEleicao') or 2026)
            old_id = str(old.get('id') or old.get('sqCandidato') or '')
            if year >= 2026 or not old_id:
                continue
            existing = [k for k in histories[cid] if k[0]==year and k[1]==old_id]
            if existing:
                for key in existing:
                    if old.get('txLink'):
                        histories[cid][key]['profile_url'] = old['txLink']
            else:
                cargo = old.get('cargo')
                if isinstance(cargo,dict):
                    cargo = cargo.get('nome') or cargo.get('descricao')
                histories[cid][(year,old_id,1)] = {'year':year,'round':1,'candidate_id':old_id,'election_id':old.get('idEleicao'),'office':cargo,'place':old.get('local'),'uf':None,'party':old.get('partido') or old.get('siglaPartido'),'result':old.get('situacaoTotalizacao'),'votes':None,'profile_url':old.get('txLink'),'source':p['url'],'identity_method':'DivulgaCand linked prior candidate ID','round_note':'Turno não informado pelo resumo REST; valor 1 usado apenas como chave provisória, não como confirmação de turno.'}
        histories[cid][(2026,cid,1)] = {'year':2026,'round':1,'candidate_id':cid,'office':'Deputado Estadual','place':'RIO GRANDE DO SUL','uf':'RS','party':row['SG_PARTIDO'],'result':'Registro de candidatura; sem resultado eleitoral nesta coleta','votes':None,'source':p.get('url') or TSE,'identity_method':'Current official ID'}
    normalized = {r['SQ_CANDIDATO']:sorted(histories[r['SQ_CANDIDATO']].values(),key=lambda h:(h['year'],h['round'],h['candidate_id'])) for r in records}
    save(DATA/'history-normalized.json',normalized)
    audit = {'checked_at':now(),'candidate_count':len(records),'profiles_read':sum(bool(p.get('data')) for p in profiles.values()),'identity_checks':checks,'identity_mismatches':discrepancies,'history_records':sum(len(v) for v in normalized.values()),'with_previous_history':sum(any(h['year']<2026 for h in v) for v in normalized.values()),'profile_errors':[{'candidate_id':k,**v} for k,v in profiles.items() if 'error' in v]}
    save(DOC/'reconciliation.json',audit)
    lines = ['# Censo inicial — RS / Deputado Estadual 2026','', '| Identificador TSE | Nome de urna | Partido | Número | Situação REST | Históricos anteriores |','|---|---|---|---|---|---|']
    for r in sorted(records,key=lambda x:(x['SG_PARTIDO'],x['NM_URNA_CANDIDATO'])):
        cid = r['SQ_CANDIDATO']
        lines.append('| '+' | '.join([cid,r['NM_URNA_CANDIDATO'],r['SG_PARTIDO'],r['NR_CANDIDATO'],profiles.get(cid,{}).get('data',{}).get('descricaoSituacao','Não consultado'),str(sum(h['year']<2026 for h in normalized[cid]))])+' |')
    (DOC/'census.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in audit.items() if k not in ('identity_checks','profile_errors')},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    collect()

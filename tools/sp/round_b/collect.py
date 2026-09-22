"""Isolated Round B public-source collection. Does not assign policy tags.
Run from a full repository checkout: python tools/sp/round_b/collect.py.
The Round A source files are never modified. Failed sources remain explicit.
"""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, io, ipaddress, json, re
import socket, subprocess, time, unicodedata, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

BASELINE = 'b42f2e1f108185c7f9c3d5af7e5e92e893aef574'
SC_REF = 'c2ce0d44f64c72c5949d373fa210d9144948d310'
OUT = Path('data/sp/round-b'); DOC = Path('docs/sp/round-b')
PORTAL = 'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
SOCIAL = 'https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip'
HISTORY = 'https://cdn.tse.jus.br/estatistica/sead/odsele/historico_candidatura/historico_candidatura_2026.zip'
PHOTOS = 'https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SP_div.zip'
MISSING = {'', '#NULO', '#NULO#', '#NE', '#NE#', '-1', '-3', '-4'}
HISTORY_KEYS = '''DT_GERACAO HH_GERACAO ANO_ELEICAO_ATUAL SQ_CANDIDATO_ATUAL SG_UF_ATUAL ANO_ELEICAO CD_TIPO_ELEICAO NM_TIPO_ELEICAO NR_TURNO CD_ELEICAO DS_ELEICAO DT_ELEICAO TP_ABRANGENCIA_ELEICAO SG_UF SG_UE NM_UE CD_CARGO DS_CARGO SQ_CANDIDATO NR_CANDIDATO NM_CANDIDATO NM_URNA_CANDIDATO NR_PARTIDO SG_PARTIDO NM_PARTIDO CD_SITUACAO_CANDIDATURA DS_SITUACAO_CANDIDATURA CD_SITUACAO_JULGAMENTO DS_SITUACAO_JULGAMENTO CD_SIT_TOT_TURNO DS_SIT_TOT_TURNO'''.split()

def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def fold(s): return ''.join(c for c in unicodedata.normalize('NFKD', s or '') if not unicodedata.combining(c)).upper().strip()
def meaningful(v): return None if v is None or str(v).strip().upper() in MISSING else str(v).strip()
def get(url, timeout=25, retries=2):
    error = None
    for attempt in range(retries):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'EsquerdaEmFoco/round-b-public-source-audit','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                raw=r.read()
                meta={'url':url,'final_url':r.geturl(),'retrieved_at':now(),'http_status':r.status,'sha256':sha(raw),'bytes':len(raw),'last_modified':r.headers.get('Last-Modified')}
            if not raw: raise ValueError('empty response')
            return raw,meta
        except Exception as exc:
            error=str(exc)
            if attempt+1<retries: time.sleep(1)
    raise RuntimeError(error)
def json_get(url, **kwargs):
    raw,meta=get(url,**kwargs)
    return json.loads(raw),meta

def zipped(url, predicate, keys):
    raw,meta=get(url,timeout=90)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[n for n in z.namelist() if n.upper().endswith('_SP.CSV')]
        if not members: members=[n for n in z.namelist() if n.upper().endswith('_BRASIL.CSV')]
        if len(members)!=1: raise ValueError('Expected exactly one state or national member')
        payload=z.read(members[0])
    try: text=payload.decode('utf-8-sig'); encoding='utf-8-sig'
    except UnicodeDecodeError: text=payload.decode('latin-1'); encoding='latin-1'
    reader=csv.DictReader(io.StringIO(text), delimiter=';'); selected=[]; generations=set(); count=0
    for ordinal,r in enumerate(reader,2):
        count+=1
        if predicate(r):
            selected.append({**{k:r[k] for k in keys if k in r},'_csv_record':ordinal})
            generations.add(r.get('DT_GERACAO','')+' '+r.get('HH_GERACAO',''))
    meta.update(member=members[0],member_sha256=sha(payload),encoding=encoding,headers=reader.fieldnames,total_member_records=count,selected_records=len(selected),generated_at=sorted(generations),locator='CSV record ordinal; header=1')
    return selected,meta

def social_url(raw):
    value=(raw or '').strip()
    if not meaningful(value): return None
    if not re.match(r'^https?://',value,re.I): return None
    p=urllib.parse.urlsplit(value)
    if p.scheme.lower() not in ('http','https') or not p.hostname or p.username or p.password: return None
    if any(ch.isspace() for ch in value): return None
    try:
        if not ipaddress.ip_address(p.hostname).is_global: return None
    except ValueError: pass
    if p.hostname.lower()=='localhost' or '.' not in p.hostname: return None
    return urllib.parse.urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path,p.query,p.fragment))

def collect():
    OUT.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'collection.json'
    if manifest_path.exists():
        print('Frozen collection exists; source recollection requires deliberate versioned refresh.'); return
    base=json.loads(Path('data/sp/normalized.json').read_text())
    candidates=base['candidates']; ids={c['id'] for c in candidates}
    assert len(ids)==234 and base['state']=='SP'
    protected={p:sha(Path(p).read_bytes()) for p in subprocess.check_output(['git','ls-files'],text=True).splitlines() if Path(p).is_file() and not p.startswith(('data/sp/round-b/','docs/sp/round-b/','tools/sp/round_b/','tests/sp/round_b/')) and p not in ['.github/workflows/sp-round-a.yml','.github/workflows/sp-round-b.yml']}
    manifest={'started_at':now(),'round_a_commit':BASELINE,'round_a_sha256':sha(Path('data/sp/normalized.json').read_bytes()),'sources':{},'errors':[],'candidate_count':len(ids),'notes':['Automated source collection is not editorial review.','No policy tag inferred from party, occupation, identity or keywords.']}
    def error(stage,exc):
        manifest['errors'].append({'stage':stage,'error':str(exc),'at':now()}); print(stage+': '+str(exc),flush=True)
    try:
        raw=subprocess.check_output(['git','show',SC_REF+':data/sc-federais-pautas/taxonomy-proposal.json'])
        original=json.loads(raw)
        topics=[]
        for t in original['topics']:
            old=t['label']; label='Saúde' if old=='Saúde pública e SUS' else old
            tid=re.sub(r'[^a-z0-9]+','-',fold(label).lower()).strip('-')
            topics.append({'id':tid,'label':label,'upstream_label':old,'kind':'documentary_topic','specific_measure_required':True})
        assert len({t['id'] for t in topics})==len(topics)
        taxonomy={'version':'1.0.0-documental','status':'fixed_for_sp_research_not_enabled_in_product','upstream_commit':SC_REF,'upstream_path':'data/sc-federais-pautas/taxonomy-proposal.json','upstream_sha256':sha(raw),'upstream_status':original['status'],'other_states_modified':False,'filters_implemented':False,'topics':topics,'rules':original['rules'],'position_values':['supports_measure','opposes_measure','authorship','coauthorship','documented_activity','statement_only'],'temporal_values':['dated_2026','dated_historical','undated'],'scope_note':'IDs reusable across states; no candidate assignments copied. Saúde is not automatic support for SUS.'}
        write(OUT/'taxonomy.json',taxonomy)
    except Exception as exc: error('taxonomy',exc)
    social=[]; history=[]; photos={}
    try:
        social,meta=zipped(SOCIAL,lambda r:r.get('SQ_CANDIDATO') in ids,['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO'])
        write(OUT/'social-official.json',social); manifest['sources']['social']=meta
        print('Social records: '+str(len(social)),flush=True)
    except Exception as exc: error('social',exc)
    try:
        history,meta=zipped(HISTORY,lambda r:r.get('SQ_CANDIDATO_ATUAL') in ids and r.get('ANO_ELEICAO_ATUAL')=='2026' and r.get('SG_UF_ATUAL')=='SP',HISTORY_KEYS)
        assert 'SQ_CANDIDATO_ATUAL' in meta['headers']
        write(OUT/'history-official.json',history); manifest['sources']['history']=meta
        print('History records: '+str(len(history)),flush=True)
    except Exception as exc: error('history',exc)
    try:
        raw,meta=get(PHOTOS,timeout=120)
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            for member in z.namelist():
                found=re.search(r'(2500\d{8})',member)
                if found and found[1] in ids and Path(member).suffix.lower() in ['.jpg','.jpeg','.png']:
                    cid=found[1]; payload=z.read(member); path=OUT/'photos'/(cid+Path(member).suffix.lower())
                    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(payload)
                    photos[cid]={'path':str(path),'source_url':PHOTOS,'source_member':member,'sha256':sha(payload),'bytes':len(payload),'retrieved_at':meta['retrieved_at'],'identity_method':'official_filename_candidate_id','visual_review':'not_performed'}
        meta['matched_count']=len(photos); manifest['sources']['photos']=meta; write(OUT/'photos.json',photos)
        print('Photo matches: '+str(len(photos)),flush=True)
    except Exception as exc: error('photos',exc)
    camara=[]; matches={}; listing_url='https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=SP&idLegislatura=57&itens=100&ordem=ASC&ordenarPor=nome'
    try:
        listing=[]; url=listing_url; pages=[]
        while url:
            body,meta=json_get(url); pages.append(meta); listing.extend(body['dados'])
            url=next((x['href'] for x in body.get('links',[]) if x.get('rel')=='next'),None)
            if len(pages)>10: raise ValueError('unexpected pagination')
        def deputy(d):
            try:
                obj,meta=json_get(d['uri'],timeout=18,retries=2); item=obj['dados']; s=item.get('ultimoStatus',{})
                return {'id':str(item['id']),'nomeCivil':item.get('nomeCivil'),'nome':s.get('nome'),'nomeEleitoral':s.get('nomeEleitoral'),'situacao':s.get('situacao'),'condicaoEleitoral':s.get('condicaoEleitoral'),'dataSituacao':s.get('data'),'siglaUf':s.get('siglaUf'),'siglaPartido':s.get('siglaPartido'),'redeSocial':item.get('redeSocial',[]),'urlWebsite':item.get('urlWebsite'),'source':meta,'public_url':'https://www.camara.leg.br/deputados/'+str(item['id'])}
            except Exception as exc: return {'id':str(d['id']),'source_url':d['uri'],'error':str(exc)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool: camara=list(pool.map(deputy,listing))
        manifest['sources']['camara']={'pages':pages,'roster_records':len(listing),'profile_records':sum('error' not in c for c in camara),'profile_errors':sum('error' in c for c in camara),'selection':'legislature57 SP, not assertion that all are currently exercising'}
        write(OUT/'camara-sp-public.json',camara)
        for c in candidates:
            exact=[d for d in camara if d.get('nomeCivil') and fold(d['nomeCivil'])==fold(c['full_name'])]
            if len(exact)==1:
                matches[c['id']]={'identity_method':'exact_normalized_civil_name','profile':exact[0]}
            elif len(exact)>1: error('identity_ambiguous',c['id'])
        write(OUT/'camara-matches.json',matches); print('Exact civil-name Câmara matches: '+str(len(matches)),flush=True)
    except Exception as exc: error('camara',exc)
    details={}
    def detail(c):
        url='https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/SP/20322002026/candidato/'+c['id']
        try:
            obj,meta=json_get(url,timeout=12,retries=1)
            identity=str(obj.get('id'))==c['id'] and fold(obj.get('nomeCompleto',''))==fold(c['full_name'])
            allowed=['id','nomeUrna','nomeCompleto','numero','descricaoSituacao','descricaoTotalizacao','descricaoSituacaoComplementar','fotoUrl','stReeleicao','ocupacao']
            public={k:obj[k] for k in allowed if isinstance(obj.get(k),(str,int,float,bool,type(None)))}
            public['source']=meta; public['identity_verified']=identity
            if not identity: public['error']='identity_mismatch_or_missing_fields'
            return c['id'],public
        except Exception as exc: return c['id'],{'source_url':url,'retrieved_at':now(),'error':str(exc),'identity_verified':False}
    first=detail(candidates[0]); details[first[0]]=first[1]
    if first[1].get('identity_verified'):
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
            for cid,record in pool.map(detail,candidates[1:]): details[cid]=record
    else:
        manifest['notes'].append('DivulgaCand first probe failed; remaining endpoints not requested. Bulk TSE sources remain available.')
    write(OUT/'divulgacand-checks.json',details)
    history_by=collections.defaultdict(list); social_by=collections.defaultdict(list)
    for r in history: history_by[r['SQ_CANDIDATO_ATUAL']].append(r)
    for r in social: social_by[r['SQ_CANDIDATO']].append(r)
    targets=[]
    for c in candidates:
        links=[]; invalid=[]
        for r in social_by[c['id']]:
            value=social_url(r.get('DS_URL'))
            if value: links.append({'url':value,'declared_url':r['DS_URL'],'source':SOCIAL,'source_csv_record':r['_csv_record'],'verification':'candidate_declared_to_tse_not_individual_http_check'})
            else: invalid.append({'declared_url':r.get('DS_URL'),'source_csv_record':r['_csv_record'],'reason':'invalid_or_unsupported_http_url'})
        links=list({r['url']:r for r in links}.values())
        targets.append({'id':c['id'],'name':c['name'],'full_name':c['full_name'],'party':c['party'],'number':c['number'],'tse_url':c['tse_url'],'links':links,'invalid_declared_urls':invalid,'history_rows':len(history_by[c['id']]),'camara_match':matches.get(c['id']),'photo':photos.get(c['id']),'editorial_status':'not_reviewed'})
    write(OUT/'research-targets.json',targets)
    manifest['coverage']={'social_candidates':sum(bool(social_by[c]) for c in ids),'history_candidates':sum(bool(history_by[c]) for c in ids),'photo_candidates':len(photos),'camara_exact_matches':len(matches),'divulgacand_checked':len(details),'divulgacand_identity_verified':sum(d.get('identity_verified',False) for d in details.values()),'editorially_reviewed':0}
    changed=[p for p,d in protected.items() if not Path(p).is_file() or sha(Path(p).read_bytes())!=d]
    assert not changed,changed
    write(DOC/'isolation.json',{'baseline':BASELINE,'protected_file_count':len(protected),'changed':changed,'protected_sha256':protected})
    manifest['completed_at']=now(); write(manifest_path,manifest)
    print(json.dumps(manifest['coverage'],ensure_ascii=False,indent=2))

if __name__=='__main__': collect()

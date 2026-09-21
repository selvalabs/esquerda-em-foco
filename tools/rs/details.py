"""Public-only, bounded source reconciliation. Never export private registration fields."""
from __future__ import annotations
import collections, concurrent.futures, csv, hashlib, io, json, re, tempfile, time, unicodedata, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from bs4 import BeautifulSoup

D=Path('data/rs'); A=Path('docs/rs'); A.mkdir(parents=True,exist_ok=True)
def save(path,obj): path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def load(name,default): return json.loads((D/name).read_text()) if (D/name).exists() else default
def get(url,timeout=18):
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 EsquerdaEmFoco public-data-audit','Accept':'*/*'})
    with urllib.request.urlopen(req,timeout=timeout) as r: return r.read(30_000_000)
def norm(x): return ''.join(c for c in unicodedata.normalize('NFD',str(x).casefold()) if unicodedata.category(c)!='Mn')
def clean(x): return '' if str(x or '').strip() in ('','#NE','#NULO','-1','-3') else str(x).strip()
records=load('candidates-official.json',[]); ids={r['SQ_CANDIDATO'] for r in records}
audit={'checked_at':datetime.now(timezone.utc).isoformat(),'errors':[],'sources':[]}
profiles=load('profiles-official.json',{})

def profile(r):
    cid=r['SQ_CANDIDATO']; url=f'https://divulgacandcontas.tse.jus.br/divulga/rest/v1/candidatura/buscar/2026/RS/20322002026/candidato/{cid}'
    try:
        raw=get(url); data=json.loads(raw)
        if str(data.get('id')) != cid: raise ValueError('Candidate ID mismatch')
        allowed=['id','nomeUrna','numero','nomeCompleto','descricaoSituacao','descricaoTotalizacao','ocupacao','cargo','partido','eleicao','sites','eleicoesAnteriores','st_REELEICAO','candidatoApto','isCandidatoInapto','descricaoSituacaoCandidato']
        return cid,{'data':{k:data[k] for k in allowed if k in data},'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':audit['checked_at']}
    except Exception as exc: return cid,{'url':url,'error':str(exc),'checked_at':audit['checked_at']}
missing=[r for r in records if not profiles.get(r['SQ_CANDIDATO'],{}).get('data')]
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    for cid,result in pool.map(profile,missing): profiles[cid]=result
save(D/'profiles-official.json',profiles)

history=collections.defaultdict(dict)
for r in load('history-official.json',[]):
    cid=r.get('SQ_CANDIDATO_ATUAL'); year=int(r['ANO_ELEICAO'])
    if cid not in ids or year>=2026: continue
    key=(year,r['SQ_CANDIDATO'],int(r.get('NR_TURNO') or 1))
    history[cid][key]={'year':year,'round':key[2],'candidate_id':r['SQ_CANDIDATO'],'election_id':r.get('CD_ELEICAO'),'office':r.get('DS_CARGO'),'place':r.get('NM_UE'),'uf':r.get('SG_UF'),'party':r.get('SG_PARTIDO'),'result':clean(r.get('DS_SIT_TOT_TURNO')),'votes':None,'source':'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'}
for r in records:
    cid=r['SQ_CANDIDATO']; p=profiles.get(cid,{}).get('data',{})
    for h in p.get('eleicoesAnteriores',[]):
        year=int(h.get('ano') or h.get('anoEleicao') or 2026)
        if year>=2026: continue
        hid=str(h.get('id') or h.get('sqCandidato') or '')
        existing=[k for k in history[cid] if k[0]==year and k[1]==hid]
        # REST shape is deliberately audited; do not infer an identity without its ID.
        if not hid: continue
        if existing:
            for key in existing:
                if h.get('txLink'): history[cid][key]['profile_url']=h['txLink']
        else:
            cargo=h.get('cargo',{})
            if isinstance(cargo,dict): cargo=cargo.get('nome') or cargo.get('descricao')
            history[cid][(year,hid,1)]={'year':year,'round':1,'candidate_id':hid,'election_id':h.get('idEleicao'),'office':cargo or h.get('nomeCargo') or h.get('dsCargo'),'place':h.get('local') or h.get('nomeUe') or h.get('nmUe'),'uf':h.get('sgUf') or 'RS','party':h.get('siglaPartido') or h.get('sgPartido'),'result':h.get('situacaoTotalizacao') or h.get('descricaoTotalizacao') or h.get('situacao'),'votes':None,'profile_url':h.get('txLink'),'source':profiles[cid]['url']}
    history[cid][(2026,cid,1)]={'year':2026,'round':1,'candidate_id':cid,'office':'DEPUTADO FEDERAL','place':'RIO GRANDE DO SUL','uf':'RS','party':r['SG_PARTIDO'],'result':'Registro de candidatura; eleição ainda não realizada','votes':None,'source':'https://dadosabertos.tse.jus.br/dataset/candidatos-2026'}

votes=load('votes-official.json',{})
# Only dated past-election records are reconciled; no votes or projections for 2026.
for year in (2024,2022):
    if str(year) in votes: continue
    targets={h['candidate_id'] for hs in history.values() for h in hs.values() if h['year']==year}
    if not targets: continue
    dataset=f'https://dadosabertos.tse.jus.br/dataset/resultados-{year}'
    try:
        page=BeautifulSoup(get(dataset),'html.parser')
        links=[a['href'] for a in page.select('a[href]') if 'votacao_candidato_munzona' in a['href'] and str(year) in a['href'] and a['href'].endswith('.zip')]
        if not links: raise ValueError('Nominal-vote archive link not found on official dataset page')
        url=links[0]; start=time.monotonic(); digest=hashlib.sha256(); count=0
        with tempfile.TemporaryFile() as f:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 public-data-audit'}),timeout=30) as response:
                while True:
                    chunk=response.read(1024*1024)
                    if not chunk: break
                    count+=len(chunk); digest.update(chunk); f.write(chunk)
                    if count>700_000_000 or time.monotonic()-start>180: raise TimeoutError('Archive exceeded bounded transfer budget')
            f.seek(0); archive=zipfile.ZipFile(f); names=[n for n in archive.namelist() if n.upper().endswith('_RS.CSV')]
            if len(names)!=1: raise ValueError('Expected unique RS voting CSV')
            sums=collections.defaultdict(int); lines=collections.Counter(); sample=None
            with archive.open(names[0]) as raw:
                text=io.TextIOWrapper(raw,encoding='utf-8-sig' if raw.peek(3)[:3]==b'\xef\xbb\xbf' else 'latin-1',newline='')
                for row in csv.DictReader(text,delimiter=';'):
                    if row.get('SQ_CANDIDATO') not in targets or row.get('SG_UF')!='RS': continue
                    key=row['SQ_CANDIDATO']+':'+row['NR_TURNO']
                    amount=row.get('QT_VOTOS_NOMINAIS')
                    if amount is None: raise ValueError('Nominal-vote column missing')
                    sums[key]+=int(amount); lines[key]+=1
                    if sample is None: sample={k:row[k] for k in row if k in ('SQ_CANDIDATO','NR_TURNO','CD_CARGO','QT_VOTOS_NOMINAIS','DT_GERACAO','HH_GERACAO')}
            votes[str(year)]={'source_url':url,'dataset':dataset,'sha256':digest.hexdigest(),'bytes':count,'member':names[0],'totals':dict(sums),'rows_per_total':dict(lines),'sample':sample,'checked_at':audit['checked_at']}
            save(D/'votes-official.json',votes)
    except Exception as exc: audit['errors'].append({'stage':'votes','year':year,'error':str(exc)})
for hs in history.values():
    for h in hs.values():
        v=votes.get(str(h['year']),{}); key=h['candidate_id']+':'+str(h['round'])
        if key in v.get('totals',{}): h['votes']=v['totals'][key]; h['votes_source']=v['source_url']
normalized={cid:sorted(hs.values(),key=lambda h:(h['year'],h['round'],h['candidate_id'])) for cid,hs in history.items()}
save(D/'history-normalized.json',normalized)

# Current mandate confirmation uses institutional HTML and exact civil-name matching.
# A static public deputy directory is tried when the live API is unavailable.
known=[73486,220553,220554,204407]
try:
    raw=get('https://dadosabertos.camara.leg.br/arquivos/deputados/json/deputados.json',12)
    directory=json.loads(raw)
    directory=directory.get('dados',directory) if isinstance(directory,dict) else directory
    names={norm(r['NM_CANDIDATO']) for r in records}|{norm(r['NM_URNA_CANDIDATO']) for r in records}
    for dep in directory:
        if any(norm(dep.get(k,'')) in names for k in ('nome','nomeCivil','nomeEleitoral')):
            known.append(int(dep['id']))
    audit['directory_columns']=list(directory[0]) if directory else []
except Exception as exc: audit['errors'].append({'stage':'camara_directory','error':str(exc)})

def institution(did):
    url=f'https://www.camara.leg.br/deputados/{did}'
    try:
        raw=get(url,15); soup=BeautifulSoup(raw,'html.parser'); text=soup.get_text(' ',strip=True)
        civil=re.search(r'Nome Civil:\s*(.*?)\s*Partido:',text)
        status=re.search(r'(titular|suplente)\s+(em exercício|fora de exercício|não em exercício|licenciado)[^\d]*2023\s*-\s*2027',text,re.I)
        return {'id':did,'url':url,'civil_name':civil[1].strip() if civil else '', 'status':status[0] if status else '', 'sha256':hashlib.sha256(raw).hexdigest(),'checked_at':audit['checked_at'],'title':soup.title.get_text(' ',strip=True) if soup.title else ''}
    except Exception as exc: return {'id':did,'url':url,'error':str(exc)}
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool: institutions=list(pool.map(institution,sorted(set(known))))
existing=load('offices-verified.json',{})
for c in records:
    matches=[x for x in institutions if norm(x.get('civil_name'))==norm(c['NM_CANDIDATO']) and re.match(r'^(titular|suplente) em exercício',x.get('status',''),re.I)]
    if len(matches)==1:
        x=matches[0]; existing[c['SQ_CANDIDATO']]={'label':'Deputado(a) federal','source':x['url'],'detail':x['status'],'checked_at':x['checked_at']}
save(D/'offices-verified.json',existing)
audit['institutional_profiles']=institutions
audit['profile_count']=len(profiles); audit['profiles_read']=sum('data' in x for x in profiles.values()); audit['history_records']=sum(len(v) for v in normalized.values()); audit['histories_with_previous']=sum(any(h['year']<2026 for h in v) for v in normalized.values()); audit['current_offices_confirmed']=len(existing); audit['vote_years']=list(votes)
audit['profile_errors']=[{'id':cid,**p} for cid,p in profiles.items() if 'error' in p]
save(A/'reconciliation.json',audit)
print(json.dumps({k:v for k,v in audit.items() if k not in ('institutional_profiles','profile_errors')},ensure_ascii=False,indent=2))

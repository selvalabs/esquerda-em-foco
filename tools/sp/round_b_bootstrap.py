"""Bootstrap público do Round B de SP: redes declaradas, histórico TSE e Câmara atual.
Não atribui pautas. Não exporta campos pessoais desnecessários.
"""
from __future__ import annotations
import csv, hashlib, io, json, time, unicodedata, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/sp'
DOCS=ROOT/'docs/sp'
SOCIAL_URL='https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip'
HISTORY_URL='https://cdn.tse.jus.br/estatistica/sead/odsele/historico_candidatura/historico_candidatura_2026.zip'
CAMARA_URL='https://dadosabertos.camara.leg.br/api/v2/deputados?siglaUf=SP&itens=100&ordem=ASC&ordenarPor=nome'

def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def get(url,timeout=120):
    err=None
    for i in range(3):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'EsquerdaEmFoco-SP-RoundB/1.0 public-data-research','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read(), {'url':url,'retrieved_at':now(),'status':getattr(r,'status',None),'etag':r.headers.get('ETag'),'last_modified':r.headers.get('Last-Modified')}
        except Exception as exc:
            err=exc; time.sleep(2*(i+1))
    raise RuntimeError(f'{url}: {err}')
def rows_from_zip(raw,suffix):
    z=zipfile.ZipFile(io.BytesIO(raw))
    names=[n for n in z.namelist() if n.upper().endswith(suffix)]
    if not names:
        names=[n for n in z.namelist() if n.upper().endswith('_BRASIL.CSV')]
    if not names: raise ValueError(f'CSV ausente para {suffix}')
    out=[]; member_meta=[]
    for name in names:
        b=z.read(name)
        try: text=b.decode('utf-8-sig'); enc='utf-8-sig'
        except UnicodeDecodeError: text=b.decode('latin-1'); enc='latin-1'
        rs=list(csv.DictReader(io.StringIO(text),delimiter=';'))
        out.extend(rs)
        member_meta.append({'member':name,'sha256':sha(b),'records':len(rs),'encoding':enc})
    return out,member_meta
def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '')) if not unicodedata.combining(c)).casefold().strip()

base=json.loads((DATA/'normalized.json').read_text(encoding='utf-8'))
candidates=base['candidates']; ids={c['id'] for c in candidates}
if len(ids)!=234: raise SystemExit(f'Esperados 234 IDs; encontrados {len(ids)}')
manifest={'stage':'round_b_bootstrap','started_at':now(),'candidate_count':len(ids),'sources':[],'errors':[]}

# Redes/URLs declaradas ao TSE
try:
    raw,meta=get(SOCIAL_URL); rows,members=rows_from_zip(raw,'_SP.CSV')
    keep=[]
    by=defaultdict(list)
    for r in rows:
        cid=r.get('SQ_CANDIDATO')
        if cid not in ids: continue
        item={k:r.get(k,'') for k in ['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO']}
        keep.append(item); by[cid].append(item)
    save(DATA/'round-b-social-official.json',keep)
    meta.update({'sha256':sha(raw),'members':members,'selected_rows':len(keep)})
    manifest['sources'].append(meta)
except Exception as exc:
    by=defaultdict(list);manifest['errors'].append({'stage':'social','error':str(exc)})

# Histórico de candidaturas vinculado pelo SQ_CANDIDATO_ATUAL
try:
    raw,meta=get(HISTORY_URL); rows,members=rows_from_zip(raw,'_SP.CSV')
    headers=list(rows[0]) if rows else []
    allowed=[k for k in headers if not any(x in k.upper() for x in ['CPF','TITULO_ELEITORAL','CNPJ','EMAIL','TELEFONE','DT_NASCIMENTO','DATA_NASCIMENTO','ENDERECO','COR_RACA','GENERO','SEXO','ESTADO_CIVIL'])]
    selected=[]
    hist_by=defaultdict(list)
    for r in rows:
        current=r.get('SQ_CANDIDATO_ATUAL')
        if current not in ids: continue
        item={k:r.get(k,'') for k in allowed}
        selected.append(item); hist_by[current].append(item)
    save(DATA/'round-b-history-official.json',selected)
    save(DOCS/'sp-history-schema.json',{'headers':headers,'allowed':allowed,'selected_rows':len(selected)})
    meta.update({'sha256':sha(raw),'members':members,'selected_rows':len(selected)})
    manifest['sources'].append(meta)
except Exception as exc:
    hist_by=defaultdict(list);manifest['errors'].append({'stage':'history','error':str(exc)})

# Deputados federais em exercício / cadastro atual da Câmara: somente correspondência exata normalizada
camara_by={}
try:
    raw,meta=get(CAMARA_URL,60); payload=json.loads(raw); listing=payload.get('dados',[])
    public=[]
    for d in listing:
        item={'id':d.get('id'),'nome':d.get('nome'),'siglaPartido':d.get('siglaPartido'),'siglaUf':d.get('siglaUf'),'uri':d.get('uri'),'urlFoto':d.get('urlFoto')}
        public.append(item)
    save(DATA/'round-b-camara-sp.json',public)
    names=defaultdict(list)
    for d in public:
        names[fold(d.get('nome'))].append(d)
    for c in candidates:
        keys={fold(c.get('name')),fold(c.get('official_name')),fold(c.get('full_name'))}
        hits=[]
        for k in keys: hits.extend(names.get(k,[]))
        uniq={h['id']:h for h in hits if h.get('id')}
        if len(uniq)==1: camara_by[c['id']]=next(iter(uniq.values()))
    meta.update({'sha256':sha(raw),'records':len(public),'exact_candidate_matches':len(camara_by)})
    manifest['sources'].append(meta)
except Exception as exc:
    manifest['errors'].append({'stage':'camara','error':str(exc)})

queue=[]
for c in candidates:
    h=hist_by.get(c['id'],[])
    years=sorted({int(r['ANO_ELEICAO']) for r in h if str(r.get('ANO_ELEICAO','')).isdigit() and int(r['ANO_ELEICAO'])<2026})
    urls=[r.get('DS_URL') for r in by.get(c['id'],[]) if r.get('DS_URL')]
    queue.append({
      'candidate_id':c['id'],'name':c['name'],'full_name':c['full_name'],'number':c['number'],'party':c['party'],
      'electoral_status':c['status'],'tse_url':c['tse_url'],'declared_urls':urls,
      'historical_election_years':years,'historical_rows':len(h),
      'current_camara_exact_match':camara_by.get(c['id']),
      'research_state':'pending_individual_review'
    })
save(DATA/'round-b-research-queue.json',queue)
manifest['finished_at']=now()
manifest['queue_count']=len(queue)
manifest['with_declared_urls']=sum(bool(x['declared_urls']) for x in queue)
manifest['with_history']=sum(bool(x['historical_rows']) for x in queue)
manifest['current_camara_exact_matches']=len(camara_by)
save(DOCS/'ROUND-B-BOOTSTRAP.json',manifest)
print(json.dumps({k:v for k,v in manifest.items() if k not in ['sources']},ensure_ascii=False,indent=2))

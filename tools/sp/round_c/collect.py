"""Collect only Round C additions. Frozen A/B inputs are never rewritten.
Network work is explicit; build.py must remain offline and deterministic.
"""
from __future__ import annotations
import concurrent.futures, csv, hashlib, io, json, re, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'data/sp/round-c'; DOC=ROOT/'docs/sp/round-c'

def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
def now(): return datetime.now(timezone.utc).isoformat()
def sha(b): return hashlib.sha256(b).hexdigest()
def fetch(url, timeout=35):
    last=None
    for attempt in range(2):
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0 (EsquerdaEmFoco public-source-check)','Accept':'*/*'})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                body=r.read(80_000_001)
                if len(body)>80_000_000: raise ValueError('Response exceeds bounded size')
                return body,{'url':url,'final_url':r.geturl(),'http_status':r.status,'retrieved_at':now(),'sha256':sha(body),'bytes':len(body),'content_type':r.headers.get('Content-Type')}
        except Exception as exc:
            last=exc
            if attempt==0:time.sleep(1)
    raise RuntimeError(str(last))
def csv_zip(url):
    raw, meta=fetch(url,90)
    z=zipfile.ZipFile(io.BytesIO(raw)); names=[n for n in z.namelist() if n.upper().endswith('_SP.CSV')]
    assert len(names)==1
    b=z.read(names[0])
    try:text=b.decode('utf-8-sig')
    except UnicodeDecodeError:text=b.decode('latin-1')
    rows=[]
    for ordinal,row in enumerate(csv.DictReader(io.StringIO(text),delimiter=';'),2):
        rows.append({**row,'_source_record':ordinal})
    meta.update(member=names[0],member_sha256=sha(b),generated_at_values=sorted({r.get('DT_GERACAO','')+' '+r.get('HH_GERACAO','') for r in rows}))
    return rows,meta

def run():
    if (OUT/'collection.json').exists():
        print('Using frozen Round C collection');return
    canonical=json.loads((ROOT/'config/party-scope-2026.json').read_text())['parties']
    byparty={p.upper():p for p in canonical}
    allrows=json.loads((ROOT/'data/sp/all-candidates-official.json').read_text())
    prior=json.loads((ROOT/'data/sp/normalized.json').read_text())
    old={c['id'] for c in prior['candidates']}
    selected=[r for r in allrows if r['SG_PARTIDO'].upper() in byparty]
    extras=[r for r in selected if r['SQ_CANDIDATO'] not in old]
    ids={r['SQ_CANDIDATO'] for r in extras}
    assert len(old)==234 and len(selected)==249 and len(ids)==15
    OUT.mkdir(parents=True,exist_ok=True); DOC.mkdir(parents=True,exist_ok=True)
    manifest={'started_at':now(),'basis':'Frozen A census + canonical scope from main; extra status/social/photo observations dated separately','canonical_parties':canonical,'round_b_records':234,'product_records':249,'extra_records':15,'sources':{},'limitations':['No individual thematic research has been performed for the 15 scope additions.','HTTP success does not establish editorial correctness.']}
    comp_url='https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand_complementar/consulta_cand_complementar_2026.zip'
    comps,meta=csv_zip(comp_url); manifest['sources']['extra_status']=meta
    allowed=['SQ_CANDIDATO','DT_GERACAO','HH_GERACAO','ANO_ELEICAO','CD_ELEICAO','CD_SITUACAO_JULGAMENTO','DS_SITUACAO_JULGAMENTO','ST_SUBSTITUIDO','SQ_SUBSTITUIDO','ST_CANDIDATO_INSERIDO_URNA','_source_record']
    status=[{k:r[k] for k in allowed if k in r} for r in comps if r['SQ_CANDIDATO'] in ids]
    assert len(status)==len(ids) and {x['SQ_CANDIDATO'] for x in status}==ids
    dump(OUT/'extra-status.json',status)
    social_url='https://cdn.tse.jus.br/estatistica/sead/odsele/consulta_cand/rede_social_candidato_2026.zip'
    socials,meta=csv_zip(social_url);manifest['sources']['extra_socials']=meta
    allowed=['SQ_CANDIDATO','DS_URL','NR_ORDEM','DT_GERACAO','HH_GERACAO','_source_record']
    dump(OUT/'extra-socials.json',[{k:r[k] for k in allowed if k in r} for r in socials if r['SQ_CANDIDATO'] in ids])
    url='https://cdn.tse.jus.br/estatistica/sead/eleicoes/eleicoes2026/fotos/foto_cand2026_SP_div.zip'
    b,meta=fetch(url,90);manifest['sources']['extra_photos']=meta
    z=zipfile.ZipFile(io.BytesIO(b));photos={}
    for name in z.namelist():
        m=re.search(r'(2500\d{8})',name)
        if not m or m[1] not in ids or not name.lower().endswith(('.jpg','.jpeg','.png')): continue
        cid=m[1];dest=OUT/'photos'/(cid+Path(name).suffix.lower());dest.parent.mkdir(exist_ok=True)
        raw=z.read(name);dest.write_bytes(raw)
        photos[cid]={'path':str(dest.relative_to(ROOT)),'source_url':url,'source_member':name,'sha256':sha(raw)}
    assert set(photos)==ids
    dump(OUT/'extra-photos.json',photos)
    url='https://servicodados.ibge.gov.br/api/v3/malhas/estados/35?formato=image/svg&qualidade=minima'
    b,meta=fetch(url);assert b'<svg' in b and b'<script' not in b
    (OUT/'sp-ibge.svg').write_bytes(b);manifest['sources']['map']=meta
    dump(OUT/'extra-candidates.json',extras)
    manifest['completed_at']=now();dump(OUT/'collection.json',manifest)
    sources={s['url'] for r in json.loads((ROOT/'data/sp/research/records.json').read_text())['records'] for s in r['sources']}
    def check(url):
        try:
            _,m=fetch(url,18);return {**m,'result':'http_accessible_not_editorial_verification'}
        except Exception as exc:return {'url':url,'checked_at':now(),'result':'unavailable_in_this_check','error':str(exc)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:checks=list(pool.map(check,sorted(sources)))
    dump(DOC/'source-link-check.json',{'checked_at':now(),'scope':'75 upstream editorial URLs only; not all declared social profiles','count':len(checks),'accessible':sum(x['result'].startswith('http_accessible') for x in checks),'records':checks})
    print(json.dumps({'product':len(selected),'new':len(extras),'photo_count':len(photos),'editorial_url_checks':len(checks)},ensure_ascii=False))
if __name__=='__main__':run()

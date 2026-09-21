"""Audit and consolidate SP federal Round B research.
Deterministic: validates candidate/source/claim/theme referential integrity and writes coverage reports.
It never derives themes from free text, party, profession or biography.
"""
from __future__ import annotations
import collections, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'data/sp'
RESEARCH=DATA/'research'
DOCS=ROOT/'docs/sp'
TAX=ROOT/'data/shared/pautas-taxonomy-v1.json'

COVERAGE={
 'documentacao_insuficiente','material_eleitoral_2026','manifestacoes_publicas_2026',
 'atuacao_legislativa_2026','historico','sem_data','misto'
}
DIRECTIONS={'apoio_ou_prioridade','oposicao','proposta','atuacao','descricao_sem_direcao'}
PERIODS={'2026','historico','sem_data'}
EVIDENCE={'campanha','declaracao_direta','legislativo','institucional','partidaria_individual','imprensa_com_declaracao_identificada'}

def load(path): return json.loads(path.read_text(encoding='utf-8'))
def dump(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()

queue=load(DATA/'round-b-research-queue.json')
taxonomy=load(TAX)
queue_by={x['candidate_id']:x for x in queue}
topics={x['id']:x for x in taxonomy['topics']}
batch_paths=sorted(RESEARCH.glob('batch-*.json'))
problems=[]
if len(queue)!=234 or len(queue_by)!=234:
    problems.append({'kind':'queue_cardinality','count':len(queue),'unique':len(queue_by)})
if len(batch_paths)!=5:
    problems.append({'kind':'batch_count','count':len(batch_paths),'expected':5})

records=[]
batch_summary=[]
for path in batch_paths:
    payload=load(path)
    rows=payload.get('records',[])
    if payload.get('candidate_count')!=len(rows):
        problems.append({'kind':'batch_declared_count','path':str(path),'declared':payload.get('candidate_count'),'actual':len(rows)})
    records.extend(rows)
    batch_summary.append({'path':str(path.relative_to(ROOT)),'sha256':sha(path),'count':len(rows),'declared_scope':payload.get('scope')})

ids=[r.get('candidate_id') for r in records]
dups=[k for k,v in collections.Counter(ids).items() if v>1]
if dups: problems.append({'kind':'duplicate_candidate_ids','ids':sorted(dups)})
missing=sorted(set(queue_by)-set(ids))
extra=sorted(set(ids)-set(queue_by))
if missing: problems.append({'kind':'missing_candidates','ids':missing})
if extra: problems.append({'kind':'unknown_candidates','ids':extra})

all_claim_ids=set()
all_source_ids=set()
source_urls=[]
coverage=collections.Counter()
claims_period=collections.Counter()
claims_evidence=collections.Counter()
claims_direction=collections.Counter()
theme_period=collections.defaultdict(lambda: collections.Counter())
party_reviewed=collections.Counter()
party_any_claim=collections.Counter()
party_current_claim=collections.Counter()
candidate_theme_2026=collections.defaultdict(lambda: collections.defaultdict(list))
with_any=set();with_current=set()

for r in records:
    cid=r.get('candidate_id')
    q=queue_by.get(cid)
    if not q: continue
    identity=r.get('identity') or {}
    for key in ('name','party','number'):
        expected=q[key]
        actual=identity.get(key)
        if str(actual)!=str(expected):
            problems.append({'kind':'identity_mismatch','candidate_id':cid,'field':key,'expected':expected,'actual':actual})
    cov=r.get('coverage')
    coverage[cov]+=1
    party_reviewed[q['party']]+=1
    if cov not in COVERAGE:
        problems.append({'kind':'invalid_coverage','candidate_id':cid,'value':cov})
    sources=r.get('sources',[])
    claims=r.get('claims',[])
    if cov=='documentacao_insuficiente' and claims:
        problems.append({'kind':'claim_on_insufficient_record','candidate_id':cid})
    local_sources={}
    for s in sources:
        sid=s.get('source_id')
        if not sid or sid in local_sources:
            problems.append({'kind':'duplicate_or_missing_source_id','candidate_id':cid,'source_id':sid})
            continue
        local_sources[sid]=s
        if sid in all_source_ids:
            problems.append({'kind':'global_duplicate_source_id','candidate_id':cid,'source_id':sid})
        all_source_ids.add(sid)
        url=s.get('url')
        if not isinstance(url,str) or not url.startswith(('http://','https://')):
            problems.append({'kind':'invalid_source_url','candidate_id':cid,'source_id':sid,'url':url})
        else:
            source_urls.append(url)
        for field in ('title','publisher','type','consulted_at'):
            if not s.get(field):
                problems.append({'kind':'missing_source_field','candidate_id':cid,'source_id':sid,'field':field})
    if claims:
        with_any.add(cid);party_any_claim[q['party']]+=1
    for c in claims:
        clid=c.get('claim_id')
        if not clid or clid in all_claim_ids:
            problems.append({'kind':'duplicate_or_missing_claim_id','candidate_id':cid,'claim_id':clid})
        all_claim_ids.add(clid)
        if not c.get('text'):
            problems.append({'kind':'missing_claim_text','candidate_id':cid,'claim_id':clid})
        period=c.get('period');direction=c.get('direction');etype=c.get('evidence_type')
        claims_period[period]+=1;claims_direction[direction]+=1;claims_evidence[etype]+=1
        if period not in PERIODS: problems.append({'kind':'invalid_period','candidate_id':cid,'claim_id':clid,'value':period})
        if direction not in DIRECTIONS: problems.append({'kind':'invalid_direction','candidate_id':cid,'claim_id':clid,'value':direction})
        if etype not in EVIDENCE: problems.append({'kind':'invalid_evidence_type','candidate_id':cid,'claim_id':clid,'value':etype})
        refs=c.get('source_ids') or []
        if not refs:
            problems.append({'kind':'claim_without_source','candidate_id':cid,'claim_id':clid})
        for ref in refs:
            if ref not in local_sources:
                problems.append({'kind':'missing_source_reference','candidate_id':cid,'claim_id':clid,'source_id':ref})
        theme_ids=c.get('theme_ids') or []
        if not theme_ids:
            problems.append({'kind':'claim_without_theme','candidate_id':cid,'claim_id':clid})
        for tid in theme_ids:
            if tid not in topics:
                problems.append({'kind':'unknown_theme','candidate_id':cid,'claim_id':clid,'theme_id':tid})
                continue
            theme_period[tid][period]+=1
            if period=='2026':
                candidate_theme_2026[cid][tid].append(clid)
        if period=='2026': with_current.add(cid)

for cid in with_current:
    party_current_claim[queue_by[cid]['party']]+=1

consolidated=[]
for r in sorted(records,key=lambda x:x['candidate_id']):
    q=queue_by[r['candidate_id']]
    item=dict(r)
    item['electoral_status']=q['electoral_status']
    item['tse_url']=q['tse_url']
    item['declared_urls']=q.get('declared_urls',[])
    item['historical_election_years']=q.get('historical_election_years',[])
    item['current_camara_exact_match']=q.get('current_camara_exact_match')
    consolidated.append(item)

current_index=[]
record_by={r['candidate_id']:r for r in consolidated}
for cid in sorted(candidate_theme_2026):
    q=queue_by[cid]
    rec=record_by[cid]
    claim_by={c['claim_id']:c for c in rec['claims']}
    source_by={s['source_id']:s for s in rec['sources']}
    themes=[]
    for tid,claim_ids in sorted(candidate_theme_2026[cid].items()):
        claim_rows=[claim_by[x] for x in claim_ids]
        src_ids=sorted({sid for c in claim_rows for sid in c['source_ids']})
        themes.append({'theme_id':tid,'theme_label':topics[tid]['label'],'claim_ids':claim_ids,'source_ids':src_ids,'sources':[source_by[sid] for sid in src_ids]})
    current_index.append({'candidate_id':cid,'name':q['name'],'party':q['party'],'number':q['number'],'themes':themes})

audit={
 'schema_version':'1.0','stage':'round_b','reviewed_at':'2026-09-21',
 'gate':'PASS' if not problems and len(records)==234 and len(set(ids))==234 else 'BLOCKED',
 'population':234,'reviewed_candidates':len(records),'unique_candidates':len(set(ids)),
 'candidates_with_any_claim':len(with_any),
 'candidates_with_2026_claim':len(with_current),
 'candidates_with_only_noncurrent_claim':len(with_any-with_current),
 'candidates_with_insufficient_documentation':coverage['documentacao_insuficiente'],
 'claims_total':sum(claims_period.values()),
 'claims_by_period':dict(sorted(claims_period.items())),
 'claims_by_evidence_type':dict(sorted(claims_evidence.items())),
 'claims_by_direction':dict(sorted(claims_direction.items())),
 'coverage_states':dict(sorted(coverage.items())),
 'reviewed_by_party':dict(sorted(party_reviewed.items())),
 'with_any_claim_by_party':dict(sorted(party_any_claim.items())),
 'with_2026_claim_by_party':dict(sorted(party_current_claim.items())),
 'sources_total':len(all_source_ids),'distinct_source_urls':len(set(source_urls)),
 'current_candidate_theme_associations':sum(len(v) for v in candidate_theme_2026.values()),
 'themes':{
   tid:{'label':topics[tid]['label'],'claims_by_period':dict(sorted(theme_period[tid].items())),
        'current_candidates':sum(1 for cid in candidate_theme_2026 if tid in candidate_theme_2026[cid])}
   for tid in sorted(topics)
 },
 'taxonomy':{'path':str(TAX.relative_to(ROOT)),'sha256':sha(TAX),'topics':len(topics),'filters_implemented':False},
 'batches':batch_summary,
 'problems':problems,
 'caveats':[
   'Contagens são cobertura documental, não pontuação, ranking ou avaliação de candidaturas.',
   'Ausência de claim significa que não foi localizada evidência individual suficiente nesta revisão; não significa oposição ou ausência de posição.',
   'Somente claims com período 2026 entram no índice de evidências atuais; histórico e sem_data permanecem separados.',
   'Fontes de campanha registram declarações/propostas da candidatura; não comprovam implementação.',
   'Atuação legislativa registra ação documentada; não implica concordância com toda a família temática.',
   'Nenhum filtro de frontend foi ativado no Round B.'
 ]
}

dump(RESEARCH/'records.json',{'schema_version':'1.0','reviewed_at':'2026-09-21','candidate_count':len(consolidated),'records':consolidated})
dump(RESEARCH/'theme-evidence-2026.json',{'schema_version':'1.0','period':'2026','candidate_count':len(current_index),'filters_implemented':False,'records':current_index})
dump(DOCS/'ROUND-B-AUDIT.json',audit)

lines=[
 '# SP · Deputados federais · Round B','',
 f"**Gate editorial/documental: {audit['gate']}**",'',
 f"- População do Round A: **{audit['population']}**.",
 f"- Fichas revisadas: **{audit['reviewed_candidates']}**.",
 f"- Fichas com algum claim documentado: **{audit['candidates_with_any_claim']}**.",
 f"- Fichas com claim identificável em 2026: **{audit['candidates_with_2026_claim']}**.",
 f"- Fichas com somente evidência histórica/sem data: **{audit['candidates_with_only_noncurrent_claim']}**.",
 f"- Fichas com documentação insuficiente para síntese temática: **{audit['candidates_with_insufficient_documentation']}**.",
 f"- Claims: **{audit['claims_total']}**; fontes registradas: **{audit['sources_total']}** ({audit['distinct_source_urls']} URLs distintas).",'',
 '## Método','',
 'Cada claim precisa apontar para fonte(s), tema(s), período, direção e tipo de evidência. Não há atribuição por partido, profissão, nome de urna ou biografia. Material de campanha, atuação legislativa, histórico e conteúdo sem data permanecem distinguidos.','',
 '## Cobertura por partido','',
 '| Partido | Revisados | Com algum claim | Com claim de 2026 |','|---|---:|---:|---:|'
]
for p in sorted(party_reviewed):
    lines.append(f"| {p} | {party_reviewed[p]} | {party_any_claim[p]} | {party_current_claim[p]} |")
lines += ['','## Temporalidade','','| Período | Claims |','|---|---:|']
for p,n in sorted(claims_period.items()): lines.append(f"| {p} | {n} |")
lines += [
 '','## Interpretação correta','',
 'As frequências temáticas medem apenas o que foi documentado nesta revisão. Não são notas, rankings ou uma medida da importância que cada candidatura atribui ao tema. Uma ficha sem claim não é classificada como contrária ao tema.','',
 'O arquivo data/sp/research/theme-evidence-2026.json contém apenas associações sustentadas por claims de 2026. Ele é um índice documental para o próximo round; não está ligado ao frontend.','',
 '## Gate técnico','',
 f"- Problemas de integridade: **{len(problems)}**.",
 f"- Taxonomia: **{len(topics)} famílias**, filtros desligados.",
 f"- Batches: **{len(batch_paths)}**, total **{len(records)}** registros.",'',
 'Detalhes completos em docs/sp/ROUND-B-AUDIT.json. Registros consolidados em data/sp/research/records.json.',''
]
(DOCS/'ROUND-B.md').write_text('\n'.join(lines),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k not in ('themes','batches','caveats')},ensure_ascii=False,indent=2))
if audit['gate']!='PASS':
    raise SystemExit('Round B audit BLOCKED; inspect docs/sp/ROUND-B-AUDIT.json')

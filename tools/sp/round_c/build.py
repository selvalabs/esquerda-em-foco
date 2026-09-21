"""Offline SP Round C renderer. A/B and other states are immutable inputs.

Run from repository root: python tools/sp/round_c/build.py
Optional: EEFOCO_SITE_URL=https://example.org/ for SP canonical/OG URLs.
Only sp/, data/sp/round-c/product.json, docs/sp/round-c/build.json,
a bounded root navigation link and the two SP sitemap entries are written.
"""
from __future__ import annotations
import collections, csv, hashlib, html, json, os, re, shutil, unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT=Path(__file__).resolve().parents[3]
INPUT=ROOT/'data/sp'; C=INPUT/'round-c'; DOC=ROOT/'docs/sp/round-c'
DEST=ROOT/'sp/deputados-federais'; ASSETS=DEST/'assets'
DATE='2026-09-21'
SITE=os.environ.get('EEFOCO_SITE_URL','https://selvalabs.github.io/esquerda-em-foco/').rstrip('/')+'/'
TSE='https://dadosabertos.tse.jus.br/dataset/candidatos-2026'
ALIASES={'apostas-protecao-economica':'apostas-jogos','infraestrutura-desenvolvimento-regional':'infraestrutura-desenvolvimento','povos-indigenas-comunidades-tradicionais':'povos-indigenas-tradicionais'}
NAV_LINK='<!-- SP-C navigation:start --><a class="edition-sp-link" href="sp/deputados-federais/">SP · Federais</a><!-- SP-C navigation:end -->'

def load(path):return json.loads(path.read_text(encoding='utf-8'))
def dump(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def esc(value):return html.escape(str(value if value is not None else ''),quote=True)
def fold(value):return ''.join(x for x in unicodedata.normalize('NFD',str(value or '')) if not unicodedata.combining(x)).casefold()
def slug(value):return re.sub(r'[^a-z0-9]+','-',fold(value)).strip('-')
def title(value):
    s=str(value or '').strip()
    if not s.isupper():return s
    words=s.title().split()
    return ' '.join(w.lower() if i and w in {'Da','De','Do','Das','Dos','E'} else w for i,w in enumerate(words))
def safe_url(value):
    if not isinstance(value,str):return None
    s=value.strip()
    if s.startswith('@') or any(c.isspace() for c in s):return None
    if not re.match(r'^https?://',s,re.I):s='https://'+s
    p=urlsplit(s)
    if p.scheme.lower() not in {'http','https'} or not p.hostname or '.' not in p.hostname or p.username or p.password:return None
    return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path,p.query,p.fragment))
def link(url,label,cls=''):
    u=safe_url(url)
    return f'<a class="{esc(cls)}" href="{esc(u)}" target="_blank" rel="noopener noreferrer">{esc(label)} ↗</a>' if u else esc(label)
def human_date(value):
    s=str(value or '')[:10]
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',s):return '/'.join(reversed(s.split('-')))
    return s or 'sem data original'

def taxonomy():
    research=load(ROOT/'data/shared/pautas-taxonomy-v1.json')
    national=load(ROOT/'config/topics-v1.json')
    national_by={t['id']:t for t in national['topics']}
    result=[]
    for t in research['topics']:
        new=ALIASES.get(t['id'],t['id'])
        if new in national_by:
            result.append({**national_by[new],'source_topic_id':t['id'],'origin':'config/topics-v1.json'})
        else:
            assert new=='ciencia-tecnologia-inovacao','Unreviewed taxonomy extension'
            result.append({**t,'source_topic_id':t['id'],'origin':'Round B explicit documentary extension','includes':'Políticas explícitas de ciência, pesquisa, tecnologia e inovação.','excludes':'Profissão ou formação não geram associação.'})
    assert len(result)==30 and len({t['id'] for t in result})==30
    return sorted(result,key=lambda x:fold(x['label']))

def product():
    tech=load(INPUT/'round-b/normalized.json')
    prior={r['id']:r for r in tech['candidates']}
    editorial=load(INPUT/'research/records.json')
    reviews={r['candidate_id']:r for r in editorial['records']}
    idx=load(INPUT/'research/theme-evidence-2026.json')
    index={r['candidate_id']:r for r in idx['records']}
    parties=load(ROOT/'config/party-scope-2026.json')['parties']
    all_official=load(INPUT/'all-candidates-official.json')
    allowed={p.upper():p for p in parties}
    selected=[r for r in all_official if r['SG_PARTIDO'].upper() in allowed]
    extras={r['SQ_CANDIDATO']:r for r in load(C/'extra-candidates.json')}
    extra_status={r['SQ_CANDIDATO']:r for r in load(C/'extra-status.json')}
    extra_photos=load(C/'extra-photos.json')
    extra_social=collections.defaultdict(list)
    for s in load(C/'extra-socials.json'):extra_social[s['SQ_CANDIDATO']].append(s['DS_URL'])
    collected=load(C/'collection.json')
    checks=load(DOC/'source-link-check.json')
    link_checks={r['url']:r for r in checks['records']}
    topics=taxonomy();topic_by={t['id']:t for t in topics}
    assert len(selected)==249 and len(prior)==234 and len(extras)==15
    assert set(reviews)==set(prior) and set(index)<=set(reviews) and len(index)==42
    assert {r['SQ_CANDIDATO'] for r in selected}==set(prior)|set(extras)
    records=[]
    for raw in selected:
        cid=raw['SQ_CANDIDATO'];assert re.fullmatch(r'\d{12}',cid)
        t=prior.get(cid);r=reviews.get(cid,{'sources':[],'claims':[],'limitations':[]})
        sources={s['source_id']:dict(s) for s in r['sources']}
        for s in sources.values():
            check=link_checks.get(s['url'])
            if check:s['link_check']={k:v for k,v in check.items() if k in {'result','http_status','retrieved_at','checked_at'}}
        associations=[]
        for entry in index.get(cid,{}).get('themes',[]):
            old=entry['theme_id'];new=ALIASES.get(old,old);assert new in topic_by
            assert entry['claim_ids'] and entry['source_ids']
            associations.append({'id':new,'source_topic_id':old,'label':topic_by[new]['label'],'claim_ids':entry['claim_ids'],'source_ids':entry['source_ids']})
        associations.sort(key=lambda x:fold(x['label']))
        current=[];other=[]
        approved={a['source_topic_id']:set(a['claim_ids']) for a in associations}
        for original in r['claims']:
            claim=dict(original)
            claim['theme_ids']=[ALIASES.get(k,k) for k in original['theme_ids']]
            assert set(claim['theme_ids'])<=set(topic_by)
            assert all(s in sources for s in claim['source_ids'])
            if claim['period']=='2026':
                # Membership comes from B's canonical index, never from text matching.
                assert all(claim['claim_id'] in approved.get(k,set()) for k in original['theme_ids'])
                current.append(claim)
            else:
                assert claim['period'] in {'historico','sem_data'}
                other.append(claim)
        claims={x['claim_id']:x for x in current}
        assert all(set(a['claim_ids'])<=set(claims) for a in associations)
        for a in associations:
            assert set(a['source_ids'])=={s for k in a['claim_ids'] for s in claims[k]['source_ids']}
        if t:
            assert t['registration_election']['votes'] is None and t['registration_election']['result'] is None
            status=t['status'];status_date=t['complement_source_record']['generated_at'][:10]
            photo=t['photo'];history=t['history'];bio=t['biography'];bio_sources=t['editorial_sources']
            socials=t['socials']+t['sites'];role=t.get('current_office')
            history_state='snapshot_tse';identity_source=t['source_record']
        else:
            status=extra_status[cid]['DS_SITUACAO_JULGAMENTO'];status_date=extra_status[cid]['DT_GERACAO']
            photo=extra_photos[cid];history=[];bio=None;bio_sources=[];role=None;history_state='not_collected_for_scope_addition'
            socials=[{'url':u,'label':urlsplit(safe_url(u) or '').hostname or 'Canal declarado'} for u in extra_social[cid]]
            identity_source={'url':load(INPUT/'manifest.json')['sources'][0]['url'],'id':cid,'csv_record':raw['_source_record'],'member':'consulta_cand_2026_SP.csv','generated_at':raw['DT_GERACAO']+' '+raw['HH_GERACAO']}
        assert status and not status.startswith('#')
        if photo:
            p=(ROOT/photo['path']).resolve()
            assert p.is_relative_to(INPUT.resolve()) and digest(p)==photo['sha256']
            local_photo='assets/photos/'+cid+p.suffix.lower()
        else:local_photo=None
        channels=[];seen=set()
        for channel in socials:
            u=safe_url(channel.get('url'))
            if not u or u in seen:continue
            seen.add(u);channels.append({'label':channel.get('label') or urlsplit(u).hostname,'url':u})
        record={'id':cid,'name':title(raw['NM_URNA_CANDIDATO']),'official_name':raw['NM_URNA_CANDIDATO'],'full_name':title(raw['NM_CANDIDATO']),'number':raw['NR_CANDIDATO'],'party':allowed[raw['SG_PARTIDO'].upper()],'state':'SP','office_code':6,'election_year':2026,'status':status,'status_id':slug(status),'status_date':status_date,'registration_election':{'year':2026,'votes':None,'result':None},'tse_url':f'https://divulgacandcontas.tse.jus.br/divulga/#/candidato/2026/20322002026/SP/{cid}','identity_source':identity_source,'photo':local_photo,'photo_source':photo,'channels':channels,'channels_verification':'Declared to TSE; not all individually HTTP checked','biography':bio,'biography_sources':bio_sources if bio else [],'current_role_observation':role,'history':history,'history_state':history_state,'sources':list(sources.values()),'claims_2026':current,'claims_other':other,'themes_2026':associations,'research_state':'round_b_imported' if t else 'canonical_scope_addition_not_reviewed','research_date':DATE if t else None,'limitations':r.get('limitations',[])}
        assert all(h['year']<2026 for h in history)
        records.append(record)
    records.sort(key=lambda x:(fold(x['party']),fold(x['name']),x['id']))
    return {'schema_version':'sp-product-1.0','state':'SP','office_code':6,'election_year':2026,'as_of':DATE,'party_scope':parties,'taxonomy':topics,'canonical':SITE+'sp/deputados-federais/','records':records,'provenance':{'research_commit':'a2689717850d451b02e2ab8a3570d5acf204546c','main_integration_reference':'89092b6192f5b06acba3fcb1ac7adef1af99b266','topic_id_migration':ALIASES,'original_round_b_count':234,'scope_additions':15,'supplemental_collection':collected,'upstream_source_link_check':{'total':checks['count'],'accessible':checks['accessible'],'warning_count':checks['count']-checks['accessible'],'note':'HTTP availability only; not a new editorial review.'}}}

def render_source(source):
    url=source['url'];name=source.get('title',source.get('publisher','Fonte'))
    published=source.get('published_at') or source.get('publication_date')
    consulted=source.get('consulted_at') or source.get('read_at') or DATE
    date_text=('Publicação: '+human_date(published)+' · ') if published else 'Data original não informada · '
    warn=source.get('link_check',{}).get('result')=='unavailable_in_this_check'
    warning='<small class="source-warning">Esta URL não respondeu à checagem automática do Round C. A referência da revisão anterior foi preservada.</small>' if warn else ''
    return f'<div class="source">{link(url,name)}<small>{esc(source.get("publisher") or source.get("kind") or "Fonte da revisão")}. {esc(date_text)}Consulta editorial: {esc(human_date(consulted))}.</small>{("<small>Localizador: "+esc(source["locator"])+"</small>") if source.get("locator") else ""}{warning}</div>'

def render_claim(claim, sources, topic_by):
    kind={'campanha':'Material de campanha','declaracao_direta':'Declaração atribuída','legislativo':'Registro legislativo','institucional':'Registro institucional','partidaria_individual':'Página partidária individual','imprensa_com_declaracao_identificada':'Declaração em entrevista'}[claim['evidence_type']]
    direction={'proposta':'Proposta','apoio_ou_prioridade':'Posição/prioridade declarada','oposicao':'Oposição à medida descrita','atuacao':'Atuação documentada ou relatada','descricao_sem_direcao':'Descrição sem direção de apoio'}[claim['direction']]
    period={'2026':'Contexto de 2026','historico':'Registro histórico','sem_data':'Sem data original confirmada'}[claim['period']]
    return f'<section class="claim" id="afirmacao-{esc(claim["claim_id"])}" data-claim-id="{esc(claim["claim_id"])}" data-period="{claim["period"]}" data-direction="{esc(claim["direction"])}" data-topics="{esc(" ".join(claim["theme_ids"]))}"><p class="claim-meta">{esc(kind)} · {esc(period)}</p><p>{esc(claim["text"])}</p><div class="claim-topics">{esc(direction)}. Tema(s): {esc("; ".join(topic_by[x]["label"] for x in claim["theme_ids"]))}.</div>{"".join(render_source(sources[s]) for s in claim["source_ids"])}</section>'

def render_card(c, topic_by):
    cid=c['id'];current=c['claims_2026'];other=c['claims_other'];sources={s['source_id']:s for s in c['sources']}
    theme_ids=[a['id'] for a in c['themes_2026']]
    search=' '.join([c['name'],c['full_name'],c['number'],c['party']]+[a['label'] for a in c['themes_2026']]+[x['text'] for x in current])
    initials=''.join(w[0] for w in c['name'].split()[:2])
    photo=f'<img src="{esc(c["photo"])}" alt="Foto oficial de candidatura de {esc(c["name"])}" width="92" height="116" loading="lazy" decoding="async">' if c['photo'] else ''
    if current:
        summary=current[0]['text'];label='Documentação de 2026'
    elif c['research_state']=='canonical_scope_addition_not_reviewed':
        label='Cadastro incluído na atualização do recorte';summary='Este registro entrou pela ampliação do recorte partidário. A pesquisa individual de pautas ainda não foi realizada.'
    elif other:
        label='Documentação histórica ou sem data';summary='Há material de outros períodos ou sem data original confirmada. Ele pode ser consultado nesta ficha, mas não participa dos filtros de 2026.'
    else:
        label='Sem síntese temática nesta revisão';summary='A revisão do Round B não registrou evidência individual suficiente para apresentar pautas. Isso não significa ausência de propostas nem oposição a qualquer tema.'
    tags=''.join(f'<button type="button" class="topic-chip" data-show-evidence="{esc(a["id"])}" aria-controls="evidencias-{cid}" aria-expanded="false" aria-label="Ver por que {esc(c["name"])} aparece em {esc(a["label"])}">{esc(a["label"])}</button>' for a in c['themes_2026'])
    current_html=''
    if current:
        # Explicit singular/plural avoids mechanically generated truncated words.
        current_html=f'<details class="card-details current-evidence" id="evidencias-{cid}"><summary>Ver {len(current)} {"afirmação" if len(current)==1 else "afirmações"} e fontes (2026)</summary><div class="detail-body"><p class="evidence-focus" hidden><span></span><button type="button" class="link-button" data-all-evidence>Ver todas as evidências da ficha</button></p>{"".join(render_claim(x,sources,topic_by) for x in current)}</div></details>'
    other_html=f'<details class="card-details historical-evidence"><summary>Histórico temático e material sem data · {len(other)}</summary><div class="detail-body"><p class="subtle">Não utilizado para preencher os filtros de 2026.</p>{"".join(render_claim(x,sources,topic_by) for x in other)}</div></details>' if other else ''
    if c['biography']:
        bio=f'<p>{esc(c["biography"])}</p>'+''.join(render_source(s) for s in c['biography_sources'])
    else:bio='<p class="subtle">Biografia individual não consolidada nesta revisão.</p>'
    role=c['current_role_observation']
    if role:
        bio+=f'<p class="subtle">Observação institucional de {esc(human_date(role.get("checked_at")))}: {esc(role["label"])}. {link(role.get("source"),"Consultar registro")}</p>'
    else:bio+='<p class="subtle">Exercício de cargo atual não confirmado individualmente nesta ficha. Candidatura ou resultado eleitoral não comprovam exercício de mandato.</p>'
    if c['history']:
        hist=''.join(f'<div class="history-item"><strong>{esc(h["year"])} · {esc(title(h["office"]))}</strong><br>{esc(title(h.get("place")))} · {esc(h.get("party"))} · {esc(h.get("result") or "Resultado não informado")}<br><span class="subtle">Votos históricos não coletados nesta base.</span></div>' for h in sorted(c['history'],key=lambda h:(-h['year'],str(h.get('candidate_id','')))))
        hist='<div class="history">'+hist+'</div><p class="subtle">Candidaturas anteriores vinculadas pelo TSE, não contagem de mandatos. '+link('https://cdn.tse.jus.br/estatistica/sead/odsele/historico_candidatura/historico_candidatura_2026.zip','Arquivo histórico oficial')+'</p>'
    elif c['history_state']=='not_collected_for_scope_addition':hist='<p class="subtle">Histórico ainda não coletado para este registro adicionado ao recorte.</p>'
    else:hist='<p class="subtle">Não foi localizada disputa anterior no arquivo vinculado consultado. Isso não comprova que seja a primeira candidatura.</p>'
    channels='<div class="channels">'+''.join(link(s['url'],s['label']) for s in c['channels'])+'</div>' if c['channels'] else '<p class="subtle">Nenhum endereço foi incorporado a esta ficha a partir da coleta disponível.</p>'
    return f'''<article class="candidate" id="candidato-{cid}" data-id="{cid}" data-name="{esc(c['name'])}" data-party="{esc(c['party'])}" data-status="{esc(c['status_id'])}" data-topics="{esc(' '.join(theme_ids))}" data-search="{esc(search)}">
<header class="card-top"><figure class="portrait">{photo}<span class="portrait-fallback" aria-hidden="true">{esc(initials)}</span></figure><div class="identity-copy"><div class="identity-top"><span class="number">{esc(c['number'])}</span><span class="party-name">{esc(c['party'])}</span></div><h3>{esc(c['name'])}</h3><p class="civil-name">{esc(c['full_name'])}</p></div><div class="registration"><span class="status-label">{esc(title(c['status']))}</span><time datetime="{DATE}">TSE · {esc(c['status_date'])}</time></div></header>
<div class="candidate-copy"><p class="kicker">{esc(label)}</p><p class="pauta">{esc(summary)}</p></div>
<div class="topic-tags js-only">{tags}</div>
<div class="card-actions">{link(c['tse_url'],'Cadastro TSE')}<a class="candidate-permalink" href="#candidato-{cid}">Link da ficha</a><button type="button" class="link-button js-only" data-share-candidate="{cid}" aria-label="Copiar endereço da ficha de {esc(c['name'])}">Copiar endereço</button></div>
{current_html}{other_html}
<details class="card-details"><summary>Trajetória e candidaturas anteriores</summary><div class="detail-body">{bio}{hist}</div></details>
<details class="card-details"><summary>Canais declarados ao TSE · {len(c['channels'])}</summary><div class="detail-body"><p class="subtle">Endereços fornecidos no cadastro eleitoral. Não houve verificação individual de todos os perfis.</p>{channels}</div></details>
</article>'''

def build():
    assert safe_url(SITE)==SITE and urlsplit(SITE).scheme=='https','Use an HTTPS canonical site URL'
    p=product();records=p['records'];topics=p['taxonomy'];topic_by={x['id']:x for x in topics}
    DEST.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True);DOC.mkdir(parents=True,exist_ok=True)
    for name in ['style.css','app.js']:shutil.copyfile(Path(__file__).parent/name,ASSETS/name)
    for c in records:
        if c['photo']:
            target=DEST/c['photo'];target.parent.mkdir(exist_ok=True);shutil.copyfile(ROOT/c['photo_source']['path'],target)
    tree=ET.fromstring((C/'sp-ibge.svg').read_bytes())
    for el in tree.iter():
        if el.tag.endswith('path'):el.set('fill','#8aab91');el.set('stroke','#35644f');el.set('stroke-width','120')
    tree.set('preserveAspectRatio','xMidYMid meet')
    ET.register_namespace('','http://www.w3.org/2000/svg');ET.ElementTree(tree).write(ASSETS/'sp-map.svg',encoding='unicode')
    counts=collections.Counter(c['party'] for c in records);statuses=collections.Counter(c['status'] for c in records)
    tema_counts=collections.Counter(a['id'] for c in records for a in c['themes_2026'])
    with2026=sum(bool(c['themes_2026']) for c in records)
    source_count=sum(len(c['sources']) for c in records)
    associations=sum(len(c['themes_2026']) for c in records)
    assert with2026==42 and associations==218 and source_count==75
    party_buttons='<button type="button" class="party-button party-all" data-party-filter="" aria-pressed="true"><span>Todos os partidos</span><small>'+str(len(records))+'</small></button>'
    party_buttons+=''.join(f'<button type="button" class="party-button" data-party-filter="{esc(party)}" aria-pressed="false"><span>{esc(party)}</span><small>{counts[party]}</small></button>' for party in p['party_scope'])
    topic_buttons=''.join(f'<button type="button" class="theme-button" data-topic-filter="{esc(t["id"])}" aria-pressed="false" title="{esc(t.get("includes",t["label"]))}"><span>{esc(t["label"])}</span><small aria-label="{tema_counts[t["id"]]} registros com evidência">{tema_counts[t["id"]]}</small></button>' for t in topics)
    status_options=''.join(f'<option value="{slug(s)}">{esc(title(s))} ({n})</option>' for s,n in sorted(statuses.items()))
    group_html=''.join(f'<section class="party-group" data-party="{esc(party)}" id="partido-{slug(party)}"><header class="party-heading"><h2>{esc(party)}</h2><p data-group-count>{counts[party]} registros</p></header><div class="candidate-list">'+''.join(render_card(c,topic_by) for c in records if c['party']==party)+'</div></section>' for party in sorted(counts,key=fold))
    edition_routes=[('../../','SC · Federais'),('../../deputados-estaduais/','SC · Estaduais'),('../../rs/deputados-federais/','RS · Federais'),('../../pr/deputados-federais/','PR · Federais'),('../../pr/deputados-estaduais/','PR · Estaduais'),('./','SP · Federais')]
    edition_links=''.join(f'<a href="{href}"'+(' aria-current="page"' if href=='./' else '')+f'>{label}</a>' for href,label in edition_routes)
    info={'canonical':p['canonical'],'parties':p['party_scope'],'topics':[{'id':t['id'],'label':t['label']} for t in topics],'statuses':[{'id':slug(s),'label':title(s)} for s in sorted(statuses)]}
    encoded_info=json.dumps(info,ensure_ascii=False).replace('<','\\u003c')
    description=f'Consulte {len(records)} registros de deputados federais por São Paulo em 2026: dados do TSE, histórico e temas documentados com fontes. Sem ranking.'
    ld={'@context':'https://schema.org','@type':'CollectionPage','name':'São Paulo · Deputados federais 2026 | Esquerda em foco','url':p['canonical'],'description':description,'dateModified':DATE,'inLanguage':'pt-BR','mainEntity':{'@type':'ItemList','itemListOrder':'https://schema.org/ItemListUnordered','numberOfItems':len(records),'itemListElement':[{'@type':'Person','name':c['name'],'identifier':c['id'],'url':p['canonical']+'#candidato-'+c['id']} for c in records]}}
    ld_json=json.dumps(ld,ensure_ascii=False).replace('<','\\u003c')
    page=f'''<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>São Paulo · Deputados federais 2026 | Esquerda em foco</title><meta name="description" content="{esc(description)}"><meta name="referrer" content="strict-origin-when-cross-origin"><meta name="theme-color" content="#f3ecdf"><link rel="canonical" href="{esc(p['canonical'])}"><meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:title" content="São Paulo · Deputados federais 2026"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(p['canonical'])}"><link rel="icon" href="../../favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="assets/style.css"><script defer src="assets/app.js"></script><script type="application/ld+json">{ld_json}</script></head>
<body><a class="skip" href="#candidaturas">Ir para as candidaturas</a>
<nav class="topbar" id="siteNav" aria-label="Navegação principal"><div class="wrap nav-inner"><a class="brand" href="../../"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span><span>Esquerda em foco</span><span class="edition">SP · 2026</span></a><button type="button" id="siteNavMenu" class="menu-toggle" aria-controls="siteNavLinks" aria-expanded="false">Menu</button><div class="main-links" id="siteNavLinks"><a href="#candidaturas">Candidaturas</a><a href="#sobre">Sobre</a><a href="#como-ler">Como ler</a><a href="#fontes">Fontes</a><a href="#edicoes">Edições</a></div></div></nav>
<header class="hero" id="topo"><img class="hero-map" src="assets/sp-map.svg" alt="" aria-hidden="true" width="1080" height="668"><div class="wrap"><div class="hero-grid"><div><p class="kicker">Esquerda em foco <span class="dot">•</span> Eleições 2026</p><h1>São Paulo</h1><p class="office">Deputado(a) Federal</p></div><p class="dek">Cadastros, trajetórias e posições públicas. Consulte as fontes e veja o que está documentado em cada candidatura.</p></div><div class="stats"><div><strong>{len(records)}</strong><span>registros no recorte</span></div><div><strong>{len(p['party_scope'])}</strong><span>siglas no recorte</span></div><div><strong>{with2026}</strong><span>com temas de 2026</span></div><div><strong>21/09</strong><span>fotografia de 2026</span></div></div><p class="subtle">Os registros incluem diferentes situações eleitorais. A posição na página não é uma avaliação de candidaturas.</p><nav class="editions" id="edicoes" aria-label="Edições do levantamento">{edition_links}</nav></div></header>
<noscript><p class="no-js-note">Sem JavaScript, todas as fichas e fontes continuam disponíveis. Use a busca do navegador; os filtros e a rotação diária precisam de JavaScript.</p></noscript>
<div class="searchbar js-only" id="searchBar"><div class="wrap search-inner"><label class="searchbox" for="searchInput"><span aria-hidden="true">⌕</span><span class="sr-only">Buscar por nome, número, partido ou tema</span><input id="searchInput" type="search" maxlength="140" autocomplete="off" placeholder="Nome, número, partido ou tema…"></label><output class="result-count" id="resultCount" aria-live="polite" aria-atomic="true">{len(records)} de {len(records)} registros</output><button id="shareFilters" class="share-button" type="button">Compartilhar filtros</button></div><div class="wrap"><p class="share-status" id="shareStatus" role="status"></p><div class="share-fallback" id="shareFallback" hidden><label for="shareURL" class="subtle">Endereço para copiar</label><input id="shareURL" readonly></div></div></div>
<main class="wrap layout" id="candidaturas"><aside class="rail js-only" aria-label="Filtros de candidaturas"><details class="filter-disclosure" id="filterDetails" open><summary>Filtrar candidaturas<span id="filterBadge"></span></summary><div class="filter-content"><div class="filter-block"><span class="filter-label">Partidos</span><div class="party-buttons">{party_buttons}</div><p>Vários partidos: qualquer uma das siglas selecionadas. PCB tem zero registros nesta fotografia.</p></div><div class="filter-block"><label class="filter-label" for="statusFilter">Situação no TSE</label><select id="statusFilter"><option value="">Todas as situações</option>{status_options}</select></div><div class="filter-block"><label class="filter-label" for="topicMode">Temas documentados · 2026</label><p>Os filtros encontram documentos sobre o tema. Não presumem apoio a toda medida incluída nele.</p><select id="topicMode"><option value="qualquer">Qualquer tema selecionado</option><option value="todos">Todos os temas selecionados</option></select><div class="theme-buttons">{topic_buttons}</div><button type="button" class="link-button" id="clearTopics">Limpar somente temas</button></div><div class="filter-block"><label for="orderFilter" class="filter-label">Ordem de exibição</label><select id="orderFilter"><option value="diaria">Rotação diária</option><option value="alfabetica">Alfabética</option></select><p id="orderNote">Ordem alfabética com rotação diária no horário de Brasília. Não é classificação.</p></div><div class="filter-tools"><button type="button" class="plain-button" data-clear-filters>Limpar filtros</button><button type="button" class="plain-button" id="seeResults">Ver resultados</button></div><p id="filterResultCount">{len(records)} registros com estes filtros</p></div></details></aside>
<div class="content"><div id="resultsStart" tabindex="-1"><p class="notice">{with2026} registros têm temas documentados em 2026. Os demais continuam visíveis, com as lacunas identificadas. <a href="#como-ler">Como ler os filtros</a></p></div><div class="selected-filters" id="selectedFilters" hidden aria-label="Filtros selecionados"></div><p class="notice" id="filterWarning" hidden role="status"></p><section class="empty" id="emptyResults" hidden><h2>Nenhum registro nesta combinação</h2><p>Isso indica ausência de correspondência nos dados pesquisados, não ausência de candidatos que defendam essas pautas.</p><button class="plain-button" type="button" data-clear-filters>Limpar filtros</button></section><div id="partyGroups">{group_html}</div>
<section class="doc-section" id="sobre"><p class="kicker">Sobre esta edição</p><details><summary>O que o levantamento reúne</summary><p>Esta edição contém {len(records)} registros para deputado federal por São Paulo em 2026, nas siglas {esc(', '.join(p['party_scope']))}. Não é uma lista de todas as candidaturas do estado. A fonte eleitoral completa consultada reúne 1.131 registros para esse cargo; o projeto aplica um recorte partidário explícito.</p><p>O produto preserva os 234 registros dos Rounds A e B e inclui outros 15 (10 da REDE e 5 do PSTU) para acompanhar a configuração nacional do projeto. PCB permanece no recorte com contagem zero. Os 15 registros adicionados ainda não receberam pesquisa temática individual.</p><p>A pesquisa temática foi importada do Round B, com revisão registrada em 21/09/2026: 48 fichas têm alguma afirmação documentada; 42 têm material identificado em 2026 e seis, apenas material histórico ou sem data confirmada. As outras 186 fichas do Round B não possuem síntese temática. A integração de interface não refaz nem amplia essa pesquisa.</p><p>As fotos e dados eleitorais provêm do TSE. O histórico apresenta candidaturas, não tempo de mandato. Cargos atuais só aparecem quando há uma observação institucional individual atribuída.</p><p>Esta é uma fotografia dos dados, não uma consulta em tempo real. Atualizações futuras de registro e de posição política podem exigir revisão.</p></details></section>
<section class="doc-section" id="como-ler"><p class="kicker">Como ler</p><details><summary>Um tema não é uma recomendação</summary><p>Ao selecionar um tema, você encontra candidaturas com documentação relacionada a ele em 2026. A ficha distingue proposta, declaração e atuação. Um requerimento de debate ou uma destinação orçamentária não é apresentado como apoio genérico a todas as políticas dessa área.</p><p>Toque em um tema da ficha para abrir as afirmações que justificam a associação, com suas fontes. Conteúdo histórico ou sem data original confirmada fica em outra seção e não entra nos filtros de 2026. Uma fonte de campanha documenta o que a candidatura declara, não comprova que a proposta foi implementada.</p><p>Partidos selecionados são combinados por “qualquer um”. Entre temas, você escolhe “qualquer” ou “todos”. Busca, partidos, situação e temas são combinados entre si. Os endereços compartilháveis guardam os filtros escolhidos; a página não grava preferências políticas em armazenamento local.</p><p>A ordem parte do alfabeto e muda uma posição por dia, entre partidos e dentro de cada partido, no horário de Brasília. Você pode optar pela ordem alfabética fixa. Nenhuma dessas ordens expressa preferência ou previsão eleitoral.</p><p>“Sem síntese” significa apenas que a revisão não incorporou documentação suficiente. Não significa oposição a um tema, ausência de propostas ou falta de trajetória. As situações de renúncia e indeferimento permanecem no cadastro e são exibidas com a redação da fonte.</p></details></section>
<section class="doc-section" id="fontes"><p class="kicker">Fontes e transparência</p><h2>O caminho até cada informação</h2><div class="source-grid"><div><p class="kicker">Cadastro e situação</p>{link(TSE,'Dados abertos do TSE')}<p class="subtle">Cadastro de 21/09/2026. Situações eleitorais e identificadores preservados.</p></div><div><p class="kicker">Pesquisa individual</p><p class="subtle">Cada afirmação aponta para a fonte consultada no Round B. Propostas e atuação são apresentadas separadamente.</p></div><div><p class="kicker">Mapa</p>{link(p['provenance']['supplemental_collection']['sources']['map']['url'],'Malha de São Paulo · IBGE')}</div><div><p class="kicker">Disponibilidade das fontes</p><p class="subtle">{p['provenance']['upstream_source_link_check']['accessible']} de 75 URLs editoriais responderam à verificação automática. Falhas de acesso ficam sinalizadas; um retorno HTTP não é confirmação editorial.</p></div></div><div class="downloads"><a href="dados.json">Dados desta edição (JSON)</a><a href="candidaturas.csv">Cadastro (CSV)</a><a href="evidencias.json">Afirmações e fontes (JSON)</a><a href="auditoria.json">Cobertura e limites (JSON)</a><a href="fontes.json">Disponibilidade das fontes (JSON)</a><a href="../">Entrada de São Paulo</a></div></section></div></main>
<footer class="footer"><div class="wrap"><p><strong>Levantamento independente</strong> · São Paulo · 2026</p><p>Consulte as fontes oficiais · Correções: <a href="mailto:jarbas@agents.soberania.cloud">jarbas@agents.soberania.cloud</a></p></div></footer><script type="application/json" id="pageData">{encoded_info}</script></body></html>'''
    (DEST/'index.html').write_text(page,encoding='utf-8')
    dump(C/'product.json',p);dump(DEST/'dados.json',p)
    dump(DEST/'evidencias.json',{'date':DATE,'note':'Imported Round B; not independently editorially rechecked in C.','records':[{'candidate_id':c['id'],'claims_2026':c['claims_2026'],'claims_other':c['claims_other'],'sources':c['sources'],'themes_2026':c['themes_2026']} for c in records]})
    dump(DEST/'fontes.json',load(DOC/'source-link-check.json'))
    with (DEST/'candidaturas.csv').open('w',encoding='utf-8-sig',newline='') as f:
        cols=['id','name','full_name','number','party','state','office_code','status','tse_url'];w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore',delimiter=';');w.writeheader();w.writerows(records)
    report={'technical_gate':'BUILD_PASS_SEE_SEPARATE_TEST_REPORT','editorial_scope':'Round B imported, not re-reviewed by C','records':len(records),'round_b_records':234,'scope_additions_not_reviewed':15,'parties':{party:counts[party] for party in p['party_scope']},'status_counts':dict(sorted(statuses.items())),'records_with_2026_topics':with2026,'records_with_only_noncurrent_claims':sum(bool(c['claims_other']) and not c['claims_2026'] for c in records),'records_without_2026_topics':len(records)-with2026,'associations_2026':associations,'claims_2026':sum(len(c['claims_2026']) for c in records),'claims_noncurrent':sum(len(c['claims_other']) for c in records),'photos':sum(bool(c['photo']) for c in records),'biographies':sum(bool(c['biography']) for c in records),'history_records':sum(len(c['history']) for c in records),'topics':len(topics),'topic_id_migration':ALIASES,'source_link_check':p['provenance']['upstream_source_link_check'],'current_filter_semantics':'documented_subject_not_generic_support','canonical':p['canonical'],'source_input_sha256':{str(path.relative_to(ROOT)):digest(path) for path in [INPUT/'research/records.json',INPUT/'research/theme-evidence-2026.json',INPUT/'round-b/normalized.json',ROOT/'config/party-scope-2026.json',ROOT/'config/topics-v1.json']},'generated_html_sha256':digest(DEST/'index.html')}
    dump(DEST/'auditoria.json',report);dump(DOC/'build.json',report)
    sitemap=f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{esc(p["canonical"])}</loc><lastmod>{DATE}</lastmod></url></urlset>\n';(DEST/'sitemap.xml').write_text(sitemap)
    hub=f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>São Paulo 2026 | Esquerda em foco</title><meta name="description" content="Edição de São Paulo: cadastro eleitoral, histórico e temas documentados com fontes."><link rel="canonical" href="{esc(SITE)}sp/"><link rel="stylesheet" href="deputados-federais/assets/style.css"></head><body><main class="hub"><p class="kicker">Esquerda em foco · Eleições 2026</p><h1>São Paulo</h1><p>Cadastros oficiais e posições públicas acompanhadas de fontes. Veja também as lacunas da pesquisa, sem notas ou classificação de candidaturas.</p><nav><a href="deputados-federais/">Deputados federais<br>{len(records)} registros no recorte</a></nav><p class="subtle">A edição de deputados estaduais de São Paulo não está disponível nesta entrega.</p><p><a href="../">Voltar ao início</a></p></main></body></html>'
    (ROOT/'sp/index.html').write_text(hub,encoding='utf-8')
    # Minimal, idempotent navigation surgery; no whole-document reserialization.
    home=ROOT/'index.html';text=home.read_text(encoding='utf-8')
    if NAV_LINK not in text:
        match=re.search(r'(<div\b[^>]*id="siteNavLinks"[^>]*>)(.*?)(</div>)',text,re.S)
        assert match,'Homepage navigation anchor not found; refusing unbounded replacement'
        text=text[:match.end(2)]+NAV_LINK+text[match.end(2):];home.write_text(text,encoding='utf-8')
    sitemap_path=ROOT/'sitemap.xml';text=sitemap_path.read_text(encoding='utf-8')
    for address in [SITE+'sp/',p['canonical']]:
        if '<loc>'+address+'</loc>' not in text:
            assert '</urlset>' in text
            text=text.replace('</urlset>',f'  <url><loc>{address}</loc><lastmod>{DATE}</lastmod></url>\n</urlset>')
    sitemap_path.write_text(text,encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in {'source_input_sha256'}},ensure_ascii=False,indent=2))
if __name__=='__main__':build()

"""Publish A-D.2 audit views after rendering, before tests. Only this edition writes.
Earlier source snapshots remain intact. Cumulative coverage includes separately
provenanced national and state nominal totals, never mixed populations.
"""
from __future__ import annotations
import collections
import hashlib
import html
import json
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
D=ROOT/'data/rs-estaduais';A=ROOT/'docs/rs-estaduais';P=ROOT/'rs/deputados-estaduais'
def load(path,default=None):return json.loads(path.read_text(encoding='utf-8')) if path.exists() else default
def save(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def run():
    data=load(D/'normalized.json');records=data['candidates']
    ledger=load(D/'ad2-research-ledger.json',[]);by_id={r['candidate_id']:r for r in ledger}
    index=load(D/'ad2-vote-index.json',{})
    history=[(c['id'],h) for c in records for h in c['history'] if h['year']<2026]
    for c in records:
        review=by_id.get(c['id'])
        if review:c['research_review']={'phase':'A-D.2','checked_at':review['checked_at'],'status':review['status'],'nominal_search_performed':True,'exhaustive':False,'search_count':len(review['searches']),'additional_source_checks':len(review['source_checks'])}
    save(D/'normalized.json',data);save(P/'dados.json',data)
    save(P/'pesquisa.json',{'phase':'A-D.2','checked_at':'2026-09-21','note':'Busca nominal cobre a fila, não significa pesquisa exaustiva nem comprova ausência de propostas. A situação eleitoral de 2026 não foi atualizada nesta etapa.','candidates':ledger})
    provenance=load(P/'fontes.json',{})
    provenance['ad2']={'applied':load(A/'ad2/applied.json',{}),'nominal_vote_evidence':index,'historical_registration_reviews':load(D/'ad2-historical-status.json',[]),'research_ledger_url':'pesquisa.json'}
    save(P/'fontes.json',provenance)
    soup=BeautifulSoup((P/'index.html').read_text(encoding='utf-8'),'html.parser')
    for node in soup.select('[data-ad2-note],#ad2-research-method'):node.decompose()
    for c in records:
        article=soup.find(id='candidato-'+c['id'])
        if article is None:raise ValueError('Rendered candidature is missing')
        notes=[]
        for h in c['history']:
            if h.get('votes_evidence_id'):
                scope='circunscrição nacional (Brasil)' if h['votes_electoral_unit']=='BR' else 'circunscrição do Rio Grande do Sul'
                notes.append('<p><strong>'+str(h['year'])+' · votação nominal:</strong> total conferido para a '+scope+', '+str(h['round'])+'º turno. <a href="'+html.escape(h['votes_source'],quote=True)+'" target="_blank" rel="noopener noreferrer">Tabela oficial do TSE ↗</a></p>')
            review=h.get('historical_registration_review')
            if review:
                state=html.escape(review.get('registration_status') or 'Não informado')
                suffix=' O total nominal continua não confirmado; nenhum zero foi inferido.' if h.get('votes') is None else ''
                notes.append('<p><strong>'+str(h['year'])+' · cadastro histórico:</strong> '+state+'.'+suffix+' Esta informação se refere à disputa antiga, não à situação de 2026. <a href="'+html.escape(review['source_url'],quote=True)+'" target="_blank" rel="noopener noreferrer">Ficha histórica do TSE ↗</a></p>')
        if notes:
            box=BeautifulSoup('<details data-ad2-note="history" class="ad2-history-note"><summary>Conferências adicionais do histórico</summary><div>'+''.join(notes)+'</div></details>','html.parser').details
            host=article.select_one('.rs-history')
            if host:host.insert_after(box)
            else:article.append(box)
    method=soup.select_one('#fontes')
    if method:method.append(BeautifulSoup('<p id="ad2-research-method" class="rs-data-links">A busca nominal A–D.2 percorreu as 99 lacunas da base corrigida. Isso não significa pesquisa exaustiva: propostas só foram acrescentadas quando sustentadas por fonte individual. <a href="pesquisa.json">Registro individual das consultas e pendências</a>.</p>','html.parser'))
    old_style=soup.find(id='ad2-history-style')
    if old_style:old_style.decompose()
    style=soup.new_tag('style',id='ad2-history-style')
    style.string='.ad2-history-note{margin-top:12px;padding-top:10px;border-top:1px solid var(--rule);font-size:.8rem;line-height:1.55;overflow-wrap:anywhere}.ad2-history-note summary{cursor:pointer;font-weight:600;min-height:32px}.ad2-history-note p{margin:.6rem 0}.ad2-history-note a{text-decoration:underline}.ad2-history-note :focus-visible{outline:2px solid currentColor;outline-offset:3px}'
    soup.head.append(style)
    rendered=str(soup).replace('viewbox=','viewBox=')
    (P/'index.html').write_text(rendered,encoding='utf-8')
    checksum=hashlib.sha256(rendered.encode()).hexdigest()
    for path in (A/'build-report.json',P/'cobertura.json'):
        obj=load(path,{})
        obj['html_sha256']=checksum
        obj['ad2']={'searched_candidates':len(ledger),'research_exhaustive':False,'new_summary_inputs':load(A/'ad2/applied.json')['new_summary_inputs'],'historical_registration_reviews':len(load(D/'ad2-historical-status.json')),'separate_nominal_sources':len(index)}
        save(path,obj)
    statuses=dict(collections.Counter(h.get('votes_status','unclassified') for _,h in history))
    summary=load(A/'phase2/votes-summary.json',{})
    summary.update({'historical_rows':len(history),'by_status':statuses,'by_year_verified':dict(collections.Counter(str(h['year']) for _,h in history if h.get('votes') is not None)),'current_coverage_stage':'A-D.2','ad2_nominal_sources':len(index),'scope_note':'Cumulative view: national presidential total has its own BR member and evidence index; RS totals retain their own sources. Null is not zero.'})
    save(A/'phase2/votes-summary.json',summary)
    coverage=load(A/'votes-coverage.json',{})
    coverage.update({'historical_rows_with_votes':sum(h.get('votes') is not None for _,h in history),'candidates_with_past_votes':sum(any(h['year']<2026 and h.get('votes') is not None for h in c['history']) for c in records),'current_coverage_stage':'A-D.2','ad2_evidence_file':'data/rs-estaduais/ad2-vote-index.json','population_note':'Uma linha presidencial usa o membro BR nacional; nenhuma soma exclusivamente do RS é apresentada como total nacional.'})
    save(A/'votes-coverage.json',coverage)
    print(json.dumps({'html_sha256':checksum,'historical_rows':len(history),'nominal_rows':coverage['historical_rows_with_votes'],'research_ledger_count':len(ledger)}))
if __name__=='__main__':run()

"""GLOBAL-04 L02: bind the common query transport to existing edition runtimes.
No electoral research, topic crosswalk or candidate text is generated here.
"""
from __future__ import annotations
import argparse,hashlib,json,posixpath,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
BASE='1a71c03987f52104af12af42eebda52449ff5570'

def load(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(path,entry):return posixpath.relpath(path,posixpath.dirname(entry))

def query_markup(soup,e,party_ui):
    tools=soup.new_tag('section',attrs={'class':'eef-query-tools','id':'eefQueryTools','hidden':'','data-global04-query':'tools','aria-label':'Ferramentas da consulta'})
    row=soup.new_tag('div',attrs={'class':'eef-query-row'});tools.append(row)
    parties=soup.new_tag('div',attrs={'class':'eef-query-parties','id':'eefQueryParties','hidden':'','data-global04-query':'parties'})
    label=soup.new_tag('p',attrs={'class':'eef-query-label'});label.string='Partidos';parties.append(label)
    host=soup.new_tag('div',attrs={'class':'eef-query-party-list','id':'eefQueryPartyHost','role':'group','aria-label':'Filtrar por um ou mais partidos'});parties.append(host)
    help=soup.new_tag('p',attrs={'class':'eef-query-help'});help.string='Ao marcar mais de um partido, entram registros de qualquer um deles. A seleção não altera a ordem por relevância.';parties.append(help);row.append(parties)
    actions=soup.new_tag('div',attrs={'class':'eef-query-actions'});row.append(actions)
    summary=soup.new_tag('p',attrs={'class':'eef-query-summary','id':'eefQuerySummary','aria-live':'polite'});summary.string='Consulta atual';actions.append(summary)
    button=soup.new_tag('button',attrs={'class':'eef-button','id':'eefShareQuery','type':'button','data-eef-query-share':'','disabled':''});button.string='Compartilhar consulta';actions.append(button)
    notice=soup.new_tag('p',attrs={'class':'eef-query-notice','id':'eefQueryNotice','role':'status','aria-live':'polite','hidden':''});tools.append(notice)
    return tools

def dialog_markup(soup):
    d=soup.new_tag('dialog',attrs={'class':'eef-query-share','id':'eefQueryShareDialog','aria-labelledby':'eefQueryShareTitle','data-global04-query':'dialog'})
    inner=soup.new_tag('div',attrs={'class':'eef-query-share__inner'});d.append(inner)
    head=soup.new_tag('header',attrs={'class':'eef-query-share__head'});inner.append(head)
    h=soup.new_tag('h2',id='eefQueryShareTitle');h.string='Compartilhar consulta';head.append(h)
    close=soup.new_tag('button',attrs={'class':'eef-button','id':'eefQueryShareClose','type':'button'});close.string='Fechar';head.append(close)
    p=soup.new_tag('p');p.string='O link guarda somente os critérios desta edição. Ele não é secreto e não mistura estado, cargo ou ano.';inner.append(p)
    lab=soup.new_tag('label',attrs={'for':'eefQueryShareUrl'});lab.string='Link da consulta';inner.append(lab)
    ta=soup.new_tag('textarea',attrs={'id':'eefQueryShareUrl','readonly':'','rows':'3'});inner.append(ta)
    actions=soup.new_tag('div',attrs={'class':'eef-query-share__actions'});inner.append(actions)
    copy=soup.new_tag('button',attrs={'class':'eef-button','id':'eefQueryCopy','type':'button'});copy.string='Copiar link';actions.append(copy)
    wa=soup.new_tag('a',attrs={'class':'eef-button','id':'eefQueryWhatsapp','target':'_blank','rel':'noopener noreferrer'});wa.string='WhatsApp';actions.append(wa)
    native=soup.new_tag('button',attrs={'class':'eef-button','id':'eefQueryNative','type':'button','hidden':''});native.string='Outros aplicativos';actions.append(native)
    status=soup.new_tag('p',attrs={'id':'eefQueryShareStatus','role':'status','aria-live':'polite'});inner.append(status)
    privacy=soup.new_tag('p',attrs={'class':'eef-query-privacy'});privacy.string='Você escolhe o contato e confirma o envio. O site não acessa seus contatos, não envia a consulta automaticamente e não salva esses critérios em uma conta.';inner.append(privacy)
    return d

def update_version(soup,suffix,path,entry):
    h=digest(ROOT/path)[:12]
    for n in soup.select('script[src]'):
        src=n.get('src','').split('?')[0]
        if src.endswith(suffix):n['src']=src+'?v='+h

def enhance(e):
    path=ROOT/e['entrypoint'];soup=BeautifulSoup(path.read_text(),'html.parser')
    for n in soup.select('[data-global04-query]'):n.decompose()
    for id in ['eefEditionQueryData','eefQueryShareDialog']:
        n=soup.find(id=id)
        if n:n.decompose()
    party_ui='native' if e['edition_id']=='2026-sp-federais' else 'global'
    # Old single-party controls remain in the DOM for backwards-compatible automation, but not as duplicate visual UI.
    if e['edition_id'] in {'2026-sc-estaduais','2026-pr-federais','2026-pr-estaduais'}:
        old=soup.find(id='partyFilter')
        if old and old.parent.name=='label':old.parent['hidden']='';old.parent['data-global04-query-legacy']='party'
    if e['edition_id']=='2026-sp-federais':
        old=soup.find(id='shareFilters')
        if old:old['hidden']='';old['data-global04-query-legacy']='share'
    search=soup.find(id='searchInput');container=search.find_parent(id='searchBar') or search.find_parent(class_='toolbar-wrap')
    if not container:raise ValueError('Missing query insertion point '+e['edition_id'])
    container.insert_after(query_markup(soup,e,party_ui))
    soup.body.append(dialog_markup(soup))
    config=soup.new_tag('script',attrs={'id':'eefEditionQueryData','type':'application/json','data-global04-query':'config'})
    config.string=json.dumps({'edition_id':e['edition_id'],'label':f"{e['state']} · {e['office_label']} · {e['election_year']}",'party_ui':party_ui},ensure_ascii=False).replace('</','<\\/')
    soup.body.append(config)
    # Global core already exists from L01; update its hash and append L02 assets after local runtimes.
    update_version(soup,'assets/global/core.js','assets/global/core.js',e['entrypoint'])
    if e['edition_id']=='2026-sc-federais':update_version(soup,'assets/pauta-filters-editorial.js','assets/pauta-filters-editorial.js',e['entrypoint'])
    if e['state']=='PR':update_version(soup,'runtime.js','pr/assets/runtime.js',e['entrypoint'])
    if e['edition_id']=='2026-sp-federais':update_version(soup,'assets/app.js','sp/deputados-federais/assets/app.js',e['entrypoint'])
    if e['edition_id']=='2026-rs-federais':
        runtime=(ROOT/'tools/rs/runtime.js').read_text()
        target=None
        for n in soup.select('script:not([src])'):
            if 'Same daily presentation rule as SC' in n.get_text() or 'function applyDailyRotation()' in n.get_text():target=n
        if not target:raise ValueError('RS runtime not found')
        target.string=runtime
    css=soup.new_tag('link',attrs={'rel':'stylesheet','href':rel('assets/global/query.css',e['entrypoint'])+'?v='+digest(ROOT/'assets/global/query.css')[:12],'data-global04-query':'asset'});soup.head.append(css)
    js=soup.new_tag('script',attrs={'src':rel('assets/global/query.js',e['entrypoint'])+'?v='+digest(ROOT/'assets/global/query.js')[:12],'defer':'','data-global04-query':'asset'});soup.body.append(js)
    path.write_text(str(BeautifulSoup(str(soup),'html.parser')).replace('viewbox=','viewBox='))
    return {'edition_id':e['edition_id'],'path':e['entrypoint'],'party_ui':party_ui,'cards':len(soup.select('article.candidate'))}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--edition');ap.add_argument('--no-metadata',action='store_true');a=ap.parse_args();registry=load(ROOT/'config/editions.json')
    editions=[e for e in registry['editions'] if e['publication_status']=='published' and (not a.edition or e['edition_id']==a.edition)]
    if not editions:raise ValueError('Unknown edition')
    results=[enhance(e) for e in editions]
    if not a.no_metadata:
        for e in editions:
            e['capabilities']['D02']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L02'}
            e['capabilities']['D08']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L02'}
            e['capabilities']['global_query_v1']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L02'}
            e['capabilities']['explicit_query_share']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L02'}
            e['capabilities']['multi_party_or']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L02'}
        save(ROOT/'config/editions.json',registry)
        prior=load(ROOT/'data/global-integration/migration-status.json')
        rows=[]
        for e in registry['editions']:
            before=next((x for x in prior['editions'] if x['edition_id']==e['edition_id']),None)
            rows.append({'edition_id':e['edition_id'],'baseline':BASE,'publication_status':e['publication_status'],
              'after_lot01':before.get('after_lot01') if before else None,'after_lot02':e['capabilities'],
              'implemented_in_lot02':['explicit-multi-party-OR','common-query-fragment','explicit-query-sharing'] if e['publication_status']=='published' else [],
              'preserved_local_query':{'2026-sc-federais':'current_support topics OR/AND','2026-sc-estaduais':'registration and trajectory','2026-rs-federais':'text search only','2026-pr-federais':'status/mandate/history/region + legacy_context themes AND','2026-pr-estaduais':'status/mandate/history/region + legacy_context themes AND','2026-sp-federais':'documented_topic themes OR/AND + status/order'}.get(e['edition_id']),
              'remaining':['G4-D editorial/evidence/transparency composition'] if e['publication_status']=='published' else ['Independent RS state publication gate'],
              'release_evidence':'Issue #43 / L02 PR; build alone is not publication'})
        save(ROOT/'data/global-integration/migration-status.json',{'schema_version':'1.0.0','baseline':BASE,'issue':43,'lot':'02','whole_issue_completed':False,'previous_lot':'PR #49','editions':rows})
        save(ROOT/'data/global04/lot02.json',{'baseline':BASE,'scope':'common-query-controls','whole_issue_completed':False,'editions':results,
          'semantic_guards':{'2026-sc-federais':'current_support','2026-pr-federais':'legacy_context','2026-pr-estaduais':'legacy_context','2026-sp-federais':'documented_topic'},
          'not_done':['G4-D editorial/evidence/transparency composition','taxonomy crosswalk review','RS state release','new political research']})
    print(json.dumps({'enhanced':results},ensure_ascii=False))
if __name__=='__main__':main()

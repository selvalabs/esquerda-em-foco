"""Lote 01: enhance current edition HTML, without rebuilding political research.
Idempotent; the original card remains the one read in the collection.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,posixpath,re
from pathlib import Path
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[2]
BASE='22bf032f12b44ec3471f90736035c3e020deea6d'
BLOCK_IDS=('eefSelectedNav','eefSelectionBar','eefCollection','eefShareDialog','eefConfirm','eefSelectionStatus','eefEditionSelectionData')

def load(p):return json.loads(p.read_text())
def save(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(path,entry):return posixpath.relpath(path,posixpath.dirname(entry))
def fragment(text):return BeautifulSoup(text,'html.parser')


def enhance(e, registry):
    path=ROOT/e['entrypoint'];soup=BeautifulSoup(path.read_text(),'html.parser')
    # Remove only the integration-owned layer before regenerating it.
    for node in soup.select('[data-global04],script[src*="assets/selecionados.js"]'):node.decompose()
    for id in BLOCK_IDS:
        n=soup.find(id=id)
        if n:n.decompose()
    for c in soup.select('article.candidate'):
        for n in c.select('.eef-card-actions,.eef-reader-party'):n.decompose()
    for a in soup.select('[data-global04-native-share]'):a.attrs.pop('data-global04-native-share',None)
    cards=soup.select('article.candidate');ids=[c['id'].removeprefix('candidato-') for c in cards]
    if not ids or len(ids)!=len(set(ids)) or any(not re.fullmatch(r'\d{12}',i) for i in ids):raise ValueError('Invalid edition IDs '+e['edition_id'])
    label=f"{e['state']} · {e['office_label']}"
    for c,cid in zip(cards,ids):
        actions=soup.new_tag('div',attrs={'class':'eef-card-actions','hidden':'','data-global04':'actions'})
        for attr,text in [('data-eef-toggle','Selecionar'),('data-eef-share','Compartilhar ficha')]:
            b=soup.new_tag('button',attrs={'class':'eef-button','type':'button',attr:cid});b.string=text
            if attr=='data-eef-toggle':b['aria-pressed']='false'
            actions.append(b)
        target=c.select_one('.candidate-copy')
        if target:target.insert(0,actions)
        else:c.append(actions)
        party=soup.new_tag('p',attrs={'class':'eef-reader-party','data-global04':'identity'});party.string=f"{c.get('data-party','')} · {label} · {e['election_year']}";actions.insert_after(party)
        for n in c.select('[data-share-candidate]'):n['data-global04-native-share']=''
    button=soup.new_tag('button',attrs={'class':'eef-button eef-global-selection-entry','id':'eefSelectedNav','data-eef-open':'','data-global04':'entry','type':'button','hidden':'','aria-label':'Abrir selecionados: 0 fichas'})
    button.append('Selecionados ');count=soup.new_tag('span',attrs={'data-eef-count':''});count.string='0';button.append(count)
    search=soup.select_one('#searchInput');container=search.find_parent(class_='toolbar') or search.find_parent(class_='search-inner')
    if container is None:raise ValueError('Missing search toolbar '+e['edition_id'])
    container.append(button)
    while soup.body.contents and not getattr(soup.body.contents[-1],'name',None) and not str(soup.body.contents[-1]).strip():soup.body.contents[-1].extract()
    for n in list(fragment((ROOT/'templates/global04/collection.html.txt').read_text()).contents):
        if getattr(n,'name',None):soup.body.append(n)
    soup.select_one('#eefCollection .eef-kicker').string=label+' · '+str(e['election_year'])
    config=soup.new_tag('script',attrs={'id':'eefEditionSelectionData','type':'application/json','data-global04':'config'})
    config.string=json.dumps({'edition_id':e['edition_id'],'label':label,'election_year':e['election_year']},ensure_ascii=False).replace('</','<\\/')
    soup.body.append(config)
    files=['assets/global/core.js','assets/selecionados-core.js','assets/global/selection-adapter.js','assets/global/selection.js']
    for f in files:
        if f=='assets/selecionados-core.js' and soup.select_one('script[src*="assets/selecionados-core.js"]'):continue
        node=soup.new_tag('script',attrs={'src':rel(f,e['entrypoint'])+'?v='+digest(ROOT/f)[:12],'data-global04':'script','defer':''});soup.body.append(node)
    link=soup.new_tag('link',attrs={'rel':'stylesheet','href':rel('assets/global/selection.css',e['entrypoint'])+'?v='+digest(ROOT/'assets/global/selection.css')[:12],'data-global04':'style'});soup.head.append(link)
    if e['edition_id']=='2026-sp-federais':
        notice=fragment('<div class="eef-sp-deeplink-notice" id="eefDeepLinkNotice" hidden data-global04="deep-link"><p id="eefDeepLinkMessage" role="status" aria-live="polite"></p><button id="eefRestoreQuery" type="button">Restaurar minha consulta</button></div>').div
        start=soup.select_one('#resultsStart')
        if start:start.insert_after(notice)
        else:soup.select_one('#partyGroups').insert_before(notice)
        for n in soup.select('script[src]'):
            if n['src'].split('?')[0].endswith('assets/app.js') and 'deputados-estaduais' not in n['src']:n['src']=n['src'].split('?')[0]+'?v='+digest(ROOT/'sp/deputados-federais/assets/app.js')[:12]
    if e['state']=='PR':
        for n in soup.select('script[src]'):
            if n['src'].split('?')[0].endswith('runtime.js'):n['src']=n['src'].split('?')[0]+'?v='+digest(ROOT/'pr/assets/runtime.js')[:12]
    if e['edition_id']=='2026-rs-federais':
        for n in soup.select('script:not([src])'):
            t=n.get_text()
            if 'function applyDailyRotation()' in t and "if(document.querySelector('article[data-eef-held]'))return;" not in t:
                n.string=t.replace('function applyDailyRotation() {',"function applyDailyRotation() {\n    if(document.querySelector('article[data-eef-held]'))return;",1)
    # Normalize adjacent whitespace from removed legacy nodes on the first build too.
    path.write_text(str(BeautifulSoup(str(soup),'html.parser')).replace('viewbox=','viewBox='))
    return {'edition_id':e['edition_id'],'cards':len(cards),'path':e['entrypoint']}


def main():
    p=argparse.ArgumentParser();p.add_argument('--edition');a=p.parse_args();registry=load(ROOT/'config/editions.json')
    if registry['root_mode']!='global_home':raise ValueError('Global home must remain active')
    editions=[e for e in registry['editions'] if e['publication_status']=='published' and (not a.edition or e['edition_id']==a.edition)]
    if not editions:raise ValueError('Unknown or unpublished edition')
    results=[enhance(e,registry) for e in editions]
    for e in editions:
        for cid in ['I01','I02','I03']:
            e['capabilities'][cid]={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L01'}
        if e['edition_id']=='2026-sp-federais':e['capabilities']['I04']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L01'}
        e['capabilities']['selected_collection']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L01'}
        e['capabilities']['global_collection_v2']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L01'}
        e['capabilities']['individual_share']={'state':'ready','semantic':None,'audit_ref':'GLOBAL-04-L01'}
    save(ROOT/'config/editions.json',registry)
    save(ROOT/'data/global04/lot01.json',{'baseline':BASE,'scope':'collection-and-deeplink','publication_gate':'check issue 43 and pull request; build alone is not publication','editions':[{'edition_id':e['edition_id'],'cards':len(BeautifulSoup((ROOT/e['entrypoint']).read_text(),'html.parser').select('article.candidate')),'path':e['entrypoint']} for e in registry['editions'] if e['publication_status']=='published'],'not_done':['Shared query UI migration G4-C','Editorial/evidence/transparency adaptation G4-D','RS state release','New political research']})
    print(json.dumps({'enhanced':results},ensure_ascii=False))

if __name__=='__main__':main()

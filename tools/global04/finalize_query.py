"""Idempotent L02 migration of the reviewed e5937b2 sources; never collects data.
Run once on the integration branch, commit the generated files, then verify them
with read-only CI. No main/other branch is overwritten by this script.
"""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def edit(path, old, new):
    p=ROOT/path;s=p.read_text()
    if new in s:return
    if s.count(old)!=1:raise ValueError(f'Ambiguous migration anchor: {path}: {old[:90]}')
    p.write_text(s.replace(old,new,1))

def main():
    p='tests/global04/query_validate.py'
    edit(p," 'config/editions.json'"," 'docs/GLOBAL-MIGRATION-PLAN.md','config/editions.json'")
    edit(p,"g.locator('article.candidate:not([hidden])').count() or e['edition_id']=='2026-sc-federais'","g.locator('article.candidate:not([hidden])').count()")
    edit(p," else:\n  vals=page.locator('[data-eef-party]')"," else:\n  if not page.locator('#eefQueryParties').evaluate('(e)=>e.open'):page.locator('#eefQueryPartyLabel').click()\n  vals=page.locator('[data-eef-party]')")
    for path,anchor,call in [
      ('assets/pauta-filters-editorial.js','function revealHash(hash, scroll) {','window.EEFQueryUI.reveal(hash,scroll)'),
      ('tools/rs/runtime.js','function revealHash() {','window.EEFQueryUI.reveal(location.hash,true)'),
      ('tools/pr/runtime.js','function revealHash(scroll = true) {','window.EEFQueryUI.reveal(location.hash,scroll)'),
      ('deputados-estaduais/ui/app.js','function revealHash() {','window.EEFQueryUI.reveal(location.hash,true)'),
      ('sp/deputados-federais/assets/app.js','function revealDeepLink(){','window.EEFQueryUI.reveal(location.hash,true)')]:
        edit(path,anchor,anchor+"\n    if(window.EEFQueryUI)return "+call+";\n    if(document.getElementById('eefEditionQueryData'))return;")
    edit('assets/pauta-filters-editorial.js',
      'core.filter(records, state).filter(record => !parties.size || parties.has(record.party))',
      "core.filter(records, {...state,query:''}).filter(record => core.normalize(search.value).trim().split(/\\s+/).filter(Boolean).every(t=>core.normalize(record.text).includes(t)) && (!parties.size || parties.has(record.party)))")
    edit('tools/rs/runtime.js','normalize(card.dataset.search).includes(query)',"query.split(/\\s+/).every(t=>normalize(card.dataset.search).includes(t))")
    edit('tools/pr/runtime.js',"window.addEventListener('popstate', () => {","window.addEventListener('popstate', () => {if(window.EEFQueryUI)return;")
    edit('deputados-estaduais/ui/app.js',"semantic:null});","semantic:null,exclusive:[['mandate','history']]});")
    edit('deputados-estaduais/ui/app.js','if (target && target.hidden) reset();',"if(target&&target.hidden){if(window.EEFQueryUI)window.EEFQueryUI.reveal(link.hash,false);else reset();}")
    p='sp/deputados-federais/assets/app.js'
    edit(p,"root.addEventListener('popstate',()=>{","root.addEventListener('popstate',()=>{if(root.EEFQueryUI)return;")
    edit(p,"restoreButton?.addEventListener('click',()=>{","restoreButton?.addEventListener('click',()=>{\n      if(root.EEFQueryUI)return;")
    edit(p,"search.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(()=>{state.q=search.value.trim().slice(0,140);change();},250);});","search.addEventListener('input',()=>{clearTimeout(timer);state.q=search.value.trim();change();});")
    edit(p,"e.preventDefault();state.q=search.value.trim().slice(0,140);change();","e.preventDefault();state.q=search.value.trim();change();")
    edit(p,"semantic:'documented_topic'});","semantic:'documented_topic',aliases:ALIASES});")
    edit(p,'function applyCommon(s){','function applyCommon(s){\n      clearTimeout(timer);')
    for origin,dest in [('tools/pr/runtime.js','pr/assets/runtime.js'),('deputados-estaduais/ui/app.js','deputados-estaduais/assets/app.js')]:
        (ROOT/dest).write_bytes((ROOT/origin).read_bytes())
    p='assets/global/core.js'
    edit(p,'const q=emptyQuery(valid.edition_id), ignored=[];',"if(!raw||typeof raw!=='object'||Array.isArray(raw))fail('Consulta inválida');\n    const q=emptyQuery(valid.edition_id), ignored=[];\n    if(raw.q!==undefined&&raw.q!==null&&typeof raw.q!=='string')fail('Busca inválida');")
    edit(p,"if(!Array.isArray(input))fail('Lista de filtros inválida');","if(!Array.isArray(input)||input.some(x=>typeof x!=='string'))fail('Lista de filtros inválida');")
    edit(p,'(valid.aliases?.[x]||x)',"(valid.aliases&&Object.hasOwn(valid.aliases,x)?valid.aliases[x]:x)")
    edit(p,'q.semantic=valid.semantic||null;',"for(const fields of valid.exclusive||[])if(fields.filter(k=>q[k]).length>1)fail('Critérios incompatíveis nesta edição');\n    q.semantic=valid.semantic||null;")
    p='tools/global04/query_build.py'
    edit(p,"parties=soup.new_tag('div',attrs=","parties=soup.new_tag('details',attrs=")
    edit(p,"label=soup.new_tag('p',attrs={'class':'eef-query-label'});label.string='Partidos'","label=soup.new_tag('summary',attrs={'class':'eef-query-label','id':'eefQueryPartyLabel'});label.string='Partidos · todos'")
    edit(p,"help.string='Ao marcar mais de um partido, entram registros de qualquer um deles. A seleção não altera a ordem por relevância.'","help.string='Escolha um ou mais partidos. Os números mostram o total de fichas da edição, antes dos filtros.'")
    edit(p,'parties.append(help);row.append(parties)',"parties.append(help);row.append(parties)\n    clearpart=soup.new_tag('button',attrs={'type':'button','id':'eefQueryAllParties','class':'eef-button'});clearpart.string='Todos os partidos';parties.append(clearpart)")
    edit(p,'actions.append(button)\n    notice',"actions.append(button)\n    clear=soup.new_tag('button',attrs={'type':'button','id':'eefQueryClear','class':'eef-button'});clear.string='Limpar consulta';actions.append(clear)\n    notice")
    edit(p,"search=soup.find(id='searchInput');container=","search=soup.find(id='searchInput');search['maxlength']='2048';container=")
    edit(p,'soup.body.append(dialog_markup(soup))',"""soup.body.append(dialog_markup(soup))
    if not soup.find(id='eefDeepLinkNotice'):
        note=BeautifulSoup('<div id="eefDeepLinkNotice" class="eef-sp-deeplink-notice" hidden data-global04-query="deep-link"><p id="eefDeepLinkMessage" role="status" aria-live="polite"></p><button id="eefRestoreQuery" type="button">Restaurar minha consulta</button></div>','html.parser').div
        soup.find(id='eefQueryTools').insert_after(note)
    if e['edition_id']=='2026-sc-estaduais':update_version(soup,'assets/app.js','deputados-estaduais/assets/app.js',e['entrypoint'])""")
    p=ROOT/'assets/global/query.css';s=p.read_text()
    extra='''
.eef-query-parties>summary{cursor:pointer;min-height:44px;padding:8px 0;overflow-wrap:anywhere}
.eef-query-party-list{padding:6px 0}
.eef-query-tools details[hidden]{display:none!important}
.eef-query-tools .eef-query-actions{flex-wrap:wrap}
.eef-query-tools .eef-query-summary{overflow-wrap:anywhere}
@media(max-width:760px){.eef-query-tools .eef-query-actions{display:flex;gap:8px}.eef-query-tools .eef-query-actions .eef-button{width:auto;flex:1 1 135px}.eef-query-tools .eef-query-summary{flex-basis:100%;font-size:13px}}
'''
    if extra not in s:p.write_text(s+extra)

if __name__=='__main__':main()

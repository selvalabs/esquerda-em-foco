"""Idempotent runtime adapter; changes no electoral or editorial payload."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]


def replace(text, old, new):
    if new in text:return text
    if text.count(old)!=1:raise ValueError('Unexpected runtime baseline: '+old[:90])
    return text.replace(old,new,1)


def patch():
    p=ROOT/'sp/deputados-federais/assets/app.js';s=p.read_text()
    s=replace(s,"    function applyOrder() {", "    function applyOrder() {\n      if(document.querySelector('article[data-eef-held]'))return;")
    s=replace(s,"    function change(replace=false){clearTimeout(timer);state.ignored=[];render();writeURL(replace);}",
      "    function change(replace=false){clearTimeout(timer);state.ignored=[];hideLinkNotice();render();writeURL(replace);}")
    s=replace(s,"    root.addEventListener('popstate',()=>{clearTimeout(timer);state=parseState(location.search,valid);render();});",
      "    root.addEventListener('popstate',()=>{clearTimeout(timer);state=parseState(location.search,valid);hideLinkNotice();render();revealDeepLink();});\n    root.addEventListener('hashchange',revealDeepLink);")
    old="""    render();
    if(location.hash.startsWith('#candidato-')){
      const el=document.getElementById(location.hash.slice(1));
      if(el&&!el.hidden)setTimeout(()=>el.scrollIntoView({block:'start'}),50);
    }"""
    new="""    let displacedFilters=null;
    const linkNotice=$('eefDeepLinkNotice'),restoreButton=$('eefRestoreQuery');
    function hideLinkNotice(){if(linkNotice)linkNotice.hidden=true;displacedFilters=null;}
    function revealDeepLink(){
      let id;try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
      const target=document.getElementById(id);if(!target)return;
      const card=target.closest('article.candidate');if(!card)return;
      if(card.dataset.eefHeld)return;
      if(card.hidden||card.closest('.party-group')?.hidden){
        clearTimeout(timer);
        displacedFilters={...state,parties:state.parties.slice(),topics:state.topics.slice(),ignored:state.ignored.slice()};
        state={...state,q:'',parties:[],topics:[],status:'',mode:'qualquer',ignored:[]};
        render();writeURL(true);
        if(linkNotice){
          $('eefDeepLinkMessage').textContent='Os filtros foram suspensos para abrir a ficha de '+card.querySelector('h3').textContent.trim()+'. Sua consulta anterior pode ser restaurada.';
          linkNotice.hidden=false;
        }
      }
      let parent=target;while(parent&&parent!==card){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
      requestAnimationFrame(()=>{target.scrollIntoView({block:'start',behavior:'instant'});target.setAttribute('tabindex','-1');target.focus({preventScroll:true});});
    }
    restoreButton?.addEventListener('click',()=>{
      if(!displacedFilters)return;
      const previous=displacedFilters;hideLinkNotice();state=previous;
      const query=serializeState(state);history.pushState(null,'',location.pathname+(query?'?'+query:''));
      render();search.focus({preventScroll:true});search.scrollIntoView({block:'center'});
    });
    root.EEFSPQuery=Object.freeze({apply:render,reveal:revealDeepLink});
    render();revealDeepLink();"""
    s=replace(s,old,new);p.write_text(s)
    for path in ['pr/assets/runtime.js','tools/pr/runtime.js']:
        p=ROOT/path;s=p.read_text();s=replace(s,'  function orderDaily(now = new Date()) {',"  function orderDaily(now = new Date()) {\n    if(document.querySelector('article[data-eef-held]'))return;");p.write_text(s)
    p=ROOT/'tools/rs/runtime.js';s=p.read_text();s=replace(s,'function applyDailyRotation() {',"function applyDailyRotation() {\n    if(document.querySelector('article[data-eef-held]'))return;");p.write_text(s)

    p=ROOT/'tools/global03/refresh.py';s=p.read_text()
    s=replace(s,"print(e['entrypoint'])", "if e.get('capabilities',{}).get('global_collection_v2',{}).get('state')=='ready':\n    import subprocess,sys\n    subprocess.run([sys.executable,str(ROOT/'tools/global04/build.py'),'--edition',e['edition_id']],check=True)\nprint(e['entrypoint'])")
    p.write_text(s)
    p=ROOT/'tests/global03/validate.py';s=p.read_text()
    s=replace(s,"check('new collection URL canonical '+str(mount),share.startswith(base+'sc/deputados-federais/#selecionados='))", "check('new collection URL canonical '+str(mount),share.startswith(base+'sc/deputados-federais/#eef=collection&v=2&edition=2026-sc-federais&'))")
    p.write_text(s)
    p=ROOT/'tools/sc_selected_ui/verify_live.py';s=p.read_text()
    s=replace(s,"OUT=Path('/tmp/eef-selected-live')", "EDITION=next(e for e in json.loads((ROOT/'config/editions.json').read_text())['editions'] if e['edition_id']=='2026-sc-federais')\nFILES[0]=EDITION['entrypoint']\nFILES += ['assets/global/core.js','assets/global/selection-adapter.js','assets/global/selection.js','assets/global/selection.css']\nOUT=Path('/tmp/eef-selected-live')")
    s=replace(s,"page.goto(BASE+'?verify='+SHA,wait_until='networkidle')", "page.goto(BASE+EDITION['canonical_path'].lstrip('/')+'?verify='+SHA,wait_until='networkidle')")
    s=replace(s,'classList.contains("eef-selected-ready")','classList.contains("eef-global04-ready")')
    s=replace(s,"nav=page.locator('#eefSelectedNav')", "nav=page.locator('#eefSelectedNav')\n            nav.scroll_into_view_if_needed()")
    s=replace(s,"fragment.get('selecionados')!=[','.join(selected)] or fragment.get('ficha')!=[selected[1]]", "fragment.get('ids')!=[','.join(selected)] or fragment.get('active')!=[selected[1]] or fragment.get('edition')!=['2026-sc-federais'] or fragment.get('v')!=['2']")
    p.write_text(s)

if __name__=='__main__':patch()

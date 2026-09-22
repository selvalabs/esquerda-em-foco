/* SP: no inferred topics, no scores, no stored political preferences. */
(function (root) {
  'use strict';
  const fold = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const unique = items => [...new Set(items)];
  const ALIASES = {'apostas-protecao-economica':'apostas-jogos','infraestrutura-desenvolvimento-regional':'infraestrutura-desenvolvimento','povos-indigenas-comunidades-tradicionais':'povos-indigenas-tradicionais'};
  function parseState(search, valid) {
    const p = new URLSearchParams(search), ignored = [];
    function select(key, allowed, mapper = x => x) {
      return unique((p.get(key) || '').split(',').filter(Boolean).map(mapper)).filter(x => {
        if (allowed.includes(x)) return true;
        ignored.push(key); return false;
      }).sort();
    }
    const parties = select('partidos', valid.parties, x => valid.parties.find(y => fold(x) === fold(y)) || x);
    const topics = select('pautas', valid.topics, x => ALIASES[x] || x);
    let status = p.get('situacao') || '';
    if (status && !valid.statuses.includes(status)) { ignored.push('situacao'); status = ''; }
    return {parties, topics, status, q:(p.get('q') || '').trim().slice(0,140), mode:p.get('modo') === 'todos' ? 'todos' : 'qualquer', order:p.get('ordem') === 'alfabetica' ? 'alfabetica' : 'diaria', ignored};
  }
  function serializeState(s) {
    const p = new URLSearchParams();
    if(s.q) p.set('q', s.q);
    if(s.parties.length) p.set('partidos', [...s.parties].sort().join(','));
    if(s.topics.length) p.set('pautas', [...s.topics].sort().join(','));
    if(s.mode === 'todos') p.set('modo', 'todos');
    if(s.status) p.set('situacao', s.status);
    if(s.order === 'alfabetica') p.set('ordem', 'alfabetica');
    return p.toString();
  }
  function matches(card, s) {
    if(s.parties.length && !s.parties.includes(card.party)) return false;
    if(s.status && s.status !== card.status) return false;
    const words = fold(s.q).split(/\s+/).filter(Boolean);
    if(words.some(x => !card.search.includes(x))) return false;
    if(!s.topics.length) return true;
    return s.mode === 'todos' ? s.topics.every(x => card.topics.includes(x)) : s.topics.some(x => card.topics.includes(x));
  }
  function dayKey(now = new Date()) {
    const parts = new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now);
    const d = Object.fromEntries(parts.map(p => [p.type,p.value]));
    return `${d.year}-${d.month}-${d.day}`;
  }
  function rotate(items, key) {
    if (!items.length) return [];
    const day = Math.floor(Date.parse(`${key}T00:00:00Z`)/86400000), shift=((day % items.length)+items.length)%items.length;
    return items.slice(shift).concat(items.slice(0,shift));
  }
  const api = {fold, parseState, serializeState, matches, dayKey, rotate};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.SPRoundC = api;
  if (typeof document === 'undefined') return;
  function boot() {
    const dataNode=document.getElementById('pageData');
    if(!dataNode) return;
    const meta = JSON.parse(dataNode.textContent), valid = {parties:meta.parties,topics:meta.topics.map(x=>x.id),statuses:meta.statuses.map(x=>x.id)};
    const topicNames = Object.fromEntries(meta.topics.map(x=>[x.id,x.label]));
    const cards = [...document.querySelectorAll('article.candidate')].map(el=>({el,id:el.dataset.id,party:el.dataset.party,status:el.dataset.status,topics:(el.dataset.topics||'').split(' ').filter(Boolean),search:fold(el.dataset.search),name:el.dataset.name}));
    const groups = [...document.querySelectorAll('.party-group')];
    let state = parseState(location.search,valid), timer=null, orderApplied=null, lastLegacySearch=location.search;
    const $=id=>document.getElementById(id), search=$('searchInput'), filterDetails=$('filterDetails'), mq=matchMedia('(max-width:760px)');
    document.documentElement.classList.add('js');
    function syncLayout() {
      filterDetails.open = !mq.matches;
      root.requestAnimationFrame(()=>{
        document.documentElement.style.setProperty('--nav-h', `${$('siteNav').clientHeight}px`);
        document.documentElement.style.setProperty('--bar-h', `${$('searchBar').offsetHeight}px`);
      });
    }
    syncLayout();
    if(mq.addEventListener) mq.addEventListener('change', syncLayout);
    else mq.addListener(syncLayout);
    root.addEventListener('resize',()=>root.requestAnimationFrame(()=>{
      document.documentElement.style.setProperty('--nav-h', `${$('siteNav').clientHeight}px`);
      document.documentElement.style.setProperty('--bar-h', `${$('searchBar').offsetHeight}px`);
    }));
    function applyOrder() {
      if(document.querySelector('article[data-eef-held]'))return;
      const key=dayKey(), sort=(a,b)=>a.localeCompare(b,'pt-BR',{sensitivity:'base'});
      if(orderApplied === state.order+key) return;
      orderApplied = state.order+key;
      let ordered=[...groups].sort((a,b)=>sort(a.dataset.party,b.dataset.party));
      if(state.order==='diaria') ordered=rotate(ordered,key);
      for(const group of ordered){
        let items=cards.filter(c=>c.party===group.dataset.party).sort((a,b)=>sort(a.name,b.name)||sort(a.id,b.id));
        if(state.order==='diaria')items=rotate(items,key);
        for(const c of items) group.querySelector('.candidate-list').appendChild(c.el);
        $('partyGroups').appendChild(group);
      }
      $('orderNote').textContent=state.order==='diaria' ? 'Ordem alfabética com rotação diária no horário de Brasília. Não é classificação.' : 'Ordem alfabética. Não é classificação.';
    }
    function reflect() {
      search.value=state.q;
      $('topicMode').value=state.mode; $('statusFilter').value=state.status; $('orderFilter').value=state.order;
      document.querySelectorAll('[data-party-filter]').forEach(b=>b.setAttribute('aria-pressed', String(b.dataset.partyFilter ? state.parties.includes(b.dataset.partyFilter) : !state.parties.length)));
      document.querySelectorAll('[data-topic-filter]').forEach(b=>b.setAttribute('aria-pressed',String(state.topics.includes(b.dataset.topicFilter))));
      const holder=$('selectedFilters'); holder.replaceChildren();
      const chips=[...state.parties.map(x=>['party',x,x]), ...state.topics.map(x=>['topic',x,topicNames[x]])];
      if(state.status) chips.push(['status',state.status,meta.statuses.find(x=>x.id===state.status).label]);
      for(const [kind,id,label] of chips){
        const b=document.createElement('button');b.type='button';b.className='selected-chip';b.textContent=`${label} ×`;b.setAttribute('aria-label',`Remover filtro ${label}`);
        b.addEventListener('click',()=>{if(kind==='party')state.parties=state.parties.filter(x=>x!==id);if(kind==='topic')state.topics=state.topics.filter(x=>x!==id);if(kind==='status')state.status='';change();});holder.appendChild(b);
      }
      holder.hidden=!chips.length;
      const active=state.parties.length+state.topics.length+(state.status?1:0)+(state.q?1:0);
      $('filterBadge').textContent=active?` · ${active} ativo${active===1?'':'s'}`:'';
    }
    function render() {
      let count=0;
      for(const c of cards){const show=matches(c,state);c.el.hidden=!show;if(show)count++;
        c.el.querySelectorAll('[data-show-evidence]').forEach(b=>b.classList.toggle('is-selected',state.topics.includes(b.dataset.showEvidence)));
      }
      for(const g of groups){const n=cards.filter(c=>c.party===g.dataset.party&&!c.el.hidden).length;g.hidden=!n;g.querySelector('[data-group-count]').textContent=`${n} registro${n===1?'':'s'}`;}
      $('resultCount').textContent=`${count} de ${cards.length} registros`;
      $('filterResultCount').textContent=`${count} registro${count===1?'':'s'} com estes filtros`;
      $('emptyResults').hidden=count!==0;
      $('filterWarning').hidden=!state.ignored.length;
      if(state.ignored.length)$('filterWarning').textContent='Algum filtro do endereço não existe nesta edição e foi ignorado.';
      reflect();applyOrder();
    }
    function writeURL(replace=false){
      const query=serializeState(state), next=location.pathname+(query?'?'+query:'')+location.hash;
      if(next===location.pathname+location.search+location.hash) return;
      try{history[replace?'replaceState':'pushState'](null,'',next);}catch(_){/* Local-file preview can still filter. */}
    }
    function change(){clearTimeout(timer);state.ignored=[];hideLinkNotice();render();}
    function clearAll(){state={...state,q:'',parties:[],topics:[],status:'',mode:'qualquer',ignored:[]};change();}
    search.addEventListener('input',()=>{clearTimeout(timer);state.q=search.value.trim();change();});
    search.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();state.q=search.value.trim();change();}});
    document.querySelectorAll('[data-party-filter]').forEach(b=>b.addEventListener('click',()=>{const id=b.dataset.partyFilter;state.parties=id?(state.parties.includes(id)?state.parties.filter(x=>x!==id):[...state.parties,id]):[];change();}));
    document.querySelectorAll('[data-topic-filter]').forEach(b=>b.addEventListener('click',()=>{const id=b.dataset.topicFilter;state.topics=state.topics.includes(id)?state.topics.filter(x=>x!==id):[...state.topics,id];change();}));
    $('topicMode').addEventListener('change',e=>{state.mode=e.target.value;change();});
    $('statusFilter').addEventListener('change',e=>{state.status=e.target.value;change();});
    $('orderFilter').addEventListener('change',e=>{state.order=e.target.value;change();});
    document.querySelectorAll('[data-clear-filters]').forEach(b=>b.addEventListener('click',clearAll));
    $('clearTopics').addEventListener('click',()=>{state.topics=[];change();});
    $('seeResults').addEventListener('click',()=>{if(mq.matches)filterDetails.open=false;root.requestAnimationFrame(()=>{const target=$('resultsStart');const offset=$('siteNav').getBoundingClientRect().height+$('searchBar').getBoundingClientRect().height+12;root.scrollTo({top:target.getBoundingClientRect().top+root.scrollY-offset,behavior:'instant'});target.focus({preventScroll:true});});});
    root.addEventListener('popstate',()=>{if(root.EEFQueryUI)return;clearTimeout(timer);if(location.search!==lastLegacySearch){state=parseState(location.search,valid);lastLegacySearch=location.search;}hideLinkNotice();render();revealDeepLink();});
    root.addEventListener('hashchange',revealDeepLink);
    function showEvidence(card, topic) {
      const details=card.querySelector('.current-evidence'); if(!details)return;
      details.open=true;
      details.querySelectorAll('.claim').forEach(c=>{c.hidden=Boolean(topic)&&!(c.dataset.topics||'').split(' ').includes(topic);});
      const note=details.querySelector('.evidence-focus');note.hidden=!topic;
      if(topic)note.querySelector('span').textContent=`Evidência para: ${topicNames[topic]}. `;
      card.querySelectorAll('[data-show-evidence]').forEach(b=>b.setAttribute('aria-expanded',String(Boolean(topic)&&b.dataset.showEvidence===topic)));
    }
    document.querySelectorAll('[data-show-evidence]').forEach(b=>b.addEventListener('click',()=>{const card=b.closest('.candidate');showEvidence(card,b.dataset.showEvidence);const d=card.querySelector('.current-evidence');d.scrollIntoView({block:'nearest'});}));
    document.querySelectorAll('[data-all-evidence]').forEach(b=>b.addEventListener('click',()=>showEvidence(b.closest('.candidate'),'')));
    document.querySelectorAll('.current-evidence').forEach(d=>d.addEventListener('toggle',()=>{if(!d.open)d.closest('.candidate').querySelectorAll('[data-show-evidence]').forEach(b=>b.setAttribute('aria-expanded','false'));}));
    function menu(open){$('siteNavLinks').classList.toggle('open',open);$('siteNavMenu').setAttribute('aria-expanded',String(open));$('siteNavMenu').textContent=open?'Fechar':'Menu';}
    $('siteNavMenu').addEventListener('click',()=>menu($('siteNavMenu').getAttribute('aria-expanded')!=='true'));
    $('siteNavLinks').querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>menu(false)));
    document.addEventListener('keydown',e=>{if(e.key==='Escape'){menu(false);$('shareFallback').hidden=true;}});
    function currentURL(candidate){
      const u=new URL(location.protocol==='http:'||location.protocol==='https:'?location.href:meta.canonical);
      if(candidate){u.search='';u.hash=`candidato-${candidate}`;}else u.search=serializeState(state);
      return u.href;
    }
    async function share(candidate){
      const value=currentURL(candidate);
      try{if(!navigator.clipboard)throw new Error('Clipboard unavailable');await navigator.clipboard.writeText(value);$('shareStatus').textContent='Endereço copiado.';$('shareFallback').hidden=true;}
      catch(_){$('shareFallback').hidden=false;$('shareURL').value=value;$('shareURL').focus();$('shareURL').select();$('shareStatus').textContent='Copie o endereço abaixo.';}
    }
    $('shareFilters').setAttribute('data-eef-query-share','');
    document.querySelectorAll('[data-share-candidate]').forEach(b=>b.addEventListener('click',()=>share(b.dataset.shareCandidate)));
    document.querySelectorAll('.portrait img').forEach(img=>{const fallback=()=>{img.hidden=true;};img.addEventListener('error',fallback);if(img.complete&&!img.naturalWidth)fallback();});
    let displacedFilters=null;
    const linkNotice=$('eefDeepLinkNotice'),restoreButton=$('eefRestoreQuery');
    function hideLinkNotice(){if(linkNotice)linkNotice.hidden=true;displacedFilters=null;}
    function revealDeepLink(){
    if(window.EEFQueryUI)return window.EEFQueryUI.reveal(location.hash,true);
    if(document.getElementById('eefEditionQueryData'))return;
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
      if(root.EEFQueryUI)return;
      if(!displacedFilters)return;
      const previous=displacedFilters;hideLinkNotice();state=previous;
      history.pushState(null,'',location.pathname);lastLegacySearch='';
      render();search.focus({preventScroll:true});search.scrollIntoView({block:'center'});
    });
    const commonValid=Object.freeze({edition_id:document.body.dataset.global03Edition||'2026-sp-federais',parties:valid.parties.slice(),topics:valid.topics.slice(),statuses:valid.statuses.slice(),regions:[],mandates:[''],histories:[''],modes:['any','all'],orders:['daily','alphabetical'],semantic:'documented_topic',aliases:ALIASES});
    function commonSnapshot(){return {edition_id:commonValid.edition_id,q:state.q,parties:state.parties.slice().sort(),topics:state.topics.slice().sort(),status:state.status,mandate:'',history:'',region:'',mode:state.mode==='todos'?'all':'any',order:state.order==='alfabetica'?'alphabetical':'daily',semantic:'documented_topic'};}
    function applyCommon(s){
      clearTimeout(timer);
      if(s.edition_id!==commonValid.edition_id||s.mandate||s.history||s.region||s.semantic!=='documented_topic'||s.parties.some(x=>!commonValid.parties.includes(x))||s.topics.some(x=>!commonValid.topics.includes(x))||s.status&&!commonValid.statuses.includes(s.status)||!commonValid.modes.includes(s.mode)||!commonValid.orders.includes(s.order))throw new TypeError('Critério não disponível nesta edição de São Paulo');
      state={parties:s.parties.slice(),topics:s.topics.slice(),status:s.status,q:s.q,mode:s.mode==='all'?'todos':'qualquer',order:s.order==='alphabetical'?'alfabetica':'diaria',ignored:[]};hideLinkNotice();render();return commonSnapshot();
    }
    function importLegacy(searchValue){state=parseState(searchValue,valid);lastLegacySearch=searchValue;hideLinkNotice();render();return commonSnapshot();}
    root.EEFEditionQuery=Object.freeze({valid:commonValid,snapshot:commonSnapshot,applyState:applyCommon,importLegacy,legacyDialect:'SP'});
    root.EEFSPQuery=Object.freeze({apply:render,reveal:revealDeepLink});
    render();revealDeepLink();
  }
  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',boot,{once:true});else boot();
})(typeof window !== 'undefined' ? window : globalThis);

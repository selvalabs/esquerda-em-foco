/* Common query controller. Criteria live only in this document's memory.
 * History entries carry opaque keys, never candidates, parties or search text.
 * Only an explicit share action serializes a query into a link. */
(function () {
  'use strict';
  const core=window.EEFGlobal, adapter=window.EEFEditionQuery;
  const $=id=>document.getElementById(id), configNode=$('eefEditionQueryData'), tools=$('eefQueryTools');
  if(!core||!adapter||!configNode||!tools||window.EEFQueryUI)return;
  let config;try{config=JSON.parse(configNode.textContent);}catch{return;}
  if(adapter.valid?.edition_id!==config.edition_id)return;
  const valid=adapter.valid, partyHost=$('eefQueryPartyHost'), partyBlock=$('eefQueryParties');
  const summary=$('eefQuerySummary'), notice=$('eefQueryNotice'), shareButton=$('eefShareQuery');
  const dialog=$('eefQueryShareDialog'), shareURL=$('eefQueryShareUrl'), shareStatus=$('eefQueryShareStatus');
  const historyMemory=new Map(), prefix=globalThis.crypto?.randomUUID?.()||String(Math.random());
  const partyCounts=new Map(), partyButtons=new Map();
  const filterControls='#searchInput,#partyFilter,#registrationFilter,#trajectoryFilter,#statusFilter,#mandateFilter,#historyFilter,#regionFilter,#topicMode,#orderFilter,input[name="pauta-mode"]';
  const filterButtons='[data-party-filter],[data-topic-filter],[data-pauta-topic],[data-pauta-remove],[data-theme],[data-pauta-clear],[data-pauta-reset],[data-clear-filters],#clearTopics,#clearFilters,#resetFilters,#emptyReset,.selected-chip';
  let sequence=0, displaced=null, sharePayload=null, opener=null, shareToken=0, typing=false, lastState=null;
  const snapshot=()=>adapter.snapshot(), copy=v=>JSON.parse(JSON.stringify(v));
  const localURL=()=>location.pathname+location.search+location.hash;
  const base=()=>new URL('./',location.href).href;
  const defaults=()=>({...core.emptyQuery(valid.edition_id),mode:valid.modes?.[0]||'any',order:valid.orders?.[0]||'daily',semantic:valid.semantic||null});
  const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const empty=s=>!s.q&&!s.parties.length&&!s.topics.length&&!s.status&&!s.mandate&&!s.history&&!s.region&&s.order!=='alphabetical';
  document.querySelectorAll('article.candidate').forEach(c=>{const p=c.dataset.party;if(p)partyCounts.set(p,(partyCounts.get(p)||0)+1);});
  function showNotice(text){notice.textContent=text;notice.hidden=!text;}
  function setState(raw){
    const parsed=core.normalizeQuery(raw,valid);
    if(parsed.ignored.length)throw new TypeError('Critério não disponível nesta edição');
    adapter.applyState(parsed.state);lastState=copy(snapshot());sync();
  }
  function memoryEntry(){const entry=historyMemory.get(history.state?.eefQueryEntry);return entry?.url===localURL()?entry:null;}
  function remember(push=false,url=localURL()){
    const key=prefix+':'+(++sequence), entry={url,state:copy(snapshot()),displaced:copy(displaced)};
    historyMemory.set(key,entry);
    try{history[push?'pushState':'replaceState']({...((history.state&&typeof history.state==='object')?history.state:{}),eefQueryEntry:key},'',url);}
    catch{/* File previews or restricted history retain the working in-memory query. */}
    lastState=copy(entry.state);
  }
  function renderParties(s){
    if(config.party_ui==='native'){partyBlock.hidden=true;return;}
    partyBlock.hidden=false;
    if(!partyButtons.size){
      for(const p of valid.parties){
        const b=document.createElement('button');b.type='button';b.className='eef-query-party';b.dataset.eefParty=p;
        b.append(document.createTextNode(p==='PCDOB'?'PCdoB':p));
        const count=document.createElement('small');count.textContent=String(partyCounts.get(p)||0);b.append(count);
        b.setAttribute('aria-label',`${p}: ${partyCounts.get(p)||0} fichas no total da edição`);
        partyButtons.set(p,b);partyHost.append(b);
      }
    }
    partyButtons.forEach((b,p)=>b.setAttribute('aria-pressed',String(s.parties.includes(p))));
    $('eefQueryAllParties').disabled=!s.parties.length;
    $('eefQueryPartyLabel').textContent=s.parties.length?`Partidos · ${s.parties.join(', ')}`:'Partidos · todos';
  }
  function sync(){
    const s=snapshot(), parts=[];
    renderParties(s);
    if(s.q)parts.push(`Busca: ${s.q}`);
    if(s.parties.length)parts.push(s.parties.join(' + '));
    if(s.topics.length)parts.push(`${s.topics.length} tema${s.topics.length===1?'':'s'} · ${s.mode==='all'?'todos':'pelo menos um'}`);
    if(s.status)parts.push('registro');if(s.mandate)parts.push('mandato');if(s.history)parts.push('histórico');if(s.region)parts.push(s.region);
    if(s.order==='alphabetical')parts.push('ordem alfabética');
    summary.textContent=parts.length?parts.join(' · '):'Nenhum filtro ativo. Todas as fichas estão disponíveis.';
    shareButton.disabled=empty(s);$('eefQueryClear').disabled=empty(s);
  }
  function hideDisplaced(){displaced=null;if($('eefDeepLinkNotice'))$('eefDeepLinkNotice').hidden=true;}
  function showDisplaced(){
    if(!$('eefDeepLinkNotice'))return;
    $('eefDeepLinkNotice').hidden=!displaced;
    if(displaced)$('eefDeepLinkMessage').textContent='Os filtros foram suspensos para abrir o conteúdo do link. Você pode restaurar sua consulta anterior.';
  }
  function commitUser(isTyping=false){
    const s=snapshot();
    if(!same(s,lastState)){
      hideDisplaced();showNotice('');
      // A typing burst occupies one history step. The snapshot itself never leaves RAM.
      remember(!(isTyping&&typing),location.pathname);typing=isTyping;
    }
    sync();
  }
  function reveal(hash,scroll=true){
    let target;try{target=$(decodeURIComponent(hash.replace(/^#/,'')));}catch{return;}
    if(!target)return;
    const card=target.closest('article.candidate'), section=target.closest('.party-section,.party-group');
    if(card?.dataset.eefHeld)return;
    if(card?.hidden||section?.hidden){
      displaced=copy(snapshot());setState(defaults());showDisplaced();remember();
    }
    let parent=target;while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
    if(scroll)requestAnimationFrame(()=>{
      if(!target.matches('a,button,input,select,textarea,summary,[tabindex]'))target.setAttribute('tabindex','-1');
      target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'instant'});
    });
    sync();
  }
  function route(){
    typing=false;
    const entry=memoryEntry();
    if(entry){setState(entry.state);displaced=copy(entry.displaced);showDisplaced();reveal(location.hash);return;}
    const parsed=core.parseQuery(location.hash,valid);
    if(parsed.kind==='query'){
      try{setState(parsed.state);hideDisplaced();showNotice('Consulta do link aplicada nesta edição.');remember();}
      catch(e){showNotice(e.message+'. A consulta atual foi preservada.');}return;
    }
    if(parsed.kind==='invalid'&&location.hash.startsWith('#eef=query')){
      showNotice(parsed.reason+'. A consulta atual foi preservada.');return;
    }
    if(location.search&&adapter.legacyDialect){
      try{
        const legacy=core.importLegacyQuery(location.search,valid,adapter.legacyDialect);
        setState(legacy.state);showNotice(legacy.ignored.length?'Algum critério do endereço antigo não existe nesta edição e foi ignorado.':'');
      }catch(e){showNotice(e.message+'. A consulta atual foi preservada.');}
    }
    reveal(location.hash);remember();sync();
  }
  // setState is also used for imports; user mutations compare against the previous checkpoint.
  function userChange(raw){const before=copy(lastState);try{setState(raw);lastState=before;commitUser();}catch(e){showNotice(e.message);}}
  partyHost.addEventListener('click',e=>{
    const b=e.target.closest('[data-eef-party]');if(!b)return;
    const s=snapshot(),p=b.dataset.eefParty;
    userChange({...s,parties:s.parties.includes(p)?s.parties.filter(x=>x!==p):s.parties.concat(p)});
  });
  $('eefQueryAllParties').addEventListener('click',()=>userChange({...snapshot(),parties:[]}));
  $('eefQueryClear').addEventListener('click',()=>userChange(defaults()));
  $('eefRestoreQuery')?.addEventListener('click',()=>{
    if(!displaced)return;
    const previous=copy(displaced);setState(previous);hideDisplaced();remember(true,location.pathname);sync();
    $('searchInput').focus({preventScroll:true});$('searchInput').scrollIntoView({block:'center'});
  });
  document.addEventListener('input',e=>{if(e.target.matches(filterControls))commitUser(e.target.id==='searchInput');});
  document.addEventListener('change',e=>{if(e.target.matches(filterControls))commitUser();});
  document.addEventListener('click',e=>{if(e.target.closest(filterButtons))commitUser();});
  document.addEventListener('eef:query-render',sync);
  function closeMenus(){
    $('global-edition-menu')?.removeAttribute('open');$('siteNav')?.classList.remove('is-open');
    $('siteNavMenu')?.setAttribute('aria-expanded','false');
  }
  function openShare(button){
    let url;try{url=core.queryLink(base(),snapshot(),valid);}catch(e){showNotice(e.message);return;}
    shareToken++;opener=button;sharePayload={title:'Esquerda em Foco',text:`Consulta em ${config.label} — critérios escolhidos para leitura.`,url};
    shareURL.value=url;shareStatus.textContent='';
    $('eefQueryWhatsapp').href='https://wa.me/?text='+encodeURIComponent(sharePayload.text+'\n'+url);
    $('eefQueryNative').hidden=typeof navigator.share!=='function';$('eefQueryNative').disabled=false;
    closeMenus();dialog.showModal();$('eefQueryShareClose').focus();
  }
  document.addEventListener('click',e=>{const b=e.target.closest('[data-eef-query-share]');if(b){e.preventDefault();openShare(b);}});
  $('eefQueryShareClose').addEventListener('click',()=>dialog.close());
  dialog.addEventListener('close',()=>{shareToken++;sharePayload=null;opener?.isConnected&&opener.focus({preventScroll:true});});
  $('eefQueryCopy').addEventListener('click',async()=>{
    if(!sharePayload)return;const token=shareToken,payload=sharePayload;
    try{if(!navigator.clipboard?.writeText)throw new Error();await navigator.clipboard.writeText(payload.url);if(token===shareToken)shareStatus.textContent='Link copiado.';}
    catch{if(token!==shareToken)return;shareStatus.textContent='Não foi possível copiar automaticamente. Selecione o link e use Copiar.';shareURL.focus();shareURL.select();}
  });
  $('eefQueryNative').addEventListener('click',async()=>{
    if(!sharePayload)return;const token=shareToken,b=$('eefQueryNative');b.disabled=true;
    try{await navigator.share(sharePayload);if(token===shareToken)shareStatus.textContent='Conteúdo entregue ao compartilhador do aparelho. Confirme o envio no aplicativo.';}
    catch(e){if(token===shareToken)shareStatus.textContent=e?.name==='AbortError'?'Compartilhamento cancelado ou sem destino disponível.':'Compartilhamento indisponível. Use Copiar link ou WhatsApp.';}
    finally{if(token===shareToken)b.disabled=false;}
  });
  window.addEventListener('hashchange',route,true);window.addEventListener('popstate',route,true);
  window.EEFQueryUI=Object.freeze({snapshot,shareUrl:()=>core.queryLink(base(),snapshot(),valid),applyHash:route,reveal});
  tools.hidden=false;document.documentElement.classList.add('eef-global04-query-ready');
  if(config.party_ui!=='native')partyBlock.open=!matchMedia('(max-width:760px)').matches;
  route();sync();
})();

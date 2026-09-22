/* GLOBAL-04 L02: common query transport/UI. No storage, analytics or political inference. */
(function(){
  'use strict';
  const core=window.EEFGlobal, adapter=window.EEFEditionQuery;
  const configNode=document.getElementById('eefEditionQueryData');
  const tools=document.getElementById('eefQueryTools');
  if(!core||!adapter||!configNode||!tools)return;
  let config;try{config=JSON.parse(configNode.textContent);}catch{return;}
  if(!adapter.valid||adapter.valid.edition_id!==config.edition_id)return;
  const $=id=>document.getElementById(id);
  const partyHost=$('eefQueryPartyHost'),partyBlock=$('eefQueryParties');
  const summary=$('eefQuerySummary'),notice=$('eefQueryNotice'),shareButton=$('eefShareQuery');
  const shareDialog=$('eefQueryShareDialog'),shareURL=$('eefQueryShareUrl'),shareStatus=$('eefQueryShareStatus');
  let sharePayload=null,lastSearch=location.search,opener=null,syncQueued=false;
  const partyCounts=new Map();
  document.querySelectorAll('article.candidate').forEach(card=>{
    const p=card.dataset.party;if(p)partyCounts.set(p,(partyCounts.get(p)||0)+1);
  });
  function base(){return new URL('./',location.href).href;}
  function empty(s){return !s.q&&!s.parties.length&&!s.topics.length&&!s.status&&!s.mandate&&!s.history&&!s.region&&!(s.order==='alphabetical');}
  function activeParts(s){
    const out=[];
    if(s.q)out.push('busca');
    if(s.parties.length)out.push(`${s.parties.length} partido${s.parties.length===1?'':'s'}`);
    if(s.topics.length)out.push(`${s.topics.length} tema${s.topics.length===1?'':'s'} · ${s.mode==='all'?'todos':'qualquer'}`);
    if(s.status)out.push('situação');if(s.mandate)out.push('mandato');if(s.history)out.push('histórico');if(s.region)out.push('localidade');
    if(s.order==='alphabetical')out.push('ordem alfabética');return out;
  }
  function snapshot(){return adapter.snapshot();}
  function showNotice(text){notice.textContent=text;notice.hidden=!text;}
  function renderParties(s){
    if(config.party_ui==='native'||!partyHost||!adapter.valid.parties?.length){if(partyBlock)partyBlock.hidden=true;return;}
    partyBlock.hidden=false;partyHost.replaceChildren();
    for(const p of adapter.valid.parties){
      const b=document.createElement('button');b.type='button';b.className='eef-query-party';b.dataset.eefParty=p;b.setAttribute('aria-pressed',String(s.parties.includes(p)));
      b.append(document.createTextNode(p));const n=document.createElement('small');n.textContent=String(partyCounts.get(p)||0);n.setAttribute('aria-label',`${partyCounts.get(p)||0} registros no total desta edição`);b.append(n);partyHost.append(b);
    }
  }
  function sync(){
    syncQueued=false;let s;try{s=snapshot();}catch{return;}
    renderParties(s);const parts=activeParts(s);summary.textContent=parts.length?`Consulta atual · ${parts.join(' · ')}`:'Consulta atual · sem critérios ativos';
    shareButton.disabled=empty(s);
  }
  function schedule(){if(syncQueued)return;syncQueued=true;setTimeout(sync,0);}
  function stripLegacySearch(){
    if(!location.search)return;
    history.replaceState(history.state,'',location.pathname+location.hash);lastSearch='';
  }
  function applyState(state,source){
    try{adapter.applyState(state,{source});showNotice(source==='link'?'Consulta do link aplicada nesta edição.':'');sync();return true;}
    catch(e){showNotice(e?.message||'Não foi possível aplicar esta consulta.');return false;}
  }
  function route(){
    const parsed=core.parseQuery(location.hash,adapter.valid);
    if(parsed.kind==='query'){applyState(parsed.state,'link');return;}
    if(parsed.kind==='invalid'&&location.hash.startsWith('#eef=query')){showNotice(parsed.reason+'. A consulta atual foi preservada.');return;}
    if(location.search!==lastSearch&&adapter.importLegacy){
      try{const state=adapter.importLegacy(location.search);if(state)applyState(state,'legacy');}
      catch(e){showNotice(e?.message||'Alguns critérios antigos não puderam ser aplicados.');}
      lastSearch=location.search;
    }
    schedule();
  }
  if(config.party_ui!=='native')partyHost?.addEventListener('click',e=>{
    const b=e.target.closest('[data-eef-party]');if(!b)return;
    const s=snapshot(),p=b.dataset.eefParty,next=s.parties.includes(p)?s.parties.filter(x=>x!==p):s.parties.concat(p);
    if(applyState({...s,parties:next},'user')){stripLegacySearch();showNotice('');}
  });
  document.addEventListener('input',e=>{if(e.target.closest('[data-global04-query]'))return;schedule();stripLegacySearch();},{capture:false});
  document.addEventListener('change',e=>{if(e.target.closest('[data-global04-query]'))return;schedule();stripLegacySearch();},{capture:false});
  document.addEventListener('click',e=>{
    if(e.target.closest('[data-eef-query-share]')){e.preventDefault();openShare(e.target.closest('[data-eef-query-share]'));return;}
    if(e.target.closest('[data-party-filter],[data-topic-filter],[data-pauta-topic],[data-theme],[data-pauta-clear],[data-pauta-reset],[data-clear-filters],#clearTopics,#clearFilters,#resetFilters'))setTimeout(()=>{schedule();stripLegacySearch();},0);
  });
  function shareData(url){return {title:'Esquerda em Foco',text:`Consulta em ${config.label} no Esquerda em Foco — critérios escolhidos para consulta.`,url};}
  function openShare(button){
    let url;try{url=core.queryLink(base(),snapshot(),adapter.valid);}catch(e){showNotice(e?.message||'Não foi possível preparar o link.');return;}
    sharePayload=shareData(url);opener=button;shareURL.value=url;shareStatus.textContent='';$('eefQueryWhatsapp').href='https://wa.me/?text='+encodeURIComponent(sharePayload.text+'\n'+url);
    $('eefQueryNative').hidden=typeof navigator.share!=='function';$('eefQueryNative').disabled=false;shareDialog.showModal();$('eefQueryShareClose').focus();
  }
  $('eefQueryShareClose').addEventListener('click',()=>shareDialog.close());
  shareDialog.addEventListener('close',()=>{sharePayload=null;if(opener?.isConnected)opener.focus({preventScroll:true});});
  $('eefQueryCopy').addEventListener('click',async()=>{
    if(!sharePayload)return;try{if(!navigator.clipboard?.writeText)throw new Error();await navigator.clipboard.writeText(sharePayload.url);shareStatus.textContent='Link copiado.';}
    catch{shareStatus.textContent='Não foi possível copiar automaticamente. Selecione o link e use Copiar.';shareURL.focus();shareURL.select();}
  });
  $('eefQueryNative').addEventListener('click',async()=>{
    if(!sharePayload)return;const b=$('eefQueryNative');b.disabled=true;
    try{await navigator.share(sharePayload);shareStatus.textContent='Conteúdo entregue ao compartilhador do aparelho. Confirme o envio no aplicativo.';}
    catch(e){shareStatus.textContent=e?.name==='AbortError'?'Compartilhamento cancelado ou sem destino disponível.':'Compartilhamento nativo indisponível. Use Copiar link ou WhatsApp.';}
    finally{b.disabled=false;}
  });
  window.addEventListener('hashchange',route);window.addEventListener('popstate',route);
  window.EEFQueryUI=Object.freeze({snapshot,shareUrl:()=>core.queryLink(base(),snapshot(),adapter.valid),applyHash:route});
  tools.hidden=false;document.documentElement.classList.add('eef-global04-query-ready');
  route();sync();
})();

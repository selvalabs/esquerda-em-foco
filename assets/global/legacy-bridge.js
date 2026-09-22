/* Legacy SC links: fixed, allowlisted destinations; no storage or automatic share. */
(function(){
  'use strict';
  const alias=document.getElementById('global-alias-target');
  if(alias){
    const u=new URL(alias.getAttribute('href'),location.href);
    if(u.origin===location.origin){u.search=location.search;u.hash=location.hash;location.replace(u.href);}
    return;
  }
  const node=document.getElementById('global-legacy-data');
  if(!node||!window.EEFGlobal)return;
  let fixtures;try{fixtures=JSON.parse(node.textContent);}catch{return;}
  function bridge(){
    const base=new URL('./',location.href).href;
    const target=EEFGlobal.legacyRootTarget(location.hash,fixtures,base);
    if(target)location.replace(target);
  }
  addEventListener('hashchange',bridge);bridge();
})();

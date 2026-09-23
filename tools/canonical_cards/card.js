/* Evidence focus within one original card. No query state, storage or network. */
(() => {
 'use strict';
 document.querySelectorAll('[data-canonical-card]').forEach(card => {
  const proof=card.querySelector('.cc-proof'),controls=proof?.querySelector('.cc-evidence-controls');
  if(!controls)return;
  const items=[...proof.querySelectorAll('[data-cc-evidence]')],buttons=[...controls.querySelectorAll('[data-cc-topic]')];
  const status=proof.querySelector('.cc-evidence-status');
  function filter(topic=''){
   let count=0;
   items.forEach(item=>{item.hidden=!!topic&&!item.dataset.ccTopics.split(' ').includes(topic);if(!item.hidden)count++;});
   buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.ccTopic===topic)));
   status.textContent=topic?`${count} registro${count===1?'':'s'} relacionado${count===1?'':'s'}. As outras evidências continuam disponíveis em “Ver todo o contexto”.`:'';
  }
  controls.hidden=false;
  controls.addEventListener('click',e=>{
   const b=e.target.closest('[data-cc-topic],[data-cc-reset]');if(!b)return;
   filter(b.hasAttribute('data-cc-reset')||b.getAttribute('aria-pressed')==='true'?'':b.dataset.ccTopic);
  });
  proof.addEventListener('toggle',()=>{if(!proof.open)filter();});
  card.addEventListener('click',e=>{
   const a=e.target.closest('a[href^="#"]');if(!a)return;
   let target;try{target=document.getElementById(decodeURIComponent(a.hash.slice(1)));}catch{return;}
   if(target?.closest('.cc-proof')===proof){filter();proof.open=true;}
  });
 });
})();

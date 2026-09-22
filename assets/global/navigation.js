/* Progressive menu enhancement. No network, cookies, location storage or metrics. */
(function(){
  'use strict';
  const picker=document.querySelector('#global-edition-menu');
  if(!picker)return;
  const summary=picker.querySelector('summary'),toggle=document.getElementById('siteNavMenu');
  function close(focus=false){if(!picker.open)return;picker.open=false;if(focus)summary.focus({preventScroll:true});}
  function closeLocal(){if(toggle?.getAttribute('aria-expanded')==='true')toggle.click();}
  picker.addEventListener('toggle',()=>{if(picker.open)closeLocal();});
  toggle?.addEventListener('click',()=>{if(toggle.getAttribute('aria-expanded')==='true')close();});
  document.addEventListener('keydown',event=>{if(event.key==='Escape'&&picker.open){event.preventDefault();close(true);}});
  document.addEventListener('click',event=>{if(picker.open&&!picker.contains(event.target))close();});
  picker.addEventListener('click',event=>{if(event.target.closest('a'))close();});
  document.addEventListener('focusin',event=>{if(picker.open&&!picker.contains(event.target))close();});
  window.addEventListener('pageshow',()=>close());
})();

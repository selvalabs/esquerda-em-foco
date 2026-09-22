/* Progressive enhancement only; links and menus remain usable without JS. */
(function(){
  'use strict';
  document.querySelectorAll('.eef-global-shell').forEach(shell=>{
    shell.addEventListener('keydown',event=>{
      if(event.key==='Escape'){
        const menu=shell.querySelector('details[open]');
        if(menu){menu.open=false;menu.querySelector('summary').focus();event.stopPropagation();}
      }
    });
  });
})();

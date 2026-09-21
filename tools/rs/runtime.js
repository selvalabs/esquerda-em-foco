(() => {
  'use strict';
  const normalize = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
  const search = document.getElementById('search');
  const counter = document.getElementById('resultCount');
  const empty = document.getElementById('emptyResults');
  const cards = Array.from(document.querySelectorAll('article.candidate'));
  const sections = Array.from(document.querySelectorAll('.party-section'));
  const nav = document.querySelector('.party-nav');
  const progress = document.getElementById('progressBar');
  const menu = document.querySelector('.site-nav');
  const toggle = document.querySelector('.site-nav__toggle');
  const links = document.querySelector('.site-nav__links');
  const epoch = Date.UTC(2026, 8, 21);
  const formatter = new Intl.DateTimeFormat('en-US', {timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'});
  const dayIndex = () => {
    const parts = Object.fromEntries(formatter.formatToParts(new Date()).filter(p=>p.type!=='literal').map(p=>[p.type,p.value]));
    return Math.max(0, Math.floor((Date.UTC(+parts.year,+parts.month-1,+parts.day)-epoch)/86400000));
  };
  const compare = (a,b) => normalize(a).localeCompare(normalize(b),'pt-BR',{sensitivity:'base'});
  const rotate = (items,offset) => items.length ? items.slice(offset%items.length).concat(items.slice(0,offset%items.length)) : items;
  let appliedDay = -1;
  function applyRotation() {
    const day = dayIndex();
    if (day===appliedDay) return;
    const sorted = sections.slice().sort((a,b)=>compare(a.dataset.partySection,b.dataset.partySection));
    rotate(sorted,day).forEach(section=>section.parentElement.appendChild(section));
    sections.forEach(section=>{
      const list = section.querySelector('.candidate-list');
      const items = Array.from(list.querySelectorAll('article.candidate')).sort((a,b)=>compare(a.querySelector('h3').textContent,b.querySelector('h3').textContent)||compare(a.id,b.id));
      rotate(items,day).forEach(card=>list.appendChild(card));
    });
    if(nav){
      const items = Array.from(nav.querySelectorAll('[data-nav-party]')).sort((a,b)=>compare(a.dataset.navParty,b.dataset.navParty));
      rotate(items,day).forEach(item=>nav.appendChild(item));
    }
    appliedDay=day; document.documentElement.dataset.rotationDay=String(day);
  }
  function filter(){
    const query=normalize(search ? search.value : '');
    let total=0;
    cards.forEach(card=>{
      const visible=!query || normalize(card.dataset.search+' '+card.textContent).includes(query);
      card.hidden=!visible; if(visible)total++;
    });
    sections.forEach(section=>{
      const visible=Array.from(section.querySelectorAll('.candidate')).filter(c=>!c.hidden).length;
      section.hidden=visible===0;
      const item=nav && Array.from(nav.querySelectorAll('[data-nav-party]')).find(a=>a.dataset.navParty===section.dataset.partySection);
      if(item){item.hidden=!visible; const count=item.querySelector('small');if(count)count.textContent=String(visible).padStart(2,'0');}
    });
    if(counter)counter.textContent=total+(total===1?' resultado':' resultados');
    if(empty)empty.hidden=total!==0;
  }
  function closeMenu(restoreFocus=false){
    if(!menu || !toggle)return;
    menu.classList.remove('is-open');toggle.setAttribute('aria-expanded','false');
    if(restoreFocus)toggle.focus();
  }
  if(toggle && menu){
    toggle.addEventListener('click',()=>{
      const open=toggle.getAttribute('aria-expanded')!=='true';
      menu.classList.toggle('is-open',open);toggle.setAttribute('aria-expanded',String(open));
    });
    document.addEventListener('click',event=>{if(!menu.contains(event.target))closeMenu();});
    document.addEventListener('keydown',event=>{if(event.key==='Escape' && toggle.getAttribute('aria-expanded')==='true')closeMenu(true);});
    if(links)links.addEventListener('click',event=>{if(event.target.closest('a'))closeMenu();});
    window.addEventListener('resize',()=>{if(window.innerWidth>760)closeMenu();},{passive:true});
  }
  function revealHash(){
    let id;
    try{id=decodeURIComponent(location.hash.slice(1));}catch{return;}
    if(!id)return;
    const target=document.getElementById(id);if(!target)return;
    if(target.matches('.candidate') && target.hidden && search){search.value='';filter();}
    if(target.tagName==='DETAILS')target.open=true;
    let parent=target.parentElement;
    while(parent){if(parent.tagName==='DETAILS')parent.open=true;parent=parent.parentElement;}
    requestAnimationFrame(()=>target.scrollIntoView({block:'start',behavior:'instant'}));
  }
  function updateProgress(){if(progress){const h=document.documentElement.scrollHeight-window.innerHeight;progress.style.width=(h>0?100*window.scrollY/h:0)+'%';}}
  applyRotation();filter();
  if(search)search.addEventListener('input',filter);
  if(counter){counter.setAttribute('role','status');counter.setAttribute('aria-live','polite');counter.setAttribute('aria-atomic','true');}
  window.addEventListener('hashchange',revealHash);
  window.addEventListener('scroll',updateProgress,{passive:true});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)applyRotation();});
  window.setInterval(applyRotation,60000);
  revealHash();updateProgress();
})();

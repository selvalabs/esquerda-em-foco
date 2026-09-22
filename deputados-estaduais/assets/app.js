/* No federal dependencies, tracking, remote scripts or shared application state. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const cards = Array.from(document.querySelectorAll('.candidate'));
  const sections = Array.from(document.querySelectorAll('.party-section'));
  const search = $('#searchInput'), party = $('#partyFilter'), trajectory = $('#trajectoryFilter'), registration = $('#registrationFilter');
  const normalize = (v) => String(v || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const index = new Map(cards.map(c => [c, normalize(c.dataset.search)]));
  const parties = new Set();
  const knownParties=[...new Set(cards.map(c=>c.dataset.party).filter(Boolean))].sort();
  const knownStatuses=registration?[...registration.options].map(o=>o.value).filter(Boolean):[];
  function apply() {
    const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const c of cards) {
      const okParty = !parties.size || parties.has(c.dataset.party);
      const okTrajectory = !trajectory.value || (trajectory.value === 'first' && c.dataset.rookie === 'true') || (trajectory.value === 'mandate' && c.dataset.currentOffice === 'true') || (trajectory.value === 'history' && c.dataset.rookie !== 'true');
      const okRegistration = !registration || !registration.value || c.dataset.registration === registration.value;
      c.hidden = !(okParty && okTrajectory && okRegistration && terms.every(t => index.get(c).includes(t)));
      if (!c.hidden) count++;
    }
    for (const section of sections) {
      const n = section.querySelectorAll('.candidate:not([hidden])').length;
      section.hidden = !n;
      section.querySelector('.party-count').textContent = `${n} ${n === 1 ? 'candidatura' : 'candidaturas'}`;
    }
    $('#resultCount').textContent = `${count} de ${cards.length}`;
    $('#emptyState').hidden = count > 0;
  }
  function reset() { search.value = ''; parties.clear(); if(party)party.value=''; trajectory.value = ''; if (registration) registration.value = ''; apply(); }
  search.addEventListener('input', apply);
  party?.addEventListener('change', () => {parties.clear();if(party.value)parties.add(party.value);apply();});
  trajectory.addEventListener('change', apply);
  if (registration) registration.addEventListener('change', apply);
  $('#resetFilters').addEventListener('click', reset);
  $('#emptyReset').addEventListener('click', () => { reset(); search.focus(); });
  const nav = $('#siteNav'), menu = $('#siteNavMenu');
  function closeMenu(focus = false) {
    nav.classList.remove('is-open'); menu.setAttribute('aria-expanded', 'false'); menu.setAttribute('aria-label', 'Abrir menu');
    if (focus) menu.focus();
  }
  menu.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    menu.setAttribute('aria-expanded', String(open)); menu.setAttribute('aria-label', open ? 'Fechar menu' : 'Abrir menu');
  });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && nav.classList.contains('is-open')) closeMenu(true); });
  document.addEventListener('click', e => { if (!nav.contains(e.target)) closeMenu(); });
  document.querySelectorAll('.site-nav a[href^="#"]').forEach(link => link.addEventListener('click', () => {
    const target = document.getElementById(link.hash.slice(1));
    if (target && target.tagName === 'DETAILS') target.open = true;
    closeMenu();
  }));
  document.querySelectorAll('.party-nav a').forEach(link => link.addEventListener('click', () => {
    const target = document.getElementById(link.hash.slice(1));
    if (target && target.hidden) reset();
  }));
  function measure() {
    const navHeight = nav.getBoundingClientRect().height;
    const toolbarHeight = $('.toolbar-wrap').getBoundingClientRect().height;
    document.documentElement.style.setProperty('--top-nav-h', `${navHeight}px`);
    document.documentElement.style.setProperty('--state-toolbar-h', `${toolbarHeight}px`);
    if (window.innerWidth > 760) closeMenu();
  }
  const ro = new ResizeObserver(measure); ro.observe($('.toolbar-wrap'));
  window.addEventListener('resize', measure, {passive: true}); measure();
  for (const img of document.querySelectorAll('.candidate-photo')) {
    img.addEventListener('error', () => img.classList.add('is-broken'));
    if (img.complete && !img.naturalWidth) img.classList.add('is-broken');
  }
  function revealHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    const target = document.getElementById(id);
    if (!target) return;
    if (target.classList.contains('candidate')) {
      if (target.hidden) reset();
      requestAnimationFrame(() => target.scrollIntoView({block: 'start'}));
    }
    if (target.tagName === 'DETAILS') target.open = true;
  }
  window.addEventListener('hashchange', revealHash);
  revealHash();
  let ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => {
      const total = document.documentElement.scrollHeight - window.innerHeight;
      const bar = $('.progress');
      if (bar) bar.style.width = `${total > 0 ? Math.min(100, window.scrollY / total * 100) : 0}%`;
      ticking = false;
    });
  }, {passive: true});
  const queryValid=Object.freeze({edition_id:'2026-sc-estaduais',parties:knownParties,topics:[],statuses:knownStatuses,regions:[],mandates:['','true'],histories:['','true','false'],modes:['any'],orders:['daily'],semantic:null});
  function snapshot(){
    return {edition_id:queryValid.edition_id,q:search.value.trim(),parties:[...parties].sort(),topics:[],status:registration?.value||'',mandate:trajectory.value==='mandate'?'true':'',history:trajectory.value==='first'?'false':trajectory.value==='history'?'true':'',region:'',mode:'any',order:'daily',semantic:null};
  }
  function applyState(s){
    if(s.edition_id!==queryValid.edition_id||s.topics.length||s.region||s.order!=='daily'||s.mode!=='any'||s.semantic!==null)throw new TypeError('Consulta incompatível com SC/Estaduais');
    if(s.mandate&&s.history)throw new TypeError('Mandato e trajetória não podem ser combinados neste controle');
    if(s.mandate&&!queryValid.mandates.includes(s.mandate)||s.history&&!queryValid.histories.includes(s.history)||s.status&&!knownStatuses.includes(s.status)||s.parties.some(x=>!knownParties.includes(x)))throw new TypeError('Critério não disponível nesta edição');
    search.value=s.q;parties.clear();s.parties.forEach(x=>parties.add(x));if(party)party.value=s.parties.length===1?s.parties[0]:'';
    if(registration)registration.value=s.status;trajectory.value=s.mandate==='true'?'mandate':s.history==='false'?'first':s.history==='true'?'history':'';apply();return snapshot();
  }
  window.EEFEditionQuery=Object.freeze({valid:queryValid,snapshot,applyState});
})();

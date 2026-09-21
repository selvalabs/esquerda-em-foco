/* No federal dependencies, tracking, remote scripts or shared application state. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const cards = Array.from(document.querySelectorAll('.candidate'));
  const sections = Array.from(document.querySelectorAll('.party-section'));
  const search = $('#searchInput'), party = $('#partyFilter'), trajectory = $('#trajectoryFilter'), registration = $('#registrationFilter');
  const normalize = (v) => String(v || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  const index = new Map(cards.map(c => [c, normalize(c.dataset.search)]));
  function apply() {
    const terms = normalize(search.value).trim().split(/\s+/).filter(Boolean);
    let count = 0;
    for (const c of cards) {
      const okParty = !party.value || c.dataset.party === party.value;
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
  function reset() { search.value = ''; party.value = ''; trajectory.value = ''; if (registration) registration.value = ''; apply(); }
  search.addEventListener('input', apply);
  party.addEventListener('change', apply);
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
})();

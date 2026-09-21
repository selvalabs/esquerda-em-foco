/* Independent RS/state edition: no tracking, scoring, prediction or random order. */
(() => {
  'use strict';
  const normal = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  const collator = new Intl.Collator('pt-BR', { sensitivity: 'base', numeric: true });
  const epoch = Date.UTC(2026, 8, 21);
  const days = date => {
    const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(date);
    const item = type => Number(parts.find(part => part.type === type).value);
    return Math.max(0, Math.floor((Date.UTC(item('year'), item('month') - 1, item('day')) - epoch) / 86400000));
  };
  const rotated = (values, offset) => {
    if (!values.length) return [];
    const cut = ((offset % values.length) + values.length) % values.length;
    return values.slice(cut).concat(values.slice(0, cut));
  };
  const search = document.getElementById('searchInput');
  const party = document.getElementById('partyFilter');
  const status = document.getElementById('statusFilter');
  const history = document.getElementById('historyFilter');
  const result = document.getElementById('resultCount');
  const empty = document.getElementById('emptyResults');
  const sections = Array.from(document.querySelectorAll('.party-section'));
  const cards = Array.from(document.querySelectorAll('article.candidate'));
  const baseParties = sections.slice().sort((a, b) => collator.compare(a.dataset.partySection, b.dataset.partySection));
  const baseCards = new Map(sections.map(section => [section, Array.from(section.querySelectorAll('article.candidate')).sort((a, b) => collator.compare(a.querySelector('h3').textContent, b.querySelector('h3').textContent) || collator.compare(a.dataset.tseId, b.dataset.tseId))]));
  const nav = document.querySelector('.party-nav');
  const navByParty = new Map(Array.from(document.querySelectorAll('[data-nav-party]')).map(a => [a.dataset.navParty, a]));
  const partyNames = new Map(baseParties.map(section => [normal(section.dataset.partySection), section.dataset.partySection]));
  result.setAttribute('role', 'status');
  result.setAttribute('aria-live', 'polite');
  result.setAttribute('aria-atomic', 'true');
  cards.forEach(card => { card.dataset.normalSearch = normal(card.dataset.search); });
  let lastDay = null;
  function filter() {
    const query = normal(search.value.trim());
    const exactParty = partyNames.get(query);
    let count = 0;
    cards.forEach(card => {
      const queryMatch = !query || (exactParty ? card.dataset.party === exactParty : card.dataset.normalSearch.includes(query));
      const match = queryMatch && (!party.value || card.dataset.party === party.value) && (!status.value || card.dataset.status === status.value) && (!history.value || card.dataset.hasHistory === history.value);
      card.hidden = !match;
      if (match) count += 1;
    });
    sections.forEach(section => {
      const visible = baseCards.get(section).filter(card => !card.hidden).length;
      section.hidden = visible === 0;
      const number = section.querySelector('.party-count');
      if (number) number.textContent = `${visible} ${visible === 1 ? 'registro' : 'registros'}`;
      const link = navByParty.get(section.dataset.partySection);
      if (link) {
        link.hidden = visible === 0;
        const badge = link.querySelector('small');
        if (badge) badge.textContent = String(visible).padStart(2, '0');
      }
    });
    result.textContent = `${count} ${count === 1 ? 'resultado' : 'resultados'} de ${cards.length}`;
    if (empty) empty.hidden = count !== 0;
    return count;
  }
  function rotate(date = new Date()) {
    const offset = days(date);
    if (offset === lastDay) return;
    lastDay = offset;
    const content = document.querySelector('.content');
    rotated(baseParties, offset).forEach(section => {
      const list = section.querySelector('.candidate-list');
      rotated(baseCards.get(section), offset).forEach(card => list.appendChild(card));
      content.appendChild(section);
      const anchor = navByParty.get(section.dataset.partySection);
      if (nav && anchor) nav.appendChild(anchor);
    });
    document.documentElement.dataset.orderDay = String(offset);
  }
  function clear(focus = false) {
    search.value = '';
    [party, status, history].forEach(select => { select.value = ''; });
    filter();
    if (focus) search.focus();
  }
  search.addEventListener('input', filter);
  [party, status, history].forEach(select => select.addEventListener('change', filter));
  document.getElementById('clearFilters').addEventListener('click', () => clear(true));
  const menu = document.getElementById('siteNavMenu');
  const siteNav = document.getElementById('siteNav');
  const menuLinks = document.getElementById('siteNavLinks');
  function closeMenu(focus = false) {
    if (!menu || !siteNav) return;
    menu.setAttribute('aria-expanded', 'false');
    siteNav.classList.remove('is-open');
    if (focus) menu.focus();
  }
  if (menu && siteNav) {
    menu.addEventListener('click', () => {
      const open = menu.getAttribute('aria-expanded') !== 'true';
      menu.setAttribute('aria-expanded', String(open));
      siteNav.classList.toggle('is-open', open);
    });
    document.addEventListener('click', event => { if (!siteNav.contains(event.target)) closeMenu(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && menu.getAttribute('aria-expanded') === 'true') closeMenu(true); });
    if (menuLinks) menuLinks.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  }
  function showHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    if (target.matches('article.candidate,.party-section') && (target.hidden || target.closest('.party-section')?.hidden)) clear();
    let ancestor = target.parentElement;
    while (ancestor) { if (ancestor.tagName === 'DETAILS') ancestor.open = true; ancestor = ancestor.parentElement; }
    closeMenu();
    requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'auto' }));
  }
  window.addEventListener('hashchange', showHash);
  function progress() {
    const bar = document.getElementById('readingProgress') || document.querySelector('.reading-progress__bar');
    if (bar) {
      const total = document.documentElement.scrollHeight - innerHeight;
      bar.style.width = `${total > 0 ? Math.min(100, 100 * scrollY / total) : 0}%`;
    }
  }
  window.addEventListener('scroll', progress, { passive: true });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) { rotate(); filter(); } });
  setInterval(() => { rotate(); filter(); }, 60000);
  // A frozen, read-only test interface; no preferences or browsing data persisted.
  window.EEFOCO_STATE = Object.freeze({ days, rotated, rotate, filter, clear });
  rotate();
  filter();
  showHash();
  progress();
})();

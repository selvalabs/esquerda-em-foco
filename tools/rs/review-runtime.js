/* Source-backed filters; daily alphabetical rotation is presentation, not ranking. */
(() => {
  'use strict';
  const normalize = (value = '') => value.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  const cards = [...document.querySelectorAll('.candidate')];
  const sections = [...document.querySelectorAll('.party-section')];
  const search = document.getElementById('searchInput');
  const count = document.getElementById('resultCount');
  const empty = document.getElementById('emptyResults');
  const partyFilter = document.getElementById('partyFilter');
  const clear = document.getElementById('clearFilters');
  const topicChecks = [...document.querySelectorAll('input[name="rs-topic"]')];
  const epoch = Date.UTC(2026, 8, 21);
  const alpha = (a, b) => normalize(a).localeCompare(normalize(b), 'pt-BR');
  const rotate = (items, days) => {
    if (!items.length) return [];
    const n = ((days % items.length) + items.length) % items.length;
    return items.slice(n).concat(items.slice(0, n));
  };
  function dayIndex(date = new Date()) {
    const values = Object.fromEntries(new Intl.DateTimeFormat('en-US', {
      timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit'
    }).formatToParts(date).filter(p => p.type !== 'literal').map(p => [p.type, p.value]));
    return Math.max(0, Math.floor((Date.UTC(+values.year, +values.month - 1, +values.day) - epoch) / 86400000));
  }
  let appliedDay = null;
  function applyDailyRotation() {
    const day = dayIndex();
    if (appliedDay === day) return;
    const content = document.querySelector('.content');
    const nav = document.querySelector('.party-nav');
    const ordered = rotate([...sections].sort((a,b) => alpha(a.dataset.partySection,b.dataset.partySection)), day);
    ordered.forEach(section => {
      const list = section.querySelector('.candidate-list');
      const children = [...list.querySelectorAll('.candidate')].sort((a,b) =>
        alpha(a.querySelector('h3').textContent,b.querySelector('h3').textContent) || a.dataset.tseId.localeCompare(b.dataset.tseId));
      rotate(children,day).forEach(card => list.append(card));
      content.append(section);
      const item = [...nav.querySelectorAll('[data-nav-party]')].find(a => a.dataset.navParty === section.dataset.partySection);
      if (item) nav.append(item);
    });
    appliedDay = day;
    document.documentElement.dataset.rotationDay = String(day);
  }
  function applySearch() {
    const query = normalize(search.value.trim());
    const exactParty = ['pcdob','pco','pdt','psb','psol','pt','pv','up'].includes(query);
    const selectedParty = partyFilter ? partyFilter.value : '';
    const topics = topicChecks.filter(input => input.checked).map(input => input.value);
    let total = 0;
    cards.forEach(card => {
      const searchable = normalize(card.dataset.search || '');
      const cardTopics = new Set((card.dataset.topics || '').split(' ').filter(Boolean));
      const textMatches = !query || (exactParty ? normalize(card.dataset.party) === query : searchable.includes(query));
      const partyMatches = !selectedParty || card.dataset.party === selectedParty;
      const topicsMatch = topics.every(topic => cardTopics.has(topic));
      card.hidden = !(textMatches && partyMatches && topicsMatch);
      if (!card.hidden) total++;
    });
    sections.forEach(section => {
      const visible = [...section.querySelectorAll('.candidate')].filter(card => !card.hidden).length;
      section.hidden = visible === 0;
      const item = [...document.querySelectorAll('[data-nav-party]')].find(a => a.dataset.navParty === section.dataset.partySection);
      if (item) { item.hidden = visible === 0; item.querySelector('small').textContent = String(visible).padStart(2,'0'); }
    });
    count.textContent = `${total} resultado${total === 1 ? '' : 's'}`;
    if (empty) empty.hidden = total !== 0;
  }
  function resetFilters() {
    search.value = '';
    if (partyFilter) partyFilter.value = '';
    topicChecks.forEach(input => { input.checked = false; });
    applySearch();
  }
  const bar = document.getElementById('progressBar');
  function progress() {
    const doc = document.documentElement;
    const max = doc.scrollHeight - doc.clientHeight;
    if (bar) bar.style.width = `${max > 0 ? Math.min(100,Math.max(0,doc.scrollTop / max * 100)) : 0}%`;
  }
  const nav = document.getElementById('siteNav');
  const menu = document.getElementById('siteNavMenu');
  function setMenu(open, restoreFocus = false) {
    const wasOpen = nav.classList.contains('is-open');
    nav.classList.toggle('is-open',open);
    menu.setAttribute('aria-expanded',String(open));
    menu.setAttribute('aria-label',open ? 'Fechar menu' : 'Abrir menu');
    if (!open && wasOpen && restoreFocus) menu.focus({preventScroll:true});
  }
  function revealHash() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch { return; }
    if (!id) return;
    const target = document.getElementById(id);
    if (!target) return;
    if (target.matches('details')) target.open = true;
    if (target.matches('.candidate') && target.hidden) resetFilters();
    requestAnimationFrame(() => target.scrollIntoView({block:'start',behavior:'instant'}));
  }
  menu.addEventListener('click',() => setMenu(!nav.classList.contains('is-open')));
  document.getElementById('siteNavLinks').addEventListener('click',event => {
    const anchor = event.target.closest('a');
    if (!anchor) return;
    if (anchor.hash) {
      const target = document.getElementById(anchor.hash.slice(1));
      if (target && target.tagName === 'DETAILS') target.open = true;
    }
    setMenu(false);
  });
  document.addEventListener('click',event => { if (!nav.contains(event.target)) setMenu(false); });
  document.addEventListener('keydown',event => { if (event.key === 'Escape') setMenu(false,true); });
  addEventListener('resize',() => { if (innerWidth > 760) setMenu(false); progress(); },{passive:true});
  addEventListener('scroll',progress,{passive:true});
  addEventListener('hashchange',revealHash);
  document.addEventListener('visibilitychange',() => { if (!document.hidden) applyDailyRotation(); });
  setInterval(applyDailyRotation,60000);
  search.addEventListener('input',() => { applySearch(); progress(); });
  if (partyFilter) partyFilter.addEventListener('change',() => { applySearch(); progress(); });
  topicChecks.forEach(input => input.addEventListener('change',() => { applySearch(); progress(); }));
  if (clear) clear.addEventListener('click',() => { resetFilters(); progress(); search.focus({preventScroll:true}); });
  count.setAttribute('role','status'); count.setAttribute('aria-live','polite'); count.setAttribute('aria-atomic','true');
  applyDailyRotation(); applySearch(); progress(); revealHash();
})();

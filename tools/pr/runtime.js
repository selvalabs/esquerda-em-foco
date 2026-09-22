/* Paraná filters: common query contract, legacy URL import, non-evaluative daily rotation. */
(() => {
  'use strict';
  const $ = (s) => document.querySelector(s);
  const cards = [...document.querySelectorAll('article.candidate')];
  const sections = [...document.querySelectorAll('.party-section')];
  const input = $('#searchInput'), party = $('#partyFilter'), status = $('#statusFilter');
  const mandate = $('#mandateFilter'), historyFilter = $('#historyFilter'), region = $('#regionFilter');
  const themeButtons = [...document.querySelectorAll('button[data-theme]')];
  const knownThemes = new Set(themeButtons.map(b => b.dataset.theme));
  const knownParties=[...new Set(cards.map(c=>c.dataset.party).filter(Boolean))].sort();
  const parties = new Set(), themes = new Set();
  const normalize = x => String(x || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase('pt-BR');
  const collator = new Intl.Collator('pt-BR', { sensitivity: 'base', numeric: true });
  let selectedDay = '',lastLegacySearch=location.search;
  const epoch = Date.UTC(2026, 8, 21);
  function dateInBrazil(now) {
    const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(now).map(p => [p.type, p.value]));
    return `${parts.year}-${parts.month}-${parts.day}`;
  }
  function rotate(items, step) {
    if (!items.length) return items;
    const n = ((step % items.length) + items.length) % items.length;
    return items.slice(n).concat(items.slice(0, n));
  }
  function orderDaily(now = new Date()) {
    if(document.querySelector('article[data-eef-held]'))return;
    const day = dateInBrazil(now);
    if (selectedDay === day) return;
    selectedDay = day;
    const days = Math.floor((Date.parse(day + 'T00:00:00Z') - epoch) / 86400000);
    const sorted = [...sections].sort((a, b) => collator.compare(a.dataset.partySection, b.dataset.partySection));
    rotate(sorted, days).forEach(section => {
      section.parentNode.append(section);
      const group = [...section.querySelectorAll('article.candidate')].sort((a, b) => collator.compare(a.querySelector('h3')?.textContent || a.dataset.search, b.querySelector('h3')?.textContent || b.dataset.search) || collator.compare(a.id, b.id));
      rotate(group, days).forEach(card => card.parentNode.append(card));
    });
    const nav = $('.party-nav');
    if (nav) rotate([...nav.querySelectorAll('[data-nav-party]')].sort((a, b) => collator.compare(a.dataset.navParty, b.dataset.navParty)), days).forEach(a => nav.append(a));
    document.documentElement.dataset.rotationDate = day;
  }
  function readLegacy(searchValue=location.search) {
    const p = new URLSearchParams(searchValue);
    input.value = p.get('q') || '';
    parties.clear();const legacyParty=p.get('partido');if(legacyParty&&knownParties.includes(legacyParty))parties.add(legacyParty);
    if(party)party.value=parties.size===1?[...parties][0]:'';
    status.value = [...status.options].some(o => o.value === p.get('situacao')) ? p.get('situacao') : '';
    for (const [control,key] of [[mandate,'mandato'],[historyFilter,'historico'],[region,'regiao']]) control.value = [...control.options].some(o => o.value === p.get(key)) ? p.get(key) : '';
    themes.clear(); (p.get('pautas') || '').split(',').filter(t => knownThemes.has(t)).forEach(t => themes.add(t));
  }
  function filter() {
    const terms = normalize(input.value).trim().split(/\s+/).filter(Boolean);
    let total = 0;
    cards.forEach(card => {
      const search = normalize(card.dataset.search);
      const cardThemes = new Set((card.dataset.themes || '').split(' '));
      const stateMatches = !status.value || (status.value === 'nao-confirmada' ? ['nao-confirmada', 'deferida-sem-confirmacao-api'].includes(card.dataset.statusGroup) : card.dataset.statusGroup === status.value);
      const moreMatches = (!mandate.value || card.dataset.currentOffice === mandate.value) && (!historyFilter.value || card.dataset.hasHistory === historyFilter.value) && (!region.value || card.dataset.region === region.value);
      const show = moreMatches && (!parties.size || parties.has(card.dataset.party)) && stateMatches && terms.every(t => search.includes(t)) && [...themes].every(t => cardThemes.has(t));
      card.hidden = !show;
      if (show) total++;
    });
    sections.forEach(section => { section.hidden = !section.querySelector('article.candidate:not([hidden])'); });
    $('#resultCount').textContent = `${total} de ${cards.length} registros`;
    if ($('#emptyResults')) $('#emptyResults').hidden = total !== 0;
    themeButtons.forEach(b => b.setAttribute('aria-pressed', String(themes.has(b.dataset.theme))));
    document.documentElement.dataset.visibleCount = String(total);
  }
  function clear() { input.value = ''; parties.clear();if(party)party.value=''; status.value = ''; mandate.value = ''; historyFilter.value = ''; region.value = ''; themes.clear(); filter(); }
  input.addEventListener('input', filter);
  party?.addEventListener('change', () => {parties.clear();if(party.value)parties.add(party.value);filter();});
  status.addEventListener('change', filter);
  [mandate,historyFilter,region].forEach(control => control.addEventListener('change', filter));
  themeButtons.forEach(b => b.addEventListener('click', () => { const t = b.dataset.theme; themes.has(t) ? themes.delete(t) : themes.add(t); filter(); }));
  $('#clearFilters').addEventListener('click', clear);
  function revealHash(scroll = true) {
    if(window.EEFQueryUI)return window.EEFQueryUI.reveal(location.hash,scroll);
    if(document.getElementById('eefEditionQueryData'))return;
    let target;
    try { target = document.getElementById(decodeURIComponent(location.hash.slice(1))); } catch { return; }
    if (!target) return;
    if (target.matches('details')) target.open = true;
    const card = target.closest('article.candidate');
    const section = target.closest('.party-section');
    if ((card && card.hidden) || (section && section.hidden)) clear();
    if (scroll) requestAnimationFrame(() => target.scrollIntoView({ block: 'start', behavior: 'instant' }));
  }
  window.addEventListener('popstate', () => {if(window.EEFQueryUI)return;if(location.search!==lastLegacySearch){readLegacy();filter();lastLegacySearch=location.search;}revealHash();});
  window.addEventListener('hashchange', () => revealHash());
  const menu = $('#siteNavMenu'), nav = $('#siteNav');
  if (menu && nav) {
    menu.addEventListener('click', () => { const open = menu.getAttribute('aria-expanded') !== 'true'; menu.setAttribute('aria-expanded', String(open)); nav.classList.toggle('is-open', open); });
    nav.querySelectorAll('a').forEach(a => a.addEventListener('click', () => { menu.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); }));
    document.addEventListener('click', e => { if (!nav.contains(e.target)) {menu.setAttribute('aria-expanded','false');nav.classList.remove('is-open');} });
    document.addEventListener('keydown', e => { if (e.key === 'Escape') { menu.setAttribute('aria-expanded', 'false'); nav.classList.remove('is-open'); } });
  }
  function progress() {
    const p = $('#progressBar'); if (!p) return;
    const range = document.documentElement.scrollHeight - innerHeight;
    p.style.width = `${range > 0 ? 100 * scrollY / range : 0}%`;
  }
  addEventListener('scroll', progress, { passive: true });
  $('#resultCount').setAttribute('role','status'); $('#resultCount').setAttribute('aria-live','polite');
  const queryValid=Object.freeze({edition_id:document.body.dataset.global03Edition||'',parties:knownParties,topics:[...knownThemes].sort(),statuses:[...status.options].map(o=>o.value).filter(Boolean),regions:[...region.options].map(o=>o.value).filter(Boolean),mandates:['','true','false'],histories:['','true','false'],modes:['all'],orders:['daily'],semantic:'legacy_context'});
  function snapshot(){return {edition_id:queryValid.edition_id,q:input.value.trim(),parties:[...parties].sort(),topics:[...themes].sort(),status:status.value,mandate:mandate.value,history:historyFilter.value,region:region.value,mode:'all',order:'daily',semantic:'legacy_context'};}
  function applyState(s){
    if(s.edition_id!==queryValid.edition_id||s.mode!=='all'||s.order!=='daily'||s.semantic!=='legacy_context'||s.parties.some(x=>!knownParties.includes(x))||s.topics.some(x=>!knownThemes.has(x))||s.status&&!queryValid.statuses.includes(s.status)||s.mandate&&!queryValid.mandates.includes(s.mandate)||s.history&&!queryValid.histories.includes(s.history)||s.region&&!queryValid.regions.includes(s.region))throw new TypeError('Critério não disponível nesta edição do Paraná');
    input.value=s.q;parties.clear();s.parties.forEach(x=>parties.add(x));if(party)party.value=s.parties.length===1?s.parties[0]:'';status.value=s.status;mandate.value=s.mandate;historyFilter.value=s.history;region.value=s.region;themes.clear();s.topics.forEach(x=>themes.add(x));filter();return snapshot();
  }
  function importLegacy(searchValue){readLegacy(searchValue);filter();lastLegacySearch=searchValue;return snapshot();}
  window.EEFEditionQuery=Object.freeze({valid:queryValid,snapshot,applyState,importLegacy,legacyDialect:'PR'});
  orderDaily(); readLegacy(); filter(); revealHash(); progress();
  setInterval(() => orderDaily(), 60000);
  document.addEventListener('visibilitychange', () => { if (!document.hidden) orderDaily(); });
  window.EEFPR = Object.freeze({ dateInBrazil, rotate });
})();

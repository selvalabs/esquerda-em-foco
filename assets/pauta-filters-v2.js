/* Gerado por tools/sc_semantic_v2_ui/build.py; modelo v2, motor e navegação v1 preservados. */
/* Filtros documentais locais. A matriz aprovada é a única origem das associações. */
(function () {
  'use strict';
  const data = window.EEF_SC_FEDERAIS_FILTERS_V2;
  const core = window.EEFPautaCore;
  const panel = document.getElementById('pautaPanel');
  const search = document.getElementById('searchInput');
  const count = document.getElementById('resultCount');
  const dialog = document.getElementById('pautaDialog');
  const opener = document.getElementById('pautaOpen');
  const sidebar = document.getElementById('pautaSidebarHost');
  const active = document.getElementById('pautaActive');
  const activeList = document.getElementById('pautaActiveList');
  const empty = document.getElementById('pautaEmpty');
  const notice = document.getElementById('pautaNotice');
  if (!data || data.schemaVersion !== "2.0.0" || !core || !panel || !search || !count || !dialog || !opener || !sidebar || !active || !empty) return;
  const topicMap = new Map(data.topics.map(topic => [topic.id, topic]));
  const candidateMap = new Map(data.candidates.map(candidate => [candidate.id, candidate]));
  const cards = Array.from(document.querySelectorAll('article.candidate'));
  if (cards.length !== candidateMap.size || cards.some(card => !candidateMap.has(card.dataset.tseId))) return;
  const records = cards.map(card => {
    const copy = card.cloneNode(true);
    copy.querySelectorAll('.candidate-copy, .candidate-index, .pauta-match').forEach(node => node.remove());
    const candidate = candidateMap.get(card.dataset.tseId);
    return {id: candidate.id, topicIds: candidate.topicIds, text: copy.textContent + " " + (card.dataset.search || ""), card, candidate};
  });
  const sections = Array.from(document.querySelectorAll('.party-section')).map(section => ({
    section,
    cards: Array.from(section.querySelectorAll('.candidate')),
    label: section.querySelector('.party-count'),
    original: section.querySelector('.party-count')?.textContent,
    party: section.dataset.partySection
  }));
  const nav = Array.from(document.querySelectorAll('.party-nav [data-nav-party]')).map(link => ({
    link, count: link.querySelector('small'), original: link.querySelector('small')?.textContent
  }));
  const selected = new Set();
  const chips = Array.from(panel.querySelectorAll('[data-pauta-topic]'));
  const modeInputs = Array.from(panel.querySelectorAll('input[name="pauta-mode"]'));
  const mobile = matchMedia('(max-width: 980px)');
  let mode = 'any';
  let visibleCount = cards.length;
  let closeAction = null;
  let backdropPointer = false;

  function node(tag, className, text) {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined) el.textContent = text;
    return el;
  }

  function matchingEvidence(record) {
    let box = record.card.querySelector('.pauta-match');
    if (!selected.size || record.card.hidden) {
      if (box) { box.hidden = true; box.replaceChildren(); }
      return;
    }
    const defended = record.card.querySelector('[data-pauta-section="pautas"]');
    if (!defended) return; // No fallback to the old single paragraph or historical text.
    if (!box) {
      box = node('div', 'pauta-match');
      defended.insertAdjacentElement('afterend', box);
    }
    const groups = new Map();
    record.candidate.matches.filter(match => selected.has(match.topicId)).forEach(match => {
      const key = JSON.stringify([match.text, match.sourceIds]);
      if (!groups.has(key)) groups.set(key, {...match, topicIds: new Set(), familyIds: new Set()});
      groups.get(key).topicIds.add(match.topicId);
      groups.get(key).familyIds.add(match.familyId);
    });
    box.replaceChildren(node('p', 'pauta-match__heading', 'Por que aparece neste filtro'));
    const list = node('ul', 'pauta-match__list');
    groups.forEach(match => {
      const item = node('li');
      const labels = [...match.topicIds].map(id => topicMap.get(id).label).join(' · ');
      item.append(node('strong', '', labels));
      const families = [...match.familyIds].map(id => data.families[id]).join(' · ');
      if (families !== labels) item.append(node('small', 'pauta-match__family', families));
      item.append(node('span', 'pauta-match__text', match.text));
      const refs = node('span', 'pauta-match__sources');
      match.sourceIds.forEach(id => {
        const source = data.sources[id];
        if (!source) return;
        const a = node('a', '', `Fonte ${source.number} ↗`);
        a.href = source.url;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.setAttribute('aria-label', `Fonte ${source.number}: ${source.title}`);
        a.title = source.title;
        refs.append(a);
      });
      item.append(refs); list.append(item);
    });
    box.append(list); box.hidden = !groups.size;
  }

  function render() {
    const state = {query: search.value, topics: selected, mode};
    const ids = new Set(core.filter(records, state).map(record => record.id));
    visibleCount = ids.size;
    records.forEach(record => {
      record.card.hidden = !ids.has(record.id);
      matchingEvidence(record);
    });
    const filtering = Boolean(selected.size || core.normalize(search.value));
    const partyCounts = new Map();
    sections.forEach(({section, cards: group, label, original, party}) => {
      const number = group.filter(card => !card.hidden).length;
      partyCounts.set(party, number);
      section.hidden = !number;
      if (label) label.textContent = filtering ? `${number} de ${group.length} candidaturas` : original;
    });
    nav.forEach(({link, count: number, original}) => {
      const value = partyCounts.get(link.dataset.navParty) || 0;
      link.hidden = !value;
      if (number) number.textContent = filtering ? String(value) : original;
    });
    count.textContent = `${visibleCount} resultado${visibleCount === 1 ? '' : 's'}`;
    chips.forEach(chip => chip.setAttribute('aria-pressed', String(selected.has(chip.dataset.pautaTopic))));
    modeInputs.forEach(input => { input.checked = input.value === mode; });
    panel.querySelector('[data-pauta-clear]').disabled = !selected.size && mode === 'any';
    panel.querySelector('[data-pauta-selection]').textContent = selected.size
      ? `${selected.size} área${selected.size === 1 ? '' : 's'} selecionada${selected.size === 1 ? '' : 's'}`
      : 'Nenhuma área selecionada';
    const openLabel = document.getElementById('pautaOpenLabel');
    openLabel.textContent = selected.size ? `Pautas · ${selected.size} selecionada${selected.size === 1 ? '' : 's'}` : 'Pautas · Filtrar';
    active.hidden = !selected.size;
    activeList.replaceChildren();
    data.topics.filter(topic => selected.has(topic.id)).forEach(topic => {
      const button = node('button', 'pauta-active__chip', topic.label + ' ×');
      button.type = 'button';
      button.dataset.pautaRemove = topic.id;
      button.setAttribute('aria-label', `Remover filtro ${topic.label}`);
      activeList.append(button);
    });
    document.getElementById('pautaActiveMode').textContent = mode === 'all' ? 'Todas as selecionadas' : 'Pelo menos uma das selecionadas';
    empty.hidden = visibleCount !== 0;
    document.getElementById('pautaDialogCount').textContent = `${visibleCount} candidatura${visibleCount === 1 ? '' : 's'} encontrada${visibleCount === 1 ? '' : 's'}`;
    document.getElementById('pautaShowResults').textContent = visibleCount ? `Ver ${visibleCount} resultado${visibleCount === 1 ? '' : 's'}` : 'Voltar à busca';
    requestAnimationFrame(() => {
      const doc = document.documentElement;
      const bar = document.getElementById('progressBar');
      if (bar) bar.style.width = `${doc.scrollHeight > doc.clientHeight ? doc.scrollTop / (doc.scrollHeight - doc.clientHeight) * 100 : 0}%`;
    });
  }

  function clearNotice() { notice.hidden = true; notice.textContent = ''; }
  function reset(all) {
    selected.clear();
    mode = 'any';
    if (all) search.value = '';
    clearNotice();
    render();
  }
  panel.addEventListener('click', event => {
    const chip = event.target.closest('[data-pauta-topic]');
    if (chip) {
      const id = chip.dataset.pautaTopic;
      if (selected.has(id)) selected.delete(id); else selected.add(id);
      clearNotice(); render();
    }
    if (event.target.closest('[data-pauta-clear]')) reset(false);
  });
  panel.addEventListener('change', event => {
    if (event.target.name === 'pauta-mode') { mode = event.target.value === 'all' ? 'all' : 'any'; clearNotice(); render(); }
  });
  activeList.addEventListener('click', event => {
    const button = event.target.closest('[data-pauta-remove]');
    if (!button) return;
    selected.delete(button.dataset.pautaRemove);
    clearNotice(); render();
    (activeList.querySelector('button') || search).focus({preventScroll: true});
  });
  document.querySelectorAll('[data-pauta-reset]').forEach(button => {
    button.addEventListener('click', () => {
      reset(button.dataset.pautaReset === 'all');
      search.focus({preventScroll: true});
    });
  });
  search.addEventListener('input', clearNotice);

  function focusAt(target, scroll) {
    if (!target) return;
    let parent = target;
    while (parent) { if (parent.tagName === 'DETAILS') parent.open = true; parent = parent.parentElement; }
    if (!target.matches('a,button,input,select,textarea,summary,[tabindex]')) target.setAttribute('tabindex', '-1');
    target.focus({preventScroll: true});
    if (scroll) target.scrollIntoView({block: 'start', behavior: 'instant'});
  }
  function revealHash(hash, scroll) {
    let id;
    try { id = decodeURIComponent(hash.replace(/^#/, '')); } catch { return; }
    const target = document.getElementById(id);
    if (!target) return;
    const candidate = target.closest('.candidate');
    const section = target.closest('.party-section');
    if ((candidate && candidate.hidden) || (section && section.hidden)) {
      reset(true);
      notice.textContent = 'Busca e pautas removidas para mostrar o conteúdo do link.';
      notice.hidden = false;
    }
    focusAt(target, scroll);
  }
  function finishClose() {
    document.documentElement.classList.remove('eef-pauta-modal');
    opener.setAttribute('aria-expanded', 'false');
    const action = closeAction;
    closeAction = null;
    if (action) action();
    else (mobile.matches ? opener : chips[0])?.focus({preventScroll: true});
  }
  function closePanel(action) {
    if (!dialog.open) { if (action) action(); return; }
    closeAction = action || null;
    dialog.close();
  }
  dialog.addEventListener('close', finishClose);
  dialog.addEventListener('cancel', () => { closeAction = null; });
  document.getElementById('pautaClose').addEventListener('click', () => closePanel());
  document.getElementById('pautaShowResults').addEventListener('click', () => closePanel(() => {
    const first = document.querySelector('.candidate:not([hidden])');
    focusAt(first || search, true);
  }));
  dialog.addEventListener('pointerdown', event => {
    const rect = dialog.getBoundingClientRect();
    backdropPointer = event.target === dialog && (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom);
  });
  dialog.addEventListener('click', event => {
    if (backdropPointer && event.target === dialog) closePanel();
    backdropPointer = false;
  });
  dialog.addEventListener('keydown', event => {
    if (event.key !== 'Tab') return;
    const focusables = Array.from(dialog.querySelectorAll('a[href], button:not(:disabled), input:not(:disabled), [tabindex="0"]')).filter(el => el.getClientRects().length);
    const first = focusables[0], last = focusables[focusables.length - 1];
    if (event.shiftKey && (document.activeElement === first || document.activeElement === document.getElementById('pautaDialogTitle'))) {
      event.preventDefault(); last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault(); first.focus();
    }
  });
  opener.addEventListener('click', () => {
    const siteNav = document.getElementById('siteNav');
    const menu = document.getElementById('siteNavMenu');
    siteNav?.classList.remove('is-open');
    menu?.setAttribute('aria-expanded', 'false');
    menu?.setAttribute('aria-label', 'Abrir menu');
    if (!dialog.open) {
      dialog.showModal();
      document.documentElement.classList.add('eef-pauta-modal');
      opener.setAttribute('aria-expanded', 'true');
      document.getElementById('pautaDialogTitle').focus({preventScroll: true});
    }
  });
  function placePanel() {
    if (mobile.matches) {
      if (typeof dialog.showModal === 'function') document.getElementById('pautaDialogBody').append(panel);
      else { document.getElementById('pautaInline').append(panel); opener.hidden = true; }
    } else {
      if (dialog.open) closePanel(() => chips[0]?.focus({preventScroll: true}));
      sidebar.append(panel);
    }
  }
  mobile.addEventListener('change', placePanel);
  document.addEventListener('click', event => {
    const a = event.target.closest('a[href^="#"]');
    if (!a || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
    const hash = a.getAttribute('href');
    let target;
    try { target = document.getElementById(decodeURIComponent(hash.slice(1))); } catch { return; }
    if (!target) return;
    if (target.tagName !== 'DETAILS' && !target.closest('.candidate') && !target.closest('.party-section') && !dialog.contains(a)) return;
    event.preventDefault();
    if (location.hash !== hash) history.pushState(null, '', hash);
    closePanel(() => revealHash(hash, true));
  });
  addEventListener('hashchange', () => closePanel(() => revealHash(location.hash, true)));
  addEventListener('popstate', () => { if (location.hash) closePanel(() => revealHash(location.hash, true)); });

  function measureBars() {
    const root = document.documentElement;
    const navHeight = document.getElementById('siteNav')?.getBoundingClientRect().height || 58;
    const footerHeight = document.querySelector('.persistent-footer')?.getBoundingClientRect().height || 48;
    root.style.setProperty('--eef-nav-height', `${Math.ceil(navHeight)}px`);
    root.style.setProperty('--eef-footer-height', `${Math.ceil(footerHeight)}px`);
  }
  if (typeof ResizeObserver === 'function') {
    const observer = new ResizeObserver(measureBars);
    [document.getElementById('siteNav'), document.querySelector('.persistent-footer')].filter(Boolean).forEach(el => observer.observe(el));
  }
  addEventListener('resize', measureBars, {passive: true});
  const rail = document.querySelector('.rail');
  rail.setAttribute('aria-label', 'Partidos e filtros por pautas');
  rail.setAttribute('tabindex', '0');
  panel.hidden = false;
  document.getElementById('pautaToolbar').hidden = false;
  document.documentElement.classList.add('eef-filters-ready');
  placePanel();
  measureBars();
  window.EEFTopicFilters = Object.freeze({apply: render});
  render();
  if (location.hash) revealHash(location.hash, true);
})();

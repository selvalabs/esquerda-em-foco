/* Selecionados: consulta individual das fichas originais. Sem storage ou analytics. */
(() => {
  'use strict';
  const core = window.EEFSelectionCore;
  const get = id => document.getElementById(id);
  const dialog = get('eefCollection');
  const shareDialog = get('eefShareDialog');
  const confirmDialog = get('eefConfirm');
  const cards = [...document.querySelectorAll('article.candidate')];
  if (!core || !dialog || !shareDialog || !confirmDialog || typeof dialog.showModal !== 'function' || cards.length !== 48) return;
  const ids = cards.map(c => c.dataset.tseId);
  if (new Set(ids).size !== 48 || ids.some(id => !/^\d{12}$/.test(id))) return;
  const byId = new Map(cards.map(c => [c.dataset.tseId, c]));
  const names = new Map(cards.map(c => [c.dataset.tseId,c.querySelector('h3').textContent.trim()]));
  const store = core.createStore(ids);
  const root = document.documentElement;
  const host = get('eefReaderHost');
  const nav = get('eefSelectedNav');
  let active = null;
  let held = null;
  let returnState = null;
  let restoreOnClose = true;
  let sharePayload = null;
  let shareOpener = null;
  let shareToken = 0;
  let pointer = null;
  let lastRoute = null;

  function announce(text) { get('eefSelectionStatus').textContent = text; }
  function base() { return new URL('./', location.href).href; }
  function applyFilters() {
    if (window.EEFTopicFilters) window.EEFTopicFilters.apply();
    else get('searchInput')?.dispatchEvent(new Event('input', {bubbles: true}));
  }
  function closeNav() {
    get('siteNav')?.classList.remove('is-open');
    const b = get('siteNavMenu');
    b?.setAttribute('aria-expanded','false');
    b?.setAttribute('aria-label','Abrir menu');
  }
  function sync() {
    const size = store.size();
    document.querySelectorAll('[data-eef-count]').forEach(el => el.textContent = String(size));
    nav.setAttribute('aria-label',`Abrir selecionados: ${size} ficha${size === 1 ? '' : 's'}`);
    document.querySelectorAll('[data-eef-toggle]').forEach(b => {
      const id = b.dataset.eefToggle, selected = store.has(id);
      b.textContent = selected ? 'Selecionado' : 'Selecionar';
      b.setAttribute('aria-pressed',String(selected));
      b.setAttribute('aria-label',(selected ? 'Remover de selecionados: ' : 'Selecionar: ') + names.get(id));
    });
    get('eefSelectionBar').hidden = !size || dialog.open;
    root.classList.toggle('eef-has-selection',Boolean(size));
  }
  function restoreCard() {
    if (!held) return;
    const {card, marker, hidden, tabindex} = held;
    marker.replaceWith(card);
    card.hidden = hidden;
    if (tabindex === null) card.removeAttribute('tabindex'); else card.setAttribute('tabindex',tabindex);
    held = null;
  }
  function focusActive() {
    const target = held?.card || get('eefCollectionTitle');
    target.setAttribute('tabindex','-1');
    target.focus({preventScroll:true});
    dialog.scrollTop = 0;
  }
  function showActive(focus = true) {
    restoreCard();
    const selected = store.snapshot();
    if (!selected.includes(active)) active = selected[0] || null;
    const index = selected.indexOf(active);
    if (active) {
      const card = byId.get(active);
      const marker = document.createComment('eef-selected-slot');
      held = {card,marker,hidden:card.hidden,tabindex:card.getAttribute('tabindex')};
      card.replaceWith(marker);
      card.hidden = false;
      host.append(card);
      get('eefOpenFull').href = '#candidato-' + active;
    }
    get('eefCollectionEmpty').hidden = Boolean(active);
    get('eefReaderControls').hidden = !active;
    get('eefCollectionActions').hidden = !active;
    get('eefPager').textContent = active ? `Ficha ${index + 1} de ${selected.length}` : '';
    get('eefPrevious').disabled = index <= 0;
    get('eefNext').disabled = index < 0 || index >= selected.length - 1;
    sync();
    if (focus) focusActive();
  }
  function openCollection(opener) {
    if (!dialog.open) {
      returnState = {element: opener || document.activeElement, x:scrollX, y:scrollY};
      restoreOnClose = true;
      closeNav();
      if (get('pautaDialog')?.open) get('pautaClose')?.click();
      showActive(false);
      dialog.showModal();
      root.classList.add('eef-collection-open');
      focusActive();
    } else showActive();
    sync();
  }
  function finishClose() {
    restoreCard();
    root.classList.remove('eef-collection-open');
    applyFilters();
    sync();
    if (restoreOnClose && returnState) {
      const target = returnState.element?.isConnected && returnState.element.getClientRects().length ? returnState.element : nav;
      target.focus({preventScroll:true});
      window.scrollTo({left:returnState.x,top:returnState.y,behavior:'instant'});
    }
    returnState = null;
    restoreOnClose = true;
  }
  function exitReader(restore = true) {
    if (!dialog.open) return;
    restoreOnClose = restore;
    // Restore synchronously before the existing hash router processes an outside anchor.
    restoreCard();
    dialog.close();
  }
  dialog.addEventListener('close',finishClose);
  dialog.addEventListener('cancel',() => { restoreOnClose = true; });
  get('eefCollectionClose').addEventListener('click',() => exitReader());
  function step(delta) {
    const selected = store.snapshot();
    const next = selected.indexOf(active) + delta;
    if (next < 0 || next >= selected.length) return;
    active = selected[next];showActive();
  }
  get('eefPrevious').addEventListener('click',() => step(-1));
  get('eefNext').addEventListener('click',() => step(1));
  get('eefReaderControls').addEventListener('keydown',e => {
    if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
    e.preventDefault();step(e.key === 'ArrowRight' ? 1 : -1);
  });
  host.addEventListener('pointerdown',e => {
    if (e.pointerType !== 'touch' || e.target.closest('button,a,input,textarea,summary')) return;
    pointer = {x:e.clientX,y:e.clientY};
  });
  host.addEventListener('pointerup',e => {
    if (!pointer) return;
    const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;pointer=null;
    if (Math.abs(dx)>75 && Math.abs(dy)<35) step(dx<0 ? 1 : -1);
  });
  host.addEventListener('pointercancel',() => { pointer=null; });
  function toggle(id) {
    if (!byId.has(id)) return;
    const selected = store.snapshot();
    const oldIndex = selected.indexOf(id);
    const was = store.has(id);
    store.toggle(id);
    if (dialog.open && was && id === active) {
      const next = store.snapshot();
      active = next[Math.min(oldIndex,next.length-1)] || null;
      showActive();
    } else sync();
    announce((was ? 'Removido: ' : 'Adicionado a selecionados: ') + names.get(id) + '.');
  }
  function openShare(id, opener) {
    shareToken++;
    shareOpener = opener;
    const collection = !id;
    try {
      const url = collection ? core.collectionUrl(base(),store.snapshot(),ids,active) : core.candidateUrl(base(),id,ids);
      sharePayload = core.shareData(url,collection ? null : names.get(id));
    } catch {
      announce('Não foi possível preparar o link desta coleção. Verifique os itens selecionados.');return;
    }
    get('eefShareTitle').textContent = collection ? 'Compartilhar selecionados' : 'Compartilhar ficha';
    get('eefShareMessage').textContent = sharePayload.text;
    get('eefShareUrl').value = sharePayload.url;
    get('eefShareStatus').textContent = '';
    get('eefWhatsapp').href = core.whatsappUrl(sharePayload);
    get('eefNativeShare').hidden = typeof navigator.share !== 'function';
    get('eefNativeShare').disabled = false;
    shareDialog.showModal();
    get('eefShareClose').focus();
  }
  get('eefShareCollection').addEventListener('click',e => openShare(null,e.currentTarget));
  get('eefShareClose').addEventListener('click',() => shareDialog.close());
  shareDialog.addEventListener('close',() => {
    shareToken++;sharePayload = null;
    if (shareOpener?.isConnected && shareOpener.getClientRects().length) shareOpener.focus({preventScroll:true});
    else (dialog.open ? get('eefCollectionTitle') : nav).focus({preventScroll:true});
  });
  get('eefCopy').addEventListener('click',async () => {
    if (!sharePayload) return;
    const token = shareToken;
    const result = await core.copyLink(sharePayload.url,navigator);
    if (token !== shareToken || !shareDialog.open) return;
    get('eefShareStatus').textContent = result.status === 'copied' ? 'Link copiado.' : 'Não foi possível copiar automaticamente. Selecione o link e use Copiar.';
    if (result.status !== 'copied') { get('eefShareUrl').focus();get('eefShareUrl').select(); }
  });
  get('eefNativeShare').addEventListener('click',async () => {
    if (!sharePayload) return;
    const token = shareToken;
    get('eefNativeShare').disabled = true;
    const result = await core.nativeShare(sharePayload,navigator);
    if (token !== shareToken || !shareDialog.open) return;
    get('eefNativeShare').disabled = false;
    get('eefShareStatus').textContent = result.status === 'handed-off' ? 'Conteúdo entregue ao compartilhador do aparelho. Confirme o envio no aplicativo.' : result.status === 'cancelled' ? 'Compartilhamento cancelado ou sem destino disponível.' : 'Compartilhamento nativo indisponível. Use Copiar link ou WhatsApp.';
  });
  get('eefClearCollection').addEventListener('click',() => { confirmDialog.showModal();get('eefCancelClear').focus(); });
  get('eefCancelClear').addEventListener('click',() => confirmDialog.close());
  get('eefConfirmClear').addEventListener('click',() => {
    store.clear();active=null;showActive(false);confirmDialog.close();announce('A coleção foi esvaziada. As fichas continuam disponíveis na lista.');
  });
  confirmDialog.addEventListener('close',() => {
    (store.size() ? get('eefClearCollection') : get('eefCollectionTitle')).focus({preventScroll:true});
  });
  document.addEventListener('click',e => {
    const toggleButton = e.target.closest('[data-eef-toggle]');
    if (toggleButton) { toggle(toggleButton.dataset.eefToggle);return; }
    const share = e.target.closest('[data-eef-share]');
    if (share) { openShare(share.dataset.eefShare,share);return; }
    const open = e.target.closest('[data-eef-open]');
    if (open) openCollection(open);
  });
  // Existing source anchors inside the current card are handled by the filter router.
  document.addEventListener('click',e => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || !dialog.open || e.ctrlKey || e.metaKey || e.shiftKey || e.altKey) return;
    let target;
    try { target = get(decodeURIComponent(a.hash.slice(1))); } catch { return; }
    if (a.id === 'eefOpenFull' || (target && !dialog.contains(target))) exitReader(false);
  },true);
  function route() {
    const hash = location.hash;
    if (hash === lastRoute) return;
    lastRoute = hash;
    const parsed = core.parseFragment(hash,ids);
    if (parsed.kind === 'collection') {
      restoreCard();store.replace(parsed.ids);active=parsed.active;
      openCollection(nav);
      announce(parsed.ignored ? 'Coleção aberta. Alguns itens não pertencem a esta edição e foram ignorados.' : 'Coleção aberta a partir do link.');
    } else if (parsed.kind === 'invalid') {
      announce(parsed.reason + '. A seleção existente foi preservada.');
    } else if (dialog.open) {
      let target;
      try { target=get(decodeURIComponent(hash.slice(1))); } catch { return; }
      if (!target || !dialog.contains(target)) exitReader(false);
    }
  }
  window.addEventListener('hashchange',route,true);
  window.addEventListener('popstate',route,true);
  function backdropClose(d,close) {
    let outside=false;
    d.addEventListener('pointerdown',e => {
      const r=d.getBoundingClientRect();
      outside=e.target===d && (e.clientX<r.left || e.clientX>r.right || e.clientY<r.top || e.clientY>r.bottom);
    });
    d.addEventListener('click',e => { if(outside && e.target===d)close();outside=false; });
  }
  backdropClose(dialog,() => exitReader());
  backdropClose(shareDialog,() => shareDialog.close());
  function measureFooter() {
    const h = document.querySelector('.persistent-footer')?.getBoundingClientRect().height || 42;
    root.style.setProperty('--eef-selected-footer',Math.ceil(h)+'px');
  }
  if (typeof ResizeObserver === 'function') {
    const observer=new ResizeObserver(measureFooter);
    const footer=document.querySelector('.persistent-footer');if(footer)observer.observe(footer);
  }
  window.addEventListener('resize',measureFooter,{passive:true});measureFooter();
  nav.hidden=false;
  document.querySelectorAll('.eef-card-actions').forEach(a => a.hidden=false);
  root.classList.add('eef-selected-ready');
  sync();route();
})();

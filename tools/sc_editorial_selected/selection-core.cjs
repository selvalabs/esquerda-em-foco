/* Coleção de consulta individual. Sem armazenamento, rede ou classificação política. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EEFSelectionCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const EDITION = 'sc-federais';
  const VERSION = '1';
  const MAX_FRAGMENT_LENGTH = 4096;
  const ID = /^\d{12}$/;
  function allowSet(values) {
    if (!Array.isArray(values) || !values.length || values.some(v => typeof v !== 'string' || !ID.test(v))) throw new TypeError('Catálogo inválido');
    return new Set(values);
  }
  function cleanIds(values, allowed) {
    if (!Array.isArray(values) || values.length > 256) throw new TypeError('Lista inválida');
    const seen = new Set();
    const ids = [];
    let ignored = 0;
    for (const id of values) {
      if (typeof id !== 'string' || !ID.test(id) || !allowed.has(id)) { ignored++; continue; }
      if (!seen.has(id)) { ids.push(id); seen.add(id); }
    }
    return {ids, ignored};
  }
  function createStore(catalog) {
    const allowed = allowSet(catalog);
    let ids = [];
    return Object.freeze({
      snapshot: () => ids.slice(),
      has: id => ids.includes(id),
      size: () => ids.length,
      add(id) {
        if (!allowed.has(id)) throw new TypeError('Ficha desconhecida');
        if (!ids.includes(id)) ids.push(id);
        return ids.slice();
      },
      remove(id) { ids = ids.filter(v => v !== id); return ids.slice(); },
      toggle(id) {
        if (!allowed.has(id)) throw new TypeError('Ficha desconhecida');
        ids = ids.includes(id) ? ids.filter(v => v !== id) : ids.concat(id);
        return ids.slice();
      },
      replace(values) { const result = cleanIds(values, allowed); ids = result.ids; return {ids:ids.slice(),ignored:result.ignored}; },
      clear() { ids = []; }
    });
  }
  function parseFragment(hash, catalog) {
    const allowed = allowSet(catalog);
    if (typeof hash !== 'string') return {kind:'invalid', reason:'Formato inválido'};
    if (hash.length > MAX_FRAGMENT_LENGTH) return {kind:'invalid', reason:'Link excede o limite de leitura'};
    const legacy = /^#candidato-(\d{12})$/.exec(hash);
    if (legacy) return allowed.has(legacy[1]) ? {kind:'candidate',id:legacy[1]} : {kind:'invalid',reason:'Ficha não encontrada nesta edição'};
    if (!hash.startsWith('#selecionados=')) return {kind:'other'};
    // Reject malformed percent encodings, rather than accepting a partially decoded value.
    if (/%(?![0-9a-f]{2})/i.test(hash)) return {kind:'invalid',reason:'Codificação inválida'};
    const q = new URLSearchParams(hash.slice(1));
    if (q.getAll('v').length !== 1 || q.getAll('edicao').length !== 1 || q.getAll('selecionados').length !== 1 || q.getAll('ficha').length > 1) return {kind:'invalid',reason:'Parâmetros duplicados ou incompletos'};
    if (q.get('v') !== VERSION || q.get('edicao') !== EDITION) return {kind:'invalid',reason:'Versão ou edição não suportada'};
    let result;
    try { result = cleanIds(q.get('selecionados') ? q.get('selecionados').split(',') : [], allowed); }
    catch { return {kind:'invalid',reason:'Lista de fichas inválida'}; }
    if (q.get('selecionados') && !result.ids.length) return {kind:'invalid',reason:'Nenhuma ficha reconhecida nesta edição'};
    const active = result.ids.includes(q.get('ficha')) ? q.get('ficha') : (result.ids[0] || null);
    return {kind:'collection',ids:result.ids,active,ignored:result.ignored};
  }
  function baseUrl(value) {
    const url = new URL(value);
    if (!['https:','http:'].includes(url.protocol) || url.username || url.password) throw new TypeError('Endereço de compartilhamento inválido');
    url.search = ''; url.hash = '';
    return url;
  }
  function collectionUrl(base, values, catalog, active) {
    const allowed = allowSet(catalog);
    const result = cleanIds(values, allowed);
    if (result.ignored || !result.ids.length) throw new TypeError('Seleção vazia ou inválida');
    const q = new URLSearchParams();
    q.set('selecionados',result.ids.join(',')); q.set('v',VERSION); q.set('edicao',EDITION);
    if (active && result.ids.includes(active)) q.set('ficha',active);
    const url = baseUrl(base); url.hash = q.toString();
    if (url.hash.length > MAX_FRAGMENT_LENGTH) throw new RangeError('Seleção excede o limite do link');
    return url.href;
  }
  function candidateUrl(base, id, catalog) {
    if (!allowSet(catalog).has(id)) throw new TypeError('Ficha desconhecida');
    const url = baseUrl(base); url.hash = 'candidato-' + id; return url.href;
  }
  function shareData(url, name) {
    const parsed = new URL(url);
    if (!['https:','http:'].includes(parsed.protocol)) throw new TypeError('URL não compartilhável');
    const text = name ? `Ficha de ${name} no Esquerda em Foco — informações e fontes para consulta.` : 'Fichas reunidas para consulta no Esquerda em Foco.';
    return {title:'Esquerda em Foco',text,url:parsed.href};
  }
  function whatsappUrl(data) {
    const out = new URL('https://wa.me/');
    out.searchParams.set('text',data.text + '\n' + data.url);
    return out.href;
  }
  async function nativeShare(data, adapter) {
    if (!adapter || typeof adapter.share !== 'function') return {status:'unavailable'};
    try {
      if (typeof adapter.canShare === 'function' && !adapter.canShare(data)) return {status:'unavailable'};
      await adapter.share(data);
      // Resolution means handoff, not that a message was delivered to a contact.
      return {status:'handed-off'};
    } catch (error) {
      return {status:error && error.name === 'AbortError' ? 'cancelled' : 'unavailable'};
    }
  }
  async function copyLink(url, adapter) {
    try {
      if (!adapter || !adapter.clipboard || typeof adapter.clipboard.writeText !== 'function') return {status:'manual'};
      await adapter.clipboard.writeText(url); return {status:'copied'};
    } catch { return {status:'manual'}; }
  }
  return Object.freeze({EDITION,VERSION,MAX_FRAGMENT_LENGTH,createStore,parseFragment,collectionUrl,candidateUrl,shareData,whatsappUrl,nativeShare,copyLink});
});

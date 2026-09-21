/* Motor sem efeitos colaterais: não classifica textos, não reordena e não persiste preferências. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EEFPautaCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  function normalize(value) {
    return String(value == null ? '' : value).toLowerCase().normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '').replace(/\s+/g, ' ').trim();
  }
  function matches(record, state) {
    const query = normalize(state.query);
    if (query && !normalize(record.text).includes(query)) return false;
    const selected = Array.from(state.topics || []);
    if (!selected.length) return true;
    const topics = new Set(record.topicIds || []);
    return state.mode === 'all'
      ? selected.every(id => topics.has(id))
      : selected.some(id => topics.has(id));
  }
  function filter(records, state) {
    return records.filter(record => matches(record, state));
  }
  function counts(records, topicIds) {
    return Object.fromEntries(topicIds.map(id => [id,
      records.reduce((n, record) => n + (new Set(record.topicIds || []).has(id) ? 1 : 0), 0)
    ]));
  }
  return Object.freeze({normalize, matches, filter, counts});
});

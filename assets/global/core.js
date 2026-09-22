/* GLOBAL-02: pure, edition-scoped contracts. No network, storage or ranking. */
(function(root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.EEFGlobal = api;
})(typeof globalThis === 'undefined' ? this : globalThis, function() {
  'use strict';
  const MAX_LINK = 65536, MAX_QUERY = 2048;
  const ID = /^\d{12}$/, EDITION = /^\d{4}-[a-z]{2}-(federais|estaduais)$/;
  const fail = message => { throw new TypeError(message); };
  const clone = v => JSON.parse(JSON.stringify(v));
  const unique = a => [...new Set(a)];
  const fold = v => String(v ?? '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  function safePath(path) {
    if (typeof path !== 'string' || !/^\/(?:[a-z0-9-]+\/)*$/.test(path)) fail('Rota inválida');
    return path;
  }
  function siteBase(input) {
    const u = new URL(input);
    if (!['http:','https:'].includes(u.protocol) || u.username || u.password || u.search || u.hash) fail('Base inválida');
    safePath(u.pathname); return u;
  }
  function routeURL(base, path) { return new URL(safePath(path).slice(1), siteBase(base)).href; }
  function edition(registry, id) {
    const e = registry.editions.find(x => x.edition_id === id || x.legacy_ids.includes(id));
    if (!e) fail('Edição desconhecida'); return e;
  }
  function resolveRoute(registry, base, input, phase = 'current') {
    const b = siteBase(base), u = new URL(input,b);
    if (u.origin !== b.origin || !u.pathname.startsWith(b.pathname)) return null;
    let path = '/' + u.pathname.slice(b.pathname.length);
    path = path.replace(/index\.html$/, '');
    if (path !== '/' && !path.endsWith('/')) path += '/';
    if ((phase === 'next' || registry.root_mode === 'global_home') && path === '/') return {kind:'home',path:'/'};
    for (const e of registry.editions) {
      if (path === e.canonical_path || path === e.current_path || e.aliases.includes(path)) {
        return {kind:'edition',edition_id:e.edition_id,available:e.publication_status === 'published',
          path:phase === 'next' ? e.canonical_path : e.current_path};
      }
    }
    const state = registry.states.find(s => s.path === path && (phase === 'next' || s.published));
    return state ? {kind:'hub',state:state.code,path} : null;
  }
  function catalogContext(editionId, ids) {
    if (!EDITION.test(editionId) || !Array.isArray(ids) || !ids.length || ids.some(x => typeof x !== 'string' || !ID.test(x)) || unique(ids).length !== ids.length) fail('Edição ou catálogo inválido');
    return {edition_id:editionId, ids:ids.slice(), allowed:new Set(ids)};
  }
  function params(hash) {
    if (typeof hash !== 'string' || hash.length > MAX_LINK || /%(?![0-9a-f]{2})/i.test(hash)) fail('Link inválido ou grande demais');
    try { decodeURIComponent(hash); } catch { fail('Codificação inválida'); }
    const p = new URLSearchParams(hash.replace(/^[#?]/,''));
    for (const key of p.keys()) if (p.getAll(key).length !== 1) fail('Parâmetro duplicado');
    return p;
  }
  function createCollection(editionId, ids) {
    const ctx = catalogContext(editionId,ids); let selected = [], active = null;
    const snapshot = () => ({edition_id:editionId,ids:selected.slice(),active});
    function validate(values) {
      if (!Array.isArray(values) || values.some(x => !ctx.allowed.has(x))) fail('Ficha de outra edição ou desconhecida');
      return unique(values);
    }
    return Object.freeze({snapshot,
      add(id) { validate([id]); if (!selected.includes(id)) selected.push(id); active ??= id; return snapshot(); },
      remove(id) { const i=selected.indexOf(id); selected=selected.filter(x=>x!==id); if(active===id) active=selected[Math.min(Math.max(i,0),selected.length-1)]??null; return snapshot(); },
      replace(values, at = null) { const next=validate(values); if(at!==null&&!next.includes(at)) fail('Ficha ativa fora da coleção'); selected=next; active=at??next[0]??null; return snapshot(); },
      open(id) { if(!selected.includes(id)) fail('Ficha não selecionada'); active=id;return snapshot(); },
      next(delta=1) { if(delta!==1&&delta!==-1) fail('Passo inválido'); if(selected.length) active=selected[Math.max(0,Math.min(selected.length-1,selected.indexOf(active)+delta))];return snapshot(); },
      clear() { selected=[];active=null;return snapshot(); }
    });
  }
  function collectionLink(base, state, ids) {
    const ctx=catalogContext(state.edition_id,ids);
    if(!Array.isArray(state.ids)||!state.ids.length||state.ids.some(x=>!ctx.allowed.has(x))||unique(state.ids).length!==state.ids.length) fail('Coleção inválida');
    if(state.active&&!state.ids.includes(state.active)) fail('Ficha ativa inválida');
    const p=new URLSearchParams({eef:'collection',v:'2',edition:state.edition_id,ids:state.ids.join(',')});
    if(state.active)p.set('active',state.active);
    const u=siteBase(base);u.hash=p.toString();
    if(u.href.length>MAX_LINK)throw new RangeError('Link grande demais; nenhum item foi removido');return u.href;
  }
  function parseCollection(hash, editionId, ids) {
    try {
      const ctx=catalogContext(editionId,ids), p=params(hash), legacy=p.has('selecionados');
      if(!legacy && p.get('eef')!=='collection') return {kind:'other'};
      const allowed=legacy?['selecionados','v','edicao','ficha']:['eef','v','edition','ids','active'];
      if([...p.keys()].some(k=>!allowed.includes(k))) fail('Parâmetro desconhecido');
      if(legacy ? (p.get('v')!=='1'||p.get('edicao')!=='sc-federais'||editionId!=='2026-sc-federais') : (p.get('v')!=='2'||p.get('edition')!==editionId)) fail('Versão ou edição incompatível');
      const raw=(p.get(legacy?'selecionados':'ids')||'').split(',');
      if(!raw.length||raw.some(x=>!ctx.allowed.has(x))||unique(raw).length!==raw.length) fail('Coleção inválida; importação não foi aplicada');
      const active=p.get(legacy?'ficha':'active')||raw[0];if(!raw.includes(active))fail('Ficha ativa inválida');
      return {kind:'collection',edition_id:editionId,ids:raw,active,legacy};
    } catch(e) {return {kind:'invalid',reason:e.message};}
  }
  function legacyRootTarget(hash, fixtures, base) {
    if(typeof hash!=='string'||!hash||hash==='#')return null;
    let decoded;try{decoded=decodeURIComponent(hash.slice(1));}catch{return null;}
    const collection=parseCollection(hash,'2026-sc-federais',fixtures.candidate_ids);
    if(fixtures.anchors.includes(decoded)||collection.kind==='collection')return routeURL(base,fixtures.target)+hash;
    return null;
  }
  function emptyQuery(editionId) {
    if(!EDITION.test(editionId))fail('Edição inválida');
    return {edition_id:editionId,q:'',parties:[],topics:[],status:'',mandate:'',history:'',region:'',mode:'any',order:'daily',semantic:null};
  }
  function normalizeQuery(raw, valid, legacy = null) {
    const q=emptyQuery(valid.edition_id), ignored=[];
    if(raw.edition_id&&raw.edition_id!==valid.edition_id)fail('Consulta de outra edição');
    q.q=String(raw.q??'').trim();if(q.q.length>MAX_QUERY)fail('Busca grande demais');
    for(const k of ['parties','topics']) {
      const input=raw[k]??[];if(!Array.isArray(input))fail('Lista de filtros inválida');
      q[k]=unique(input.map(x=>k==='parties'?(valid.parties.find(y=>fold(x)===fold(y))||x):(valid.aliases?.[x]||x))).filter(x=>{
        if((valid[k]||[]).includes(x))return true;ignored.push(k+':'+x);return false;
      }).sort();
    }
    for(const [k,choices] of [['status',valid.statuses||[]],['mandate',valid.mandates||['','true','false']],['history',valid.histories||['','true','false']],['region',valid.regions||[]]]) {
      const v=raw[k]??'';if(v===''||choices.includes(v))q[k]=v;else ignored.push(k+':'+v);
    }
    const modes=valid.modes||['any','all'],orders=valid.orders||['daily','alphabetical'];
    q.mode=raw.mode==='all'?'all':'any';q.order=raw.order==='alphabetical'?'alphabetical':'daily';
    if(!modes.includes(q.mode)){ignored.push('mode:'+q.mode);q.mode=modes[0]||'any';}
    if(!orders.includes(q.order)){ignored.push('order:'+q.order);q.order=orders[0]||'daily';}
    if(raw.mode&&!['all','any'].includes(raw.mode))ignored.push('mode');
    if(raw.order&&!['daily','alphabetical'].includes(raw.order))ignored.push('order');
    q.semantic=valid.semantic||null;
    if(raw.semantic&&raw.semantic!==q.semantic)fail('Semântica incompatível');
    if(legacy==='PR')q.mode='all';
    return {state:q,ignored};
  }
  function importLegacyQuery(search, valid, dialect) {
    if(!['PR','SP'].includes(dialect))fail('Importador não suportado');
    const p=params(search), allowed=dialect==='PR'?['q','partido','pautas','situacao','mandato','historico','regiao']:['q','partidos','pautas','situacao','modo','ordem'];
    const result=normalizeQuery({q:p.get('q'),parties:(p.get(dialect==='PR'?'partido':'partidos')||'').split(',').filter(Boolean),
      topics:(p.get('pautas')||'').split(',').filter(Boolean),status:p.get('situacao'),mandate:p.get('mandato'),history:p.get('historico'),region:p.get('regiao'),
      mode:dialect==='PR'||p.get('modo')==='todos'?'all':'any',order:p.get('ordem')==='alfabetica'?'alphabetical':'daily'},valid,dialect);
    result.ignored.push(...[...p.keys()].filter(k=>!allowed.includes(k)));return result;
  }
  function queryLink(base, state, valid) {
    const r=normalizeQuery(state,valid);if(r.ignored.length)fail('Consulta inválida; não foi truncada');
    const u=siteBase(base),p=new URLSearchParams({eef:'query',v:'1',edition:valid.edition_id,state:JSON.stringify(r.state)});u.hash=p.toString();
    if(u.href.length>MAX_LINK)throw new RangeError('Link grande demais');return u.href;
  }
  function parseQuery(hash,valid) {
    try {
      const p=params(hash);if(p.get('eef')!=='query')return {kind:'other'};
      if([...p.keys()].some(k=>!['eef','v','edition','state'].includes(k))||p.get('v')!=='1'||p.get('edition')!==valid.edition_id)fail('Consulta incompatível');
      const raw=JSON.parse(p.get('state'));if(!raw||Array.isArray(raw)||typeof raw!=='object')fail('Consulta inválida');
      if(Object.keys(raw).some(k=>!Object.hasOwn(emptyQuery(valid.edition_id),k)))fail('Campo desconhecido');
      const r=normalizeQuery(raw,valid);if(r.ignored.length)fail('Critérios inválidos; importação não aplicada');return {kind:'query',...r};
    } catch(e) {return {kind:'invalid',reason:e.message};}
  }
  function createQuerySession(valid) {
    let state=emptyQuery(valid.edition_id);
    return Object.freeze({snapshot:()=>clone(state),
      update(raw){const r=normalizeQuery({...state,...raw},valid);if(r.ignored.length)fail('Critério inválido');state=r.state;return clone(state);},
      restore(hash){const r=parseQuery(hash,valid);if(r.kind==='query')state=r.state;return r;},
      clear(){state=emptyQuery(valid.edition_id);return clone(state);}
    });
  }
  function bindQueryNavigation(session, valid, host, dialect = null) {
    let lastSearch = null;
    function restore() {
      const result = session.restore(host.location.hash);
      if (result.kind === 'other' && dialect && host.location.search !== lastSearch) {
        const imported = importLegacyQuery(host.location.search,valid,dialect);
        session.update(imported.state);
      }
      lastSearch = host.location.search;
      return result;
    }
    host.addEventListener('popstate',restore);host.addEventListener('hashchange',restore);restore();
    return () => {host.removeEventListener('popstate',restore);host.removeEventListener('hashchange',restore);};
  }
  function matches(record, query) {
    if(query.edition_id!==record.edition_id)return false;
    if(query.topics.length&&record.semantic!==query.semantic)return false;
    const text=fold(record.search||'');
    return fold(query.q).split(/\s+/).filter(Boolean).every(t=>text.includes(t)) &&
      (!query.parties.length||query.parties.includes(record.party)) && (!query.status||query.status===record.status) &&
      (!query.mandate||query.mandate===record.mandate) && (!query.history||query.history===record.history) && (!query.region||query.region===record.region) &&
      (!query.topics.length||(query.mode==='all'?query.topics.every(t=>(record.topics||[]).includes(t)):query.topics.some(t=>(record.topics||[]).includes(t))));
  }
  return Object.freeze({MAX_LINK,MAX_QUERY,fold,safePath,siteBase,routeURL,edition,resolveRoute,catalogContext,createCollection,
    collectionLink,parseCollection,legacyRootTarget,emptyQuery,normalizeQuery,importLegacyQuery,queryLink,parseQuery,createQuerySession,bindQueryNavigation,matches});
});

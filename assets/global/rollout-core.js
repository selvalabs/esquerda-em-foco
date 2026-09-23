/* Global D1 query specification in production. No DOM, network, storage or scoring. */
(function(root,factory){const api=factory(typeof module==='object'&&module.exports?require('./core.js'):root.EEFGlobal);if(typeof module==='object'&&module.exports)module.exports=api;else root.EEFCanonicalQuery=api;})(typeof globalThis==='undefined'?this:globalThis,function(legacyCore){
 'use strict';
 const MAX=65536, scopes=['documented_topic','current_support','legacy_context'];
 const fields=['registration','aptitude','mandate','history','region'];
 const fold=x=>String(x??'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR');
 const copy=x=>JSON.parse(JSON.stringify(x));const fail=t=>{throw new TypeError(t);};
 function empty(cfg){return {edition_id:cfg.edition_id,taxonomy_version:cfg.taxonomy_version,q:'',parties:[],selectors:[],scope:'documented_topic',mode:'any',registration:'',aptitude:'',mandate:'',history:'',region:'',order:'daily'};}
 function topicSet(cfg,selector){
  if(selector.kind==='topic'){if(!cfg.topics.some(t=>t.id===selector.id))fail('Tema desconhecido');return [selector.id];}
  if(selector.kind==='group'){const g=cfg.groups.find(g=>g.id===selector.id);if(!g)fail('Grupo desconhecido');return g.members.slice();}
  if(selector.kind==='legacy'){if(!cfg.legacy_contract.valid.topics.includes(selector.id))fail('Tema antigo desconhecido');return [];}
  fail('Tipo de filtro desconhecido');
 }
 function normalize(input,cfg){
  if(!input||typeof input!=='object'||Array.isArray(input))fail('Consulta inválida');
  const q=empty(cfg);if(Object.keys(input).some(k=>!Object.hasOwn(q,k)))fail('Campo de consulta desconhecido');
  if(input.edition_id!==cfg.edition_id||input.taxonomy_version!==cfg.taxonomy_version)fail('Consulta de outra edição ou taxonomia');
  if(typeof input.q!=='string'||input.q.length>2048)fail('Busca inválida ou longa demais');q.q=input.q.trim();
  if(!Array.isArray(input.parties)||input.parties.some(p=>typeof p!=='string'||!cfg.parties.includes(p)))fail('Partido desconhecido');
  q.parties=[...new Set(input.parties)].sort();
  if(!scopes.includes(input.scope)||!['any','all'].includes(input.mode)||!['daily','alphabetical'].includes(input.order))fail('Recorte, combinação ou ordem inválidos');
  q.scope=input.scope;q.mode=input.mode;q.order=input.order;
  if(!Array.isArray(input.selectors)||input.selectors.length>100)fail('Seleção de temas inválida');
  for(const s of input.selectors){
   if(!s||typeof s!=='object'||Object.keys(s).sort().join(',')!=='id,kind'||typeof s.id!=='string')fail('Seletor inválido');topicSet(cfg,s);
   if(!q.selectors.some(x=>x.id===s.id&&x.kind===s.kind))q.selectors.push({kind:s.kind,id:s.id});
  }
  // A selected child already satisfies its parent in ALL. Do not impose redundant clauses.
  if(q.mode==='all')q.selectors=q.selectors.filter(s=>s.kind!=='group'||!q.selectors.some(c=>c.kind==='topic'&&topicSet(cfg,s).includes(c.id)));
  q.selectors.sort((a,b)=>(a.kind+':'+a.id).localeCompare(b.kind+':'+b.id));
  for(const f of fields){
   const v=input[f];if(typeof v!=='string')fail('Campo inválido: '+f);
   if(!v){q[f]='';continue;}
   const dim=cfg.dimensions.find(x=>x.id===f);
   if(v.startsWith('legacy:')){
    const old={registration:'statuses',mandate:'mandates',history:'histories',region:'regions'}[f];
    if(!old||!cfg.legacy_contract.valid[old]?.includes(v.slice(7)))fail('Critério antigo inválido');
   }else if(!dim||!dim.options.some(x=>x.value===v))fail('Valor desconhecido: '+f);
   q[f]=v;
  }
  return q;
 }
 function hasCriteria(q){return !!(q.q||q.parties.length||q.selectors.length||fields.some(f=>q[f])||q.order!=='daily');}
 function evidenceMatches(record,q,cfg){
  const target=new Set(q.selectors.filter(s=>s.kind!=='legacy').flatMap(s=>topicSet(cfg,s)));
  return record.evidence.filter(e=>e.scopes.includes(q.scope)&&target.has(e.topic));
 }
 function matches(record,q,cfg){
  if(q.parties.length&&!q.parties.includes(record.party))return false;
  if(!fold(q.q).split(/\s+/).filter(Boolean).every(t=>fold(record.search).includes(t)))return false;
  for(const f of fields){
   if(!q[f])continue;
   if(q[f].startsWith('legacy:')){
    const old={registration:'status',mandate:'mandate',history:'history',region:'region'}[f],wanted=q[f].slice(7);
    const got=record.legacy[old];
    if(f==='registration'&&cfg.legacy_contract.dialect==='PR'&&wanted==='nao-confirmada'){if(!['nao-confirmada','deferida-sem-confirmacao-api'].includes(got))return false;}
    else if(got!==wanted)return false;
   }else if(record[f]!==q[f])return false;
  }
  if(!q.selectors.length)return true;
  const own=new Set(record.evidence.filter(e=>e.scopes.includes(q.scope)).map(e=>e.topic));
  const hits=q.selectors.map(s=>s.kind==='legacy'?record.legacy.topics.includes(s.id):topicSet(cfg,s).some(t=>own.has(t)));
  return q.mode==='all'?hits.every(Boolean):hits.some(Boolean);
 }
 function validateConfig(cfg){
  if(!/^\d{4}-[a-z]{2}-(federais|estaduais)$/.test(cfg.edition_id)||cfg.taxonomy_version!=='1.0.0')fail('Contrato de edição inválido');
  if(!Array.isArray(cfg.records)||!cfg.records.length||cfg.records.some(r=>!/^\d{12}$/.test(r.id))||new Set(cfg.records.map(r=>r.id)).size!==cfg.records.length)fail('Catálogo inválido');
  for(const r of cfg.records)for(const e of r.evidence){if(!cfg.topics.some(t=>t.id===e.topic)||!e.scopes.length||e.scopes.some(s=>!scopes.includes(s))||!e.object||!e.sources.length)fail('Vínculo sem evidência');}
  return true;
 }
 function fromLegacy(old,cfg){
  const parsed=legacyCore.normalizeQuery(old,cfg.legacy_contract.valid);if(parsed.ignored.length)fail('Critério antigo inválido; importação não aplicada');
  const s=parsed.state,q=empty(cfg);q.q=s.q;q.parties=s.parties;q.scope=s.semantic||'documented_topic';q.mode=s.mode;q.order=s.order;
  q.selectors=s.topics.map(id=>({kind:'legacy',id}));
  for(const [oldKey,key] of [['status','registration'],['mandate','mandate'],['history','history'],['region','region']])if(s[oldKey])q[key]='legacy:'+s[oldKey];
  return normalize(q,cfg);
 }
 function params(hash){
  if(typeof hash!=='string'||hash.length>MAX||/%(?![0-9a-f]{2})/i.test(hash))fail('Link inválido ou longo demais');
  try{decodeURIComponent(hash);}catch{fail('Codificação inválida');}
  const p=new URLSearchParams(hash.replace(/^[#?]/,''));for(const k of p.keys())if(p.getAll(k).length!==1)fail('Parâmetro repetido');return p;
 }
 function parse(hash,cfg){
  try{
   const p=params(hash);if(p.get('eef')!=='query')return {kind:'other'};
   if(p.get('v')==='1'){
    const old=legacyCore.parseQuery(hash,cfg.legacy_contract.valid);if(old.kind!=='query')return old;
    return {kind:'query',state:fromLegacy(old.state,cfg),legacy:true};
   }
   if(p.get('v')!=='2'||p.get('edition')!==cfg.edition_id||[...p.keys()].some(k=>!['eef','v','edition','taxonomy','state'].includes(k))||p.get('taxonomy')!==cfg.taxonomy_version)fail('Versão, edição ou taxonomia incompatível');
   return {kind:'query',state:normalize(JSON.parse(p.get('state')),cfg),legacy:false};
  }catch(e){return {kind:'invalid',reason:e.message};}
 }
 function importSearch(search,cfg){
  if(!cfg.legacy_contract.dialect)return {kind:'other'};
  try{const old=legacyCore.importLegacyQuery(search,cfg.legacy_contract.valid,cfg.legacy_contract.dialect);return {kind:'query',state:fromLegacy(old.state,cfg),legacy:true,ignored:old.ignored};}catch(e){return {kind:'invalid',reason:e.message};}
 }
 function link(base,state,cfg){
  const q=normalize(state,cfg),u=legacyCore.siteBase(base);u.hash=new URLSearchParams({eef:'query',v:'2',edition:cfg.edition_id,taxonomy:cfg.taxonomy_version,state:JSON.stringify(q)}).toString();if(u.href.length>MAX)throw new RangeError('Link longo demais; nenhum critério foi removido');return u.href;
 }
 return Object.freeze({empty,normalize,hasCriteria,matches,evidenceMatches,topicSet,validateConfig,fromLegacy,parse,importSearch,link,fold,copy});
});

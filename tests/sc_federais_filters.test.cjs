'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const core = require('../assets/pauta-filter-core.js');
const payload = JSON.parse(fs.readFileSync('data/sc-federais-filters-v1/payload.json', 'utf8'));
const matrix = JSON.parse(fs.readFileSync('data/sc-federais-topics-v1/matrix.json', 'utf8'));
const records = payload.candidates.map(c => ({id:c.id, topicIds:c.topicIds, text:matrix.candidates.find(m=>m.candidate_id===c.id).name}));
const topics = payload.topics.map(t=>t.id);
function expected(selected, mode) {
  return matrix.candidates.filter(c=>!selected.length || (mode==='all' ? selected.every(t=>c.current_support_topic_ids.includes(t)) : selected.some(t=>c.current_support_topic_ids.includes(t)))).map(c=>c.candidate_id);
}
function actual(selected, mode='any', query='') { return core.filter(records,{topics:selected, mode, query}).map(c=>c.id); }
test('Sem seleção: todas as 48 fichas, inclusive as sem associações',()=>{
  assert.equal(records.length,48); assert.deepEqual(actual([]), records.map(c=>c.id)); assert.deepEqual(actual([], 'all'),actual([]));
});
test('Cada chip corresponde aos apoios explícitos na matriz, não a palavras no nome',()=>{
  for(const t of topics) assert.deepEqual(actual([t]),expected([t],'any'),t);
  assert(!actual(['saude']).includes('240002533818'));
});
test('Todas as combinações de duas pautas: OR e AND independentes da implementação',()=>{
  for(const a of topics) for(const b of topics) for(const mode of ['any','all']) assert.deepEqual(actual([a,b],mode),expected([a,b],mode),`${a}/${b}/${mode}`);
});
test('Combinações de três pautas e seleção do catálogo inteiro',()=>{
  for(let i=0;i<topics.length;i++) for(const mode of ['any','all']) {
    const selection=[topics[i],topics[(i+3)%topics.length],topics[(i+7)%topics.length]];
    assert.deepEqual(actual(selection,mode),expected(selection,mode));
  }
  for(const mode of ['any','all']) assert.deepEqual(actual(topics,mode),expected(topics,mode));
});
test('Busca normalizada se combina por interseção com a seleção temática',()=>{
  assert.equal(core.normalize('  JÉSSICA   Michels '),'jessica michels');
  for(const mode of ['any','all']) for(const query of ['JÉSSICA','caren','Nandja','inexistente-xyz']) {
    const selection=['saude','educacao'];
    const ids=expected(selection,mode).filter(id=>core.normalize(records.find(r=>r.id===id).text).includes(core.normalize(query)));
    assert.deepEqual(actual(selection,mode,query),ids);
  }
});
test('Contagens são por pessoa e não por quantidade de fontes ou frases',()=>{
  const counts=core.counts(records, topics);
  for(const t of payload.topics) assert.equal(counts[t.id],t.count);
  assert.equal(core.counts([{topicIds:['saude','saude']}],['saude']).saude,1);
});
test('Filtrar preserva a ordem de entrada em qualquer rotação diária',()=>{
  for(let offset=0;offset<records.length;offset++) {
    const order=records.slice(offset).concat(records.slice(0,offset));
    const allowed=new Set(expected(['saude'],'any'));
    assert.deepEqual(core.filter(order,{topics:['saude']}).map(c=>c.id),order.filter(c=>allowed.has(c.id)).map(c=>c.id));
  }
});
test('Nenhuma mutação dos dados ou da seleção',()=>{
  const input=JSON.stringify(records); const selected=new Set(['saude','educacao']);
  core.filter(records,{topics:selected,mode:'all'}); core.counts(records,topics);
  assert.equal(JSON.stringify(records),input); assert.deepEqual([...selected],['saude','educacao']);
});
test('Histórico, oposição isolada, debate e data indeterminada não viram apoio',()=>{
  const ids=new Set(payload.candidates.flatMap(c=>c.matches.map(m=>m.associationId)));
  for(const a of matrix.associations) assert.equal(ids.has(a.association_id),a.eligible_current_support,a.association_id);
  assert(!actual(['educacao']).includes('240002533825')); // oposição a modalidades não é apoio à família
  assert(!actual(['educacao']).includes('240002533833')); // requerimento de debate não equivale a apoio
  assert(!actual(['educacao']).includes('240002541412')); // apresentação sem período determinado
});
test('Tema desconhecido não causa inclusão indevida',()=>{
  assert.deepEqual(actual(['nao-existe']),[]);
  assert.deepEqual(actual(['saude','nao-existe'],'all'),[]);
  assert.deepEqual(actual(['saude','nao-existe'],'any'),actual(['saude']));
});

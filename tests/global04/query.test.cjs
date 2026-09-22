'use strict';
const test=require('node:test'),assert=require('node:assert/strict');
const C=require('../../assets/global/core.js');
const BASE='https://example.test/esquerda-em-foco/';
const baseState=e=>({...C.emptyQuery(e)});
const val={edition_id:'2026-pr-federais',parties:['PCdoB','PSOL','PT'],topics:['saude','educacao'],statuses:['apta','inapta'],regions:['Curitiba','Londrina'],mandates:['','true','false'],histories:['','true','false'],modes:['all'],orders:['daily'],semantic:'legacy_context',aliases:{}};

test('adapter-specific modes and orders reject semantic drift',()=>{
  const good=C.normalizeQuery({...baseState(val.edition_id),topics:['saude'],mode:'all',semantic:'legacy_context'},val);
  assert.equal(good.ignored.length,0);assert.equal(good.state.mode,'all');assert.equal(good.state.order,'daily');
  const bad=C.normalizeQuery({...baseState(val.edition_id),mode:'any',semantic:'legacy_context'},val);
  assert.ok(bad.ignored.includes('mode:any'));assert.equal(bad.state.mode,'all');
});

test('adapter-specific mandate/history options remain explicit',()=>{
  const sc={...val,edition_id:'2026-sc-estaduais',topics:[],regions:[],mandates:['','true'],histories:['','true','false'],modes:['any'],semantic:null};
  assert.equal(C.normalizeQuery({...baseState(sc.edition_id),mandate:'true'},sc).ignored.length,0);
  assert.ok(C.normalizeQuery({...baseState(sc.edition_id),mandate:'false'},sc).ignored.includes('mandate:false'));
});

test('common query link is fragment-only, reversible, scoped to edition',()=>{
  const state={...baseState(val.edition_id),q:'água pública',parties:['PT','PSOL'],topics:['saude'],status:'apta',mandate:'true',history:'true',region:'Curitiba',mode:'all',order:'daily',semantic:'legacy_context'};
  const link=C.queryLink(BASE,state,val),u=new URL(link);
  assert.equal(u.search,'');assert.match(u.hash,/^#eef=query&v=1&edition=2026-pr-federais&state=/);
  const parsed=C.parseQuery(u.hash,val);assert.equal(parsed.kind,'query');assert.deepEqual(parsed.state,C.normalizeQuery(state,val).state);
  assert.equal(C.parseQuery(u.hash,{...val,edition_id:'2026-pr-estaduais'}).kind,'invalid');
});

test('legacy PR preserves singular party and AND themes',()=>{
  const out=C.importLegacyQuery('?q=agua&partido=pt&pautas=saude,educacao&situacao=apta&mandato=true&historico=false&regiao=Curitiba',val,'PR');
  assert.deepEqual(out.state.parties,['PT']);assert.deepEqual(out.state.topics,['educacao','saude']);assert.equal(out.state.mode,'all');assert.equal(out.state.order,'daily');assert.deepEqual(out.ignored,[]);
});

test('legacy SP preserves multiple parties and OR/all modes without crosswalk inference',()=>{
  const sp={edition_id:'2026-sp-federais',parties:['PCdoB','PSOL','PT'],topics:['ciencia-tecnologia','saude'],statuses:['apta'],regions:[],mandates:[''],histories:[''],modes:['any','all'],orders:['daily','alphabetical'],semantic:'documented_topic',aliases:{ciencia:'ciencia-tecnologia'}};
  let out=C.importLegacyQuery('?partidos=psol,PT&pautas=ciencia&situacao=apta&ordem=alfabetica',sp,'SP');
  assert.deepEqual(out.state.parties,['PSOL','PT']);assert.deepEqual(out.state.topics,['ciencia-tecnologia']);assert.equal(out.state.mode,'any');assert.equal(out.state.order,'alphabetical');
  out=C.importLegacyQuery('?partidos=PT&pautas=saude&modo=todos',sp,'SP');assert.equal(out.state.mode,'all');
});

test('new party filtering is OR and never changes semantic type',()=>{
  const q={...baseState(val.edition_id),parties:['PT','PSOL'],semantic:'legacy_context',mode:'all'};
  const a={edition_id:val.edition_id,party:'PT',status:'',mandate:'',history:'',region:'',semantic:'legacy_context',search:'',topics:[]};
  const b={...a,party:'PSOL'},c={...a,party:'PCdoB'},wrong={...a,semantic:'current_support'};
  assert.equal(C.matches(a,q),true);assert.equal(C.matches(b,q),true);assert.equal(C.matches(c,q),false);
  q.topics=['saude'];assert.equal(C.matches(wrong,q),false);
});

test('invalid or foreign query is atomic and does not become partial state',()=>{
  const session=C.createQuerySession(val);session.update({parties:['PT'],mode:'all',semantic:'legacy_context'});const before=session.snapshot();
  const other={...before,edition_id:'2026-pr-estaduais'};
  const p=new URLSearchParams({eef:'query',v:'1',edition:'2026-pr-estaduais',state:JSON.stringify(other)});
  const out=session.restore('#'+p.toString());assert.equal(out.kind,'invalid');assert.deepEqual(session.snapshot(),before);
  const bad=new URLSearchParams({eef:'query',v:'1',edition:val.edition_id,state:JSON.stringify({...before,parties:['INVALID']})});
  assert.equal(session.restore('#'+bad).kind,'invalid');assert.deepEqual(session.snapshot(),before);
});

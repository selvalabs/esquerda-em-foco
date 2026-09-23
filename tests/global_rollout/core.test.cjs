'use strict';
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),test=require('node:test');
const C=require('../../assets/global/rollout-core.js'),old=require('../../assets/global/core.js');
const root=path.resolve(__dirname,'../..');
const registry=JSON.parse(fs.readFileSync(path.join(root,'config/editions.json'),'utf8'));
const editionConfig=e=>{
 const html=fs.readFileSync(path.join(root,e.entrypoint),'utf8');
 const match=html.match(/<script[^>]+id="cqData"[^>]*>([\s\S]*?)<\/script>/);assert.ok(match,'Generated query data missing');return JSON.parse(match[1]);
};
const editions=registry.editions.filter(e=>e.publication_status==='published');
let total=0,oracleCases=0;
// Independent reference function; deliberately does not call the production matcher.
function reference(r,s,cfg){
 const normal=x=>String(x).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 if(s.q.trim().split(/\s+/).filter(Boolean).some(x=>!normal(r.search).includes(normal(x))))return false;
 if(s.parties.length&&!s.parties.includes(r.party))return false;
 for(const field of ['registration','aptitude','mandate','history','region']){
  const want=s[field];if(!want)continue;
  if(want.startsWith('legacy:')){
   const k={registration:'status',mandate:'mandate',history:'history',region:'region'}[field],v=want.slice(7);
   const accepted=field==='registration'&&cfg.legacy_contract.dialect==='PR'&&v==='nao-confirmada'?['nao-confirmada','deferida-sem-confirmacao-api']:[v];
   if(!accepted.includes(r.legacy[k]))return false;
  }else if(r[field]!==want)return false;
 }
 const hits=s.selectors.map(filter=>{
  if(filter.kind==='legacy')return r.legacy.topics.indexOf(filter.id)>=0;
  const topics=filter.kind==='topic'?[filter.id]:cfg.groups.find(x=>x.id===filter.id).members;
  return r.evidence.some(e=>topics.includes(e.topic)&&e.scopes.includes(s.scope));
 });
 return !hits.length||(s.mode==='all'?hits.every(x=>x):hits.some(x=>x));
}
for(const edition of editions){
 const cfg=editionConfig(edition);total+=cfg.records.length;
 test(cfg.edition_id+' valid identities and 39/16 contract',()=>{assert.equal(C.validateConfig(cfg),true);assert.equal(cfg.topics.length,39);assert.equal(cfg.groups.length,16);assert.equal(new Set(cfg.records.map(r=>r.id)).size,cfg.records.length);});
 test(cfg.edition_id+' exact independent combinations',()=>{
  const q=C.empty(cfg),cases=[q];
  for(let i=0;i<cfg.parties.length;i++)for(let j=i;j<cfg.parties.length;j++)cases.push({...q,parties:[...new Set([cfg.parties[i],cfg.parties[j]])]});
  for(const d of cfg.dimensions)for(const v of d.options)cases.push({...q,[d.id]:v.value});
  for(const scope of ['documented_topic','current_support','legacy_context']){
   for(const t of cfg.topics)cases.push({...q,scope,selectors:[{kind:'topic',id:t.id}]});
   for(const g of cfg.groups)cases.push({...q,scope,selectors:[{kind:'group',id:g.id}]});
   for(const mode of ['any','all'])for(let i=0;i<cfg.topics.length-1;i+=2)cases.push({...q,scope,mode,parties:cfg.parties.slice(0,2),selectors:cfg.topics.slice(i,i+2).map(t=>({kind:'topic',id:t.id}))});
  }
  for(const raw of cases){const s=C.normalize(raw,cfg);const actual=cfg.records.filter(r=>C.matches(r,s,cfg)).map(r=>r.id);const expected=cfg.records.filter(r=>reference(r,s,cfg)).map(r=>r.id);assert.deepEqual(actual,expected);oracleCases++;}
 });
 test(cfg.edition_id+' legacy v1 single and all native themes exact',()=>{
  const valid=cfg.legacy_contract.valid;
  for(const mode of valid.modes)for(const id of valid.topics){
   const s={...old.emptyQuery(cfg.edition_id),topics:[id],mode,semantic:valid.semantic};
   const link=old.queryLink('https://example.test/'+cfg.edition_id+'/',s,valid);
   const imported=C.parse(new URL(link).hash,cfg);assert.equal(imported.kind,'query');assert.equal(imported.legacy,true);
   const actual=cfg.records.filter(r=>C.matches(r,imported.state,cfg)).map(r=>r.id);
   const expected=cfg.records.filter(r=>r.legacy.topics.includes(id)).map(r=>r.id);assert.deepEqual(actual,expected);
  }
 });
 test(cfg.edition_id+' all v2 fields and selectors round trip',()=>{
  const s={...C.empty(cfg),q:'Água educação',parties:cfg.parties.slice(0,2),scope:'legacy_context',mode:'all',order:'alphabetical',selectors:[{kind:'topic',id:cfg.topics[0].id}]};
  for(const d of cfg.dimensions)if(d.options.length)s[d.id]=d.options[0].value;
  const normalized=C.normalize(s,cfg),link=C.link('https://example.test/project/',normalized,cfg),p=C.parse(new URL(link).hash,cfg);assert.equal(p.kind,'query');assert.deepEqual(p.state,normalized);assert.equal(new URL(link).search,'');
 });
 test(cfg.edition_id+' foreign edition, version, malformed state rejected',()=>{
  const s=C.empty(cfg),link=C.link('https://example.test/',s,cfg),hash=new URL(link).hash;
  assert.equal(C.parse(hash.replace('taxonomy=1.0.0','taxonomy=9.9.9'),cfg).kind,'invalid');
  assert.equal(C.parse(hash.replace('edition='+cfg.edition_id,'edition=2030-sp-federais'),cfg).kind,'invalid');
  assert.equal(C.parse(hash+'&v=2',cfg).kind,'invalid');
  assert.throws(()=>C.normalize({...s,parties:['__proto__']},cfg));assert.throws(()=>C.normalize({...s,selectors:[{kind:'topic',id:'__proto__'}]},cfg));
  assert.throws(()=>C.normalize({...s,q:5},cfg));assert.throws(()=>C.normalize({...s,q:'x'.repeat(2049)},cfg));
  assert.throws(()=>C.normalize({...s,unexpected:true},cfg));
 });
 test(cfg.edition_id+' group/child redundancy never creates sibling membership',()=>{
  const g=cfg.groups.find(g=>g.members.length>1),s=C.normalize({...C.empty(cfg),mode:'all',selectors:[{kind:'group',id:g.id},{kind:'topic',id:g.members[0]}]},cfg);
  assert.deepEqual(s.selectors,[{kind:'topic',id:g.members[0]}]);
  const artificial={...cfg.records[0],evidence:[{topic:g.members[0],scopes:['documented_topic']}],legacy:{topics:[]}};
  assert.equal(C.matches(artificial,{...s,selectors:[{kind:'topic',id:g.members[1]}]},cfg),false);
 });
 if(cfg.legacy_contract.dialect==='PR')test(cfg.edition_id+' PR new ANY vs old ALL, no new associations',()=>{
  const topics=cfg.legacy_contract.valid.topics.slice(0,2);const parsed=C.importSearch('?pautas='+topics.join(','),cfg);assert.equal(parsed.state.mode,'all');
  assert.equal(C.empty(cfg).mode,'any');const any={...parsed.state,mode:'any'};
  const ids=cfg.records.filter(r=>C.matches(r,any,cfg)).map(r=>r.id);assert.deepEqual(ids,cfg.records.filter(r=>topics.some(t=>r.legacy.topics.includes(t))).map(r=>r.id));
 });
}
test('760 records and independent test breadth',()=>{assert.equal(total,760);assert.ok(oracleCases>1500,oracleCases);console.log('independent query combinations:',oracleCases);});

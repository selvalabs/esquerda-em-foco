const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const core = require('../assets/pauta-filter-core.js');
const data = JSON.parse(fs.readFileSync('data/sc-semantic-v2-ui/payload.json'));
const audit = JSON.parse(fs.readFileSync('data/sc-semantic-v2/association-audit.json')).associations;
const model = JSON.parse(fs.readFileSync('data/sc-semantic-v2/candidate-content.json')).candidates;
const records = data.candidates.map(c=>({...c,text:model.find(m=>m.candidate_id===c.id).name}));
const tids = data.topics.map(t=>t.id);
function independent(selected,mode){
  return model.filter(c=>{
    const own = new Set(audit.filter(a=>a.candidate_id===c.candidate_id&&a.eligible_v2).map(a=>a.macro_id));
    return !selected.length || (mode==='all' ? selected.every(t=>own.has(t)) : selected.some(t=>own.has(t)));
  }).map(c=>c.candidate_id).sort();
}
test('Universe remains 48 without filters',()=>assert.equal(core.filter(records,{}).length,48));
test('Every macro derives only from its eligible associations',()=>{
  for(const c of records){
    assert.deepEqual(c.topicIds,[...new Set(audit.filter(a=>a.candidate_id===c.id&&a.eligible_v2).map(a=>a.macro_id))].sort());
  }
});
test('All one/two/three-group OR and AND combinations match independent audit',()=>{
  const selections=[[],tids];
  for(let i=0;i<tids.length;i++){
    selections.push([tids[i]]);
    for(let j=i+1;j<tids.length;j++){
      selections.push([tids[i],tids[j]]);
      for(let k=j+1;k<tids.length;k++)selections.push([tids[i],tids[j],tids[k]]);
    }
  }
  for(const topics of selections)for(const mode of ['any','all']){
    assert.deepEqual(core.filter(records,{topics,mode}).map(c=>c.id).sort(),independent(topics,mode));
  }
});
test('Counts deduplicate people, not claims',()=>assert.deepEqual(core.counts(records,tids),Object.fromEntries(data.topics.map(t=>[t.id,t.count]))));
test('The 11 downgraded associations never re-enter payload',()=>{
  const ids=new Set(records.flatMap(c=>c.matches.map(m=>m.associationId)));
  assert.equal(ids.size,112);
  for(const a of audit.filter(a=>a.eligible_v1&&!a.eligible_v2))assert.equal(ids.has(a.association_id),false);
});
test('Broad group membership never adds all its sibling families',()=>{
  const ju=records.find(c=>c.id==='240002533832');
  assert.ok(ju.topicIds.includes('economia-estado'));
  assert.ok(!ju.matches.some(m=>['apostas-jogos','empresas-publicas-privatizacoes'].includes(m.familyId)));
});
test('Unknown group yields no candidates',()=>assert.equal(core.filter(records,{topics:['not-a-topic']}).length,0));
test('Text search normalizes accents and combines with topics',()=>{
  assert.equal(core.filter(records,{query:'  JU  ',topics:['economia-estado']})[0].id,'240002533832');
  assert.equal(core.normalize('TRIBUTAÇÃO'),'tributacao');
});
test('Daily display order is not changed by filter and inputs do not mutate',()=>{
  const snapshot=JSON.stringify(records);
  const reverse=[...records].reverse();
  const found=core.filter(reverse,{topics:['saude']});
  assert.deepEqual(found.map(c=>c.id),reverse.filter(c=>independent(['saude']).includes(c.id)).map(c=>c.id));
  assert.equal(JSON.stringify(records),snapshot);
});

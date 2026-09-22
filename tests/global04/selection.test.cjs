'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const C=require('../../assets/global/core.js'),B=require('../../assets/global/selection-adapter.js'),S=require('../../assets/selecionados-core.js');
const catalog=n=>Array.from({length:n},(_,i)=>String(250000000000+i));
for(const [edition,size] of [['sc-federais',48],['sc-estaduais',97],['rs-federais',111],['pr-federais',115],['pr-estaduais',140],['sp-federais',249],['sp-federais',513],['sp-federais',3000]])test(edition+' complete collection '+size,()=>{
 const ids=catalog(size),a=B.bind({edition_id:'2026-'+edition,election_year:2026,label:edition},ids,S),store=a.createStore();
 for(const id of ids)store.toggle(id);
 assert.deepEqual(store.snapshot(),ids);assert.equal(store.size(),size);
 const snapshot=store.snapshot();snapshot.reverse();assert.deepEqual(store.snapshot(),ids);
 const href=a.collectionUrl('https://example.test/site/'+edition+'/',store.snapshot(),ids,ids.at(-1));
 const result=a.parseFragment(new URL(href).hash);assert.equal(result.kind,'collection');assert.deepEqual(result.ids,ids);assert.equal(result.active,ids.at(-1));assert.equal(result.edition_id,'2026-'+edition);
 assert.equal(a.parseFragment('#candidato-'+ids[0]).id,ids[0]);
});
test('no cross-edition import even when ID catalogs coincide',()=>{
 const ids=catalog(3),a=B.bind({edition_id:'2026-sc-federais'},ids,S),b=B.bind({edition_id:'2026-pr-estaduais'},ids,S);
 const href=a.collectionUrl('https://example.test/sc/',ids,ids,ids[1]);assert.equal(b.parseFragment(new URL(href).hash).kind,'invalid');
});
test('no cross-year import',()=>{
 const ids=catalog(3),a=B.bind({edition_id:'2026-sc-federais'},ids,S),b=B.bind({edition_id:'2030-sc-federais'},ids,S);
 assert.equal(b.parseFragment(new URL(a.collectionUrl('https://example.test/',ids,ids,ids[0])).hash).kind,'invalid');
});
test('SC v1 incoming links remain supported; outgoing links are v2',()=>{
 const ids=catalog(3),a=B.bind({edition_id:'2026-sc-federais'},ids,S);
 const old='#selecionados='+ids.join(',')+'&v=1&edicao=sc-federais&ficha='+ids[1];
 assert.deepEqual(a.parseFragment(old).ids,ids);assert.equal(a.parseFragment(old).active,ids[1]);assert.equal(new URL(a.collectionUrl('https://example.test/',ids,ids,ids[1])).hash.includes('v=2'),true);
});
test('invalid replacement is atomic; remove and reinsert keeps insertion order',()=>{
 const ids=catalog(3),a=B.bind({edition_id:'2026-sp-federais'},ids,S),s=a.createStore();s.replace(ids);
 assert.throws(()=>s.replace(['000000000000']));assert.deepEqual(s.snapshot(),ids);s.remove(ids[1]);s.add(ids[1]);assert.deepEqual(s.snapshot(),[ids[0],ids[2],ids[1]]);
 s.clear();assert.equal(s.size(),0);
});
test('large transport does not remove selected cards',()=>{
 const ids=catalog(5000),a=B.bind({edition_id:'2026-sp-federais'},ids,S),s=a.createStore();s.replace(ids);assert.throws(()=>a.collectionUrl('https://example.test/',s.snapshot(),ids,ids[0]),RangeError);assert.deepEqual(s.snapshot(),ids);
});
test('invalid link does not create a record or external destination',()=>{
 const a=B.bind({edition_id:'2026-sp-federais'},catalog(3),S);assert.throws(()=>a.candidateUrl('https://example.test/','000000000000'));assert.throws(()=>a.candidateUrl('javascript:alert(1)',catalog(3)[0]));
 const hash='#eef=collection&v=2&edition=2026-sp-federais&ids=250000000000&redirect=https://evil.test';assert.equal(a.parseFragment(hash).kind,'invalid');
});
test('sharing is descriptive, scoped, no recipient and percent-encoded once',()=>{
 const a=B.bind({edition_id:'2026-sp-federais',label:'SP · Deputados federais',election_year:2026},catalog(1),S),data=a.shareData('https://example.test/#candidato-250000000000','Pessoa A');
 assert.ok(data.text.includes('SP · Deputados federais · 2026'));const wa=new URL(a.whatsappUrl(data));assert.equal(wa.host,'wa.me');assert.equal(wa.pathname,'/');assert.equal(wa.searchParams.get('text'),data.text+'\n'+data.url);
});
test('cancel native share never calls clipboard',async()=>{
 let copied=0;const a=B.bind({edition_id:'2026-sp-federais'},catalog(1),S),r=await a.nativeShare({url:'https://example.test/'},{share:async()=>{const e=new Error();e.name='AbortError';throw e;},clipboard:{writeText:async()=>copied++}});
 assert.equal(r.status,'cancelled');assert.equal(copied,0);
});
test('failed clipboard does not report success',async()=>{
 const a=B.bind({edition_id:'2026-sp-federais'},catalog(1),S),r=await a.copyLink('https://example.test/',{clipboard:{writeText:async()=>{throw Error('denied');}}});assert.notEqual(r.status,'copied');
});

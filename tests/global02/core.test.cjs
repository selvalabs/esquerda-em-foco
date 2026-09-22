'use strict';
const test=require('node:test'), assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'../..'), C=require('../../assets/global/core.js');
const registry=JSON.parse(fs.readFileSync(path.join(root,'config/editions.json')));
const fixtures=JSON.parse(fs.readFileSync(path.join(root,'config/legacy-sc-links.json')));
const ids=n=>Array.from({length:n},(_,i)=>String(250000000000+i));
const BASE='https://example.test/esquerda-em-foco/';
for(const size of [48,97,149,249,513,3000])test('collection complete round-trip '+size,()=>{
 const catalog=ids(size),store=C.createCollection('2026-sp-federais',catalog);
 catalog.forEach(x=>store.add(x));store.open(catalog[Math.floor(size/2)]);
 const before=store.snapshot(),link=C.collectionLink(BASE,before,catalog),out=C.parseCollection(new URL(link).hash,'2026-sp-federais',catalog);
 assert.equal(out.kind,'collection');assert.deepEqual(out.ids,catalog);assert.equal(out.active,before.active);assert.deepEqual(store.snapshot(),before);
});
test('no artificial selection limit; explicit transport limit',()=>{
 const catalog=ids(5000),s=C.createCollection('2026-sp-federais',catalog);s.replace(catalog);
 assert.throws(()=>C.collectionLink(BASE,s.snapshot(),catalog),RangeError);assert.equal(s.snapshot().ids.length,5000);
});
test('insertion, reinsertion, removal and active neighbour',()=>{
 const a=ids(3),s=C.createCollection('2026-sp-federais',a);s.add(a[0]);s.add(a[1]);s.add(a[2]);s.add(a[0]);
 assert.deepEqual(s.snapshot().ids,a);s.open(a[1]);s.remove(a[1]);assert.equal(s.snapshot().active,a[2]);s.add(a[1]);assert.deepEqual(s.snapshot().ids,[a[0],a[2],a[1]]);
 s.next();assert.equal(s.snapshot().active,a[1]);s.next();assert.equal(s.snapshot().active,a[1]);s.next(-1);assert.equal(s.snapshot().active,a[2]);s.clear();assert.equal(s.snapshot().active,null);
});
test('atomic invalid replacement',()=>{
 const a=ids(2),s=C.createCollection('2026-sp-federais',a);s.add(a[0]);assert.throws(()=>s.replace([a[1],'000000000000']));assert.deepEqual(s.snapshot().ids,[a[0]]);
});
test('edition and year isolation',()=>{
 const a=ids(2),s=C.createCollection('2026-sp-federais',a);s.add(a[0]);const h=new URL(C.collectionLink(BASE,s.snapshot(),a)).hash;
 for(const e of ['2026-pr-federais','2026-sp-estaduais','2030-sp-federais'])assert.equal(C.parseCollection(h,e,a).kind,'invalid');
});
test('snapshot not shared by reference',()=>{const s=C.createCollection('2026-sp-federais',ids(2));const a=s.snapshot();a.ids.push('oops');assert.equal(s.snapshot().ids.length,0);});
test('duplicate catalog and wrong ID formats rejected',()=>{assert.throws(()=>C.createCollection('2026-sp-federais',[...ids(1),...ids(1)]));assert.throws(()=>C.createCollection('sp-federais',ids(1)));});
for(const bad of ['#eef=collection&v=2&v=2','#eef=collection&v=2&edition=2026-sp-federais&ids=%FF','#eef=collection&v=2&edition=2026-sp-federais&ids=%G0','#eef=collection&v=9&edition=2026-sp-federais&ids=250000000000'])test('invalid collection '+bad.slice(-25),()=>assert.equal(C.parseCollection(bad,'2026-sp-federais',ids(2)).kind,'invalid'));
test('unknown fields and silent truncation rejected',()=>{
 const h='#eef=collection&v=2&edition=2026-sp-federais&ids=250000000000,999999999999';assert.equal(C.parseCollection(h,'2026-sp-federais',ids(2)).kind,'invalid');
 assert.equal(C.parseCollection(h.replace(',999999999999','')+'&next=https://evil.test','2026-sp-federais',ids(2)).kind,'invalid');
});
test('legacy v1 preserves all 48 IDs, order and active',()=>{
 const a=fixtures.candidate_ids;const h='#selecionados='+a.join(',')+'&v=1&edicao=sc-federais&ficha='+a.at(-1);
 const p=C.parseCollection(h,'2026-sc-federais',a);assert.equal(p.kind,'collection');assert.deepEqual(p.ids,a);assert.equal(p.active,a.at(-1));assert.equal(C.legacyRootTarget(h,fixtures,BASE),BASE+'sc/deputados-federais/'+h);
});
for(const base of ['https://example.test/','https://example.test/esquerda-em-foco/'])test('routes and root fragment bridge '+base,()=>{
 for(const anchor of fixtures.anchors)assert.equal(C.legacyRootTarget('#'+encodeURIComponent(anchor),fixtures,base),base+'sc/deputados-federais/#'+encodeURIComponent(anchor));
 for(const bad of ['', '#','#global-estados','#candidato-000000000000','#%FF','#https://evil.test/'])assert.equal(C.legacyRootTarget(bad,fixtures,base),null);
 for(const e of registry.editions){const r=C.resolveRoute(registry,base,C.routeURL(base,e.canonical_path),'next');assert.equal(r.edition_id,e.edition_id);assert.equal(r.available,e.publication_status==='published');}
 assert.equal(C.resolveRoute(registry,base,base,'next').kind,'home');assert.equal(C.resolveRoute(registry,base,base,'current').edition_id,'2026-sc-federais');
 assert.equal(C.resolveRoute(registry,base,'https://evil.test/'),null);
});
for(const bad of ['https://example.test/x','https://user:pwd@example.test/','https://example.test/?x=1','javascript:alert(1)','https://example.test/#x'])test('unsafe base '+bad,()=>assert.throws(()=>C.siteBase(bad)));
const valid={edition_id:'2026-pr-federais',parties:['PT','PSOL','PCdoB'],topics:['saude','ciencia-tecnologia'],statuses:['apta','inapta'],regions:['Curitiba'],semantic:'legacy_context',aliases:{}};
test('PR singular party and AND are preserved',()=>{
 const r=C.importLegacyQuery('?partido=PT&pautas=saude,ciencia-tecnologia&situacao=apta&mandato=true&historico=false&regiao=Curitiba',valid,'PR');
 assert.deepEqual(r.state.parties,['PT']);assert.equal(r.state.mode,'all');assert.equal(r.state.mandate,'true');assert.equal(r.state.history,'false');assert.equal(r.state.region,'Curitiba');assert.deepEqual(r.ignored,[]);
});
test('SP multi-party, aliases, OR, order',()=>{
 const v={...valid,edition_id:'2026-sp-federais',semantic:'documented_topic',aliases:{ciencia:'ciencia-tecnologia'}};
 const r=C.importLegacyQuery('?partidos=psol,PCDOB&pautas=ciencia&ordem=alfabetica',v,'SP');
 assert.deepEqual(r.state.parties,['PCdoB','PSOL']);assert.equal(r.state.mode,'any');assert.equal(r.state.order,'alphabetical');assert.deepEqual(r.state.topics,['ciencia-tecnologia']);
 assert.equal(C.importLegacyQuery('?modo=todos',v,'SP').state.mode,'all');
});
test('invalid legacy filters are reported, not invented',()=>{
 const r=C.importLegacyQuery('?partido=INVALID&pautas=oops&next=http://evil&situacao=oops',valid,'PR');assert.equal(r.ignored.length,4);assert.deepEqual(r.state.parties,[]);assert.deepEqual(r.state.topics,[]);
});
test('explicit query round-trip only; no storage',()=>{
 const s=C.createQuerySession(valid);s.update({q:'Água e educação',parties:['PT'],topics:['saude'],mode:'all'});
 const link=C.queryLink(BASE,s.snapshot(),valid);assert.equal(new URL(link).search,'');assert.deepEqual(C.parseQuery(new URL(link).hash,valid).state,s.snapshot());
 assert.equal(s.restore('#candidato-250000000000').kind,'other');assert.equal(s.snapshot().q,'Água e educação');
});
test('query edition/semantic mismatch rejected',()=>{
 const s=C.createQuerySession(valid);s.update({topics:['saude']});const h=new URL(C.queryLink(BASE,s.snapshot(),valid)).hash;
 assert.equal(C.parseQuery(h,{...valid,edition_id:'2026-pr-estaduais'}).kind,'invalid');assert.equal(C.parseQuery(h,{...valid,semantic:'current_support'}).kind,'invalid');
});
test('query import has no silent truncation',()=>{
 assert.throws(()=>C.importLegacyQuery('?q='+'x'.repeat(2049),valid,'PR'));assert.throws(()=>C.queryLink(BASE,{...C.emptyQuery(valid.edition_id),topics:['not-real']},valid));
});
test('unknown query fields rejected',()=>{
 const p=new URLSearchParams({eef:'query',v:'1',edition:valid.edition_id,state:JSON.stringify({...C.emptyQuery(valid.edition_id),redirect:'https://evil.test'})});assert.equal(C.parseQuery('#'+p,valid).kind,'invalid');
});
test('filtering preserves semantic separation and does not reorder',()=>{
 const query={...C.emptyQuery(valid.edition_id),q:'agua',parties:['PT'],topics:['saude'],semantic:'current_support'};
 const record={edition_id:valid.edition_id,search:'Água',party:'PT',topics:['saude'],semantic:'documented_topic'};
 assert.equal(C.matches(record,query),false);assert.equal(C.matches({...record,semantic:'current_support'},query),true);
 assert.equal(C.matches({...record,edition_id:'2026-pr-estaduais',semantic:'current_support'},query),false);
});
test('popstate restores shared query; hash-only navigation preserves memory',()=>{
 const listeners={},host={location:{hash:'',search:''},addEventListener:(k,f)=>listeners[k]=f,removeEventListener:k=>delete listeners[k]};
 const session=C.createQuerySession(valid),dispose=C.bindQueryNavigation(session,valid,host,'PR');session.update({q:'manual'});
 host.location.hash='#candidato-250000000000';listeners.hashchange();assert.equal(session.snapshot().q,'manual');
 const next={...session.snapshot(),q:'shared'};host.location.hash=new URL(C.queryLink(BASE,next,valid)).hash;listeners.popstate();assert.equal(session.snapshot().q,'shared');
 dispose();assert.equal(Object.keys(listeners).length,0);
});

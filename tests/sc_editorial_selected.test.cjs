const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const core = require('../tools/sc_editorial_selected/selection-core.cjs');
const data = JSON.parse(fs.readFileSync('data/sc-editorial-selected-r1/editorial.json','utf8'));
const ids = data.candidates.map(c=>c.candidate_id);
const base='https://selvalabs.github.io/esquerda-em-foco/?utm_source=test#topo';

test('Coleção vazia e snapshots sem referência mutável',()=>{
  const s=core.createStore(ids);assert.equal(s.size(),0);s.add(ids[0]);
  const view=s.snapshot();view.push(ids[1]);assert.deepEqual(s.snapshot(),[ids[0]]);
});
test('Todas as 48 fichas podem ser selecionadas, sem limite de 3 ou 4',()=>{
  const s=core.createStore(ids);for(const id of ids)s.add(id);
  assert.equal(s.size(),48);s.add(ids[0]);assert.equal(s.size(),48);
  assert.throws(()=>s.add('999999999999'));assert.equal(s.size(),48);
});
test('Ordem de seleção estável, remoção e reinserção no final',()=>{
  const s=core.createStore(ids);s.add(ids[2]);s.add(ids[0]);s.add(ids[1]);s.remove(ids[0]);s.add(ids[0]);
  assert.deepEqual(s.snapshot(),[ids[2],ids[1],ids[0]]);s.toggle(ids[1]);assert.deepEqual(s.snapshot(),[ids[2],ids[0]]);s.clear();assert.equal(s.size(),0);
});
test('Round-trip do conjunto completo conserva edição, ordem e ficha ativa',()=>{
  const reverse=[...ids].reverse();const url=core.collectionUrl(base,reverse,ids,ids[20]);
  const u=new URL(url);assert.equal(u.search,'');assert.equal(u.pathname,'/esquerda-em-foco/');
  const result=core.parseFragment(u.hash,ids);assert.equal(result.kind,'collection');assert.deepEqual(result.ids,reverse);assert.equal(result.active,ids[20]);
  assert.ok(u.hash.length<core.MAX_FRAGMENT_LENGTH);
});
test('IDs repetidos e desconhecidos são tratados sem gerar fichas',()=>{
  const hash=`#selecionados=${ids[0]},${ids[0]},999999999999,${ids[1]}&v=1&edicao=sc-federais&ficha=999999999999`;
  const parsed=core.parseFragment(hash,ids);assert.deepEqual(parsed.ids,[ids[0],ids[1]]);assert.equal(parsed.ignored,1);assert.equal(parsed.active,ids[0]);
});
test('Versão, edição, codificação e parâmetros inválidos não entram no estado',()=>{
  for(const hash of [
    `#selecionados=${ids[0]}&v=9&edicao=sc-federais`,
    `#selecionados=${ids[0]}&v=1&edicao=rs-federais`,
    `#selecionados=${ids[0]}&v=1&v=1&edicao=sc-federais`,
    '#selecionados=%ZZ&v=1&edicao=sc-federais',
    '#selecionados=%3Cscript%3E&v=1&edicao=sc-federais',
    '#selecionados='+('a'.repeat(5000)),
    '#selecionados=999999999999&v=1&edicao=sc-federais'
  ])assert.equal(core.parseFragment(hash,ids).kind,'invalid');
});
test('Âncoras individuais antigas e demais âncoras continuam distinguíveis',()=>{
  assert.deepEqual(core.parseFragment('#candidato-'+ids[0],ids),{kind:'candidate',id:ids[0]});
  assert.equal(core.parseFragment('#topo',ids).kind,'other');assert.equal(core.parseFragment('#pauta-fonte-'+ids[0]+'-s1',ids).kind,'other');
  assert.equal(core.parseFragment('#candidato-999999999999',ids).kind,'invalid');
});
test('Links mantêm subdiretório do Pages ou raiz da VPS sem parâmetros de rastreio',()=>{
  assert.equal(core.candidateUrl(base,ids[0],ids),'https://selvalabs.github.io/esquerda-em-foco/#candidato-'+ids[0]);
  assert.equal(core.candidateUrl('https://example.org/?x=1',ids[0],ids),'https://example.org/#candidato-'+ids[0]);
  for(const value of ['javascript:alert(1)','data:text/html,x','https://user:password@example.org/'])assert.throws(()=>core.candidateUrl(value,ids[0],ids));
  assert.throws(()=>core.collectionUrl(base,[],ids));
});
test('WhatsApp recebe texto e link codificados uma vez, sem destinatário imposto',()=>{
  const url=core.collectionUrl(base,[ids[0],ids[1]],ids,ids[1]);
  const payload=core.shareData(url);const wa=new URL(core.whatsappUrl(payload));
  assert.equal(wa.origin,'https://wa.me');assert.equal(wa.searchParams.get('text'),payload.text+'\n'+url);assert.equal(wa.searchParams.has('phone'),false);
  assert.equal(core.shareData(core.candidateUrl(base,ids[0],ids),'Jú & João').text,'Ficha de Jú & João no Esquerda em Foco — informações e fontes para consulta.');
});
test('Cancelar compartilhamento não copia nem tenta enviar por outro canal',async()=>{
  let copied=0,called=0;
  const adapter={share:async()=>{called++;throw Object.assign(new Error('Cancelado'),{name:'AbortError'});},clipboard:{writeText:async()=>copied++}};
  assert.equal((await core.nativeShare(core.shareData(base),adapter)).status,'cancelled');assert.equal(called,1);assert.equal(copied,0);
});
test('Compartilhamento nativo distingue indisponibilidade e entrega ao sistema',async()=>{
  assert.equal((await core.nativeShare(core.shareData(base),{})).status,'unavailable');
  assert.equal((await core.nativeShare(core.shareData(base),{canShare:()=>false,share:async()=>{throw Error('não deveria executar');}})).status,'unavailable');
  assert.equal((await core.nativeShare(core.shareData(base),{share:async()=>{}})).status,'handed-off');
});
test('Cópia só informa sucesso após confirmação e oferece fallback manual',async()=>{
  let value='';assert.equal((await core.copyLink('https://example.org/',{clipboard:{writeText:async v=>{value=v;}}})).status,'copied');assert.equal(value,'https://example.org/');
  assert.equal((await core.copyLink('https://example.org/',{})).status,'manual');
  assert.equal((await core.copyLink('https://example.org/',{clipboard:{writeText:async()=>{throw Error('negado');}}})).status,'manual');
});

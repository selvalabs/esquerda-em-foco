/* Bind the GLOBAL-02 collection contract to one edition. No storage or network. */
(function(root,factory){
  const api=factory(typeof module==='object'&&module.exports?require('./core.js'):root.EEFGlobal);
  if(typeof module==='object'&&module.exports)module.exports=api;else root.EEFEditionSelection=api;
})(typeof globalThis==='undefined'?this:globalThis,function(C){
  'use strict';
  function bind(edition,catalog,sharing){
    C.catalogContext(edition.edition_id,catalog);
    const known=new Set(catalog);
    function createStore(){
      const state=C.createCollection(edition.edition_id,catalog);
      return Object.freeze({snapshot:()=>state.snapshot().ids,has:id=>state.snapshot().ids.includes(id),size:()=>state.snapshot().ids.length,
        add:id=>state.add(id).ids,remove:id=>state.remove(id).ids,
        toggle(id){return state.snapshot().ids.includes(id)?state.remove(id).ids:state.add(id).ids;},
        replace(ids){return {ids:state.replace(ids).ids,ignored:0};},clear:()=>state.clear()});
    }
    function parseFragment(hash){
      const result=C.parseCollection(hash,edition.edition_id,catalog);
      if(result.kind!=='other')return result;
      if(typeof hash!=='string')return {kind:'invalid',reason:'Formato inválido'};
      const m=/^#candidato-(\d{12})$/.exec(hash);
      return m?(known.has(m[1])?{kind:'candidate',id:m[1]}:{kind:'invalid',reason:'Ficha não encontrada nesta edição'}):result;
    }
    function candidateUrl(base,id){if(!known.has(id))throw new TypeError('Ficha desconhecida');const u=C.siteBase(base);u.hash='candidato-'+id;return u.href;}
    function shareData(url,name){const data=sharing.shareData(url,name);return {...data,text:data.text+' '+edition.label+' · '+edition.election_year+'.'};}
    return Object.freeze({createStore,parseFragment,candidateUrl,shareData,
      collectionUrl(base,ids,_catalog,active){return C.collectionLink(base,{edition_id:edition.edition_id,ids,active},catalog);},
      whatsappUrl:sharing.whatsappUrl,nativeShare:sharing.nativeShare,copyLink:sharing.copyLink});
  }
  return Object.freeze({bind});
});

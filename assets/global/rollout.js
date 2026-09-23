/* One visibility controller for all published editions. Explicit shared links;
   preferences remain in document memory, including opaque history checkpoints. */
(function(){
 'use strict';
 const C=window.EEFCanonicalQuery,$=id=>document.getElementById(id),node=$('cqData');
 if(!C||!node||window.EEFQueryUI)return;
 let cfg;try{cfg=JSON.parse(node.textContent);C.validateConfig(cfg);}catch(e){console.error('Consulta global indisponível',e);return;}
 const cards=new Map([...document.querySelectorAll('article.candidate')].map(c=>[c.id.replace('candidato-',''),c]));
 if(cards.size!==cfg.records.length||cfg.records.some(r=>!cards.has(r.id)))return;
 const input=$('searchInput'),tools=$('eefQueryTools'),panel=$('cqPanel'),dialog=$('eefQueryShareDialog');
 const groups=[...document.querySelectorAll('.party-section,.party-group')];
 const collator=new Intl.Collator('pt-BR',{sensitivity:'base',numeric:true}), fields=['registration','aptitude','mandate','history','region','order'];
 const keyPrefix=crypto.randomUUID?.()||String(Math.random()),memory=new Map();let seq=0,typing=false,displaced=null,share=null,shareToken=0,opener=null,lastOrder=null;
 let state=C.empty(cfg),checkpoint=C.copy(state);const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b),url=()=>location.pathname+location.search+location.hash;
 const recordById=new Map(cfg.records.map(r=>[r.id,r]));
 const topicName=id=>cfg.topics.find(t=>t.id===id)?.label||id;
 const selectorName=s=>s.kind==='legacy'?(cfg.legacy_contract.topic_labels[s.id]||s.id)+' (link anterior)':s.kind==='group'?cfg.groups.find(g=>g.id===s.id).label:topicName(s.id);
 const scopeText={documented_topic:'Declarações e atuação com fontes ligadas ao conteúdo. Citar um assunto não significa apoiar todas as medidas sobre ele.',current_support:'Somente apoios e prioridades atuais com contexto individual revisado. Atuação e oposição não são transformadas em apoio.',legacy_context:'Vínculos temáticos da pesquisa anterior. O texto e a fonte são preservados, sem presumir atualidade ou apoio e sem atribuir cada frase a uma fonte.'};
 function notice(text=''){$('eefQueryNotice').textContent=text;$('eefQueryNotice').hidden=!text;}
 function save(push=false,target=url()){
  const key=keyPrefix+':'+(++seq);memory.set(key,{state:C.copy(state),displaced:C.copy(displaced),url:target});
  try{history[push?'pushState':'replaceState']({eefQueryEntry:key},'',target);}catch{}
  checkpoint=C.copy(state);
 }
 function oldLabel(f,v){const k={registration:'status',mandate:'mandate',history:'history',region:'region'}[f];return (cfg.legacy_contract.control_labels[k]?.[v]||v)+' (critério do link anterior)';}
 function valueLabel(f,v){return v.startsWith('legacy:')?oldLabel(f,v.slice(7)):cfg.dimensions.find(d=>d.id===f)?.options.find(o=>o.value===v)?.label||v;}
 function activeChip(text,action){const b=document.createElement('button');b.type='button';b.className='cq-chip cq-remove';b.textContent=text+' ×';b.setAttribute('aria-label','Retirar filtro: '+text);b.addEventListener('click',action);return b;}
 function sync(){
  input.value=state.q;$('cqScope').value=state.scope;
  tools.querySelectorAll('[name="cq-mode"]').forEach(r=>r.checked=r.value===state.mode);
  tools.querySelectorAll('[data-cq-party]').forEach(b=>b.setAttribute('aria-pressed',String(state.parties.includes(b.dataset.cqParty))));
  for(const f of fields){const el=$('cq-'+f);if(!el)continue;
   el.querySelectorAll('[data-cq-compat]').forEach(n=>n.remove());
   if(state[f]?.startsWith('legacy:')){const o=document.createElement('option');o.value=state[f];o.textContent=oldLabel(f,state[f].slice(7));o.dataset.cqCompat='';el.append(o);}
   el.value=state[f];
  }
  const own=cfg.records.map(r=>new Set(r.evidence.filter(e=>e.scopes.includes(state.scope)).map(e=>e.topic)));
  tools.querySelectorAll('[data-cq-topic]').forEach(b=>{
   const id=b.dataset.cqTopic,n=own.filter(s=>s.has(id)).length;
   b.querySelector('small').textContent=String(n);b.setAttribute('aria-pressed',String(state.selectors.some(s=>s.kind==='topic'&&s.id===id)));
   b.title=n?'Correspondências neste tipo de evidência':'Nenhum vínculo elegível foi consolidado neste recorte. Isso não indica oposição.';
  });
  tools.querySelectorAll('[data-cq-group]').forEach(b=>{
   const g=cfg.groups.find(g=>g.id===b.dataset.cqGroup),n=own.filter(s=>g.members.some(t=>s.has(t))).length;
   tools.querySelector('[data-cq-group-count="'+g.id+'"]').textContent=String(n);
   b.setAttribute('aria-pressed',String(state.selectors.some(s=>s.kind==='group'&&s.id===g.id)));
  });
  const laneCount=cfg.records.filter(r=>r.evidence.some(e=>e.scopes.includes(state.scope))).length;
  const contextCount=cfg.records.filter(r=>r.evidence.some(e=>e.scopes.includes('legacy_context'))).length;
  $('cqScopeHint').textContent=scopeText[state.scope]+(!laneCount?' Ainda não há vínculos elegíveis consolidados neste recorte da edição.':'');
  $('cqContextShortcut').hidden=!!laneCount||!contextCount||state.scope==='legacy_context';
  const active=$('cqActive');active.replaceChildren();
  if(state.q)active.append(activeChip('Busca: '+state.q,()=>change({...state,q:''})));
  state.parties.forEach(p=>active.append(activeChip(p,()=>change({...state,parties:state.parties.filter(x=>x!==p)}))));
  state.selectors.forEach(s=>active.append(activeChip(selectorName(s),()=>change({...state,selectors:state.selectors.filter(x=>!(x.id===s.id&&x.kind===s.kind))}))));
  fields.filter(f=>f!=='order'&&state[f]).forEach(f=>active.append(activeChip(valueLabel(f,state[f]),()=>change({...state,[f]:''}))));
  const count=state.parties.length+state.selectors.length+fields.filter(f=>f!=='order'&&state[f]).length+Number(!!state.q);
  $('cqPanelCount').textContent=count?count+' critério'+(count===1?'':'s')+' ativo'+(count===1?'':'s'):'Busca, partidos e evidências';
  $('eefQuerySummary').textContent=count?'A consulta combina os filtros ativos. Temas: '+(state.mode==='all'?'todos os selecionados':'qualquer um dos selecionados')+'.':'Todas as fichas estão disponíveis. Abra os filtros para explorar.';
  $('eefShareQuery').disabled=!C.hasCriteria(state);$('eefQueryClear').disabled=!C.hasCriteria(state);
 }
 function order(){
  if(document.querySelector('[data-eef-held]'))return;
  const now=new Date(),parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'America/Sao_Paulo',year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(now).map(x=>[x.type,x.value]));
  const day=parts.year+'-'+parts.month+'-'+parts.day,key=state.order+day;if(key===lastOrder)return;lastOrder=key;
  const offset=Math.max(0,Math.floor((Date.parse(day+'T00:00:00Z')-Date.parse(cfg.epochs.daily+'T00:00:00Z'))/86400000));
  const rotate=a=>{if(state.order==='alphabetical'||!a.length)return a;const n=offset%a.length;return a.slice(n).concat(a.slice(0,n));};
  rotate(groups.slice().sort((a,b)=>collator.compare(a.dataset.partySection||a.dataset.party,b.dataset.partySection||b.dataset.party))).forEach(g=>{
   g.parentNode.append(g);const list=[...g.querySelectorAll('article.candidate')].sort((a,b)=>collator.compare(recordById.get(a.id.replace('candidato-','')).name,recordById.get(b.id.replace('candidato-','')).name)||collator.compare(a.id,b.id));
   rotate(list).forEach(c=>c.parentNode.append(c));
  });
  const nav=document.querySelector('.party-nav');if(nav)rotate([...nav.querySelectorAll('[data-nav-party]')].sort((a,b)=>collator.compare(a.dataset.navParty,b.dataset.navParty))).forEach(a=>nav.append(a));
  document.documentElement.dataset.rotationDate=day;
 }
 function relevant(record){
  const direct=C.evidenceMatches(record,state,cfg);if(!state.selectors.some(s=>s.kind==='legacy'))return direct;
  const legacy=state.selectors.filter(s=>s.kind==='legacy');
  return record.evidence.filter(e=>direct.includes(e)||e.scopes.includes(state.scope)&&legacy.some(s=>(cfg.legacy_contract.topic_members?.[s.id]||[s.id]).includes(e.native_topic)));
 }
 function notes(record,card){
  card.querySelectorAll('.cq-match,.cq-inline-note').forEach(n=>n.remove());
  if(!state.selectors.length||card.hidden)return;
  const matches=relevant(record),box=document.createElement('aside');box.className='cq-match';
  const p=document.createElement('p');p.textContent='Por que aparece nesta consulta?';box.append(p);
  const object=document.createElement('p');object.textContent=matches.length?[...new Set(matches.map(e=>e.native_label))].join(' · '):'Critério preservado do link anterior. Consulte o texto e as fontes originais.';box.append(object);
  if(matches.length){
   const details=document.createElement('details'),summary=document.createElement('summary');summary.textContent='Ver os registros que sustentam a correspondência';details.append(summary);
   const seen=new Set();matches.forEach(ev=>{
    if(seen.has(ev.object))return;seen.add(ev.object);
    const text=document.createElement('p');text.textContent=ev.object;details.append(text);
    if(ev.granularity==='whole_synthesis'){const limit=document.createElement('p');limit.className='cq-help';limit.textContent='Vínculo da síntese de pesquisa; não é uma atribuição de cada frase ao documento.';details.append(limit);}
    const urls=new Set();ev.sources.forEach(source=>{if(urls.has(source.url))return;urls.add(source.url);const a=document.createElement('a');a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Consultar a fonte deste vínculo';details.append(a);const loc=document.createElement('p');loc.className='cq-help';loc.textContent=(source.locator_kind==='research_record_not_external_passage'?'Registro na pesquisa (não é trecho literal da fonte): ':'Localizador da evidência: ')+source.locator;details.append(loc);});
   });box.append(details);
  }
  if(matches.length){const b=document.createElement('button');b.type='button';b.dataset.cqReason=record.id;b.textContent='Ver as evidências desta correspondência';box.append(b);}
  card.querySelector('.cc-reading-title')?.insertAdjacentElement('afterend',box);
  if(cfg.edition_id==='2026-sc-federais'){
   const paragraphs=new Map();matches.forEach(e=>{
    const p=[...card.querySelectorAll('[data-eef-associations]')].find(p=>p.dataset.eefAssociations.split(' ').includes(e.native_id));
    if(p){if(!paragraphs.has(p))paragraphs.set(p,new Set());paragraphs.get(p).add(topicName(e.topic));}
   });
   paragraphs.forEach((topics,p)=>{const n=document.createElement('p');n.className='cq-inline-note eef-filter-note';n.textContent='Correspondência documentada: '+[...topics].join(' · ')+'.';p.insertAdjacentElement('afterend',n);});
  }
 }
 function render(){
  let visible=0;
  cfg.records.forEach(r=>{const card=cards.get(r.id),show=C.matches(r,state,cfg);if(!card.dataset.eefHeld)card.hidden=!show;if(show)visible++;notes(r,card);});
  groups.forEach(g=>{
   const actual=[...cards.values()].filter(c=>!c.dataset.eefHeld&&g.contains(c));g.hidden=!actual.some(c=>!c.hidden);
   const n=g.querySelector('.party-count');if(n)n.textContent=String(actual.filter(c=>!c.hidden).length);
  });
  $('resultCount').textContent=visible+' de '+cards.size+' registros';$('resultCount').setAttribute('role','status');$('resultCount').setAttribute('aria-live','polite');
  if($('emptyResults'))$('emptyResults').hidden=visible!==0;
  document.documentElement.dataset.visibleCount=String(visible);order();sync();
 }
 function apply(raw){const next=C.normalize(raw,cfg);if(!same(next,state))window.EEFCollectionUI?.close();state=next;render();return C.copy(state);}
 function change(raw,isTyping=false){
  try{apply(raw);displaced=null;if($('eefDeepLinkNotice'))$('eefDeepLinkNotice').hidden=true;notice();if(!same(state,checkpoint))save(!(isTyping&&typing),location.pathname);typing=isTyping;}
  catch(e){notice(e.message+'. Sua consulta foi preservada.');}
 }
 function toggle(kind,id){const yes=state.selectors.some(s=>s.kind===kind&&s.id===id);change({...state,selectors:yes?state.selectors.filter(s=>!(s.kind===kind&&s.id===id)):state.selectors.concat({kind,id})});}
 tools.addEventListener('click',e=>{
  const b=e.target.closest('[data-cq-party],[data-cq-topic],[data-cq-group]');if(!b)return;
  if(b.hasAttribute('data-cq-party')){const p=b.dataset.cqParty;change({...state,parties:state.parties.includes(p)?state.parties.filter(x=>x!==p):state.parties.concat(p)});}
  else toggle(b.hasAttribute('data-cq-topic')?'topic':'group',b.dataset.cqTopic||b.dataset.cqGroup);
 });
 input.addEventListener('input',()=>change({...state,q:input.value},true));
 input.form?.addEventListener('submit',e=>{e.preventDefault();change({...state,q:input.value});});
 tools.addEventListener('change',e=>{const n=e.target;if(n.name==='cq-mode')change({...state,mode:n.value});else if(n.dataset.cqField)change({...state,[n.dataset.cqField]:n.value});});
 $('cqScope').addEventListener('change',()=>change({...state,scope:$('cqScope').value,selectors:state.selectors.filter(s=>s.kind!=='legacy')}));
 $('cqContextShortcut').addEventListener('click',()=>change({...state,scope:'legacy_context',selectors:state.selectors.filter(s=>s.kind!=='legacy')}));
 $('eefQueryClear').addEventListener('click',()=>change(C.empty(cfg)));
 panel.addEventListener('keydown',e=>{if(e.key==='Escape'&&panel.open){e.preventDefault();panel.open=false;panel.querySelector('summary').focus({preventScroll:true});}});
 function showDisplaced(){if(!$('eefDeepLinkNotice'))return;$('eefDeepLinkNotice').hidden=!displaced;$('eefDeepLinkMessage').textContent='Os filtros foram suspensos para abrir a ficha ou fonte do link. Você pode restaurar sua consulta anterior.';}
 function reveal(hash,scroll=true){
  let target;try{target=$(decodeURIComponent(hash.replace(/^#/,'')));}catch{return;}
  if(!target)return;if(target.classList.contains('cq-anchor')){panel.open=true;target=panel;}
  const card=target.closest('article.candidate'),group=target.closest('.party-section,.party-group');
  if(card?.dataset.eefHeld)return;
  if(card?.hidden||group?.hidden){displaced=C.copy(state);apply(C.empty(cfg));showDisplaced();save();}
  let n=target;while(n){if(n.tagName==='DETAILS')n.open=true;n=n.parentElement;}
  if(scroll)requestAnimationFrame(()=>{if(!target.matches('a,button,input,select,textarea,summary,[tabindex]'))target.setAttribute('tabindex','-1');target.focus({preventScroll:true});target.scrollIntoView({block:'start',behavior:'instant'});});
 }
 $('eefRestoreQuery')?.addEventListener('click',()=>{if(!displaced)return;const old=C.copy(displaced);apply(old);displaced=null;showDisplaced();save(true,location.pathname);input.focus({preventScroll:true});input.scrollIntoView({block:'center'});});
 function route(){
  typing=false;const entry=memory.get(history.state?.eefQueryEntry);
  if(entry?.url===url()){apply(entry.state);displaced=C.copy(entry.displaced);showDisplaced();reveal(location.hash);return;}
  let parsed=C.parse(location.hash,cfg);
  if(parsed.kind==='other'&&location.search)parsed=C.importSearch(location.search,cfg);
  if(parsed.kind==='query'){
   apply(parsed.state);displaced=null;showDisplaced();notice(parsed.legacy?'Consulta anterior preservada. Os critérios marcados “link anterior” mantêm o significado original.':'Consulta do link aplicada nesta edição.');
  }else if(parsed.kind==='invalid'){notice(parsed.reason+'. Sua consulta atual foi preservada.');return;}
  reveal(location.hash);save();
 }
 addEventListener('hashchange',route,true);addEventListener('popstate',route,true);
 document.addEventListener('click',e=>{
  const reason=e.target.closest('[data-cq-reason]'),old=e.target.closest('[data-show-evidence]');
  if(reason||old){
   const card=reason?cards.get(reason.dataset.cqReason):old.closest('article.candidate'),proof=card?.querySelector('.cc-proof');
   if(proof){const record=recordById.get(card.id.replace('candidato-','')),ids=new Set(relevant(record).map(x=>x.native_id));proof.open=true;
    proof.querySelectorAll('[data-cc-evidence]').forEach(li=>li.hidden=!!reason&&ids.size>0&&!ids.has(li.dataset.ccEvidence));
    proof.querySelector('.cc-evidence-status').textContent=reason?'Evidências relacionadas à consulta. Use “Ver todo o contexto” para as demais.':'';
    proof.querySelector('summary').focus();proof.scrollIntoView({block:'start'});
   }return;
  }
  const a=e.target.closest('a[href^="#"]');if(!a||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey)return;
  let target;try{target=$(decodeURIComponent(a.hash.slice(1)));}catch{return;}
  if(!target)return;
  // Source navigation is coordinated with the original-card collection handler.
  e.preventDefault();if(location.hash!==a.hash)history.pushState(null,'',a.hash);reveal(a.hash);save();
 });
 function closeMenus(){document.getElementById('global-edition-menu')?.removeAttribute('open');$('siteNav')?.classList.remove('is-open');$('siteNavMenu')?.setAttribute('aria-expanded','false');}
 $('siteNavMenu')?.addEventListener('click',()=>{const b=$('siteNavMenu'),open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(open));$('siteNav').classList.toggle('is-open',open);});
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&$('siteNav')?.classList.contains('is-open')){closeMenus();$('siteNavMenu')?.focus();}});
 $('siteNav')?.addEventListener('click',e=>{if(e.target.closest('a'))closeMenus();});
 document.addEventListener('click',e=>{if($('siteNav')&&!$('siteNav').contains(e.target)){$('siteNav').classList.remove('is-open');$('siteNavMenu')?.setAttribute('aria-expanded','false');}});
 function bars(){const root=document.documentElement;root.style.setProperty('--eef-nav-height',Math.ceil($('siteNav')?.getBoundingClientRect().height||58)+'px');root.style.setProperty('--eef-footer-height',Math.ceil(document.querySelector('.persistent-footer')?.getBoundingClientRect().height||48)+'px');const progress=$('progressBar')||document.querySelector('.progress');if(progress){const range=root.scrollHeight-innerHeight;progress.style.width=(range>0?100*scrollY/range:0)+'%';}}
 addEventListener('scroll',bars,{passive:true});addEventListener('resize',bars,{passive:true});bars();
 $('eefShareQuery').addEventListener('click',e=>{try{
  const shared=C.link(new URL('./',location.href).href,state,cfg);shareToken++;share={title:'Esquerda em Foco',text:'Consulta em '+cfg.label+' — critérios escolhidos para leitura.',url:shared};opener=e.currentTarget;
  $('eefQueryShareUrl').value=shared;$('eefQueryShareStatus').textContent='';$('eefQueryWhatsapp').href='https://wa.me/?text='+encodeURIComponent(share.text+'\n'+shared);$('eefQueryNative').hidden=typeof navigator.share!=='function';$('eefQueryNative').disabled=false;closeMenus();dialog.showModal();$('eefQueryShareClose').focus();
 }catch(e){notice(e.message);}});
 $('eefQueryShareClose').addEventListener('click',()=>dialog.close());dialog.addEventListener('close',()=>{shareToken++;share=null;opener?.focus({preventScroll:true});});
 $('eefQueryCopy').addEventListener('click',async()=>{if(!share)return;const token=shareToken;try{if(!navigator.clipboard?.writeText)throw new Error();await navigator.clipboard.writeText(share.url);if(token===shareToken)$('eefQueryShareStatus').textContent='Link copiado.';}catch{if(token!==shareToken)return;$('eefQueryShareStatus').textContent='Não foi possível copiar automaticamente. Selecione o link e use Copiar.';$('eefQueryShareUrl').focus();$('eefQueryShareUrl').select();}});
 $('eefQueryNative').addEventListener('click',async()=>{if(!share)return;const token=shareToken;$('eefQueryNative').disabled=true;try{await navigator.share(share);if(token===shareToken)$('eefQueryShareStatus').textContent='Conteúdo entregue ao compartilhador. Confirme o envio no aplicativo.';}catch(e){if(token===shareToken)$('eefQueryShareStatus').textContent=e.name==='AbortError'?'Compartilhamento cancelado.':'Compartilhamento indisponível. Use Copiar link.';}finally{if(token===shareToken)$('eefQueryNative').disabled=false;}});
 window.EEFTopicFilters=Object.freeze({apply:render});
 window.EEFEditionQuery=Object.freeze({valid:cfg,snapshot:()=>C.copy(state),applyState:apply});
 window.EEFQueryUI=Object.freeze({snapshot:()=>C.copy(state),shareUrl:()=>C.link(new URL('./',location.href).href,state,cfg),applyHash:route,reveal});
 document.documentElement.classList.add('js','eef-global04-query-ready','eef-rollout-ready');tools.hidden=false;
 document.querySelectorAll('[data-global04-native-share]').forEach(n=>n.hidden=true);
 render();route();setInterval(order,60000);
})();

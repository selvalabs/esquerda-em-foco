(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('editorialData').textContent);
  const core = window.EEFSelectionCore;
  const ids = data.candidates.map(c => c.candidate_id);
  const byId = new Map(data.candidates.map(c => [c.candidate_id,c]));
  const store = core.createStore(ids);
  const el = id => document.getElementById(id);
  let mode = 'list';
  let active = null;
  let sharePayload = null;
  let shareOpener = null;
  let clearOpener = null;
  let pointer = null;
  const normalize = text => text.toLocaleLowerCase('pt-BR').normalize('NFD').replace(/[\u0300-\u036f]/g,'');
  function node(tag, text, className) {
    const n = document.createElement(tag);
    if (text !== undefined) n.textContent = text;
    if (className) n.className = className;
    return n;
  }
  function button(text, action, id) {
    const b = node('button',text);
    b.type = 'button'; b.dataset.action = action;
    if (id) b.dataset.id = id;
    return b;
  }
  function announce(text) { el('notice').textContent = text; }
  function focusCard() {
    const heading = el('activeName');
    if (!heading) return;
    heading.focus({preventScroll:true});
    heading.scrollIntoView({block:'start',behavior:'auto'});
  }
  function selectionState() {
    document.querySelectorAll('[data-selection-count]').forEach(x => x.textContent = store.size());
    document.querySelectorAll('[data-action="toggle"]').forEach(b => {
      const yes = store.has(b.dataset.id);
      b.textContent = yes ? 'Selecionado' : 'Selecionar';
      b.setAttribute('aria-pressed',String(yes));
      b.setAttribute('aria-label',(yes?'Remover de selecionados: ':'Selecionar: ')+byId.get(b.dataset.id).name);
    });
    el('selectionBar').hidden = !store.size() || mode === 'selected';
  }
  function roster() {
    const query = normalize(el('nameSearch').value.trim());
    const results = data.candidates.filter(c => !query || normalize(c.name).includes(query));
    const fragment = document.createDocumentFragment();
    for (const c of results) {
      const row = node('div',undefined,'roster-row'); row.setAttribute('role','listitem');
      const identity = node('div',undefined,'identity');
      const open = button(c.name,'read',c.candidate_id); open.className = 'name';
      identity.append(open,node('div',c.party+' · '+c.number,'roster-meta'));
      const select = button('Selecionar','toggle',c.candidate_id); select.className='select';
      row.append(identity,select); fragment.append(row);
    }
    el('roster').replaceChildren(fragment);
    el('rosterCount').textContent = results.length+' ficha'+(results.length===1?'':'s');
    el('searchEmpty').hidden = Boolean(results.length);
    selectionState();
  }
  function sourcesFor(paragraph) {
    const citations = node('div',undefined,'citations');
    for (const sid of paragraph.source_ids) {
      const source = data.sources[sid];
      const a = node('a',source.caption+' ↗');
      a.href = source.url; a.target = '_blank'; a.rel = 'noopener noreferrer';
      a.title = source.title; a.setAttribute('aria-label',source.caption+': '+source.title);
      a.dataset.sourceId = sid; citations.append(a);
    }
    return citations;
  }
  function readingSection(section) {
    const s = node('section',undefined,'reader-section'); s.dataset.section = section.id;
    s.append(node('h4',section.title));
    for (const p of section.paragraphs) {
      const box = node('div',undefined,'paragraph'); box.dataset.paragraphId=p.paragraph_id;
      box.append(node('p',p.text),sourcesFor(p)); s.append(box);
    }
    if (section.notice) s.append(node('p',section.notice,'warning'));
    return s;
  }
  function card(id) {
    const c = byId.get(id);
    const article = node('article',undefined,'reader-card'); article.dataset.candidateId=id;
    article.setAttribute('aria-labelledby','activeName');
    const title=node('h3',c.name);title.id='activeName';title.tabIndex=-1;
    article.append(node('p','Ficha para consulta','eyebrow'),title,node('p',c.party+' · '+c.number+' · Deputado federal · SC','card-meta'));
    const actions=node('div',undefined,'card-actions');
    actions.append(button('Selecionar','toggle',id),button('Compartilhar ficha','share-single',id));
    const full=node('a','Abrir ficha no site ↗');full.href=core.candidateUrl(data.site_base,id,ids);full.target='_blank';full.rel='noopener noreferrer';
    actions.append(full);article.append(actions);
    const visible=c.sections.filter(s=>s.id!=='contexto');
    for(const s of visible)article.append(readingSection(s));
    if(c.gap_text)article.append(node('p',c.gap_text));
    if(!visible.length && !c.gap_text)article.append(node('p',data.ui.context_intro));
    const context=node('details',undefined,'sources');context.id='sourceDetails';
    context.append(node('summary',data.ui.source_details));
    context.append(node('p',data.ui.model_notice,'source-meta'));
    for(const s of c.sections.filter(s=>s.id==='contexto'))context.append(readingSection(s));
    const sourceList=node('ol');
    for(const sid of c.source_ids){
      const source=data.sources[sid];const li=node('li');li.id='source-'+sid;
      const a=node('a',source.title+' ↗');a.href=source.url;a.target='_blank';a.rel='noopener noreferrer';
      li.append(a,node('p',source.publisher+' · '+source.caption,'source-meta'),node('p',source.locator,'source-meta'));
      if(!source.content_reconfirmed)li.append(node('p','A fonte não pôde ser reconferida na revisão semântica. O registro não alimenta os filtros atuais.','source-warning'));
      sourceList.append(li);
    }
    if(c.source_ids.length)context.append(sourceList);
    else context.append(node('p','Não há fonte programática individual suficiente associada à ficha neste levantamento.'));
    const notes=[...c.sections.map(s=>s.context_note).filter(Boolean),...c.retained_limitations];
    if(notes.length){
      const detail=node('details',undefined,'details-notes');detail.append(node('summary','O que foi possível confirmar'));
      for(const note of [...new Set(notes)])detail.append(node('p',note));context.append(detail);
    }
    article.append(context);
    // Gesture changes the individual reader only. Vertical page scrolling is never cancelled.
    article.addEventListener('pointerdown',e=>{
      if(mode!=='selected'||e.pointerType!=='touch'||e.target.closest('button,a,summary,input,textarea'))return;
      pointer={x:e.clientX,y:e.clientY};
    });
    article.addEventListener('pointerup',e=>{
      if(!pointer)return;const dx=e.clientX-pointer.x,dy=e.clientY-pointer.y;pointer=null;
      if(Math.abs(dx)>70&&Math.abs(dy)<40)step(dx<0?1:-1);
    });
    article.addEventListener('pointercancel',()=>{pointer=null;});
    return article;
  }
  function renderReader() {
    const chosen=store.snapshot();
    const empty=mode==='selected'&&!chosen.length;
    if(mode==='selected'&&!chosen.includes(active))active=chosen[0]||null;
    el('selectedEmpty').hidden=!empty;
    el('collectionControls').hidden=mode!=='selected'||empty;
    el('collectionActions').hidden=mode!=='selected'||empty;
    el('readingTitle').textContent=mode==='selected'?'Selecionados':'Leitura da ficha';
    el('cardHost').replaceChildren(...(!empty&&active?[card(active)]:[]));
    const index=chosen.indexOf(active);
    el('pager').textContent=empty?'':`Ficha ${index+1} de ${chosen.length}`;
    el('previous').disabled=index<=0;el('next').disabled=index<0||index>=chosen.length-1;
    selectionState();
  }
  function show(target,id) {
    mode=target;if(id)active=id;
    el('rosterView').hidden=mode!=='list';el('readingView').hidden=mode==='list';
    el('listViewBtn').setAttribute('aria-pressed',String(mode!=='selected'));
    el('selectedViewBtn').setAttribute('aria-pressed',String(mode==='selected'));
    if(mode==='list')roster();else renderReader();
    selectionState();
  }
  function step(delta) {
    if(mode!=='selected')return;
    const chosen=store.snapshot(),i=chosen.indexOf(active),next=i+delta;
    if(next<0||next>=chosen.length)return;
    active=chosen[next];renderReader();focusCard();
  }
  function toggle(id) {
    const prior=store.snapshot(),index=prior.indexOf(id),was=store.has(id);
    store.toggle(id);
    if(mode==='selected'&&was&&id===active){
      const chosen=store.snapshot();active=chosen[Math.min(index,chosen.length-1)]||null;
      renderReader();if(active)focusCard();else el('backToList').focus();
    }else selectionState();
    announce((was?'Removido de selecionados: ':'Adicionado a selecionados: ')+byId.get(id).name+'.');
  }
  function openShare(kind,id,opener) {
    shareOpener=opener;sharePayload=null;
    const collection=kind==='collection';
    el('shareTitle').textContent=collection?'Compartilhar coleção':'Compartilhar ficha';
    el('shareStatus').textContent='';
    el('shareUrl').value='';el('copyLink').disabled=false;
    el('shareWarning').hidden=!collection;
    el('shareWarning').textContent=data.ui.prototype_share;
    if(collection){
      try{sharePayload=core.shareData(core.collectionUrl(location.href,store.snapshot(),ids,active));}
      catch{el('shareStatus').textContent='Para testar links da coleção, abra a prévia por um servidor HTTP local. A leitura e a seleção funcionam também neste arquivo.';el('copyLink').disabled=true;}
    }else sharePayload=core.shareData(core.candidateUrl(data.site_base,id,ids),byId.get(id).name);
    el('shareMessage').textContent=sharePayload?sharePayload.text:'';
    el('shareUrl').value=sharePayload?sharePayload.url:'';
    // Do not distribute a local prototype collection as though production supported it.
    el('nativeShare').hidden=collection||typeof navigator.share!=='function';
    el('whatsappLink').hidden=collection;
    el('whatsappLink').removeAttribute('href');
    if(!collection&&sharePayload)el('whatsappLink').href=core.whatsappUrl(sharePayload);
    el('shareDialog').showModal();el('closeShare').focus();
  }
  document.addEventListener('click',e=>{
    const b=e.target.closest('[data-action]');if(!b)return;
    const {action,id}=b.dataset;
    if(action==='read'){show('single',id);focusCard();}
    if(action==='toggle')toggle(id);
    if(action==='share-single')openShare('single',id,b);
  });
  el('nameSearch').addEventListener('input',roster);
  el('listViewBtn').addEventListener('click',()=>show('list'));
  el('backToList').addEventListener('click',()=>{show('list');el('nameSearch').focus();});
  for(const id of ['selectedViewBtn','openCollectionBar'])el(id).addEventListener('click',()=>{show('selected');if(active)focusCard();else el('backToList').focus();});
  el('previous').addEventListener('click',()=>step(-1));el('next').addEventListener('click',()=>step(1));
  el('collectionControls').addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();step(e.key==='ArrowRight'?1:-1);}});
  el('shareCollection').addEventListener('click',e=>openShare('collection',null,e.currentTarget));
  el('closeShare').addEventListener('click',()=>el('shareDialog').close());
  el('shareDialog').addEventListener('close',()=>{if(shareOpener&&shareOpener.isConnected)shareOpener.focus();else if(el('activeName'))el('activeName').focus();});
  el('copyLink').addEventListener('click',async()=>{
    if(!sharePayload)return;
    const result=await core.copyLink(sharePayload.url,navigator);
    el('shareStatus').textContent=result.status==='copied'?'Link copiado.':'Não foi possível copiar automaticamente. Selecione o link abaixo e use Copiar.';
    if(result.status==='manual'){el('shareUrl').focus();el('shareUrl').select();}
  });
  el('nativeShare').addEventListener('click',async()=>{
    if(!sharePayload)return;
    el('nativeShare').disabled=true;
    const result=await core.nativeShare(sharePayload,navigator);
    el('nativeShare').disabled=false;
    el('shareStatus').textContent=result.status==='handed-off'?'Conteúdo entregue ao compartilhador do aparelho. Confirme o envio no aplicativo.':result.status==='cancelled'?'Compartilhamento cancelado ou sem destino disponível.':'Compartilhamento nativo indisponível. Use Copiar link ou WhatsApp.';
  });
  el('clearCollection').addEventListener('click',e=>{clearOpener=e.currentTarget;el('clearDialog').showModal();el('cancelClear').focus();});
  el('cancelClear').addEventListener('click',()=>el('clearDialog').close());
  el('confirmClear').addEventListener('click',()=>{store.clear();active=null;el('clearDialog').close();renderReader();announce('A coleção foi esvaziada. Todas as fichas continuam disponíveis na lista.');});
  el('clearDialog').addEventListener('close',()=>{if(store.size()&&clearOpener&&clearOpener.isConnected)clearOpener.focus();else el('backToList').focus();});
  function restoreHash() {
    const result=core.parseFragment(location.hash,ids);
    if(result.kind==='collection'){
      store.replace(result.ids);active=result.active;show('selected');
      announce(result.ignored?'Coleção aberta. Alguns IDs não pertencem a esta edição e foram ignorados.':'Coleção aberta a partir do link.');
    }else if(result.kind==='candidate'){show('single',result.id);}
    else if(result.kind==='invalid')announce(result.reason+'. A seleção existente foi preservada.');
  }
  window.addEventListener('hashchange',restoreHash);
  show('list');restoreHash();
  // Deliberately no storage, analytics, automatic URL update or message sending.
})();

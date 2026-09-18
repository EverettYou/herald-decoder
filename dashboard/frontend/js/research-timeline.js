(function () {
  const CARD_WIDTH = 224, CARD_HEIGHT = 118, COLUMN_GAP = 72, BRANCH_GAP = 28;
  const MIN_ZOOM = .2, MAX_ZOOM = 2, VIEWPORT_GAP = 24, VIEWPORT_MAX = 548;
  const escape = value => String(value ?? '').replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#039;','"':'&quot;'}[c]));
  const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
  const number = id => `Lab ${id.match(/^lab-(\d+)/)?.[1] || id}`;
  const dateLabel = value => {
    const date = new Date(`${value}T00:00:00Z`);
    return Number.isNaN(+date) ? 'Date not recorded' : new Intl.DateTimeFormat('en', {month:'short',day:'numeric',year:'numeric',timeZone:'UTC'}).format(date);
  };
  let dispose = () => {};

  // Columns encode ancestry, not elapsed time. A spanning tree places cards;
  // every recorded parent edge is drawn with the same cubic, even if it passes
  // under an unrelated card.
  function layout(labs, heights = new Map()) {
    const byId = new Map(labs.map(lab => [lab.id, lab]));
    if (byId.size !== labs.length) throw new Error('Duplicate Lab identifiers');
    if (!labs.length) return {ordered:[],nodes:new Map(),edges:[],width:0,height:0};
    const parents = new Map(labs.map(lab => [lab.id,[...new Set(lab.parents || [])].filter(id => byId.has(id))]));
    const children = new Map(labs.map(lab => [lab.id,[]]));
    parents.forEach((ids,id) => ids.forEach(parent => children.get(parent).push(id)));
    const compare = (a,b) => (byId.get(a).created || '').localeCompare(byId.get(b).created || '') || a.localeCompare(b);
    const pending = new Map([...parents].map(([id,ids]) => [id,ids.length]));
    const ready = [...pending].filter(([,count]) => !count).map(([id]) => id).sort(compare);
    const ordered = [], ranks = new Map();
    while (ready.length) {
      const id = ready.shift(); ordered.push(byId.get(id));
      ranks.set(id, Math.max(-1,...parents.get(id).map(parent => ranks.get(parent))) + 1);
      children.get(id).forEach(child => {pending.set(child,pending.get(child)-1);if (!pending.get(child)) ready.push(child);});
      ready.sort(compare);
    }
    if (ordered.length !== labs.length) throw new Error('Lab parent relationships contain a cycle');
    const primary = new Map(), branches = new Map(labs.map(lab => [lab.id,[]]));
    ordered.forEach(lab => {
      const parent = [...parents.get(lab.id)].sort((a,b) => ranks.get(b)-ranks.get(a) || compare(b,a))[0];
      if (parent) {primary.set(lab.id,parent);branches.get(parent).push(lab.id);}
    });
    const newest = new Map();
    [...ordered].reverse().forEach(lab => newest.set(lab.id,[lab.created || '',...branches.get(lab.id).map(id => newest.get(id))].sort().at(-1)));
    const branchOrder = (a,b) => newest.get(b).localeCompare(newest.get(a)) || compare(a,b);
    branches.forEach(ids => ids.sort(branchOrder));
    const roots = ordered.filter(lab => !primary.has(lab.id)).map(lab => lab.id).sort(branchOrder);
    const marginY = 44;
    const rowHeight = Math.max(CARD_HEIGHT,...heights.values());
    let cursor = 0;
    const centers = new Map();
    const place = id => {
      const kids = branches.get(id);
      if (!kids.length) {centers.set(id,marginY+rowHeight/2+cursor*(rowHeight+BRANCH_GAP));cursor++;}
      else {kids.forEach(place);centers.set(id,(centers.get(kids[0])+centers.get(kids.at(-1)))/2);}
    };
    roots.forEach(place);
    const nodes = new Map(ordered.map(lab => {
      const height = heights.get(lab.id) || CARD_HEIGHT;
      return [lab.id,{...lab,rank:ranks.get(lab.id),x:30+ranks.get(lab.id)*(CARD_WIDTH+COLUMN_GAP),y:centers.get(lab.id)-height/2,width:CARD_WIDTH,height}];
    }));
    const width = Math.max(...[...nodes.values()].map(n => n.x+n.width))+30;
    const height = Math.max(...[...nodes.values()].map(n => n.y+n.height))+marginY;
    const edges = ordered.flatMap(lab => parents.get(lab.id).map(source => ({source,target:lab.id,primary:primary.get(lab.id)===source})));
    edges.forEach(edge => {
      const source = nodes.get(edge.source), target = nodes.get(edge.target);
      const outgoing = edges.filter(e => e.source===edge.source).sort((a,b) => nodes.get(a.target).y-nodes.get(b.target).y || a.target.localeCompare(b.target));
      const incoming = edges.filter(e => e.target===edge.target).sort((a,b) => nodes.get(a.source).y-nodes.get(b.source).y || a.source.localeCompare(b.source));
      const sx = source.x+source.width, tx = target.x;
      const sy = source.y+source.height*(outgoing.indexOf(edge)+1)/(outgoing.length+1);
      const ty = target.y+target.height*(incoming.indexOf(edge)+1)/(incoming.length+1);
      const dx = COLUMN_GAP*.48;
      edge.path = `M ${sx} ${sy} C ${sx+dx} ${sy}, ${tx-dx} ${ty}, ${tx} ${ty}`;
    });
    return {ordered,nodes,edges,parents,children,primary,width,height};
  }

  function mount(labs) {
    dispose();
    const target = document.querySelector('#research-timeline');
    if (!target) return;
    if (!labs?.length) {target.innerHTML='<p class="evolution-empty">Research studies will appear here as they are created.</p>';return;}
    const controls = document.querySelector('#timeline-controls');
    const controller = new AbortController(), signal = controller.signal;
    const on = (node,type,fn,options={}) => node?.addEventListener(type,fn,{...options,signal});
    let model;
    try {model=layout(labs);} catch(error) {
      target.innerHTML=`<p class="evolution-empty">${escape(error.message)}. <a href="/labs">Browse all Labs</a></p>`;return;
    }
    target.innerHTML=`<div class="evolution-viewport" tabindex="0" role="region" aria-label="Lab evolution map. Scroll or drag to pan; pinch to zoom. Tab to a study and press Enter to open it."><div class="evolution-space"><div class="evolution-world"><svg class="evolution-edges" aria-hidden="true"></svg>${model.ordered.map(lab=>`<a class="evolution-card" data-lab="${escape(lab.id)}" data-stage="${escape(lab.stage)}" href="/lab?id=${encodeURIComponent(lab.id)}" aria-label="${escape(lab.title)}, ${escape(lab.stage)}, created ${escape(dateLabel(lab.created))}" title="${escape(lab.summary || lab.title)}"><span class="evolution-card-top"><span class="evolution-status"><i></i>${escape(lab.stage || 'Study')}</span><span class="evolution-open" aria-hidden="true">↗</span></span><h3>${escape(lab.title)}</h3><span class="evolution-card-bottom"><span>${escape(number(lab.id))}</span><time datetime="${escape(lab.created || '')}">${escape(dateLabel(lab.created))}</time></span></a>`).join('')}</div></div></div><div class="evolution-context" aria-live="polite"><span class="evolution-context-label">THE RESEARCH SO FAR</span><span data-evolution-context>${labs.length} studies, connected by the work they build on.</span></div>`;
    const viewport=target.querySelector('.evolution-viewport'), space=target.querySelector('.evolution-space'), world=target.querySelector('.evolution-world'), surface=target.querySelector('svg');
    const cards=[...world.querySelectorAll('.evolution-card')];
    model=layout(labs,new Map(cards.map(card=>[card.dataset.lab,card.offsetHeight])));
    const state={zoom:1,offsetX:0,offsetY:0,fit:false,followLatest:true,disposed:false};
    world.style.width=`${model.width}px`;world.style.height=`${model.height}px`;
    surface.setAttribute('viewBox',`0 0 ${model.width} ${model.height}`);
    surface.innerHTML=model.edges.map(edge=>`<path class="evolution-edge" data-source="${escape(edge.source)}" data-target="${escape(edge.target)}" d="${edge.path}"/>`).join('');
    cards.forEach(card=>{const node=model.nodes.get(card.dataset.lab);card.style.left=`${node.x}px`;card.style.top=`${node.y}px`;});
    const edgeElements=[...surface.querySelectorAll('.evolution-edge')];
    const defaultContext=`${labs.length} studies · ${model.edges.length} recorded connections. Dates show when each study began.`;
    const context=target.querySelector('[data-evolution-context]');context.textContent=defaultContext;
    const trace=id=>{
      const neighbors=new Set([id]);model.edges.filter(e=>e.source===id || e.target===id).forEach(e=>{neighbors.add(e.source);neighbors.add(e.target);});
      cards.forEach(card=>{card.classList.toggle('is-muted',Boolean(id)&&!neighbors.has(card.dataset.lab));card.classList.toggle('is-traced',id===card.dataset.lab);});
      edgeElements.forEach(edge=>{const active=edge.dataset.source===id || edge.dataset.target===id;edge.classList.toggle('is-traced',active);edge.classList.toggle('is-muted',Boolean(id)&&!active);});
      const lab=model.nodes.get(id);
      context.textContent=lab ? `${lab.title}${model.parents.get(id).length?' · Builds on '+model.parents.get(id).map(parent=>model.nodes.get(parent).title).join(' and '):' · Founding study'}` : defaultContext;
    };
    const maxViewportHeight=()=>{
      const cssMax=parseFloat(getComputedStyle(viewport).maxHeight);
      return Number.isFinite(cssMax)&&cssMax>0?cssMax:VIEWPORT_MAX;
    };
    const revealLatest=()=>{
      viewport.scrollLeft=Math.max(0,viewport.scrollWidth-viewport.clientWidth);
      viewport.scrollTop=0;
    };
    const paint=()=>{
      const scaledW=model.width*state.zoom,scaledH=model.height*state.zoom;
      const nextHeight=Math.min(maxViewportHeight(),Math.max(160,Math.ceil(scaledH+VIEWPORT_GAP)));
      if (viewport.style.height!==`${nextHeight}px`) viewport.style.height=`${nextHeight}px`;
      const width=Math.max(viewport.clientWidth,scaledW),height=Math.max(viewport.clientHeight,scaledH);
      const spareX=width-scaledW;
      state.offsetX=state.followLatest?spareX:spareX/2;
      state.offsetY=(height-scaledH)/2;
      space.style.width=`${width}px`;space.style.height=`${height}px`;
      world.style.transform=`translate(${state.offsetX}px, ${state.offsetY}px) scale(${state.zoom})`;
      viewport.dataset.zoom=String(state.zoom);
      const output=controls?.querySelector('[data-timeline-scale]');if(output)output.textContent=`${Math.round(state.zoom*100)}%`;
      controls?.querySelector('[data-timeline-zoom-out]')?.toggleAttribute('disabled',state.zoom<=MIN_ZOOM);
      controls?.querySelector('[data-timeline-zoom-in]')?.toggleAttribute('disabled',state.zoom>=MAX_ZOOM);
    };
    const zoomTo=(value,x=viewport.clientWidth/2,y=viewport.clientHeight/2)=>{
      const wx=(viewport.scrollLeft+x-state.offsetX)/state.zoom,wy=(viewport.scrollTop+y-state.offsetY)/state.zoom;
      state.zoom=clamp(value,MIN_ZOOM,MAX_ZOOM);state.fit=false;state.followLatest=false;paint();
      viewport.scrollLeft=wx*state.zoom+state.offsetX-x;viewport.scrollTop=wy*state.zoom+state.offsetY-y;
    };
    const fit=(overview=false)=>{
      state.followLatest=false;state.fit=overview?'overview':false;
      state.zoom=clamp(Math.min(1,viewport.clientWidth/model.width,viewport.clientHeight/model.height),overview?MIN_ZOOM:1,MAX_ZOOM);
      paint();viewport.scrollLeft=0;viewport.scrollTop=0;trace(null);
    };
    const showLatest=()=>{state.fit=false;state.followLatest=true;state.zoom=1;paint();revealLatest();};
    on(controls?.querySelector('[data-timeline-zoom-in]'),'click',()=>zoomTo(state.zoom*1.2));
    on(controls?.querySelector('[data-timeline-zoom-out]'),'click',()=>zoomTo(state.zoom/1.2));
    on(controls?.querySelector('[data-timeline-fit]'),'click',()=>fit(true));
    let safariGesture=false,gestureZoom=1;
    // Unmodified wheel/trackpad scrolling is deliberately left to the browser.
    // macOS trackpad pinch is delivered as ctrl+wheel in Chromium/Firefox.
    on(viewport,'wheel',event=>{
      if (!event.ctrlKey) return;
      event.preventDefault();if(safariGesture)return;
      const rect=viewport.getBoundingClientRect();zoomTo(state.zoom*Math.exp(-event.deltaY*.008),event.clientX-rect.left,event.clientY-rect.top);
    },{passive:false});
    on(viewport,'gesturestart',event=>{event.preventDefault();safariGesture=true;gestureZoom=state.zoom;},{passive:false});
    on(viewport,'gesturechange',event=>{
      event.preventDefault();const rect=viewport.getBoundingClientRect();
      const x=Number.isFinite(event.clientX)?event.clientX-rect.left:viewport.clientWidth/2;
      const y=Number.isFinite(event.clientY)?event.clientY-rect.top:viewport.clientHeight/2;
      if(Number.isFinite(event.scale))zoomTo(gestureZoom*event.scale,x,y);
    },{passive:false});
    on(viewport,'gestureend',event=>{event.preventDefault();safariGesture=false;},{passive:false});
    const pointers=new Map();let drag=null,pinch=null,suppressClick=false;
    const pair=()=>{const [a,b]=[...pointers.values()];return {distance:Math.hypot(a.x-b.x,a.y-b.y),x:(a.x+b.x)/2,y:(a.y+b.y)/2};};
    on(viewport,'pointerdown',event=>{
      if(event.button!==0)return;
      if(event.pointerType==='mouse'&&event.target.closest('.evolution-card')){suppressClick=false;return;}
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===1){suppressClick=false;drag={x:event.clientX,y:event.clientY,left:viewport.scrollLeft,top:viewport.scrollTop};}
      else if(pointers.size===2){pinch={...pair(),zoom:state.zoom};drag=null;suppressClick=true;}
      // Capture on the original link for touch, preserving stationary tap clicks.
      event.target.setPointerCapture(event.pointerId);
    });
    on(viewport,'pointermove',event=>{
      if(!pointers.has(event.pointerId))return;
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===2&&pinch){const next=pair(),rect=viewport.getBoundingClientRect();zoomTo(pinch.zoom*next.distance/Math.max(1,pinch.distance),pinch.x-rect.left,pinch.y-rect.top);viewport.scrollLeft-=next.x-pinch.x;viewport.scrollTop-=next.y-pinch.y;pinch={...next,zoom:state.zoom};}
      else if(drag){const dx=event.clientX-drag.x,dy=event.clientY-drag.y;if(Math.hypot(dx,dy)>4){suppressClick=true;state.followLatest=false;viewport.classList.add('is-dragging');viewport.scrollLeft=drag.left-dx;viewport.scrollTop=drag.top-dy;}}
    });
    const release=event=>{pointers.delete(event.pointerId);pinch=null;drag=null;viewport.classList.remove('is-dragging');if(pointers.size===1){const p=[...pointers.values()][0];drag={x:p.x,y:p.y,left:viewport.scrollLeft,top:viewport.scrollTop};}};
    on(viewport,'pointerup',release);on(viewport,'pointercancel',release);
    on(viewport,'click',event=>{if(suppressClick){event.preventDefault();event.stopPropagation();suppressClick=false;}},{capture:true});
    on(viewport,'keydown',event=>{if(event.target!==viewport)return;if(event.key==='+'||event.key==='='){event.preventDefault();zoomTo(state.zoom*1.2);}if(event.key==='-'){event.preventDefault();zoomTo(state.zoom/1.2);}if(event.key==='0'){event.preventDefault();fit(true);}});
    cards.forEach(card=>{
      on(card,'pointerenter',()=>{if(!pointers.size)trace(card.dataset.lab);});on(card,'pointerleave',()=>{if(document.activeElement!==card)trace(null);});
      on(card,'focus',()=>trace(card.dataset.lab));on(card,'blur',()=>trace(null));
      on(card,'click',event=>{if(event.defaultPrevented||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;if(window.HeraldNavigate){event.preventDefault();window.HeraldNavigate(card.getAttribute('href'));}});
    });
    const observer=new ResizeObserver(()=>{
      if(state.disposed)return;
      if(state.fit==='overview') fit(true);
      else {paint();if(state.followLatest)revealLatest();}
    });observer.observe(viewport);showLatest();
    dispose=()=>{state.disposed=true;controller.abort();observer.disconnect();dispose=()=>{};};
  }
  window.HeraldResearchTimeline={mount,layout,dispose:()=>dispose()};
}());

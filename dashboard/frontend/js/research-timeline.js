(function () {
  const NS = 'http://www.w3.org/2000/svg';
  const PADDING_X = 74;
  const DATE_GROUP_GAP = .72;
  const MAX_SLOT_PIXELS = 118;
  const MIN_ZOOM = 1;
  const MAX_ZOOM = 10;
  const STAGE_COLORS = { design: '#7567b7', active: '#087a70', blocked: '#b94034', complete: '#687673' };
  let cleanup = () => {};

  const escape = value => String(value ?? '').replace(/[&<>'"]/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;' }[character]));
  const dateValue = value => Date.parse(`${value}T00:00:00Z`);
  const dateLabel = value => new Intl.DateTimeFormat('en', { month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC' }).format(new Date(dateValue(value)));
  const shortNumber = id => `Lab ${String(id).match(/^lab-(\d+)/)?.[1] || id}`;
  const svg = (name, attributes = {}) => { const element = document.createElementNS(NS, name); Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value)); return element; };
  const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));

  function layout(labs) {
    const byId = new Map(labs.map(lab => [lab.id, lab]));
    const children = new Map(labs.map(lab => [lab.id, []]));
    labs.forEach(lab => (lab.parents || []).filter(parent => byId.has(parent)).forEach(parent => children.get(parent).push(lab)));
    children.forEach(items => items.sort((a, b) => dateValue(a.created) - dateValue(b.created) || a.id.localeCompare(b.id)));
    const ordered = [...labs].sort((a, b) => dateValue(a.created) - dateValue(b.created) || a.id.localeCompare(b.id));
    const dateGroups = [];
    ordered.forEach(lab => {
      let group = dateGroups.at(-1);
      if (!group || group.date !== lab.created) { group = { date: lab.created, labs: [] }; dateGroups.push(group); }
      group.labs.push(lab);
    });
    const xPositions = new Map();
    const withinDays = new Map();
    let xCursor = 0;
    dateGroups.forEach((group, index) => {
      group.start = xCursor;
      group.labs.forEach((lab, withinDay) => { xPositions.set(lab.id, xCursor + withinDay); withinDays.set(lab.id, withinDay); });
      group.end = xCursor + group.labs.length - 1;
      group.center = (group.start + group.end) / 2;
      xCursor = group.end + 1 + (index < dateGroups.length - 1 ? DATE_GROUP_GAP : 0);
    });
    const separators = dateGroups.slice(0, -1).map((group, index) => (group.end + dateGroups[index + 1].start) / 2);
    const lanes = new Map();
    let nextLane = 0;
    ordered.forEach(lab => {
      const parents = (lab.parents || []).filter(parent => byId.has(parent));
      if (!parents.length) { lanes.set(lab.id, nextLane++); return; }
      const primary = parents[0];
      const siblings = children.get(primary) || [];
      lanes.set(lab.id, siblings[0]?.id === lab.id ? lanes.get(primary) : nextLane++);
    });
    return {
      byId, children, ordered, lanes, laneCount: Math.max(1, nextLane),
      dateGroups, separators, xPositions, withinDays,
      minX: dateGroups[0].start - .55,
      maxX: dateGroups.at(-1).end + .55
    };
  }

  function mount(labs) {
    cleanup();
    const target = document.querySelector('#research-timeline');
    if (!target || !labs?.length) return;
    const model = layout(labs);
    const state = { zoom: 1, pan: 0, laneSpacing: 52, dragging: null, disposed: false };
    target.innerHTML = `<div class="timeline-canvas" tabindex="0" aria-label="Research timeline. Drag to pan; use the controls or mouse wheel to zoom."></div><div class="timeline-tooltip" role="tooltip" hidden></div>`;
    const canvas = target.querySelector('.timeline-canvas');
    const tooltip = target.querySelector('.timeline-tooltip');
    const controls = document.querySelector('#timeline-controls');
    const dimensions = () => ({ width: Math.max(320, Math.round(canvas.getBoundingClientRect().width || 800)), height: Math.max(172, 72 + (model.laneCount - 1) * state.laneSpacing + 58) });
    const domain = () => {
      const full = model.maxX - model.minX;
      const visible = full / state.zoom;
      const center = (model.minX + model.maxX) / 2 + state.pan * (full - visible) / 2;
      return [center - visible / 2, center + visible / 2];
    };
    const setZoom = (next, anchor = .5) => {
      const old = domain(), oldSpan = old[1] - old[0];
      state.zoom = clamp(next, MIN_ZOOM, MAX_ZOOM);
      const nextSpan = (model.maxX - model.minX) / state.zoom;
      const anchorPosition = old[0] + oldSpan * anchor;
      const center = anchorPosition - nextSpan * anchor;
      const available = Math.max(.0001, (model.maxX - model.minX) - nextSpan);
      state.pan = clamp(((center - (model.minX + model.maxX) / 2) * 2) / available, -1, 1);
      draw();
    };
    const open = lab => (window.HeraldNavigate || (path => { window.location.href = path; }))(`/lab?id=${encodeURIComponent(lab.id)}`);
    const showTip = (event, lab) => {
      tooltip.innerHTML = `<strong>${escape(shortNumber(lab.id))}</strong><span>${escape(lab.title)}</span><small>${escape(dateLabel(lab.created))} · ${escape(lab.stage)}</small>`;
      tooltip.hidden = false;
      const bounds = target.getBoundingClientRect();
      tooltip.style.left = `${clamp(event.clientX - bounds.left + 12, 8, bounds.width - 220)}px`;
      tooltip.style.top = `${clamp(event.clientY - bounds.top + 12, 8, bounds.height - 74)}px`;
    };

    function draw() {
      const size = dimensions();
      const [start, end] = domain();
      const availableWidth = size.width - PADDING_X - 28;
      const plotWidth = Math.min(availableWidth, (model.maxX - model.minX) * MAX_SLOT_PIXELS);
      const plotLeft = PADDING_X + (availableWidth - plotWidth) / 2;
      const plotRight = plotLeft + plotWidth;
      const scaleX = value => plotLeft + ((value - start) / (end - start)) * plotWidth;
      const laneY = lane => 58 + lane * state.laneSpacing;
      const surface = svg('svg', { viewBox: `0 0 ${size.width} ${size.height}`, width: '100%', height: size.height, role: 'img', 'aria-label': 'Branching timeline of Labs by creation date' });
      surface.append(svg('rect', { x: .5, y: .5, width: size.width - 1, height: size.height - 1, rx: 8, class: 'timeline-frame' }));
      const axisY = size.height - 29;
      surface.append(svg('line', { x1: plotLeft, y1: axisY, x2: plotRight, y2: axisY, class: 'timeline-axis' }));
      model.separators.forEach(separator => {
        const x = scaleX(separator);
        if (x > plotLeft && x < plotRight) surface.append(svg('line', { x1: x, y1: 18, x2: x, y2: axisY, class: 'timeline-day-separator' }));
      });
      model.dateGroups.forEach(group => {
        const x = scaleX(group.center);
        if (x < plotLeft - 2 || x > plotRight + 2) return;
        const label = svg('text', { x, y: axisY + 20, 'text-anchor': 'middle', class: 'timeline-tick' });
        label.textContent = dateLabel(group.date);
        surface.append(label);
      });
      model.ordered.forEach(lab => {
        const targetX = scaleX(model.xPositions.get(lab.id)), targetY = laneY(model.lanes.get(lab.id));
        (lab.parents || []).filter(parent => model.byId.has(parent)).forEach(parentId => {
          const sourceX = scaleX(model.xPositions.get(parentId)), sourceY = laneY(model.lanes.get(parentId));
          const lane = model.lanes.get(parentId);
          const obstruction = model.ordered.some(other => other.id !== parentId && other.id !== lab.id && model.lanes.get(other.id) === lane && model.xPositions.get(other.id) > model.xPositions.get(parentId) && model.xPositions.get(other.id) < model.xPositions.get(lab.id));
          let path;
          if (sourceY === targetY && !obstruction) path = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`;
          else {
            const direction = targetY >= sourceY ? 1 : -1;
            const corridorY = sourceY + direction * state.laneSpacing * .42;
            const shoulder = Math.min(34, Math.max(16, (targetX - sourceX) * .22));
            path = `M ${sourceX} ${sourceY} C ${sourceX + shoulder * .45} ${sourceY}, ${sourceX + shoulder * .55} ${corridorY}, ${sourceX + shoulder} ${corridorY} L ${targetX - shoulder} ${corridorY} C ${targetX - shoulder * .55} ${corridorY}, ${targetX - shoulder * .45} ${targetY}, ${targetX} ${targetY}`;
          }
          surface.append(svg('path', { d: path, class: 'timeline-link' }));
        });
      });
      model.ordered.forEach(lab => {
        const x = scaleX(model.xPositions.get(lab.id)), y = laneY(model.lanes.get(lab.id));
        if (x < plotLeft - 24 || x > plotRight + 24) return;
        const group = svg('g', { class: 'timeline-node', tabindex: '0', role: 'link', 'aria-label': `${shortNumber(lab.id)}: ${lab.title}` });
        group.append(svg('circle', { cx: x, cy: y, r: 15, class: 'timeline-node-halo' }));
        group.append(svg('circle', { cx: x, cy: y, r: 10, fill: STAGE_COLORS[lab.stage] || '#687673', class: 'timeline-node-marker' }));
        group.append(svg('circle', { cx: x, cy: y, r: 4, class: 'timeline-node-core' }));
        const labelAbove = model.withinDays.get(lab.id) % 2 === 0;
        const label = svg('text', { x, y: y + (labelAbove ? -17 : 25), 'text-anchor': 'middle', class: 'timeline-label' });
        label.textContent = shortNumber(lab.id);
        group.append(label);
        group.addEventListener('pointerenter', event => showTip(event, lab));
        group.addEventListener('pointermove', event => showTip(event, lab));
        group.addEventListener('pointerleave', () => { tooltip.hidden = true; });
        group.addEventListener('click', () => open(lab));
        group.addEventListener('keydown', event => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); open(lab); } });
        surface.append(group);
      });
      canvas.replaceChildren(surface);
      controls?.querySelector('[data-timeline-zoom-out]')?.toggleAttribute('disabled', state.zoom <= MIN_ZOOM);
      controls?.querySelector('[data-timeline-zoom-in]')?.toggleAttribute('disabled', state.zoom >= MAX_ZOOM);
    }

    const onWheel = event => { event.preventDefault(); const rect = canvas.getBoundingClientRect(); setZoom(state.zoom * Math.exp(-event.deltaY * .0015), clamp((event.clientX - rect.left) / rect.width, 0, 1)); };
    const onDown = event => { if (event.target.closest('.timeline-node')) return; state.dragging = { x: event.clientX, pan: state.pan }; canvas.setPointerCapture(event.pointerId); };
    const onMove = event => { if (!state.dragging) return; const rect = canvas.getBoundingClientRect(); const visibleRatio = 1 - 1 / state.zoom; state.pan = visibleRatio ? clamp(state.dragging.pan - ((event.clientX - state.dragging.x) / rect.width) * 2 / visibleRatio, -1, 1) : 0; draw(); };
    const onUp = () => { state.dragging = null; };
    const zoomIn = () => setZoom(state.zoom * 1.55);
    const zoomOut = () => setZoom(state.zoom / 1.55);
    const fit = () => { state.zoom = 1; state.pan = 0; draw(); };
    const spacing = event => { state.laneSpacing = Number(event.target.value); draw(); };
    canvas.addEventListener('wheel', onWheel, { passive: false });
    canvas.addEventListener('pointerdown', onDown); canvas.addEventListener('pointermove', onMove); canvas.addEventListener('pointerup', onUp); canvas.addEventListener('pointercancel', onUp);
    controls?.querySelector('[data-timeline-zoom-in]')?.addEventListener('click', zoomIn);
    controls?.querySelector('[data-timeline-zoom-out]')?.addEventListener('click', zoomOut);
    controls?.querySelector('[data-timeline-fit]')?.addEventListener('click', fit);
    controls?.querySelector('[data-timeline-spacing]')?.addEventListener('change', spacing);
    const observer = new ResizeObserver(draw); observer.observe(canvas); draw();
    cleanup = () => { state.disposed = true; observer.disconnect(); canvas.removeEventListener('wheel', onWheel); canvas.removeEventListener('pointerdown', onDown); canvas.removeEventListener('pointermove', onMove); canvas.removeEventListener('pointerup', onUp); canvas.removeEventListener('pointercancel', onUp); cleanup = () => {}; };
  }

  window.HeraldResearchTimeline = { mount, layout };
}());

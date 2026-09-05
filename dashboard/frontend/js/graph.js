(function () {
  const DESKTOP_HEIGHT = 520;
  const MOBILE_HEIGHT = 380;
  const WHEEL_ZOOM_SENSITIVITY = .0008;
  const MAX_WHEEL_DELTA = 40;
  // The layout is allowed to keep its natural shape.  This only starts to act
  // once its bounding box is visibly unlike the drawing area.
  const ASPECT_RATIO_DEAD_ZONE = .045;
  const ASPECT_RATIO_STRENGTH = .0028;
  const DOUBLE_CLICK_WINDOW_MS = 360;
  const BASE_LABEL_COUNT = 7;
  const MAX_LABEL_LINES = 3;
  const LABEL_LINE_WIDTH = 24;
  const TYPE_COLORS = {
    project: '#147d70', concept: '#536fb5', method: '#d27a35', reference: '#a3538f',
    evidence: '#6a8b3d', note: '#6f7d79'
  };
  let activeCleanup = () => {};

  const escape = value => String(value ?? '').replace(/[&<>"']/g, character => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;'
  })[character]);
  const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(maximum, value));
  const hash = value => [...value].reduce((result, character) => ((result * 33) ^ character.charCodeAt(0)) >>> 0, 5381);
  const labelWidth = value => [...String(value)].reduce((width, character) => width + (/[^\x00-\xff]/.test(character) ? 2 : 1), 0);

  function truncateLabelLine(value, width) {
    let result = '';
    let used = 0;
    for (const character of [...String(value)]) {
      const next = /[^\x00-\xff]/.test(character) ? 2 : 1;
      if (used + next + 1 > width) break;
      result += character;
      used += next;
    }
    return `${result.trimEnd()}…`;
  }

  function wrappedLabel(value, lineWidth = LABEL_LINE_WIDTH, maxLines = MAX_LABEL_LINES) {
    const words = String(value).trim().split(/\s+/).filter(Boolean);
    if (!words.length) return [''];
    const lines = [];
    let current = '';
    words.forEach(word => {
      if (labelWidth(word) > lineWidth) {
        if (current) {
          lines.push(current);
          current = '';
        }
        let segment = '';
        [...word].forEach(character => {
          if (labelWidth(segment + character) > lineWidth) {
            lines.push(segment);
            segment = character;
          } else segment += character;
        });
        current = segment;
        return;
      }
      const candidate = current ? `${current} ${word}` : word;
      if (labelWidth(candidate) <= lineWidth) current = candidate;
      else {
        lines.push(current);
        current = word;
      }
    });
    if (current) lines.push(current);
    if (lines.length <= maxLines) return lines;
    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] = truncateLabelLine(`${kept[maxLines - 1]} ${lines.slice(maxLines).join(' ')}`, lineWidth);
    return kept;
  }

  function spatialLabelRank(nodes, positions) {
    const maximumImportance = Math.max(...nodes.map(node => node.importance_score || 0), 1);
    const nearest = node => {
      const point = positions[node.id];
      if (!point || nodes.length < 2) return 0;
      return Math.min(...nodes.filter(other => other.id !== node.id).map(other => {
        const otherPoint = positions[other.id];
        return otherPoint ? Math.hypot(point.x - otherPoint.x, point.y - otherPoint.y) : 0;
      }));
    };
    const distances = new Map(nodes.map(node => [node.id, nearest(node)]));
    const maximumDistance = Math.max(1, ...distances.values());
    const score = node => .6 * ((node.importance_score || 0) / maximumImportance) + .4 * (distances.get(node.id) / maximumDistance);
    return [...nodes].sort((left, right) => score(right) - score(left) || String(left.id).localeCompare(String(right.id)));
  }

  function graphSize(target) {
    const width = Math.max(320, Math.round(target.getBoundingClientRect().width || 760));
    return { width, height: width < 620 ? MOBILE_HEIGHT : DESKTOP_HEIGHT };
  }

  function softAspectRatioForce(nodes, positions, size, alpha = 1) {
    if (nodes.length < 2) return 0;
    const points = nodes.map(node => positions[node.id]).filter(Boolean);
    if (points.length < 2) return 0;
    const bounds = points.reduce((box, point) => ({
      minX: Math.min(box.minX, point.x), maxX: Math.max(box.maxX, point.x),
      minY: Math.min(box.minY, point.y), maxY: Math.max(box.maxY, point.y)
    }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });
    const graphAspect = Math.max(1, bounds.maxX - bounds.minX) / Math.max(1, bounds.maxY - bounds.minY);
    const canvasAspect = size.width / size.height;
    const imbalance = Math.log(graphAspect / canvasAspect);
    const excess = Math.abs(imbalance) - ASPECT_RATIO_DEAD_ZONE;
    if (excess <= 0) return 0;

    // A gentle affine nudge about the graph centre: a too-wide graph contracts
    // in x and expands in y (and vice versa).  It is deliberately a force,
    // rather than a rescale or boundary, so links, communities, and dragging
    // can still determine the final embedding.
    const correction = Math.sign(imbalance) * Math.min(.6, excess) * ASPECT_RATIO_STRENGTH * alpha;
    const centerX = (bounds.minX + bounds.maxX) / 2;
    const centerY = (bounds.minY + bounds.maxY) / 2;
    nodes.forEach(node => {
      const point = positions[node.id];
      if (!point || point.fixed) return;
      point.vx -= (point.x - centerX) * correction;
      point.vy += (point.y - centerY) * correction;
    });
    return correction;
  }

  function communityAnchors(graph, size) {
    const communities = graph.communities.length ? graph.communities : [{ id: 0 }];
    return new Map(communities.map((community, index) => {
      const x = size.width * ((index + 1) / (communities.length + 1));
      const y = size.height * (communities.length === 1 ? .5 : index % 2 ? .64 : .36);
      return [community.id, { x, y }];
    }));
  }

  function seededPositions(graph, size, salt = 0) {
    const anchors = communityAnchors(graph, size);
    return Object.fromEntries(graph.nodes.map((node, index) => {
      const seed = hash(`${node.id}:${salt}`);
      const anchor = node.type === 'project'
        ? { x: size.width / 2, y: size.height / 2 }
        : anchors.get(node.community) || { x: size.width / 2, y: size.height / 2 };
      const angle = ((seed % 360) / 180) * Math.PI + index * .37;
      const radius = 38 + seed % 62;
      return [node.id, {
        x: clamp(anchor.x + Math.cos(angle) * radius, 28, size.width - 28),
        y: clamp(anchor.y + Math.sin(angle) * radius, 28, size.height - 28),
        vx: 0, vy: 0, fixed: false
      }];
    }));
  }

  function mount(graph) {
    activeCleanup();
    const target = document.querySelector('#relation-graph');
    if (!target) return;

    const visibleEdges = graph.display_edges || graph.edges;
    const confirmedEdges = visibleEdges.filter(edge => edge.display_role !== 'predicted');
    const state = {
      graph,
      size: graphSize(target),
      positions: null,
      labelOrder: [],
      colorMode: 'community',
      view: null,
      pan: null,
      drag: null,
      alpha: 1,
      frame: 0,
      salt: 0,
      disposed: false,
      edgeElements: new Map(),
      nodeElements: new Map(),
      labelElements: new Map(),
      lastNodeTap: null
    };
    state.positions = seededPositions(graph, state.size);
    state.labelOrder = spatialLabelRank(graph.nodes, state.positions).map(node => node.id);
    state.view = { x: 0, y: 0, width: state.size.width, height: state.size.height };

    const community = id => graph.communities.find(item => item.id === id);
    const nodeColor = node => state.colorMode === 'type'
      ? (TYPE_COLORS[node.type] || TYPE_COLORS.note)
      : (community(node.community)?.color || TYPE_COLORS.note);
    const edgeKey = edge => `${edge.source}|${edge.target}`;
    const svgPoint = (svg, event) => {
      const point = svg.createSVGPoint();
      point.x = event.clientX;
      point.y = event.clientY;
      return point.matrixTransform(svg.getScreenCTM().inverse());
    };
    const openNode = id => {
      const href = state.nodeElements.get(id)?.getAttribute('href');
      if (href) (window.HeraldNavigate || (path => { window.location.href = path; }))(href);
    };

    function applyZoomInvariantStyles() {
      const inverseZoom = state.view.width / state.size.width;
      graph.nodes.forEach(node => {
        const group = state.nodeElements.get(node.id);
        if (!group) return;
        group.querySelector('circle')?.setAttribute('r', String(node.size * inverseZoom));
        const label = state.labelElements.get(node.id);
        if (!label) return;
        const lines = Number(label.dataset.lines || 1);
        const x = (node.size + 7) * inverseZoom;
        label.setAttribute('x', String(x));
        label.setAttribute('y', String(-((lines - 1) * 5.5) * inverseZoom));
        label.style.fontSize = `${10 * inverseZoom}px`;
        label.style.strokeWidth = `${4 * inverseZoom}px`;
        label.querySelectorAll('tspan').forEach(tspan => tspan.setAttribute('x', String(x)));
      });
    }

    function updateLabelOrder() {
      state.labelOrder = spatialLabelRank(graph.nodes, state.positions).map(node => node.id);
      updateLabelDensity();
    }

    function updateLabelDensity() {
      const svg = target.querySelector('svg');
      if (!svg) return;
      const labels = new Map([...target.querySelectorAll('.knowledge-label')].map(label => [label.dataset.labelFor, label]));
      labels.forEach(label => label.classList.remove('visible'));
      const linearZoom = state.size.width / state.view.width;
      const atMaximumZoom = state.view.width <= state.size.width * .305;
      const targetCount = atMaximumZoom
        ? labels.size
        : Math.max(3, Math.min(labels.size, Math.round(BASE_LABEL_COUNT * linearZoom * linearZoom)));
      const rect = svg.getBoundingClientRect();
      const occupied = [];
      let visibleCount = 0;
      for (const id of state.labelOrder) {
        if (visibleCount >= targetCount && !atMaximumZoom) break;
        const label = labels.get(id);
        const point = state.positions[id];
        if (!label || !point) continue;
        const screenX = (point.x - state.view.x) * rect.width / state.view.width;
        const screenY = (point.y - state.view.y) * rect.height / state.view.height;
        if (!atMaximumZoom && (screenX < -20 || screenX > rect.width + 20 || screenY < -20 || screenY > rect.height + 20)) continue;
        const lines = Number(label.dataset.lines || 1);
        const widest = Number(label.dataset.labelWidth || LABEL_LINE_WIDTH);
        const box = {
          left: screenX + 12,
          right: screenX + 12 + Math.min(LABEL_LINE_WIDTH, widest) * 5.7,
          top: screenY - lines * 6,
          bottom: screenY + lines * 6
        };
        const overlaps = occupied.some(other => !(
          box.right + 4 < other.left || box.left - 4 > other.right
          || box.bottom + 3 < other.top || box.top - 3 > other.bottom
        ));
        if (!atMaximumZoom && overlaps) continue;
        label.classList.add('visible');
        occupied.push(box);
        visibleCount += 1;
      }
    }

    function setView(next) {
      state.view = next;
      target.querySelector('svg')?.setAttribute('viewBox', `${next.x} ${next.y} ${next.width} ${next.height}`);
      applyZoomInvariantStyles();
      updateLabelDensity();
    }

    function fitView() {
      const points = Object.values(state.positions);
      if (!points.length) return;
      const bounds = points.reduce((box, point) => ({
        minX: Math.min(box.minX, point.x), maxX: Math.max(box.maxX, point.x),
        minY: Math.min(box.minY, point.y), maxY: Math.max(box.maxY, point.y)
      }), { minX: Infinity, maxX: -Infinity, minY: Infinity, maxY: -Infinity });
      const padding = 58;
      let width = Math.max(250, bounds.maxX - bounds.minX + padding * 2);
      let height = Math.max(180, bounds.maxY - bounds.minY + padding * 2);
      const aspect = state.size.width / state.size.height;
      if (width / height > aspect) height = width / aspect;
      else width = height * aspect;
      setView({
        x: (bounds.minX + bounds.maxX - width) / 2,
        y: (bounds.minY + bounds.maxY - height) / 2,
        width, height
      });
    }

    function highlight(ids = []) {
      const selected = new Set(ids);
      target.querySelectorAll('[data-node-id]').forEach(element => {
        element.classList.toggle('dimmed', selected.size > 0 && !selected.has(element.dataset.nodeId));
      });
      target.querySelectorAll('[data-edge-key]').forEach(element => {
        const active = selected.has(element.dataset.source) && selected.has(element.dataset.target);
        element.classList.toggle('highlighted', active);
        element.classList.toggle('dimmed', selected.size > 0 && !active);
      });
    }

    function renderLegend() {
      const legend = document.querySelector('#graph-legend');
      if (!legend) return;
      if (state.colorMode === 'community') {
        legend.innerHTML = graph.communities.map(item => `<button type="button" data-community="${item.id}"><i style="background:${item.color}"></i><span>${escape(item.label)}</span></button>`).join('');
      } else {
        const counts = graph.nodes.reduce((result, node) => ({ ...result, [node.type]: (result[node.type] || 0) + 1 }), {});
        legend.innerHTML = Object.entries(counts).map(([type, count]) => `<button type="button" data-type="${escape(type)}"><i style="background:${TYPE_COLORS[type] || TYPE_COLORS.note}"></i><span>${escape(type)}</span><small>${count}</small></button>`).join('');
      }
      legend.querySelectorAll('[data-community]').forEach(button => button.onclick = () => highlight(graph.nodes.filter(node => node.community === Number(button.dataset.community)).map(node => node.id)));
      legend.querySelectorAll('[data-type]').forEach(button => button.onclick = () => highlight(graph.nodes.filter(node => node.type === button.dataset.type).map(node => node.id)));
    }

    function renderInsights() {
      const insightTarget = document.querySelector('#graph-insights');
      if (!insightTarget) return;
      const items = [...(graph.insights.predicted_connections || []), ...(graph.insights.graph_anomalies || [])];
      insightTarget.innerHTML = items.length
        ? items.slice(0, 4).map(item => `<button type="button" data-insight="${item.node_ids.map(encodeURIComponent).join('|')}"><span>${escape(item.title)}</span><small>${escape(item.description)}</small></button>`).join('')
        : '<p class="graph-insight-empty">No predictions or graph anomalies.</p>';
      insightTarget.querySelectorAll('[data-insight]').forEach(button => button.onclick = () => highlight(button.dataset.insight.split('|').map(decodeURIComponent)));
    }

    function updateGeometry() {
      visibleEdges.forEach(edge => {
        const element = state.edgeElements.get(edgeKey(edge));
        const left = state.positions[edge.source];
        const right = state.positions[edge.target];
        if (!element || !left || !right) return;
        element.setAttribute('x1', left.x);
        element.setAttribute('y1', left.y);
        element.setAttribute('x2', right.x);
        element.setAttribute('y2', right.y);
      });
      graph.nodes.forEach(node => {
        const element = state.nodeElements.get(node.id);
        const label = state.labelElements.get(node.id);
        const point = state.positions[node.id];
        if (element && point) element.setAttribute('transform', `translate(${point.x} ${point.y})`);
        if (label && point) label.setAttribute('transform', `translate(${point.x} ${point.y})`);
      });
    }

    function tick() {
      const nodes = graph.nodes;
      const anchors = communityAnchors(graph, state.size);
      for (let index = 0; index < nodes.length; index += 1) {
        for (let other = index + 1; other < nodes.length; other += 1) {
          const leftNode = nodes[index];
          const rightNode = nodes[other];
          const left = state.positions[leftNode.id];
          const right = state.positions[rightNode.id];
          const dx = left.x - right.x || .1;
          const dy = left.y - right.y || .1;
          const distance = Math.max(1, Math.hypot(dx, dy));
          const minimum = leftNode.size + rightNode.size + 28;
          const repulsion = 1800 / (distance * distance) * state.alpha;
          const collision = distance < minimum ? (minimum - distance) * .06 * state.alpha : 0;
          const force = repulsion + collision;
          left.vx += dx / distance * force;
          left.vy += dy / distance * force;
          right.vx -= dx / distance * force;
          right.vy -= dy / distance * force;
        }
      }
      visibleEdges.forEach(edge => {
        const left = state.positions[edge.source];
        const right = state.positions[edge.target];
        if (!left || !right) return;
        const dx = right.x - left.x;
        const dy = right.y - left.y;
        const distance = Math.max(1, Math.hypot(dx, dy));
        const desired = edge.display_role === 'authored' ? 94 : edge.display_role === 'grounded' ? 110 : 124;
        const strength = edge.display_role === 'authored' ? .0064 : edge.display_role === 'grounded' ? .0037 : .0018;
        const force = (distance - desired) * strength * state.alpha;
        left.vx += dx / distance * force;
        left.vy += dy / distance * force;
        right.vx -= dx / distance * force;
        right.vy -= dy / distance * force;
      });
      softAspectRatioForce(nodes, state.positions, state.size, state.alpha);
      nodes.forEach(node => {
        const point = state.positions[node.id];
        const anchor = node.type === 'project'
          ? { x: state.size.width / 2, y: state.size.height / 2 }
          : anchors.get(node.community) || { x: state.size.width / 2, y: state.size.height / 2 };
        const pull = node.type === 'project' ? .014 : .0042;
        point.vx += (anchor.x - point.x) * pull * state.alpha;
        point.vy += (anchor.y - point.y) * pull * state.alpha;
        if (point.fixed) return;
        point.vx *= .82;
        point.vy *= .82;
        point.x = clamp(point.x + point.vx, 24, state.size.width - 24);
        point.y = clamp(point.y + point.vy, 24, state.size.height - 24);
      });
    }

    function simulate() {
      state.frame = 0;
      const loop = () => {
        if (state.disposed) return;
        tick();
        tick();
        updateGeometry();
        state.alpha *= .965;
        if (state.alpha > .012 || state.drag) state.frame = requestAnimationFrame(loop);
        else {
          state.frame = 0;
          updateLabelOrder();
        }
      };
      state.frame = requestAnimationFrame(loop);
    }

    function reheat(alpha = .45) {
      state.alpha = Math.max(state.alpha, alpha);
      if (!state.frame) simulate();
    }

    function render() {
      const edges = visibleEdges.map(edge => `<line class="knowledge-edge ${escape(edge.display_role || 'authored')}" data-edge-key="${escape(edgeKey(edge))}" data-source="${escape(edge.source)}" data-target="${escape(edge.target)}"><title>${escape(edge.reasons.join(' · '))}</title></line>`).join('');
      const nodes = graph.nodes.map(node => {
        return `<a class="knowledge-node-group" data-node-id="${escape(node.id)}" href="${escape(node.href || `/wiki?page=${encodeURIComponent(node.id)}`)}" aria-label="Double-click to open ${escape(node.label)}"><circle class="knowledge-node" r="${node.size}" style="fill:${nodeColor(node)}"></circle><title>Double-click to open ${escape(node.label)}</title></a>`;
      }).join('');
      // SVG uses paint order.  Keeping every label in this final layer means a
      // node can never cover a label, regardless of its index or drag position.
      const labels = graph.nodes.map(node => {
        const lines = wrappedLabel(node.label);
        const width = Math.max(...lines.map(labelWidth));
        const tspans = lines.map((line, index) => `<tspan dy="${index ? '1.12em' : '0'}">${escape(line)}</tspan>`).join('');
        return `<text class="knowledge-label" data-label-for="${escape(node.id)}" data-lines="${lines.length}" data-label-width="${width}">${tspans}</text>`;
      }).join('');
      target.innerHTML = `<svg class="knowledge-svg" viewBox="0 0 ${state.size.width} ${state.size.height}" role="img" aria-label="Interactive Herald Decoder project knowledge graph"><g class="knowledge-edge-layer">${edges}</g><g class="knowledge-node-layer">${nodes}</g><g class="knowledge-label-layer">${labels}</g></svg>`;
      state.edgeElements = new Map([...target.querySelectorAll('[data-edge-key]')].map(element => [element.dataset.edgeKey, element]));
      state.nodeElements = new Map([...target.querySelectorAll('[data-node-id]')].map(element => [element.dataset.nodeId, element]));
      state.labelElements = new Map([...target.querySelectorAll('.knowledge-label')].map(element => [element.dataset.labelFor, element]));
      updateGeometry();
      applyZoomInvariantStyles();
      updateLabelDensity();

      const svg = target.querySelector('svg');
      target.querySelectorAll('[data-node-id]').forEach(element => {
        element.onmouseenter = () => {
          if (state.drag) return;
          const id = element.dataset.nodeId;
          state.labelElements.get(id)?.classList.add('hovered');
          const neighbors = new Set([id]);
          confirmedEdges.forEach(edge => {
            if (edge.source === id) neighbors.add(edge.target);
            if (edge.target === id) neighbors.add(edge.source);
          });
          highlight([...neighbors]);
          const node = graph.nodes.find(item => item.id === id);
          const tooltip = document.querySelector('#graph-tooltip');
          const rich = window.HeraldRichText;
          tooltip.innerHTML = `<strong>${escape(node.label)}</strong><span>${escape(node.type)} · ${node.degree} confirmed links · double-click to open</span><div class="graph-tooltip-summary rich-text">${rich ? rich.block(node.summary) : escape(node.summary)}</div>`;
          rich?.typeset(tooltip);
          tooltip.hidden = false;
        };
        element.onmouseleave = () => {
          if (state.drag) return;
          state.labelElements.get(element.dataset.nodeId)?.classList.remove('hovered');
          highlight();
          document.querySelector('#graph-tooltip').hidden = true;
        };
        element.onfocus = () => state.labelElements.get(element.dataset.nodeId)?.classList.add('hovered');
        element.onblur = () => state.labelElements.get(element.dataset.nodeId)?.classList.remove('hovered');
        element.onpointerdown = event => {
          event.stopPropagation();
          const point = state.positions[element.dataset.nodeId];
          state.drag = { id: element.dataset.nodeId, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, moved: false };
          point.fixed = true;
          element.classList.add('dragging');
          svg.setPointerCapture?.(event.pointerId);
          reheat(.38);
        };
        element.onclick = event => {
          // Pointer capture sends the matching pointer-up to the SVG, not this
          // anchor.  Prevent its unreliable native navigation; pointer-up below
          // owns the robust double-click gesture.
          event.preventDefault();
        };
        element.ondblclick = event => event.preventDefault();
      });

      svg.onwheel = event => {
        event.preventDefault();
        const deltaScale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? state.size.height : 1;
        const wheelDelta = clamp(event.deltaY * deltaScale, -MAX_WHEEL_DELTA, MAX_WHEEL_DELTA);
        const factor = Math.exp(wheelDelta * WHEEL_ZOOM_SENSITIVITY);
        const width = clamp(state.view.width * factor, state.size.width * .3, state.size.width * 2.6);
        const height = width * state.size.height / state.size.width;
        setView({ x: state.view.x + (state.view.width - width) / 2, y: state.view.y + (state.view.height - height) / 2, width, height });
      };
      svg.onpointerdown = event => {
        state.pan = { x: event.clientX, y: event.clientY, view: { ...state.view }, pointerId: event.pointerId };
        svg.setPointerCapture?.(event.pointerId);
        svg.classList.add('panning');
      };
      svg.onpointermove = event => {
        if (state.drag?.pointerId === event.pointerId) {
          const position = svgPoint(svg, event);
          const point = state.positions[state.drag.id];
          point.x = clamp(position.x, 20, state.size.width - 20);
          point.y = clamp(position.y, 20, state.size.height - 20);
          state.drag.moved ||= Math.hypot(event.clientX - state.drag.startX, event.clientY - state.drag.startY) > 4;
          updateGeometry();
          return;
        }
        if (!state.pan || state.pan.pointerId !== event.pointerId) return;
        const rect = svg.getBoundingClientRect();
        setView({ ...state.pan.view, x: state.pan.view.x - (event.clientX - state.pan.x) * state.pan.view.width / rect.width, y: state.pan.view.y - (event.clientY - state.pan.y) * state.pan.view.height / rect.height });
      };
      svg.onpointerup = event => {
        if (state.drag?.pointerId === event.pointerId) {
          const drag = state.drag;
          const element = state.nodeElements.get(drag.id);
          state.positions[drag.id].fixed = false;
          element?.classList.remove('dragging');
          if (drag.moved && element) element.dataset.dragged = 'true';
          if (!drag.moved) {
            const timestamp = performance.now();
            const previous = state.lastNodeTap;
            const isDoubleClick = previous
              && previous.id === drag.id
              && timestamp - previous.timestamp <= DOUBLE_CLICK_WINDOW_MS;
            state.lastNodeTap = isDoubleClick ? null : { id: drag.id, timestamp };
            if (isDoubleClick) openNode(drag.id);
          } else state.lastNodeTap = null;
          state.drag = null;
          reheat(.22);
        }
        if (state.pan?.pointerId === event.pointerId) {
          state.pan = null;
          svg.classList.remove('panning');
        }
      };
      svg.onpointercancel = svg.onpointerup;
    }

    render();
    renderLegend();
    renderInsights();
    simulate();

    const counts = visibleEdges.reduce((result, edge) => ({ ...result, [edge.display_role]: (result[edge.display_role] || 0) + 1 }), {});
    const count = document.querySelector('#graph-count');
    if (count) count.textContent = `${graph.nodes.length} pages · ${graph.communities.length} communities`;
    document.querySelectorAll('[data-graph-color]').forEach(button => button.onclick = () => {
      state.colorMode = button.dataset.graphColor;
      document.querySelectorAll('[data-graph-color]').forEach(item => item.classList.toggle('active', item === button));
      state.nodeElements.forEach((element, id) => {
        const node = graph.nodes.find(item => item.id === id);
        element.querySelector('circle').style.fill = nodeColor(node);
      });
      renderLegend();
    });
    document.querySelectorAll('[data-graph-action]').forEach(button => button.onclick = () => {
      const action = button.dataset.graphAction;
      if (action === 'fit') return fitView();
      if (action === 'relayout') {
        state.salt += 1;
        state.positions = seededPositions(graph, state.size, state.salt);
        setView({ x: 0, y: 0, width: state.size.width, height: state.size.height });
        updateGeometry();
        return reheat(1);
      }
      const factor = action === 'zoom-in' ? .8 : 1.25;
      const width = clamp(state.view.width * factor, state.size.width * .3, state.size.width * 2.6);
      const height = width * state.size.height / state.size.width;
      setView({ x: state.view.x + (state.view.width - width) / 2, y: state.view.y + (state.view.height - height) / 2, width, height });
    });

    const resizeObserver = new ResizeObserver(() => {
      const next = graphSize(target);
      if (Math.abs(next.width - state.size.width) < 2 && next.height === state.size.height) return;
      const scaleX = next.width / state.size.width;
      const scaleY = next.height / state.size.height;
      Object.values(state.positions).forEach(point => {
        point.x *= scaleX;
        point.y *= scaleY;
      });
      state.size = next;
      setView({ x: 0, y: 0, width: next.width, height: next.height });
      reheat(.5);
    });
    resizeObserver.observe(target);

    activeCleanup = () => {
      state.disposed = true;
      if (state.frame) cancelAnimationFrame(state.frame);
      resizeObserver.disconnect();
    };
  }

  window.HeraldKnowledgeGraph = {
    mount,
    cleanup: () => activeCleanup(),
    test: { wrappedLabel, spatialLabelRank, labelWidth, softAspectRatioForce }
  };
})();

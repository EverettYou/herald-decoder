const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'frontend', 'js', 'graph.js'),
  'utf8',
);
const context = { window: {} };
vm.runInNewContext(source, context);
const helpers = context.window.HeraldKnowledgeGraph.test;

test('knowledge graph labels wrap to three fixed-width lines with ellipsis', () => {
  const lines = helpers.wrappedLabel(
    'A deliberately long knowledge graph label that needs several wrapped lines',
    18,
    3,
  );
  assert.equal(lines.length, 3);
  assert.ok(lines[2].endsWith('…'));
  assert.ok(lines.every(line => helpers.labelWidth(line) <= 18));
});

test('label density grows with zoom and reveals every label at maximum zoom', () => {
  assert.match(source, /BASE_LABEL_COUNT \* linearZoom \* linearZoom/);
  assert.match(source, /atMaximumZoom\s*\? labels\.size/);
  assert.match(source, /occupied\.some/);
  assert.match(source, /applyZoomInvariantStyles/);
});

test('labels occupy a final SVG layer above every node', () => {
  assert.match(source, /<g class="knowledge-node-layer">\$\{nodes\}<\/g><g class="knowledge-label-layer">\$\{labels\}<\/g>/);
  assert.match(source, /state\.labelElements = new Map/);
  assert.match(source, /label\.setAttribute\('transform'/);
});

test('hover neighborhood is derived from displayed confirmed edges', () => {
  assert.match(source, /const confirmedEdges = visibleEdges\.filter/);
  assert.match(source, /confirmedEdges\.forEach\(edge =>/);
  assert.doesNotMatch(source, /graph\.edges\.forEach\(edge =>/);
});

test('legend lists only communities and keeps relationship rendering in the graph', () => {
  assert.match(source, /display_role !== 'predicted'/);
  assert.match(source, /graph\.communities\.map/);
  assert.doesNotMatch(source, /graph-relation-legend/);
  assert.doesNotMatch(source, /graph-edge-swatch/);
});

test('a double-click opens a graph node through the pointer-capture-safe gesture', () => {
  assert.match(source, /window\.HeraldNavigate/);
  assert.match(source, /const DOUBLE_CLICK_WINDOW_MS = 360;/);
  assert.match(source, /previous\.id === drag\.id/);
  assert.match(source, /if \(isDoubleClick\) openNode\(drag\.id\)/);
  assert.match(source, /Double-click to open/);
});

test('layout gets a weak aspect-ratio force rather than a geometric rescale', () => {
  const nodes = [{ id: 'left' }, { id: 'right' }];
  const positions = {
    left: { x: 0, y: 0, vx: 0, vy: 0 },
    right: { x: 400, y: 100, vx: 0, vy: 0 },
  };
  const correction = helpers.softAspectRatioForce(nodes, positions, { width: 200, height: 200 });

  assert.ok(correction > 0, 'a too-wide graph is gently corrected');
  assert.ok(positions.left.vx > 0 && positions.right.vx < 0, 'the force narrows the graph');
  assert.ok(positions.left.vy < 0 && positions.right.vy > 0, 'the force gives it more height');
  assert.equal(positions.left.x, 0, 'positions are not hard-rescaled');
  assert.match(source, /ASPECT_RATIO_DEAD_ZONE/);
  assert.match(source, /softAspectRatioForce\(nodes, state\.positions, state\.size, state\.alpha\)/);
});

test('layout cache restores known node positions and simulates only for new nodes', () => {
  assert.match(source, /LAYOUT_CACHE_KEY/);
  assert.match(source, /function restoredPositions/);
  assert.match(source, /alpha: restored\.hasNewNodes \? \.42 : 0/);
  assert.match(source, /scheduleLayoutSave\(\);/);
  assert.match(source, /if \(state\.alpha > \.012\) simulate\(\);/);
});

test('layout cache preserves existing nodes while identifying only new nodes for incremental placement', () => {
  const storage = new Map();
  const cachedContext = { window: { localStorage: {
    getItem: key => storage.get(key) || null,
    setItem: (key, value) => storage.set(key, value),
  } } };
  vm.runInNewContext(source, cachedContext);
  storage.set('herald-decoder:knowledge-graph-layout:v1', JSON.stringify({
    version: 1,
    fingerprint: 'old',
    size: { width: 800, height: 520 },
    nodes: { known: { x: 120, y: 210 } },
  }));
  const graph = { fingerprint: 'new', communities: [{ id: 0 }], nodes: [
    { id: 'known', community: 0, type: 'concept' },
    { id: 'new', community: 0, type: 'method' },
  ] };
  const restored = cachedContext.window.HeraldKnowledgeGraph.test.restoredPositions(graph, { width: 800, height: 520 });
  assert.equal(restored.restored, 1);
  assert.equal(restored.hasNewNodes, true);
  assert.equal(restored.positions.known.x, 120);
  assert.equal(restored.positions.known.y, 210);
  assert.equal(restored.positions.known.anchored, true);
  assert.ok(Number.isFinite(restored.positions.new.x));
});

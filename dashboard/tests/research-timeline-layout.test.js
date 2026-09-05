const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const projectRoot = path.join(__dirname, '..', '..');
const source = fs.readFileSync(path.join(projectRoot, 'dashboard', 'frontend', 'js', 'research-timeline.js'), 'utf8');
const index = JSON.parse(fs.readFileSync(path.join(projectRoot, 'labs', 'labs.json'), 'utf8')).labs;
const labs = index.map(item => ({
  ...item,
  ...JSON.parse(fs.readFileSync(path.join(projectRoot, 'labs', item.id, 'lab.json'), 'utf8')),
}));
const sandbox = { window: {} };
vm.runInNewContext(source, sandbox);
const layout = sandbox.window.HeraldResearchTimeline.layout;

test('same-day Labs receive distinct ordered x slots', () => {
  const model = layout(labs);
  const positions = model.ordered.map(lab => model.xPositions.get(lab.id));
  assert.equal(new Set(positions).size, labs.length);
  assert.ok(model.xPositions.get('lab-001-string-herald-visualization') < model.xPositions.get('lab-002-herald-belief-matching'));
  assert.ok(model.xPositions.get('lab-004-d4-intrinsic-heralded-decoding') < model.xPositions.get('lab-005-spacetime-jit-anyonic-decoding'));
});

test('date separators fall between date groups rather than on Lab nodes', () => {
  const model = layout(labs);
  const nodePositions = new Set(model.xPositions.values());
  assert.equal(model.dateGroups.length, 3);
  assert.equal(model.separators.length, 2);
  model.separators.forEach(separator => assert.equal(nodePositions.has(separator), false));
  model.dateGroups.slice(0, -1).forEach((group, index) => {
    assert.ok(group.end < model.separators[index]);
    assert.ok(model.separators[index] < model.dateGroups[index + 1].start);
  });
});

test('vertical positions remain quantized into integer lanes', () => {
  const model = layout(labs);
  model.ordered.forEach(lab => assert.ok(Number.isInteger(model.lanes.get(lab.id))));
});

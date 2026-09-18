const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');
const root = path.join(__dirname, '../..');
const source = fs.readFileSync(path.join(root, 'dashboard/frontend/js/research-timeline.js'), 'utf8');
const sandbox = {window: {}};
vm.runInNewContext(source, sandbox);
const {layout} = sandbox.window.HeraldResearchTimeline;
const labs = JSON.parse(fs.readFileSync(path.join(root, 'labs/labs.json'))).labs.map(item => ({...item,...JSON.parse(fs.readFileSync(path.join(root,'labs',item.id,'lab.json')))}));
const key = edge => `${edge.source}->${edge.target}`;
const overlap = (a,b) => a.x < b.x+b.width && a.x+a.width > b.x && a.y < b.y+b.height && a.y+a.height > b.y;

test('preserves all registered parent relationships, including cross-generation edges', () => {
  const m = layout(labs);
  assert.deepEqual(Array.from(m.edges,key).sort(), labs.flatMap(lab => (lab.parents||[]).map(source => `${source}->${lab.id}`)).sort());
  assert.equal(m.edges.filter(e=>!e.primary).length,2);
  for (const e of m.edges) assert.ok(m.nodes.get(e.source).x < m.nodes.get(e.target).x);
});

test('layout is independent of registry and parent-array ordering', () => {
  const original = layout(labs), shuffled = layout([...labs].reverse().map(lab=>({...lab,parents:[...(lab.parents||[])].reverse()})));
  for(const [id,node] of original.nodes) {
    const other=shuffled.nodes.get(id);
    assert.deepEqual([node.x,node.y,node.rank],[other.x,other.y,other.rank]);
  }
});

test('branches straddle their shared foundation; the newest direction is not sunk below older branches', () => {
  const m=layout(labs), n=number=>m.nodes.get(labs.find(lab=>lab.id.startsWith(`lab-00${number}-`)).id), center=node=>node.y+node.height/2;
  assert.ok(center(n(6)) < center(n(2)));
  assert.ok(center(n(3)) > center(n(2)));
  assert.equal(center(n(1)),center(n(2)));
  assert.equal(center(n(4)),center(n(5)));
});

test('cards never overlap, including multiple roots and variable measured title heights', () => {
  const fixture=[...labs,{id:'independent',title:'Independent study',created:'2026-09-09',parents:[]}];
  const m=layout(fixture,new Map(fixture.map((lab,i)=>[lab.id,156+i*31]))),nodes=[...m.nodes.values()];
  for(let i=0;i<nodes.length;i++) {
    assert.ok(nodes[i].x>=0 && nodes[i].y>=0);
    assert.ok(nodes[i].x+nodes[i].width<=m.width && nodes[i].y+nodes[i].height<=m.height);
    for(let j=i+1;j<nodes.length;j++) assert.equal(overlap(nodes[i],nodes[j]),false);
  }
});

test('every parent edge uses the same cubic curve and may pass under unrelated cards', () => {
  const m = layout(labs);
  const cubic = /^M [\d.-]+ [\d.-]+ C [\d.-]+ [\d.-]+, [\d.-]+ [\d.-]+, [\d.-]+ [\d.-]+$/;
  for (const edge of m.edges) {
    assert.match(edge.path, cubic);
    assert.equal(edge.points, undefined);
  }
  assert.equal(new Set(m.edges.map(edge => edge.path.replace(/[\d.-]+/g,'n'))).size, 1);
});

test('handles empty catalogs, unregistered parents, and same-day dependencies without inventing dates', () => {
  assert.equal(layout([]).nodes.size,0);
  const fixture=[{id:'b',created:'2026-09-01',parents:['a','a','external']},{id:'a',created:'2026-09-01'}];
  const m=layout(fixture);
  assert.equal(m.edges.length,1);assert.equal(m.nodes.get('b').created,m.nodes.get('a').created);
  assert.ok(m.nodes.get('b').x>m.nodes.get('a').x);
});

test('fails explicitly for cycles or duplicate IDs instead of producing invalid coordinates', () => {
  assert.throws(()=>layout([{id:'a',parents:['b']},{id:'b',parents:['a']}]),/cycle/);
  assert.throws(()=>layout([{id:'a'},{id:'a'}]),/Duplicate/);
});

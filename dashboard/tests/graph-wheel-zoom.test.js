const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'frontend', 'js', 'graph.js'),
  'utf8',
);

test('wheel zoom is continuous and capped at a gentle step', () => {
  assert.match(source, /const WHEEL_ZOOM_SENSITIVITY = \.0008;/);
  assert.match(source, /const MAX_WHEEL_DELTA = 40;/);
  assert.match(source, /Math\.exp\(wheelDelta \* WHEEL_ZOOM_SENSITIVITY\)/);
  assert.doesNotMatch(source, /event\.deltaY > 0 \? 1\.12 : \.88/);

  const maximumFactor = Math.exp(40 * .0008);
  assert.ok(maximumFactor < 1.034, `maximum wheel step is too large: ${maximumFactor}`);
});

const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const app = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'js', 'app.js'), 'utf8');

test('Wiki landing places search under its header without a duplicate research-program CTA', () => {
  const header = app.indexOf('Wiki control plane');
  const search = app.indexOf('id="wiki-landing-search"');
  assert.ok(header >= 0);
  assert.ok(search > header);
  assert.doesNotMatch(app, /Open research program/);
});

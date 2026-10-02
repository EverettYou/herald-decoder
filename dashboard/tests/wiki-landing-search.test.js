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

test('Wiki lint refreshes asynchronously without blocking the landing payload', () => {
  assert.match(app, /id="wiki-lint-status"/);
  assert.match(app, /d\.lint\.refreshing/);
  assert.match(app, /api\('\/api\/wiki\/lint'\)/);
  assert.match(app, /Checking in background/);
});

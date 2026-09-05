const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const root = path.join(__dirname, '..', 'frontend');
const app = fs.readFileSync(path.join(root, 'js', 'app.js'), 'utf8');
const search = fs.readFileSync(path.join(root, 'js', 'search.js'), 'utf8');
const index = fs.readFileSync(path.join(root, 'index.html'), 'utf8');

test('references, labs, and Wiki share one search client', () => {
  assert.match(app, /scope:'references'/);
  assert.match(app, /scope:'labs'/);
  assert.match(app, /scope:'wiki'/);
  assert.match(app, /window\.HeraldSearch\.bind/);
  assert.doesNotMatch(app, /\/api\/wiki\/search/);
  assert.match(search, /fetch\(`\/api\/search\?\$\{params\}`/);
  assert.ok(index.indexOf('/js/search.js') < index.indexOf('/js/app.js'));
});

test('search results distinguish exact, direct, and conceptual matches', () => {
  assert.match(search, /exact: \{ label: 'Exact match', icon: 'fa-bullseye' \}/);
  assert.match(search, /direct: \{ label: 'Direct hit', icon: 'fa-link' \}/);
  assert.match(search, /conceptual: \{ label: 'Conceptually related', icon: 'fa-wand-magic-sparkles' \}/);
});

test('Wiki landing search and control panels precede the navigation sections', () => {
  assert.ok(app.indexOf('class="wiki-landing-search"') < app.indexOf('class="wiki-index-stats"'));
  assert.match(app, /class="wiki-index-grid"/);
  assert.match(app, /class="wiki-index-lower"/);
  assert.ok(app.indexOf('${controlPanels}${navigationSections}') >= 0);
  assert.ok(app.indexOf("section('Research program'") > app.indexOf('const navigationSections='));
});

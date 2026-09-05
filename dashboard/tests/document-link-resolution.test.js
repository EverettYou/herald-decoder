const assert = require('node:assert/strict');
const path = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'frontend', 'js', 'rich-text.js'));

const { resolveProjectHref } = window.HeraldRichText.testing;

assert.equal(
  resolveProjectHref('../../wiki/methods/herald-aware-belief-matching.md#probabilistic-model-and-inference-target', 'labs/lab-002-herald-belief-matching/REPORT.md'),
  '/wiki?page=methods%2Fherald-aware-belief-matching#probabilistic-model-and-inference-target'
);
assert.equal(
  resolveProjectHref('notes/bp-convergence-remediation.md#c5--c8-bounded-implementation-work', 'labs/lab-002-herald-belief-matching/REPORT.md'),
  '/document?path=labs%2Flab-002-herald-belief-matching%2Fnotes%2Fbp-convergence-remediation.md#c5--c8-bounded-implementation-work'
);
assert.equal(
  resolveProjectHref('figures/herald-belief-matching.html', 'labs/lab-002-herald-belief-matching/REPORT.md'),
  '/lab-assets/lab-002-herald-belief-matching/figures/herald-belief-matching.html'
);
assert.equal(
  resolveProjectHref(
    '../../labs/lab-006-sun-bp-theory/REPORT.md#4-executable-evidence',
    'wiki/methods/sun-fusion-herald-belief-propagation.md'
  ),
  '/document?path=labs%2Flab-006-sun-bp-theory%2FREPORT.md#4-executable-evidence'
);
assert.equal(resolveProjectHref('../../.env', 'labs/lab-002-herald-belief-matching/REPORT.md'), null);
assert.equal(resolveProjectHref('https://example.org', 'labs/lab-002-herald-belief-matching/REPORT.md'), null);

const appSource = require('node:fs').readFileSync(
  path.join(__dirname, '..', 'frontend', 'js', 'app.js'),
  'utf8'
);
assert.match(appSource, /markdown\(p\.content,\{sourcePath:p\.path\}\)/);

console.log('project document link resolution passed');

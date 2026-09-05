const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const css = fs.readFileSync(
  path.join(__dirname, '..', 'frontend', 'css', 'interface.css'),
  'utf8',
);

function rule(selector) {
  const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const match = css.match(new RegExp(`${escaped}\\s*\\{([^}]*)\\}`));
  assert.ok(match, `missing CSS rule for ${selector}`);
  return match[1];
}

test('search controls use one explicit vertical coordinate system', () => {
  assert.match(rule('.search-control'), /height:\s*44px/);
  assert.match(rule('.search-control input'), /padding:\s*0 42px 0 40px/);

  const icon = rule('.search-icon');
  assert.match(icon, /top:\s*0/);
  assert.match(icon, /height:\s*44px/);
  assert.match(icon, /display:\s*grid/);
  assert.match(icon, /place-items:\s*center/);
  assert.doesNotMatch(icon, /translateY/);

  const clear = rule('.search-clear');
  assert.match(clear, /top:\s*7px/);
  assert.match(clear, /height:\s*30px/);
  assert.match(clear, /display:\s*grid/);
  assert.match(clear, /place-items:\s*center/);
  assert.doesNotMatch(clear, /translateY/);

  const select = rule('.select-control');
  assert.match(select, /height:\s*44px/);
  assert.match(select, /margin:\s*0/);

  const toolbar = rule('.reference-toolbar,\n.lab-toolbar');
  assert.match(toolbar, /align-items:\s*center/);
});

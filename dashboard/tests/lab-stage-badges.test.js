const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const css = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'css', 'interface.css'), 'utf8');
const page = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'js', 'lab-page.js'), 'utf8');
const app = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'js', 'app.js'), 'utf8');

test('Lab stage taxonomy and badge colors use one canonical vocabulary', () => {
  ['active', 'blocked', 'complete'].forEach(stage => {
    assert.match(css, new RegExp(`\\.badge-${stage}\\s*\\{`));
  });
  assert.match(page, /\['active', 'blocked', 'complete'\]/);
  assert.doesNotMatch(page, /\['design', 'active', 'blocked', 'complete'\]/);
});

test('Lab detail does not present a fictional linear research pipeline', () => {
  assert.doesNotMatch(page, /REPORT STATUS/);
  assert.doesNotMatch(page, /detail\.progress/);
  assert.doesNotMatch(page, /\['Frame', 'complete'\]/);
  assert.doesNotMatch(page, /\['Promote'/);
});

test('Lab catalog renders a Lab number, creation date, and parent lineage from metadata', () => {
  assert.match(app, /const labNumber=id=>/);
  assert.match(app, /padStart\(3,'0'\)/);
  assert.match(app, /class="lab-row-number"/);
  assert.match(app, /class="lab-row-meta"/);
  assert.match(app, /class="lab-row-created"/);
  assert.match(app, /class="lab-row-created">\$\{escapeHtml\(item\.created/);
  assert.doesNotMatch(app, /Created \$\{escapeHtml\(item\.created/);
  assert.match(app, /<b>Parents<\/b>/);
  assert.match(app, /item\.parents\|\|\[\]/);
  assert.match(css, /\.lab-row-number\s*\{/);
  assert.match(css, /\.lab-row-meta\s*\{/);
  assert.match(css, /\.lab-row-created\s*\{/);
  assert.match(css, /\.lab-row-lineage\s*\{/);
});

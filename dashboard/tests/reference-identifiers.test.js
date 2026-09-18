const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const source = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'js', 'app.js'), 'utf8');
const catalogCss = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'css', 'catalog.css'), 'utf8');

test('reference cards use source-appropriate identifiers', () => {
  assert.match(source, /item\.kind==='repository'/);
  assert.match(source, /label:'GitHub',value:githubPath\(item\)/);
  assert.match(source, /label:'arXiv',value:item\.arxiv\|\|'—'/);
  assert.match(source, /new URL\(item\.url\)\.pathname/);
  assert.doesNotMatch(source, /arXiv:\$\{escapeHtml\(i\.arxiv\|\|'—'\)\}/);
});

test('reference viewer has one page and an explicit PDF action', () => {
  const matches = source.match(/async function reference\(/g) || [];
  assert.equal(matches.length, 1);
  assert.match(source, /Open PDF/);
  assert.match(source, /d\.has_pdf/);
  assert.match(source, /HeraldPdfViewer\.mount/);
  assert.match(source, /\/api\/references\/\$\{id\}\/bytes/);
  assert.match(source, /\/pdf-viewer\?id=/);
  assert.doesNotMatch(source, /view=FitH&navpanes=0/);
  assert.doesNotMatch(source, /<iframe title="\$\{escapeHtml\(i\.title\)\} PDF"/);
});

test('repository cards use repository language and iconography', () => {
  assert.match(source, /fa-brands fa-github/);
  assert.match(source, /githubPath\(item\)/);
  assert.doesNotMatch(source, /class="paper-action"/);
  assert.doesNotMatch(source, /class="lab-row-action"/);
  assert.match(catalogCss, /\.paper-meta \.paper-id\s*\{[\s\S]*overflow-wrap:\s*anywhere/);
});

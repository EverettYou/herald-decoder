const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const css = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'css', 'interface.css'), 'utf8');
const viewer = fs.readFileSync(path.join(__dirname, '..', 'frontend', 'js', 'repo-viewer.js'), 'utf8');

test('repository tree paths wrap rather than overflow their navigation pane', () => {
  assert.match(
    css,
    /\.repo-tree-folder summary,\.repo-tree-file\s*\{[\s\S]*white-space:\s*normal[\s\S]*overflow-wrap:\s*anywhere[\s\S]*word-break:\s*break-word/
  );
  assert.match(viewer, /class="repo-tree-name"/);
});

test('code files use the solid code icon rather than a missing regular glyph', () => {
  assert.match(viewer, /code: 'fa-solid fa-code'/);
  assert.doesNotMatch(viewer, /fa-regular fa-code/);
});

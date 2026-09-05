const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');

const source = fs.readFileSync(
  path.join(__dirname, '..', 'frontend', 'js', 'discussion-page.js'),
  'utf8',
);
const css = fs.readFileSync(
  path.join(__dirname, '..', 'frontend', 'css', 'interface.css'),
  'utf8',
);

test('discussion follows an issue-list, issue-detail, and new-issue flow', () => {
  assert.match(source, /class="issue-board"/);
  assert.match(source, /id="discussion-search"/);
  assert.match(source, /data-issue-filter="open"/);
  assert.match(source, /let status = 'open';/);
  assert.match(source, /No open research thread\./);
  assert.match(source, /class="issue-detail-layout"/);
  assert.match(source, /class="issue-timeline"/);
  assert.match(source, /id="issue-reply-form"/);
  assert.match(source, /id="new-issue-title"/);
  assert.match(source, /id="new-issue-body"/);
  assert.match(source, /Markdown and LaTeX math supported/);
  assert.match(source, /request\('\/api\/discussion\/threads', 'POST'/);
  assert.match(source, /related_labs:/);
  assert.match(css, /\.issue-row\[hidden\]\s*\{\s*display:\s*none;/);
});

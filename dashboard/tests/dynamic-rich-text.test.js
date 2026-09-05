const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const frontendRoot = path.join(__dirname, '..', 'frontend');
const app = fs.readFileSync(path.join(frontendRoot, 'js', 'app.js'), 'utf8');
const graph = fs.readFileSync(path.join(frontendRoot, 'js', 'graph.js'), 'utf8');
const labPage = fs.readFileSync(path.join(frontendRoot, 'js', 'lab-page.js'), 'utf8');
const discussionPage = fs.readFileSync(path.join(frontendRoot, 'js', 'discussion-page.js'), 'utf8');
const index = fs.readFileSync(path.join(frontendRoot, 'index.html'), 'utf8');
const style = fs.readFileSync(path.join(frontendRoot, 'css', 'style.css'), 'utf8');
const interfaceStyle = fs.readFileSync(path.join(frontendRoot, 'css', 'interface.css'), 'utf8');

[
  'markdown(p.homepage_intro)',
  'markdown(i.summary',
  'markdown(i.project_relevance',
  'markdown(p.preview)',
  'markdown(item.current_focus)',
  'markdown(item.next_action)',
  'markdown(p.content,{sourcePath:p.path})',
  'markdown(m.content)'
].forEach(pattern => assert.ok(app.includes(pattern), `Missing rich-text route: ${pattern}`));

[
  'markdown(lab.summary)',
  'markdown(lab.current_focus)',
  'markdown(lab.next_action)',
  'markdown(detail.question)',
  'markdown(detail.motivation)',
  'richInline(item)',
  'markdown(data.report.content, { sourcePath: data.report.path })',
  'markdown(source.content, { sourcePath: source.path })'
].forEach(pattern => assert.ok(labPage.includes(pattern), `Missing Lab rich-text route: ${pattern}`));

assert.ok(discussionPage.includes('markdown(message.content)'), 'Discussion messages must use the shared rich-text renderer');
assert.ok(index.includes('/js/document-page.js'), 'The project document viewer must load before the app router');

assert.ok(graph.includes('rich.block(node.summary)'), 'Graph summaries must use the shared rich-text renderer');
assert.ok(
  index.indexOf('/js/rich-text.js') < index.indexOf('/js/graph.js') &&
  index.indexOf('/js/rich-text.js') < index.indexOf('/js/lab-page.js') &&
  index.indexOf('/js/rich-text.js') < index.indexOf('/js/discussion-page.js') &&
  index.indexOf('/js/discussion-page.js') < index.indexOf('/js/app.js') &&
  index.indexOf('/js/lab-page.js') < index.indexOf('/js/app.js') &&
  index.indexOf('/js/rich-text.js') < index.indexOf('/js/app.js'),
  'The shared rich-text renderer must load before graph and app code'
);
assert.ok(!app.includes('function renderRichText'), 'Rich-text rendering must not be reimplemented inside app.js');
assert.doesNotMatch(app, /function document\s*\(/, 'Route handlers must not shadow the browser document object');
assert.doesNotMatch(app, /wikiStats\.after\(wikiOverview\)/, 'Wiki sections must retain their declared document order');
assert.ok(
  labPage.indexOf('id="lab-results"') < labPage.indexOf('id="lab-documents"') &&
  labPage.indexOf('id="lab-documents"') < labPage.indexOf('id="lab-record"'),
  'Lab information hierarchy must present Results, then Documents, then Research record'
);
assert.match(labPage, /data-lab-document="report" role="tab" aria-selected="true"/);
assert.match(labPage, /<details class="lab-record-group">\s*<summary><span>Resolved history/);
assert.match(labPage, /<aside class="lab-detail-rail"[\s\S]*DISCUSSION/);
[
  '/vendor/marked.umd.js',
  '/vendor/purify.min.js',
  '/vendor/katex/katex.min.js',
  '/vendor/katex/contrib/auto-render.min.js'
].forEach(asset => assert.ok(index.includes(asset), `Missing local rendering dependency: ${asset}`));
assert.doesNotMatch(index, /https:\/\/cdn\.jsdelivr\.net\/npm\/(marked|dompurify|katex)/);
assert.doesNotMatch(
  style,
  /\.lab-row-columns\s+span\s*\{[^}]*display\s*:\s*block/,
  'Lab catalog layout must not override the nested spans used by inline KaTeX'
);
assert.match(style, /\.lab-row-columns>div>b\{display:block/);
assert.match(interfaceStyle, /\.lab-document img\s*\{[^}]*max-width:\s*80%[^}]*height:\s*auto/);
assert.match(interfaceStyle, /\.document-panel > h2\s*\{[^}]*margin:\s*42px 0 16px[^}]*border-top/);
assert.match(interfaceStyle, /\.wiki-workspace\s*\{[^}]*align-items:\s*start/);
assert.match(interfaceStyle, /\.wiki-workspace > aside\s*\{[^}]*position:\s*static[^}]*max-height:\s*none[^}]*overflow:\s*visible/);
assert.doesNotMatch(interfaceStyle, /\.wiki-workspace #wiki-list,[\s\S]*max-height:\s*min\(760px, calc\(100vh - 255px\)\)[\s\S]*overflow-y:\s*auto/);
assert.doesNotMatch(interfaceStyle, /\.wiki-index-section\s*\{[^}]*max-height:[^}]*overflow-y:\s*auto/);
assert.doesNotMatch(interfaceStyle, /#wiki-list\s*\{[^}]*max-height:[^}]*overflow-y:\s*auto/);
assert.doesNotMatch(interfaceStyle, /\.wiki-context\s*\{[^}]*max-height:[^}]*overflow:\s*auto/);
assert.match(interfaceStyle, /\.wiki-landing-results\s*\{[^}]*max-height:[^}]*overflow-y:\s*auto/);

console.log('dynamic rich-text coverage passed');

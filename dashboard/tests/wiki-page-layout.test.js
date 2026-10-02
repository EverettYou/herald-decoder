const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const frontend = path.join(__dirname, '..', 'frontend');
const page = fs.readFileSync(path.join(frontend, 'js', 'wiki-page.js'), 'utf8');
const app = fs.readFileSync(path.join(frontend, 'js', 'app.js'), 'utf8');
const index = fs.readFileSync(path.join(frontend, 'index.html'), 'utf8');
const css = fs.readFileSync(path.join(frontend, 'css', 'interface.css'), 'utf8');

assert.ok(index.includes('/js/wiki-page.js'), 'Wiki reader module must be loaded');
assert.ok(index.indexOf('/js/wiki-page.js') < index.indexOf('/js/app.js'), 'Wiki reader must load before the router');
assert.match(app, /HeraldWikiPage\.render/);
assert.match(page, /id="wiki-page-search-results"/);
assert.doesNotMatch(page, /wiki-page-search-result-copy[\s\S]{0,180}<small>/);
assert.match(page, /class="document-panel wiki-page-document"/);
assert.match(page, />Types</);
assert.doesNotMatch(page, /Page context/);
assert.match(page, /Keywords/);
assert.doesNotMatch(page, /id="wiki-list"/);
assert.doesNotMatch(page, /id="wiki-context"/);
assert.doesNotMatch(page, /Linked from/);
assert.doesNotMatch(page, /source_refs/);
assert.match(css, /\.wiki-page-shell\s*\{[^}]*width:\s*min\(100%, 1120px\)/);
assert.match(css, /\.wiki-searchbar\.wiki-page-search\s*\{[^}]*display:\s*block[^}]*margin:\s*0 auto 24px/);
assert.match(css, /\.document-panel\.wiki-page-document\s*\{[^}]*padding:\s*0 0 54px/);
assert.match(css, /input\[type="search"\]::\-webkit-search-cancel-button\s*\{[^}]*appearance:\s*none/);
assert.match(css, /\.wiki-page-reading\s*\{[^}]*900px/);

console.log('wiki page single-column layout coverage passed');

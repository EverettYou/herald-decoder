const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

global.window = {};
require(path.join(__dirname, '..', 'frontend', 'js', 'rich-text.js'));

const { protectMath, restoreMathTokens, renderWikiLinks } = window.HeraldRichText.testing;
const markedModule = require(path.join(__dirname, '..', 'frontend', 'vendor', 'marked.umd.js'));
const marked = markedModule.marked || markedModule;
const katex = require(path.join(__dirname, '..', 'frontend', 'vendor', 'katex', 'katex.js'));
const sample = String.raw`Inline \(SU(2)\) and $p_m$.

\[
d_v=\sum_{e\ni v}x_e\in\{0,1,2,3\}.
\]

$$h_v^{\rm obs}=h_v^{\rm true}(1-\ell_v).$$`;
const protectedMath = protectMath(sample);

assert.equal(protectedMath.tokens.length, 4);
assert.doesNotMatch(protectedMath.source, /\\\[|\\\]|\\\(|\\\)|\$\$/);
assert.equal(restoreMathTokens(protectedMath.source, protectedMath.tokens), sample);

const parsed = marked.parse(protectedMath.source, { gfm: true });
const restored = restoreMathTokens(parsed, protectedMath.tokens);
assert.match(restored, /\\\(SU\(2\)\\\)/);
assert.match(restored, /\\\[\s*\n?d_v=/);
assert.match(katex.renderToString(String.raw`p_m\in[0,1/2]`, { throwOnError: true }), /class="katex"/);

const collision = protectMath('HERALDMATHPLACEHOLDER and \\(x\\)');
assert.equal(collision.tokens.length, 1);
assert.equal(restoreMathTokens(collision.source, collision.tokens), 'HERALDMATHPLACEHOLDER and \\(x\\)');

const wikiLinks = renderWikiLinks(
  '[[concepts/strong-to-weak-ssb|Strong-to-weak symmetry breaking]] and [[methods/side-information-aware-decoding]].'
);
assert.equal(
  wikiLinks,
  '[Strong-to-weak symmetry breaking](/wiki?page=concepts%2Fstrong-to-weak-ssb) and [methods/side-information-aware-decoding](/wiki?page=methods%2Fside-information-aware-decoding).'
);
assert.match(
  marked.parse(wikiLinks, { gfm: true }),
  /<a href="\/wiki\?page=concepts%2Fstrong-to-weak-ssb">Strong-to-weak symmetry breaking<\/a>/
);

const labOneReport = fs.readFileSync(
  path.join(__dirname, '..', '..', 'labs', 'lab-001-string-herald-visualization', 'REPORT.md'),
  'utf8'
);
assert.match(labOneReport, /figures\/seed1-herald-ablation\.svg/);
assert.match(labOneReport, /wiki\/overview\.md/);

function markdownFiles(root) {
  return fs.readdirSync(root, { withFileTypes: true }).flatMap((entry) => {
    const file = path.join(root, entry.name);
    if (entry.isDirectory()) return markdownFiles(file);
    return entry.isFile() && entry.name.endsWith('.md') && entry.name !== 'README.md' ? [file] : [];
  });
}

function removeDelimitedMath(source) {
  return source
    .replace(/\\\[[\s\S]*?\\\]/g, '')
    .replace(/\\\([\s\S]*?\\\)/g, '')
    .replace(/\$\$[\s\S]*?\$\$/g, '')
    .replace(/\$[^$\n]+\$/g, '');
}

function mathBody(math) {
  if (math.startsWith('$$')) return math.slice(2, -2);
  if (math.startsWith('\\[') || math.startsWith('\\(')) return math.slice(2, -2);
  return math.slice(1, -1);
}

const markdownRoots = [
  path.join(__dirname, '..', '..', 'wiki'),
  path.join(__dirname, '..', '..', 'labs'),
];
const malformedParentheticalMath = /\(\s*(?:\(|\\(?:tilde|lambda|oplus|sum|operatorname|mathrm|rm|mathbb|frac|tau|mid)|[A-Za-z]+(?:_[A-Za-z{]|\^[A-Za-z{]|=|>|<))/;
for (const file of markdownRoots.flatMap(markdownFiles)) {
  const source = fs.readFileSync(file, 'utf8');
  const unmarked = removeDelimitedMath(source);
  assert.doesNotMatch(unmarked, malformedParentheticalMath, `${file} contains unmarked mathematical notation`);
  assert.doesNotMatch(source, /\t/, `${file} contains a tab character, often a swallowed \\t command`);
  for (const { math } of protectMath(source).tokens) {
    const displayMode = math.startsWith('$$') || math.startsWith('\\[');
    assert.doesNotThrow(
      () => katex.renderToString(mathBody(math), { throwOnError: true, displayMode }),
      `${file} contains invalid LaTex: ${math}`
    );
  }
}

console.log('rich-text math protection passed');

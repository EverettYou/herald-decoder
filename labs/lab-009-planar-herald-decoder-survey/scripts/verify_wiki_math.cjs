const fs = require('node:fs');
const path = require('node:path');
const folder = path.resolve(__dirname, '..');
const root = path.resolve(folder, '../..');
global.window = {};
require(path.join(root, 'dashboard/frontend/js/rich-text.js'));
const katex = require(path.join(root, 'dashboard/frontend/vendor/katex/katex.js'));
const { protectMath } = window.HeraldRichText.testing;
function files(dir) {
  return fs.readdirSync(dir, {withFileTypes:true}).flatMap(entry => entry.isDirectory()
    ? files(path.join(dir,entry.name)) : entry.name.endsWith('.md') ? [path.join(dir,entry.name)] : []);
}
let count = 0;
for (const file of [path.join(folder,'REPORT.md'),...files(path.join(folder,'wiki'))]) {
  for (const { math } of protectMath(fs.readFileSync(file,'utf8')).tokens) {
    const width = math.startsWith('$') && !math.startsWith('$$') ? 1 : 2;
    katex.renderToString(math.slice(width,-width), {
      throwOnError:true, displayMode:math.startsWith('$$') || math.startsWith('\\[')
    });
    count++;
  }
}
const receipt = {status:'passed',scope:'Lab009 report and all local wiki pages',formulas:count};
fs.writeFileSync(path.join(folder,'results/wiki-math-validation.json'),JSON.stringify(receipt,null,2)+'\n');
console.log(JSON.stringify(receipt));

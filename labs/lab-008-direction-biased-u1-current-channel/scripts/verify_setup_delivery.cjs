/* Read-only dashboard/browser audit; writes only its local evidence and screenshots. */
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const crypto = require('crypto');
const { chromium } = require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB = path.resolve(__dirname, '..');
const ROOT = path.resolve(LAB, '../..');
const id = path.basename(LAB);
const base = 'http://127.0.0.1:8010';
const read = p => fs.readFileSync(p, 'utf8');
const sha = p => crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');

async function main() {
  const data = await (await fetch(base+'/api/labs/'+id)).json();
  const meta = JSON.parse(read(path.join(LAB,'lab.json')));
  for (const key of ['stage','summary','current_focus','next_action','parents']) assert.deepEqual(data.lab[key],meta[key],key);
  assert.equal(data.report.content,read(path.join(LAB,'REPORT.md')));
  assert.equal(data.plan.content,read(path.join(LAB,'PLAN.md')));
  assert.equal(data.outputs.filter(r=>r.id==='local-wiki').length,1);
  assert.equal(new Set(data.outputs.map(r=>r.id)).size,data.outputs.length);
  const prior = await (await fetch(base+'/api/labs/lab-007-decoding-statistical-mechanics/wiki?page=index')).json();
  assert(!prior.pages.includes('biased-u1-feasibility'));
  assert(prior.content.includes(id));
  const checks=JSON.parse(read(path.join(LAB,'results/sector-prediction-audit-2026-09-18.json')));
  assert.equal(checks.status,'passed');
  for(const [p,hash] of Object.entries(checks.source_sha256)) assert.equal(sha(path.join(ROOT,p)),hash,p);
  const shots = path.join(ROOT,'.tmp/lab008-delivery');
  fs.mkdirSync(shots,{recursive:true});
  const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
  const page=await browser.newPage({viewport:{width:1500,height:1050}});
  const errors=[];
  page.on('pageerror',e=>errors.push(String(e)));
  const rendered=[];
  try {
    const surfaces=[
      ['report','/lab?id='+id,'#lab-document','REPORT.md'],
      ...['index','direction-biased-u1-current-channel','sector-predictions','numerical-evidence'].map(name=>
        [name,'/lab-wiki?lab='+id+'&page='+name,'#local-wiki-document','wiki/'+name+'.md'])
    ];
    for(const [name,url,selector,file] of surfaces) {
      if(name!=='report') {
        const wiki=await(await fetch(base+'/api/labs/'+id+'/wiki?page='+name)).json();
        assert.equal(wiki.content,read(path.join(LAB,file)));
      }
      await page.goto(base+url);
      await page.waitForSelector(selector+' h1');
      await page.evaluate(()=>document.fonts.ready);
      const doc=page.locator(selector);
      const body=await doc.innerText();
      assert(!body.includes('Dashboard error'));
      assert.equal(await doc.locator('.katex-error').count(),0,name);
      if(['report','sector-predictions','direction-biased-u1-current-channel'].includes(name)) assert((await doc.locator('.katex').count())>0,name);
      if(name==='report') {assert(body.includes('L008.10'));assert(body.includes('171'));}
      if(name==='direction-biased-u1-current-channel') assert(!/feasibility/i.test(await doc.locator('h1').last().innerText()));
      const links=await doc.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
      for(const href of links) assert.equal((await page.request.get(base+href)).status(),200,href);
      const overflow=await doc.locator('.katex-display').evaluateAll(nodes=>nodes.map((n,i)=>({i,width:n.clientWidth,scroll:n.scrollWidth})).filter(x=>x.scroll>x.width+2));
      await page.screenshot({path:path.join(shots,name+'.png'),fullPage:true});
      rendered.push({name,url:base+url,source_sha256:sha(path.join(LAB,file)),local_links:links.length,display_equations:await doc.locator('.katex-display').count(),overflow});
    }
    assert.deepEqual(errors,[]);
  } finally { await browser.close(); }
  const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),
    current_inputs_verified:true,report_and_note_source_agreement:true,active_registry_verified:true,
    no_old_note_in_lab007:true,lab_stage:meta.stage,parents:meta.parents,rendered,
    screenshot_directory:path.relative(ROOT,shots),page_errors:errors,
    limits:['Setup and bounded checks only; no new LER production or transition inference.']};
  fs.writeFileSync(path.join(LAB,'results/setup-delivery-2026-09-18.json'),JSON.stringify(out,null,2)+'\n');
  console.log(JSON.stringify(out,null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

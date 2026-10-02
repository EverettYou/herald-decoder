const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const d=await get('/api/labs/'+id),meta=JSON.parse(read(path.join(LAB,'lab.json')));
 for(const k of ['stage','current_focus','next_action'])assert.equal(d.lab[k],meta[k]);
 assert.equal(d.report.content,read(path.join(LAB,'REPORT.md')));assert.equal(d.plan.content,read(path.join(LAB,'PLAN.md')));
 assert.equal(meta.stage,'active');assert.equal(d.outputs.filter(x=>x.kind==='figure').length,3);
 const numeric=JSON.parse(read(path.join(LAB,'results/analytic-partition-bridge-2026-09-18.json')));assert.equal(numeric.status,'passed');
 for(const [p,h] of Object.entries(numeric.source_sha256))assert.equal(sha(path.join(ROOT,p)),h);
 const shots=path.join(ROOT,'.tmp/lab008-analytic-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
  for(const [name,file,kind] of [['report','REPORT.md','report'],['analytic-wiki','wiki/partition-function-ler.md','wiki'],
      ['current-user-document','wiki/sector-predictions.md','document'],['analytic-document','wiki/partition-function-ler.md','document']]){
   const repo='labs/'+id+'/'+file;
   const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page=partition-function-ler':'/document?path='+encodeURIComponent(repo);
   if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
   if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page=partition-function-ler')).content,read(path.join(LAB,file)));
   await page.goto(base+url);
   const selector=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
   await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
   const doc=page.locator(selector);assert.equal(await doc.locator('.katex-error').count(),0,name);
   const over=await doc.locator('.katex-display').evaluateAll(ns=>ns.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent));assert.deepEqual(over,[],name);
   const text=await doc.innerText();assert(text.includes(kind==='report'?'7.5 p^2':kind==='document'&&name==='current-user-document'?'Current priority':'Leading coefficients'));
   const links=await doc.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
   for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
   await page.screenshot({path:path.join(shots,name+'.png'),fullPage:true});
   if(name==='analytic-document'){
     await doc.locator('h3').filter({hasText:'Leading coefficients'}).scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(shots,'leading-coefficients.png')});
   }
   surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/partition-function-ler.md','wiki/sector-predictions.md','wiki/index.md',
 'scripts/check_analytic_partition_bridge.py','results/analytic-partition-bridge-2026-09-18.json','manifests/analytic-partition-bridge-2026-09-18.json'];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(p=>[p,sha(path.join(LAB,p))])),screenshots:path.relative(ROOT,shots),
  scope:'Analytic K projection, exact path and low-p square theorem. Moderate-p full curve remains open; lab active.'};
 fs.writeFileSync(path.join(LAB,'results/analytic-delivery-2026-09-18.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,surfaces:surfaces.map(x=>x.name),screenshots:out.screenshots},null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

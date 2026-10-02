const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const d=await get('/api/labs/'+id),meta=JSON.parse(read(path.join(LAB,'lab.json')));
 for(const k of ['stage','current_focus','next_action'])assert.equal(d.lab[k],meta[k]);
 const registry=JSON.parse(read(path.join(ROOT,'labs/labs.json'))).labs.find(x=>x.id===id);
 for(const k of ['stage','current_focus','next_action'])assert.equal(registry[k],meta[k]);
 assert.equal(d.report.content,read(path.join(LAB,'REPORT.md')));assert.equal(d.plan.content,read(path.join(LAB,'PLAN.md')));
 assert.equal(meta.stage,'active');assert.equal(d.outputs.filter(x=>x.kind==='figure').length,3);
 const numeric=JSON.parse(read(path.join(LAB,'results/replica-boundary-theory-2026-09-18.json')));
 assert.equal(numeric.status,'passed');
 for(const [p,h] of Object.entries(numeric.source_sha256))assert.equal(sha(path.join(ROOT,p)),h);
 const shots=path.join(ROOT,'.tmp/lab008-replica-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
  for(const [name,file,kind,expected] of [
    ['report','REPORT.md','report','Replica boundary observable'],
    ['replica-wiki','wiki/replica-boundary-ratios.md','wiki','Reconstructing the full LER'],
    ['cft-wiki','wiki/complex-weights-and-cft.md','wiki','Solving a candidate Gaussian replica annulus'],
    ['current-user-document','wiki/sector-predictions.md','document','physical replica limit'],
    ['replica-document','wiki/replica-boundary-ratios.md','document','Reconstructing the full LER'],
    ['cft-document','wiki/complex-weights-and-cft.md','document','0.36766']]){
   const repo='labs/'+id+'/'+file,slug=path.basename(file,'.md');
   const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page='+slug:'/document?path='+encodeURIComponent(repo);
   if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
   if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page='+slug)).content,read(path.join(LAB,file)));
   await page.goto(base+url);
   const selector=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
   await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
   const doc=page.locator(selector);assert.equal(await doc.locator('.katex-error').count(),0,name);
   const over=await doc.locator('.katex-display').evaluateAll(ns=>ns.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent));
   assert.deepEqual(over,[],name);
   const text=await doc.innerText();assert(text.includes(expected),name);
   if(name==='cft-document')assert(text.includes('not a prediction yet for the Lab 006 open square'));
   const links=await doc.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
   for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
   await page.screenshot({path:path.join(shots,name+'.png'),fullPage:true});
   if(name==='replica-document'){
     await doc.locator('h3').filter({hasText:'A rigorous order parameter'}).scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(shots,'physical-moment-bound.png')});
   }
   if(name==='cft-document'){
     await doc.locator('h3').filter({hasText:'Solving a candidate Gaussian replica annulus'}).scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(shots,'gaussian-ratio.png')});
     await doc.locator('p').filter({hasText:'Combining this candidate'}).scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(shots,'conditional-interpretation.png')});
   }
   surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/partition-function-ler.md','wiki/sector-predictions.md','wiki/index.md',
 'wiki/replica-boundary-ratios.md','wiki/complex-weights-and-cft.md','scripts/check_replica_boundary_theory.py',
 'results/replica-boundary-theory-2026-09-18.json','manifests/replica-boundary-theory-2026-09-18.json'];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(p=>[p,sha(path.join(LAB,p))])),screenshots:path.relative(ROOT,shots),
  scope:'Exact physical replica identities and path bounds; conditional Gaussian replica calculation. No physical 2D critical point or CFT identified.'};
 fs.writeFileSync(path.join(LAB,'results/replica-delivery-2026-09-18.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,surfaces:surfaces.map(x=>x.name),screenshots:out.screenshots},null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

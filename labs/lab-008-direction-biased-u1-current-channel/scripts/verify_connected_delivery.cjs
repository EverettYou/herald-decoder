const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const d=await get('/api/labs/'+id),meta=JSON.parse(read(path.join(LAB,'lab.json')));
 const registry=JSON.parse(read(path.join(ROOT,'labs/labs.json'))).labs.find(x=>x.id===id);
 for(const k of ['stage','current_focus','next_action']){
  assert.equal(d.lab[k],meta[k]);assert.equal(registry[k],meta[k]);
 }
 assert.equal(d.report.content,read(path.join(LAB,'REPORT.md')));
 assert.equal(d.plan.content,read(path.join(LAB,'PLAN.md')));
 assert.equal(meta.stage,'active');assert.equal(d.outputs.filter(x=>x.kind==='figure').length,4);
 const numeric=JSON.parse(read(path.join(LAB,'results/connected-current-defects-2026-09-19.json')));
 assert.equal(numeric.status,'passed');assert.equal(numeric.exact_directed_L3.status,'certified');
 for(const g of numeric.exact_gates)for(const row of g.cells)assert.equal(row.missing_witnesses,0);
 for(const [p,h] of Object.entries(numeric.source_sha256))assert.equal(sha(path.join(ROOT,p)),h);
 const overlap=JSON.parse(read(path.join(LAB,'results/connected-defect-overlap-2026-09-19.json')));
 assert.equal(overlap.status,'passed_promoted');assert.equal(overlap.exact_l3_gate.pair_cell_checks,765);
 assert.equal(overlap.exact_l3_gate.max_absolute_error,0);assert.equal(overlap.L5.intersection_evaluations,3488);
 assert(overlap.L5.cells.every(x=>x.tree_bound<x.path_sum));
 assert.equal(overlap.L5.cells.filter(x=>x.improves_strongest_certified_upper).length,2);
 for(const [p,h] of Object.entries(overlap.source_sha256))assert.equal(sha(path.join(ROOT,p)),h);
 for(const file of ['witness-union-floor-2026-09-19.json','directional-crossover-2026-09-19.json']){
   const result=JSON.parse(read(path.join(LAB,'results',file)));assert.equal(result.status,'passed');
   for(const [p,h] of Object.entries(result.source_sha256))assert.equal(sha(path.join(ROOT,p)),h);
   if(file.startsWith('directional'))assert.equal(result.critical_coefficient_checks,15);
   else assert(result.L5.find(x=>x.p===.3&&x.q===.5).witness_union_floor>.5);
 }
 const shots=path.join(ROOT,'.tmp/lab008-connected-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
  for(const [name,file,kind,expected] of [
    ['report','REPORT.md','report','Connected defects: new rigorous calculation'],
    ['connected-wiki','wiki/connected-current-defects.md','wiki','Exact overlap correction'],
    ['connected-document','wiki/connected-current-defects.md','document','positive bivariate current-count polynomial'],
    ['crossover-document','wiki/directional-crossover.md','document','The complete boundary-layer coefficient'],
    ['crossover-wiki','wiki/directional-crossover.md','wiki','The complete boundary-layer coefficient'],
    ['current-user-document','wiki/complex-weights-and-cft.md','document','Which statistical model answers the original question?'],
    ['sector-document','wiki/sector-predictions.md','document','connected-current calculation']]){
   const repo='labs/'+id+'/'+file,slug=path.basename(file,'.md');
   const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page='+slug:'/document?path='+encodeURIComponent(repo);
   if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
   if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page='+slug)).content,read(path.join(LAB,file)));
   await page.goto(base+url);
   const selector=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
   await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
   const doc=page.locator(selector);assert.equal(await doc.locator('.katex-error').count(),0,name);
   const over=await doc.locator('.katex-display').evaluateAll(ns=>ns.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent));
   assert.deepEqual(over,[],name);assert((await doc.innerText()).includes(expected),name);
   const links=await doc.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
   for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
   if(kind==='report'){
     const images=doc.locator('img');assert.equal(await images.count(),4);
     assert(await images.evaluateAll(ns=>ns.every(n=>n.complete&&n.naturalWidth>0)));
   }
   await page.screenshot({path:path.join(shots,name+'.png')});
   if(name==='crossover-document'){
     for(const [title,shot] of [['Exact exponent along a biased approach','crossover-exponent'],['The complete boundary-layer coefficient','crossover-coefficient'],['Recovering the directed coefficient','crossover-limit']]){
       await doc.locator('h3').filter({hasText:title}).evaluate(el=>el.scrollIntoView({block:'start'}));
       await page.screenshot({path:path.join(shots,shot+'.png')});
     }
   }
   if(name==='current-user-document'){
     await doc.locator('h3').filter({hasText:'Which statistical model answers the original question?'}).evaluate(el=>el.scrollIntoView({block:'start'}));
     await page.screenshot({path:path.join(shots,'model-and-ler.png')});
   }
   if(name==='connected-document'){
     for(const [title,shot] of [['A rigorous floor on the witness envelope','witness-floor'],['Exact overlap correction','exact-overlap'],['An exact two-dimensional patch curve','exact-curve'],['Honeycomb theorem','honeycomb-theorem'],['Finite square certificates','finite-certificates']]){
       await doc.locator('h3').filter({hasText:title}).scrollIntoViewIfNeeded();
       await page.screenshot({path:path.join(shots,shot+'.png')});
     }
     await doc.locator('p').filter({hasText:'perfect interior integer-charge observations'}).scrollIntoViewIfNeeded();
     await page.screenshot({path:path.join(shots,'honeycomb-conclusion.png')});
   }
   surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/connected-current-defects.md','wiki/complex-weights-and-cft.md',
 'wiki/partition-function-ler.md','wiki/sector-predictions.md','wiki/theory-boundary-synthesis.md','wiki/index.md',
 'scripts/check_connected_current_defects.py','results/connected-current-defects-2026-09-19.json',
 'scripts/check_connected_defect_overlap.py','results/connected-defect-overlap-2026-09-19.json',
 'manifests/connected-current-defects-2026-09-19.json','manifests/connected-defect-overlap-2026-09-19.json',
 'wiki/directional-crossover.md','scripts/check_witness_union_floor.py','scripts/check_directional_crossover.py',
 'results/witness-union-floor-2026-09-19.json','results/directional-crossover-2026-09-19.json',
 'manifests/witness-union-floor-2026-09-19.json','manifests/directional-crossover-2026-09-19.json',
 'manifests/reverse-sector-response-2026-09-19.json','scripts/verify_connected_delivery.cjs'];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(p=>[p,sha(path.join(LAB,p))])),screenshots:path.relative(ROOT,shots),
  scope:'Exact directional crossover exponents and boundary-layer coefficients; witness-envelope obstruction; preceding finite bounds and directed-honeycomb theorem retained. No moderate-p square curve or physical CFT identified. Fixed-p reverse-sector response is registered and not yet run.'};
 fs.writeFileSync(path.join(LAB,'results/connected-current-delivery-2026-09-19.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,surfaces:surfaces.map(x=>x.name),screenshots:out.screenshots},null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

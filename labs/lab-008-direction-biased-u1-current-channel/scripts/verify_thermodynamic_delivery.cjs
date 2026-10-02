const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const api=await get('/api/labs/'+id),meta=JSON.parse(read(path.join(LAB,'lab.json')));
 const registry=JSON.parse(read(path.join(ROOT,'labs/labs.json'))).labs.find(x=>x.id===id);
 for(const k of ['stage','current_focus','next_action']){assert.equal(api.lab[k],meta[k]);assert.equal(registry[k],meta[k]);}
 assert.equal(meta.stage,'active');
 assert.equal(api.report.content,read(path.join(LAB,'REPORT.md')));assert.equal(api.plan.content,read(path.join(LAB,'PLAN.md')));
 assert.equal(meta.results.filter(x=>x.id==='thermodynamic-limits').length,1);
 const result=JSON.parse(read(path.join(LAB,'results/thermodynamic-limits-2026-09-20.json')));
 assert.equal(result.status,'passed');assert.equal(result.finite.cells.length,28);
 assert.equal(result.new_physical_record_samples,0);assert.equal(result.finite.missing_binary_witnesses,0);
 for(const [file,h] of Object.entries(result.source_sha256))assert.equal(sha(path.join(ROOT,file)),h,file);
 const shots=path.join(ROOT,'.tmp/lab008-thermodynamic-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
  for(const [name,file,kind,expected] of [
   ['report','REPORT.md','report','Thermodynamic correctability and free energy'],
   ['thermodynamic-wiki','wiki/thermodynamic-limits.md','wiki','An open all-p correctable interval on honeycomb'],
   ['thermodynamic-document','wiki/thermodynamic-limits.md','document','What bulk free-energy limit can actually be proved?'],
   ['current-user-document','wiki/complex-weights-and-cft.md','document','Thermodynamic result, 2026-09-20']]){
    const repo='labs/'+id+'/'+file,slug=path.basename(file,'.md');
    const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page='+slug:'/document?path='+encodeURIComponent(repo);
    if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
    if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page='+slug)).content,read(path.join(LAB,file)));
    await page.goto(base+url);
    const selector=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
    await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
    const doc=page.locator(selector);assert((await doc.innerText()).includes(expected));
    assert.equal(await doc.locator('.katex-error').count(),0,name);
    assert.deepEqual(await doc.locator('.katex-display').evaluateAll(ns=>ns.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent)),[],name);
    const links=await doc.locator('a[href]').evaluateAll(ns=>ns.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
    for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
    if(kind==='report')assert(await doc.locator('img').evaluateAll(ns=>ns.every(n=>n.complete&&n.naturalWidth>0)));
    await page.screenshot({path:path.join(shots,name+'.png')});
    if(name==='report'){
      await doc.locator('h3').filter({hasText:'L008.21 Thermodynamic correctability and free energy'}).evaluate(el=>el.scrollIntoView({block:'start'}));
      await page.screenshot({path:path.join(shots,'report-theorem.png')});
    }
    if(name==='thermodynamic-document')for(const [title,shot] of [
      ['An open all-p correctable interval on honeycomb','honeycomb-window'],
      ['A precise thermodynamic order parameter','gap-criterion'],
      ['What bulk free-energy limit can actually be proved?','bulk-density']]){
       await doc.locator('h3').filter({hasText:title}).evaluate(el=>el.scrollIntoView({block:'start'}));
       await page.screenshot({path:path.join(shots,shot+'.png')});
      }
    surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/index.md','wiki/thermodynamic-limits.md','wiki/complex-weights-and-cft.md',
 'scripts/check_thermodynamic_limits.py','scripts/verify_thermodynamic_delivery.cjs','results/thermodynamic-limits-2026-09-20.json',
 'manifests/thermodynamic-limits-2026-09-20.json','manifests/square-midpoint-thermodynamics-2026-09-20.json'];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(f=>[f,sha(path.join(LAB,f))])),screenshots:path.relative(ROOT,shots),
  scope:'Sufficient thermodynamic correctability, robust all-p honeycomb window, gap/entropy characterization and averaged bulk-density existence. No general square criticality or physical CFT claimed.'};
 fs.writeFileSync(path.join(LAB,'results/thermodynamic-limits-delivery-2026-09-20.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,surfaces:surfaces.map(x=>x.name),screenshots:out.screenshots}));
}
main().catch(e=>{console.error(e);process.exit(1);});

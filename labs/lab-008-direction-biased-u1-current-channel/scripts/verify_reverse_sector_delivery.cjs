const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB),base='http://127.0.0.1:8010';
const read=p=>fs.readFileSync(p,'utf8'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
async function get(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}
async function main(){
 const api=await get('/api/labs/'+id),meta=JSON.parse(read(path.join(LAB,'lab.json')));
 const registry=JSON.parse(read(path.join(ROOT,'labs/labs.json'))).labs.find(x=>x.id===id);
 for(const key of ['stage','current_focus','next_action']){assert.equal(api.lab[key],meta[key]);assert.equal(registry[key],meta[key]);}
 assert.equal(api.report.content,read(path.join(LAB,'REPORT.md')));
 assert.equal(api.plan.content,read(path.join(LAB,'PLAN.md')));
 const result=JSON.parse(read(path.join(LAB,'results/reverse-sector-response-2026-09-19.json')));
 const manifest=JSON.parse(read(path.join(LAB,'manifests/reverse-sector-response-2026-09-19.json')));
 assert.equal(result.status,'passed');assert.equal(manifest.status,'passed');
 assert.equal(result.proof_checks.full_support_cells,15);
 assert.equal(result.proof_checks.all_LER_errors_within_exact_TV,true);
 assert.equal(result.proof_checks.all_exact_TV_within_quadratic_bound,true);
 assert.equal(result.new_physical_record_samples,0);
 assert.equal(manifest.completion.L5_response_LER_evaluated,false);
 for(const [file,hash] of Object.entries(result.source_sha256))assert.equal(sha(path.join(ROOT,file)),hash,file);
 const shots=path.join(ROOT,'.tmp/lab008-reverse-sector-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],surfaces=[];
 page.on('pageerror',error=>errors.push(String(error)));
 try{
  for(const [name,file,kind,expected] of [
   ['report','REPORT.md','report','Normalized fixed-p response'],
   ['response-wiki','wiki/reverse-sector-response.md','wiki','Exact uniform error certificate'],
   ['response-document','wiki/reverse-sector-response.md','document','Full-support L3 validation'],
   ['current-user-document','wiki/complex-weights-and-cft.md','document','Fixed-p reverse response']]){
    const repo='labs/'+id+'/'+file,slug=path.basename(file,'.md');
    const url=kind==='report'?'/lab?id='+id:kind==='wiki'?'/lab-wiki?lab='+id+'&page='+slug:'/document?path='+encodeURIComponent(repo);
    if(kind==='document')assert.equal((await get('/api/documents/file?path='+encodeURIComponent(repo))).content,read(path.join(LAB,file)));
    if(kind==='wiki')assert.equal((await get('/api/labs/'+id+'/wiki?page='+slug)).content,read(path.join(LAB,file)));
    await page.goto(base+url);
    const selector=kind==='report'?'#lab-document':kind==='wiki'?'#local-wiki-document':'.project-document-preview';
    await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
    const doc=page.locator(selector);assert.equal(await doc.locator('.katex-error').count(),0,name);
    const overflow=await doc.locator('.katex-display').evaluateAll(nodes=>nodes.filter(n=>n.scrollWidth>n.clientWidth+2).map(n=>n.textContent));
    assert.deepEqual(overflow,[],name);assert((await doc.innerText()).includes(expected),name);
    const links=await doc.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
    for(const link of links)assert.equal((await page.request.get(base+link)).status(),200,link);
    await page.screenshot({path:path.join(shots,name+'.png')});
    if(name==='response-document'){
      for(const [title,shot] of [['A normalized joint-law expansion','joint-law'],['Exact uniform error certificate','error-bound'],['Full-support L3 validation','l3-validation']]){
        await doc.locator('h3').filter({hasText:title}).scrollIntoViewIfNeeded();
        await page.screenshot({path:path.join(shots,shot+'.png')});
      }
    }
    surfaces.push({name,url:base+url,file,sha256:sha(path.join(LAB,file)),local_links:links.length});
  }
  assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['PLAN.md','REPORT.md','lab.json','wiki/index.md','wiki/directional-crossover.md','wiki/reverse-sector-response.md',
 'wiki/complex-weights-and-cft.md','scripts/check_reverse_sector_response.py','results/reverse-sector-response-2026-09-19.json',
 'manifests/reverse-sector-response-2026-09-19.json','scripts/verify_reverse_sector_delivery.cjs'];
 const output={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),surfaces,page_errors:errors,
  file_sha256:Object.fromEntries(files.map(file=>[file,sha(path.join(LAB,file))])),screenshots:path.relative(ROOT,shots),
  scope:'Normalized fixed-p reverse-sector response, exact TV/LER certificate and full-support L3 validation. No L5 response LER, threshold, fit or CFT claim.'};
 fs.writeFileSync(path.join(LAB,'results/reverse-sector-response-delivery-2026-09-19.json'),JSON.stringify(output,null,2)+'\n');
 console.log(JSON.stringify({status:output.status,surfaces:surfaces.map(x=>x.name),screenshots:output.screenshots},null,2));
}
main().catch(error=>{console.error(error);process.exit(1);});

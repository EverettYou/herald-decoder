/* Read-only local dashboard audit of the finite-mechanism research delivery. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto');
const {chromium}=require('/Users/home/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const LAB=path.resolve(__dirname,'..'),ROOT=path.resolve(LAB,'../..'),id=path.basename(LAB);
const base='http://127.0.0.1:8010',read=p=>fs.readFileSync(p,'utf8');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex'),sha=p=>hash(fs.readFileSync(p));
async function json(url){const r=await fetch(base+url);assert.equal(r.status,200,url);return r.json();}

async function main(){
 const meta=JSON.parse(read(path.join(LAB,'lab.json'))),data=await json('/api/labs/'+id);
 for(const k of ['stage','summary','current_focus','next_action','parents'])assert.deepEqual(data.lab[k],meta[k],k);
 assert.equal(data.report.content,read(path.join(LAB,'REPORT.md')));
 assert.equal(data.plan.content,read(path.join(LAB,'PLAN.md')));
 const scientific=JSON.parse(read(path.join(LAB,'results/scientific-integrity-2026-09-18.json')));
 assert.equal(scientific.status,'passed');assert.equal(scientific.production_records,10944);
 for(const [p,h] of Object.entries(scientific.input_sha256))assert.equal(sha(path.join(ROOT,p)),h,p);
 for(const [p,h] of Object.entries(scientific.source_sha256))assert.equal(sha(path.join(ROOT,p)),h,p);
 const figures=meta.results.filter(x=>x.presentation==='result');assert.equal(figures.length,3);
 assert.deepEqual(data.outputs.map(x=>x.id).sort(),['local-wiki',...figures.map(x=>x.id)].sort());
 for(const f of figures){
   const output=data.outputs.find(x=>x.id===f.id);assert.equal(output.asset_path,f.path);assert.equal(output.title,f.title);
   assert(data.report.content.includes(']('+f.path+')'),f.path);
 }
 const shots=path.join(ROOT,'.tmp/lab008-research-delivery');fs.mkdirSync(shots,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'});
 const page=await browser.newPage({viewport:{width:1500,height:1050}}),errors=[],rendered=[];
 page.on('pageerror',e=>errors.push(String(e)));
 try{
   const surfaces=[['report','/lab?id='+id,'#lab-document','REPORT.md'],
     ...['index','direction-biased-u1-current-channel','sector-predictions','numerical-evidence','mechanism-results'].map(n=>
      [n,'/lab-wiki?lab='+id+'&page='+n,'#local-wiki-document','wiki/'+n+'.md'])];
   for(const [name,url,selector,file] of surfaces){
     if(name!=='report'){const wiki=await json('/api/labs/'+id+'/wiki?page='+name);assert.equal(wiki.content,read(path.join(LAB,file)));}
     await page.goto(base+url);await page.waitForSelector(selector+' h1');await page.evaluate(()=>document.fonts.ready);
     await page.waitForFunction(sel=>Array.from(document.querySelectorAll(sel+' img')).every(n=>n.complete&&n.naturalWidth>0),selector);
     const doc=page.locator(selector),body=await doc.innerText();assert(!body.includes('Dashboard error'));
     assert.equal(await doc.locator('.katex-error').count(),0,name);
     if(name==='report'){assert(body.includes('10,944'));assert(body.includes('L008.13'));assert.equal(await doc.locator('img').count(),3);}
     const images=await doc.locator('img').evaluateAll(nodes=>nodes.map(n=>({url:n.src,alt:n.alt,width:n.naturalWidth})));
     for(const im of images){
       const f=figures.find(x=>im.url.endsWith('/'+x.path));assert(f,im.url);
       const r=await page.request.get(im.url);assert.equal(r.status(),200);assert.equal(hash(await r.body()),sha(path.join(LAB,f.path)));
     }
     const links=await doc.locator('a[href]').evaluateAll(nodes=>nodes.map(n=>n.getAttribute('href')).filter(x=>x.startsWith('/')));
     for(const href of links)assert.equal((await page.request.get(base+href)).status(),200,href);
     const overflow=await doc.locator('.katex-display').evaluateAll(nodes=>nodes.map((n,i)=>({i,width:n.clientWidth,scroll:n.scrollWidth})).filter(x=>x.scroll>x.width+2));
     assert.deepEqual(overflow,[],name+' formula overflow');
     await page.screenshot({path:path.join(shots,name+'.png'),fullPage:true});
     if(name==='report'){
       await doc.screenshot({path:path.join(shots,'report-document.png')});
       await page.locator('.research-results-list').count();
       await page.locator('[data-lab-document="plan"]').click();
       assert((await doc.innerText()).includes('Execution record'));
     }
     rendered.push({name,url:base+url,file,source_sha256:sha(path.join(LAB,file)),images,links_checked:links.length,formula_overflow:overflow});
   }
   for(const f of figures){
     const url=base+'/lab-result?lab='+id+'&result='+f.id;
     await page.goto(url);await page.waitForSelector('#result-content img');
     await page.waitForFunction(()=>{const n=document.querySelector('#result-content img');return n?.complete&&n.naturalWidth>0;});
     assert.equal(await page.locator('.result-page-heading h1').innerText(),f.title);
     await page.screenshot({path:path.join(shots,f.id+'.png'),fullPage:true});
     rendered.push({name:f.id,url,asset_sha256:sha(path.join(LAB,f.path))});
   }
   assert.deepEqual(errors,[]);
 }finally{await browser.close();}
 const files=['REPORT.md','PLAN.md','lab.json','results/scientific-integrity-2026-09-18.json',
   'scripts/render_mechanism.py','scripts/render_extension.py','results/square-mechanism-2026-09-18-analysis.json',
   'results/honeycomb-arrow-control-2026-09-18-analysis.json','results/size-bias-distributions-2026-09-18.json',...figures.map(x=>x.path)];
 const out={status:'browser_verified_pending_visual_review',updated:new Date().toISOString(),
   current_inputs_verified:true,regenerated_figure_bytes_verified:true,report_source_agreement:true,
   active_registry_verified:true,exact_promoted_figure_count:3,lab_stage:meta.stage,
   file_sha256:Object.fromEntries(files.map(p=>[p,sha(path.join(LAB,p))])),rendered,
   screenshot_directory:path.relative(ROOT,shots),page_errors:errors,
   limits:['Finite-mechanism evidence only; thermodynamic phase class remains unresolved.']};
 fs.writeFileSync(path.join(LAB,'results/research-delivery-2026-09-18.json'),JSON.stringify(out,null,2)+'\n');
 console.log(JSON.stringify({status:out.status,lab_stage:meta.stage,rendered:rendered.map(x=>x.name),screenshots:out.screenshot_directory},null,2));
}
main().catch(e=>{console.error(e);process.exit(1);});

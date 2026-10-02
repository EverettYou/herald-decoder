/* Render the actual local dashboard. Requires Playwright and local Chrome.
 * Does not acquire benchmark data or change the research registry. */
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const folder = path.resolve(__dirname, '..');
const root = path.resolve(folder, '../..');
const lab = path.basename(folder);
const base = process.env.LAB009_DASHBOARD_URL || 'http://127.0.0.1:8010';
const sha = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const read = name => JSON.parse(fs.readFileSync(path.join(folder, name), 'utf8'));

(async () => {
  const receipt = { status: 'running', verified_at: new Date().toISOString(), base_url: base,
    report: {}, figures: [], wiki: [], documents: [], workbench: [], browser_errors: [] };
  const figures = read('results/figure-provenance.json');
  for (const [name, digest] of Object.entries({...figures.input_sha256, ...figures.output_sha256})) {
    assert.equal(sha(path.join(folder, name)), digest, `changed figure input/output: ${name}`);
  }
  receipt.figure_hashes = { inputs: Object.keys(figures.input_sha256).length,
    outputs: Object.keys(figures.output_sha256).length, all_match: true };
  const shots = read('results/survey-analysis.json');
  assert.equal(shots.status, 'passed');
  assert.ok(Object.keys(shots.current_source_sha256).length >= 10);
  for (const [name, digest] of Object.entries(shots.current_source_sha256)) {
    assert.equal(sha(path.join(root, name)), digest, `changed decoder source: ${name}`);
  }
  for (const row of read('results/data-provenance.json').records) {
    assert.equal(sha(path.join(folder, row.snapshot)),row.sha256,`changed inherited snapshot: ${row.snapshot}`);
  }
  receipt.scientific_vector_audit = 'results/survey-analysis.json';
  const qa = path.join(folder, 'results/verification');
  fs.mkdirSync(qa, { recursive: true });
  const browser = await chromium.launch({
    executablePath: process.env.LAB009_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
  page.on('pageerror', e => receipt.browser_errors.push(String(e)));
  async function visit(url, selector) {
    const response = await page.goto(base + url);
    assert.equal(response.status(), 200, url);
    await page.locator(selector).waitFor({timeout: 30000});
    assert.equal(await page.getByText('Dashboard error', {exact: true}).count(), 0);
  }
  async function json(url) {
    const response = await page.request.get(base + url);
    assert.equal(response.status(), 200, url);
    return response.json();
  }
  const payload = await json(`/api/labs/${lab}`);
  const expected = [...figures.figures.map(f=>f.id), 'decoder-workbench', 'survey-summary', 'local-wiki'].sort();
  assert.deepEqual(payload.outputs.map(o=>o.id).sort(), expected, 'active result registry');
  await visit(`/lab?id=${lab}`, '#lab-document');
  await page.waitForFunction(() => [...document.querySelectorAll('#lab-document img')]
    .every(i => i.complete && i.naturalWidth > 0));
  const report = await page.locator('#lab-document').innerText();
  assert.ok(report.includes('p,q in [0,1]'));
  assert.ok(report.includes('3,200 independent records'));
  const imageUrls = await page.locator('#lab-document img').evaluateAll(imgs=>imgs.map(i=>i.src));
  assert.equal(imageUrls.length, figures.figures.length);
  for (const f of figures.figures) assert.ok(imageUrls.some(url=>url.endsWith(f.files[0])));
  assert.ok(!imageUrls.some(url=>url.includes('full-prior-matched') || url.includes('phase-b18')));
  assert.equal(await page.locator('#lab-document .katex-error').count(), 0);
  const captions = await page.locator('#lab-document em').allTextContents();
  assert.equal(captions.filter(t=>/^Figure L009\./.test(t)).length, figures.figures.length);
  await page.screenshot({path:path.join(qa,'report.png'),fullPage:true});
  receipt.report = {url:page.url(), all_current_images_loaded:true, image_count:figures.figures.length, captions_verified:true,
    full_domain_visible:true, superseded_images_absent:true, sha256:sha(path.join(folder,'REPORT.md')),
    screenshot:'results/verification/report.png', registry_ids:expected, stage:payload.lab.stage};
  const docLinks = [...new Set(await page.locator('#lab-document a[href^="/document?"]').evaluateAll(as=>as.map(a=>a.getAttribute('href'))))];
  for (const href of docLinks) {
    const relative = new URL(href, base).searchParams.get('path');
    const data = await json('/api/documents/file?path='+encodeURIComponent(relative));
    assert.ok(data.content.length > 0);
    receipt.documents.push({path:relative,url:base+href,readable:true});
  }
  for (const f of figures.figures) {
    await visit(`/lab-result?lab=${lab}&result=${f.id}`, '#result-content img');
    await page.waitForFunction(()=>[...document.querySelectorAll('#result-content img')].every(i=>i.complete&&i.naturalWidth>0));
    assert.ok((await page.locator('#result-content img').getAttribute('src')).endsWith(f.files[0]));
    assert.ok((await page.locator('.result-figure figcaption').innerText()).includes(f.semantics));
    // Verify the downloadable vector exports through the same asset server.
    for (const vector of f.files.slice(1)) {
      const response = await page.request.get(`${base}/lab-assets/${lab}/${vector}`,{headers:{'Sec-Fetch-Dest':'empty',Accept:vector.endsWith('.pdf')?'application/pdf':'image/svg+xml'}});
      assert.equal(response.status(),200);
      const bytes = await response.body();
      assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'),figures.output_sha256[vector]);
    }
    if (['warm-runtime'].includes(f.id)) await page.screenshot({path:path.join(qa,`${f.id}-page.png`),fullPage:true});
    receipt.figures.push({id:f.id,url:page.url(),image_loaded:true,caption_matches:true,svg_pdf_hashes_match:true,inputs:f.inputs});
  }
  const wikiApi = await json(`/api/labs/${lab}/wiki?page=index`);
  for (const id of wikiApi.pages) {
    await visit(`/lab-wiki?lab=${lab}&page=${encodeURIComponent(id)}`, '#local-wiki-document');
    assert.ok((await page.locator('#local-wiki-document').innerText()).length > 100);
    assert.equal(await page.locator('#local-wiki-document .katex-error').count(),0,`wiki math: ${id}`);
    if (id==='planar-ml') await page.screenshot({path:path.join(qa,'planar-wiki.png'),fullPage:true});
    receipt.wiki.push({page:id,url:page.url(),content_visible:true,math_errors:0});
  }
  await visit('/document?path=src%2Fherald_decoder%2FREADME.md','.project-document-preview');
  assert.ok((await page.locator('.project-document-preview').innerText()).includes('make_decoder'));
  receipt.source_readme={url:page.url(),api_visible:true};
  await visit(`/document?path=${encodeURIComponent('labs/'+lab+'/data/README.md')}`,'.project-document-preview');
  assert.equal(await page.locator('.project-document-preview a[href$=".svg"]').count(),figures.figures.reduce((n,f)=>n+f.files.filter(x=>x.endsWith('.svg')).length,0));
  assert.equal(await page.locator('.project-document-preview a[href$=".pdf"]').count(),figures.figures.reduce((n,f)=>n+f.files.filter(x=>x.endsWith('.pdf')).length,0));
  receipt.vector_guide={url:page.url(),all_available_svg_and_pdf_links_visible:true};
  await visit(`/lab-result?lab=${lab}&result=survey-summary`,'.result-code');
  const visibleSummary=JSON.parse(await page.locator('.result-code').innerText());
  assert.equal(visibleSummary.fresh_trials,3200);
  receipt.summary={url:page.url(),status:visibleSummary.status};
  await visit(`/lab-result?lab=${lab}&result=decoder-workbench`,'iframe');
  const frame=page.frameLocator('iframe');
  await frame.locator('#run').waitFor();
  for (const p of [.24,.8,0,1]) {
    await frame.locator('#p').fill(String(p));
    const responsePromise=page.waitForResponse(r=>r.url().endsWith(`/api/labs/${lab}/artifact`)&&r.request().method()==='POST');
    await frame.locator('#run').click();
    const response=await responsePromise;
    assert.equal(response.status(),200);
    const result=await response.json();
    await frame.locator('#status').filter({hasText:`p = ${p},`}).waitFor();
    assert.equal(await frame.locator('#rows tr').count(),5);
    assert.ok(await frame.locator('#plot line').count()>0);
    for (const row of result.methods) {
      if ((p===0||p===1)&&row.method==='bp_matching') assert.ok(row.error);
      else {assert.ok(!row.error,JSON.stringify(row));assert.equal(row.syndrome_valid,true);}
    }
    receipt.workbench.push({p,q:.5,url:page.url(),five_rows_rendered:true,
      valid_nonlegacy_methods:true,legacy_endpoint_error:p===0||p===1});
    if (p===.8) await page.screenshot({path:path.join(qa,'workbench-high-p.png'),fullPage:true});
  }
  assert.deepEqual(receipt.browser_errors,[]);
  await browser.close();
  receipt.status='passed';
  fs.writeFileSync(path.join(folder,'results/rendered-delivery.json'),JSON.stringify(receipt,null,2)+'\n');
  console.log(JSON.stringify({status:receipt.status,figures:receipt.figures.length,wiki_pages:receipt.wiki.length,
    document_links:receipt.documents.length,workbench_cases:receipt.workbench.length,stage:receipt.report.stage}));
})().catch(error=>{console.error(error);process.exit(1);});

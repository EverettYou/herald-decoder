/* Verify the exact document URL and its Local Wiki counterpart. */
const {chromium} = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const folder = path.resolve(__dirname,'..');
const lab = path.basename(folder);
const base = process.env.LAB009_DASHBOARD_URL || 'http://127.0.0.1:8010';
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const diagrams = JSON.parse(fs.readFileSync(path.join(folder,'results/k4-gadget-diagrams.json')));
assert.equal(diagrams.status,'passed');
assert.equal(diagrams.figures.length,3);
assert.equal(diagrams.generator_source_sha256,hash(fs.readFileSync(path.join(folder,'scripts/build_k4_gadget_diagrams.py'))));
assert.equal(diagrams.partition_fixture_sha256,hash(fs.readFileSync(path.join(folder,diagrams.partition_fixture))));
for (const figure of diagrams.figures) for (const file of figure.files) {
  assert.equal(file.sha256,hash(fs.readFileSync(path.join(folder,file.path))),file.path);
}
(async () => {
  const browser = await chromium.launch({
    executablePath:process.env.LAB009_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless:true
  });
  try {
    const page = await browser.newPage({viewport:{width:1440,height:1200}});
    const errors = [];
    page.on('pageerror',error => errors.push(String(error)));
    const checks = [];
    const file = `labs/${lab}/wiki/planar-ml.md`;
    const urls = [
      ['/document?path='+encodeURIComponent(file),'.project-document-preview'],
      [`/lab-wiki?lab=${lab}&page=planar-ml`,'#local-wiki-document']
    ];
    fs.mkdirSync(path.join(folder,'results/verification'),{recursive:true});
    for (const [url,selector] of urls) {
      const response = await page.goto(base+url);
      assert.equal(response.status(),200);
      const body = page.locator(selector);
      await body.waitFor();
      await body.getByRole('heading',{name:'Constructive gadget and weights',exact:true}).waitFor();
      const text = await body.innerText();
      for (const phrase of ['expanded auxiliary matching graph','Exactly what the matrix K contains',
        'The Grassmann path-integral interpretation','private leaf',
        'Construction and weights.','Four local matching cases.','Gluing gadgets into the matrix graph.',
        'Existence and the full nonnegative solution family','complete graph on four vertices',
        'construction has no solution','Herald-channel example in site-function notation',
        'This first diagram is symbolic','uses the physical herald record',
        'Each panel states its site entry']) {
        assert.ok(text.includes(phrase),phrase);
      }
      assert.ok(!/[\u3400-\u4dbf\u4e00-\u9fff]/u.test(text),'Chinese prose remains in the rendered note');
      assert.ok(!/2\s*,\s*3\s*,\s*5\s*,\s*7/.test(text),'Superseded illustrative tuple remains');
      assert.equal(await body.locator('.katex-error').count(),0);
      assert.equal(await body.locator('table').count(),3);
      const theoryScreenshots = [];
      for (const [name,heading] of [['notation','The original edge-spin partition function'],
        ['solution-family','Existence and the full nonnegative solution family']]) {
        await body.getByRole('heading',{name:heading,exact:true}).scrollIntoViewIfNeeded();
        const screenshot=`results/verification/k4-${name}-surface-${checks.length}.png`;
        await page.screenshot({path:path.join(folder,screenshot)});
        theoryScreenshots.push(screenshot);
      }
      assert.equal(await body.locator('img').count(),3);
      const imageChecks = [];
      for (const figure of diagrams.figures) {
        const rendered = body.locator(`img[src*="${figure.name}.png"]`);
        assert.equal(await rendered.count(),1,figure.name);
        await rendered.scrollIntoViewIfNeeded();
        const imageState = await rendered.evaluate(async img => {
          if (!img.complete) await new Promise((resolve,reject) => {
            img.addEventListener('load',resolve,{once:true});
            img.addEventListener('error',reject,{once:true});
          });
          return {src:img.src,loaded:img.complete && img.naturalWidth>0,
            width:img.naturalWidth,height:img.naturalHeight,alt:img.alt};
        });
        assert.ok(imageState.loaded,figure.name);
        assert.ok(imageState.alt.length>20);
        const screenshot=`results/verification/${figure.name}-surface-${checks.length}.png`;
        await page.screenshot({path:path.join(folder,screenshot)});
        for (const extension of ['svg','pdf']) {
          assert.equal(await body.locator(`a[href*="${figure.name}.${extension}"]`).count(),1);
        }
        imageChecks.push({...imageState,screenshot,vector_links_visible:true});
      }
      await body.getByRole('heading',{name:'Constructive gadget and weights',exact:true}).scrollIntoViewIfNeeded();
      const screenshot=`results/verification/pfaffian-site-review-${checks.length}.png`;
      await page.screenshot({path:path.join(folder,screenshot)});
      checks.push({url:page.url(),source_and_site_mapping_visible:true,
        gaussian_integral_visible:true,site_and_K_tables_visible:true,
        zero_support_case_visible:true,english_only:true,math_errors:0,screenshot,
        complete_K4_explanation_visible:true,nonnegative_solution_family_visible:true,
        theory_screenshots:theoryScreenshots,diagrams:imageChecks});
    }
    const downloads=[];
    for (const figure of diagrams.figures) for (const file of figure.files) {
      const url=base+`/lab-assets/${lab}/${file.path}`;
      const response=await page.request.get(url,{headers:{'Sec-Fetch-Dest':'empty'}});
      assert.equal(response.status(),200,url);
      const bytes=await response.body();
      assert.equal(hash(bytes),file.sha256,url);
      downloads.push({url,sha256:file.sha256});
    }
    const matchingSvg=fs.readFileSync(path.join(folder,'figures/k4-gadget-matchings.svg'),'utf8');
    for (const [pattern,value] of [['000','1'],['011','0.4'],['101','0.4'],['110','0.4']]) {
      assert.ok(matchingSvg.includes(`f_{${pattern}}=${value}`));
    }
    assert.ok(matchingSvg.includes('f_{000}/f_{011}=2.5'));
    assert.ok(!matchingSvg.includes('(2,3,5,7)'));
    const source = fs.readFileSync(path.join(folder,'wiki/planar-ml.md'));
    const doc = await page.request.get(base+'/api/documents/file?path='+encodeURIComponent(file));
    assert.equal(doc.status(),200);
    assert.equal((await doc.json()).content,source.toString());
    const json = await page.request.get(base+'/api/documents/file?path='+encodeURIComponent(`labs/${lab}/results/site-gadget-partition-review.json`));
    assert.equal(json.status(),200);
    assert.equal(JSON.parse((await json.json()).content).status,'passed');
    assert.deepEqual(errors,[]);
    const receipt = {status:'passed',verified_at:new Date().toISOString(),
      wiki_source_sha256:hash(source),diagram_receipt_sha256:hash(fs.readFileSync(path.join(folder,'results/k4-gadget-diagrams.json'))),
      local_partition_check:'results/site-gadget-partition-review.json',checks,downloads,browser_errors:errors,
      physical_signature_label_check:{all_four_site_entries_and_values_explicit_in_panel_titles:true,
        first_diagram_identified_as_symbolic:true,triangle_ratio_and_pivot_condition_visible:true,
        herald_parameters_visible:true,arbitrary_tuple_removed:true},
      scope:'Theory explanation only; active phase campaign state and production decoder code untouched.'};
    fs.writeFileSync(path.join(folder,'results/site-gadget-wiki-render-review.json'),JSON.stringify(receipt,null,2)+'\n');
    console.log(JSON.stringify({status:'passed',surfaces:checks.length,diagrams:diagrams.figures.length,downloads:downloads.length,math_errors:0}));
  } finally {
    await browser.close();
  }
})().catch(error=>{console.error(error);process.exit(1);});

#!/usr/bin/env python3
"""Verify exact Lab 007 report/Local Wiki content, links and rendered mathematics."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import urllib.request
from playwright.sync_api import sync_playwright

LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parents[1];BASE='http://127.0.0.1:8010'

def get(path):return json.load(urllib.request.urlopen(BASE+path))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    checks=json.loads((LAB/'results/exact-model-checks-2026-09-14.json').read_text())
    supplement=json.loads((LAB/'results/mapping-supplement-2026-09-14.json').read_text())
    assert checks['status']==supplement['status']=='passed'
    assert checks['source_sha256']==digest(LAB/'scripts/check_exact_model.py')
    assert supplement['source_sha256']==digest(LAB/'scripts/check_mapping_supplement.py')
    data=get('/api/labs/'+LAB.name);meta=json.loads((LAB/'lab.json').read_text())
    for key in ('stage','summary','current_focus','next_action','updated'):assert data['lab'][key]==meta[key]
    assert data['report']['content']==(LAB/'REPORT.md').read_text()
    assert len([r for r in data['outputs'] if r['id']=='local-wiki'])==1
    assert len({r['id'] for r in data['outputs']})==len(data['outputs'])
    shots=ROOT/'.tmp/lab007-delivery';shots.mkdir(parents=True,exist_ok=True);errors=[];pages=[];documents=[];shared=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox']);page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE+'/lab?id='+LAB.name);page.wait_for_selector('#lab-document .katex');page.evaluate('document.fonts.ready');doc=page.locator('#lab-document')
        text=doc.inner_text();assert '488,340' in text and '128/193' in text and 'No threshold' in text
        assert doc.locator('table').count()==1;assert doc.locator('.katex-error').count()==0
        links=doc.locator('a[href*="/document?"]');assert links.count()==7
        document_links=[links.nth(i).get_attribute('href') for i in range(links.count())]
        for href in document_links:assert page.request.get(BASE+href).status==200
        doc.locator('table').scroll_into_view_if_needed();page.screenshot(path=str(shots/'report-model-table.png'))
        page.locator('#lab-results').scroll_into_view_if_needed();page.screenshot(path=str(shots/'report-registry.png'))
        for name in ('index','partition-function','conjugacy','statistical-model','decoder-gap','predictions','problem','source-context'):
            api=get('/api/labs/'+LAB.name+'/wiki?page='+name)
            assert api['content']==(LAB/'wiki'/f'{name}.md').read_text()
            url=BASE+'/lab-wiki?lab='+LAB.name+'&page='+name;page.goto(url);page.wait_for_selector('#local-wiki-document h1');page.evaluate('document.fonts.ready')
            doc=page.locator('#local-wiki-document');body=doc.inner_text();assert 'Dashboard error' not in body
            assert doc.locator('.katex-error').count()==0,(name,doc.locator('.katex-error').all_text_contents())
            math=doc.locator('.katex-display').count()
            if name in ('partition-function','conjugacy','statistical-model','decoder-gap'):assert math>0
            if name in ('statistical-model','decoder-gap','conjugacy','predictions','source-context'):assert doc.locator('table').count()>=1
            local_links=[]
            for anchor in doc.locator('a[href]').all():
                href=anchor.get_attribute('href')
                if href.startswith('/'):
                    response=page.request.get(BASE+href);assert response.status==200,(name,href,response.status);local_links.append(href)
            overflow=doc.locator('.katex-display').evaluate_all('(nodes)=>nodes.map((n,i)=>({index:i,width:n.clientWidth,scroll:n.scrollWidth})).filter(x=>x.scroll>x.width+2)')
            pages.append({'page':name,'url':url,'source_sha256':digest(LAB/'wiki'/f'{name}.md'),'display_equations':math,'local_links_verified':len(local_links),'horizontally_scrolling_equations':overflow})
            if name in ('statistical-model','decoder-gap'):
                doc.locator('table').first.scroll_into_view_if_needed();page.screenshot(path=str(shots/(name+'.png')))
        for href in document_links:
            page.goto(BASE+href);page.wait_for_selector('.project-document-preview');page.evaluate('document.fonts.ready')
            doc=page.locator('.project-document-preview');assert len(doc.inner_text())>500
            assert doc.locator('.katex-error').count()==0
            documents.append({'url':BASE+href,'rendered_characters':len(doc.inner_text()),'display_equations':doc.locator('.katex-display').count()})
        assert len([r for r in data['outputs'] if r['id']=='representation-informed-sector-model'])==1
        for name,phrase in [('models/representation-informed-sector-model','90 fixture'),('methods/sun-fusion-herald-belief-propagation','Exact sector model'),('questions/program-level-scientific-roadmap','formulation gate completed'),('thesis','Current theoretical evidence boundary')]:
            page.goto(BASE+'/wiki?page='+name);page.wait_for_function('(phrase)=>document.querySelector("#wiki-document")?.innerText.includes(phrase)',arg=phrase);page.evaluate('document.fonts.ready')
            doc=page.locator('#wiki-document');assert doc.locator('.katex-error').count()==0
            shared.append({'page':name,'source_sha256':digest(ROOT/'wiki'/f'{name}.md')})
            if name=='models/representation-informed-sector-model':doc.locator('table').scroll_into_view_if_needed();page.screenshot(path=str(shots/'shared-model.png'))
        assert not errors,errors;browser.close()
    out={'status':'browser_verified_pending_visual_review','updated':datetime.now(timezone.utc).isoformat(),
         'report_url':BASE+'/lab?id='+LAB.name,'report_sha256':digest(LAB/'REPORT.md'),'lab_stage':meta['stage'],
         'current_inputs_verified':True,'artifact_regeneration':'Prose theory and table; no generated scientific figure required.',
         'report_content_and_embeds_verified':True,'active_registry_verified':True,'rendered_pages':pages,'rendered_document_links':documents,'shared_wiki_pages':shared,'page_errors':errors,
         'screenshots':[str((shots/name).relative_to(ROOT)) for name in ('report-model-table.png','report-registry.png','statistical-model.png','decoder-gap.png','shared-model.png')],
         'source_inputs':{name:digest(LAB/'results'/name) for name in ('exact-model-checks-2026-09-14.json','mapping-supplement-2026-09-14.json')},
         'semantic_scope':'Ordinary SU(N) classical fusion instrument; exact finite checks and restricted loop gas; no threshold or BKT claim.'}
    (LAB/'results/theory-delivery-2026-09-14.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))

if __name__=='__main__':main()

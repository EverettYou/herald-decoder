#!/usr/bin/env python3
"""Verify the combined LER figure through raw inputs, registry, report and browser."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import urllib.request
from playwright.sync_api import sync_playwright

LAB=Path(__file__).resolve().parents[1];ROOT=LAB.parents[1]
BASE='http://127.0.0.1:8010'

def main():
    audit=json.loads((LAB/'results/a8-ler-overview-render.json').read_text())
    assert audit['status']=='passed' and audit['sampled_cells']==600
    assert audit['layout']['rows']==['U1','SU2','SU3'] and audit['layout']['columns']==['square','honeycomb']
    assert audit['layout']['shared_x'] and not audit['layout']['shared_y'] and not audit['layout']['p_zero_marker']
    assert audit['layout']['colors']=={'5':'#fca082','7':'#ef6548','9':'#cb181d','11':'#7f0000'}
    for panel in audit['panels']:
        assert hashlib.sha256((LAB/panel['input']).read_bytes()).hexdigest()==panel['input_sha256']
        assert not (LAB/f"figures/a8-{panel['lattice']}-{panel['group']}-ler.png").exists()
    figure=LAB/audit['figure'];digest=hashlib.sha256(figure.read_bytes()).hexdigest();assert digest==audit['figure_sha256']
    subprocess.run([sys.executable,str(ROOT/'skills/research-workflow/scripts/verify_lab_figure_delivery.py'),str(LAB),audit['figure'],'--result-id','full-record-ler-overview','--forbid-result-id-pattern',r'^full-record-(square|honeycomb)-(u1|su2|su3)-ler$'],check=True)
    data=json.load(urllib.request.urlopen(BASE+'/api/labs/'+LAB.name));selected=[o for o in data['outputs'] if o['id'].startswith('full-record-')]
    assert len(selected)==7
    screenshots=ROOT/'.tmp/a8-overview-browser';screenshots.mkdir(exist_ok=True)
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1100});page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE+'/lab?id='+LAB.name)
        page.wait_for_function('document.querySelectorAll("#lab-document img").length===1 && document.querySelector("#lab-document img").naturalWidth>0')
        img=page.locator('#lab-document img');assert img.get_attribute('src').endswith('/'+audit['figure'])
        assert page.locator('#lab-results a[href*="full-record-ler-overview"]').count()==1
        assert page.locator('#lab-results a[href*="full-record-"]').count()==7
        assert 'Red darkens from L=5 to L=11' in page.locator('#lab-document').inner_text()
        page.evaluate('document.fonts.ready');img.scroll_into_view_if_needed();page.screenshot(path=str(screenshots/'report.png'),full_page=False)
        page.goto(BASE+'/lab-result?lab='+LAB.name+'&result=full-record-ler-overview')
        page.wait_for_function('document.querySelector(".result-figure img")?.naturalWidth > 0')
        src=page.locator('.result-figure img').get_attribute('src');response=page.request.get(BASE+src)
        assert response.status==200 and hashlib.sha256(response.body()).hexdigest()==digest
        page.evaluate('document.fonts.ready');page.screenshot(path=str(screenshots/'result.png'),full_page=True)
        assert not errors,errors
        browser.close()
    result={'status':'passed','updated':datetime.now(timezone.utc).isoformat(),'input_hashes_verified':6,'figure_sha256':digest,
            'report_images_loaded':1,'active_ler_results':1,'companion_diagnostics':6,'superseded_standalone_pngs':0,
            'layout':audit['layout'],'report_url':BASE+'/lab?id='+LAB.name,'result_url':BASE+'/lab-result?lab='+LAB.name+'&result=full-record-ler-overview',
            'browser_image_bytes_match':True,'page_errors':errors,'screenshots':[str((screenshots/name).relative_to(ROOT)) for name in ('report.png','result.png')]}
    (LAB/'results/a8-overview-delivery-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Passed: six unchanged inputs, one report image, one active LER result, correct red palette and axes, no old standalone PNGs, rendered bytes match.')

if __name__=='__main__':main()

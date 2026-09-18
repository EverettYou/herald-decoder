"""Live homepage verification; run with an installed Playwright Chromium browser."""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def verify(base_url, output):
    output.mkdir(parents=True, exist_ok=True)
    checks = {}
    with sync_playwright() as p:
        browser = p.chromium.launch(channel='chromium', headless=True, args=['--no-sandbox'])
        page = browser.new_page(viewport={'width': 1440, 'height': 1100})
        errors = []
        page.on('pageerror', lambda error: errors.append(str(error)))
        page.goto(base_url)
        page.wait_for_selector('.evolution-card')
        viewport = page.locator('.evolution-viewport')
        panel = page.locator('.research-timeline-panel')
        viewport.scroll_into_view_if_needed()
        zoom = lambda: float(viewport.get_attribute('data-zoom'))
        scroll = lambda: viewport.evaluate('(v)=>({x:v.scrollLeft,y:v.scrollTop})')
        assert page.locator('.evolution-card').count() == 6
        assert page.locator('.evolution-edge').count() == 7
        assert page.locator('[data-timeline-spacing]').count() == 0
        checks['live_catalog'] = {'cards': 6, 'edges': 7}
        geometry = viewport.evaluate('''v => {
          const bounds=v.getBoundingClientRect();
          return [...v.querySelectorAll('.evolution-card')].map(e=>{
            const r=e.getBoundingClientRect(),title=e.querySelector('h3').getBoundingClientRect();
            return {id:e.dataset.lab,title:e.querySelector('h3').innerText,
              visible:r.left>=bounds.left&&r.right<=bounds.right&&r.top>=bounds.top&&r.bottom<=bounds.bottom,
              textFits:title.bottom<r.bottom&&e.scrollHeight<=e.offsetHeight};
          });
        }''')
        assert all(n['visible'] and n['textFits'] for n in geometry), geometry
        checks['desktop_cards'] = geometry
        crossings = page.locator('.evolution-edges').evaluate('''svg=>{
          const paths=[...svg.querySelectorAll('.evolution-edge')].map(p=>{
            const length=p.getTotalLength(),points=[];
            for(let i=0;i<=length;i+=3)points.push(p.getPointAtLength(i));
            points.push(p.getPointAtLength(length));return {id:p.dataset.source+' → '+p.dataset.target,points};
          });
          const cross=(a,b,c)=>(b.x-a.x)*(c.y-a.y)-(b.y-a.y)*(c.x-a.x);
          const hits=[];
          for(let i=0;i<paths.length;i++)for(let j=i+1;j<paths.length;j++){
            const a=paths[i].points,b=paths[j].points;let hit=false;
            for(let k=1;k<a.length&&!hit;k++)for(let l=1;l<b.length&&!hit;l++)
              if(cross(a[k-1],a[k],b[l-1])*cross(a[k-1],a[k],b[l])<-.0001 && cross(b[l-1],b[l],a[k-1])*cross(b[l-1],b[l],a[k])<-.0001)hit=true;
            if(hit)hits.push([paths[i].id,paths[j].id]);
          }
          return hits;
        }''')
        assert not crossings, crossings
        checks['edge_crossings'] = crossings
        page.mouse.move(0, 0)
        panel.screenshot(path=str(output / 'desktop.png'))
        initial_zoom = zoom()
        box = viewport.bounding_box()
        page.mouse.move(box['x']+20, box['y']+20)
        page.mouse.wheel(0, 120)
        page.wait_for_timeout(150)
        assert zoom() == initial_zoom
        checks['ordinary_scroll_does_not_zoom'] = True
        for _ in range(4):
            page.locator('[data-timeline-zoom-in]').click()
        viewport.scroll_into_view_if_needed()
        viewport.evaluate('(v)=>{v.scrollLeft=180;v.scrollTop=120}')
        before = scroll(); before_zoom = zoom(); box = viewport.bounding_box()
        page.mouse.move(box['x']+30, box['y']+30)
        page.mouse.wheel(80, 110)
        page.wait_for_timeout(250)
        after = scroll()
        assert after['x'] > before['x'] and after['y'] > before['y'], (before, after)
        assert zoom() == before_zoom
        checks['native_two_axis_scroll'] = {'before': before, 'after': after}
        # Browser-mapped macOS pinch signal. Verify the world point at the cursor.
        anchor = lambda: viewport.evaluate('''v=>{const r=v.getBoundingClientRect(),w=v.querySelector('.evolution-world').getBoundingClientRect(),z=Number(v.dataset.zoom);return {x:(r.left+300-w.left)/z,y:(r.top+220-w.top)/z}}''')
        old_anchor = anchor()
        viewport.evaluate('''v=>{const r=v.getBoundingClientRect();v.dispatchEvent(new WheelEvent('wheel',{deltaY:15,ctrlKey:true,clientX:r.left+300,clientY:r.top+220,bubbles:true,cancelable:true}));}''')
        new_anchor = anchor()
        assert zoom() < before_zoom
        assert abs(old_anchor['x']-new_anchor['x']) < 2 and abs(old_anchor['y']-new_anchor['y']) < 2, (old_anchor,new_anchor)
        checks['pinch_cursor_anchor'] = {'before': old_anchor, 'after': new_anchor}
        viewport.evaluate('(v)=>{v.scrollLeft=200;v.scrollTop=200}')
        before = scroll(); box = viewport.bounding_box()
        page.mouse.move(box['x']+8,box['y']+8)
        page.mouse.down(); page.mouse.move(box['x']+68,box['y']+58,steps=6); page.mouse.up()
        after = scroll()
        assert after['x'] < before['x'] and after['y'] < before['y'], (before,after)
        checks['mouse_drag'] = True
        page.locator('[data-timeline-fit]').click()
        assert abs(zoom()-initial_zoom) < .001
        su = page.locator('.evolution-card[data-lab="lab-006-sun-bp-theory"]')
        page.keyboard.press('Tab')
        su.focus()
        assert su.evaluate("e=>e.matches(':focus-visible')")
        assert page.locator('.evolution-edge.is-traced').count() == 1
        panel.screenshot(path=str(output / 'focus.png'))
        su.press('Enter')
        page.wait_for_url('**/lab?id=lab-006-sun-bp-theory')
        checks['keyboard_navigation_and_trace'] = True
        page.locator('.brand').click()
        page.wait_for_selector('.evolution-card')
        initial_zoom = zoom()
        page.locator('[data-timeline-zoom-in]').click()
        assert abs(zoom()-initial_zoom*1.2) < .001
        checks['remount_controls'] = True
        # Safari GestureEvent mapping can be exercised in Chromium, though this
        # does not substitute for physical Safari/macOS device testing.
        before_zoom = zoom()
        viewport.evaluate('''v=>{const r=v.getBoundingClientRect();for(const [type,scale] of [['gesturestart',1],['gesturechange',1.1],['gestureend',1.1]]){const e=new Event(type,{bubbles:true,cancelable:true});Object.assign(e,{scale,clientX:r.left+200,clientY:r.top+200});v.dispatchEvent(e)}}''')
        assert abs(zoom()-before_zoom*1.1) < .001
        checks['safari_gesture_event_mapping'] = 'Synthetic event test; physical Safari not tested'
        checks['page_errors'] = errors
        assert not errors, errors
        mobile = browser.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True)
        touch_page = mobile.new_page()
        touch_page.goto(base_url)
        touch_page.wait_for_selector('.evolution-card')
        v = touch_page.locator('.evolution-viewport')
        v.evaluate("e=>e.scrollIntoView({block:'start'})")
        assert touch_page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        assert float(v.get_attribute('data-zoom')) >= .7
        touch_page.locator('.research-timeline-panel').screenshot(path=str(output / 'mobile.png'))
        v.evaluate("e=>e.scrollIntoView({block:'start'})")
        box = v.bounding_box(); x=box['x']+100; y=max(0,box['y'])+100
        cdp=mobile.new_cdp_session(touch_page)
        def touches(kind, points):
            touch_page.wait_for_timeout(80)  # Give the synthetic finger movement a realistic duration.
            cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[{'x':px,'y':py,'id':i+1} for i,(px,py) in enumerate(points)]})
        before_zoom=float(v.get_attribute('data-zoom'))
        touches('touchStart',[(x-35,y),(x+35,y)])
        touches('touchMove',[(x-55,y),(x+55,y)])
        touches('touchEnd',[])
        assert float(v.get_attribute('data-zoom')) > before_zoom
        checks['two_finger_touch_pinch'] = True
        v.evaluate('(v)=>{v.scrollLeft=100;v.scrollTop=100}')
        before=v.evaluate('(v)=>({x:v.scrollLeft,y:v.scrollTop})')
        touches('touchStart',[(x,y)])
        touches('touchMove',[(x-50,y-40)])
        touches('touchEnd',[])
        after=v.evaluate('(v)=>({x:v.scrollLeft,y:v.scrollTop})')
        assert after['x']>before['x'] and after['y']>before['y'], (before,after)
        assert touch_page.url.rstrip('/')==base_url.rstrip('/')
        checks['touch_pan_without_navigation'] = True
        touch_page.wait_for_timeout(400)
        touch_page.locator('[data-timeline-fit]').tap()
        touch_page.wait_for_function("Number(document.querySelector('.evolution-viewport').dataset.zoom)<.4",timeout=5000)
        assert float(v.get_attribute('data-zoom')) < .4
        checks['mobile_overview'] = True
        touch_page.locator('.evolution-card').first.tap()
        touch_page.wait_for_url('**/lab?id=lab-001-string-herald-visualization')
        checks['touch_tap_navigation'] = True
        mobile.close();browser.close()
    (output/'browser-results.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://localhost:8010/')
    parser.add_argument('--output',type=Path,default=Path('.tmp/evolution-audit'))
    args=parser.parse_args();verify(args.base_url,args.output)

import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_basket.py').read().split('with sync_playwright()')[0])

def swipe(page, cdp, x, y0, y1, steps=10, delay=16):
    cdp.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y0}]})
    for i in range(1, steps+1):
        cdp.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':x,'y':y0+(y1-y0)*i/steps}]})
        page.wait_for_timeout(delay)
    cdp.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
    page.wait_for_timeout(450)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**p.devices['iPhone 13'])
    page = ctx.new_page(); cdp = ctx.new_cdp_session(page)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.goto(URL); page.evaluate('localStorage.clear()'); page.reload(); page.wait_for_timeout(400)

    check('Install guide shows in Safari on iPhone', page.locator('#install .install').count() == 1)
    page.screenshot(path=OUT + 'v13-01-install.png')
    page.click('#install [data-act="installLater"]'); page.wait_for_timeout(100)
    check('Not now hides guide', page.locator('#install .install').count() == 0)
    ctx2 = b.new_context(**p.devices['iPhone 13']); pg2 = ctx2.new_page()
    pg2.add_init_script("Object.defineProperty(navigator, 'standalone', { get: () => true })")
    pg2.goto(URL); pg2.wait_for_timeout(300)
    check('No guide when opened from Home Screen', pg2.locator('#install .install').count() == 0)
    ctx2.close()

    us = page.evaluate("[getComputedStyle(document.body).webkitUserSelect, getComputedStyle(document.querySelector('#addInput')).webkitUserSelect]")
    check('Selection off on page, on in inputs', us[0] == 'none' and us[1] in ('text', 'auto'))

    # Toast inside visible area
    add(page, 'Milk x2'); add(page, 'milk x3'); page.wait_for_timeout(400)
    tb = page.locator('#toast').bounding_box(); vh = page.viewport_size['height']
    check('Toast fully on screen', tb['y'] + tb['height'] <= vh - 20)
    page.locator('#addInput').blur()

    # Shops: supermarket gets sections, B&Q doesn't
    page.evaluate("addShop('Tesco Express'); addShop('B&Q'); save(); render();")
    st = state(page)
    secs = {s['name']: len(s['sections']) for s in st['shops']}
    check('Tesco Express gets sections, B&Q none', secs['Tesco Express'] == 24 and secs['B&Q'] == 0)

    # Swipe down from handle closes
    hold(page, item(page, 'Milk'))
    sb = page.locator('#sheet').bounding_box()
    check('Sheet bottom on screen', sb['y'] + sb['height'] <= vh + 1)
    page.screenshot(path=OUT + 'v13-02-sheet.png')
    swipe(page, cdp, 195, sb['y'] + 12, sb['y'] + 260)
    check('Swipe down on handle closes sheet', page.evaluate('sheetCtx') is None)
    # Small swipe snaps back
    hold(page, item(page, 'Milk'))
    sb = page.locator('#sheet').bounding_box()
    swipe(page, cdp, 195, sb['y'] + 12, sb['y'] + 50, steps=10, delay=40)
    check('Small slow swipe keeps sheet open', page.evaluate('sheetCtx') is not None)
    tf = page.evaluate("getComputedStyle(sheet).transform")
    check('Snapped back to place', tf in ('none', 'matrix(1, 0, 0, 1, 0, 0)'))
    # Swipe from body of sheet (at top of scroll) closes
    swipe(page, cdp, 195, sb['y'] + 150, sb['y'] + 420)
    check('Swipe down on sheet body closes', page.evaluate('sheetCtx') is None)
    # Close button
    hold(page, item(page, 'Milk')); page.click('#sheet .sheet-close'); page.wait_for_timeout(350)
    check('Close button closes', page.evaluate('sheetCtx') is None)

    # Remove all sections
    tid = [s['id'] for s in state(page)['shops'] if s['name'] == 'Tesco Express'][0]
    tap(page, f'.tab[data-tab="{tid}"]'); page.wait_for_timeout(200)
    page.click('#btnShop'); page.wait_for_timeout(350)
    page.click('#sheet [data-act="clearSections"]'); page.click('#sheet [data-act="clearSections"]'); page.wait_for_timeout(300)
    check('Remove all sections', [len(s['sections']) for s in state(page)['shops'] if s['id'] == tid][0] == 0)
    b.close()

print('\nConsole errors:', errors)
print('Failed:', [n for n, ok in results if not ok])

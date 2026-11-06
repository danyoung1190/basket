import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
def secs(pg, shop): return pg.evaluate(f"state.shops.find(s=>s.name==='{shop}').sections.map(s=>s.name)")
def swipe(pg, sel, dx):
    bb = pg.locator(sel).first.bounding_box(); x, y = bb['x'] + bb['width'] * .6, bb['y'] + bb['height'] / 2
    pg.mouse.move(x, y); pg.mouse.down()
    for i in range(1, 11): pg.mouse.move(x + dx * i / 10, y + 1); pg.wait_for_timeout(15)
    pg.mouse.up(); pg.wait_for_timeout(300)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone(p, b)
    A.evaluate("addShop('Tesco'); state.tab = state.shops[0].id; ['Milk','Bananas','Paprika'].forEach(n => addItem(n, {quiet:true})); save(); render();")
    A.click('#btnShop'); A.wait_for_timeout(350)
    row = '#sheet .secrow.swipe:has(.nm:text-is("Bakery"))'
    check('No one-tap delete button on sections', A.locator('#sheet .secrow .mini[data-act="secDelete"]').count() == 0)
    A.locator(row + ' .nm').click(); A.wait_for_timeout(200)
    check('Tapping a section does not delete it', 'Bakery' in secs(A, 'Tesco'))
    swipe(A, row + ' .slide', -30)
    check('Short slide snaps back, nothing deleted', 'Bakery' in secs(A, 'Tesco') and A.locator(row + '.open').count() == 0)
    swipe(A, row + ' .slide', -120)
    check('Long slide reveals Delete', A.locator(row + '.open').count() == 1 and 'Bakery' in secs(A, 'Tesco'))
    A.locator(row + ' .swipe-del').click(); A.wait_for_timeout(350)
    check('Tap Delete removes it', 'Bakery' not in secs(A, 'Tesco'))
    A.click('#toast [data-act="undo"]'); A.wait_for_timeout(300)
    check('Undo brings it back', 'Bakery' in secs(A, 'Tesco'))
    # Slide on a row must not press its arrow buttons
    before = secs(A, 'Tesco')
    A.evaluate("openShopSheet(state.shops[0].id)"); A.wait_for_timeout(350)
    swipe(A, '#sheet .secrow.swipe:has(.nm:text-is("Dairy & eggs")) .mini[data-act="secUp"]', -120)
    check('Swipe that starts on an arrow does not move the section', secs(A, 'Tesco') == before)
    # Rename sheet also offers delete, two taps
    A.locator('#sheet .secrow.swipe:has(.nm:text-is("Frozen")) [data-act="secRename"]').click(); A.wait_for_timeout(350)
    A.click('#sheet [data-act="promptDelete"]'); A.wait_for_timeout(150)
    check('Rename sheet delete needs a second tap', 'Frozen' in secs(A, 'Tesco'))
    A.click('#sheet [data-act="promptDelete"]'); A.wait_for_timeout(350)
    check('Second tap deletes', 'Frozen' not in secs(A, 'Tesco'))
    A.keyboard.press('Escape'); A.wait_for_timeout(350)

    # Share a private shop live, from the header Share button
    A.click('#btnShare'); A.wait_for_timeout(300)
    check('Share offers live or message', A.locator('#sheet [data-act="shareLive"]').count() == 1 and A.locator('#sheet [data-act="shareText"]').count() == 1)
    A.click('#sheet [data-act="shareLive"]'); A.wait_for_timeout(1800)
    code = A.locator('#sheet .bigcode').text_content().strip()
    check('Tesco is now shared, code shown', code.startswith('TRLY-') and A.evaluate("isShared(state.shops[0])"))
    check('Same tab, items kept', A.evaluate("state.shops.length") == 1 and sorted(A.evaluate("itemsIn(state.shops[0].id).map(i=>i.name)")) == ['Bananas', 'Milk', 'Paprika'])
    A.keyboard.press('Escape'); A.wait_for_timeout(300)
    ctxB, B = phone(p, b)
    B.evaluate(f"joinSharedList('{code}')"); settle(B, ms=1800)
    check('Other phone gets the items', sorted(B.evaluate("itemsIn(state.shops.find(s=>s.name==='Tesco').id).map(i=>i.name)")) == ['Bananas', 'Milk', 'Paprika'])
    check('Other phone gets the aisles, minus the deleted one', 'Frozen' not in secs(B, 'Tesco') and 'Bakery' in secs(B, 'Tesco'))
    add(B, 'Bread'); B.locator('#addInput').blur(); settle(A, B, ms=1500)
    check('Live both ways after converting', 'Bread' in A.evaluate("itemsIn(state.shops[0].id).map(i=>i.name)"))
    # shop sheet on a shared list shows Share code, not the convert button
    A.click('#btnShop'); A.wait_for_timeout(300)
    check('Shared shop sheet shows Share code', A.locator('#sheet [data-act="showCode"]').count() == 1 and A.locator('#sheet [data-act="makeShared"]').count() == 0)
    ctxA.close(); ctxB.close()

    # Offline: converting fails cleanly and the shop stays private
    ctxC, C = phone(p, b)
    C.evaluate("addShop('Aldi'); state.tab = state.shops[0].id; addItem('Eggs', {quiet:true}); save(); render(); window.__offline = true; fb = null;")
    C.route('https://www.gstatic.com/firebasejs/**', lambda r, q: r.abort())
    C.click('#btnShop'); C.wait_for_timeout(300); C.click('#sheet [data-act="makeShared"]'); C.wait_for_timeout(2500)
    check('Offline convert leaves the shop private', not C.evaluate("isShared(state.shops[0])") and C.evaluate("itemsIn(state.shops[0].id).length") == 1)
    ctxC.close(); b.close()

print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e and 'ERR_FAILED' not in e])
print('Failed:', [n for n, ok in results if not ok])

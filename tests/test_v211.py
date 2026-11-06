import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, urllib.request
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])

def secs(pg, shop):  return pg.evaluate(f"state.shops.find(s=>s.name==='{shop}').sections.map(s=>s.name)")
def secof(pg, shop, item): return pg.evaluate(f"""(() => {{ const s=state.shops.find(x=>x.name==='{shop}'); const i=state.items.find(x=>x.shopId===s.id && x.name==='{item}'); const sec=s.sections.find(z=>z.id===i.sectionId); return sec?sec.name:null; }})()""")

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone(p, b)
    A.evaluate("createSharedList('Home')"); A.wait_for_timeout(1500)
    for n in ['Milk', 'Cheddar', 'Bananas', 'Bin bags', 'Milkk']: add(A, n)
    A.locator('#addInput').blur(); settle(A)
    check('Shared list files Milk into Dairy & eggs', secof(A, 'Home', 'Milk') == 'Dairy & eggs')
    check('Aisles appear in walking order', secs(A, 'Home') == ['Fruit & veg', 'Dairy & eggs', 'Cheese', 'Household'])
    check('Headers shown', A.locator('.row.header:not(.empty)').count() == 4)
    check('Typo still files', secof(A, 'Home', 'Milkk') == 'Dairy & eggs')

    code = A.evaluate("formatCode(sharedShops()[0].shared.listId)") if A.evaluate("typeof formatCode") == 'function' else None
    lid = A.evaluate("sharedShops()[0].shared.listId")
    ctxB, B = phone(p, b)
    B.evaluate(f"joinSharedList('{lid}')"); settle(B, ms=1500)
    check('B gets the aisles', secs(B, 'Home') == secs(A, 'Home') and secof(B, 'Home', 'Milk') == 'Dairy & eggs')

    # Race: both phones add a new aisle at once; last meta write wins, then healing puts the lost one back.
    A.evaluate("window.__offline = true"); B.evaluate("window.__offline = true")
    add(A, 'Paprika'); add(B, 'Spaghetti'); A.locator('#addInput').blur(); B.locator('#addInput').blur()
    A.wait_for_timeout(300)
    A.evaluate("window.__offline = false"); A.wait_for_timeout(600); B.evaluate("window.__offline = false"); settle(A, B, ms=2500)
    sa, sb = secs(A, 'Home'), secs(B, 'Home')
    print('A', sa); print('B', sb)
    check('After a race both phones have both aisles', 'Herbs & spices' in sa and 'Pasta, rice & grains' in sa and sa == sb)
    check('Both items filed on both phones', secof(A, 'Home', 'Spaghetti') == 'Pasta, rice & grains' and secof(B, 'Home', 'Paprika') == 'Herbs & spices')

    # Deleting an aisle is respected
    A.evaluate("""(() => { const s=state.shops.find(x=>x.name==='Home'); state.tab=s.id; render(); })()""")
    A.click('#btnShop'); A.wait_for_timeout(300)
    hid = A.evaluate("state.shops.find(x=>x.name==='Home').sections.find(s=>s.name==='Household').id")
    A.locator(f'#sheet .secrow.swipe[data-sec="{hid}"] .slide').scroll_into_view_if_needed(); A.wait_for_timeout(200)
    sl = A.locator(f'#sheet .secrow.swipe[data-sec="{hid}"] .slide').bounding_box(); sx, sy = sl['x'] + sl['width'] * .6, sl['y'] + sl['height'] / 2
    A.mouse.move(sx, sy); A.mouse.down()
    for i in range(1, 11): A.mouse.move(sx - 12 * i, sy + 1); A.wait_for_timeout(15)
    A.mouse.up(); A.wait_for_timeout(300)
    A.click(f'#sheet .secrow.swipe[data-sec="{hid}"] .swipe-del'); A.wait_for_timeout(300); A.keyboard.press('Escape'); A.wait_for_timeout(350)
    add(A, 'Kitchen roll'); A.locator('#addInput').blur(); settle(A, B, ms=1200)
    check('Deleted aisle not recreated', 'Household' not in secs(A, 'Home') and secof(A, 'Home', 'Kitchen roll') is None)
    check('Deleted aisle stays deleted on B', 'Household' not in secs(B, 'Home'))

    # Private shop with a non-supermarket name
    A.evaluate("addShop('Big shop'); state.tab = state.shops.find(s=>s.name==='Big shop').id; save(); render();")
    check('Non-supermarket shop starts empty', secs(A, 'Big shop') == [])
    add(A, 'Oregano'); add(A, 'Widget thing'); A.locator('#addInput').blur(); A.wait_for_timeout(200)
    check('Aisle appears on demand', secof(A, 'Big shop', 'Oregano') == 'Herbs & spices' and secof(A, 'Big shop', 'Widget thing') is None)

    # List tab groups by aisle
    A.evaluate("state.tab='list'; save(); render();")
    add(A, 'Bread'); add(A, 'Shampoo'); add(A, 'Gizmo'); A.locator('#addInput').blur(); A.wait_for_timeout(200)
    heads = A.eval_on_selector_all('#list .row.header', 'els => els.map(e => e.dataset.cat)')
    first = A.eval_on_selector_all('#list .row', 'els => els.map(e => e.textContent.trim())')
    check('List tab grouped', heads == ['Bakery', 'Toiletries & beauty'] and first[0].startswith('Gizmo'))

    # Header size
    h = A.evaluate("document.querySelector('#band').getBoundingClientRect().height")
    check('Header compact', h < 120)
    tw = A.evaluate("(() => { const t=document.querySelector('#title'); return t.scrollHeight <= 34; })()")
    check('Title on one line', tw)

    # Trolley needs two taps to empty
    A.evaluate("state.tab = state.shops.find(s=>s.name==='Big shop').id; render();")
    tap(A, item(A, 'Oregano')); A.wait_for_timeout(1200)
    A.evaluate("openTrolleySheet()"); A.wait_for_timeout(400)
    A.click('#sheet [data-act="clearTicked"]'); A.wait_for_timeout(150)
    check('First tap only arms', 'Tap again' in A.locator('#sheet [data-act="clearTicked"]').text_content() and A.evaluate("trolleyItems().length") == 1)
    A.wait_for_timeout(4300)
    check('Disarms after a pause', A.locator('#sheet [data-act="clearTicked"]').text_content() == 'Empty the trolley')
    A.click('#sheet [data-act="clearTicked"]'); A.click('#sheet [data-act="clearTicked"]'); A.wait_for_timeout(400)
    check('Second tap empties', A.evaluate("trolleyItems().length") == 0)
    A.click('#toast [data-act="undo"]'); A.wait_for_timeout(200)
    check('Undo brings it back', A.evaluate("trolleyItems().length") == 1)
    A.screenshot(path=OUT + 'v211-a.png')
    ctxA.close(); ctxB.close()

    # Migration: an old private shop with unfiled items gets filed once on load
    ctx = b.new_context(**p.devices['iPhone 13'], service_workers='block'); M = ctx.new_page()
    M.on('pageerror', lambda e: errors.append(str(e)))
    M.goto(URL)
    M.evaluate("""localStorage.setItem('basket.v1', JSON.stringify({version:1, shops:[{id:'s1', name:'Home', color:'#7B3FA0', sections:[]}],
      items:[{id:'i1', name:'Milk', qty:1, shopId:'s1', sectionId:null, done:false, order:0},{id:'i2', name:'Paprika', qty:1, shopId:'s1', sectionId:null, done:false, order:1}],
      removed:[], history:{}, tab:'s1', lastBackupAt:null}))""")
    M.reload(); M.wait_for_timeout(600)
    check('Old unfiled items get filed', M.evaluate("state.items.map(i => (state.shops[0].sections.find(s=>s.id===i.sectionId)||{}).name)") == ['Dairy & eggs', 'Herbs & spices'])
    M.evaluate("setSection('i1', null)"); M.reload(); M.wait_for_timeout(600)
    check('Filing runs only once', M.evaluate("state.items.find(i=>i.id==='i1').sectionId") is None)
    ctx.close(); b.close()

print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e])
print('Failed:', [n for n, ok in results if not ok])

# ---- 2.1.2: handle needs a hold; a quick swipe on it does nothing ----
with sync_playwright() as p:
    b = p.chromium.launch(); ctx, A = phone(p, b)
    A.evaluate("addShop('Tesco'); state.tab = state.shops[0].id; ['Bananas','Milk','Bread'].forEach(n => addItem(n, {quiet:true})); save(); render();")
    before = A.evaluate("state.items.map(i => [i.name, i.sectionId])")
    g = A.locator(item(A, 'Bananas') + ' .grip').first.bounding_box()
    x, y = g['x'] + g['width']/2, g['y'] + g['height']/2
    A.mouse.move(x, y); A.mouse.down()
    for i in range(1, 12): A.mouse.move(x, y + 30*i); A.wait_for_timeout(12)
    A.mouse.up(); A.wait_for_timeout(300)
    check('Quick swipe on handle moves nothing', A.evaluate("state.items.map(i => [i.name, i.sectionId])") == before and not A.evaluate("document.body.classList.contains('is-dragging')"))
    A.mouse.move(x, y); A.mouse.down(); A.wait_for_timeout(260)
    check('Hold on handle starts a drag', A.evaluate("document.body.classList.contains('is-dragging')"))
    A.mouse.up(); A.wait_for_timeout(200)
    A.locator('#addInput').focus(); A.wait_for_timeout(200)
    check('Quick add is a single scrolling row', A.locator('#suggest .chips.scroll').count() == 1 and A.locator('#suggest .chip').count() <= 8)
    h = A.evaluate("document.querySelector('#dock').getBoundingClientRect().height")
    check('Trolley dock under 120px', h < 120)
    ok = A.evaluate("""() => { const draw = n => packageSvg({ id:'t', name:n }, 100, null); const names = ['Bananas','Carrots','Toilet roll','Red wine','Coke','Dog food','Toothpaste','Eggs','Cheddar','Bin bags'];
      const out = names.map(draw); return new Set(out).size === names.length && !draw('Toilet roll').includes(draw('Bread').slice(60, 120)); }""")
    check('Produce has its own shapes', ok)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

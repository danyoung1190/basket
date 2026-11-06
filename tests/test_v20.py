import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, urllib.request
from playwright.sync_api import sync_playwright
src = open(TESTS + 'test_v15.py').read()
exec(src.split("with sync_playwright() as p:\n    b = p.chromium.launch()\n")[0])

def phone3(p, b, old_home=False, perms=None, welcome=False, reduce=False):
    ctx = b.new_context(**p.devices['iPhone 13'], service_workers='block', permissions=perms or [], reduced_motion='reduce' if reduce else 'no-preference')
    ctx.route('https://www.gstatic.com/firebasejs/**', lambda route, req: route.fulfill(status=200, headers={'Content-Type': 'application/javascript', 'Access-Control-Allow-Origin': '*'}, body=open(FAKE + req.url.split('/')[-1]).read()))
    ctx.route('**/firebase-config.js', lambda route, req: route.fulfill(status=200, content_type='application/javascript', body=CONFIG_JS))
    pg = ctx.new_page()
    pg.add_init_script("Object.defineProperty(navigator, 'standalone', { get: () => true })" + ("; window.__TROLLEY_OLD_HOME = true" if old_home else ""))
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(700)
    if not welcome: pg.evaluate("() => { if (sheetCtx && sheetCtx.type === 'welcome') closeSheet(); }"); pg.wait_for_timeout(350)
    return ctx, pg

def secname(pg, itemname):
    return pg.evaluate(f"""() => {{ const i = state.items.find(x => x.name === {json.dumps(itemname)}); const s = shopById(i.shopId); const sec = s && s.sections.find(x => x.id === i.sectionId); return sec ? sec.name : null; }}""")

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- Welcome ----------
    ctxW, W = phone3(p, b, welcome=True)
    check('Welcome shows on first run', W.locator('#sheet h2:has-text("Welcome to Virtual Trolley")').count() == 1)
    W.screenshot(path=OUT + 'v20-01-welcome.png')
    W.click('#sheet [data-act="welcomeShops"]'); W.wait_for_timeout(300)
    W.click('#sheet [data-v="Tesco"]'); W.click('#sheet [data-v="Aldi"]'); W.click('#sheet [data-act="pickDone"]'); W.wait_for_timeout(300)
    check('Shop picker adds chosen shops', W.evaluate("state.shops.map(s=>s.name)") == ['Tesco', 'Aldi'])
    W.reload(); W.wait_for_timeout(800)
    check('Welcome does not show again', W.evaluate("!sheetCtx"))

    # ---------- Aisles ----------
    check('New supermarket has 24 aisles', W.evaluate("state.shops[0].sections.length") == 24)
    W.evaluate("state.tab = state.shops[0].id; save(); render();")
    for n in ['Paprika', 'origano', 'Tea bags', 'Plain flour', 'Pesto', 'Basmati rice', 'Cheddar', 'Salmon', 'Calpol', 'Gin']:
        add(W, n)
    W.locator('#addInput').blur(); W.wait_for_timeout(200)
    got = {n: secname(W, n) for n in ['Paprika', 'origano', 'Tea bags', 'Plain flour', 'Pesto', 'Basmati rice', 'Cheddar', 'Salmon', 'Calpol', 'Gin']}
    print(got)
    check('Items file into detailed aisles (typo included)', got == {'Paprika':'Herbs & spices','origano':'Herbs & spices','Tea bags':'Tea & coffee','Plain flour':'Baking','Pesto':'Sauces & condiments','Basmati rice':'Pasta, rice & grains','Cheddar':'Cheese','Salmon':'Fish & seafood','Calpol':'Health & medicine','Gin':'Beer, wine & spirits'})

    # Old-style shop upgrade
    W.evaluate("""() => {
      const old = ['Fruit & veg','Bakery','Meat & fish','Fridge','Freezer','Cupboard','Snacks & treats','Drinks','Household','Toiletries','Baby','Pets'];
      const s = { id:'oldshop', name:'Sainsbury\\'s', color:'#7B3FA0', sections: old.map((n, i) => ({ id:'o' + i, name:n })).concat([{ id:'mine', name:'Party stuff' }]) };
      state.shops.push(s);
      const mk = (name, sec) => ({ id:'i_' + name, name, qty:1, shopId:'oldshop', sectionId:sec, done:false, order:0, updatedAt:1 });
      state.items.push(mk('Cumin', 'o5'), mk('Milk', 'o3'), mk('Balloons', 'mine'), mk('Bread', 'o1'), mk('Frozen peas', 'o4'));
      state.tab = 'oldshop'; save(); render(); }""")
    W.click('#btnShop'); W.wait_for_timeout(350)
    check('Old shop offers the new aisles', W.locator('#sheet [data-act="upgradeSections"]').count() == 1)
    W.click('#sheet [data-act="upgradeSections"]'); W.wait_for_timeout(300)
    got = {n: secname(W, n) for n in ['Cumin', 'Milk', 'Balloons', 'Bread', 'Frozen peas']}
    print(got)
    check('Upgrade refiles items and keeps custom sections', got == {'Cumin':'Herbs & spices','Milk':'Dairy & eggs','Balloons':'Party stuff','Bread':'Bakery','Frozen peas':'Frozen'})
    check('Upgrade button gone afterwards', W.locator('#sheet [data-act="upgradeSections"]').count() == 0)
    W.keyboard.press('Escape'); W.wait_for_timeout(300)

    # ---------- Tabs ----------
    W.click('#btnShop'); W.wait_for_timeout(300)
    W.click('#sheet [data-act="toggleHide"]'); W.wait_for_timeout(300)
    check('Hidden shop leaves the top bar', W.locator('.tab:has-text("Sainsbury")').count() == 0 and W.evaluate("state.tab") != 'oldshop')
    W.evaluate("state.tab = state.shops[0].id; save(); render(); hideToast();"); W.wait_for_timeout(300)
    hold(W, item(W, 'Paprika'))
    check('Hidden shop still offered in Send to', W.locator('#sheet [data-act="moveTo"][data-shop="oldshop"]').count() == 1)
    W.keyboard.press('Escape'); W.wait_for_timeout(300)
    W.click('#btnSettings'); W.wait_for_timeout(300); W.click('#sheet [data-act="tabsSheet"]'); W.wait_for_timeout(300)
    W.screenshot(path=OUT + 'v20-02-tabs.png')
    W.click('#sheet [data-act="tabToggle"][data-tab="list"]'); W.wait_for_timeout(250)
    check('List tab can be hidden', W.locator('.tab[data-tab="list"]').count() == 0)
    # hide Tesco and Aldi too: last one must stay
    ids = W.evaluate("state.shops.filter(s=>!s.hidden).map(s=>s.id)")
    for i in ids:
        W.click(f'#sheet [data-act="tabToggle"][data-tab="{i}"]'); W.wait_for_timeout(250)
    check('Cannot hide the last tab', W.locator('.tab:not(.add):not(.meals)').count() == 1 and 'at least one' in W.locator('#toast').text_content())
    W.click('#sheet [data-act="tabToggle"][data-tab="oldshop"]'); W.wait_for_timeout(250)
    first = W.evaluate("state.shops[0].name")
    W.click(f'#sheet [data-act="tabDown"][data-tab="{W.evaluate("state.shops[0].id")}"]'); W.wait_for_timeout(250)
    check('Tabs can be reordered', W.evaluate("state.shops[1].name") == first)
    W.keyboard.press('Escape'); W.wait_for_timeout(300)
    ctxW.close()

    # ---------- Trolley animation ----------
    ctxT, T = phone3(p, b)
    T.evaluate("addShop('Tesco'); state.tab = state.shops[0].id; save(); render();")
    add(T, 'Milk'); add(T, 'Bread'); T.locator('#addInput').blur(); T.wait_for_timeout(300)
    check('Trolley dock shows', T.locator('#dock').is_visible())
    tap(T, item(T, 'Milk')); T.wait_for_timeout(330)
    check('Item flies to the trolley', T.locator('.flyer').count() == 1)
    T.screenshot(path=OUT + 'v20-03-flying.png')
    T.wait_for_timeout(900)
    check('Flyer gone and trolley counts 1', T.locator('.flyer').count() == 0 and T.locator('#dock .tcount').text_content() == '1')
    check('A package sits in the basket', T.locator('#dock .good').count() == 1)
    check('Ticked item left the list', T.locator('#list .row.item').count() == 1)
    check('Item is ticked', T.evaluate("state.items.find(i=>i.name==='Milk').done"))
    T.evaluate("toast('A fairly long message to check it does not cover the trolley', true)"); T.wait_for_timeout(350)
    tb, cb = T.locator('#toast').bounding_box(), T.locator('#dock').bounding_box()
    check('Toast sits above the trolley', tb['y'] + tb['height'] <= cb['y'] + 1)
    T.screenshot(path=OUT + 'v20-04-trolley.png')
    # Swipe up on the trolley
    d = T.locator('#dock').bounding_box()
    T.mouse.move(d['x'] + d['width'] / 2, d['y'] + 50); T.mouse.down()
    for k in range(1, 8): T.mouse.move(d['x'] + d['width'] / 2, d['y'] + 50 - k * 12); T.wait_for_timeout(16)
    T.mouse.up(); T.wait_for_timeout(450)
    check('Swipe up opens the trolley', T.evaluate("sheetCtx && sheetCtx.type") == 'trolley' and T.locator('#sheet .trolley-list .row.item').count() == 1)
    T.screenshot(path=OUT + 'v20-07-inside.png')
    T.click('#sheet .trolley-list .row.item'); T.wait_for_timeout(400)
    check('Tapping an item in the trolley puts it back', not T.evaluate("state.items.find(i=>i.name==='Milk').done") and T.locator('#list .row.item').count() == 2)
    check('Trolley sheet updates in place', T.locator('#sheet .trolley-list .row.item').count() == 0 and 'Nothing in it yet' in T.locator('#sheet').text_content())
    T.keyboard.press('Escape'); T.wait_for_timeout(350)
    # several quick ticks
    tap(T, item(T, 'Milk')); T.wait_for_timeout(120); tap(T, item(T, 'Bread')); T.wait_for_timeout(1500)
    check('Quick ticks both land', T.locator('#dock .tcount').text_content() == '2' and T.locator('#dock .good').count() == 2)
    T.click('#dock'); T.wait_for_timeout(400); T.click('#sheet [data-act="clearTicked"]'); T.click('#sheet [data-act="clearTicked"]'); T.wait_for_timeout(400)
    check('Empty it clears the trolley', T.evaluate("state.items.length") == 0)
    ctxT.close()
    ctxR, R = phone3(p, b, reduce=True)
    add(R, 'Eggs'); R.locator('#addInput').blur(); R.wait_for_timeout(200)
    tap(R, item(R, 'Eggs')); R.wait_for_timeout(200)
    check('Reduced motion: ticks instantly with no flyer', R.locator('.flyer').count() == 0 and R.evaluate("state.items[0].done"))
    ctxR.close()

    # ---------- Move from the old address ----------
    ctxO, O = phone3(p, b, old_home=True, perms=['clipboard-read', 'clipboard-write'])
    O.evaluate("addShop('Tesco'); addShop('B&Q'); state.shops[1].hidden = true; save(); render();")
    add(O, 'Milk x2'); add(O, 'Paprika'); O.locator('#addInput').blur(); O.wait_for_timeout(200)
    # a shared list too
    O.evaluate("(async () => { await createSharedList('Home'); })()"); O.wait_for_timeout(900)
    O.evaluate("state.tab = 'list'; save(); render();")
    check('Old address shows the moved card', O.locator('#moved h2:has-text("new home")').count() == 1)
    O.screenshot(path=OUT + 'v20-05-moved.png')
    O.click('#moved [data-act="moveStart"]'); O.wait_for_timeout(1800)
    code = O.locator('#sheet .bigcode').text_content().strip()
    print('move code', code)
    check('Move code shown', code.startswith('MOVE-'))
    clip = O.evaluate("navigator.clipboard.readText()")
    check('Move code copied automatically', clip == code)
    O.screenshot(path=OUT + 'v20-06-moveready.png')
    src_state = O.evaluate("JSON.parse(JSON.stringify(state))")
    ctxN, N = phone3(p, b, perms=['clipboard-read', 'clipboard-write'], welcome=True)
    N.evaluate("t => navigator.clipboard.writeText(t)", code)
    N.click('#sheet [data-act="movePaste"]'); N.wait_for_timeout(2200)
    st = N.evaluate("JSON.parse(JSON.stringify(state))")
    check('Lists arrive on the new address', sorted(i['name'] for i in st['items']) == sorted(i['name'] for i in src_state['items']) and len(st['shops']) == 3)
    check('Hidden tab and quantities preserved', any(s['name'] == 'B&Q' and s.get('hidden') for s in st['shops']) and any(i['name'] == 'Milk' and i['qty'] == 2 for i in st['items']))
    check('Shared list reconnects after move', N.evaluate("live.size") == 1)
    check('Move code used up', stats()['count'] >= 0 and N.evaluate("(async()=>{ const s = await fb.fs.getDocFromServer(transferRef(" + json.dumps(code.replace('MOVE-','').replace('-','')) + ")); return s.exists(); })()") == False)
    # Using it again fails clearly
    N.evaluate("t => navigator.clipboard.writeText(t)", code)
    N.click('#btnSettings'); N.wait_for_timeout(300); N.click('#sheet [data-act="movePaste"]'); N.wait_for_timeout(1500)
    check('Reused move code explained', 'already been used' in N.locator('#sheet .err').text_content())
    ctxN.close(); ctxO.close()
    b.close()

print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e])
print('Failed:', [n for n, ok in results if not ok])

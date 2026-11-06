import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_basket.py').read().split('with sync_playwright()')[0])

def secname(st, it):
    for sh in st['shops']:
        for s in sh['sections']:
            if s['id'] == it['sectionId']: return s['name']
    return None

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**p.devices['iPhone 13'])
    page = ctx.new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL); page.evaluate('localStorage.clear()'); page.reload(); page.wait_for_timeout(400)

    # Quick add chips on a fresh install
    page.click('#addInput'); page.wait_for_timeout(150)
    check('Quick add staples shown on fresh install', page.locator('#suggest .chip').count() == 8)
    page.screenshot(path=OUT + 'v11-01-quickadd.png')
    page.locator('#addInput').blur()

    # New shop gets standard sections
    tap(page, '.tab.add'); page.wait_for_timeout(350); page.click('#sheet [data-act="menuShop"]'); page.wait_for_timeout(350)
    page.click('#sheet [data-v="Tesco"]'); page.wait_for_timeout(400)
    st = state(page)
    check('New shop has 24 standard sections', len(st['shops'][0]['sections']) == 24)
    check('Empty sections hidden', page.locator('#list .row.header:visible').count() == 0)

    # Catalogue suggestion while typing
    page.click('#addInput'); page.type('#addInput', 'crois'); page.wait_for_timeout(150)
    check('Typing "crois" suggests Croissants', page.locator('#suggest [data-add="Croissants"]').count() == 1)
    page.screenshot(path=OUT + 'v11-02-typing.png')
    page.click('#suggest [data-add="Croissants"]'); page.wait_for_timeout(150)

    # Auto-filing in shop
    for n in ['Semi skimmed milk', 'Frozen peas', 'Bananas', 'Chicken thighs', 'Toilet roll', 'Creme fraiche', 'Widgets']:
        add(page, n)
    page.locator('#addInput').fill(''); page.locator('#addInput').blur(); page.wait_for_timeout(200)
    st = state(page)
    got = {i['name']: secname(st, i) for i in st['items']}
    print(got)
    check('Croissants -> Bakery', got['Croissants'] == 'Bakery')
    check('Semi skimmed milk -> Dairy & eggs', got['Semi skimmed milk'] == 'Dairy & eggs')
    check('Frozen peas -> Frozen', got['Frozen peas'] == 'Frozen')
    check('Bananas -> Fruit & veg', got['Bananas'] == 'Fruit & veg')
    check('Chicken thighs -> Meat & poultry', got['Chicken thighs'] == 'Meat & poultry')
    check('Toilet roll -> Household', got['Toilet roll'] == 'Household')
    check('Creme fraiche -> Dairy & eggs', got['Creme fraiche'] == 'Dairy & eggs')
    check('Unknown item unsectioned', got['Widgets'] is None)
    page.screenshot(path=OUT + 'v11-03-tesco.png', full_page=True)

    # Drag Widgets into a hidden empty section (Cupboard)
    page.mouse.move(0, 0)
    g = page.locator(item(page, 'Widgets') + ' .grip').first.bounding_box()
    sx, sy = g['x'] + 25, g['y'] + 27
    page.mouse.move(sx, sy); page.mouse.down(); page.wait_for_timeout(260)
    hdr = page.locator('.row.header:has-text("Baking")').bounding_box()
    print('HDR', hdr, 'viewport', page.viewport_size, 'grip', g)
    check('Empty sections appear while dragging', hdr is not None and hdr['height'] > 0)
    # Like a real finger: drag to the bottom edge, let it scroll until Cupboard is in view, then drop under it.
    for i in range(1, 15):
        page.mouse.move(sx, sy + (600 - sy) * i / 14); page.wait_for_timeout(20)
    for _ in range(200):
        hdr = page.locator('.row.header:has-text("Baking")').bounding_box()
        if hdr['y'] < 420: break
        page.wait_for_timeout(16)
    ty = hdr['y'] + hdr['height'] + 27  # centre of the gap under the heading
    for i in range(1, 10):
        page.mouse.move(sx, 600 + (ty - 600) * i / 9); page.wait_for_timeout(20)
    page.wait_for_timeout(100); page.mouse.up(); page.wait_for_timeout(300)
    st = state(page)
    w = [i for i in st['items'] if i['name'] == 'Widgets'][0]
    print('Widgets landed in', secname(st, w))
    check('Widgets dragged into Baking', secname(st, w) == 'Baking')

    # Her override wins: move Bananas to Snacks & treats, remove, re-add -> Snacks & treats
    hold(page, item(page, 'Bananas'))
    sid = [s['id'] for s in st['shops'][0]['sections'] if s['name'] == 'Snacks & sweets'][0]
    page.click('#sheet [data-act="allSecs"]'); page.wait_for_timeout(150)
    page.click(f'#sheet [data-act="setSection"][data-sec="{sid}"]'); page.wait_for_timeout(350)
    hold(page, item(page, 'Bananas'))
    page.click('#sheet [data-act="removeItem"]'); page.wait_for_timeout(300)
    add(page, 'Bananas'); page.locator('#addInput').blur(); page.wait_for_timeout(150)
    st = state(page)
    bn = [i for i in st['items'] if i['name'] == 'Bananas'][0]
    check('Her filing remembered over catalogue', secname(st, bn) == 'Snacks & sweets')

    # From List, send to a shop -> auto-filed
    tap(page, '.tab[data-tab="list"]'); page.wait_for_timeout(200)
    add(page, 'Cheddar'); page.locator('#addInput').blur(); page.wait_for_timeout(150)
    hold(page, item(page, 'Cheddar'))
    tid = st['shops'][0]['id']
    page.click(f'#sheet [data-act="moveTo"][data-shop="{tid}"]'); page.wait_for_timeout(350)
    st = state(page)
    ch = [i for i in st['items'] if i['name'] == 'Cheddar'][0]
    check('Sent from List lands in Cheese', ch['shopId'] == tid and secname(st, ch) == 'Cheese')

    # Tick and undo still fine
    tap(page, f'.tab[data-tab="{tid}"]'); page.wait_for_timeout(200)
    tap(page, item(page, 'Cheddar')); page.wait_for_timeout(500)
    check('Tick works', [i for i in state(page)['items'] if i['name'] == 'Cheddar'][0]['done'])

    # Old shop without sections: Add standard sections files existing items
    page.evaluate("""() => { const s = { id:'old', name:'Aldi', color:'#2D5BC9', sections:[] }; state.shops.push(s);
      state.items.push({ id:'x1', name:'Bread', shopId:'old', sectionId:null, done:false, order:0 }); save(); render(); }""")
    tap(page, '.tab[data-tab="old"]'); page.wait_for_timeout(200)
    page.click('#btnShop'); page.wait_for_timeout(350)
    page.click('#sheet [data-act="addStandard"]'); page.wait_for_timeout(350)
    st = state(page)
    br = [i for i in st['items'] if i['id'] == 'x1'][0]
    check('Add standard sections files existing items', secname(st, br) == 'Bakery')
    page.keyboard.press('Escape'); page.wait_for_timeout(300)

    # Category matcher spot checks
    res = page.evaluate("""() => ['Milk chocolate','Hot chocolate','Coconut milk','Rice','4 pints milk','Tomato soup','Chickpeas','Scotch eggs','birthday candles','Gin','Crème fraîche'].map(n => [n, categoryFor(n)])""")
    print(res)
    exp = {'Milk chocolate':'Snacks & sweets','Hot chocolate':'Tea & coffee','Coconut milk':'Tins & jars','Rice':'Pasta, rice & grains','4 pints milk':'Dairy & eggs','Chickpeas':'Tins & jars','Scotch eggs':'Chilled & deli','birthday candles':'Household','Gin':'Beer, wine & spirits','Crème fraîche':'Dairy & eggs'}
    check('Matcher spot checks', all(dict(res)[k] == v for k, v in exp.items()))
    b.close()

print('\nConsole errors:', errors)
print('Failed:', [n for n, ok in results if not ok])

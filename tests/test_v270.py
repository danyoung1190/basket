import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, time
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
BAR = WORK
import subprocess as _sp
for _c in ('5000157024671', '5012345678900'):   # fake camera videos, built from small pictures (the videos are huge)
    if not _os.path.exists(f'{WORK}cam_{_c}.y4m'):
        _sp.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', f'{TESTS}assets/frame_{_c}.png', '-t', '2', '-r', '10', '-pix_fmt', 'yuv420p', f'{WORK}cam_{_c}.y4m'], check=True)
BEANS = {'code':'5000157024671','status':1,'status_verbose':'product found','product':{'brands':'Heinz','product_name':'Beanz','generic_name':'Baked beans in tomato sauce','categories_tags_en':['en:Plant-based foods','en:Canned foods','en:Legumes','en:Baked beans'],'quantity':'415 g'}}
def cam_browser(p, code):
    return p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', f'--use-file-for-fake-video-capture={BAR}cam_{code}.y4m'])
def until(pg, js, secs=12):
    t = time.time()
    while time.time() - t < secs:
        if pg.evaluate(js): return True
        pg.wait_for_timeout(200)
    return False
def off(route, req, body, status=200):
    route.fulfill(status=status, headers={'Content-Type':'application/json', 'Access-Control-Allow-Origin':'*'}, body=json.dumps(body))
with sync_playwright() as p:
    # 1. A product Open Food Facts knows: offered as the catalogue name, remembered for next time
    b = cam_browser(p, '5000157024671'); ctx, A = phone(p, b); ctx.grant_permissions(['camera'])
    calls = []
    ctx.route('https://world.openfoodfacts.org/**', lambda r, q: (calls.append(q.url), off(r, q, BEANS)))
    A.evaluate("state.nameAsked=true; addShop('Tesco'); state.tab = state.shops[0].id; save(); render();")
    check('Scan button shows', A.locator('#scanBtn').is_visible())
    A.click('#scanBtn')
    ok = until(A, "sheetCtx && sheetCtx.type === 'barcodeChoice'")
    check('Reads the barcode from the camera and looks it up', ok and '5000157024671' in (calls[0] if calls else ''))
    opts = A.eval_on_selector_all('#sheet [data-mact="bpick"]', 'els => els.map(e => e.dataset.name)')
    print(A.text_content('#sheet h2'), opts)
    check('Offers the plain name first, then the product', opts[:1] == ['Baked beans'] and any('Heinz' in o for o in opts))
    A.click('#sheet [data-mact="bpick"]'); A.wait_for_timeout(600)
    check('Added to Tesco', A.evaluate("itemsIn(state.shops[0].id).map(i=>i.name)") == ['Baked beans'])
    check('Barcode remembered', A.evaluate("state.barcodes['5000157024671']") == 'Baked beans')
    A.wait_for_timeout(2500)
    check('Jar still in view: not added twice', A.evaluate("itemsIn(state.shops[0].id)[0].qty || 1") == 1)
    # moving it away and back (simulate: forget the last sighting) makes it x2, with no lookup
    n_calls = len(calls)
    A.evaluate("lastBarcode = { code:'', seen:0 }"); A.wait_for_timeout(1500)
    check('Second jar makes it x2, instantly', A.evaluate("itemsIn(state.shops[0].id)[0].qty") == 2 and len(calls) == n_calls)
    check('Says what happened', 'Baked beans ×2' in A.text_content('#sheet .scanlog'))
    A.click('#sheet [data-mact="bdone"]'); A.wait_for_timeout(300)
    check('Done turns the camera off', A.evaluate("bscan === null"))
    b.close()
    # 2. Unknown to Open Food Facts: she types a name, it's remembered
    b = cam_browser(p, '5012345678900'); ctx, A = phone(p, b); ctx.grant_permissions(['camera'])
    ctx.route('https://world.openfoodfacts.org/**', lambda r, q: off(r, q, {'code':'5012345678900','status':0,'status_verbose':'product not found'}, 404))
    A.evaluate("state.nameAsked=true;"); A.click('#scanBtn')
    until(A, "sheetCtx && sheetCtx.type === 'barcodeChoice'")
    check('Unknown product asks for a name', "isn't known yet" in A.text_content('#sheet h2'))
    A.fill('#sheet form[data-mform="bname"] input', "Nan's chutney"); A.press('#sheet form[data-mform="bname"] input', 'Enter'); A.wait_for_timeout(500)
    check('Typed name added and remembered', A.evaluate("state.items.some(i=>i.name===\"Nan's chutney\") && state.barcodes['5012345678900'] === \"Nan's chutney\""))
    A.click('#sheet [data-mact="bdone"]')
    # 3. No signal: says so, still lets her name it
    ctx.unroute('https://world.openfoodfacts.org/**'); ctx.route('https://world.openfoodfacts.org/**', lambda r, q: r.abort())
    A.evaluate("delete state.barcodes['5012345678900']; lastBarcode = { code:'', seen:0 }; save();")
    A.click('#scanBtn'); until(A, "sheetCtx && sheetCtx.type === 'barcodeChoice'")
    check('No signal: explains and asks for a name', "Couldn't look it up" in A.text_content('#sheet h2'))
    b.close()
    # 4. Recipe library
    b = p.chromium.launch(); ctx, A = phone(p, b)
    A.evaluate("""() => { state.nameAsked = true; const d = n => { const x = new Date(); x.setDate(x.getDate() + n); return dayKey(x); };
      state.meals = [
        { id:'a1', date:d(-60), name:'Chilli', imgs:[], ing:'1 onion' }, { id:'a2', date:d(-20), name:'Chilli', imgs:[], ing:'' },
        { id:'b1', date:d(-10), name:'Fish pie', imgs:[], ing:'' }, { id:'c1', date:d(-90), name:'Lasagne', imgs:[], ing:'' },
        { id:'d1', date:d(3), name:'Roast', imgs:[], ing:'' }, { id:'e1', date:d(-3), name:'chilli', imgs:[], ing:'' } ];
      save(); view = 'meals'; render(); }""")
    check('Library button shows how many recipes', A.locator('#mealsView [data-mact="lib"] .n').text_content() == '4')
    A.click('#mealsView [data-mact="lib"]'); A.wait_for_timeout(300)
    names = A.eval_on_selector_all('#sheet .librow strong', 'els => els.map(e => e.textContent)')
    print(names, A.eval_on_selector_all('#sheet .librow small', 'els => els.map(e => e.textContent)'))
    check('One entry per meal, longest-ago first, planned ones last', [n.lower() for n in names] == ['lasagne', 'fish pie', 'chilli', 'roast'])
    check('Counts times had and says when', 'had 3 times' in A.locator('#sheet .librow:has-text("hilli") small').text_content() and 'Planned for' in A.locator('#sheet .librow:has-text("Roast") small').text_content())
    A.click('#sheet [data-mact="libSort"][data-v="often"]'); A.wait_for_timeout(150)
    check('Most often puts chilli first', A.locator('#sheet .librow strong').first.text_content().lower() == 'chilli')
    A.fill('#sheet [data-libq]', 'fish'); A.wait_for_timeout(150)
    check('Search filters as she types', A.locator('#sheet .librow').count() == 1)
    A.fill('#sheet [data-libq]', ''); A.wait_for_timeout(150)
    A.locator('#sheet .librow:has-text("hilli") [data-mact="libAgain"]').click(); A.wait_for_timeout(300)
    check('Plan uses the copy with the ingredients', A.evaluate("mealDraft && mealDraft.ing") == '1 onion')
    A.locator('#sheet [data-mact="day"]').nth(9).click(); A.click('#sheet form[data-mform="meal"] button[type="submit"]'); A.wait_for_timeout(300)
    check('Planned again', A.evaluate("state.meals.filter(m => fold(m.name) === 'chilli').length") == 4)
    b.close()
print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e and 'ERR_FAILED' not in e])
print('Failed:', [n for n, ok in results if not ok])

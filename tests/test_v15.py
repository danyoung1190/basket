import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, urllib.request
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_basket.py').read().split('with sync_playwright()')[0])
FAKE = TESTS + 'fakefb/'
urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766/reset', data=b'{}', method='POST')).read()
def stats(): return json.loads(urllib.request.urlopen('http://127.0.0.1:8766/stats').read())

CONFIG_JS = "window.BASKET_FIREBASE = { apiKey:'fake', projectId:'fake-basket' };"
def phone(p, b, standalone=True, configured=True):
    ctx = b.new_context(**p.devices['iPhone 13'], service_workers='block')
    ctx.route('https://www.gstatic.com/firebasejs/**', lambda route, req: route.fulfill(status=200, headers={'Content-Type': 'application/javascript', 'Access-Control-Allow-Origin': '*'}, body=open(FAKE + req.url.split('/')[-1]).read()))
    ctx.route('**/firebase-config.js', lambda route, req: route.fulfill(status=200, content_type='application/javascript', body=CONFIG_JS if configured else 'window.BASKET_FIREBASE = {};'))
    pg = ctx.new_page()
    if standalone: pg.add_init_script("Object.defineProperty(navigator, 'standalone', { get: () => true })")
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(700); pg.evaluate("() => { if (sheetCtx && sheetCtx.type === 'welcome') closeSheet(); }"); pg.wait_for_timeout(350)
    return ctx, pg

def settle(*pgs, ms=900):
    for pg in pgs: pg.wait_for_timeout(ms)

def names(pg, shop_name):
    return pg.evaluate(f"""() => {{ const s = state.shops.find(x => x.name === '{shop_name}'); return s ? itemsIn(s.id).filter(i=>!i.done).map(i => i.name + (i.qty>1?' x'+i.qty:'')).sort() : null; }}""")

with sync_playwright() as p:
    b = p.chromium.launch()

    # Not configured: clear message, nothing breaks
    ctxN, N = phone(p, b, configured=False)
    N.click('#btnSettings'); N.wait_for_timeout(300); N.click('#sheet [data-act="shareHub"]'); N.wait_for_timeout(300)
    check('Unconfigured copy explains itself', "isn't set up" in N.locator('#sheet').text_content())
    ctxN.close()

    ctxA, A = phone(p, b)
    # Create on A: just a name
    A.click('#btnSettings'); A.wait_for_timeout(300); A.click('#sheet [data-act="shareHub"]'); A.wait_for_timeout(300)
    A.click('#sheet [data-act="createStart"]'); A.wait_for_timeout(300)
    A.fill('#sheet input.field', 'Home'); A.press('#sheet input.field', 'Enter'); A.wait_for_timeout(1200)
    code = A.locator('#sheet .bigcode').text_content().strip()
    print('code', code)
    check('Short code shown with QR', code.startswith('TRLY-') and len(code) == 24 and A.locator('#sheet .qr svg').count() == 1)
    A.screenshot(path=OUT + 'v15-01-code.png')
    A.keyboard.press('Escape'); A.wait_for_timeout(350)
    check('Home tab with cloud icon', A.locator('.tab:has-text("Home") svg.cloud').count() == 1)
    check('Status Live', 'Live' in A.locator('#subtitle').text_content())

    add(A, 'Milk x2'); add(A, 'Bread'); A.locator('#addInput').blur(); settle(A)
    check('Items written to store', stats()['count'] == 3)

    # Join on B
    ctxB, B = phone(p, b)
    B.click('#btnSettings'); B.wait_for_timeout(300); B.click('#sheet [data-act="shareHub"]'); B.wait_for_timeout(300)
    B.click('#sheet [data-act="joinStart"]'); B.wait_for_timeout(300)
    B.fill('#sheet input.code', 'nonsense'); B.click('#sheet button[type="submit"]'); B.wait_for_timeout(400)
    check('Bad code rejected', 'No Virtual Trolley code' in B.locator('#sheet .err').text_content())
    B.fill('#sheet input.code', 'BSKT-' + 'A' * 4 + '-' + 'A' * 4 + '-' + 'A' * 4 + '-' + 'A' * 4); B.click('#sheet button[type="submit"]'); B.wait_for_timeout(600)
    check('Unknown code rejected', 'No list has that code' in B.locator('#sheet .err').text_content())
    B.fill('#sheet input.code', code.lower().replace('-', ' ')); B.click('#sheet button[type="submit"]'); settle(B, ms=1500)
    check('B joined (lower case, spaces forgiven) and sees items', names(B, 'Home') == ['Bread', 'Milk x2'])
    B.screenshot(path=OUT + 'v15-02-joined.png')

    # Live two-way
    add(B, 'Eggs'); B.locator('#addInput').blur()
    tap(B, item(B, 'Milk')); B.wait_for_timeout(500)
    add(A, 'Butter'); A.locator('#addInput').blur()
    settle(A, B, ms=1500)
    check('A sees Eggs, Butter, Milk ticked, live', names(A, 'Home') == ['Bread', 'Butter', 'Eggs'] and A.evaluate("state.items.find(i=>i.name==='Milk').done"))
    check('B sees Butter live', names(B, 'Home') == ['Bread', 'Butter', 'Eggs'])

    # Removal lands in other phone's bin
    hold(B, item(B, 'Bread')); B.click('#sheet [data-act="removeItem"]'); settle(A, B, ms=1200)
    check('Removal reaches A', names(A, 'Home') == ['Butter', 'Eggs'])
    check('Removed item in A recently removed', any(r['name'] == 'Bread' for r in state(A)['removed']))
    check('B bin has Bread once', sum(1 for r in state(B)['removed'] if r['name'] == 'Bread') == 1)

    # Move out to private shop on A
    A.evaluate("addShop('Tesco'); save(); render();")
    hold(A, item(A, 'Eggs'))
    tid = A.evaluate("state.shops.find(s=>s.name==='Tesco').id")
    A.click(f'#sheet [data-act="moveTo"][data-shop="{tid}"]'); settle(A, B, ms=1200)
    check('Moved-out item leaves shared list on B', names(B, 'Home') == ['Butter'])
    check('Eggs private on A', A.evaluate(f"itemsIn('{tid}').map(i=>i.name)") == ['Eggs'])

    # Sections + rename sync
    A.evaluate("const s=state.shops.find(x=>x.name==='Home'); addSection(s.id,'Fridge'); save(); render();"); settle(A, B, ms=1200)
    check('Section reaches B', B.evaluate("state.shops.find(x=>x.name==='Home').sections.map(s=>s.name)") == A.evaluate("state.shops.find(x=>x.name==='Home').sections.map(s=>s.name)") and 'Fridge' in B.evaluate("state.shops.find(x=>x.name==='Home').sections.map(s=>s.name)"))
    B.evaluate("const s=state.shops.find(x=>x.name==='Home'); s.name='Family'; save(); render();"); settle(A, B, ms=1200)
    check('Rename reaches A', A.evaluate("state.shops.some(x=>x.name==='Family')"))

    # No churn
    w = stats()['writes']; settle(A, B, ms=1500)
    check('No writes when idle', stats()['writes'] == w)

    # Offline on B: edit queues, status says so, then flushes
    B.evaluate("window.__offline = true")
    add(B, 'Cheese'); B.locator('#addInput').blur(); settle(B, ms=800)
    check('Offline status shown', 'waiting' in B.locator('#subtitle').text_content() or 'Offline' in B.locator('#subtitle').text_content())
    B.click('#btnSync'); B.wait_for_timeout(500)
    check('Refresh offline explains', 'No signal' in B.locator('#toast').text_content())
    settle(A, ms=600)
    check('A has not got Cheese yet', 'Cheese' not in names(A, 'Family'))
    B.evaluate("window.__offline = false"); settle(A, B, ms=1500)
    check('Queued change arrives after reconnect', 'Cheese' in names(A, 'Family'))
    check('Status back to Live', 'Live' in B.locator('#subtitle').text_content())

    # Undo works across sync
    hold(A, item(A, 'Cheese')); A.click('#sheet [data-act="removeItem"]'); A.wait_for_timeout(200)
    A.click('#toast [data-act="undo"]'); settle(A, B, ms=1500)
    check('Undo of removal restores on both', 'Cheese' in names(A, 'Family') and 'Cheese' in names(B, 'Family'))

    # Reload A keeps the shared list and reconnects
    A.reload(); settle(A, ms=1500)
    check('Reload reconnects', 'Cheese' in names(A, 'Family') and A.evaluate("[...live.values()].length") == 1)

    # Leave on B
    B.evaluate("state.tab = state.shops.find(x=>x.name==='Family').id; save(); render();")
    B.click('#btnShop'); B.wait_for_timeout(300)
    B.click('#sheet [data-act="deleteShop"]'); B.click('#sheet [data-act="deleteShop"]'); settle(B)
    check('B left', names(B, 'Family') is None and B.evaluate("live.size") == 0)
    settle(A); check('A unaffected', 'Cheese' in names(A, 'Family'))

    # Safari link + app link
    lid = parse = A.evaluate("sharedShops()[0].shared.listId")
    ctxS, S = phone(p, b, standalone=False); S.goto('about:blank'); S.goto(URL + '#join=' + lid); S.wait_for_timeout(500)
    check('Safari link shows the code and steps', lid[:4] in S.locator('#sheet .bigcode').text_content().replace('-', ''))
    S.screenshot(path=OUT + 'v15-03-safari.png'); ctxS.close()
    ctxJ, J = phone(p, b); J.goto('about:blank'); J.goto(URL + '#join=' + lid); J.wait_for_timeout(500)
    check('App link prefills', J.locator('#sheet input.code').input_value().replace('-', '') == 'TRLY' + lid)
    J.click('#sheet button[type="submit"]'); settle(J, ms=1500)
    check('Join via link works', 'Cheese' in (names(J, 'Family') or []))
    ctxJ.close()

    # Auth failure surfaces
    ctxF, F = phone(p, b)
    F.evaluate("window.__authFail = true")
    F.click('#btnSettings'); F.wait_for_timeout(300); F.click('#sheet [data-act="shareHub"]'); F.wait_for_timeout(300)
    F.click('#sheet [data-act="joinStart"]'); F.wait_for_timeout(300)
    F.fill('#sheet input.code', code); F.click('#sheet button[type="submit"]'); F.wait_for_timeout(600)
    check('Auth problem explained', 'Anonymous sign-in' in F.locator('#sheet .err').text_content())
    ctxF.close()
    b.close()

print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e])
print('Failed:', [n for n, ok in results if not ok])

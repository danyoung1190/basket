import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_basket.py').read().split('with sync_playwright()')[0])

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**p.devices['iPhone 13'])
    page = ctx.new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL); page.evaluate('localStorage.clear()'); page.reload(); page.wait_for_timeout(400)

    # Parsing
    res = page.evaluate("""() => ['Chicken x4','chicken x 4','Chicken ×4','4x chicken','4 x Chicken','2 litre milk','Box','Coke x 12','Eggs x0','Weetabix 24','Weetabix x 24','Box x2','Chickenx4'].map(s => { const r = parseQty(s); return [s, r.name, r.qty]; })""")
    print(res)
    exp = {'Chicken x4':('Chicken',4),'chicken x 4':('chicken',4),'Chicken ×4':('Chicken',4),'4x chicken':('chicken',4),'4 x Chicken':('Chicken',4),
           '2 litre milk':('2 litre milk',None),'Box':('Box',None),'Coke x 12':('Coke',12),'Eggs x0':('Eggs x0',None),'Weetabix 24':('Weetabix 24',None),'Weetabix x 24':('Weetabix',24),'Box x2':('Box',2),'Chickenx4':('Chickenx4',None)}
    check('Quantity parsing', all((r[1], r[2]) == exp[r[0]] for r in res))

    # Add with quantity, then change by retyping, then stepper
    add(page, 'Chicken breasts x4')
    st = state(page); ch = st['items'][0]
    check('Added with qty 4', ch['name'] == 'Chicken breasts' and ch['qty'] == 4)
    check('Badge shows ×4', page.locator('.row.item .qty').first.text_content() == '×4')
    add(page, 'chicken breasts x6')
    check('Retyping with x6 updates qty', state(page)['items'][0]['qty'] == 6 and len(state(page)['items']) == 1)
    page.locator('#addInput').blur(); page.wait_for_timeout(150)
    hold(page, item(page, 'Chicken breasts'))
    page.click('#sheet [data-act="qtyDown"]'); page.click('#sheet [data-act="qtyDown"]'); page.wait_for_timeout(100)
    check('Stepper lowers qty to 4', state(page)['items'][0]['qty'] == 4 and page.locator('#sheet .stepper output').text_content() == '4')
    page.screenshot(path=OUT + 'v12-01-sheet.png')
    page.keyboard.press('Escape'); page.wait_for_timeout(350)

    # Share text includes quantity (clipboard fallback: stub navigator.share)
    page.evaluate("() => { window.__shared = null; navigator.share = d => { window.__shared = d.text; return Promise.resolve(); }; }")
    page.click('#btnShare'); page.wait_for_timeout(100)
    check('Share includes ×4', '×4' in (page.evaluate('window.__shared') or ''))

    # Purchase tracking on tick/untick
    tap(page, item(page, 'Chicken breasts')); page.wait_for_timeout(500)
    h = state(page)['history']['chicken breasts']
    check('Tick records a purchase', len(h['buys']) == 1)
    page.wait_for_timeout(900); page.click('#dock'); page.wait_for_timeout(400)
    page.click('#sheet .trolley-list .row.item'); page.wait_for_timeout(300)
    page.keyboard.press('Escape'); page.wait_for_timeout(350)
    h = state(page)['history']['chicken breasts']
    check('Untick removes that purchase', len(h['buys']) == 0)

    # Due again: fake a history of weekly milk and fortnightly bin bags
    page.evaluate("""() => {
      const now = Date.now(), D = 864e5;
      state.history['milk'] = { name:'Milk', count:5, lastAt:now - 8*D, shopId:null, sectionId:null, qty:2, buys:[now-36*D, now-29*D, now-22*D, now-15*D, now-8*D] };
      state.history['bin bags'] = { name:'Bin bags', count:3, lastAt:now - 3*D, shopId:null, sectionId:null, buys:[now-31*D, now-17*D, now-3*D] };
      state.history['eggs'] = { name:'Eggs', count:3, lastAt:now - 10*D, shopId:null, sectionId:null, buys:[now-30*D, now-20*D, now-10*D] };
      state.history['bread'] = { name:'Bread', count:1, lastAt:now - 30*D, buys:[now-30*D] };
      save(); render(); }""")
    names = page.eval_on_selector_all('#dueBar .chip', 'els => els.map(e => e.textContent)')
    print('Due:', names)
    check('Weekly milk is due (with usual qty)', 'Milk ×2' in names)
    check('Bin bags not due yet', not any(n.startswith('Bin bags') for n in names))
    check('Single purchase is not enough to predict', not any(n.startswith('Bread') for n in names))
    page.screenshot(path=OUT + 'v12-02-due.png')
    page.click('[data-act="dueAll"]'); page.wait_for_timeout(200)
    milk = [i for i in state(page)['items'] if i['name'] == 'Milk']
    check('Add all adds Milk ×2', milk and milk[0]['qty'] == 2)
    check('Due strip empties once added', page.locator('#dueBar .chip').count() == 0)
    page.click('#toast [data-act="undo"]'); page.wait_for_timeout(150)
    check('Undo add all', not any(i['name'] == 'Milk' for i in state(page)['items']))
    page.click('[data-act="dueHide"]'); page.wait_for_timeout(150)
    check('Not today hides strip', page.locator('#dueBar .due').count() == 0)

    # Stats line
    page.evaluate("state.dueHiddenUntil = null; save(); render();")
    add(page, 'Milk'); page.locator('#addInput').blur(); page.wait_for_timeout(150)
    hold(page, item(page, 'Milk'))
    txt = page.locator('#sheet .stats').text_content()
    print('Stats:', txt)
    check('Stats line shows pattern', 'Bought 5 times, about every 7 days' in txt)
    page.screenshot(path=OUT + 'v12-03-stats.png')
    b.close()

print('\nConsole errors:', errors)
print('Failed:', [n for n, ok in results if not ok])

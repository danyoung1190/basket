import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
def row(pg, n): return pg.locator(f'.row.item:has(.name:text-is("{n}"))')
with sync_playwright() as p:
    b = p.chromium.launch()
    # ---- scroll position survives a tick ----
    ctx, S = phone(p, b)
    S.evaluate("""() => { addShop('Tesco'); state.tab = state.shops[0].id;
      ['Apples','Bananas','Carrots','Broccoli','Bread','Baguette','Chicken','Beef mince','Salmon','Milk','Eggs','Butter','Yoghurt','Cheddar','Brie','Ham','Pizza','Peas','Ice cream','Oregano','Paprika','Pasta','Rice','Baked beans','Ketchup','Flour','Sugar','Cornflakes','Tea bags','Coffee','Crisps','Chocolate','Coke','Water','Red wine','Beer','Bin bags','Shampoo','Toothpaste','Dog food'].forEach(n => addItem(n, {quiet:true})); save(); render(); }""")
    S.wait_for_timeout(300); S.evaluate("window.scrollTo(0, 1100)"); S.wait_for_timeout(300)
    y0 = S.evaluate("window.scrollY"); target = S.evaluate("""(() => { const r = [...document.querySelectorAll('.row.item')].find(r => { const b = r.getBoundingClientRect(); return b.top > 250 && b.bottom < innerHeight - 200; }); return r.querySelector('.name').textContent; })()""")
    tap(S, item(S, target)); S.wait_for_timeout(1500)
    y1 = S.evaluate("window.scrollY")
    print('scroll', y0, y1, target)
    check('Ticking does not jump to the top', y0 > 500 and abs(y1 - y0) < 80)
    ctx.close()

    # ---- names and New ----
    ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("createSharedList('Home')"); A.wait_for_timeout(1500); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    lid = A.evaluate("sharedShops()[0].shared.listId")
    check('Shared list shows a quiet name prompt, no popup', A.locator('#sortBar .namebar').count() == 1 and A.locator('#sheet.open').count() == 0)
    A.click('#sortBar [data-act="askName"]'); A.wait_for_timeout(300)
    check('Tapping it asks for the name', A.locator('#sheet form[data-form="myName"]').count() == 1)
    A.fill('#sheet form[data-form="myName"] input', 'Dan'); A.press('#sheet form[data-form="myName"] input', 'Enter'); A.wait_for_timeout(300)
    add(A, 'Milk'); A.locator('#addInput').blur(); settle(A)
    B.evaluate(f"joinSharedList('{lid}')"); settle(B, ms=1600)
    B.evaluate("state.me = 'Liv'; state.nameAsked = true; save();")
    check('B sees who added Milk', row(B, 'Milk').locator('.by').text_content() == 'Dan')
    check('A does not see its own name', row(A, 'Milk').locator('.by').count() == 0)
    B.click('#sortBar [data-act="nameLater"]'); B.wait_for_timeout(200)
    check('Prompt can be dismissed', B.locator('#sortBar .namebar').count() == 0)
    # B adds while A is "away"
    A.evaluate("noteHidden(); hiddenAt = Date.now() - 120000; state.lastSeenAt = hiddenAt;")
    add(B, 'Bread'); B.locator('#addInput').blur(); settle(A, B, ms=1500)
    A.evaluate("seenCutoff = hiddenAt; render();")  # what visibilitychange does on return
    check('A sees Bread as New, from Liv', row(A, 'Bread').locator('.newtag').count() == 1 and row(A, 'Bread').locator('.by').text_content() == 'Liv')
    check('Milk (own) is not New on A', row(A, 'Milk').locator('.newtag').count() == 0)
    check('B does not see its own item as New', row(B, 'Bread').locator('.newtag').count() == 0)
    # Coming back again later clears it
    A.evaluate("hiddenAt = Date.now(); seenCutoff = hiddenAt; render();")
    check('New clears on the next visit', row(A, 'Bread').locator('.newtag').count() == 0 and row(A, 'Bread').locator('.by').count() == 1)
    # Sending an item into the shared list from another tab counts as added
    B.evaluate("addShop('Aldi'); state.tab = state.shops.find(s=>s.name==='Aldi').id; addItem('Eggs', {quiet:true}); save(); render();")
    A.evaluate("seenCutoff = Date.now() - 1000")
    home = B.evaluate("state.shops.find(s=>s.name==='Home').id")
    hold(B, item(B, 'Eggs')); B.click(f'#sheet [data-act="moveTo"][data-shop="{home}"]'); settle(A, B, ms=1500)
    check('Moved-in item is New for A', row(A, 'Eggs').locator('.newtag').count() == 1)
    # Ticking keeps the fields; trolley rows show no tags
    tap(A, item(A, 'Bread')); settle(A, B, ms=1500)
    check('Fields survive a tick round trip', B.evaluate("(() => { const i = state.items.find(x=>x.name==='Bread'); return i.addedBy === 'Liv' && i.addedDev && i.done; })()"))
    A.screenshot(path=OUT + 'v230-a.png')
    # Settings shows and changes the name
    A.click('#btnSettings'); A.wait_for_timeout(300)
    check('Settings shows the name', 'Your name: Dan' in A.locator('#sheet [data-act="askName"]').text_content())
    # Device id is not in the list data (a move must not clone it)
    check('Device id stays out of state', 'addedDev' not in A.evaluate("Object.keys(state).join(',')") and A.evaluate("!('device' in state)"))
    ctxA.close(); ctxB.close(); b.close()
print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e])
print('Failed:', [n for n, ok in results if not ok])

with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.me='Dan'; state.nameAsked=true; createSharedList('Home')"); A.wait_for_timeout(1500); A.keyboard.press('Escape')
    lid = A.evaluate("sharedShops()[0].shared.listId"); add(A, 'Milk'); A.locator('#addInput').blur(); settle(A)
    B.evaluate(f"state.nameAsked=true; joinSharedList('{lid}')"); settle(B, ms=1500)
    check('Joining: existing items are not New', row(B, 'Milk').locator('.newtag').count() == 0 and row(B, 'Milk').locator('.by').text_content() == 'Dan')
    add(A, 'Eggs'); A.locator('#addInput').blur(); settle(A, B, ms=1500)
    check('Added after joining: New', row(B, 'Eggs').locator('.newtag').count() == 1)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

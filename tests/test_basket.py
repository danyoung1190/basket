import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, sys, time
from playwright.sync_api import sync_playwright

URL = 'http://localhost:8765/'
OUT = WORK
errors = []
results = []

def check(name, cond):
    results.append((name, bool(cond)))
    print(('PASS ' if cond else 'FAIL ') + name)

def state(page):
    return page.evaluate("JSON.parse(localStorage.getItem('basket.v1'))")

def _retry(fn):
    for i in range(3):
        try: return fn()
        except Exception as e:
            if i == 2 or 'not attached' not in str(e): raise

def hold(page, sel):
  return _retry(lambda: _hold(page, sel))

def _clear_dock(page, sel):
    # Fixed trolley at the bottom covers the last rows, as it would a finger: scroll them clear first.
    page.locator(sel).first.scroll_into_view_if_needed()
    page.locator(sel).first.evaluate('''el => { const d = document.querySelector('#dock');
      if (el.closest('#sheet')) return;
      const t = document.querySelector('#toast.show'); if (t && typeof hideToast === 'function') hideToast(); // a finger would wait for it
      if (!d || d.hidden) return; const r = el.getBoundingClientRect(), hit = d.querySelector('.hit') || d, dr = hit.getBoundingClientRect();
      const limit = Math.min(dr.top, d.getBoundingClientRect().top + 40);
      if (r.bottom > limit - 8) window.scrollBy(0, r.bottom - limit + 24); }''')
    page.wait_for_timeout(120)

def _hold(page, sel):
    _clear_dock(page, sel)
    box = page.locator(sel).first.bounding_box()
    x, y = box['x'] + min(60, box['width'] / 2), box['y'] + box['height'] / 2
    page.mouse.move(x, y); page.mouse.down(); page.wait_for_timeout(650); page.mouse.up()
    page.wait_for_timeout(350)

def tap(page, sel):
  return _retry(lambda: _tap(page, sel))

def _tap(page, sel):
    _clear_dock(page, sel)
    box = page.locator(sel).first.bounding_box()
    x, y = box['x'] + min(60, box['width'] / 2), box['y'] + box['height'] / 2
    page.mouse.move(x, y); page.mouse.down(); page.mouse.up()

def item(page, name):
    return f'.row.item:has(.name:text-is("{name}"))'

def add(page, name):
    page.fill('#addInput', name); page.press('#addInput', 'Enter'); page.wait_for_timeout(80)

def drag_to(page, src_sel, dst_sel, below=True):
    # Behave like a person: aim at the gap under the heading as it looks *now*, re-aiming as rows slide.
    page.locator(src_sel + ' .grip').first.scroll_into_view_if_needed()
    page.evaluate('window.scrollBy(0, 120)')
    g = page.locator(src_sel + ' .grip').first.bounding_box()
    x, y = g['x'] + g['width'] / 2, g['y'] + g['height'] / 2
    page.mouse.move(x, y); page.mouse.down(); page.wait_for_timeout(260)
    for _ in range(4):
        row = page.locator(dst_sel).first.bounding_box()
        ty = (row['y'] + row['height'] + 27) if below else (row['y'] - 27)
        for i in range(1, 9):
            page.mouse.move(x, y + (ty - y) * i / 8); page.wait_for_timeout(16)
        y = ty
    page.wait_for_timeout(100); page.mouse.up(); page.wait_for_timeout(250)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**p.devices['iPhone 13'], color_scheme='light')
    page = ctx.new_page()
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(URL); page.wait_for_timeout(400)
    page.screenshot(path=OUT + '01-empty.png')

    # Add shops
    tap(page, '.tab.add'); page.wait_for_timeout(350); page.click('#sheet [data-act="menuShop"]'); page.wait_for_timeout(350)
    page.click('#sheet [data-v="Tesco"]'); page.wait_for_timeout(400)
    check('Tesco added and selected', state(page)['tab'] == state(page)['shops'][0]['id'])
    tap(page, '.tab.add'); page.wait_for_timeout(350); page.click('#sheet [data-act="menuShop"]'); page.wait_for_timeout(350)
    page.fill('#sheet input.field', 'Aldi'); page.press('#sheet input.field', 'Enter'); page.wait_for_timeout(400)
    check('Two shops', len(state(page)['shops']) == 2)
    page.evaluate("state.shops.forEach(s => s.sections = []); save(); render();")  # v1.0 flow: start without standard sections

    # Back to List and add items
    tap(page, '.tab[data-tab="list"]'); page.wait_for_timeout(200)
    for n in ['Milk', 'Bread', 'Bananas', 'Eggs', 'Washing up liquid', 'Cheddar']:
        add(page, n)
    add(page, 'milk')
    check('Duplicate not added', len(state(page)['items']) == 6)
    page.locator('#addInput').blur(); page.wait_for_timeout(100)
    page.screenshot(path=OUT + '02-list.png')

    # Long press Milk, send to Tesco
    hold(page, item(page, 'Milk'))
    check('Item sheet opened', page.locator('#sheet.open h2:text-is("Milk")').count() == 1)
    page.screenshot(path=OUT + '03-hold-sheet.png')
    tesco = state(page)['shops'][0]
    page.click(f'#sheet [data-act="moveTo"][data-shop="{tesco["id"]}"]'); page.wait_for_timeout(400)
    milk = [i for i in state(page)['items'] if i['name'] == 'Milk'][0]
    check('Milk moved to Tesco', milk['shopId'] == tesco['id'])
    # Undo then redo
    page.click('#toast [data-act="undo"]'); page.wait_for_timeout(150)
    milk = [i for i in state(page)['items'] if i['name'] == 'Milk'][0]
    check('Undo move works', milk['shopId'] is None)
    for n in ['Milk', 'Bananas', 'Eggs', 'Cheddar']:
        hold(page, item(page, n))
        page.click(f'#sheet [data-act="moveTo"][data-shop="{tesco["id"]}"]'); page.wait_for_timeout(350)
    aldi = state(page)['shops'][1]
    hold(page, item(page, 'Bread'))
    page.click(f'#sheet [data-act="moveTo"][data-shop="{aldi["id"]}"]'); page.wait_for_timeout(350)

    # Tesco: add sections via shop settings
    tap(page, f'.tab[data-tab="{tesco["id"]}"]'); page.wait_for_timeout(200)
    # 2.1.1: aisles appear on their own as items arrive
    secn = {s['id']: s['name'] for s in state(page)['shops'][0]['sections']}
    its = {i['name']: i for i in state(page)['items']}
    check('Items filed into new aisles on arrival', secn.get(its['Bananas']['sectionId']) == 'Fruit & veg' and secn.get(its['Milk']['sectionId']) == 'Dairy & eggs' and secn.get(its['Cheddar']['sectionId']) == 'Cheese')
    page.screenshot(path=OUT + '04-tesco-sections.png')

    # Drag Bananas under Fruit & veg, Milk & Eggs under Dairy
    drag_to(page, item(page, 'Bananas'), '.row.header:has-text("Fruit & veg")')
    drag_to(page, item(page, 'Milk'), '.row.header:has-text("Dairy & eggs")')
    sec = {s['name']: s['id'] for s in state(page)['shops'][0]['sections']}
    its = {i['name']: i for i in state(page)['items']}
    check('Bananas dragged into Fruit & veg', its['Bananas']['sectionId'] == sec['Fruit & veg'])
    check('Milk dragged into Dairy & eggs', its['Milk']['sectionId'] == sec['Dairy & eggs'])
    # Set section via sheet
    hold(page, item(page, 'Eggs'))
    page.click('#sheet [data-act="allSecs"]'); page.wait_for_timeout(150)
    page.click(f'#sheet [data-act="setSection"][data-sec="{sec["Dairy & eggs"]}"]'); page.wait_for_timeout(350)
    its = {i['name']: i for i in state(page)['items']}
    check('Eggs set to Dairy via sheet', its['Eggs']['sectionId'] == sec['Dairy & eggs'])
    order = page.eval_on_selector_all('#list .row', 'els => els.map(e => e.textContent.trim())')
    print('Tesco order:', order)

    # Tick Milk
    tap(page, item(page, 'Milk')); page.wait_for_timeout(1400)
    its = {i['name']: i for i in state(page)['items']}
    check('Milk ticked', its['Milk']['done'])
    check('Ticked item is in the trolley', page.locator('#dock .tcount').text_content() == '1')
    page.screenshot(path=OUT + '05-ticked.png')
    page.click('#dock'); page.wait_for_timeout(400)
    check('Trolley opens and lists Milk', page.locator('#sheet .trolley-list .row.item').count() == 1)
    page.click('#sheet [data-act="clearTicked"]'); page.click('#sheet [data-act="clearTicked"]'); page.wait_for_timeout(400)
    check('Clear moves to removed', any(r['name'] == 'Milk' for r in state(page)['removed']))
    page.click('#toast [data-act="undo"]'); page.wait_for_timeout(150)
    check('Undo clear', any(i['name'] == 'Milk' for i in state(page)['items']))
    page.evaluate("clearTicked()"); page.wait_for_timeout(200)

    # Quick re-add on list tab
    tap(page, '.tab[data-tab="list"]'); page.wait_for_timeout(200)
    page.click('#addInput'); page.type('#addInput', 'mi'); page.wait_for_timeout(150)
    check('Suggestion shows Milk', page.locator('#suggest [data-add="Milk"]').count() == 1)
    page.screenshot(path=OUT + '06-suggest.png')
    page.click('#suggest [data-add="Milk"]'); page.wait_for_timeout(200)
    add(page, 'Bananas')
    page.locator('#addInput').fill(''); page.locator('#addInput').blur(); page.wait_for_timeout(150)
    check('Sort button appears', page.locator('[data-act="sortAll"]').count() == 1)
    page.screenshot(path=OUT + '07-sort.png')
    page.click('[data-act="sortAll"]'); page.wait_for_timeout(200)
    its = {i['name']: i for i in state(page)['items']}
    check('Sort all sends Milk to Tesco Dairy', its['Milk']['shopId'] == tesco['id'] and its['Milk']['sectionId'] == sec['Dairy & eggs'])

    # Remembered placement on add inside shop
    tap(page, f'.tab[data-tab="{tesco["id"]}"]'); page.wait_for_timeout(200)

    # Persistence and offline
    page.reload(); page.wait_for_timeout(600)
    check('Persists after reload', len(state(page)['items']) >= 6)
    page.evaluate("navigator.serviceWorker.ready.then(()=>1)")
    page.wait_for_timeout(800)
    page.reload(); page.wait_for_timeout(600)  # ensure controlled
    ctx.set_offline(True)
    page.reload(); page.wait_for_timeout(800)
    check('Opens offline', page.locator('#title').text_content() != '')
    ctx.set_offline(False)
    page.screenshot(path=OUT + '08-after-offline.png')

    # Restore from backup file
    backup = {'app': 'basket', 'exportedAt': '2026-10-01T10:00:00Z', 'data': state(page)}
    path = OUT + 'backup.json'
    open(path, 'w').write(json.dumps(backup))
    page.click('#btnSettings'); page.wait_for_timeout(350)
    page.screenshot(path=OUT + '09-settings.png')
    page.set_input_files('#restoreInput', path); page.wait_for_timeout(400)
    check('Restore confirm shown', page.locator('#sheet [data-act="confirmRestore"]').count() == 1)
    page.click('#sheet [data-act="confirmRestore"]'); page.wait_for_timeout(300)
    check('Restore applied', len(state(page)['items']) == len(backup['data']['items']))
    open(OUT + 'bad.json', 'w').write('{"nope":1}')
    page.click('#btnSettings'); page.wait_for_timeout(300)
    page.set_input_files('#restoreInput', OUT + 'bad.json'); page.wait_for_timeout(300)
    check('Bad backup rejected', "isn't a Virtual Trolley backup" in page.locator('#toast').text_content())
    page.keyboard.press('Escape'); page.wait_for_timeout(350)

    # Corrupt storage recovery
    page.evaluate("localStorage.setItem('basket.v1', '{broken')")
    page.reload(); page.wait_for_timeout(500)
    check('Recovers last good copy', len(state(page)['items']) >= 6 if state(page) else False)

    # Delete shop: items go to list
    page.evaluate("localStorage.getItem('basket.v1')")
    tap(page, f'.tab[data-tab="{aldi["id"]}"]'); page.wait_for_timeout(200)
    page.click('#btnShop'); page.wait_for_timeout(300)
    page.click('#sheet [data-act="deleteShop"]'); page.click('#sheet [data-act="deleteShop"]'); page.wait_for_timeout(300)
    its = {i['name']: i for i in state(page)['items']}
    check('Deleted shop items back on list', its['Bread']['shopId'] is None and len(state(page)['shops']) == 1)
    page.click('#toast [data-act="undo"]'); page.wait_for_timeout(200)
    check('Undo delete shop', len(state(page)['shops']) == 2)

    # Final light screenshot of Tesco
    tap(page, f'.tab[data-tab="{tesco["id"]}"]'); page.wait_for_timeout(300)
    page.screenshot(path=OUT + '10-tesco-light.png')
    final_state = state(page)

    # Dark mode
    ctx2 = b.new_context(**p.devices['iPhone 13'], color_scheme='dark')
    pg2 = ctx2.new_page()
    pg2.goto(URL); pg2.evaluate("s => localStorage.setItem('basket.v1', JSON.stringify(s))", final_state)
    pg2.reload(); pg2.wait_for_timeout(500)
    pg2.screenshot(path=OUT + '11-tesco-dark.png')
    hold(pg2, item(pg2, 'Cheddar'))
    pg2.screenshot(path=OUT + '12-dark-sheet.png')
    b.close()

print('\nConsole errors:', errors)
print('Failed:', [n for n, ok in results if not ok])

import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])

_check = check
def check(name, cond, info=None):
    if not cond and info is not None: print('   got', info)
    _check(name, cond)

def secs(pg, shop):  return pg.evaluate(f"state.shops.find(s=>s.name==='{shop}').sections.map(s=>s.name)")
def secof(pg, shop, item): return pg.evaluate(f"""(() => {{ const s=state.shops.find(x=>x.name==='{shop}'); const i=state.items.find(x=>x.shopId===s.id && x.name==='{item}'); const sec=s.sections.find(z=>z.id===i.sectionId); return sec?sec.name:null; }})()""")
def open_item(pg, shop, item):
    pg.evaluate(f"""openItemSheet(state.items.find(x=>x.shopId===state.shops.find(s=>s.name==='{shop}').id && x.name==='{item}').id)"""); pg.wait_for_timeout(350)
def chips(pg): return pg.locator('#sheet [data-secchips] .chip').all_inner_texts()
def search(pg, q):
    pg.fill('#sheet [data-secq]', q); pg.wait_for_timeout(120)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone(p, b)
    A.evaluate("createSharedList('Home')"); A.wait_for_timeout(1500)
    for n in ['Milk', 'Glorp flakes', 'Zing hoops', 'Car wax', 'Cookie crisp', 'Ice cubes']: add(A, n)
    A.locator('#addInput').blur(); settle(A)
    check('New cereal names file themselves', secof(A, 'Home', 'Cookie crisp') == 'Breakfast & spreads')
    check('Unknown item has no section', secof(A, 'Home', 'Glorp flakes') is None)

    lid = A.evaluate("sharedShops()[0].shared.listId")
    ctxB, B = phone(p, b)
    B.evaluate(f"joinSharedList('{lid}')"); settle(B, ms=1500)

    open_item(A, 'Home', 'Glorp flakes')
    check('Search box shown', A.locator('#sheet [data-secq]').count() == 1)
    check('Opening an item does not pop the keyboard up', A.evaluate("!document.activeElement.matches('input, textarea')"))
    h0 = A.evaluate("sheet.offsetHeight")
    A.click('#sheet [data-secq]'); A.wait_for_timeout(500)
    search(A, 'zzzz')
    check('Sheet keeps its height while searching', abs(A.evaluate("sheet.offsetHeight") - h0) <= 2, (h0, A.evaluate("sheet.offsetHeight")))
    search(A, '')
    c0 = chips(A)
    check('Empty search shows the shop sections only', c0[0] == 'None' and c0[-1] == '+ New section' and 'Baby' not in c0, c0)

    search(A, 'cereal'); c = chips(A)
    check('"cereal" finds Breakfast & spreads first', c and c[0] == 'Breakfast & spreads', c)
    check('Offers a new section too', c[-1].startswith('+ New section'), c)
    A.screenshot(path=WORK + 'v271_search.png')
    A.locator('#sheet [data-secchips] .chip').first.click(); A.wait_for_timeout(400)
    check('Picked aisle is created and item moved', secof(A, 'Home', 'Glorp flakes') == 'Breakfast & spreads')
    s = secs(A, 'Home')
    std = A.evaluate("STANDARD_SECTIONS"); order = [x for x in std if x in s]
    check('Aisle sits in walking order', [x for x in s if x in std] == order, s)
    A.evaluate("undo()"); A.wait_for_timeout(200)
    check('Undo puts it back in no section', secof(A, 'Home', 'Glorp flakes') is None)
    open_item(A, 'Home', 'Glorp flakes'); search(A, 'cereal'); A.locator('#sheet [data-secchips] .chip').first.click(); A.wait_for_timeout(300)

    # A product name finds its aisle, and Enter takes the top match
    open_item(A, 'Home', 'Zing hoops'); search(A, 'weetabix')
    check('Product name finds its aisle', chips(A)[0] == 'Breakfast & spreads', chips(A))
    A.press('#sheet [data-secq]', 'Enter'); A.wait_for_timeout(400)
    check('Enter picks the top match', secof(A, 'Home', 'Zing hoops') == 'Breakfast & spreads')

    A.evaluate("openPrompt({ title:'Rename item', value:'x', onSave: () => {} })"); A.wait_for_timeout(300)
    check('Short forms still start with the keyboard up', A.evaluate("document.activeElement.matches('#sheet input')"))
    A.keyboard.press('Escape'); A.wait_for_timeout(350)
    A.evaluate("openLibrary()"); A.wait_for_timeout(300)
    check('Recipe library does not pop the keyboard up', A.evaluate("!document.activeElement.matches('input, textarea')"))
    A.keyboard.press('Escape'); A.wait_for_timeout(350)
    # Typos
    open_item(A, 'Home', 'Ice cubes'); search(A, 'frozn')
    check('Typo still finds Frozen', chips(A)[0] == 'Frozen', chips(A))
    A.keyboard.press('Escape'); A.wait_for_timeout(350)

    # Nothing matches: make a section with that name
    open_item(A, 'Home', 'Car wax'); search(A, 'Car stuff'); c = chips(A)
    check('No match offers only a new section', c == ['+ New section “Car stuff”'], c)
    A.locator('#sheet [data-secchips] .chip').first.click(); A.wait_for_timeout(400)
    check('New section made and item moved', secof(A, 'Home', 'Car wax') == 'Car stuff')

    # Clearing the search goes back to the normal list
    open_item(A, 'Home', 'Milk'); search(A, 'cer'); search(A, '')
    check('Cleared search shows shop sections', chips(A)[0] == 'None' and 'Car stuff' in chips(A))
    A.keyboard.press('Escape'); A.wait_for_timeout(300)

    settle(A, B, ms=1500)
    check('Shared list: other phone gets the new sections', 'Car stuff' in secs(B, 'Home') and 'Breakfast & spreads' in secs(B, 'Home'))
    check('Shared list: other phone sees items moved', secof(B, 'Home', 'Glorp flakes') == 'Breakfast & spreads' and secof(B, 'Home', 'Car wax') == 'Car stuff')

    # A removed aisle can still be picked on purpose, and that undoes the removal
    A.evaluate("addShop('Big shop'); state.tab = state.shops.find(s=>s.name==='Big shop').id; save(); render();")
    add(A, 'Bottle opener'); A.locator('#addInput').blur(); A.wait_for_timeout(200)
    A.evaluate("state.shops.find(s=>s.name==='Big shop').skipAisles=['Household']; save();")
    open_item(A, 'Big shop', 'Bottle opener'); search(A, 'household')
    A.locator('#sheet [data-secchips] .chip').first.click(); A.wait_for_timeout(300)
    check('Removed aisle picked on purpose comes back', secof(A, 'Big shop', 'Bottle opener') == 'Household' and 'Household' not in A.evaluate("state.shops.find(s=>s.name==='Big shop').skipAisles"))
    check('Private shop sections stay on this phone', 'Household' in secs(A, 'Big shop') and B.evaluate("state.shops.every(s=>s.name!=='Big shop')"))
    b.close()
print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e and 'ERR_FAILED' not in e])
print('Failed:', [n for n, ok in results if not ok])

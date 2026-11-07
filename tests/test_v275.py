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

ITEMS = ['Bananas', 'Apples', 'Carrots', 'Onions', 'Potatoes', 'Peppers', 'Chicken breasts', 'Beef mince', 'Sausages', 'Bacon',
         'Milk', 'Butter', 'Eggs', 'Yogurts', 'Cheddar', 'Ham', 'Peas', 'Ice cream', 'Pasta', 'Rice', 'Chopped tomatoes',
         'Baked beans', 'Ketchup', 'Crisps', 'Biscuits', 'Squash', 'Washing up liquid', 'Toilet roll', 'Shampoo', 'Paracetamol']

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx, A = phone(p, b)
    A.evaluate("addShop('Tesco'); state.tab = state.shops.find(s=>s.name==='Tesco').id; save(); render();"); A.wait_for_timeout(200)
    for n in ITEMS: add(A, n)
    A.wait_for_timeout(300)
    A.evaluate("window.scrollTo(0, 0)"); A.wait_for_timeout(300)
    check('Long list is taller than the screen', A.evaluate("document.body.scrollHeight > innerHeight * 1.5"))

    add(A, 'Bin bags'); A.wait_for_timeout(700)
    check('Adding an item far down does not move the page', A.evaluate("scrollY") < 5, A.evaluate("scrollY"))
    t = A.inner_text('#toast')
    check('It says where it went', 'Added to Household' in t, t)
    check('With a Show button', A.locator('#toast [data-act="showItem"]').count() == 1)
    check('Add box still has the cursor', A.evaluate("document.activeElement.id === 'addInput'"))
    A.screenshot(path=WORK + 'v275_added.png')

    A.evaluate("hideToast()")
    A.evaluate("addShop('Aldi'); state.tab = state.shops.find(s=>s.name==='Aldi').id; save(); render();"); A.wait_for_timeout(200)
    for n in ['Milk', 'Bread', 'Eggs']: add(A, n)
    A.wait_for_timeout(300); A.evaluate("hideToast()")
    add(A, 'Grapes'); A.wait_for_timeout(700)
    check('Short list: new item on screen, no message', A.locator('#toast.show').count() == 0 and A.evaluate("scrollY") < 5, A.inner_text('#toast'))
    A.evaluate("state.tab = state.shops.find(s=>s.name==='Tesco').id; save(); render(); window.scrollTo(0,0)"); A.wait_for_timeout(300)
    add(A, 'Shampoo'); A.wait_for_timeout(700)
    t = A.inner_text('#toast')
    check('Already on the list (off screen): says so, with Show, no move', 'already on the list' in t and 'Show' in t and A.evaluate("scrollY") < 5, t)

    A.click('#toast [data-act="showItem"]'); A.wait_for_timeout(900)
    r = A.evaluate("(() => { const r=[...document.querySelectorAll('.row.item')].find(x=>x.textContent.includes('Shampoo')).getBoundingClientRect(); return [r.top, r.bottom, innerHeight]; })()")
    check('Show scrolls to it', r[0] >= 0 and r[1] <= r[2], r)
    check('No errors', not [e for e in errors if 'Failed to load resource' not in e and 'ERR_' not in e])
    b.close()
print('Failed:', [n for n, ok in results if not ok])

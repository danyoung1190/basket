import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
SP = WORK
def add_meal(pg, name, who=None):
    pg.click('#mealsView .day.today [data-mact="add"]'); pg.wait_for_timeout(300)
    pg.fill('#sheet input[name="name"]', name)
    if who is not None: pg.click(f'#sheet [data-mact="who"][data-v="{who}"]')
    pg.click('#sheet form[data-mform="meal"] button[type="submit"]'); pg.wait_for_timeout(400)
with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.me='Liv'; state.nameAsked=true; createSharedList('Home')"); A.wait_for_timeout(1500); A.keyboard.press('Escape')
    lid = A.evaluate("sharedShops()[0].shared.listId")
    B.evaluate(f"state.nameAsked=true; joinSharedList('{lid}')"); settle(B, ms=1500)
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500)
    plan = A.locator('#sheet .bigcode').text_content().strip(); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    B.evaluate(f"joinSharedList('{plan}')"); settle(B, ms=1500)
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    add_meal(A, 'Steak and chips')
    check('First meal of the day is for everyone', A.evaluate("state.meals[0].who") == '')
    A.click('#mealsView .day.today [data-mact="add"]'); A.wait_for_timeout(300)
    check('Second meal on a day defaults to Kids', A.locator('#sheet [data-mact="who"][data-v="kids"]').get_attribute('aria-pressed') == 'true')
    A.fill('#sheet input[name="name"]', 'Fish fingers'); A.click('#sheet form[data-mform="meal"] button[type="submit"]'); A.wait_for_timeout(400)
    who = A.evaluate("Object.fromEntries(state.meals.map(m => [m.name, m.who]))")
    check('Adding a Kids meal turns the Everyone meal into Us', who == {'Steak and chips': 'us', 'Fish fingers': 'kids'})
    cards = A.eval_on_selector_all('#mealsView .day.today .meal strong', 'els => els.map(e => e.textContent)')
    print(cards)
    check('Day shows Us first, then Kids, with labels', cards[0].startswith('UsSteak') and cards[1].startswith('KidsFish'))
    settle(A, B, ms=1500); B.click('#tabs .tab.meals'); B.wait_for_timeout(400)
    check('Other phone gets who it is for', B.evaluate("Object.fromEntries(state.meals.map(m => [m.name, m.who]))") == who)
    # Edit back to everyone
    A.locator('#mealsView .meal:has-text("Fish fingers")').click(); A.wait_for_timeout(300); A.click('#sheet [data-mact="edit"]'); A.wait_for_timeout(300)
    check('Edit shows Kids selected', A.locator('#sheet [data-mact="who"][data-v="kids"]').get_attribute('aria-pressed') == 'true')
    A.click('#sheet [data-mact="who"][data-v=""]'); A.click('#sheet form[data-mform="meal"] button[type="submit"]'); A.wait_for_timeout(300)
    check('Can change it back', A.evaluate("state.meals.find(m=>m.name==='Fish fingers').who") == '')
    A.screenshot(path=WORK + 'who_meals.png')
    b.close()
print('Failed:', [n for n, ok in results if not ok])

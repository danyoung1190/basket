import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import time
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
SP = WORK
def new_meal(pg, name, files):
    pg.click('#mealsView .day.today [data-mact="add"]'); pg.wait_for_timeout(300)
    pg.fill('#sheet input[name="name"]', name); pg.set_input_files('#sheet [data-mfile]', files); pg.wait_for_timeout(2500)
    pg.click('#sheet form[data-mform="meal"] button[type="submit"]'); pg.wait_for_timeout(400)
def wait_sheet(pg, typ, secs=60):
    t = time.time()
    while time.time() - t < secs:
        if pg.evaluate("sheetCtx && sheetCtx.type") == typ: return True
        pg.wait_for_timeout(250)
    return False
with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.me='Liv'; state.nameAsked=true;"); A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500); plan = A.evaluate("mealPlanId()"); A.keyboard.press('Escape')
    B.evaluate(f"state.nameAsked=true; joinSharedList('{plan}')"); settle(B, ms=1200)
    new_meal(A, 'Lemon chilli pasta', [TESTS + 'assets/pasta.png'])
    A.locator('#mealsView .meal:has-text("Lemon chilli pasta")').click(); A.wait_for_timeout(300)
    t0 = time.time(); A.click('#sheet [data-mact="ing"]'); A.wait_for_timeout(200)
    check('Shows it is reading', A.evaluate("sheetCtx.type") == 'reading')
    ok = wait_sheet(A, 'ingCheck'); print('read in %.1fs' % (time.time() - t0))
    rows = dict(A.eval_on_selector_all('#sheet .ingrow', 'els => els.map(e => [e.querySelector(".nm").childNodes[0].textContent.trim(), e.getAttribute("aria-pressed")])'))
    print(rows)
    check('Goes straight to the checklist', ok)
    check('Reads the ingredients from the screenshot', all(k in rows for k in ['Butter', 'Garlic', 'Chilli flakes', 'Lemon juice', 'Cream', 'Chilli oil', 'Pasta', 'Cheese']))
    check('No screen clutter picked up', not any(k.lower().startswith(('join', 'izhe', 'spicy', 'comments')) for k in rows))
    check('Optional and cupboard things start unticked', rows.get('Red chillies') == 'false' and rows.get('Salt') == 'false' and rows.get('Olive oil') == 'false')
    check('Text saved on the meal', 'Ingredients' in A.evaluate("state.meals[0].ing"))
    settle(A, B, ms=1500)
    check('Other phone gets the text, no second read needed', 'Chilli flakes' in B.evaluate("state.meals[0].ing"))
    A.click('#sheet [data-mact="ingEdit"]'); A.wait_for_timeout(300)
    check('The read text can be checked and fixed', 'Chilli flakes' in A.input_value('#sheet textarea[data-ing]') and A.locator('#sheet [data-mact="ingOcr"]').count() == 1)
    A.keyboard.press('Escape'); A.wait_for_timeout(300)
    # closing mid-read doesn't pop back open
    new_meal(A, 'Pork tacos', [TESTS + 'assets/insta.png'])
    A.locator('#mealsView .meal:has-text("Pork tacos")').click(); A.wait_for_timeout(300)
    A.click('#sheet [data-mact="ing"]'); A.wait_for_timeout(400); A.keyboard.press('Escape')
    for _ in range(40):
        if A.evaluate("!!(mealById(state.meals.find(m=>m.name==='Pork tacos').id).ing)"): break
        A.wait_for_timeout(300)
    A.wait_for_timeout(500)
    check('Closing while reading: no surprise sheet, text still saved', A.evaluate("!sheetCtx") and 'pork tenderloin' in A.evaluate("state.meals.find(m=>m.name==='Pork tacos').ing"))
    ctxA.close(); ctxB.close()
    # no signal on first use: falls back to paste, says why
    ctxC, C = phone(p, b); C.route('**/ocr/**', lambda r, q: r.abort())
    C.evaluate("state.nameAsked=true;"); C.click('#tabs .tab.meals'); C.wait_for_timeout(300)
    new_meal(C, 'Soup', [TESTS + 'assets/fake_ing.png'])
    C.locator('#mealsView .meal:has-text("Soup")').click(); C.wait_for_timeout(300); C.click('#sheet [data-mact="ing"]')
    check('No reader: offers paste, explains', wait_sheet(C, 'ingPaste', 15) and 'needs signal' in C.text_content('#sheet .sub'))
    b.close()
print('Failed:', [n for n, ok in results if not ok])

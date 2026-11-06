import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.nameAsked=true;"); A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.evaluate("state.meals.push({ id:'m1', date:dayKey(new Date()), name:'Roast', imgs:[], ing:'', who:'', order:1, addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() }); save(); render();")
    first = lambda pg: pg.locator('#mealsView .day .dayhead span').first.text_content()
    check('Monday first by default', first(A).startswith('Monday'))
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500); plan = A.evaluate("mealPlanId()"); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    B.evaluate(f"state.nameAsked=true; joinSharedList('{plan}')"); settle(B, ms=1500)
    A.click('#mealsView [data-mact="wsheet"]'); A.wait_for_timeout(300)
    A.click('#sheet [data-mact="wstart"][data-v="0"]'); A.wait_for_timeout(300); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    check('Sunday first once chosen', first(A).startswith('Sunday') and A.locator('#mealsView .day').count() == 7)
    check('Today still holds its meal', A.locator('#mealsView .day.today .meal:has-text("Roast")').count() == 1)
    check('Footer says Sunday', 'Sunday' in A.locator('#mealsView .syncnote').last.text_content())
    settle(A, B, ms=1500); B.evaluate("render()"); B.wait_for_timeout(200)
    check('Other phone follows: Sunday first', first(B).startswith('Sunday'))
    B.evaluate("setWeekStart(6)"); settle(A, B, ms=1500)
    check('Saturday from the other phone comes back too', first(A).startswith('Saturday'))
    A.click('#btnSettings'); A.wait_for_timeout(300)
    check('Settings shows it', 'Saturday' in A.locator('#sheet [data-act="weekStart"]').text_content())
    # every week view is 7 consecutive days starting on the chosen day, any day of the week
    ok = A.evaluate("""() => { const res = []; for (const ws of [0, 1, 6]) { state.weekStart = ws; for (let off = -2; off <= 2; off++) { const d = weekDays(off);
        res.push(d.length === 7 && d[0].getDay() === ws && d.every((x, i) => i === 0 || (x - d[i-1]) / 864e5 >= 0.95 && (x - d[i-1]) / 864e5 <= 1.05)); }
        res.push(weekDays(0).some(x => dayKey(x) === dayKey(new Date()))); } return res.every(Boolean); }""")
    check('Weeks always 7 days from the chosen start, and this week contains today', ok)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

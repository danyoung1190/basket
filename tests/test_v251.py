import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.me='Dan'; state.nameAsked=true;"); A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.evaluate("state.meals.push({ id:'m1', date:dayKey(new Date()), name:'Beans on toast', imgs:[], ing:'', who:'kids', order:1, addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() }); save(); render();")
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500)
    plan = A.evaluate("mealPlanId()"); A.keyboard.press('Escape'); settle(A)
    # what the older version did on the other phone: a shopping-list tab for the plan
    B.evaluate(f"""state.nameAsked = true; state.shops.push({{ id:'oldtab', name:'Meal plan', color:'#C8463F', sections:[], shared:{{ fb:true, listId:'{plan}', joinedAt:Date.now() }} }});
      state.tab = 'oldtab'; state.mealsHidden = true; state.mealsMoved = false; save();""")
    B.reload(); B.wait_for_timeout(2500)
    check('The wrong tab is gone', B.evaluate("state.shops.some(s => s.id === 'oldtab')") is False and B.locator('#tabs .tab:has-text("Meal plan")').count() == 0)
    check('It is the meal plan now, open on Meals', B.evaluate("mealPlanId()") == plan and B.text_content('#title') == 'Meals')
    check('Meals tab is shown even if it had been hidden', B.locator('#tabs .tab.meals').count() == 1)
    import json, urllib.request
    left = json.loads(urllib.request.urlopen(f'http://127.0.0.1:8766/col?path=lists/{plan}/meals').read())['docs']
    check('The plan keeps its meals in the shared store', 'm1' in left)
    check('Shared meals arrive', B.locator('#mealsView .meal:has-text("Beans on toast")').count() == 1)
    B.click('#mealsView .day.today [data-mact="add"]'); B.wait_for_timeout(300)
    B.fill('#sheet input[name="name"]', 'Spag bol'); B.click('#sheet [data-mact="who"][data-v="us"]'); B.click('#sheet form[data-mform="meal"] button[type="submit"]'); settle(A, B, ms=1500)
    check('And meals added there reach the other phone', A.evaluate("state.meals.some(m => m.name === 'Spag bol')"))
    B.reload(); B.wait_for_timeout(1500)
    check('Stays fixed after reopening', B.evaluate("mealPlanId()") == plan and B.evaluate("state.shops.length") == 0)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

with sync_playwright() as p:
    b = p.chromium.launch(); ctx, A = phone(p, b)
    A.evaluate("addShop('Tesco'); addShop('B&Q'); state.tab = state.shops[0].id; save(); render();")
    check('No pill when nothing is hidden', A.locator('#tabs .hiddenpill').count() == 0)
    A.evaluate("setTabHidden('meals', true); setTabHidden(state.shops[1].id, true);")
    check('Pill shows how many are hidden', A.locator('#tabs .hiddenpill').text_content() == '2 hidden')
    A.locator('#tabs .hiddenpill').click(); A.wait_for_timeout(400)
    check('Tapping it opens the tab switches', A.locator('#sheet [data-act="tabToggle"][data-tab="meals"]').count() == 1)
    A.click('#sheet [data-act="tabToggle"][data-tab="meals"]'); A.wait_for_timeout(250)
    check('Switching Meals on brings it back', A.locator('#tabs .tab.meals').count() == 1 and A.locator('#tabs .hiddenpill').text_content() == '1 hidden')
    b.close()
print('Failed:', [n for n, ok in results if not ok])

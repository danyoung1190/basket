import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, urllib.request
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
SP = WORK
METHOD = open(TESTS + 'assets/parse.py').read().split('METHOD = """')[1].split('"""')[0]
def store(): return json.loads(urllib.request.urlopen('http://127.0.0.1:8766/stats').read())
def names(pg, shop): return sorted(pg.evaluate(f"itemsIn(state.shops.find(s=>s.name==='{shop}').id).filter(i=>!i.done).map(i=>i.name + (i.qty>1?' x'+i.qty:''))"))
with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone(p, b); ctxB, B = phone(p, b)
    A.evaluate("state.me='Liv'; state.nameAsked=true; addShop('Tesco'); createSharedList('Home')"); A.wait_for_timeout(1500); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    lid = A.evaluate("sharedShops()[0].shared.listId")
    B.evaluate(f"state.me='Dan'; state.nameAsked=true; joinSharedList('{lid}')"); settle(B, ms=1500)
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500)
    plan = A.locator('#sheet .bigcode').text_content().strip(); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    B.evaluate(f"joinSharedList('{plan}')"); settle(B, ms=1500)

    # --- add a meal with two screenshots ---
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    check('Joining the plan code lands on Meals, not a new shop tab', B.text_content('#title') == 'Meals' and B.evaluate("state.shops.length") == 1)
    check('Meals tab shows the week', A.text_content('#title') == 'Meals' and A.locator('#mealsView .day').count() == 7 and A.locator('#addForm').is_hidden())
    A.click('#mealsView .day.today [data-mact="add"]'); A.wait_for_timeout(300)
    A.fill('#sheet form[data-mform="meal"] input[name="name"]', 'Pulled pork tacos')
    A.set_input_files('#sheet [data-mfile]', [TESTS + 'assets/insta.png', TESTS + 'assets/fake_ing.png']); A.wait_for_timeout(2500)
    check('Two thumbnails after picking screenshots', A.locator('#sheet .thumbs .t').count() == 2)
    check('Name kept while pictures were added', A.input_value('#sheet form[data-mform="meal"] input[name="name"]') == 'Pulled pork tacos')
    A.click('#sheet form[data-mform="meal"] button[type="submit"]'); A.wait_for_timeout(400)
    sizes = A.evaluate("Promise.all(state.meals[0].imgs.map(k => IMG.get(k))).then(a => a.map(x => x.length))")
    print('image sizes', sizes)
    check('Screenshots shrunk under 850 KB each', all(0 < n < 850000 for n in sizes))
    check('Meal saved for today', A.evaluate("state.meals.length === 1 && state.meals[0].date === dayKey(new Date())"))
    settle(A, B, ms=2000)

    # --- other phone sees it, with pictures ---
    B.click('#tabs .tab.meals'); B.wait_for_timeout(500)
    check('B sees the meal, with who added it', B.locator('#mealsView .meal strong').first.text_content().startswith('Pulled pork tacos') and 'Liv' in B.locator('#mealsView .meal small').first.text_content())
    B.locator('#mealsView .meal').first.click(); B.wait_for_timeout(1500)
    srcs = B.eval_on_selector_all('#sheet .shots img', 'els => els.map(e => (e.getAttribute("src") || "").slice(0, 15))')
    check('B loads both screenshots from the shared list', len(srcs) == 2 and all(s.startswith('data:image/jpeg') for s in srcs))
    B.locator('#sheet .shots img').first.click(); B.wait_for_timeout(300)
    check('Tapping a screenshot opens it full screen', B.locator('#viewer').is_visible())
    B.click('#viewer .vclose'); B.wait_for_timeout(200)

    # --- ingredients to the list (from the method text alone) ---
    B.click('#sheet [data-mact="ing"]')
    for _ in range(120):
        if B.evaluate("sheetCtx && sheetCtx.type") in ('ingCheck', 'ingPaste'): break
        B.wait_for_timeout(250)
    check('Screenshots are read first', B.evaluate("sheetCtx.type") == 'ingCheck')
    B.click('#sheet [data-mact="ingEdit"]'); B.wait_for_timeout(300)
    B.fill('#sheet textarea[data-ing]', METHOD); B.click('#sheet [data-mact="ingRead"]'); B.wait_for_timeout(400)
    rows = B.eval_on_selector_all('#sheet .ingrow', 'els => els.map(e => [e.querySelector(".nm").childNodes[0].textContent.trim(), e.getAttribute("aria-pressed")])')
    print(rows)
    d = dict(rows)
    check('Method text finds the foods', all(k in d for k in ['Pork tenderloin', 'Red onions', 'Garlic', 'Smoked paprika', 'Lime juice', 'Cornflour', 'Chicken stock cubes']))
    check('Salt and pepper start unticked (cupboard)', d.get('Salt') == 'false' and d.get('Black pepper') == 'false')
    home = B.evaluate("state.shops.find(s=>s.name==='Home').id")
    check('Defaults to the shared list', B.locator(f'#sheet [data-mact="ingShop"][data-s="{home}"]').get_attribute('aria-pressed') == 'true')
    B.locator('#sheet .ingrow:has-text("Cornflour")').click(); B.wait_for_timeout(150)   # she has cornflour
    btn = B.locator('#sheet [data-mact="ingAdd"]').text_content()
    B.click('#sheet [data-mact="ingAdd"]'); B.wait_for_timeout(500)
    got = names(B, 'Home')
    print(btn, got)
    check('Items added to Home, minus unticked', 'Pork tenderloin' in got and 'Cornflour' not in got and 'Salt' not in got)
    check('Recipe text saved on the meal', B.evaluate("state.meals[0].ing.includes('pork tenderloin')"))
    settle(A, B, ms=1500)
    check('Other phone gets the items live', 'Pork tenderloin' in names(A, 'Home'))
    check('Other phone gets the recipe text', A.evaluate("state.meals[0].ing.length") > 100)
    check('Cupboard learned: cornflour now unticked next time', B.evaluate("state.pantry['cornflour'] === true"))
    check('Added items sit in aisles', B.evaluate("(() => { const s = state.shops.find(x=>x.name==='Home'); const i = state.items.find(x=>x.name==='Pork tenderloin' && x.shopId===s.id); return !!s.sections.find(z=>z.id===i.sectionId); })()"))

    # --- second meal, week ingredients merge ---
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300)
    A.evaluate("""() => { const d = weekDays(0)[ (new Date().getDay() + 6) % 7 === 6 ? 5 : 6 ];
      state.meals.push({ id:uid(), date:dayKey(d), name:'Chilli', note:'', ing:'Ingredients\\n500g beef mince\\n2 onions, diced\\n1 tin chopped tomatoes\\n1 tin kidney beans', imgs:[], order:Date.now(), addedBy:'Liv', addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() });
      state.meals.push({ id:uid(), date:dayKey(d), name:'Soup', note:'', ing:'- 1 onion\\n- 3 carrots\\n- vegetable stock', imgs:[], order:Date.now()+1, addedBy:'Liv', addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() });
      save(); render(); }""")
    A.click('#mealsView [data-mact="ingWeek"]'); A.wait_for_timeout(400)
    wk = A.eval_on_selector_all('#sheet .ingrow .nm', 'els => els.map(e => e.textContent.replace(/\\s+/g, " ").trim())')
    print(wk)
    check('Week view merges onions across meals', any(w.startswith('Onions') and '×3' in w for w in wk))
    check('Things already on a list start unticked', A.locator('#sheet .ingrow:has-text("Pork tenderloin")').get_attribute('aria-pressed') == 'false')
    A.keyboard.press('Escape'); A.wait_for_timeout(300)

    ctxH, Hm = phone(p, b)
    Hm.evaluate(f"state.nameAsked=true; joinSharedList('{lid}')"); Hm.wait_for_timeout(1500)
    Hm.click('#tabs .tab.meals'); Hm.wait_for_timeout(500)
    check('Someone on Home but not the meal plan sees no meals', Hm.evaluate("state.meals.length") == 0 and 'Only on this phone' in Hm.text_content('#mealsView .syncnote'))
    ctxH.close()
    # --- plan again copies a meal, pictures shared; deleting one keeps the other's pictures ---
    A.locator('#mealsView .meal:has-text("Pulled pork tacos")').click(); A.wait_for_timeout(300)
    A.click('#sheet [data-mact="again"]'); A.wait_for_timeout(300)
    check('Plan again offers this week and next', A.locator('#sheet [data-mact="day"]').count() == 14 and A.input_value('#sheet input[name="name"]') == 'Pulled pork tacos')
    A.locator('#sheet [data-mact="day"]').nth(10).click(); A.click('#sheet form[data-mform="meal"] button[type="submit"]'); A.wait_for_timeout(400)
    copies = A.evaluate("state.meals.filter(m=>m.name==='Pulled pork tacos').map(m=>[m.date, m.imgs.join(','), m.ing.length > 100])")
    print(copies)
    check('Copy has the same pictures and ingredients', len(copies) == 2 and copies[0][1] == copies[1][1] and copies[1][2])
    copy_id = A.evaluate("state.meals.filter(m=>m.name==='Pulled pork tacos').sort((a,b)=>a.date<b.date?1:-1)[0].id")
    A.evaluate(f"(() => {{ const m = mealById('{copy_id}'); state.meals = state.meals.filter(x => x.id !== m.id); save(); deleteMealImages(m); }})()"); A.wait_for_timeout(500)
    check('Deleting the copy keeps the original pictures', A.evaluate("Promise.all(state.meals.find(m=>m.name==='Pulled pork tacos').imgs.map(k => IMG.get(k))).then(a => a.every(Boolean))"))
    # --- delete removes it everywhere, pictures too ---
    before = store()['count']
    A.locator('#mealsView .meal:has-text("Pulled pork tacos")').click(); A.wait_for_timeout(300)
    A.click('#sheet [data-mact="del"]'); A.wait_for_timeout(100)
    check('Delete needs a second tap', A.evaluate("state.meals.length") == 3)
    A.click('#sheet [data-mact="del"]'); settle(A, B, ms=1500)
    check('Deleted on both phones', A.evaluate("state.meals.some(m=>m.name==='Pulled pork tacos')") is False and B.evaluate("state.meals.some(m=>m.name==='Pulled pork tacos')") is False)
    check('Its pictures are deleted from the shared list', store()['count'] <= before - 3)

    # --- hide the Meals tab ---
    A.evaluate("openTabsSheet()"); A.wait_for_timeout(300); A.click('#sheet [data-act="tabToggle"][data-tab="meals"]'); A.wait_for_timeout(250)
    check('Meals tab can be hidden', A.locator('#tabs .tab.meals').count() == 0 and A.text_content('#title') != 'Meals')
    ctxA.close(); ctxB.close()

    # --- before the Firestore rules change: works on the phone, says why it isn't sharing ---
    ctxC, C = phone(p, b)
    C.add_init_script("window.__deny = /\\/(meals|images)(\\/|$)/")
    C.goto(URL); C.wait_for_timeout(500)
    C.evaluate(f"state.nameAsked=true; closeSheet(); joinSharedList('{plan}')"); C.wait_for_timeout(1500)
    C.click('#tabs .tab.meals'); C.wait_for_timeout(500)
    check('Rules missing: explains, meal still saved here', 'one-time setup' in C.text_content('#mealsView .syncnote'))
    C.evaluate("state.meals.push({ id:uid(), date:dayKey(new Date()), name:'Pasta', imgs:[], ing:'', order:1, updatedAt:Date.now() }); save(); render();")
    check('Meal kept locally', C.locator('#mealsView .meal:has-text("Pasta")').count() == 1)
    ctxC.close()

    # --- old meals are tidied away ---
    ctxD, Dd = phone(p, b)
    Dd.evaluate("""() => { const old = new Date(); old.setDate(old.getDate() - 30); state.meals = [{ id:'old', date:dayKey(old), name:'Old', imgs:[] }, { id:'new', date:dayKey(new Date()), name:'Now', imgs:[] }]; save(); }""")
    Dd.reload(); Dd.wait_for_timeout(600)
    check('Old meals are kept for good', Dd.evaluate("state.meals.map(m=>m.id)") == ['old', 'new'])
    Dd.evaluate("state.nameAsked=true; closeSheet()"); Dd.wait_for_timeout(300)
    Dd.click('#tabs .tab.meals'); Dd.wait_for_timeout(300)
    for _ in range(5): Dd.click('#mealsView [data-mact="week"][data-d="-1"]'); Dd.wait_for_timeout(80)
    check('Can go back many weeks', '5 weeks ago' in Dd.text_content('#mealsView .wk'))
    Dd.click('#mealsView [data-mact="weekNow"]'); Dd.wait_for_timeout(150)
    check('Today jumps back to this week', 'This week' in Dd.text_content('#mealsView .wk'))
    ctxD.close(); b.close()
print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e and 'permission' not in e.lower()])
print('Failed:', [n for n, ok in results if not ok])

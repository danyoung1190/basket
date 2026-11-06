import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, urllib.request
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
def post(path, body): return json.loads(urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8766' + path, data=json.dumps(body).encode(), method='POST', headers={'Content-Type':'application/json'})).read())
def get(path): return json.loads(urllib.request.urlopen('http://127.0.0.1:8766' + path).read())
with sync_playwright() as p:
    b = p.chromium.launch(); ctxA, A = phone(p, b)
    A.evaluate("state.nameAsked=true; createSharedList('Home')"); A.wait_for_timeout(1500); A.keyboard.press('Escape')
    lid = A.evaluate("sharedShops()[0].shared.listId")
    # what 2.4 left behind: a meal and its picture on the Home list
    post('/set', {'path': f'lists/{lid}/meals/m1', 'data': {'id':'m1', 'date':'2026-10-29', 'name':'Old chilli', 'imgs':['p1'], 'ing':'1 onion', 'who':'', 'updatedAt':1}, 'merge': False})
    post('/set', {'path': f'lists/{lid}/images/p1', 'data': {'data':'data:image/jpeg;base64,AAAA', 'at':1}, 'merge': False})
    A.evaluate("state.mealsMoved = false; save();"); A.reload(); A.wait_for_timeout(2500)
    check('Old meal comes onto the phone', A.evaluate("state.meals.some(m => m.name === 'Old chilli')"))
    check('Its picture is kept on the phone', A.evaluate("IMG.get('p1').then(Boolean)"))
    left = get(f'/col?path=lists/{lid}/meals')['docs']; pics = get(f'/col?path=lists/{lid}/images')['docs']
    check('And it is gone from the shopping list', not left and not pics)
    check('Moved only once', A.evaluate("state.mealsMoved") is True)
    # sharing the plan then carries it, picture included
    A.click('#tabs .tab.meals'); A.wait_for_timeout(300); A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1800)
    plan = A.evaluate("mealPlanId()")
    check('Plan has the old meal and its picture', 'm1' in get(f'/col?path=lists/{plan}/meals')['docs'] and 'p1' in get(f'/col?path=lists/{plan}/images')['docs'])
    # stop sharing keeps meals
    A.click('#sheet [data-mact="mleave"]'); A.click('#sheet [data-mact="mleave"]'); A.wait_for_timeout(300)
    check('Stop sharing keeps the meals here', A.evaluate("!mealPlanId() && state.meals.length === 1"))
    b.close()
print('Failed:', [n for n, ok in results if not ok])

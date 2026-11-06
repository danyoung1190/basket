import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
SP = WORK
with sync_playwright() as p:
    b = p.chromium.launch(); ctx, A = phone(p, b)
    A.evaluate("state.nameAsked=true; addShop('Tesco'); state.tab = state.shops[0].id; save(); render();")
    for n in ['Yoghurts x10', 'Bananas', 'Milk x2', 'Bread']: add(A, n)
    A.locator('#addInput').blur(); A.wait_for_timeout(300)
    tap(A, item(A, 'Bananas')); A.wait_for_timeout(1500)
    check('One banana counts one', A.text_content('#dock .tcount') == '1')
    tap(A, item(A, 'Yoghurts')); A.wait_for_timeout(500)
    A.screenshot(path=WORK + 'ten_mid.png')
    A.wait_for_timeout(1500)
    check('Ten yoghurts count ten', A.text_content('#dock .tcount') == '11')
    check('Ten yoghurt drawings in the trolley', A.locator('#dock svg .good').count() == 11)
    check('Subtitle counts what is in the trolley', '11 in the trolley' in A.text_content('#subtitle'))
    tap(A, item(A, 'Milk')); A.wait_for_timeout(1600)
    check('Milk x2 adds two', A.text_content('#dock .tcount') == '13' and A.locator('#dock svg .good').count() == 13)
    A.screenshot(path=WORK + 'ten_done.png')
    # a huge quantity still draws sensibly, counts truly
    A.evaluate("state.items.find(i=>i.name==='Bread').qty = 40; save(); render();")
    tap(A, item(A, 'Bread')); A.wait_for_timeout(1800)
    check('40 counts 40, drawings capped', A.text_content('#dock .tcount') == '53' and A.locator('#dock svg .good').count() <= 96)
    A.screenshot(path=WORK + 'ten_full.png')
    # putting it back takes all ten out
    A.evaluate("openTrolleySheet()"); A.wait_for_timeout(400)
    A.click('#sheet .trolley-list .row.item:has-text("Yoghurts")'); A.wait_for_timeout(800)
    check('Putting yoghurts back removes all ten', A.text_content('#dock .tcount') == '43')
    b.close()
print('Failed:', [n for n, ok in results if not ok])

"""2.8.1: long meal names in the recipe library stay inside their row and never run under the Plan button."""
import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'
WORK = _tf.gettempdir() + '/trolley-tests/'
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])

NAMES = ['Chicken dippers, noodles, sweetcorn and peas', 'Chilli, lemon pasta', 'Chicken bat/pizza, mash/smiles, beans, broccoli',
         'Salmon, jackets and broccoli', 'Eggelicious wraps', 'Chorizo, wrap, cheese, waffles and beans', 'Posh dogs and chips',
         'Spicy tomato and crispy halloumi pasta', 'Supercalifragilisticexpialidociouslylongunbrokenwordofameal']

with sync_playwright() as p:
    b = p.chromium.launch()
    for dev in ('iPhone 13', 'iPhone SE'):
        ctx = b.new_context(**p.devices[dev], service_workers='block')
        ctx.route('**/firebase-config.js', lambda route, req: route.fulfill(status=200, content_type='application/javascript', body='window.BASKET_FIREBASE = {};'))
        A = ctx.new_page()
        A.on('pageerror', lambda e: errors.append(str(e)))
        A.goto(URL); A.evaluate('localStorage.clear()'); A.reload(); A.wait_for_timeout(500)
        A.evaluate("() => { if (sheetCtx) closeSheet(); }"); A.wait_for_timeout(300)
        A.evaluate("""names => { names.forEach((n, i) => { const d = new Date(); d.setDate(d.getDate() - i - 1);
            state.meals.push({ id:'m' + i, date:dayKey(d), name:n, imgs:[], ing:'', who:'', order:i, addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() }); }); save(); openLibrary(); }""", NAMES)
        A.wait_for_timeout(400)
        bad = A.evaluate("""() => [...sheet.querySelectorAll('.librow')].map(r => {
            const t = r.querySelector('.meal strong').getBoundingClientRect(), card = r.querySelector('.meal').getBoundingClientRect(),
                  plan = r.querySelector('.libagain').getBoundingClientRect(), sheetR = sheet.getBoundingClientRect();
            return { name:r.querySelector('strong').textContent, ok: t.right <= card.right - 4 && card.right <= plan.left && plan.right <= sheetR.right, lines: Math.round(t.height / 21) };
        }).filter(x => !x.ok || x.lines > 2)""")
        check(f'{dev}: every name stays in its row, at most 2 lines', not bad)
        if bad: print('   ', bad)
        wraps = A.evaluate("[...sheet.querySelectorAll('.librow .meal strong')].some(s => s.getBoundingClientRect().height > 30)")
        check(f'{dev}: long names wrap rather than being cut short', wraps)
        A.screenshot(path=WORK + f'v281_{dev.replace(" ", "")}.png')
        ctx.close()
    check('No errors', not errors)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

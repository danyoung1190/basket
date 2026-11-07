"""2.8.0: automatic daily backup to Firebase, keeping copies, going back a day, recovery code on a new phone,
backup files with screenshots, and what happens when the backup can't be saved."""
import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
from playwright.sync_api import sync_playwright
exec(open(TESTS + 'test_v15.py').read().split('\nwith sync_playwright()')[0])
import json, urllib.request, urllib.parse
_check = check
def check(name, cond, info=None):
    if not cond and info is not None: print('   got', info)
    _check(name, cond)
def srv(path):
    return json.loads(urllib.request.urlopen('http://127.0.0.1:8766/doc?path=' + urllib.parse.quote(path)).read())
def col(path):
    return json.loads(urllib.request.urlopen('http://127.0.0.1:8766/col?path=' + urllib.parse.quote(path)).read())['docs']
DAYMS = 864e5
PIC = "data:image/jpeg;base64," + "A" * 4000

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone(p, b)
    A.evaluate("addShop('Tesco'); state.tab = state.shops.find(s=>s.name==='Tesco').id; save(); render();")
    for n in ['Milk', 'Bread', 'Bin bags', 'Shampoo']: add(A, n)
    A.evaluate(f"""(async () => {{ await IMG.put('img1', '{PIC}'); state.meals = [{{ id:'m1', day:dayKey(new Date()), name:'Lasagne', imgs:['img1'] }}]; save(); }})()""")
    A.wait_for_timeout(300)

    # It runs by itself a few seconds after opening
    A.wait_for_timeout(7500)
    L = A.evaluate("bkLocal()")
    check('Backs up by itself after opening', bool(L.get('id')) and bool(L.get('lastOk')), L)
    bid = L['id']
    head = srv(f'lists/{bid}')
    check('Backup space is marked as a backup', head['exists'] and head['data']['kind'] == 'backup')
    check('One copy, with counts', len(head['data']['snaps']) == 1 and head['data']['snaps'][0]['items'] == 4, head['data'].get('snaps'))
    snap = srv(f"lists/{bid}/snaps/{head['data']['snaps'][0]['id']}")['data']
    check('Copy holds the whole state', json.loads(snap['d'])['data']['items'][0]['name'] in ('Milk', 'Bread', 'Bin bags', 'Shampoo'))
    check('Screenshot copied', srv(f'lists/{bid}/images/img1')['data']['data'] == PIC)
    check('Only once a day', A.evaluate("runBackup()") is False)

    # Big state is split into parts and read back whole
    A.evaluate("state.history = Object.fromEntries([...Array(9000)].map((_, i) => ['thing number ' + i, { n:i, last:Date.now(), name:'Thing number ' + i + ' “quoted”' }])); save();")
    ok = A.evaluate("runBackup({ force:true })")
    snaps = srv(f'lists/{bid}')['data']['snaps']
    check('Large copy split into parts', ok and snaps[0]['parts'] > 1, snaps[0])

    # Keeping: simulate 120 days of daily backups
    A.evaluate("""(async () => { const now = Date.now(); for (let d = 120; d >= 1; d--) await runBackup({ force:true, now: now - d * DAY }); })()""")
    A.wait_for_timeout(500)
    A.evaluate("runBackup({ force:true })"); A.wait_for_timeout(500)
    snaps = srv(f'lists/{bid}')['data']['snaps']
    import time
    now = time.time() * 1000
    ages = sorted((now - s['at']) / DAYMS for s in snaps)
    daily = [a for a in ages if a < 14]
    weekly = [a for a in ages if a >= 14]
    check('14 days of daily copies', len(daily) == 14 or len(daily) == 15, ages)
    check('Then about one a week for 12 weeks', 9 <= len(weekly) <= 12 and max(ages) < 84, ages)
    stored = [k for k in col(f'lists/{bid}/snaps')]
    check('Pruned copies are deleted from Firebase', len([k for k in stored if '-' in k[10:]]) <= sum((s.get('parts') or 1) - 1 for s in snaps) and len([k for k in stored if len(k) == 10]) == len(snaps), (len(stored), len(snaps)))

    # Not opening the app for months doesn't wipe them
    kept = A.evaluate("bkKeep([...Array(8)].map((_, i) => ({ id:'x' + i, at:Date.now() - (200 + i) * DAY })), Date.now()).length")
    check('Long gap: newest 5 always kept', kept == 5, kept)

    # Settings shows it
    A.evaluate("openSettings()"); A.wait_for_timeout(300)
    t = A.inner_text('#sheet')
    check('Settings says when it last backed up', 'Backed up automatically once a day' in t and 'Last:' in t, t[:300])
    A.screenshot(path=WORK + 'v280_settings.png')

    # Go back to an earlier day: remove things, put yesterday back, undo
    A.evaluate("closeSheet()"); A.wait_for_timeout(300)
    A.evaluate("state.history = {}; runBackup({ force:true })"); A.wait_for_timeout(400)
    A.evaluate("state.items = state.items.filter(i => i.name !== 'Bin bags' && i.name !== 'Shampoo'); save(); render();")
    A.evaluate("openBackupList(bkLocal().id, false)"); A.wait_for_timeout(800)
    rows = A.locator('#sheet [data-act="bkPick"]').count()
    check('Earlier days listed', rows >= 20, rows)
    A.screenshot(path=WORK + 'v280_list.png')
    A.locator('#sheet [data-act="bkPick"]').first.click(); A.wait_for_timeout(900)
    check('Asks before replacing', 'Put it back' in A.inner_text('#sheet'))
    A.click('#sheet [data-act="confirmRestore"]'); A.wait_for_timeout(500)
    check('Removed items are back', sorted(names(A, 'Tesco')) == ['Bin bags', 'Bread', 'Milk', 'Shampoo'], names(A, 'Tesco'))
    check("Putting back doesn't overwrite today's copy", A.evaluate("runBackup()") is False)
    A.evaluate("undo()"); A.wait_for_timeout(300)
    check('Undo works after putting back', sorted(names(A, 'Tesco')) == ['Bread', 'Milk'], names(A, 'Tesco'))
    A.evaluate("undo && state.items.length < 4 && (snapshot(), true)")

    # Recovery code on a brand new phone
    A.evaluate("openRecoveryCode()"); A.wait_for_timeout(300)
    code = A.inner_text('#sheet .bigcode')
    check('Recovery code shown', code.startswith('SAVE-') and len(code) == 24, code)
    A.screenshot(path=WORK + 'v280_code.png')
    ctxB, B = phone(p, b)
    B.evaluate("openRecoveryIn()"); B.wait_for_timeout(300)
    B.fill('#sheet input.code', code.lower().replace('-', ' '))
    B.click('#sheet form[data-form="save"] button[type="submit"]'); B.wait_for_timeout(1000)
    check('New phone finds the backups from a typed code', B.locator('#sheet [data-act="bkPick"]').count() >= 20)
    check('Copies marked as from another phone', 'from another phone' in B.inner_text('#sheet'))
    B.locator('#sheet [data-act="bkPick"]').first.click(); B.wait_for_timeout(900)
    B.click('#sheet [data-act="confirmRestore"]'); B.wait_for_timeout(600)
    check('New phone has the lists', sorted(names(B, 'Tesco') or []) == ['Bin bags', 'Bread', 'Milk', 'Shampoo'], names(B, 'Tesco'))
    check('New phone has the meal', B.evaluate("state.meals.length") == 1)
    check('New phone has the screenshot', B.evaluate("IMG.get('img1')") == PIC)
    LB = B.evaluate("bkLocal()")
    check('New phone carries on in the same backup', LB.get('id') == bid and LB.get('lastDay'), LB)
    B.fill('body', '') if False else None
    B.evaluate("openRecoveryIn()"); B.fill('#sheet input.code', 'SAVE-AAAA-BBBB-CCCC-DDDD')
    B.click('#sheet form[data-form="save"] button[type="submit"]'); B.wait_for_timeout(800)
    check('Wrong code says so', 'No backup found' in B.inner_text('#sheet'))
    B.evaluate("openRecoveryIn()"); B.fill('#sheet input.code', 'hello'); B.click('#sheet form[data-form="save"] button[type="submit"]'); B.wait_for_timeout(200)
    check('Nonsense code says what they look like', 'SAVE-XXXX' in B.inner_text('#sheet .err'))
    B.evaluate("closeSheet()")

    # Shared list: putting back keeps what the other person added since
    ctxC, C = phone(p, b)
    A.evaluate("makeShared(state.shops.find(s=>s.name==='Tesco'))"); A.wait_for_timeout(1500)
    lid = A.evaluate("state.shops.find(s=>s.name==='Tesco').shared.listId")
    C.evaluate(f"joinSharedList('{lid}')"); settle(A, C, ms=1500)
    A.evaluate("runBackup({ force:true })"); A.wait_for_timeout(500)
    add(C, 'Cheese'); settle(A, C, ms=1500)
    A.evaluate("state.items = state.items.filter(i => i.name !== 'Milk'); save(); render();"); settle(A, C, ms=1500)
    check('Shared: Milk gone on both', 'Milk' not in names(C, 'Tesco'))
    A.evaluate("openBackupList(bkLocal().id, false)"); A.wait_for_timeout(800)
    A.locator('#sheet [data-act="bkPick"]').first.click(); A.wait_for_timeout(900)
    A.click('#sheet [data-act="confirmRestore"]'); settle(A, C, ms=2500)
    check('Shared: Milk back on both phones', 'Milk' in names(A, 'Tesco') and 'Milk' in names(C, 'Tesco'), (names(A, 'Tesco'), names(C, 'Tesco')))
    check("Shared: the other person's Cheese kept", 'Cheese' in names(A, 'Tesco') and 'Cheese' in names(C, 'Tesco'), (names(A, 'Tesco'), names(C, 'Tesco')))

    # Shared meal plan: putting back keeps meals the other person planned since
    A.evaluate("view = 'meals'; state.view = 'meals'; render();"); A.wait_for_timeout(200)
    A.click('#mealsView [data-mact="mshare"]'); A.wait_for_timeout(1500); plan = A.evaluate("mealPlanId()"); A.keyboard.press('Escape'); A.wait_for_timeout(300)
    C.evaluate(f"state.nameAsked=true; joinSharedList('{plan}')"); settle(A, C, ms=1500)
    A.evaluate("runBackup({ force:true })"); A.wait_for_timeout(500)
    C.evaluate("state.meals.push({ id:'m2', date:dayKey(new Date()), name:'Fish pie', imgs:[], ing:'', who:'', order:2, addedDev:DEV, addedAt:Date.now(), updatedAt:Date.now() }); save(); render();")
    settle(A, C, ms=1500)
    check('Meal plan: Fish pie reached this phone', A.evaluate("state.meals.some(m => m.name === 'Fish pie')"))
    A.evaluate("openBackupList(bkLocal().id, false)"); A.wait_for_timeout(800)
    A.locator('#sheet [data-act="bkPick"]').first.click(); A.wait_for_timeout(900)
    A.click('#sheet [data-act="confirmRestore"]'); settle(A, C, ms=2500)
    check("Meal plan: the other person's newer meal kept on both", A.evaluate("state.meals.some(m => m.name === 'Fish pie')") and C.evaluate("state.meals.some(m => m.name === 'Fish pie')"))
    check('Meal plan: older meals still there', A.evaluate("state.meals.some(m => m.name === 'Lasagne')") and C.evaluate("state.meals.some(m => m.name === 'Lasagne')"))
    A.evaluate("view = 'list'; state.view = 'list'; render();")

    # Backup file now includes screenshots, and restoring a file puts them back
    with A.expect_download() as dl:
        A.evaluate("navigator.canShare = () => false; backup()")
    path = WORK + 'v280_backup.json'; dl.value.save_as(path)
    f = json.load(open(path))
    check('Backup file includes screenshots', f.get('images', {}).get('img1') == PIC)
    ctxD, D = phone(p, b)
    D.evaluate("openSettings()"); D.wait_for_timeout(300)
    D.set_input_files('#restoreInput', path); D.wait_for_timeout(600)
    D.click('#sheet [data-act="confirmRestore"]'); D.wait_for_timeout(500)
    check('Restoring a file puts screenshots back', D.evaluate("IMG.get('img1')") == PIC)

    # When it can't save: says so in Settings, retries next time, and the dot shows after 3 days
    ctxE, E = phone(p, b)
    add(E, 'Eggs')
    E.evaluate("window.__deny = /^lists\\//");
    E.evaluate("runBackup({ force:true })"); E.wait_for_timeout(500)
    LE = E.evaluate("bkLocal()")
    check('Failure recorded, not marked done', LE.get('lastErr') and not LE.get('lastOk') and not LE.get('lastDay'), LE)
    E.evaluate("openSettings()"); E.wait_for_timeout(300)
    check("Settings says it didn't work", "didn't work" in E.inner_text('#sheet'))
    E.evaluate("closeSheet()")
    check('No dot straight away', E.evaluate("bkFailing()") is False)
    E.evaluate("const L = bkLocal(); L.lastTry = Date.now(); L.lastOk = Date.now() - 4 * DAY; bkStore(L); renderBadge();")
    check('Dot after 3 days without a backup', E.evaluate("!$('#badge').hidden"))
    E.evaluate("window.__deny = null"); E.evaluate("runBackup()"); E.wait_for_timeout(600)
    check('Works again once allowed', E.evaluate("!!bkLocal().lastOk && !bkLocal().lastErr && $('#badge').hidden"))

    # Nothing to save: no empty backups
    ctxF, F = phone(p, b)
    F.wait_for_timeout(7000)
    check('Empty phone makes no backup', not F.evaluate("bkLocal().id"))

    errs = [e for e in errors if 'Failed to load resource' not in e and 'ERR_' not in e and 'permission' not in e.lower()]
    check('No errors', not errs, errs)
    b.close()
print('Failed:', [n for n, ok in results if not ok])

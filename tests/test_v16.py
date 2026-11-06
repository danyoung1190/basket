import os as _os, tempfile as _tf
TESTS = _os.path.dirname(_os.path.abspath(__file__)) + '/'   # this folder
WORK = _tf.gettempdir() + '/trolley-tests/'                  # screenshots and scratch files
_os.makedirs(WORK, exist_ok=True)
import json, subprocess, urllib.request
from playwright.sync_api import sync_playwright
src = open(TESTS + 'test_v15.py').read()
exec(src.split("with sync_playwright() as p:\n    b = p.chromium.launch()\n")[0])
SP = WORK

def phone2(p, b, perms=None):
    ctx = b.new_context(**p.devices['iPhone 13'], service_workers='block', permissions=perms or [])
    ctx.route('https://www.gstatic.com/firebasejs/**', lambda route, req: route.fulfill(status=200, headers={'Content-Type': 'application/javascript', 'Access-Control-Allow-Origin': '*'}, body=open(FAKE + req.url.split('/')[-1]).read()))
    ctx.route('**/firebase-config.js', lambda route, req: route.fulfill(status=200, content_type='application/javascript', body=CONFIG_JS))
    pg = ctx.new_page()
    pg.add_init_script("Object.defineProperty(navigator, 'standalone', { get: () => true })")
    pg.on('pageerror', lambda e: errors.append(str(e)))
    pg.goto(URL); pg.evaluate('localStorage.clear()'); pg.reload(); pg.wait_for_timeout(700); pg.evaluate("() => { if (sheetCtx && sheetCtx.type === 'welcome') closeSheet(); }"); pg.wait_for_timeout(350)
    return ctx, pg

with sync_playwright() as p:
    b = p.chromium.launch()
    ctxA, A = phone2(p, b)
    # + Add menu
    tap(A, '.tab.add'); A.wait_for_timeout(350)
    check('+ Add opens menu with 3 choices', A.locator('#sheet .menu-item').count() == 3)
    A.screenshot(path=OUT + 'v16-01-menu.png')
    A.click('#sheet [data-act="menuShop"]'); A.wait_for_timeout(300)
    A.click('#sheet [data-v="Tesco"]'); A.wait_for_timeout(300)
    check('New shop from menu', A.evaluate("state.shops.some(s=>s.name==='Tesco')"))
    tap(A, '.tab.add'); A.wait_for_timeout(350)
    A.click('#sheet [data-act="menuShared"]'); A.wait_for_timeout(300)
    A.fill('#sheet input.field', 'Home'); A.press('#sheet input.field', 'Enter'); A.wait_for_timeout(1200)
    code = A.locator('#sheet .bigcode').text_content().strip()
    check('Shared list created from menu', code.startswith('TRLY-'))
    A.screenshot(path=OUT + 'v16-02-share.png')
    A.locator('#sheet .qr').screenshot(path=SP + 'qr.png')
    A.keyboard.press('Escape'); A.wait_for_timeout(300)
    add(A, 'Milk'); A.locator('#addInput').blur(); A.wait_for_timeout(800)

    # Build a fake camera feed showing that QR
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-loop', '1', '-i', SP + 'qr.png', '-t', '3', '-r', '15',
                    '-vf', 'scale=420:-1,pad=1280:720:(ow-iw)/2:(oh-ih)/2:white,format=yuv420p', SP + 'cam.y4m'], check=True)

    # Paste flow on phone B (whole WhatsApp message on the clipboard)
    ctxB, B = phone2(p, b, perms=['clipboard-read', 'clipboard-write'])
    check('Empty app offers Join a shared list', B.locator('#empty [data-act="joinStart"]').count() == 1)
    B.click('#empty [data-act="joinStart"]'); B.wait_for_timeout(350)
    B.screenshot(path=OUT + 'v16-03-join.png')
    msg = f'Join my "Home" list in Basket. Copy this whole message...\n\n{code}\n\nDon\'t have Basket yet?'
    B.evaluate("t => navigator.clipboard.writeText(t)", msg)
    B.click('#sheet [data-act="pasteCode"]'); B.wait_for_timeout(1500)
    check('Paste of a whole message joins in one tap', names(B, 'Home') == ['Milk'])
    check('Join sheet closed with toast', 'Joined Home' in B.locator('#toast').text_content())
    # Paste with nothing useful
    B.evaluate("navigator.clipboard.writeText('hello there')")
    tap(B, '.tab.add'); B.wait_for_timeout(300); B.click('#sheet [data-act="menuJoin"]'); B.wait_for_timeout(300)
    B.click('#sheet [data-act="pasteCode"]'); B.wait_for_timeout(500)
    check('Paste without a code explains', 'No Virtual Trolley code found' in B.locator('#sheet .err').text_content())
    ctxB.close()
    b.close()

    # Scan flow on phone C with the fake camera
    b2 = p.chromium.launch(args=['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream', f'--use-file-for-fake-video-capture={SP}cam.y4m'])
    ctxC, C = phone2(p, b2, perms=['camera'])
    tap(C, '.tab.add'); C.wait_for_timeout(300); C.click('#sheet [data-act="menuJoin"]'); C.wait_for_timeout(300)
    C.click('#sheet [data-act="scanCode"]'); C.wait_for_timeout(600)
    C.screenshot(path=OUT + 'v16-04-scan.png')
    for _ in range(40):
        if names(C, 'Home'): break
        C.wait_for_timeout(250)
    check('In-app scan joins the list', names(C, 'Home') == ['Milk'])
    check('Camera released after scan', C.evaluate("scan === null"))
    # Cancel releases camera (decoder stubbed so it keeps looking)
    C.evaluate("window.jsQR = () => null")
    tap(C, '.tab.add'); C.wait_for_timeout(300); C.click('#sheet [data-act="menuJoin"]'); C.wait_for_timeout(300)
    C.click('#sheet [data-act="scanCode"]'); C.wait_for_timeout(500)
    C.click('#sheet [data-act="scanStop"]'); C.wait_for_timeout(300)
    check('Cancel stops the camera', C.evaluate("scan === null") and C.locator('#sheet [data-act="scanCode"]').count() == 1)
    C.keyboard.press('Escape'); C.wait_for_timeout(300)
    b2.close()

    # No camera available: graceful
    b3 = p.chromium.launch()
    ctxD, D = phone2(p, b3)
    D.evaluate("() => { navigator.mediaDevices.getUserMedia = () => Promise.reject(Object.assign(new Error('no'), { name:'NotAllowedError' })); }")
    tap(D, '.tab.add'); D.wait_for_timeout(300); D.click('#sheet [data-act="menuJoin"]'); D.wait_for_timeout(300)
    D.click('#sheet [data-act="scanCode"]'); D.wait_for_timeout(600)
    check('Blocked camera explained, back on join sheet', 'blocked' in D.locator('#toast').text_content() and D.locator('#sheet [data-act="pasteCode"]').count() == 1)
    # Typing still works, with sloppy input
    D.fill('#sheet input.code', code.replace('-', ' ').lower()); D.click('#sheet button[type="submit"]'); D.wait_for_timeout(1500)
    check('Typed code still works', names(D, 'Home') == ['Milk'])
    b3.close()

print('\nConsole errors:', [e for e in errors if 'Failed to load resource' not in e])
print('Failed:', [n for n, ok in results if not ok])

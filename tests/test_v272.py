"""Updates must land. Serves a copy of the app from a server with no cache headers (so the browser's own
web cache holds old copies, as it did on the phone), ships a new version, and reopens the app.
Runs the old service worker as a control: it must show the stale copy, proving the test catches the bug."""
import os, shutil, subprocess, time, tempfile, re
from playwright.sync_api import sync_playwright
TESTS = os.path.dirname(os.path.abspath(__file__)) + '/'
REPO = os.path.dirname(TESTS.rstrip('/')) + '/'
WORK = tempfile.gettempdir() + '/trolley-tests/'
os.makedirs(WORK, exist_ok=True)
results = []
def check(name, cond, info=None):
    results.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name + ('' if cond or info is None else f'   got {info}'))

OLD_SW = subprocess.run(['git', '-C', REPO, 'show', '7ae1aef:sw.js'], capture_output=True, text=True).stdout
OLD_IDX = subprocess.run(['git', '-C', REPO, 'show', '7ae1aef:index.html'], capture_output=True, text=True).stdout

def site(port, sw, idx):
    d = WORK + f'site{port}/'
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(REPO, d, ignore=shutil.ignore_patterns('tests', '.git', 'ocr', 'vendor'))
    open(d + 'sw.js', 'w').write(sw); open(d + 'index.html', 'w').write(idx)
    old = time.time() - 30 * 86400   # old Last-Modified, so the browser treats its copy as fresh for days
    for f in os.listdir(d):
        if os.path.isfile(d + f): os.utime(d + f, (old, old))
    srv = subprocess.Popen(['python3', '-m', 'http.server', str(port)], cwd=d, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.8)
    return d, srv

def ship(d, version):
    for f, pat, rep in (('index.html', r"const APP_VERSION = '[^']+'", f"const APP_VERSION = '{version}'"),
                        ('sw.js', r"const CACHE = '[^']+'", f"const CACHE = 'trolley-{version}'")):
        s = open(d + f).read(); open(d + f, 'w').write(re.sub(pat, rep, s))

def version(pg):
    try: return pg.evaluate("typeof APP_VERSION === 'string' ? APP_VERSION : null")
    except Exception: return None

def run(port, sw, idx, opens, to=None):
    d, srv = site(port, sw, idx)
    seen = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            ctx = b.new_context(viewport={'width': 390, 'height': 844})
            pg = ctx.new_page()
            url = f'http://localhost:{port}/'
            pg.goto(url); pg.wait_for_function("navigator.serviceWorker.controller || new Promise(r => navigator.serviceWorker.addEventListener('controllerchange', r))", timeout=15000)
            pg.reload(); pg.wait_for_timeout(800)
            first = version(pg)
            if to: open(d + 'sw.js', 'w').write(to[0]); open(d + 'index.html', 'w').write(to[1])
            else: ship(d, '9.9.9')
            for _ in range(opens):
                pg.close(); pg = ctx.new_page(); pg.goto(url); pg.wait_for_timeout(4000)
                seen.append(version(pg))
            b.close()
    finally:
        srv.terminate()
    return first, seen

# Control: the old service worker keeps serving the stale page
first, seen = run(8781, OLD_SW, OLD_IDX, 3)
print('old worker:', first, seen)
check('Control: old code is stuck on the old version after 3 reopens', seen[-1] != '9.9.9')

# Fixed: the new version shows on the first reopen (it switches over by itself)
first, seen = run(8782, open(REPO + 'sw.js').read(), open(REPO + 'index.html').read(), 2)
print('new worker:', first, seen)
check('Starts on the current version', first and first != '9.9.9')
check('New version shows on the first reopen', seen[0] == '9.9.9', seen)
check('And stays', seen[-1] == '9.9.9', seen)
# The phone today: old code running, this release arrives
NEW = (open(REPO + 'sw.js').read(), open(REPO + 'index.html').read())
NEWV = re.search(r"APP_VERSION = '([^']+)'", NEW[1]).group(1)
first, seen = run(8783, OLD_SW, OLD_IDX, 3, to=NEW)
print('old to new:', first, seen)
check('From the old version, this release lands within two reopens', NEWV in seen[:2], seen)
print('Failed:', [n for n, ok in results if not ok])

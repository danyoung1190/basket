import json, threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
STORE = {}; LOCK = threading.Lock(); WRITES = [0]
class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def _send(self, obj, code=200):
        b = json.dumps(obj).encode()
        self.send_response(code); self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Access-Control-Allow-Headers', '*')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_OPTIONS(self): self._send({})
    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query); path = q.get('path', [''])[0]
        with LOCK:
            if u.path == '/col':
                pre = path.rstrip('/') + '/'
                docs = {k[len(pre):]: v for k, v in STORE.items() if k.startswith(pre) and '/' not in k[len(pre):]}
                return self._send({'docs': docs})
            if u.path == '/doc':
                return self._send({'exists': path in STORE, 'data': STORE.get(path)})
            if u.path == '/stats':
                return self._send({'writes': WRITES[0], 'count': len(STORE)})
        self._send({'error': 'nf'}, 404)
    def do_POST(self):
        n = int(self.headers.get('Content-Length', 0)); body = json.loads(self.rfile.read(n) or b'{}')
        with LOCK:
            if self.path == '/set':
                WRITES[0] += 1
                if body.get('merge') and body['path'] in STORE: STORE[body['path']].update(body['data'])
                else: STORE[body['path']] = body['data']
            elif self.path == '/del':
                WRITES[0] += 1; STORE.pop(body['path'], None)
            elif self.path == '/reset':
                STORE.clear(); WRITES[0] = 0
        self._send({'ok': True})
ThreadingHTTPServer(('127.0.0.1', 8766), H).serve_forever()

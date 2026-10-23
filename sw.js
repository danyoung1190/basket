// Trolley service worker: makes the app open with no signal.
// When you change any app file, bump CACHE (e.g. basket-v2) so phones pick up the new version.
const CACHE = 'trolley-v15';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './qrcode.js',
  './jsqr.js',
  './firebase-config.js',
  './icons/icon-180.png',
  './icons/icon-192.png',
  './icons/icon-512.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE && k !== CACHE + '-sdk').map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

// Cache first so the app opens instantly in a shop with bad signal,
// then refresh the cached copy in the background when online.
self.addEventListener('fetch', event => {
  const req = event.request;
  const url = new URL(req.url);
  // The Firebase SDK is fetched from Google. Keep a copy so sharing still starts with no signal.
  if (req.method === 'GET' && url.hostname === 'www.gstatic.com' && url.pathname.startsWith('/firebasejs/')) {
    event.respondWith(caches.open(CACHE + '-sdk').then(async cache => {
      const hit = await cache.match(req);
      if (hit) return hit;
      const res = await fetch(req);
      if (res && res.ok) cache.put(req, res.clone());
      return res;
    }));
    return;
  }
  if (req.method !== 'GET' || url.origin !== self.location.origin) return;
  const isPage = req.mode === 'navigate';
  event.respondWith(
    caches.open(CACHE).then(async cache => {
      const cached = await cache.match(isPage ? './index.html' : req, { ignoreSearch: true });
      const network = fetch(req)
        .then(res => {
          if (res && res.ok) cache.put(isPage ? './index.html' : req, res.clone());
          return res;
        })
        .catch(() => null);
      if (cached) { event.waitUntil(network); return cached; }
      const res = await network;
      return res || new Response('Offline', { status: 503, headers: { 'Content-Type': 'text/plain' } });
    })
  );
});

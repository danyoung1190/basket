// Minimal fake of the Firestore API Basket uses, backed by a local HTTP store shared by every "phone".
const SRV = 'http://127.0.0.1:8766';
const cache = new Map(); const queue = []; const pendingDel = new Set(); const listeners = [];
let flushing = false;
window.__offline = window.__offline || false;
function unavailable(){ const e = new Error('offline'); e.code = 'unavailable'; return e; }
async function call(method, path, body){
  if (window.__offline) throw unavailable();
  const r = await fetch(SRV + path, { method, headers:{ 'Content-Type':'application/json' }, body: body ? JSON.stringify(body) : undefined });
  return r.json();
}
export function initializeFirestore(app, opts){ return { app, opts }; }
export function getFirestore(app){ return { app }; }
export function persistentLocalCache(o){ return o; }
export function persistentMultipleTabManager(){ return {}; }
export function doc(db, ...segs){ return { type:'doc', path:segs.join('/') }; }
export function collection(db, ...segs){ return { type:'col', path:segs.join('/') }; }
const snapOf = (path, data, pending) => ({ id:path.split('/').pop(), ref:{ path }, exists:() => data !== undefined && data !== null, data:() => data, metadata:{ hasPendingWrites:pending, fromCache:false } });
function notify(){ listeners.forEach(l => l.tick(true)); }
async function flush(){
  if (flushing || window.__offline) return; flushing = true;
  while (queue.length && !window.__offline) {
    const op = queue[0];
    try { await call('POST', op.type === 'set' ? '/set' : '/del', op); queue.shift(); if (op.type === 'del') pendingDel.delete(op.path); }
    catch(e) { break; }
  }
  flushing = false;
}
const denied = path => window.__deny && window.__deny.test(path);
function deniedErr(){ const e = new Error('Missing or insufficient permissions.'); e.code = 'permission-denied'; return e; }
export async function getDoc(ref){ if (denied(ref.path)) throw deniedErr(); try { return await getDocFromServer(ref); } catch(e) { const d = cache.get(ref.path); return snapOf(ref.path, d, false); } }
export async function setDoc(ref, data, opts){
  if (denied(ref.path)) throw deniedErr();
  const cur = cache.get(ref.path) || {};
  cache.set(ref.path, opts && opts.merge ? Object.assign({}, cur, data) : Object.assign({}, data));
  queue.push({ type:'set', path:ref.path, data:cache.get(ref.path), merge:!!(opts && opts.merge) });
  notify(); flush();
}
export async function deleteDoc(ref){
  cache.delete(ref.path); pendingDel.add(ref.path);
  queue.push({ type:'del', path:ref.path }); notify(); flush();
}
export async function getDocFromServer(ref){ const r = await call('GET', `/doc?path=${encodeURIComponent(ref.path)}`); return snapOf(ref.path, r.exists ? r.data : undefined, false); }
export async function getDocsFromServer(ref){ const r = await call('GET', `/col?path=${encodeURIComponent(ref.path)}`); return { docs:Object.entries(r.docs).map(([id, d]) => snapOf(ref.path + '/' + id, d, false)) }; }
// Like the real one: waits until the server has every queued write (gives up only when offline).
export async function waitForPendingWrites(){ while (queue.length && !window.__offline) { await flush(); if (queue.length) await new Promise(r => setTimeout(r, 20)); } if (queue.length) throw unavailable(); }
export function onSnapshot(ref, opts, cb, errCb){
  if (typeof opts === 'function') { errCb = cb; cb = opts; opts = {}; }
  if (denied(ref.path)) { setTimeout(() => errCb && errCb(deniedErr()), 30); return () => {}; }
  const L = { ref, prev:null, stopped:false };
  L.tick = async (localOnly) => {
    if (L.stopped) return;
    let docs = new Map(), fromCache = true;
    if (!localOnly && !window.__offline) {
      try {
        if (ref.type === 'col') { const r = await call('GET', `/col?path=${encodeURIComponent(ref.path)}`); Object.entries(r.docs).forEach(([id, d]) => docs.set(ref.path + '/' + id, d)); }
        else { const r = await call('GET', `/doc?path=${encodeURIComponent(ref.path)}`); if (r.exists) docs.set(ref.path, r.data); }
        fromCache = false;
        // server truth replaces cache for this ref, except docs still queued locally
        const queuedPaths = new Set(queue.map(q => q.path));
        [...cache.keys()].filter(k => ref.type === 'col' ? (k.startsWith(ref.path + '/') && !k.slice(ref.path.length + 1).includes('/')) : k === ref.path)
          .forEach(k => { if (!queuedPaths.has(k)) cache.delete(k); });
        docs.forEach((d, k) => { if (!queuedPaths.has(k)) cache.set(k, d); });
      } catch(e) { fromCache = true; }
    }
    // Build the view from cache (which now includes local pending writes).
    const view = new Map();
    [...cache.entries()].forEach(([k, d]) => { if (ref.type === 'col' ? (k.startsWith(ref.path + '/') && !k.slice(ref.path.length + 1).includes('/')) : k === ref.path) view.set(k, d); });
    const pendingPaths = new Set(queue.map(q => q.path));
    const changes = [];
    const prev = L.prev || new Map();
    view.forEach((d, k) => { if (!prev.has(k)) changes.push({ type:'added', doc:snapOf(k, d, pendingPaths.has(k)) }); else if (JSON.stringify(prev.get(k)) !== JSON.stringify(d)) changes.push({ type:'modified', doc:snapOf(k, d, pendingPaths.has(k)) }); });
    prev.forEach((d, k) => { if (!view.has(k)) changes.push({ type:'removed', doc:snapOf(k, d, pendingDel.has(k) || pendingPaths.has(k)) }); });
    const metaChanged = L.lastMeta !== `${fromCache}|${pendingPaths.size > 0}`;
    L.lastMeta = `${fromCache}|${pendingPaths.size > 0}`;
    if (!changes.length && L.prev && !(opts.includeMetadataChanges && metaChanged)) return;
    L.prev = view;
    const hasPending = [...view.keys()].some(k => pendingPaths.has(k)) || [...pendingDel].some(k => ref.type === 'col' ? k.startsWith(ref.path + '/') : k === ref.path);
    if (ref.type === 'col') {
      const arr = [...view.entries()].map(([k, d]) => snapOf(k, d, pendingPaths.has(k)));
      cb({ forEach:f => arr.forEach(f), docs:arr, docChanges:() => changes, metadata:{ fromCache, hasPendingWrites:hasPending }, size:arr.length });
    } else {
      const d = view.get(ref.path);
      const sn = snapOf(ref.path, d, pendingPaths.has(ref.path)); sn.metadata = { fromCache, hasPendingWrites:hasPending };
      cb(sn);
    }
  };
  listeners.push(L);
  L.tick(true); L.tick(false);
  L.timer = setInterval(() => { flush(); L.tick(false); }, 250);
  return () => { L.stopped = true; clearInterval(L.timer); const i = listeners.indexOf(L); if (i >= 0) listeners.splice(i, 1); };
}

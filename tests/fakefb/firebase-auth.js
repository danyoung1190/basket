export function getAuth(app){ return { app, user:null, cbs:[] }; }
export function onAuthStateChanged(auth, cb){ auth.cbs.push(cb); if (auth.user) cb(auth.user); return () => { auth.cbs = auth.cbs.filter(c => c !== cb); }; }
export async function signInAnonymously(auth){ if (window.__authFail) { const e = new Error('nope'); e.code = 'auth/operation-not-allowed'; throw e; } auth.user = { uid:'anon-' + Math.random().toString(36).slice(2) }; auth.cbs.forEach(c => c(auth.user)); return { user:auth.user }; }

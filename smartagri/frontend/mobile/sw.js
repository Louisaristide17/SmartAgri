/* ============================================================
   SmartAgri — Service Worker (PWA offline)
   ============================================================ */
const CACHE_NAME   = 'smartagri-v2.2-session';
const CACHE_ASSETS = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './manifest.json',
  './icon-192.svg',
  './icon-512.svg',
];

/* ── Installation : mettre en cache les fichiers de base ── */
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(CACHE_ASSETS))
      .catch(err => console.log('Cache error:', err))
  );
  self.skipWaiting();
});

/* ── Activation : nettoyer les anciens caches ── */
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME)
            .map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

/* ── Fetch : stratégie cache-first pour les assets,
   network-first pour l'API ── */
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // API → toujours network (données fraîches)
  if (url.hostname.includes('localhost') && url.port === '8000') {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(
          JSON.stringify({ detail: 'Hors ligne — serveur indisponible' }),
          { status: 503, headers: { 'Content-Type': 'application/json' } }
        );
      })
    );
    return;
  }

  // Assets → cache-first
  event.respondWith(
    caches.match(event.request).then(cached => {
      if (cached) return cached;
      return fetch(event.request).then(response => {
        if (response.ok && response.type === 'basic') {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      }).catch(() => cached);
    })
  );
});

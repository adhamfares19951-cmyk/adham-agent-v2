const CACHE_NAME = 'adham-hq-v1';
const ASSETS = [
  '/',
  '/manifest.json'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) return caches.delete(key);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Network first, falling back to cache
  if (e.request.url.includes('/api/') || e.request.url.includes('/ws/')) {
    return; // Don't cache dynamic APIs
  }
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});
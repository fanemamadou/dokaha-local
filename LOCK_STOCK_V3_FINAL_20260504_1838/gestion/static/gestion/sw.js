const CACHE_NAME = 'dokaha-v1';
const ASSETS = [
  '/', '/dashboard/', '/accounts/login/',
  '/static/gestion/base.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS)));
});

self.addEventListener('fetch', e => {
  // Stratégie : Network first, fallback cache
  e.respondWith(
    fetch(e.request).catch(() => caches.match(e.request))
  );
});

// Sync background pour formulaires hors-ligne (optionnel)
self.addEventListener('sync', e => {
  if (e.tag === 'sync-forms') {
    // À implémenter : rejouer les submissions en attente
    console.log('🔄 Sync formulaires déclenchée');
  }
});

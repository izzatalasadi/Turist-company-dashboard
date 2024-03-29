const CACHE_NAME = 'v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/css/styles.css',  // Adjust based on your actual CSS file path
  '/static/js/scripts.js',   // Adjust based on your actual JS file path
  // Add other resources you want to cache
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('Opened cache');
        return cache.addAll(urlsToCache);
      })
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) {
          return response;
        }
        return fetch(event.request);
      }
    )
  );
});

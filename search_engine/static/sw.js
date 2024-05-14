const CACHE_NAME = 'DMC_nordic_v1';
const urlsToCache = [
  '/',
  '/index.html',
  '/static/css/style.css',
  '/static/css/styles.css',
  '/static/js/scripts.js',
  '/static/js/vendor.bundle.base.js',
  '/static/js/bootstrap-datepicker.min.js',
  '/static/js/off-canvas.js',
  '/static/js/hoverable-collapse.js',
  '/static/js/template.js',
  '/static/js/settings.js',
  '/static/images/faces/face1.jpeg', // Example image
  
];

// Install event - cache static assets
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      console.log('Opened cache');
      return cache.addAll(urlsToCache);
    }).catch(function(error) {
      console.error('Caching failed:', error);
    })
  );

  // Fetch guest data and add it to the cache
  event.waitUntil(
    fetch('/api/guests')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch guests data');
        }
        return response.json().catch(() => {
          throw new Error('Guest data is not valid JSON');
        });
      })
      .then(guests => {
        if (!Array.isArray(guests)) {
          throw new Error('Guest data is not an array');
        }
        const guestRequests = guests.map(guest => {
          return new Request(`/guests/${guest.id}`, { cache: 'reload' });
        });
        return caches.open(CACHE_NAME).then(cache => {
          return cache.addAll(guestRequests);
        });
      }).catch(error => {
        console.error('Failed to cache guest data:', error);
      })
  );

  // Fetch PDFs and add them to the cache
  event.waitUntil(
    fetch('/api/pdfs')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to fetch PDFs data');
        }
        return response.json().catch(() => {
          throw new Error('PDF data is not valid JSON');
        });
      })
      .then(pdfs => {
        if (!Array.isArray(pdfs)) {
          throw new Error('PDF data is not an array');
        }
        const pdfRequests = pdfs.map(pdf => {
          return new Request(`/static/pdf/${pdf.filename}`, { cache: 'reload' });
        });
        return caches.open(CACHE_NAME).then(cache => {
          return cache.addAll(pdfRequests);
        });
      }).catch(error => {
        console.error('Failed to cache PDF files:', error);
      })
  );
});

// Fetch event - respond with cached resources or fetch from network
self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      if (response) {
        return response;
      }
      return fetch(event.request).then(networkResponse => {
        if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
          return networkResponse;
        }
        const responseToCache = networkResponse.clone();
        caches.open(CACHE_NAME).then(cache => {
          cache.put(event.request, responseToCache);
        });
        return networkResponse;
      });
    }).catch(error => {
      console.error('Fetch failed:', error);
    })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});
const CACHE_NAME = 'extreme-tech-v1';
const urlsToCache = [
  '/',
  '/offline.html',
  '/static/manifest.json',
  '/static/Extreme Tech Log.png',
  '/static/android/launchericon-48x48.png',
  '/static/android/launchericon-72x72.png',
  '/static/android/launchericon-96x96.png',
  '/static/android/launchericon-144x144.png',
  '/static/android/launchericon-192x192.png',
  '/static/android/launchericon-512x512.png',
  '/static/ios/180.png',
  '/static/windows/Square150x150Logo.scale-100.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// Install event: cache essential files
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(urlsToCache).catch(err => {
        console.warn('Failed to cache some urls:', err);
      });
    })
  );
  self.skipWaiting();
});

// Activate event: clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames
          .filter(cacheName => cacheName !== CACHE_NAME)
          .map(cacheName => caches.delete(cacheName))
      );
    })
  );
  self.clients.claim();
});

// Fetch event: serve from cache, fallback to network
self.addEventListener('fetch', event => {
  const { request } = event;

  // Skip non-GET requests
  if (request.method !== 'GET') {
    event.respondWith(fetch(request));
    return;
  }

  // Strategy: Cache First, then Network
  event.respondWith(
    caches.match(request).then(response => {
      if (response) {
        return response;
      }

      return fetch(request)
        .then(networkResponse => {
          // Cache successful responses for offline use
          if (networkResponse && networkResponse.status === 200) {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(error => {
          console.warn('Fetch failed:', error);
          
          // Return offline page for HTML requests
          if (request.headers.get('accept')?.includes('text/html')) {
            return caches.match('/offline.html').catch(() => {
              return new Response('Offline - Please check your connection', {
                status: 503,
                statusText: 'Service Unavailable',
                headers: new Headers({
                  'Content-Type': 'text/plain'
                })
              });
            });
          }
          
          // Return error response for other types
          return new Response('Network error occurred', {
            status: 503,
            statusText: 'Service Unavailable'
          });
        });
    })
  );
});

// Handle messages from clients
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background sync for offline sales (optional, requires BackgroundSync API)
self.addEventListener('sync', event => {
  if (event.tag === 'sync-sales') {
    event.waitUntil(syncSalesData());
  }
});

async function syncSalesData() {
  try {
    const db = await openIndexedDB();
    const pendingSales = await getPendingSales(db);
    
    for (const sale of pendingSales) {
      try {
        const response = await fetch('/sales/pos_process/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': await getCSRFToken()
          },
          body: JSON.stringify(sale)
        });
        
        if (response.ok) {
          await markSaleSynced(db, sale.id);
        }
      } catch (error) {
        console.warn('Failed to sync sale:', error);
      }
    }
  } catch (error) {
    console.error('Background sync error:', error);
  }
}

function openIndexedDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open('extremeTechDB', 1);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = event => {
      const db = event.target.result;
      if (!db.objectStoreNames.contains('pendingSales')) {
        db.createObjectStore('pendingSales', { keyPath: 'id' });
      }
    };
  });
}

async function getPendingSales(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingSales', 'readonly');
    const store = tx.objectStore('pendingSales');
    const request = store.getAll();
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
  });
}

async function markSaleSynced(db, saleId) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction('pendingSales', 'readwrite');
    const store = tx.objectStore('pendingSales');
    const request = store.delete(saleId);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve();
  });
}

async function getCSRFToken() {
  const response = await fetch('/');
  const html = await response.text();
  const match = html.match(/name="csrfmiddlewaretoken"\s+value="([^"]+)"/);
  return match ? match[1] : '';
}

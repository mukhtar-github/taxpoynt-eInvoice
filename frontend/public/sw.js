/**
 * Service Worker for Nigerian Mobile PWA
 * Optimized for Nigerian network conditions
 */

const CACHE_NAME = 'taxpoynt-v1';
const STATIC_CACHE = 'taxpoynt-static-v1';
const DYNAMIC_CACHE = 'taxpoynt-dynamic-v1';

// Critical resources to cache immediately
const STATIC_ASSETS = [
  '/',
  '/dashboard',
  '/dashboard/transmission',
  '/dashboard/integrations',
  '/manifest.json',
  '/icons/logo.svg'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /^\/api\/dashboard/,
  /^\/api\/integrations/,
  /^\/api\/transmission/
];

// Network-first cache strategy for dynamic content
const NETWORK_FIRST_PATTERNS = [
  /^\/api\/firs/,
  /^\/api\/real-time/
];

// Cache-first strategy for static assets
const CACHE_FIRST_PATTERNS = [
  /\.(css|js|png|jpg|jpeg|gif|svg|webp|woff|woff2)$/,
  /^\/icons\//,
  /^\/images\//
];

self.addEventListener('install', (event) => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('Precaching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        // Skip waiting to activate immediately
        return self.skipWaiting();
      })
  );
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          // Delete old caches
          if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
            console.log('Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      // Take control immediately
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different caching strategies
  if (CACHE_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(cacheFirst(request));
  } else if (NETWORK_FIRST_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(networkFirst(request));
  } else if (API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
    event.respondWith(staleWhileRevalidate(request));
  } else {
    event.respondWith(networkFirst(request));
  }
});

// Cache-first strategy (good for static assets)
async function cacheFirst(request) {
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(STATIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('Cache-first fetch failed:', error);
    return new Response('Network error', { status: 503 });
  }
}

// Network-first strategy (good for dynamic content)
async function networkFirst(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.log('Network-first fetch failed, trying cache:', error);
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      return caches.match('/offline.html') || 
             new Response('Offline', { status: 503 });
    }
    
    return new Response('Network error', { status: 503 });
  }
}

// Stale-while-revalidate strategy (good for API calls)
async function staleWhileRevalidate(request) {
  const cache = await caches.open(DYNAMIC_CACHE);
  const cachedResponse = await cache.match(request);
  
  const fetchPromise = fetch(request).then((response) => {
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  }).catch(() => {
    console.log('Stale-while-revalidate fetch failed');
    return cachedResponse;
  });
  
  // Return cached response immediately if available, otherwise wait for network
  return cachedResponse || fetchPromise;
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync-invoices') {
    event.waitUntil(syncInvoices());
  }
});

async function syncInvoices() {
  try {
    // Get pending invoices from IndexedDB or localStorage
    const pendingInvoices = await getPendingInvoices();
    
    for (const invoice of pendingInvoices) {
      try {
        await fetch('/api/invoices', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(invoice)
        });
        
        // Remove from pending after successful sync
        await removePendingInvoice(invoice.id);
      } catch (error) {
        console.log('Failed to sync invoice:', invoice.id, error);
      }
    }
  } catch (error) {
    console.log('Background sync failed:', error);
  }
}

// Helper functions for pending invoice management
async function getPendingInvoices() {
  // Implementation would use IndexedDB or another storage method
  return [];
}

async function removePendingInvoice(invoiceId) {
  // Implementation would remove from IndexedDB or storage
  console.log('Removing pending invoice:', invoiceId);
}

// Push notification handling
self.addEventListener('push', (event) => {
  const options = {
    body: event.data ? event.data.text() : 'New notification from TaxPoynt',
    icon: '/icons/logo.svg',
    badge: '/icons/favicon.svg',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: '1'
    },
    actions: [
      {
        action: 'explore',
        title: 'View Dashboard',
        icon: '/icons/logo.svg'
      },
      {
        action: 'close',
        title: 'Close',
        icon: '/icons/logo.svg'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('TaxPoynt', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  
  if (event.action === 'explore') {
    event.waitUntil(
      clients.openWindow('/dashboard')
    );
  }
});
/**
 * Service Worker for OCR App
 * Caches static assets for faster loading
 */

const CACHE_NAME = 'ocr-app-v1';
const STATIC_CACHE = 'static-v1';

// Assets to cache immediately
const STATIC_ASSETS = [
    '/static/assets/css/critical-ocr.css',
    '/static/assets/css/ocr-modal-fix.min.css',
    '/static/assets/css/modal.min.css',
    '/static/assets/css/ocr-pages.min.css',
    '/static/assets/js/ocr-modal-optimized.min.js',
    '/static/assets/js/force-300px-height.min.js'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('📦 Caching static assets...');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('✅ Static assets cached');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
                            console.log('🗑️ Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker activated');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Only handle GET requests
    if (request.method !== 'GET') return;
    
    // Handle static assets
    if (url.pathname.startsWith('/static/assets/')) {
        event.respondWith(
            caches.match(request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        console.log('📦 Serving from cache:', url.pathname);
                        return cachedResponse;
                    }
                    
                    // Not in cache, fetch and cache
                    return fetch(request)
                        .then((response) => {
                            // Only cache successful responses
                            if (response.status === 200) {
                                const responseClone = response.clone();
                                caches.open(STATIC_CACHE)
                                    .then((cache) => {
                                        cache.put(request, responseClone);
                                    });
                            }
                            return response;
                        })
                        .catch(() => {
                            console.log('❌ Failed to fetch:', url.pathname);
                            // Return a fallback response if needed
                            return new Response('Asset not available', {
                                status: 404,
                                statusText: 'Not Found'
                            });
                        });
                })
        );
        return;
    }
    
    // Handle HTML pages with network-first strategy
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Cache successful HTML responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then((cache) => {
                                cache.put(request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback to cache if network fails
                    return caches.match(request)
                        .then((cachedResponse) => {
                            return cachedResponse || new Response('Page not available offline', {
                                status: 503,
                                statusText: 'Service Unavailable'
                            });
                        });
                })
        );
    }
});

// Handle messages from main thread
self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_URLS') {
        const urls = event.data.urls;
        caches.open(STATIC_CACHE)
            .then((cache) => {
                return cache.addAll(urls);
            })
            .then(() => {
                event.ports[0].postMessage({ success: true });
            })
            .catch((error) => {
                event.ports[0].postMessage({ success: false, error: error.message });
            });
    }
});
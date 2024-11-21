// This is the "Offline page" service worker

importScripts('https://storage.googleapis.com/workbox-cdn/releases/5.1.2/workbox-sw.js');

const CACHE = "pwabuilder-page";

// TODO: replace the following with the correct offline fallback page i.e.: const offlineFallbackPage = "offline.html";
const offlineFallbackPage = "offline.html";

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener('install', async (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => {
        console.log('[Service Worker] Installing and caching offline fallback page:', offlineFallbackPage);
        return cache.add(offlineFallbackPage).catch(error => {
          console.error('[Service Worker] Failed to cache offline fallback page:', offlineFallbackPage, error);
        });
      })
  );
});

if (workbox.navigationPreload.isSupported()) {
  workbox.navigationPreload.enable();
}

self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith((async () => {
      try {
        const preloadResp = await event.preloadResponse;

        if (preloadResp) {
          console.log('[Service Worker] Using preload response for:', event.request.url);
          return preloadResp;
        }

        const networkResp = await fetch(event.request);
        console.log('[Service Worker] Fetched from network:', event.request.url);
        return networkResp;
      } catch (error) {
        console.error('[Service Worker] Network request failed:', event.request.url, error);

        const cache = await caches.open(CACHE);
        const cachedResp = await cache.match(offlineFallbackPage);
        if (cachedResp) {
          console.log('[Service Worker] Serving cached offline page for:', event.request.url);
          return cachedResp;
        } else {
          console.error('[Service Worker] No cached offline page found');
        }
      }
    })());
  }
});

// This is the "Offline page" service worker

importScripts('https://storage.googleapis.com/workbox-cdn/releases/5.1.2/workbox-sw.js');

const CACHE = "pwabuilder-page";

const staticFilesToCache = [
  '/',
  '/static/android-launchericon-96-96.png',
  '/static/android-launchericon-144-144.png',
  '/static/android-launchericon-512-512.png',
  '/static/Game_back.webp',
  '/static/i.jpg',
  '/static/image.webp',
  '/static/lab.svg',
  '/static/manifest.json',
  '/static/rastvory.png',
  '/static/silikislot.png',
  '/static/tabl.jpg',
  '/static/sw.js',
  '/static/favicon.svg',
  '/aboutme',
  '/all_profiles',
  '/chat',
  '/complete_reaction',
  '/documentation',
  '/edit_profile',
  '/electronic_configuration',
  '/get_reaction_chain',
  '/instruction',
  '/login',
  '/minigame',
  '/molyarnaya_massa',
  '/orghim',
  '/profile',
  '/register',
  '/tablica',
  '/tablica_kislotnosti',
  '/tablica_rastvorimosti',
  // Добавьте все файлы из директории static, которые вы хотите кэшировать
];

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener('install', async (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => {
      console.log('[Service Worker] Installing and caching static files');
      const cachePromises = staticFilesToCache.map(file => {
        return cache.add(file).then(() => {
          console.log('[Service Worker] Cached:', file);
        }).catch(error => {
          console.error('[Service Worker] Failed to cache:', file, error);
        });
      });
      return Promise.all(cachePromises);
    })
  );
});

if (workbox.navigationPreload.isSupported()) {
    workbox.navigationPreload.enable();
}

self.addEventListener('fetch', (event) => {
    // Обрабатываем только навигационные запросы (например, переходы по страницам)
    if (event.request.mode === 'navigate') {
        event.respondWith((async () => {
            // Ждем завершения запроса на предзагрузку
            const preloadResponse = await event.preloadResponse;

            // Если есть ответ от предзагрузки, возвращаем его
            if (preloadResponse) {
                console.log('[Service Worker] Using preload response for:', event.request.url);
                return preloadResponse;
            }

            // Если предзагрузки нет, пробуем получить из сети
            try {
                const networkResponse = await fetch(event.request);
                console.log('[Service Worker] Fetched from network:', event.request.url);
                return networkResponse;
            } catch (error) {
                console.error('[Service Worker] Network request failed:', event.request.url, error);

                // Если нет ответа из сети, пробуем получить из кэша
                const cache = await caches.open(CACHE);
                const cachedResponse = await cache.match(event.request);
                if (cachedResponse) {
                    console.log('[Service Worker] Serving cached response for:', event.request.url);
                    return cachedResponse;
                } else {
                    console.error('[Service Worker] No cached response found');
                    // Здесь можно вернуть страницу с ошибкой или сообщение о недоступности
                }
            }
        })());
    }
});

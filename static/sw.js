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
  '/uravnivanie',
  '/rastvory',
  '/uchebnik',
  '/orghim'
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
  event.respondWith((async () => {
    try {
      const networkResponse = await fetch(event.request);
      // Если запрос успешен, кэшируем ответ
      const cache = await caches.open(CACHE);
      cache.put(event.request, networkResponse.clone());
      return networkResponse;
    } catch (error) {
      console.error('[Service Worker] Network request failed:', event.request.url, error);
      // Попробуйте вернуть кэшированный ответ
      const cachedResponse = await caches.match(event.request);
      if (cachedResponse) {
        return cachedResponse;
      } else {
        // Возвращаем страницу с ошибкой или главную страницу
        return caches.match('/'); // Или можете указать другую страницу
      }
    }
  })());
});
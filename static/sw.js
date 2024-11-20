const CACHE_NAME = 'my-cache-v1';
const urlsToCache = [
    '/',
    'templates/index.html',
    // Добавьте другие ресурсы, которые нужно кэшировать, // Пример кэширования изображения
    // Добавьте другие изображения и CSS-файлы
];

// Установка service worker и кэширование ресурсов
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Кэшируем ресурсы');
                return cache.addAll(urlsToCache).catch((error) => {
                    console.error('Ошибка при кэшировании:', error);
                });
            })
    );
});

// Обработка запросов
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Возвращаем кэшированный ресурс или загружаем из сети
                return response || fetch(event.request);
            })
    );
});

// Обновление кэша
self.addEventListener('activate', (event) => {
    const cacheWhitelist = [CACHE_NAME];
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheWhitelist.indexOf(cacheName) === -1) {
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});
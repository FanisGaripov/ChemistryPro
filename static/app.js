// Register Service Worker
if ('serviceWorker' in navigator) {
    navigator.serviceWorker
    .register('/sw.js')
    .then(function(registration) {
        console.log('Service Worker Registered');
        return registration;
    })
    .catch(function(err) {
        console.error('Unable to register service worker.', err);
    });
}


window.addEventListener('online', function(e) {
    console.log("You are online");
}, false);



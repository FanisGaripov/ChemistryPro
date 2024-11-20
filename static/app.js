if('serviceWorker' in navigator) {
    navigator.serviceWorker.register("static/sw.js")
        .then(() => console.log("Зарегистрировали"))
        .catch(() => console.log("Ошибка"));
}
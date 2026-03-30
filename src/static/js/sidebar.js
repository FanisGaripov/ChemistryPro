function toggleSidebar() {
    var sidebar = document.getElementById('sidebar');
    sidebar.classList.toggle('active');
}

// Закрытие сайдбара при клике вне его области
document.addEventListener('click', function(event) {
    var sidebar = document.getElementById('sidebar');
    var toggler = document.querySelector('.navbar-toggler');

    // Проверяем, был ли клик вне сайдбара и кнопки для его открытия
    if (!sidebar.contains(event.target) && !toggler.contains(event.target)) {
        sidebar.classList.remove('active'); // Закрываем сайдбар
    }
});
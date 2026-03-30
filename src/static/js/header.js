function toggleDropdown(element) {
    // Закрываем все другие дропдауны
    document.querySelectorAll('.dropdown').forEach(function(dropdown) {
        if (!dropdown.contains(element.parentElement)) {
            dropdown.classList.remove('active');
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.display = 'none';
            }
        }
    });

    // Переключаем текущий дропдаун
    const dropdown = element.parentElement;
    const menu = dropdown.querySelector('.dropdown-menu');
    const isActive = dropdown.classList.contains('active');

    if (isActive) {
        dropdown.classList.remove('active');
        menu.style.display = 'none';
    } else {
        dropdown.classList.add('active');
        menu.style.display = 'block';
    }
}

// Закрываем дропдауны при клике вне их области
document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown')) {
        document.querySelectorAll('.dropdown').forEach(function(dropdown) {
            dropdown.classList.remove('active');
            const menu = dropdown.querySelector('.dropdown-menu');
            if (menu) {
                menu.style.display = 'none';
            }
        });
    }
});
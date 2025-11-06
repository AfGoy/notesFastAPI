// Обработка выпадающего меню профиля
document.addEventListener('DOMContentLoaded', function() {
    const profileBtn = document.getElementById('profileBtn');
    const dropdownContent = document.getElementById('dropdownContent');
    const profileMenu = document.querySelector('.profile-menu');
    const logoutBtn = document.getElementById('logoutBtn'); // Кнопка выхода
    const profileBtnMenu = document.querySelector('.dropdown-item:first-child'); // Кнопка профиля

    // Функция для перехода в профиль
    function goToProfile() {
        alert('Переход на страницу профиля');
        // window.location.href = '/profile';
    }

    // Назначение обработчика для кнопки выхода
    if (logoutBtn) {
        logoutBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            logout();
        });
    }

    // Назначение обработчика для кнопки профиля
    if (profileBtnMenu) {
        profileBtnMenu.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            goToProfile();
            profileMenu.classList.remove('active'); // Закрываем меню после выбора
        });
    }

    // Открытие/закрытие меню по клику на кнопку профиля
    profileBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        profileMenu.classList.toggle('active');
    });

    // Закрытие меню при клике вне его области
    document.addEventListener('click', function(e) {
        if (!profileMenu.contains(e.target)) {
            profileMenu.classList.remove('active');
        }
    });

    // Предотвращение закрытия меню при клике внутри него
    dropdownContent.addEventListener('click', function(e) {
        e.stopPropagation();
    });

    // Функция для горизонтального скролла
    function setupHorizontalScroll(scrollContainerId, leftBtnId, rightBtnId) {
        const scrollContainer = document.getElementById(scrollContainerId);
        const leftBtn = document.getElementById(leftBtnId);
        const rightBtn = document.getElementById(rightBtnId);

        if (!scrollContainer || !leftBtn || !rightBtn) return;

        const scrollAmount = 300;

        leftBtn.addEventListener('click', () => {
            scrollContainer.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });

        rightBtn.addEventListener('click', () => {
            scrollContainer.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });

        // Обновление видимости кнопок скролла
        const updateScrollButtons = () => {
            const { scrollLeft, scrollWidth, clientWidth } = scrollContainer;

            leftBtn.style.opacity = scrollLeft > 10 ? '1' : '0.5';
            rightBtn.style.opacity = scrollLeft < scrollWidth - clientWidth - 10 ? '1' : '0.5';
        };

        scrollContainer.addEventListener('scroll', updateScrollButtons);
        window.addEventListener('resize', updateScrollButtons);

        // Первоначальная проверка
        setTimeout(updateScrollButtons, 100);
    }

    // Настройка скролла для папок и заметок
    setupHorizontalScroll('foldersScroll', 'foldersScrollLeft', 'foldersScrollRight');
    setupHorizontalScroll('notesScroll', 'notesScrollLeft', 'notesScrollRight');

    // Анимация появления карточек при загрузке страницы
    const folderCards = document.querySelectorAll('.folder-card');
    const noteCards = document.querySelectorAll('.note-card');

    folderCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateX(30px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, 100 + index * 100);
    });

    noteCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateX(30px)';
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateX(0)';
        }, 300 + index * 100);
    });

    // Проверка аутентификации при загрузке
    checkAuthStatus();
});

// ========================
// ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
// ========================

/**
 * Устанавливает куки (если нужно устанавливать на фронтенде)
 * @param {string} name - имя куки
 * @param {string} value - значение
 * @param {number} days - срок жизни в днях
 */
function setCookie(name, value, days = 7) {
    const expires = new Date(Date.now() + days * 864e5).toUTCString();
    document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

/**
 * Получает значение куки по имени
 * @param {string} name - имя куки
 * @returns {string|null} значение или null
 */
function getCookie(name) {
    return document.cookie.split('; ').reduce((r, v) => {
        const parts = v.split('=');
        return parts[0] === name ? decodeURIComponent(parts[1]) : r;
    }, null);
}

/**
 * Удаляет куки по имени
 * @param {string} name - имя куки
 */
function deleteCookie(name) {
    document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

// ========================
// ОСНОВНЫЕ ФУНКЦИИ
// ========================

// Функция для выхода из системы
function logout() {
    // Удаляем токены из куки
    deleteCookie('access_token');
    deleteCookie('refresh_token');

    // Также на всякий случай очищаем localStorage (если что-то там осталось)
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('userData');

    // Перенаправляем на страницу входа
    window.location.href = '/auth/create';
}

// Функция проверки статуса аутентификации
function checkAuthStatus() {
    const token = getCookie('access_token'); // ✅ Читаем из куки!
    const profileName = document.querySelector('.profile-name');
    const logoutBtn = document.getElementById('logoutBtn');

    if (!token && profileName) {
        profileName.textContent = 'Гость';

        if (logoutBtn) {
            logoutBtn.style.opacity = '0.5';
            logoutBtn.style.cursor = 'not-allowed';
            logoutBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                alert('Вы не авторизованы');
            };
        }
    } else if (token && profileName) {
        // Если токен есть — можно попытаться восстановить имя из localStorage (если сохранили)
        const userData = localStorage.getItem('userData');
        if (userData) {
            try {
                const parsed = JSON.parse(userData);
                if (parsed && parsed.username) {
                    profileName.textContent = parsed.username;
                }
            } catch (e) {
                console.warn('Не удалось распарсить userData');
            }
        }

        // Активируем кнопку выхода
        if (logoutBtn) {
            logoutBtn.style.opacity = '1';
            logoutBtn.style.cursor = 'pointer';
            logoutBtn.onclick = function(e) {
                e.preventDefault();
                e.stopPropagation();
                logout();
            };
        }
    }
}

// Функция для сохранения токена после авторизации
function setAuthToken(token, refreshToken, userData) {
    // Сохраняем токены в куки (основное хранилище)
    setCookie('access_token', token, 7);
    setCookie('refresh_token', refreshToken, 7);

    // Дополнительно: сохраняем userData в localStorage для отображения имени
    if (userData) {
        localStorage.setItem('userData', JSON.stringify(userData));
    }

    // Обновляем имя пользователя
    const profileName = document.querySelector('.profile-name');
    if (profileName && userData && userData.username) {
        profileName.textContent = userData.username;
    }

    // Активируем кнопку выхода
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.style.opacity = '1';
        logoutBtn.style.cursor = 'pointer';
        logoutBtn.onclick = function(e) {
            e.preventDefault();
            e.stopPropagation();
            logout();
        };
    }
}



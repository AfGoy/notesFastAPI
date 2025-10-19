class AuthManager {
    constructor() {
        this.currentTab = 'login';
        this.init();
    }

    init() {
        this.setupTabSwitching();
        this.setupFormSubmissions();
    }

    setupTabSwitching() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tab = e.target.dataset.tab;
                this.switchTab(tab);
            });
        });
    }

    switchTab(tab) {
        // Обновляем активные кнопки табов
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tab}"]`).classList.add('active');

        // Показываем активную форму
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.remove('active');
        });
        document.getElementById(`${tab}Form`).classList.add('active');

        this.currentTab = tab;
        this.hideMessage();
    }

    setupFormSubmissions() {
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
    }

    async handleLogin() {
        const formData = new FormData(document.getElementById('loginForm'));
        const data = {
            username: formData.get('username'),
            password: formData.get('password'),
            grant_type: 'password'
        };

        try {
            const response = await fetch('/auth/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(data)
            });

            if (response.ok) {
                const result = await response.json();
                this.saveToken(result.access_token);
                this.showMessage('Успешный вход!', 'success');
                setTimeout(() => {
                    window.location.href = '/';
                }, 1000);
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Ошибка входа', 'error');
            }
        } catch (error) {
            this.showMessage('Ошибка сети', 'error');
        }
    }

    async handleRegister() {
        const formData = new FormData(document.getElementById('registerForm'));
        const data = {
            login: formData.get('login'),
            password: formData.get('password'),
            confirm_password: formData.get('confirm_password')
        };

        // Валидация паролей
        if (data.password !== data.confirm_password) {
            this.showMessage('Пароли не совпадают', 'error');
            return;
        }

        try {
            const response = await fetch('/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams(data)
            });

            if (response.ok) {
                this.showMessage('Регистрация успешна! Теперь вы можете войти.', 'success');
                this.switchTab('login');
                document.getElementById('registerForm').reset();
            } else {
                const error = await response.json();
                this.showMessage(error.detail || 'Ошибка регистрации', 'error');
            }
        } catch (error) {
            this.showMessage('Ошибка сети', 'error');
        }
    }

    saveToken(token) {
        localStorage.setItem('access_token', token);
        // Также можно установить cookie для серверного использования
        document.cookie = `access_token=${token}; path=/; max-age=86400`; // 24 часа
    }

    showMessage(text, type) {
        const messageEl = document.getElementById('message');
        messageEl.textContent = text;
        messageEl.className = `message ${type}`;
        messageEl.classList.remove('hidden');

        // Автоматическое скрытие сообщения через 5 секунд
        setTimeout(() => {
            this.hideMessage();
        }, 5000);
    }

    hideMessage() {
        const messageEl = document.getElementById('message');
        messageEl.classList.add('hidden');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    new AuthManager();
});

// Вспомогательная функция для проверки авторизации
function checkAuth() {
    return localStorage.getItem('access_token') || document.cookie.includes('access_token');
}

// Функция для получения токена
function getToken() {
    return localStorage.getItem('access_token') || 
           document.cookie.split('; ').find(row => row.startsWith('access_token='))?.split('=')[1];
}
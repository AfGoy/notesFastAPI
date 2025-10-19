document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById("createFolderModal");
    const btn = document.getElementById("createFolderBtn");
    const span = document.querySelector(".close");
    const form = document.getElementById("createFolderForm");
    const passwordField = document.getElementById("passwordField");
    const passwordProtectedCheckbox = document.getElementById("passwordProtected");
    const passwordInput = document.getElementById("folderPassword");

    // Открыть модальное окно
    btn.onclick = function() {
        modal.style.display = "block";
    }

    // Закрыть модальное окно
    span.onclick = function() {
        modal.style.display = "none";
    }

    window.onclick = function(event) {
        if (event.target === modal) {
            modal.style.display = "none";
        }
    }

    // Показать/скрыть поле ввода пароля
    passwordProtectedCheckbox.onchange = function() {
        passwordField.style.display = this.checked ? "block" : "none";
    }

    // Отправка формы
    form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const name = form.name.value.trim();
    const color = form.color.value;
    const isPublic = form.public.checked;
    const isProtected = form.password_protected.checked;
    const password = form.password.value.trim();

    // Сброс возможной ошибки
    passwordInput.classList.remove("input-error");

    // 🔒 Валидация пароля
    if (isProtected && password === "") {
        passwordInput.classList.add("input-error");
        passwordInput.focus();
        return;
    }

    const folderData = {
        name: name,
        color: color,
        is_public: isPublic,
        password_check: isProtected,
        password: isProtected ? password : null
    };

    const token = localStorage.getItem('access_token');

    try {
        const response = await fetch('/folder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(folderData)
        });

        if (response.ok) {
            modal.style.display = "none";
            location.reload();
        } else {
            const error = await response.json();
            alert('Ошибка: ' + (error.detail || 'Неизвестная ошибка'));
        }
    } catch (err) {
        console.error('Ошибка:', err);
        alert('Произошла ошибка при создании папки.');
    }
    });

    });

document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("createFolderModal");
    const openBtn = document.getElementById("createFolderBtn");
    const closeBtn = document.querySelector(".modal .close");
    const passwordCheckbox = document.getElementById("passwordProtected");
    const passwordField = document.getElementById("passwordField");
    const form = document.getElementById("createFolderForm");

    // Открыть модалку
    openBtn.addEventListener("click", () => {
        modal.style.display = "block";
    });

    // Закрыть модалку
    closeBtn.addEventListener("click", () => {
        modal.style.display = "none";
    });

    // Скрывать/показывать поле пароля
    passwordCheckbox.addEventListener("change", () => {
        if (passwordCheckbox.checked) {
            passwordField.style.display = "block";
        } else {
            passwordField.style.display = "none";
        }
    });


    // Закрытие по клику вне модального окна
    window.addEventListener("click", function (event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    });
});
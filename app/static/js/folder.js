document.addEventListener('DOMContentLoaded', () => {
    const selectAllCheckbox = document.getElementById('selectAll');
    const noteCheckboxes = document.querySelectorAll('.note-select');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkMoveBtn = document.getElementById('bulkMoveBtn');
    const addNoteBtn = document.getElementById('addNoteBtn');
    const modal = document.getElementById('noteModal');
    const span = document.querySelector('.close');
    const form = document.getElementById('noteForm');

    // Получаем folder_id из URL (предполагается путь вида /folder/123)
    const urlParts = window.location.pathname.split('/');
    const folderId = parseInt(urlParts[urlParts.length - 1]);

    if (!folderId || isNaN(folderId)) {
        console.error('Не удалось определить folder_id из URL');
    }

    // === Функции ===
    const updateBulkActions = () => {
        const anyChecked = Array.from(noteCheckboxes).some(cb => cb.checked);
        bulkDeleteBtn.disabled = !anyChecked;
        bulkMoveBtn.disabled = !anyChecked; 
    };

    const addNoteToGrid = (note) => {
        const grid = document.getElementById('notesGrid');
        const noteCard = document.createElement('div');
        noteCard.className = 'note-card';
        noteCard.setAttribute('data-note-id', note.id);
        // Форматируем дату как в шаблоне (можно улучшить)
        const formattedDate = new Date(note.updated_at || new Date()).toLocaleString('ru-RU');
        noteCard.innerHTML = `
            <div class="note-checkbox">
                <input type="checkbox" class="note-select" value="${note.id}">
            </div>
            <div class="note-content">
                <h3>${note.name}</h3>
                <p class="note-date">Обновлено: ${formattedDate}</p>
            </div>
        `;
        grid.appendChild(noteCard);

        // Назначаем обработчик для нового чекбокса
        const newCheckbox = noteCard.querySelector('.note-select');
        newCheckbox.addEventListener('change', handleNoteCheckboxChange);
    };

    const handleNoteCheckboxChange = () => {
        const allChecked = Array.from(document.querySelectorAll('.note-select')).every(cb => cb.checked);
        selectAllCheckbox.checked = allChecked;
        updateBulkActions();
    };

    // === Обработчики ===
    selectAllCheckbox.addEventListener('change', function () {
        document.querySelectorAll('.note-select').forEach(cb => cb.checked = this.checked);
        updateBulkActions();
    });

    noteCheckboxes.forEach(cb => {
        cb.addEventListener('change', handleNoteCheckboxChange);
    });

    bulkDeleteBtn.addEventListener('click', async () => {
        const selectedIds = Array.from(document.querySelectorAll('.note-select'))
            .filter(cb => cb.checked)
            .map(cb => parseInt(cb.value));

        if (selectedIds.length === 0) return;

        if (confirm(`Удалить ${selectedIds.length} заметок?`)) {
            // TODO: отправить DELETE-запрос на сервер
            selectedIds.forEach(id => {
                const card = document.querySelector(`.note-card[data-note-id="${id}"]`);
                if (card) card.remove();
            });
            updateBulkActions();
        }
    });

    bulkMoveBtn.addEventListener('click', () => {
        const selectedIds = Array.from(document.querySelectorAll('.note-select'))
            .filter(cb => cb.checked)
            .map(cb => parseInt(cb.value));

        if (selectedIds.length === 0) return;

        const targetFolderId = prompt('Введите ID папки для перемещения:');
        if (targetFolderId && !isNaN(targetFolderId)) {
            alert(`Переместить ${selectedIds.length} заметок в папку ${targetFolderId}`);
            // TODO: отправить запрос на перемещение
        }
    });

    addNoteBtn.onclick = () => modal.style.display = 'block';
    span.onclick = () => modal.style.display = 'none';
    window.onclick = (e) => {
        if (e.target === modal) modal.style.display = 'none';
    };

    form.onsubmit = async (e) => {
        e.preventDefault();

        const name = document.getElementById('noteName').value.trim();
        const text = document.getElementById('noteText').value.trim();

        if (!name || !text) {
            alert('Название и текст не могут быть пустыми');
            return;
        }

        const data = {
            name: name,
            text: text,
            folder_id: folderId,
            is_public: document.getElementById('notePublic').checked
        };

        try {
            // 🔥 ИСПРАВЛЕНО: отправляем на правильный эндпоинт!
            const res = await fetch('/note/', {  // или '/api/notes', зависит от вашего бэкенда
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                const note = await res.json();
                addNoteToGrid(note);
                modal.style.display = 'none';
                form.reset();
                // Сброс кастомного чекбокса (если нужно)
                document.getElementById('notePublic').checked = false;
            } else {
                const errorText = await res.text();
                console.error('Ошибка сервера:', errorText);
                alert('Ошибка при создании заметки: ' + (res.status === 400 ? 'Неверные данные' : 'Серверная ошибка'));
            }
        } catch (err) {
            console.error('Сетевая ошибка:', err);
            alert('Ошибка сети. Проверьте подключение.');
        }
    };
});
document.addEventListener('DOMContentLoaded', () => {
    const selectAllCheckbox = document.getElementById('selectAll');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkMoveBtn = document.getElementById('bulkMoveBtn');
    const addNoteBtn = document.getElementById('addNoteBtn');
    const noteModal = document.getElementById('noteModal');
    const moveModal = document.getElementById('moveModal');
    const closeNoteBtn = document.querySelector('.close');
    const closeMoveBtn = document.querySelector('.close-move');
    const confirmMoveBtn = document.getElementById('confirmMoveBtn');
    const noteForm = document.getElementById('noteForm');
    const folderListContainer = document.getElementById('folderListContainer');

    console.log("confirmMoveBtn:", confirmMoveBtn);

    const urlParts = window.location.pathname.split('/');
    const folderId = parseInt(urlParts[urlParts.length - 1]);
    const userId = parseInt(document.body.dataset.userId); // ⚠️ добавь data-user-id="..." в <body> в HTML

    let cachedFolders = [];
    let foldersLoaded = false;

    const updateBulkActions = () => {
        const anyChecked = Array.from(document.querySelectorAll('.note-select')).some(cb => cb.checked);
        bulkDeleteBtn.disabled = !anyChecked;
        bulkMoveBtn.disabled = !anyChecked;
    };

    const handleNoteCheckboxChange = () => {
        const allChecked = Array.from(document.querySelectorAll('.note-select')).every(cb => cb.checked);
        selectAllCheckbox.checked = allChecked;
        updateBulkActions();
    };

    selectAllCheckbox.addEventListener('change', function () {
        document.querySelectorAll('.note-select').forEach(cb => cb.checked = this.checked);
        updateBulkActions();
    });

    document.querySelectorAll('.note-select').forEach(cb => cb.addEventListener('change', handleNoteCheckboxChange));

    // === 🔹 Загрузка папок пользователя для модалки ===
    async function loadFoldersForUser() {
        if (foldersLoaded) return cachedFolders;
        if (!userId || isNaN(userId)) {
            console.warn('Не указан userId — не могу загрузить папки для модалки.');
            cachedFolders = [];
            foldersLoaded = true;
            return cachedFolders;
        }

        try {
            const resp = await fetch(`/folder/by_user/${userId}/`, {
                method: 'GET',
                headers: { 'Accept': 'application/json' }
            });

            if (!resp.ok) {
                console.error('Ошибка HTTP при получении папок:', resp.status);
                cachedFolders = [];
            } else {
                const data = await resp.json();
                cachedFolders = Array.isArray(data) ? data : [];
            }
        } catch (err) {
            console.error('Ошибка сети при загрузке папок:', err);
            cachedFolders = [];
        }

        foldersLoaded = true;
        return cachedFolders;
    }

    // === 🔹 Отрисовка списка папок в модалке ===
    function renderFolderList(folders) {
        if (!folderListContainer) return;
        folderListContainer.innerHTML = '';

        if (folders.length === 0) {
            folderListContainer.innerHTML = '<p>Нет доступных папок для перемещения.</p>';
            return;
        }

        folders.forEach(f => {
            if (f.id === folderId) return; // не показываем текущую папку
            const label = document.createElement('label');
            label.innerHTML = `
                <input type="radio" name="targetFolder" value="${f.id}">
                ${f.name}
            `;
            folderListContainer.appendChild(label);
        });
    }

    // 🔹 Показ модалки перемещения
    bulkMoveBtn.addEventListener('click', async () => {
        const selected = Array.from(document.querySelectorAll('.note-select:checked'));
        if (selected.length === 0) return;

        const folders = await loadFoldersForUser();
        renderFolderList(folders);
        moveModal.classList.add('show');
    });

    // 🔹 Закрытие модалок
    window.onclick = (e) => {
        if (e.target === noteModal) noteModal.classList.remove('show');
        if (e.target === moveModal) moveModal.classList.remove('show');
    };

    // 🔹 Подтверждение перемещения
    confirmMoveBtn.addEventListener('click', async () => {
        const selectedFolder = document.querySelector('input[name="targetFolder"]:checked');
        if (!selectedFolder) return alert('Выберите папку.');

        const targetFolderId = parseInt(selectedFolder.value);
        const selectedIds = Array.from(document.querySelectorAll('.note-select:checked')).map(cb => parseInt(cb.value));

        try {
            console.log(selectedIds)
            console.log(targetFolderId)
            const response = await fetch('/note/mass_move/', {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note_ids: selectedIds, folder_id: targetFolderId })
            });

            if (response.ok) {
                selectedIds.forEach(id => {
                    const card = document.querySelector(`.note-card[data-note-id="${id}"]`);
                    if (card) card.remove();
                });
                moveModal.classList.remove('show');
                updateBulkActions();
            } else {
                alert('Ошибка при перемещении заметок');
            }
        } catch (err) {
            alert('Ошибка сети при перемещении');
        }
    });

    // 🔹 Показ модалки создания
    addNoteBtn.onclick = () => noteModal.classList.add('show');

    // 🔹 Создание заметки
    noteForm.onsubmit = async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('noteName').value.trim(),
            text: document.getElementById('noteText').value.trim(),
            folder_id: folderId,
            is_public: document.getElementById('notePublic').checked
        };

        try {
            const res = await fetch('/note/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });

            if (res.ok) {
                const note = await res.json();
                addNoteToGrid(note);
                noteModal.classList.remove('show');
                noteForm.reset();
            } else {
                alert('Ошибка при создании заметки.');
            }
        } catch {
            alert('Ошибка сети.');
        }
    };

    const addNoteToGrid = (note) => {
        const grid = document.getElementById('notesGrid');
        const noteCard = document.createElement('div');
        noteCard.className = 'note-card';
        noteCard.setAttribute('data-note-id', note.id);
        noteCard.innerHTML = `
            <div class="note-checkbox">
                <input type="checkbox" class="note-select" value="${note.id}">
            </div>
            <div class="note-content">
                <h3>${note.name}</h3>
                <p class="note-date">Обновлено: ${new Date().toLocaleString('ru-RU')}</p>
            </div>
        `;
        grid.appendChild(noteCard);
        noteCard.querySelector('.note-select').addEventListener('change', handleNoteCheckboxChange);
    };
});

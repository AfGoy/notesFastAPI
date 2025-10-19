document.addEventListener('DOMContentLoaded', function () {

    const selectAllCheckbox = document.getElementById('selectAll');
    const noteCheckboxes = document.querySelectorAll('.note-select');
    const bulkDeleteBtn = document.getElementById('bulkDeleteBtn');
    const bulkMoveBtn = document.getElementById('bulkMoveBtn');
    const addNoteBtn = document.getElementById('addNoteBtn');

    // Функция обновления состояния кнопок
    function updateBulkActions() {
        const anyChecked = Array.from(noteCheckboxes).some(cb => cb.checked);
        bulkDeleteBtn.disabled = !anyChecked;
        bulkMoveBtn.disabled = !anyChecked;
    }

    // Выбор всех
    selectAllCheckbox.addEventListener('change', function () {
        noteCheckboxes.forEach(cb => cb.checked = this.checked);
        updateBulkActions();
    });

    // При изменении любого чекбокса заметки
    noteCheckboxes.forEach(cb => {
        cb.addEventListener('change', function () {
            // Если хоть один не выбран — снимаем "выбрать все"
            if (!this.checked) {
                selectAllCheckbox.checked = false;
            } else {
                // Проверяем, выбраны ли ВСЕ
                const allChecked = Array.from(noteCheckboxes).every(cb => cb.checked);
                selectAllCheckbox.checked = allChecked;
            }
            updateBulkActions();
        });
    });

    // Кнопка "Добавить заметку"
    addNoteBtn.addEventListener('click', function () {
        alert('Функция добавления заметки — в разработке');
        // Здесь можно: window.location.href = '/notes/create?folder_id=...'
    });

    // Кнопка "Удалить выбранные"
    bulkDeleteBtn.addEventListener('click', function () {
        const selectedIds = Array.from(noteCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedIds.length === 0) return;

        if (confirm(`Вы уверены, что хотите удалить ${selectedIds.length} заметок?`)) {
            // Здесь отправка на сервер
            console.log('Удалить заметки:', selectedIds);
            // Пример: fetch('/api/notes/bulk-delete', { method: 'POST', body: JSON.stringify({ ids: selectedIds }) })
            // После успешного удаления — обновить UI
            selectedIds.forEach(id => {
                const card = document.querySelector(`.note-card[data-note-id="${id}"]`);
                if (card) card.remove();
            });
            updateBulkActions();
        }
    });

    // Кнопка "Переместить"
    bulkMoveBtn.addEventListener('click', function () {
        const selectedIds = Array.from(noteCheckboxes)
            .filter(cb => cb.checked)
            .map(cb => cb.value);

        if (selectedIds.length === 0) return;

        const folderId = prompt('Введите ID папки, куда переместить:');
        if (!folderId) return;

        // Здесь отправка на сервер
        console.log('Переместить заметки:', selectedIds, 'в папку:', folderId);
        // Пример: fetch('/api/notes/bulk-move', { method: 'POST', body: JSON.stringify({ ids: selectedIds, folder_id: folderId }) })

        alert(`Заметки будут перемещены в папку ${folderId}`);
    });

});
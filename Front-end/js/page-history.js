// js/page-history.js

// 模拟历史数据
let historyData = [
    {time: '2025-09-03 16:00', original: '你好', translation: 'Hello', type: 'text'},
    {time: '2025-09-03 16:05', original: '世界', translation: 'World', type: 'text'},
    {time: '2025-09-03 16:10', original: '图片示例', translation: 'Picture Example', type: 'picture'},
    {time: '2025-09-03 16:15', original: '文件示例', translation: 'File Example', type: 'file'}
];

const historyBody = document.getElementById('history-body');
const searchInput = document.getElementById('search-input');
const sortSelects = document.querySelectorAll('.sort-select');
const notification = document.getElementById('notification');
const notificationText = document.getElementById('notification-text');
const selectAllCheckbox = document.getElementById('select-all');
const deleteBtn = document.querySelector('.delete-btn');

// 渲染表格
function renderHistory(data) {
    historyBody.innerHTML = '';
    if (data.length === 0) {
        document.getElementById('no-results').style.display = 'block';
        return;
    } else {
        document.getElementById('no-results').style.display = 'none';
    }

    data.forEach((item, index) => {
        const tr = document.createElement('tr');

        tr.innerHTML = `
            <td>${item.time}</td>
            <td>${item.original}</td>
            <td>${item.translation}</td>
            <td>
                <button class="copy-btn" data-index="${index}"><i class="fas fa-copy"></i></button>
                <input type="checkbox" class="checkbox" data-index="${index}">
            </td>
        `;

        historyBody.appendChild(tr);
    });

    // 绑定复制事件
    document.querySelectorAll('.copy-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = btn.dataset.index;
            navigator.clipboard.writeText(data[idx].translation).then(() => {
                showNotification('已复制到剪贴板');
            });
        });
    });
}

// 显示通知
function showNotification(msg) {
    notificationText.textContent = msg;
    notification.style.display = 'block';
    setTimeout(() => {
        notification.style.display = 'none';
    }, 2000);
}

// 搜索功能
searchInput.addEventListener('input', () => {
    filterAndSort();
});

// 筛选和排序功能
sortSelects.forEach(select => {
    select.addEventListener('change', () => {
        filterAndSort();
    });
});

function filterAndSort() {
    let filtered = [...historyData];
    const searchValue = searchInput.value.toLowerCase();
    const typeFilter = sortSelects[0].value;
    const sortOption = sortSelects[1].value;

    // 搜索
    if (searchValue) {
        filtered = filtered.filter(item => item.original.toLowerCase().includes(searchValue));
    }

    // 类型筛选
    if (typeFilter !== 'all') {
        filtered = filtered.filter(item => item.type === typeFilter);
    }

    // 排序
    filtered.sort((a, b) => {
        if (sortOption === 'newest') return new Date(b.time) - new Date(a.time);
        if (sortOption === 'oldest') return new Date(a.time) - new Date(b.time);
        if (sortOption === 'a-z') return a.original.localeCompare(b.original);
        if (sortOption === 'z-a') return b.original.localeCompare(a.original);
    });

    renderHistory(filtered);
}

// 全选/取消全选
selectAllCheckbox.addEventListener('change', () => {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
});

// 删除选中
deleteBtn.addEventListener('click', () => {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    const toDeleteIndexes = [];
    checkboxes.forEach(cb => {
        if (cb.checked) toDeleteIndexes.push(Number(cb.dataset.index));
    });
    historyData = historyData.filter((_, idx) => !toDeleteIndexes.includes(idx));
    renderHistory(historyData);
});

// 导出 CSV
document.getElementById('export-btn').addEventListener('click', () => {
    let csvContent = '时间,原文,译文,类型\n';
    historyData.forEach(item => {
        csvContent += `"${item.time}","${item.original}","${item.translation}","${item.type}"\n`;
    });

    const blob = new Blob([csvContent], {type: 'text/csv;charset=utf-8;'});
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'translation_history.csv';
    link.click();
});

// 刷新按钮
document.getElementById('refresh-btn').addEventListener('click', () => {
    renderHistory(historyData);
});

// 返回按钮
document.getElementById('back-btn').addEventListener('click', () => {
    window.history.back();
});

// 初始渲染
renderHistory(historyData);

window.addEventListener('unload',()=>{
    localStorage.removeItem("currentUserId");
});

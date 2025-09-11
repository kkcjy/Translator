let historyData = [
    // { time: '2025-09-03 16:00', original: '你好', translation: 'Hello', type: 'text' },
    // { time: '2025-09-03 16:05', original: '世界', translation: 'World', type: 'text' },
    // { time: '2025-09-03 16:10', original: '图片示例', translation: 'Picture Example', type: 'picture' },
    // { time: '2025-09-03 16:15', original: '文件示例', translation: 'File Example', type: 'file' }
];

const historyBody = document.getElementById('history-body');
const searchInput = document.getElementById('search-input');
const sortSelects = document.querySelectorAll('.sort-select');
const notification = document.getElementById('notification');
const notificationText = document.getElementById('notification-text');
const selectAllCheckbox = document.getElementById('select-all');
const deleteBtn = document.querySelector('.delete-btn');
// FastAPI base URL
const API_URL = "https://www.r4286138.nyat.app:10434";
const ITEMS_PER_PAGE = 10;
let currentPage = 1;
let totalPages = 1;
let currentData = [];

const prevPageBtn = document.getElementById('prev-page');
const nextPageBtn = document.getElementById('next-page');
const currentPageSpan = document.getElementById('current-page');
const pageInfoSpan = document.getElementById('page-info');

// 更新分页状态
function updatePagination() {
    totalPages = Math.ceil(currentData.length / ITEMS_PER_PAGE);

    // 更新按钮状态
    prevPageBtn.disabled = currentPage <= 1;
    nextPageBtn.disabled = currentPage >= totalPages;

    // 更新页码信息
    currentPageSpan.textContent = currentPage;
    pageInfoSpan.textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;

    // 渲染当前页的数据
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const endIndex = Math.min(startIndex + ITEMS_PER_PAGE, currentData.length);
    const pageData = currentData.slice(startIndex, endIndex);

    renderHistory(pageData);
}

// 上一页
prevPageBtn.addEventListener('click', () => {
    if (currentPage > 1) {
        currentPage--;
        updatePagination();
    }
});

// 下一页
nextPageBtn.addEventListener('click', () => {
    if (currentPage < totalPages) {
        currentPage++;
        updatePagination();
    }
});


// 通用请求函数
async function makeRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("请求失败:", error);
        throw error;
    }
}

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
        // 为图片和文件类型记录显示图标
        let originalContent, translationContent;

        if (item.type === 'picture') {
            originalContent = `<div class="icon-display" data-title="${item.original}"><i class="fas fa-image"></i> 图片</div>`;
        } else if (item.type === 'file') {
            originalContent = `<div class="icon-display" data-title="${item.original}"><i class="fas fa-file"></i> 文件</div>`;
        } else {
            originalContent = item.original;
        }

        translationContent = item.translation;

        tr.innerHTML = `
                    <td><input type="checkbox" class="checkbox" data-index="${index}" data-id="${item.id}" onchange="updateDeleteButtonState()"></td>
                    <td>${item.time}</td>
                    <td class="content-cell">${originalContent}</td>
                    <td class="content-cell">${translationContent}</td>
                    <td>
                        <div class="copy-buttons">
                            <button title="原文" class="copy-btn copys" data-index="${index}">
                                <i class="fas fa-copy"></i> 原文
                            </button>
                            <button title="译文" class="copy-btn copyt" data-index="${index}">
                                <i class="fas fa-copy"></i> 译文
                            </button>
                        </div>
                    </td>
                `;

        historyBody.appendChild(tr);
    });

    updateDeleteButtonState();

    // 绑定复制事件
    document.querySelectorAll('button.copyt').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = btn.dataset.index;
            navigator.clipboard.writeText(data[idx].translation).then(() => {
                showNotification('已复制到剪贴板');
            });
        });
    });

    document.querySelectorAll('button.copys').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = btn.dataset.index;
            navigator.clipboard.writeText(data[idx].original).then(() => {
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

function updateDeleteButtonState() {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    const anyChecked = Array.from(checkboxes).some(cb => cb.checked);
    deleteBtn.disabled = !anyChecked;
    deleteBtn.style.cursor = anyChecked ? 'pointer' : 'not-allowed';
    deleteBtn.style.backgroundColor = anyChecked ? '#ff4757' : '#ff9f9fff';
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

const originalFilterAndSort = window.filterAndSort;
window.filterAndSort = function () {
    let filtered = [...historyData];
    const searchValue = searchInput.value.toLowerCase();
    const typeFilter = document.getElementById('type-filter').value;
    const sortOption = document.getElementById('sort-select').value;

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

    // 更新当前数据和页码
    currentData = filtered;
    currentPage = 1;
    updatePagination();
};
// 全选/取消全选
selectAllCheckbox.addEventListener('change', () => {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    checkboxes.forEach(cb => cb.checked = selectAllCheckbox.checked);
    if (selectAllCheckbox.checked && checkboxes.length > 0) {
        deleteBtn.disabled = false;
        deleteBtn.style.cursor = 'pointer';
        deleteBtn.style.backgroundColor = '#ff4757';
    } else {
        deleteBtn.disabled = true;
        deleteBtn.style.cursor = 'not-allowed';
        deleteBtn.style.backgroundColor = '#ff9f9fff';
    }
});

// 删除选中
deleteBtn.addEventListener('click', async () => {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    const toDeleteIndexes = [];
    let toDeleteIds = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            toDeleteIndexes.push(Number(cb.dataset.index));
            toDeleteIds.push(cb.dataset.id);
        }
    });
    historyData = historyData.filter((_, idx) => !toDeleteIndexes.includes(idx));
    renderHistory(historyData);
    await makeRequest(`${API_URL}/history/delete`, {
        method: "POST",
        body: JSON.stringify({
            ids: toDeleteIds,
        })
    }).catch(error => {
        showNotification('无法连接到服务器!:' + error.message);
        console.error('删除记录失败:', error.message);
    });
    deleteBtn.disabled = true;
    deleteBtn.style.cursor = 'not-allowed';
    deleteBtn.style.backgroundColor = '#ff9f9fff';
});

// 导出 CSV
document.getElementById('export-btn').addEventListener('click', () => {
    let csvContent = '时间,原文,译文,类型\n';
    historyData.forEach(item => {
        csvContent += `"${item.time}","${item.original}","${item.translation}","${item.type}"\n`;
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
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

// 修改 getHistoryData 函数，添加分页支持
const originalGetHistoryData = window.getHistoryData;
window.getHistoryData = async function () {
    if (sessionStorage.getItem("currentUserId") == null) {
        showNotification('请先登录!');
        setTimeout(() => {
            window.location.href = "page-login.html";
        }, 2000);
        return;
    }
    try {
        const data = await makeRequest(`${API_URL}/history/${sessionStorage.getItem("currentUserId")}`, {
            method: "GET",
        });
        if (data.length <= 0) {
            historyData = [];
            currentData = [];
            updatePagination();
            return;
        }
        let jsonStr = '[';
        data.forEach(string => {
            jsonStr += string + ',';
        })
        jsonStr = jsonStr.slice(0, -1) + ']';
        jsonStr = jsonStr.replace(/[\r|\n|\t]/g, "")
        historyData = JSON.parse(jsonStr);
        currentData = [...historyData];
        updatePagination();
    } catch (error) {
        showNotification('无法连接到服务器!:' + error.message);
        console.error('获取历史记录失败:', error.message);
    }
};

// 修改删除功能，更新分页
const originalDeleteFunction = deleteBtn.onclick;
deleteBtn.onclick = async function () {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    const toDeleteIndexes = [];
    let toDeleteIds = [];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            toDeleteIndexes.push(Number(cb.dataset.index));
            toDeleteIds.push(cb.dataset.id);
        }
    });

    // 从原始数据中删除
    historyData = historyData.filter((item, idx) => !toDeleteIndexes.includes(idx));

    // 更新当前数据并重新分页
    currentData = [...historyData];
    currentPage = 1;
    updatePagination();

    // 发送删除请求到服务器
    await makeRequest(`${API_URL}/history/delete`, {
        method: "POST",
        body: JSON.stringify({
            ids: toDeleteIds,
        })
    }).catch(error => {
        showNotification('无法连接到服务器!:' + error.message);
        console.error('删除记录失败:', error.message);
    });
};
document.addEventListener('DOMContentLoaded', getHistoryData);
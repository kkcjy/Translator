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
                    <td>${item.time}</td>
                    <td>${originalContent}</td>
                    <td>${translationContent}</td>
                    <td>
                        <button title="复制原文" class="copy-btn copys" data-index="${index}"><i class="fas fa-copy"></i></button>
                        <button title="复制译文" class="copy-btn copyt" data-index="${index}"><i class="fas fa-copy"></i></button>
                        <input type="checkbox" class="checkbox" data-index="${index}" data-id="${item.id}" onchange="updateDeleteButtonState()">
                    </td>
                `;

        historyBody.appendChild(tr);
    });
    updateDeleteButtonState();
    // 绑定复制事件
    document.querySelectorAll('td>button.copyt').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = btn.dataset.index;
            navigator.clipboard.writeText(data[idx].translation).then(() => {
                showNotification('已复制到剪贴板');
            });
        });
    });
    document.querySelectorAll('td>button.copys').forEach(btn => {
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

function updateDeleteButtonState(){
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
    if(selectAllCheckbox.checked && checkboxes.length>0){
        deleteBtn.disabled=false;
        deleteBtn.style.cursor='pointer';
        deleteBtn.style.backgroundColor='#ff4757';
    }else{
        deleteBtn.disabled=true;
        deleteBtn.style.cursor='not-allowed';
        deleteBtn.style.backgroundColor='#ff9f9fff';
    }
});

// 删除选中
deleteBtn.addEventListener('click', async() => {
    const checkboxes = document.querySelectorAll('.history-table .checkbox');
    const toDeleteIndexes = [];
    let toDeleteIds=[];
    checkboxes.forEach(cb => {
        if (cb.checked) {
            toDeleteIndexes.push(Number(cb.dataset.index));
            toDeleteIds.push(cb.dataset.id);
        }
    });
    historyData = historyData.filter((_, idx) => !toDeleteIndexes.includes(idx));
    renderHistory(historyData);
    await makeRequest(`${API_URL}/history/delete`,{
        method:"POST",
        body:JSON.stringify({
            ids:toDeleteIds,
        })
    }).catch(error=>{
        showNotification('无法连接到服务器!:'+error.message);
        console.error('删除记录失败:',error.message);
    });
    deleteBtn.disabled=true;
    deleteBtn.style.cursor='not-allowed';
    deleteBtn.style.backgroundColor='#ff9f9fff';
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

async function getHistoryData(){
    if(sessionStorage.getItem("currentUserId")==null){
        showNotification('请先登录!');
        setTimeout(()=>{
            window.location.href="page-login.html";
        },2000);
        return;
    }
    try{
        const data=await makeRequest(`${API_URL}/history/${sessionStorage.getItem("currentUserId")}`,{
            method:"GET",
        });
        if(data.length<=0){
            historyData=[];
            renderHistory(historyData);
            return;
        }
        let jsonStr='[';
        data.forEach(string=>{
            jsonStr+=string+',';
        })
        jsonStr=jsonStr.slice(0,-1)+']';
        historyData=JSON.parse(jsonStr);
        // 初始渲染
        renderHistory(historyData);
    }catch(error){
        showNotification('无法连接到服务器!:'+error.message);
    }
}
document.addEventListener('DOMContentLoaded', getHistoryData);
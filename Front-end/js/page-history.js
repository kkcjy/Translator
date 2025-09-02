document.addEventListener('DOMContentLoaded', function() {
    const historyUrl = 'page-translate.html'; 
    const backUrl = 'page-translate.html'; 

    const historyBody = document.getElementById('history-body');
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notification-text');

    // 返回按钮
    document.getElementById('back-btn').addEventListener('click', () => {
        window.location.href = backUrl;
    });

    // 刷新按钮
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadHistory();
    });

    // 加载历史记录
    async function loadHistory() {
        try {
            const response = await fetch(historyUrl);
            const data = await response.json(); // 假设返回 [{time, original, translation, type}, ...]
            
            historyBody.innerHTML = ''; // 清空表格
            
            data.forEach(item => {
                const tr = document.createElement('tr');

                // 时间列
                const timeTd = document.createElement('td');
                timeTd.className = 'time-col';
                timeTd.textContent = item.time;
                
                // 原文列
                const originalTd = document.createElement('td');
                originalTd.className = 'original-col';
                if (item.type === 'image') {
                    originalTd.innerHTML = `<span class="file-indicator"><i class="fas fa-image"></i> 图片</span>`;
                } else if (item.type === 'file') {
                    originalTd.innerHTML = `<span class="file-indicator"><i class="fas fa-file"></i> 文件</span>`;
                } else {
                    originalTd.textContent = item.original;
                }
                
                // 译文列
                const translationTd = document.createElement('td');
                translationTd.className = 'translation-col';
                translationTd.textContent = item.translation;

                // 操作列
                const actionsTd = document.createElement('td');
                actionsTd.className = 'actions-col';
                actionsTd.innerHTML = `
                    <div class="action-buttons">
                        <button class="action-btn copy-btn" title="复制译文"><i class="fas fa-copy"></i></button>
                        <button class="action-btn sound-btn" title="播放声音"><i class="fas fa-volume-up"></i></button>
                    </div>
                `;

                tr.append(timeTd, originalTd, translationTd, actionsTd);
                historyBody.appendChild(tr);

                // 创建每行复选框
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.className = 'checkbox';
                checkbox.style.marginRight = '10px';
                timeTd.prepend(checkbox);

                // 行点击选择
                tr.addEventListener('click', (e) => {
                    if (e.target.type !== 'checkbox' &&
                        !e.target.classList.contains('action-btn') &&
                        !e.target.parentElement.classList.contains('action-btn')) {
                        checkbox.checked = !checkbox.checked;
                    }
                });
            });

            attachRowActions(); // 给新行绑定复制和朗读事件
        } catch (err) {
            console.error('加载历史失败:', err);
        }
    }

    // 绑定复制和朗读
    function attachRowActions() {
        const copyButtons = document.querySelectorAll('.copy-btn');
        copyButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const text = this.closest('tr').querySelector('.translation-col').textContent;
                navigator.clipboard.writeText(text).then(() => {
                    notificationText.textContent = '已复制到剪贴板';
                    notification.classList.add('show');
                    setTimeout(() => notification.classList.remove('show'), 2000);
                });
            });
        });

        const soundButtons = document.querySelectorAll('.sound-btn');
        soundButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.stopPropagation();
                const text = this.closest('tr').querySelector('.translation-col').textContent;
                if ('speechSynthesis' in window) {
                    const speech = new SpeechSynthesisUtterance(text);
                    speech.lang = 'zh-CN';
                    window.speechSynthesis.speak(speech);
                    notificationText.textContent = '正在播放音频';
                    notification.classList.add('show');
                    setTimeout(() => notification.classList.remove('show'), 2000);
                } else {
                    alert('浏览器不支持文本转语音');
                }
            });
        });
    }

    // 全选功能
    const selectAll = document.getElementById('select-all');
    selectAll.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('tbody .checkbox');
        checkboxes.forEach(cb => cb.checked = selectAll.checked);
    });

    // 删除按钮
    document.querySelector('.delete-btn').addEventListener('click', () => {
        const selected = document.querySelectorAll('tbody .checkbox:checked');
        if (selected.length > 0) {
            if (confirm(`确定要删除选中的 ${selected.length} 条记录吗？`)) {
                alert('删除操作已执行（演示）');
            }
        } else {
            alert('请先选择记录');
        }
    });

    // 初次加载
    loadHistory();
});
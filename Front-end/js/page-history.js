document.addEventListener('DOMContentLoaded', function() {
    // 选项卡功能
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
        });
    });
    
    // 全选功能
    const selectAll = document.getElementById('select-all');
    selectAll.addEventListener('change', function() {
        const checkboxes = document.querySelectorAll('tbody .checkbox');
        checkboxes.forEach(checkbox => {
            checkbox.checked = selectAll.checked;
        });
    });
    
    // 行选择功能
    const rows = document.querySelectorAll('tbody tr');
    rows.forEach(row => {
        // 创建每行的复选框
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'checkbox';
        checkbox.style.marginRight = '10px';
        
        // 插入到行的第一个单元格
        const firstCell = row.firstElementChild;
        firstCell.prepend(checkbox);
        
        // 行点击事件
        row.addEventListener('click', (e) => {
            if (e.target.type !== 'checkbox' && 
                !e.target.classList.contains('action-btn') &&
                !e.target.parentElement.classList.contains('action-btn')) {
                checkbox.checked = !checkbox.checked;
            }
        });
    });
    
    // 删除按钮功能
    const deleteBtn = document.querySelector('.delete-btn');
    deleteBtn.addEventListener('click', () => {
        const selectedItems = document.querySelectorAll('tbody .checkbox:checked');
        if (selectedItems.length > 0) {
            if (confirm(`确定要删除选中的 ${selectedItems.length} 条记录吗？`)) {
                alert('删除操作已执行（演示功能）');
            }
        } else {
            alert('请先选择要删除的记录');
        }
    });
    
    // 复制功能
    const copyButtons = document.querySelectorAll('.copy-btn');
    const notification = document.getElementById('notification');
    const notificationText = document.getElementById('notification-text');
    
    copyButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const textToCopy = this.closest('tr').querySelector('.translation-col').textContent;
            
            // 使用Clipboard API复制文本
            navigator.clipboard.writeText(textToCopy).then(() => {
                // 显示通知
                notificationText.textContent = '已复制到剪贴板';
                notification.classList.add('show');
                
                // 2秒后隐藏通知
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 2000);
            }).catch(err => {
                console.error('无法复制文本: ', err);
                notificationText.textContent = '复制失败';
                notification.classList.add('show');
                
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 2000);
            });
        });
    });
    
    // 播放声音功能
    const soundButtons = document.querySelectorAll('.sound-btn');
    
    soundButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            const textToSpeak = this.closest('tr').querySelector('.translation-col').textContent;
            
            // 使用Web Speech API播放声音
            if ('speechSynthesis' in window) {
                const speech = new SpeechSynthesisUtterance();
                speech.text = textToSpeak;
                speech.lang = 'zh-CN'; // 设置为中文
                speech.volume = 1;
                speech.rate = 1;
                speech.pitch = 1;
                
                window.speechSynthesis.speak(speech);
                
                // 显示通知
                notificationText.textContent = '正在播放音频';
                notification.classList.add('show');
                
                // 2秒后隐藏通知
                setTimeout(() => {
                    notification.classList.remove('show');
                }, 2000);
            } else {
                alert('您的浏览器不支持文本转语音功能');
            }
        });
    });
});
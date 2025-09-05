// 设置弹窗显示/隐藏
const settingModal = document.getElementById('setting-modal');
const openSettingBtn = document.getElementById('open-setting-btn');
const openSettingBtnMobile = document.getElementById('open-setting-btn-mobile');
const closeSettingBtn = document.getElementById('close-setting-btn');
const confirmBtn = document.getElementById('setting-confirm-btn');
const cancelBtn = document.getElementById('setting-cancel-btn');
const avatarUpload = document.getElementById('avatar-upload');
const avatarPreview = document.getElementById('avatar-preview');
const fontSizeRange = document.getElementById('font-size-range');
const fontSizeValue = document.getElementById('font-size-value');
const bgModeBtns = document.querySelectorAll('.bg-mode-btn');
const bgModeRadios = document.querySelectorAll('.bg-mode-radio');
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
// 从sessionStorage加载设置
const savedSettings = sessionStorage.getItem('appSettings');
window.currentSettings = savedSettings ? JSON.parse(savedSettings) : {
  avatar: 'img/default_ava.jpg',
  fontSize: '16px',
  bgMode: 'light'
};
function saveSettings() {
  sessionStorage.setItem('appSettings', JSON.stringify(currentSettings));
}
// radio按钮逻辑
function updateBgModeRadioUI(selectedMode) {
  bgModeRadios.forEach(radio => {
    const dot = radio.nextElementSibling.querySelector('.radio-dot');
    if (radio.dataset.mode === selectedMode) {
      radio.checked = true;
      if (dot) dot.style.opacity = '1';
    } else {
      radio.checked = false;
      if (dot) dot.style.opacity = '0';
    }
  });
}
// 打开弹窗时同步临时设置
function openSettingModal() {
  // 头像
  avatarPreview.src = currentSettings.avatar?currentSettings.avatar:'img/default_ava.jpg';
  // 字体滑动条
  let sizeNum = parseInt(currentSettings.fontSize);
  fontSizeRange.value = sizeNum;
  fontSizeValue.textContent = sizeNum + 'px';
  // 背景按钮
  updateBgModeRadioUI(currentSettings.bgMode);
  // 临时设置同步
  tempSettings = { ...currentSettings };
  settingModal.classList.remove('opacity-0', 'pointer-events-none');
  settingModal.classList.add('opacity-100');
}

openSettingBtn && openSettingBtn.addEventListener('click', openSettingModal);
openSettingBtnMobile && openSettingBtnMobile.addEventListener('click', (e) => {
  e.preventDefault();
  openSettingModal();
});
// 关闭弹窗（取消/关闭按钮）
function closeSettingModal() {
  settingModal.classList.add('opacity-0', 'pointer-events-none');
  settingModal.classList.remove('opacity-100');
}
closeSettingBtn && closeSettingBtn.addEventListener('click', closeSettingModal);
cancelBtn && cancelBtn.addEventListener('click', closeSettingModal);
confirmBtn && confirmBtn.addEventListener('click', closeSettingModal);
// 头像上传（只更新临时设置，不立即应用）
avatarUpload && avatarUpload.addEventListener('change', function () {
  const file = this.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = function (e) {
      avatarPreview.src = e.target.result;
      tempSettings.avatar = e.target.result;
    };
    reader.readAsDataURL(file);
  }
});

// 字体大小滑动条（仅弹窗内预览，不立即应用到主界面）
fontSizeRange && fontSizeRange.addEventListener('input', function () {
  let val = this.value;
  fontSizeValue.textContent = val + 'px';
  tempSettings.fontSize = val + 'px';
  // 只预览所有输入和结果区域内的 textarea 字体大小
  document.querySelectorAll('.input-container textarea, #results-content textarea').forEach(area => {
    area.style.fontSize = val + 'px';
  });
});

// 背景色切换（只更新临时设置，不立即应用）
bgModeRadios.forEach(radio => {
  radio.addEventListener('change', function () {
    updateBgModeRadioUI(this.dataset.mode);
    tempSettings.bgMode = this.dataset.mode;
  });
});

// 应用设置（点击“确定”后才应用）
function applySettings(settings) {
  saveSettings(settings);
  window.applyResultsTheme();
  // 只设置所有输入和结果区域内的 textarea 字体大小
  document.querySelectorAll('.input-container textarea, #results-content textarea').forEach(area => {
    area.style.fontSize = settings.fontSize;
  });

  // 不再设置 document.body.style.fontSize，避免影响页面其他字体

  // 翻译结果区域深色/浅色切换
  const resultsContent = document.getElementById('results-content');
  const resultsTextareas = resultsContent ? resultsContent.querySelectorAll('textarea') : [];
  if (settings.bgMode === 'light') {
    if (resultsContent) {
      resultsContent.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      resultsContent.classList.add('bg-white', 'text-dark', 'border-gray-200');
      resultsContent.style.backgroundColor = '';
      resultsContent.style.color = '';
      resultsContent.style.borderColor = '';
    }
    resultsTextareas.forEach(function (textarea) {
      textarea.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      textarea.classList.add('bg-white', 'text-dark', 'border-gray-200');
      textarea.style.backgroundColor = '';
      textarea.style.color = '';
      textarea.style.borderColor = '';
    });
  } else {
    if (resultsContent) {
      resultsContent.classList.remove('bg-white', 'text-dark', 'border-gray-200');
      resultsContent.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      resultsContent.style.backgroundColor = '#1e293b';
      resultsContent.style.color = '#e5e7eb';
      resultsContent.style.borderColor = '#334155';
    }
    resultsTextareas.forEach(function (textarea) {
      textarea.classList.remove('bg-white', 'text-dark', 'border-gray-200');
      textarea.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      textarea.style.backgroundColor = '#1e293b';
      textarea.style.color = '#e5e7eb';
      textarea.style.borderColor = '#334155';
    });
  }

  // 背景色相关逻辑保持不变
  // 头像（可选：同步到主界面其他头像区域）
  // avatarPreview.src = settings.avatar; // 弹窗内已同步
  // 字体大小
  // 背景色
  const welcomeDesc = document.getElementById('welcome-desc');
  const modelCards = document.querySelectorAll('.model-card');
  const modelSectionBox = document.querySelector('.max-w-4xl.mx-auto.mb-8 > div');
  const selectedModelDisplay = document.getElementById('selected-model-display');
  const inputContainers = document.querySelectorAll('.input-container > div');
  const resultsContainers = document.querySelectorAll('.results-container > div');
  const historyCards = document.querySelectorAll('#translation-results-container > div');
  // 文本框
  const textareasAll = document.querySelectorAll('textarea');
  // 功能特点卡片
  // 修改选择器，确保所有卡片都能切换
  const featureCards = document.querySelectorAll('.max-w-5xl .rounded-xl.shadow-sm');
  document.getElementById('Avatar').src = sessionStorage.getItem("currentUserAvatar");
  document.getElementById('MobileAvatar').src = sessionStorage.getItem("currentUserAvatar");
  if (settings.bgMode === 'light') {
    document.body.classList.remove('dark');
    document.body.classList.add('bg-gradient-to-br', 'from-light', 'to-blue-50', 'text-dark');
    document.body.classList.remove('bg-gray-900', 'text-white');
    if (welcomeDesc) welcomeDesc.style.color = '';
    // 模型选择区域外层
    if (modelSectionBox) {
      modelSectionBox.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      modelSectionBox.classList.add('bg-white', 'border-gray-200', 'text-dark');
    }
    // 选中模型显示区域
    if (selectedModelDisplay) {
      selectedModelDisplay.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      selectedModelDisplay.classList.add('bg-primary/10', 'border-primary/30', 'text-dark');
    }
    // 卡片浅色
    modelCards.forEach(card => {
      card.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      card.classList.add('bg-white', 'border-gray-200', 'text-dark');
    });
    inputContainers.forEach(card => {
      card.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      card.classList.add('bg-white', 'border-gray-200', 'text-dark');
    });
    resultsContainers.forEach(card => {
      card.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      card.classList.add('bg-white', 'border-gray-200', 'text-dark');
    });
    historyCards.forEach(card => {
      card.classList.remove('bg-gray-900', 'border-gray-700', 'text-white');
      card.classList.add('bg-white', 'border-gray-200', 'text-dark');
    });
    // 文本框浅色
    textareasAll.forEach(area => {
      area.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      area.classList.add('bg-white', 'text-dark', 'border-gray-200');
      area.style.backgroundColor = '';
      area.style.color = '';
      area.style.borderColor = '';
    });
    // 功能特点卡片浅色
    featureCards.forEach(card => {
      card.classList.remove('bg-gray-900', 'text-white');
      card.classList.add('bg-white', 'text-dark');
    });

    // 设置弹窗浅色
    settingModal.classList.remove('bg-gray-900', 'bg-black/30');
    settingModal.classList.add('bg-transparent');
    const modalBox = settingModal.querySelector("#setting-modal-box");
    if (modalBox) {
      modalBox.classList.remove('bg-gray-900', 'text-white');
      modalBox.classList.add('bg-white', 'text-dark');
    }
  } else {
    document.body.classList.add('dark');
    document.body.classList.remove('bg-gradient-to-br', 'from-light', 'to-blue-50', 'text-dark');
    document.body.classList.add('bg-gray-900', 'text-white');
    if (welcomeDesc) welcomeDesc.style.color = '#e5e7eb';
    // 模型选择区域外层
    if (modelSectionBox) {
      modelSectionBox.classList.remove('bg-white', 'border-gray-200', 'text-dark');
      modelSectionBox.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    }
    // 选中模型显示区域
    if (selectedModelDisplay) {
      selectedModelDisplay.classList.remove('bg-primary/10', 'border-primary/30', 'text-dark');
      selectedModelDisplay.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    }
    // 卡片深色
    modelCards.forEach(card => {
      card.classList.remove('bg-white', 'border-gray-200', 'text-dark');
      card.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    });
    inputContainers.forEach(card => {
      card.classList.remove('bg-white', 'border-gray-200', 'text-dark');
      card.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    });
    resultsContainers.forEach(card => {
      card.classList.remove('bg-white', 'border-gray-200', 'text-dark');
      card.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    });
    historyCards.forEach(card => {
      card.classList.remove('bg-white', 'border-gray-200', 'text-dark');
      card.classList.add('bg-gray-900', 'border-gray-700', 'text-white');
    });
    // 文本框深色
    textareasAll.forEach(area => {
      area.classList.remove('bg-white', 'text-dark', 'border-gray-200');
      area.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      area.style.backgroundColor = '#1e293b';
      area.style.color = '#e5e7eb';
      area.style.borderColor = '#334155';
    });
    // 功能特点卡片深色
    featureCards.forEach(card => {
      card.classList.remove('bg-white', 'text-dark');
      card.classList.add('bg-gray-900', 'text-white');
    });

    // 设置弹窗深色
    settingModal.classList.remove('bg-black/30', 'bg-gray-900');
    settingModal.classList.add('bg-transparent');
    const modalBox = settingModal.querySelector("#setting-modal-box");
    if (modalBox) {
      modalBox.classList.remove('bg-white', 'text-dark');
      modalBox.classList.add('bg-gray-900', 'text-white');
    }
  }
}

function showWarning(message) {
  const notification = document.getElementById('notification'); // 确保 HTML 有这个元素

  // 设置通知内容和图标（警告三角形）
  notification.innerHTML = `
    <i class="fa fa-exclamation-triangle mr-2"></i>
    <span>${message}</span>
  `;

  // 样式
  notification.className = 'fixed bottom-4 right-4 text-white px-4 py-3 rounded-lg shadow-lg transform translate-y-20 opacity-0 transition-all duration-300 flex items-center bg-red-600';

  // 弹出动画
  setTimeout(() => {
    notification.classList.remove('translate-y-20', 'opacity-0');
  }, 10);

  // 自动隐藏
  setTimeout(() => {
    notification.classList.add('translate-y-20', 'opacity-0');
  }, 3000);
}

// 结果区域样式应用函数
function applyResultsTheme() {
  const resultsContent = document.getElementById('results-content');
  const mode = currentSettings.bgMode;
  // 处理所有 textarea
  const allTextareas = document.querySelectorAll('#results-content textarea');
  allTextareas.forEach(function (textarea) {
    if (mode === 'light') {
      textarea.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      textarea.classList.add('bg-white', 'text-dark', 'border-gray-200');
      textarea.style.backgroundColor = '';
      textarea.style.color = '';
      textarea.style.borderColor = '';
    } else {
      textarea.classList.remove('bg-white', 'text-dark', 'border-gray-200');
      textarea.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      textarea.style.backgroundColor = '#1e293b';
      textarea.style.color = '#e7e9eb';
      textarea.style.borderColor = '#334155';
    }
  });

  // 处理所有 .p-3.bg-gray-50.rounded-lg.min-h-[100px] 结果块
  const resultBlocks = document.querySelectorAll('#results-content .p-3');
  resultBlocks.forEach(function (block) {
    if (mode === 'light') {
      block.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      block.classList.add('bg-gray-50', 'text-dark');
      block.style.backgroundColor = '';
      block.style.color = '';
      block.style.borderColor = '';
    } else {
      block.classList.remove('bg-gray-50', 'text-dark');
      block.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      block.style.backgroundColor = '#1e293b';
      block.style.color = '#e7e9eb';
      block.style.borderColor = '#334155';
    }
  });

  // 如果没有textarea和结果块，才处理resultsContent本身
  if (allTextareas.length === 0 && resultBlocks.length === 0 && resultsContent) {
    if (mode === 'light') {
      resultsContent.classList.remove('bg-gray-900', 'text-white', 'border-gray-700');
      resultsContent.classList.add('bg-white', 'text-dark', 'border-gray-200');
      resultsContent.style.backgroundColor = '';
      resultsContent.style.color = '';
      resultsContent.style.borderColor = '';
    } else {
      resultsContent.classList.remove('bg-white', 'text-dark', 'border-gray-200');
      resultsContent.classList.add('bg-gray-900', 'text-white', 'border-gray-700');
      resultsContent.style.backgroundColor = '#1e293b';
      resultsContent.style.color = '#e7e9eb';
      resultsContent.style.borderColor = '#334155';
    }
  }
}

// 确定按钮：应用临时设置到主界面
confirmBtn && confirmBtn.addEventListener('click', async()=>{
  currentSettings = { ...tempSettings };
  if(sessionStorage.getItem("currentUserId"))
  {
    try{
      const data=await makeRequest(`${API_URL}/settings`,{
        method:"PUT",
        body:JSON.stringify({
          userId:parseInt(sessionStorage.getItem("currentUserId"),10),
          avatar:currentSettings.avatar,
          fontSize:parseInt(currentSettings.fontSize.match(/\d+/)[0],10),
          bgMode:currentSettings.bgMode
        })
      });
    }catch(error)
    {
      console.error("保存设置到服务器失败:", error);
    }
    sessionStorage.setItem("currentUserAvatar",currentSettings.avatar);
    applySettings(currentSettings);
    applyResultsTheme();
    // 新增：应用结果和特色卡片主题
    if (typeof window.applyResultsTheme === 'function') {
      window.applyResultsTheme();
    }
    closeSettingModal();
  }
  else {
    showNotification(`登陆账号后方可设置！`);
  }
});

// 页面初始化时应用当前设置
window.addEventListener('DOMContentLoaded', function () {
  applySettings(currentSettings);
})
// 挂载到 window，供外部 JS 调用
window.applyResultsTheme = applyResultsTheme;

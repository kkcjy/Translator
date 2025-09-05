// 页面交互逻辑
const modelCards = document.querySelectorAll('.model-card');
const modelSelection = document.getElementById('model-selection');
const selectedModelDisplay = document.getElementById('selected-model-display');
const selectedModelName = document.getElementById('selected-model-name');
const changeModelBtn = document.getElementById('change-model-btn');
const translationInputContainer = document.getElementById('translation-input-container');
const translationResultsContainer = document.getElementById('translation-results-container');
const translateBtn = document.getElementById('translate-btn');
const sourceText = document.getElementById('source-text');
const charCount = document.getElementById('char-count');
const resultsContent = document.getElementById('results-content');
const translationHistory = document.getElementById('translation-history');
const copyResultsBtn = document.getElementById('copy-results');
const swapLanguagesBtn = document.getElementById('swap-languages');
const subscribeText = document.getElementById('subscribe-input');
const subscribeBtn = document.getElementById('subscribe-btn');
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
const navbar = document.getElementById('navbar');
const notification = document.getElementById('notification');
const notificationText = document.getElementById('notification-text');
const loginOrAvatar = document.getElementById('login-or-avatar');
const openBtn = document.getElementById('open-terms');
const closeBtn = document.getElementById('close-terms');
const modal = document.getElementById('terms-modal');

let selectedModel = null;
let isChineseToEnglish = true;
let sourceLang = "zh";
let targetLang = "en";

function init() {
  window.addEventListener('scroll', handleScroll);
  if(sessionStorage.getItem("currentUserId")!==null)
  {
    loginOrAvatar.style.display="null";
    loginOrAvatar.innerHTML=`<img id="Avatar" src='${sessionStorage.getItem("currentUserAvatar")}' alt='img/default_ava.jpg' class='w-8 h-8 rounded-full'>`;
    mobileMenuButton.style.display="null";
    mobileMenuButton.innerHTML=`<img id="MobileAvatar" src='${sessionStorage.getItem("currentUserAvatar")}' alt='img/default_ava.jpg' class='w-8 h-8 rounded-full'>`;
  }
  modelCards.forEach(card => {
    card.addEventListener('click', () => selectModel(card));
  });
  changeModelBtn.addEventListener('click', showModelSelection);
  sourceText.addEventListener('input', updateTextInput);
  translateBtn.addEventListener('click', performTranslation);
  copyResultsBtn.addEventListener('click', copyResults);
  swapLanguagesBtn.addEventListener('click', swapLanguages);
  subscribeBtn.addEventListener('click', subscribeUpdates);
  mobileMenuButton.addEventListener('click', toggleMobileMenu);
  updateTranslateButtonState();
}

function handleScroll() {
  if (window.scrollY > 10) {
    navbar.classList.add('py-2', 'shadow');
    navbar.classList.remove('py-3');
  } else {
    navbar.classList.add('py-3');
    navbar.classList.remove('py-2', 'shadow');
  }
}

function selectModel(card) {
  const modelName = card.querySelector('h4').textContent;
  selectedModel = modelName;
  selectedModelName.textContent = modelName;
  modelSelection.classList.add('hidden');
  selectedModelDisplay.classList.remove('hidden');
  translationInputContainer.style.marginTop = '0';
  setTimeout(() => {
    translationResultsContainer.style.opacity = '1';
    translationResultsContainer.style.height = 'auto';
  }, 300);
  updateTranslateButtonState();
  showNotification(`已选择 ${modelName}`);
}

function showModelSelection() {
  modelSelection.classList.remove('hidden');
  selectedModelDisplay.classList.add('hidden');
  translationResultsContainer.style.opacity = '0';
  translationResultsContainer.style.height = '0';
  translationInputContainer.style.marginTop = '80px';
  selectedModel = null;
  updateTranslateButtonState();
}

function updateTextInput() {
  charCount.textContent = sourceText.value.length;
  updateTranslateButtonState();
}

function updateTranslateButtonState() {
  if (selectedModel && sourceText.value.trim().length > 0) {
    translateBtn.innerHTML='<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
  } else {
    translateBtn.innerHTML='<i class="fa fa-language mr-2"></i> 请先选择模型并输入文本';
    disableTranslateButton();
  }
}

function enableTranslateButton() {
  translateBtn.disabled = false;
  translateBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  translateBtn.classList.add('hover:shadow-md');
}

function disableTranslateButton() {
  translateBtn.disabled = true;
  translateBtn.classList.add('opacity-50', 'cursor-not-allowed');
  translateBtn.classList.remove('hover:shadow-md');
}

async function performTranslation() {
  if (!selectedModel || !sourceText.value.trim()) return;
  translateBtn.disabled = true;
  translateBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 翻译中...';
  try {
    const response = await fetch('http://0.0.0.0:8000/translate/', {//Try to use common request function like other files.Back end URL=https://www.r4286138.nyat.app:10434
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getToken()}`
      },
      body: JSON.stringify({
        source_text: sourceText.value.trim(),
        source_lang: isChineseToEnglish ? "zh" : "en",
        target_lang: isChineseToEnglish ? "en" : "zh",
        model_name: selectedModel
      })
    });

    if (!response.ok) {
      if (response.status === 401) {
        showNotification('认证失败，请重新登录', 'error');
        // 清除无效token
        localStorage.removeItem('authToken');
        window.location.href = 'page-login.html';
        return;
      }
      throw new Error('翻译请求失败');
    }

    const data = await response.json();

    // 显示翻译结果
    resultsContent.innerHTML = `
      <div class="p-3 bg-gray-50 rounded-lg min-h-[100px]">
        ${data.translated_text}
      </div>
    `;

    showNotification('翻译完成');

    // 应用主题设置
    if (typeof window.applyResultsTheme === 'function') {
      window.applyResultsTheme();
    }
  } catch (error) {
    console.error('翻译错误:', error);
    showNotification('翻译失败，请重试', 'error');
  } finally {
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
  }
}

function copyResults() {
  const resultText = resultsContent.textContent.trim();
  if (!resultText || resultText === '翻译结果将显示在这里') {
    showNotification('没有可复制的内容', 'warning');
    return;
  }
  navigator.clipboard.writeText(resultText).then(() => {
    showNotification('结果已复制到剪贴板');
  }).catch(err => {
    showNotification('复制失败，请手动复制', 'error');
    console.error('复制失败:', err);
  });
}

function swapLanguages() {
  [sourceLang, targetLang] = [targetLang, sourceLang];
  isChineseToEnglish = !isChineseToEnglish;
  const langLeftText = document.getElementById('lang-left').querySelector('span');
  const langRightText = document.getElementById('lang-right').querySelector('span');
  const tempText = langLeftText.textContent;
  langLeftText.textContent = langRightText.textContent;
  langRightText.textContent = tempText;
  const direction = sourceLang === "zh" ? '中文→英文' : '英文→中文';
  showNotification(`已切换为${isChineseToEnglish ? '中文→英文' : '英文→中文'}`);
}

// 邮箱验证函数
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function subscribeUpdates() {
  const email = subscribeText.value.trim();
  if (!validateEmail(email)) {
    showNotification(`请输入有效的邮箱地址`, 'error')
  } 
  else {
    showNotification(`订阅成功！`);
  }
}

function toggleMobileMenu() {
  if (mobileMenu.classList.contains('opacity-0')) {
    mobileMenu.classList.remove('opacity-0', '-translate-y-full', 'pointer-events-none');
    mobileMenu.classList.add('opacity-100', 'translate-y-0', 'pointer-events-auto');
    mobileMenuButton.innerHTML = '<i class="fa fa-times"></i>';
  } else {
    mobileMenu.classList.add('opacity-0', '-translate-y-full', 'pointer-events-none');
    mobileMenu.classList.remove('opacity-100', 'translate-y-0', 'pointer-events-auto');
    mobileMenuButton.innerHTML = '<i class="fa fa-bars"></i>';
  }
}

function showNotification(message, type = 'success') {
  notificationText.textContent = message;
  notification.className = 'fixed bottom-4 right-4 text-white px-4 py-3 rounded-lg shadow-lg transform translate-y-20 opacity-0 transition-all duration-300 flex items-center';
  if (type === 'success') {
    notification.classList.add('bg-dark');
    notification.innerHTML = `<i class="fa fa-check-circle text-secondary mr-2"></i><span>${message}</span>`;
  } else if (type === 'warning') {
    notification.classList.add('bg-amber-600');
    notification.innerHTML = `<i class="fa fa-exclamation-triangle mr-2"></i><span>${message}</span>`;
  } else if (type === 'error') {
    notification.classList.add('bg-red-600');
    notification.innerHTML = `<i class="fa fa-times-circle mr-2"></i><span>${message}</span>`;
  }
  setTimeout(() => {
    notification.classList.remove('translate-y-20', 'opacity-0');
  }, 10);
  setTimeout(() => {
    notification.classList.add('translate-y-20', 'opacity-0');
  }, 3000);
}

// 翻译结果和特色卡片主题应用
window.applyResultsTheme = function () {
  // 翻译结果文本块
  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';
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
      block.style.color = '#e5e7eb';
      block.style.borderColor = '#334155';
    }
  });

  // 翻译结果文本框
  const resultTextareas = document.querySelectorAll('#results-content textarea');
  resultTextareas.forEach(function (textarea) {
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
      textarea.style.color = '#e5e7eb';
      textarea.style.borderColor = '#334155';
    }
  });

  // 特色卡片
  const featureCards = document.querySelectorAll('.max-w-5xl .rounded-xl.shadow-sm');
  featureCards.forEach(card => {
    if (mode === 'light') {
      card.classList.remove('bg-gray-900', 'text-white');
      card.classList.add('bg-white', 'text-dark');
    } else {
      card.classList.remove('bg-white', 'text-dark');
      card.classList.add('bg-gray-900', 'text-white');
    }
  });
};

// 打开弹窗
openBtn.addEventListener('click', e => {
  e.preventDefault();
  modal.style.display = 'flex';
});

// 关闭弹窗
closeBtn.addEventListener('click', () => {
  modal.style.display = 'none';
});

// 点击遮罩关闭
modal.addEventListener('click', e => {
  if(e.target === modal) {
    modal.style.display = 'none';
  }
});
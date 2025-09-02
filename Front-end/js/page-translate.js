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
const mobileMenuButton = document.getElementById('mobile-menu-button');
const mobileMenu = document.getElementById('mobile-menu');
const navbar = document.getElementById('navbar');
const notification = document.getElementById('notification');
const notificationText = document.getElementById('notification-text');

let selectedModel = null;
let isChineseToEnglish = true;

function init() {
  window.addEventListener('scroll', handleScroll);
  modelCards.forEach(card => {
    card.addEventListener('click', () => selectModel(card));
  });
  changeModelBtn.addEventListener('click', showModelSelection);
  sourceText.addEventListener('input', updateTextInput);
  translateBtn.addEventListener('click', performTranslation);
  copyResultsBtn.addEventListener('click', copyResults);
  swapLanguagesBtn.addEventListener('click', swapLanguages);
  mobileMenuButton.addEventListener('click', toggleMobileMenu);
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
  disableTranslateButton();
}

function updateTextInput() {
  charCount.textContent = sourceText.value.length;
  updateTranslateButtonState();
}

function updateTranslateButtonState() {
  if (selectedModel && sourceText.value.trim().length > 0) {
    enableTranslateButton();
  } else {
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

function performTranslation() {
  if (!selectedModel || !sourceText.value.trim()) return;
  translateBtn.disabled = true;
  translateBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 翻译中...';
  setTimeout(() => {
    const source = sourceText.value.trim();
    let result = '';
    if (isChineseToEnglish) {
      result = `[${selectedModel} 翻译] This is a simulated translation result for: "${source.substring(0, 20)}${source.length > 20 ? '...' : ''}"`;
    } else {
      result = `[${selectedModel} 翻译] 这是模拟翻译结果："${source.substring(0, 20)}${source.length > 20 ? '...' : ''}"`;
    }
    resultsContent.innerHTML = `
      <div class="p-3 bg-gray-50 rounded-lg min-h-[100px]">
        ${result}
      </div>
    `;
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
    showNotification('翻译完成');
    if (typeof window.applyResultsTheme === 'function') {
      window.applyResultsTheme();
    }
  }, 1500);
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
  isChineseToEnglish = !isChineseToEnglish;
  const langLeftText = document.getElementById('lang-left').querySelector('span');
  const langRightText = document.getElementById('lang-right').querySelector('span');
  const tempText = langLeftText.textContent;
  langLeftText.textContent = langRightText.textContent;
  langRightText.textContent = tempText;
  showNotification(`已切换为${isChineseToEnglish ? '中文→英文' : '英文→中文'}`);
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
window.applyResultsTheme = function() {
  // 翻译结果文本块
  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';
  const resultBlocks = document.querySelectorAll('#results-content .p-3');
  resultBlocks.forEach(function(block) {
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
  resultTextareas.forEach(function(textarea) {
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

document.addEventListener('DOMContentLoaded', init);
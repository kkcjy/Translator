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
const charCountContainer = document.getElementById('char-count-container');
const fileInput = document.getElementById('file-upload');
const fileList = document.getElementById('file-list');
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
const historyLink = document.getElementById('page-history');
const dropdown = document.getElementById('user-dropdown');
const logoutBtn = document.getElementById('logout-btn');
const sentenceToolbar = document.getElementById('sentence-toolbar');
const translateSentenceBtn = document.getElementById('translate-sentence-btn');
const speakSentenceBtn = document.getElementById('speak-sentence-btn');
let avatarLink;
let selectedModel = null;
let isChineseToEnglish = true;
let sourceLang = "zh";
let targetLang = "en";
let selectedFiles = [];
let sentenceSelectBtn = document.getElementById('sentence-select-btn');
let isSentenceSelectMode = false;
let sourceSentenceContainer;
let currentSelectedSentence = null;
async function init() {
  sessionStorage.removeItem("currentHisId");
  sessionStorage.removeItem("selectedModel");
  window.addEventListener('scroll', handleScroll);
  if (sessionStorage.getItem("currentUserId") !== null) {
    loginOrAvatar.style.display = "null";
    loginOrAvatar.href = "javascript:void(0);";
    loginOrAvatar.innerHTML = `<img id="Avatar" src='${sessionStorage.getItem("currentUserAvatar")}' alt='img/default_ava.jpg' class='avatar'>`;
    document.getElementById("Avatar").addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
    });
    // 更新用户名显示
    const userName = await makeRequest(`${API_URL}/user/${parseInt(sessionStorage.getItem("currentUserId"), 10)}`, { method: 'GET' })
    // 用户名修改功能
    const usernameInput = document.getElementById('username-input');
    // 从sessionStorage加载当前用户名
    usernameInput.value = userName;
    document.querySelectorAll('.user-name').forEach(element => {
      element.textContent = userName;
    });
    document.getElementsByClassName("user-info-avatar")[0].src = sessionStorage.getItem("currentUserAvatar");
    mobileMenuButton.style.display = "null";
    mobileMenuButton.innerHTML = `<img id="MobileAvatar" src='${sessionStorage.getItem("currentUserAvatar")}' alt='img/default_ava.jpg' class='w-8 h-8 rounded-full'>`;
  }
  document.addEventListener('click', function () {
    dropdown.classList.remove('show');
  });
  dropdown.addEventListener('click', function (e) {
    e.stopPropagation();
  });
  logoutBtn.addEventListener('click', function (e) {
    e.preventDefault();
    if (confirm('确定要退出登录吗？')) {
      showNotification('退出登录成功！');
      sessionStorage.removeItem("currentUserId");
      sessionStorage.removeItem("currentUserAvatar");
      window.location.href = "page-translate.html";
      dropdown.classList.remove('show');
    }
  });
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
  // 新增事件监听
  document.addEventListener('click', handleDocumentClick);
  translateSentenceBtn.addEventListener('click', translateSelectedSentence);
  speakSentenceBtn.addEventListener('click', speakSelectedSentence);
  sentenceSelectBtn.addEventListener('click', toggleSentenceSelectMode);
  updateTranslateButtonState();
  updateFeedbackState();
}
function updateSentenceContainerTheme() {
  if (!sourceSentenceContainer) return;

  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';

  if (mode === 'light') {
    sourceSentenceContainer.style.backgroundColor = '#fff';
    sourceSentenceContainer.style.color = '';
    sourceSentenceContainer.style.borderColor = '';
  } else {
    sourceSentenceContainer.style.backgroundColor = '#1e293b';
    sourceSentenceContainer.style.color = '#e5e7eb';
    sourceSentenceContainer.style.borderColor = '#334155';
  }
}
function applySentenceContainerTheme(container) {
  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';

  if (mode === 'light') {
    container.style.backgroundColor = '#fff';
    container.style.color = '';
    container.style.borderColor = '';
  } else {
    container.style.backgroundColor = '#1e293b';
    container.style.color = '#e5e7eb';
    container.style.borderColor = '#334155';
  }
}
function handleDocumentClick(e) {
  // 点击非句子区域时隐藏工具栏
  if (!e.target.closest('.hover') && !e.target.closest('#sentence-toolbar')) {
    hideSentenceToolbar();
  }
  if (!e.target.closest(".feedback-modal") && !e.target.closest("#appreciate-btn") && !e.target.closest("#disatisfy-btn")) {
    document.getElementById("feedback-modal").classList.remove("visible");
  }
}
// 添加切换单句选中模式的函数
function toggleSentenceSelectMode() {
  isSentenceSelectMode = !isSentenceSelectMode;

  if (isSentenceSelectMode) {
    // 进入单句选中模式
    enterSentenceSelectMode();
    sentenceSelectBtn.innerHTML = '<i class="fa fa-times mr-2"></i> 退出选中';
    sentenceSelectBtn.classList.remove('bg-gray-200', 'text-dark');
    sentenceSelectBtn.classList.add('bg-primary', 'text-white');
    updateTranslateButtonState();
  } else {
    // 退出单句选中模式
    exitSentenceSelectMode();
    sentenceSelectBtn.innerHTML = '<i class="fa fa-mouse-pointer mr-2"></i> 单句选中';
    sentenceSelectBtn.classList.remove('bg-primary', 'text-white');
    sentenceSelectBtn.classList.add('bg-gray-200', 'text-dark');
    updateTranslateButtonState();
  }
}

function enterSentenceSelectMode() {
  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';

  // 隐藏原文本框
  sourceText.style.display = 'none';
  charCountContainer.style.display = 'none';

  // 获取原始textarea的样式
  const textareaStyle = window.getComputedStyle(sourceText);

  sourceSentenceContainer = document.createElement('div');
  sourceSentenceContainer.id = 'source-sentence-container';
  // 获取当前字体大小设置
  const savedSettings = sessionStorage.getItem('appSettings');
  const currentSettings = savedSettings ? JSON.parse(savedSettings) : { fontSize: '16px' };

  // 设置句子容器的字体大小
  sourceSentenceContainer.style.fontSize = currentSettings.fontSize;
  // 复制原始textarea的样式
  sourceSentenceContainer.style.width = textareaStyle.width;
  sourceSentenceContainer.style.minHeight = textareaStyle.height;
  sourceSentenceContainer.style.padding = textareaStyle.padding;
  sourceSentenceContainer.style.fontSize = textareaStyle.fontSize;
  sourceSentenceContainer.style.lineHeight = textareaStyle.lineHeight;
  sourceSentenceContainer.style.fontFamily = textareaStyle.fontFamily;
  sourceSentenceContainer.style.border = textareaStyle.border;
  sourceSentenceContainer.style.borderRadius = textareaStyle.borderRadius;
  sourceSentenceContainer.style.boxSizing = textareaStyle.boxSizing;
  if (mode === 'light') {
    sourceSentenceContainer.style.backgroundColor = '#fff';
    sourceSentenceContainer.style.color = textareaStyle.color;
  } else {
    sourceSentenceContainer.style.backgroundColor = '#1e293b';
    sourceSentenceContainer.style.color = '#e5e7eb';
    sourceSentenceContainer.style.borderColor = '#334155';
  }
  applySentenceContainerTheme(sourceSentenceContainer);
  const sourceTextContent = sourceText.value.trim();
  const splited = splitText(sourceTextContent);
  let fontedResult = "";

  for (let i = 0; i < splited.length; i++) {
    fontedResult += `<span class="hover">${splited[i]}</span>`;
  }

  sourceSentenceContainer.innerHTML = fontedResult;

  // 插入到原文本框位置
  sourceText.parentNode.insertBefore(sourceSentenceContainer, sourceText.nextSibling);

  // 添加句子点击事件
  setTimeout(() => {
    document.querySelectorAll('#source-sentence-container .hover').forEach(sentence => {
      sentence.addEventListener('click', handleSentenceClick);
    });
  }, 0);
}

function exitSentenceSelectMode() {
  // 移除句子容器
  if (sourceSentenceContainer && sourceSentenceContainer.parentNode) {
    sourceSentenceContainer.parentNode.removeChild(sourceSentenceContainer);
  }

  // 显示原文本框
  sourceText.style.display = 'block';
  charCountContainer.style.display = 'block';

  // 隐藏句子工具栏
  hideSentenceToolbar();
}

function hideSentenceToolbar() {
  sentenceToolbar.classList.remove('visible');
  if (currentSelectedSentence) {
    currentSelectedSentence.classList.remove('selected');
    currentSelectedSentence = null;
  }
}
async function translateSelectedSentence() {
  if (!selectModel) {
    showNotification('请先选择模型', 'warning');
    return;
  }
  translateBtn.disabled = true;
  translateBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 翻译中...';
  try {
    let sourceTextContent = currentSelectedSentence.textContent;
    const translated = await makeRequest(`${API_URL}/translate`, {
      method: 'POST',
      body: JSON.stringify({
        source_text: sourceTextContent,
        source_lang: isChineseToEnglish ? "zh" : "en",
        target_lang: isChineseToEnglish ? "en" : "zh",
        category: 0,
        model_name: selectedModel,
        userId: sessionStorage.getItem("currentUserId")
      })
    });
    // 显示翻译结果
    const splited = splitText(translated.text);
    sessionStorage.setItem("currentHisId", translated.hisId);
    let fontedResult = "";
    for (let i = 0; i < splited.length; i++) {
      // 为每个句子创建单独的span元素
      fontedResult += `<span class="hover">${splited[i]}</span>`;
    }
    const savedSettings = sessionStorage.getItem('appSettings');
    const currentSettings = savedSettings ? JSON.parse(savedSettings) : { fontSize: '16px' };
    resultsContent.style.fontSize = currentSettings.fontSize;
    resultsContent.innerHTML = `
      <div class="p-3 bg-gray-50 rounded-lg min-h-[100px]">
        ${fontedResult}
      </div>
    `;
    // 添加句子选择事件
    setTimeout(() => {
      resultsContent.querySelectorAll('.hover').forEach(sentence => {
        sentence.addEventListener('click', handleSentenceClick);
      });
    }, 0);
    showNotification('翻译完成');

    // 应用主题设置
    if (typeof window.applyResultsTheme === 'function') {
      window.applyResultsTheme();
    }
  } catch (error) {
    console.error('翻译错误:', error);
    showNotification('翻译失败，请重试', 'error');
  }
  finally {
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
    updateFeedbackState();
  }
}

function speakSelectedSentence() {
  if (!currentSelectedSentence) return;
  const sentence = currentSelectedSentence.textContent;
  speakText(sentence);
  showNotification(`正在朗读选中的句子`);
}

function speakText(text, lang) {
  if ('speechSynthesis' in window) {
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    window.speechSynthesis.speak(utterance);
  } else {
    showNotification('您的浏览器不支持语音合成功能', 'warning');
  }

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
  sessionStorage.setItem("selectedModel", modelName);
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
  sessionStorage.removeItem("selectedModel");
  updateTranslateButtonState();
}

function updateTextInput() {
  charCount.textContent = sourceText.value.length;
  updateTranslateButtonState();
}
function updateFeedbackState() {
  const aBtn = document.getElementById("appreciate-btn");
  const dBtn = document.getElementById("disatisfy-btn");
  const resultText = resultsContent.textContent.trim();
  if (!resultText || resultText === '翻译结果将显示在这里' || !sessionStorage.getItem("currentUserId")) {
    aBtn.disabled = true;
    aBtn.classList.add("opacity-50", "cursor-not-allowed");
    dBtn.disabled = true;
    dBtn.classList.add("opacity-50", "cursor-not-allowed");
  } else {
    aBtn.disabled = false;
    aBtn.classList.remove("opacity-50", "cursor-not-allowed");
    dBtn.disabled = false;
    dBtn.classList.remove("opacity-50", "cursor-not-allowed");
  }
}
function updateTranslateButtonState() {
  if (selectedModel && (sourceText.value.trim().length > 0 || selectedFiles.length)) {
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
  } else {
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 请先选择模型并输入文本或文件';
    disableTranslateButton();
  }
  // 单句选中模式下禁用翻译按钮
  if (isSentenceSelectMode) {
    translateBtn.disabled = true;
    translateBtn.classList.add('opacity-50', 'cursor-not-allowed');
    translateBtn.classList.remove('hover:shadow-md');
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
  if (!selectedModel || (!sourceText.value.trim() && selectedFiles.length === 0)) return;
  translateBtn.disabled = true;
  translateBtn.innerHTML = '<i class="fa fa-spinner fa-spin mr-2"></i> 翻译中...';
  let sourceTextContent = sourceText.value.trim();
  try {
    let category = 0;
    // 如果有文件，优先使用文件
    if (selectedFiles.length > 0) {
      sourceTextContent = `[文件: ${selectedFiles[0].name}]`;
      if (selectedFiles[0].name.endsWith('.jpg') || selectedFiles[0].name.endsWith('.png') || selectedFiles[0].name.endsWith('.jpeg')) {
        category = 1;
        const formData = new FormData();
        formData.append("file", selectedFiles[0]);
        res = await fetch(`${API_URL}/translate/pic`, {
          method: 'POST',
          body: formData
        });
        jsonData = await res.json();
        Literals = jsonData.ocr_result;
        sourceTextContent = "";
        Literals.forEach(Sentence => {
          if (Sentence.category != "Picture" && Sentence.category != "picture") {
            sourceTextContent += `${Sentence.text} `;
          }
        });
      } else if (selectedFiles[0].name.endsWith('.docx') || selectedFiles[0].name.endsWith('.pdf')) {
        category = 2;
        const formData = new FormData();
        formData.append("file", selectedFiles[0]);
        res = await fetch(`${API_URL}/translate/file`, {
          method: 'POST',
          body: formData
        });
        jsonData = await res.json();
        sourceTextContent = jsonData.text;
      }
    }
    response = await makeRequest(`${API_URL}/translate`, {
      method: 'POST',
      body: JSON.stringify({
        source_text: sourceTextContent,
        source_lang: isChineseToEnglish ? "zh" : "en",
        target_lang: isChineseToEnglish ? "en" : "zh",
        category: category,
        model_name: selectedModel,
        userId: sessionStorage.getItem("currentUserId")
      })
    });
    // 显示翻译结果
    const splited = splitText(response.text);
    sessionStorage.setItem("currentHisId", response.hisId);
    let fontedResult = "";
    for (let i = 0; i < splited.length; i++) {
      // 为每个句子创建单独的span元素
      fontedResult += `<span class="hover">${splited[i]}</span>`;
    }
    const savedSettings = sessionStorage.getItem('appSettings');
    const currentSettings = savedSettings ? JSON.parse(savedSettings) : { fontSize: '16px' };
    resultsContent.style.fontSize = currentSettings.fontSize;
    resultsContent.innerHTML = `
      <div class="p-3 bg-gray-50 rounded-lg min-h-[100px]">
        ${fontedResult}
      </div>
    `;
    // 添加句子选择事件
    setTimeout(() => {
      resultsContent.querySelectorAll('.hover').forEach(sentence => {
        sentence.addEventListener('click', handleSentenceClick);
      });
    }, 0);
    showNotification('翻译完成');

    // 应用主题设置
    if (typeof window.applyResultsTheme === 'function') {
      window.applyResultsTheme();
    }
  } catch (error) {
    console.error('翻译错误:', error);
    showNotification('翻译失败，请重试', 'error');
  }
  finally {
    updateFeedbackState();
    translateBtn.innerHTML = '<i class="fa fa-language mr-2"></i> 开始翻译';
    enableTranslateButton();
  }
}
function handleSentenceClick(e) {
  // 移除之前的选择
  document.querySelectorAll('.hover.selected').forEach(s => {
    s.classList.remove('selected');
  });

  // 设置当前选择
  const sentence = e.target;
  sentence.classList.add('selected');
  currentSelectedSentence = sentence;

  // 判断句子是否在翻译结果区域
  const isInResults = sentence.closest('#results-content');

  // 获取工具栏按钮
  const translateBtn = document.getElementById('translate-sentence-btn');
  const speakBtn = document.getElementById('speak-sentence-btn');

  // 根据所在区域显示或隐藏按钮
  if (isInResults) {
    // 在翻译结果区域，隐藏翻译按钮
    translateBtn.classList.add('hidden');
    speakBtn.classList.remove('hidden');
  } else {
    // 在源文本区域，显示两个按钮
    translateBtn.classList.remove('hidden');
    speakBtn.classList.remove('hidden');
  }

  // 显示工具栏
  const rect = sentence.getBoundingClientRect();
  sentenceToolbar.style.top = `${rect.bottom + window.scrollY + 5}px`;
  sentenceToolbar.style.left = `${rect.left + window.scrollX}px`;
  sentenceToolbar.classList.add('visible');

  // 阻止事件冒泡
  e.stopPropagation();
}
function splitText(text) {
  // 用于存储断句结果
  const result = [];

  // 当前句子的起始位置
  let start = 0;

  // 遍历文本
  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    // 检查是否是句号（英文或中文）或逗号
    if (char === '.' || char === '。' || char === '!' || char === '！') {
      // 检查是否是小数点（前后都是数字）
      const isDecimal = (
        (i > 0 && /\d/.test(text[i - 1])) &&
        (i < text.length - 1 && /\d/.test(text[i + 1]))
      );

      // 如果不是小数点，则在此处断句
      if (!isDecimal) {
        // 提取句子
        const sentence = text.substring(start, i + 1);
        result.push(sentence);
        // 更新起始位置
        start = i + 1;
      }
    }
  }

  // 添加最后一个句子（如果有）
  if (start < text.length) {
    const lastSentence = text.substring(start);
    result.push(lastSentence);
  }

  return result;
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

  // 如果在单句选中模式，更新源文本句子的显示
  if (isSentenceSelectMode) {
    exitSentenceSelectMode();
    enterSentenceSelectMode();
  }
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

function renderFileList() {
  fileList.innerHTML = '';
  if (selectedFiles.length === 0) {
    // 没有文件时显示文本框
    sourceText.style.display = 'block';
    charCountContainer.style.display = 'block';
    return;
  }

  // 有文件时隐藏文本框并显示文件信息
  sourceText.style.display = 'none';
  charCountContainer.style.display = 'none';
  selectedFiles.forEach((file, index) => {
    const li = document.createElement('li');
    li.className = "flex justify-between items-center bg-gray-100 px-2 py-1 rounded mb-2";

    const fileInfo = document.createElement('div');
    fileInfo.className = "flex items-center";

    const fileIcon = document.createElement('i');
    fileIcon.className = "fa fa-file-text-o mr-2 text-primary";

    const nameSpan = document.createElement('span');
    nameSpan.textContent = file.name;
    nameSpan.className = "max-w-[200px] truncate";

    fileInfo.appendChild(fileIcon);
    fileInfo.appendChild(nameSpan);

    const removeBtn = document.createElement('button');
    removeBtn.textContent = '删除';
    removeBtn.className = "text-red-500 text-xs ml-2 hover:underline";
    removeBtn.onclick = () => {
      selectedFiles.splice(index, 1);
      renderFileList();
      updateTranslateButtonState();
    }

    li.appendChild(fileInfo);
    li.appendChild(removeBtn);
    fileList.appendChild(li);
  });
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
  const resultBlocks = document.querySelectorAll('#results-content .p-3');
  const mode = (window.currentSettings && window.currentSettings.bgMode) || 'light';
  // 设置弹窗主题
  const settingModal = document.getElementById('setting-modal-box');
  A = document.getElementById("appreciate-btn");
  D = document.getElementById("disatisfy-btn");
  if (settingModal) {
    if (mode === 'light') {
      settingModal.classList.remove('dark');
      A.classList.remove("text-white");
      A.classList.add("text-dark");
      D.classList.remove("text-white");
      D.classList.add("text-dark");
    } else {
      settingModal.classList.add('dark');
      A.classList.remove("text-dark");
      A.classList.add("text-white");
      D.classList.remove("text-dark");
      D.classList.add("text-white");
    }
  }
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
  if (mode === 'light') {
    sentenceToolbar.classList.remove('dark-mode');
  } else {
    sentenceToolbar.classList.add('dark-mode');
  }
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
  if (e.target === modal) {
    modal.style.display = 'none';
  }
});

fileInput.addEventListener('change', () => {
  // 每次只允许一个文件，替换原有文件
  selectedFiles = Array.from(fileInput.files).slice(0, 1);
  renderFileList();
  fileInput.value = '';
  updateTranslateButtonState();
});

historyLink.addEventListener('click', function (event) {
  console.log(sessionStorage.getItem("currentUserId"));
  if (sessionStorage.getItem("currentUserId") == null) {
    event.preventDefault();
    showNotification(`登陆账号后方可查询`, `warning`);
  }
});

document.addEventListener('DOMContentLoaded', init);
window.updateSentenceContainerTheme = updateSentenceContainerTheme;
const settingsModal = document.getElementById("settings-modal");
const previewBox = document.getElementById("preview-box");

// 打开/关闭弹窗
document.getElementById("open-settings").onclick = (e) => {
  e.preventDefault();
  settingsModal.classList.replace("hidden","flex");
};
document.getElementById("close-settings").onclick = () => {
  settingsModal.classList.replace("flex","hidden");
};

// 默认设置
const defaultSettings = {
  fontSize: "medium",
  theme: "light"
};

// 获取本地保存设置
let userSettings = JSON.parse(localStorage.getItem("userSettings")) || defaultSettings;

// 应用设置到预览区和全局
function applySettings() {
  // 字体大小全局生效
  switch(userSettings.fontSize){
    case "small":
      document.body.style.fontSize = "14px";
      break;
    case "medium":
      document.body.style.fontSize = "16px";
      break;
    case "large":
      document.body.style.fontSize = "18px";
      break;
  }

  // 背景主题只改背景色，字体颜色随背景自动匹配
  document.body.classList.remove("dark","eye"); // 移除之前主题类

  switch(userSettings.theme){
    case "light":
      document.body.style.backgroundColor = "#f8fafc"; // 浅色背景
      document.body.style.color = "#111827";           // 深色字体
      break;
    case "dark":
      document.body.style.backgroundColor = "#1f2937"; // 深色背景
      document.body.style.color = "#f9fafb";           // 浅色字体
      break;
    case "eye":
      document.body.style.backgroundColor = "#fef9f0"; // 护眼背景
      document.body.style.color = "#111827";           // 深色字体
      break;
  }

  // 预览框也同步背景和字体颜色
  previewBox.style.backgroundColor = document.body.style.backgroundColor;
  previewBox.style.color = document.body.style.color;
  previewBox.style.fontSize = document.body.style.fontSize;
}

// 初始化
applySettings();

// 字体大小按钮
document.querySelectorAll('[data-size]').forEach(btn => {
  btn.onclick = () => {
    userSettings.fontSize = btn.getAttribute("data-size");
    applySettings();
    localStorage.setItem("userSettings", JSON.stringify(userSettings));
  };
});

// 背景主题按钮
document.querySelectorAll('[data-theme]').forEach(btn => {
  btn.onclick = () => {
    userSettings.theme = btn.getAttribute("data-theme");
    applySettings();
    localStorage.setItem("userSettings", JSON.stringify(userSettings));
  };
});

// 重置按钮
document.getElementById("reset-settings").onclick = () => {
  userSettings = {...defaultSettings};
  applySettings();
  localStorage.setItem("userSettings", JSON.stringify(userSettings));
};

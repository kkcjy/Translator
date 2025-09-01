const feedbackModal = document.getElementById("feedback-modal");

// 打开弹窗
document.getElementById("open-feedback").onclick = (e) => {
  e.preventDefault();
  feedbackModal.classList.replace("hidden","flex");
};

// 关闭弹窗
document.getElementById("close-feedback").onclick = () => {
  feedbackModal.classList.replace("flex","hidden");
};

// 提交反馈
document.getElementById("submit-feedback").onclick = () => {
  const model = document.getElementById("model-select").value;
  const score = document.querySelector('input[name="feedback-score"]:checked')?.value;
  const text = document.getElementById("feedback-text").value;

  if (!score) {
    alert("请选择好评或差评");
    return;
  }

  // 这里可以发送到后端或存储在 localStorage
  const feedback = { model, score, text, timestamp: new Date().toISOString() };
  console.log("用户反馈：", feedback);

  // 保存示例（可选）
  let feedbackList = JSON.parse(localStorage.getItem("feedbackList")) || [];
  feedbackList.push(feedback);
  localStorage.setItem("feedbackList", JSON.stringify(feedbackList));

  alert("感谢您的反馈！");
  feedbackModal.classList.replace("flex","hidden");

  // 清空表单
  document.getElementById("feedback-text").value = "";
  document.querySelectorAll('input[name="feedback-score"]').forEach(r => r.checked = false);
  document.getElementById("model-select").selectedIndex = 0;
};

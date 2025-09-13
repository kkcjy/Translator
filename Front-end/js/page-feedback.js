const feedbackModal = document.getElementById("feedback-modal");
const comments=document.getElementById("comment-input");
const submit_comment_btn=document.getElementById("submit-comment");

// 打开弹窗
document.getElementById("appreciate-btn").onclick = (e) => {
  e.preventDefault();
  const rect=e.target.getBoundingClientRect();
  feedbackModal.style.top=`${rect.bottom+window.scrollY+5}px`;
  feedbackModal.style.left=`${rect.left+window.scrollX}px`;
  feedbackModal.classList.add("visible");
  submit_comment_btn.onclick=submit_appreciate;
};
document.getElementById("disatisfy-btn").onclick=(e)=>{
  e.preventDefault();
  const rect=e.target.getBoundingClientRect();
  feedbackModal.style.top=`${rect.bottom+window.scrollY+5}px`;
  feedbackModal.style.left=`${rect.left+window.scrollX}px`;
  feedbackModal.classList.add("visible");
  submit_comment_btn.onclick=submit_disatisfy;
}

// 关闭弹窗
document.getElementById("close-feedback").onclick = () => {
  feedbackModal.classList.remove("visible");
};

async function submit_appreciate(){
  try{
    await makeRequest(`${API_URL}/feedback`,{
      method:"PUT",
      body:JSON.stringify({
        userId:sessionStorage.getItem("currentUserId"),
        hisId:sessionStorage.getItem("currentHisId"),
        model:sessionStorage.getItem("selectedModel"),
        judge:true,
        comment:comments.textContent
      })
    });
  }catch(error){
    console.error(error);
    showNotification("反馈失败！","error");
  }
  feedbackModal.classList.remove("visible");
}

async function submit_disatisfy(){
  try{
    await makeRequest(`${API_URL}/feedback`,{
      method:"PUT",
      body:JSON.stringify({
        userId:sessionStorage.getItem("currentUserId"),
        hisId:sessionStorage.getItem("currentHisId"),
        model:sessionStorage.getItem("selectedModel"),
        judge:false,
        comment:comments.textContent
      })
    });
  }catch(error){
    console.error(error);
    showNotification("反馈失败！","error");
  }
  feedbackModal.classList.remove("visible");
}
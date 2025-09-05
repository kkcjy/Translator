// 密码显示/隐藏切换
const toggleNewPassword = document.getElementById('toggleNewPassword');
const newPasswordInput = document.getElementById('newPassword');
const toggleConfirmNewPassword = document.getElementById('toggleConfirmNewPassword');
const confirmNewPasswordInput = document.getElementById('confirmNewPassword');

function setupPasswordToggle(toggleBtn, inputField) {
    toggleBtn.addEventListener('click', () => {
        const type = inputField.getAttribute('type') === 'password' ? 'text' : 'password';
        inputField.setAttribute('type', type);
        
        // 切换图标
        const icon = toggleBtn.querySelector('i');
        if (type === 'text') {
            icon.classList.remove('fa-eye-slash');
            icon.classList.add('fa-eye');
        } else {
            icon.classList.remove('fa-eye');
            icon.classList.add('fa-eye-slash');
        }
    });
}
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

setupPasswordToggle(toggleNewPassword, newPasswordInput);
setupPasswordToggle(toggleConfirmNewPassword, confirmNewPasswordInput);

// 验证码发送
const sendCodeBtn = document.getElementById('sendCodeBtn');
sendCodeBtn.addEventListener('click', async() => {
    const email = document.getElementById('email').value.trim();
    
    if (!validateEmail(email)) {
        document.getElementById('emailError').style.display = 'block';
        return;
    }
    
    // 模拟发送验证码
    sendCodeBtn.disabled = true;
    sendCodeBtn.innerHTML = '发送中...';
    const data=await makeRequest(`${API_URL}/send-verification-code`, {
        method: 'POST',
        body: JSON.stringify({ email: email })
    });
    sessionStorage.setItem('verificationCode', data.code);

    let countdown = 60;
    setTimeout(() => {
        const timer = setInterval(() => {
            sendCodeBtn.innerHTML = `重新发送(${countdown})`;
            countdown--;
            if (countdown < 0) {
                clearInterval(timer);
                sendCodeBtn.innerHTML = '发送验证码';
                sendCodeBtn.disabled = false;
            }
        }, 1000);
        
        // 显示成功提示
        const codeError = document.getElementById('codeError');
        codeError.textContent = '验证码已发送到您的邮箱';
        codeError.style.color = '#10b981';
        codeError.style.display = 'block';
        
        setTimeout(() => {
            codeError.textContent = '验证码错误';
            codeError.style.color = '#ef4444';
            codeError.style.display = 'none';
        }, 3000);
    }, 1000);
});

// 表单提交处理
const forgotPasswordForm = document.getElementById('forgotPasswordForm');
const submitBtn = document.getElementById('submitBtn');

forgotPasswordForm.addEventListener('submit', async(e) => {
    e.preventDefault();
    let isValid = true;

    // 邮箱验证
    const email = document.getElementById('email').value.trim();
    if (!validateEmail(email)) {
        document.getElementById('emailError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('emailError').style.display = 'none';
    }

    // 验证码验证
    const verificationCode = document.getElementById('verificationCode').value.trim();
    if (verificationCode == '') {
        document.getElementById('codeError').textContent = '请输入验证码';
        document.getElementById('codeError').style.display = 'block';
        isValid = false;
    } else if(verificationCode!==sessionStorage.getItem('verificationCode')){
        document.getElementById('codeError').textContent = '验证码错误';
        document.getElementById('codeError').style.display = 'block';
        isValid = false;
    }else {
        document.getElementById('codeError').style.display = 'none';
    }

    // 新密码验证
    const newPassword = newPasswordInput.value.trim();
    if (newPassword.length < 8) {
        document.getElementById('newPasswordError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('newPasswordError').style.display = 'none';
    }

    // 确认新密码验证
    const confirmNewPassword = confirmNewPasswordInput.value.trim();
    if (confirmNewPassword !== newPassword) {
        document.getElementById('confirmError').style.display = 'block';
        isValid = false;
    } else {
        document.getElementById('confirmError').style.display = 'none';
    }

    // 如果验证通过，模拟重置密码过程
    if (isValid) {
        // 显示加载状态
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="loading-spinner"></span> 重置中...';
        try
        {
            await makeRequest(`${API_URL}/password/reset`, {
                method:"PUT",
                body:JSON.stringify({
                    email:email,
                    new_password:newPassword
                })
            });
        }catch(error)
        {
            alert("密码重置失败：" + error.message);
            console.error("密码重置失败：" + error.message);
            // 重置按钮状态
            submitBtn.disabled = false;
            submitBtn.innerHTML = '重置密码';
            return;
        }
        // 重置成功提示
        alert('密码重置成功！即将跳转到登录页面');
        
        // 重置按钮状态
        submitBtn.disabled = false;
        submitBtn.innerHTML = '重置密码';
        
        // 实际项目中此处跳转到登录页面
        window.location.href="page-login.html";
    }
});

// 邮箱验证函数
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 输入框聚焦时隐藏错误提示
const inputs = document.querySelectorAll('.form-input');
inputs.forEach(input => {
    input.addEventListener('focus', () => {
        const errorEl = input.parentElement.nextElementSibling;
        if (errorEl && errorEl.classList.contains('error-message')) {
            errorEl.style.display = 'none';
        }
    });
});
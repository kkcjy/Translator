// 修改后的page-login.js
// 密码显示/隐藏切换
const togglePassword = document.getElementById('togglePassword');
const passwordInput = document.getElementById('password');

togglePassword.addEventListener('click', () => {
    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
    passwordInput.setAttribute('type', type);
    
    // 切换图标
    const icon = togglePassword.querySelector('i');
    if (type === 'text') {
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
    } else {
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
    }
});

// FastAPI base URL
const API_URL = "http://127.0.0.1:8001";

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

// 表单提交处理
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const emailInput = document.getElementById('email');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');

loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    let isValid = true;

    // 邮箱验证
    const email = emailInput.value.trim();
    if (!validateEmail(email)) {
        emailError.style.display = 'block';
        isValid = false;
    } else {
        emailError.style.display = 'none';
    }

    // 密码验证
    const password = passwordInput.value.trim();
    if (password === '') {
        passwordError.style.display = 'block';
        isValid = false;
    } else {
        passwordError.style.display = 'none';
    }

    // 如果验证通过，发送登录请求
    if (isValid) {
        // 显示加载状态
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading-spinner"></span> 登录中...';

        try {
            // 发送登录请求到FastAPI后端
            const data = await makeRequest(`${API_URL}/login`, {
                method: "POST",
                body: JSON.stringify({ email, password })
            });

            // 登录成功
            alert('登录成功！即将跳转到首页');
            
            // 检查"记住我"选项
            const rememberMe = document.getElementById('rememberMe').checked;
            if (rememberMe) {
                // 保存邮箱到localStorage
                localStorage.setItem('savedEmail', email);
                // 保存token到localStorage
                localStorage.setItem('authToken', data.access_token);
            } else {
                localStorage.removeItem('savedEmail');
                localStorage.removeItem('authToken');
            }

            // 跳转到首页
            window.location.href = "page-translate.html";
            
        } catch (error) {
            // 登录失败
            alert('登录失败: ' + error.message);
            
            // 重置按钮状态
            loginBtn.disabled = false;
            loginBtn.innerHTML = '登录';
        }
    }
});

// 邮箱验证函数
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 页面加载时检查是否有保存的邮箱
window.addEventListener('load', () => {
    const savedEmail = localStorage.getItem('savedEmail');
    if (savedEmail) {
        emailInput.value = savedEmail;
        document.getElementById('rememberMe').checked = true;
    }
});

// 输入框聚焦时隐藏错误提示
[emailInput, passwordInput].forEach(input => {
    input.addEventListener('focus', () => {
        if (input === emailInput) {
            emailError.style.display = 'none';
        } else {
            passwordError.style.display = 'none';
        }
    });
});
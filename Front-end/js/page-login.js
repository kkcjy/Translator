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

// 表单提交处理
const loginForm = document.getElementById('loginForm');
const loginBtn = document.getElementById('loginBtn');
const emailInput = document.getElementById('email');
const emailError = document.getElementById('emailError');
const passwordError = document.getElementById('passwordError');

loginForm.addEventListener('submit', (e) => {
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

    // 如果验证通过，模拟登录过程
    if (isValid) {
        // 显示加载状态
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<span class="loading-spinner"></span> 登录中...';

        // 模拟登录请求（实际项目中替换为真实接口请求）
        setTimeout(() => {
            // 检查"记住我"选项
            const rememberMe = document.getElementById('rememberMe').checked;
            if (rememberMe) {
                // 记住密码（实际项目中应使用安全的方式存储，如HttpOnly Cookie）
                localStorage.setItem('savedEmail', email);
            } else {
                localStorage.removeItem('savedEmail');
            }

            // 登录成功提示
            alert('登录成功！即将跳转到首页');
            
            // 重置按钮状态
            loginBtn.disabled = false;
            loginBtn.innerHTML = '登录';
            
            // 实际项目中此处跳转到首页
            window.location.href="page-translate.html"
            // window.location.href = '/home';
        }, 1500);
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

# 文枢翻译系统 (Wen Shu Translator)
一个基于现代深度学习技术的多模态翻译系统，支持文本、图片和文档的精准翻译，提供专业级的中英互译服务。


## 项目概述
文枢翻译系统是一个集成了前沿AI翻译技术的全栈应用，由前端交互界面、高性能后端API和多种翻译模型组成。系统支持文本翻译、图片OCR识别翻译和文档翻译，为用户提供流畅的多语言翻译体验。


## 技术架构
### 系统架构图
```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    front end    │    │    back end     │    │      models     │
│  (HTML/JS/CSS)  │<-->│    (FastAPI)    │<-->│   (TRS + OCR)   │
└─────────────────┘    └────────┬────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │      MySQL      │
                       │                 │
                       └─────────────────┘
```

### 前端 (Frontend)
- **技术栈**: HTML5 + CSS3 + JavaScript (原生)
- **UI框架**: Tailwind CSS + 自定义样式
- **功能模块**:
  - 用户认证（登录/注册/密码找回）
  - 翻译主界面（文本/图片/文档输入）
  - 历史记录管理
  - 用户设置与个性化
  - 响应式设计（支持桌面和移动端）

### 后端 (Backend)
- **框架**: FastAPI (Python)
- **数据库**: MySQL (通过PyMySQL连接)
- **核心功能**:
  - 用户认证与权限管理
  - 翻译任务调度
  - 文件处理（PDF/DOCX解析）
  - 图片OCR处理
  - 历史记录存储
  - 邮件服务（验证码发送）

### 翻译模型 (Models)
系统集成四种翻译模型，满足不同场景需求：

| 模型类型         | 特点                                  | 技术原理                                  |
|------------------|---------------------------------------|-------------------------------------------|
| 高速翻译模型     | 极速响应，适合实时对话翻译            | 基于规则和轻量级神经网络优化              |
| 高精度翻译模型   | 专业级翻译质量，适合学术和商务场景    | 深度Transformer架构与注意力机制          |
| DeepSeek-R1模型  | 强大的上下文理解能力，AI大模型        | 基于Transformer的生成式模型（来源：DeepSeek-R1-Distill-Qwen-1.5B） |
| 通义千问模型     | 批量翻译优化，文化适配性好            | 大规模预训练语言模型（来源：Qwen/Qwen3-0.6B） |

#### OCR处理模型
- **功能**: 图片文字提取与布局分析
- **技术**: 基于Transformer的视觉-语言模型
- **输出格式**: 支持文本、表格、公式等多种元素识别


## 功能特点
- 🔄 **多格式支持**: 文本、图片(PNG/JPG)、文档(PDF/DOCX)
- 🌐 **多语言互译**: 专业级中英互译
- ⚡ **智能模型选择**: 四种专业模型适应不同场景
- 📊 **历史管理**: 完整的翻译历史记录和检索功能
- 👤 **个性化设置**: 用户头像、字体大小、主题偏好
- 📧 **安全认证**: 邮箱验证、令牌机制、密码加密
- 📱 **响应式设计**: 适配桌面和移动设备
- 🔍 **高级搜索**: 按内容、类型和时间筛选历史记录
- 📤 **数据导出**: 支持翻译记录导出功能


## 安装与部署
### 环境要求
- Python 3.8+
- MySQL 5.7+
- PyTorch 1.12+ (CPU/GPU版本)
- CUDA 11.7+ (GPU部署推荐)
- 至少16GB RAM (推荐32GB用于大模型运行)
- 至少50GB可用存储空间 (用于模型文件)

### 数据库设置
1. **创建数据库**
```sql
CREATE DATABASE Translator CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

2. **创建用户并授权**
```sql
CREATE USER 'server'@'localhost' IDENTIFIED BY 'server';
GRANT ALL PRIVILEGES ON Translator.* TO 'server'@'localhost';
FLUSH PRIVILEGES;
```

3. **导入表结构**
```sql
-- 用户表
CREATE TABLE TRS_USER (
    userId INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 令牌表
CREATE TABLE TRS_AUTHTOKEN (
    tokenId INT AUTO_INCREMENT PRIMARY KEY,
    account VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    deadline DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户设置表
CREATE TABLE TRS_SETTING (
    userId INT PRIMARY KEY,
    username VARCHAR(255),
    avatar TEXT,
    size INT DEFAULT 16,
    color VARCHAR(50) DEFAULT 'light',
    FOREIGN KEY (userId) REFERENCES TRS_USER(userId)
);

-- 翻译历史表
CREATE TABLE TRS_T_HISTORY (
    hisId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    date DATETIME NOT NULL,
    type INT NOT NULL, -- 0:文本, 1:图片, 2:文件
    input TEXT NOT NULL,
    output TEXT NOT NULL,
    FOREIGN KEY (userId) REFERENCES TRS_USER(userId)
);

-- 反馈表
CREATE TABLE TRS_T_FEEDBACK (
    feedbackId INT AUTO_INCREMENT PRIMARY KEY,
    userId INT NOT NULL,
    hisId INT NOT NULL,
    model VARCHAR(50) NOT NULL,
    judge BOOLEAN NOT NULL, -- 好评/差评
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (userId) REFERENCES TRS_USER(userId),
    FOREIGN KEY (hisId) REFERENCES TRS_T_HISTORY(hisId)
);
```

### 后端部署
1. **安装Python依赖**
```bash
pip install fastapi uvicorn pymysql python-multipart python-jose[cryptography] passlib[bcrypt] emails fastapi-mail pillow pymupdf python-docx requests transformers torch torchvision
```

2. **配置环境变量**
创建 `.env` 文件：
```ini
DB_HOST=localhost
DB_USER=server
DB_PASSWORD=server
DB_NAME=Translator
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=your_email@example.com
MAIL_PORT=465
MAIL_SERVER=smtp.example.com
MODEL_URI=http://localhost:8000
```

3. **下载模型权重**
- 下载DeepSeek-R1模型至 `model/DeepSeek-R1/`
- 下载Qwen3模型至 `model/Qwen3/`
- 下载OCR模型至 `model/DotsOCR/`

4. **启动后端服务**
```bash
uvicorn BackEnd:app --host 0.0.0.0 --port 8000 --reload
```

### 前端部署
1. **配置Web服务器**
```nginx
# Nginx配置示例
server {
    listen 80;
    server_name your_domain.com;
    
    root /path/to/translator/frontend;
    index page-translate.html;
    
    # 静态资源服务
    location / {
        try_files $uri $uri/ =404;
    }
    
    # API代理
    location /api/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    #  Websocket支持 (如果需要)
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

2. **配置API端点**
在 `js/config.js` 中设置API基础URL：
```javascript
const API_BASE_URL = 'http://your_domain.com/api';
```

### 模型服务集成
模型服务已直接集成到主后端中，无需单独部署：
- 高速翻译模型 - 直接内置在后端逻辑中
- 高精度翻译模型 - 直接内置在后端逻辑中
- DeepSeek-R1模型 - 通过HTTP API调用(需先启动模型服务)
- 通义千问模型 - 通过HTTP API调用(需先启动模型服务)

**启动开源模型服务**：
```bash
# 启动DeepSeek-R1模型服务
python Translator_API.py DeepSeek-R1

# 启动通义千问模型服务  
python Translator_API.py Qwen3
```

### 系统配置调整
1. **数据库连接配置 (db.py)**
```python
def getConnection():
    connection = pymysql.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "server"),
        password=os.getenv("DB_PASSWORD", "server"),
        database=os.getenv("DB_NAME", "Translator"),
        charset="utf8mb4"
    )
    return connection
```

2. **邮件服务配置 (BackEnd.py)**
```python
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 465)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    VALIDATE_CERTS=True
)
```


## 使用指南
### 用户注册与登录
1. 访问系统首页
2. 点击"注册/登录"按钮
3. 填写邮箱并获取验证码
4. 设置密码完成注册
5. 使用邮箱和密码登录系统

### 文本翻译
1. 在翻译界面选择源语言和目标语言
2. 在文本框中输入要翻译的内容
3. 选择适合的翻译模型
4. 点击"开始翻译"按钮
5. 查看翻译结果并可以进行复制或收藏

### 文件翻译
1. 点击"选择文件"按钮
2. 上传PDF或DOCX格式文档
3. 系统自动提取文本内容
4. 选择翻译模型并开始翻译
5. 查看并下载翻译结果

### 图片翻译
1. 点击"选择文件"按钮上传图片
2. 系统自动识别图片中的文字
3. 选择翻译模型并开始翻译
4. 查看图文对照的翻译结果

### 历史记录管理
1. 点击"历史记录"查看所有翻译历史
2. 使用搜索框按内容筛选记录
3. 按类型或时间排序历史记录
4. 选择记录进行查看、复制或删除
5. 支持批量导出历史记录


## API接口文档
启动服务后访问 `http://localhost:8000/docs` 查看完整的API文档。

### 主要接口端点
- POST `/api/token` - 获取访问令牌
- POST `/api/login` - 用户登录验证
- POST `/api/register` - 用户注册
- POST `/api/send-verification-code` - 发送邮箱验证码
- POST `/api/translate` - 文本翻译
- POST `/api/translate/file` - 文件翻译
- POST `/api/translate/pic` - 图片翻译
- GET `/api/history/{userId}` - 获取用户历史记录
- PUT `/api/settings` - 更新用户设置
- POST `/api/feedback` - 提交翻译反馈


## 故障排除
### 常见问题
1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库用户名和密码是否正确
   - 确认数据库是否存在且可访问

2. **模型加载失败**
   - 检查模型文件路径是否正确
   - 确认有足够的存储空间和内存
   - 验证PyTorch/TensorFlow版本兼容性

3. **邮件发送失败**
   - 检查邮箱SMTP设置是否正确
   - 验证邮箱密码或授权码是否正确
   - 确认网络连接允许SMTP通信

4. **文件上传失败**
   - 检查服务器存储空间是否充足
   - 确认文件大小未超过限制
   - 验证文件格式是否受支持

### 日志查看
后端服务日志默认输出到控制台，可通过以下方式查看详细错误信息：
```bash
# 查看实时日志
tail -f uvicorn.log

# 查看错误日志
grep "ERROR" uvicorn.log
```

### 性能优化建议
1. **数据库优化**
   - 为常用查询字段添加索引
   - 定期清理历史记录和过期令牌
   - 使用连接池管理数据库连接

2. **模型优化**
   - 启用模型量化减少内存占用
   - 使用模型缓存避免重复加载
   - 实现请求批处理提高吞吐量

3. **前端优化**
   - 启用资源压缩和缓存
   - 使用CDN加速静态资源加载
   - 实现懒加载减少初始负载

4. **系统监控**
   - 设置资源使用警报
   - 监控API响应时间和错误率
   - 定期备份数据库和重要文件


## 开发框架
- 后端开发: FastAPI, PyMySQL, 模型集成
- 前端开发: HTML/CSS/JavaScript, Tailwind CSS
- 模型开发: DeepSeek, Qwen, 自定义Transformer
- 系统架构: 微服务设计, 负载均衡, 高可用方案


## 支持与反馈
如有问题或建议，请通过GitHub Issues提交反馈或联系开发团队。

文枢翻译系统 - 让语言不再成为沟通的障碍
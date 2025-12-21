# 代码上传指南

本指南详细说明如何上传HTML游戏代码到AI游戏平台，包括文件准备、上传方式、安全检查和故障排除。

## 📋 前置条件

- 已部署AI游戏平台
- 准备好HTML游戏文件
- 了解基本的HTML/JavaScript知识

## 📦 文件准备

### 支持的文件格式

- **单个HTML文件** (`.html`, `.htm`)
- **ZIP压缩包** (`.zip`) - 包含HTML、CSS、JS、图片等资源

### 文件大小限制

- 最大文件大小: **1MB**
- 建议大小: **500KB以下**以获得最佳性能

### 文件结构要求

#### 单个HTML文件
```html
<!DOCTYPE html>
<html>
<head>
    <title>我的游戏</title>
    <style>
        /* CSS样式 */
    </style>
</head>
<body>
    <!-- 游戏内容 -->
    <script>
        // JavaScript代码
    </script>
</body>
</html>
```

#### ZIP压缩包结构
```
my-game.zip
├── index.html          # 必须：入口文件
├── style.css           # 可选：样式文件
├── game.js             # 可选：游戏逻辑
├── assets/             # 可选：资源文件夹
│   ├── images/
│   └── sounds/
└── lib/                # 可选：第三方库
    └── socket.io.js
```

**重要**: ZIP包必须包含 `index.html` 作为入口文件。

## 🚀 上传方式

### 方式一：使用Flutter客户端（推荐）

#### 步骤1：启动客户端
```bash
cd mobile_app/universal_game_client
flutter run -d macos
```

#### 步骤2：进入上传页面
点击应用中的 "Upload Code" 标签。

#### 步骤3：选择文件
1. 点击文件选择区域
2. 浏览并选择你的HTML文件或ZIP包
3. 确认文件大小在限制范围内

#### 步骤4：填写游戏信息
- **游戏名称** (必填): 为游戏起一个描述性的名称
- **描述** (可选): 简要说明游戏玩法
- **最大玩家数** (可选): 默认10，范围1-100

#### 步骤5：上传
点击 "Upload & Create Server" 按钮，等待：
1. 文件上传 (进度条显示)
2. 代码安全检查
3. Docker容器创建
4. 服务器注册

成功后会自动跳转到服务器列表。

### 方式二：使用API

#### 使用curl命令
```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.html" \
  -F "name=我的游戏" \
  -F "description=游戏描述" \
  -F "max_players=20"
```

#### 使用Python
```python
import requests

url = "http://localhost:8080/upload"
files = {'file': open('my-game.html', 'rb')}
data = {
    'name': '我的游戏',
    'description': '游戏描述',
    'max_players': 20
}

response = requests.post(url, files=files, data=data)
print(response.json())
```

#### 使用JavaScript/Node.js
```javascript
const FormData = require('form-data');
const fs = require('fs');
const axios = require('axios');

const form = new FormData();
form.append('file', fs.createReadStream('my-game.html'));
form.append('name', '我的游戏');
form.append('description', '游戏描述');
form.append('max_players', '20');

axios.post('http://localhost:8080/upload', form, {
    headers: form.getHeaders()
})
.then(response => console.log(response.data))
.catch(error => console.error(error));
```

## 🔒 代码安全检查

### 自动安全扫描

系统会自动检查以下潜在安全问题：

#### 1. 文件系统访问
❌ **禁止的操作**:
```javascript
const fs = require('fs');              // 文件系统模块
const path = require('path');          // 路径模块
fs.readFile('file.txt');               // 读取文件
fs.writeFile('file.txt', data);        // 写入文件
```

#### 2. 进程操作
❌ **禁止的操作**:
```javascript
const { exec } = require('child_process');  // 子进程模块
process.exit(1);                            // 退出进程
exec('rm -rf /');                           // 执行系统命令
```

#### 3. 网络请求（部分限制）
⚠️ **受限的操作**:
```javascript
const http = require('http');
http.request(options);                 // HTTP请求
https.request(options);                // HTTPS请求
```

✅ **允许的操作**:
```javascript
fetch('https://api.example.com');      // Fetch API
XMLHttpRequest                         // AJAX请求
```

#### 4. 危险函数
❌ **禁止的操作**:
```javascript
eval('malicious code');                // eval函数
new Function('return this')();         // Function构造器
```

### 安全检查结果

#### 通过检查
```json
{
  "status": "success",
  "server_id": "user123_game_001",
  "message": "游戏服务器创建成功"
}
```

#### 检查失败
```json
{
  "error": {
    "code": 400,
    "message": "代码安全检查失败",
    "details": {
      "issues": [
        {
          "severity": "high",
          "message": "检测到文件系统访问: require('fs')",
          "line": 15
        },
        {
          "severity": "high",
          "message": "检测到危险函数: eval()",
          "line": 42
        }
      ]
    }
  }
}
```

## ✅ 最佳实践

### 1. 文件优化

#### 压缩HTML
```bash
# 使用html-minifier
npm install -g html-minifier
html-minifier --collapse-whitespace --remove-comments input.html -o output.html
```

#### 优化图片
- 使用WebP格式
- 压缩PNG/JPEG
- 使用适当的分辨率

#### 内联小资源
```html
<!-- 内联小图片 -->
<img src="data:image/png;base64,iVBORw0KG..." />

<!-- 内联CSS -->
<style>
    /* 样式代码 */
</style>

<!-- 内联JavaScript -->
<script>
    // JavaScript代码
</script>
```

### 2. 代码组织

#### 模块化结构
```javascript
// 游戏状态管理
const GameState = {
    init() { /* ... */ },
    update() { /* ... */ },
    render() { /* ... */ }
};

// 网络通信
const NetworkManager = {
    connect() { /* ... */ },
    send() { /* ... */ },
    receive() { /* ... */ }
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    GameState.init();
    NetworkManager.connect();
});
```

### 3. 错误处理

```javascript
// WebSocket连接错误处理
socket.on('connect_error', (error) => {
    console.error('连接失败:', error);
    showErrorMessage('无法连接到服务器，请刷新页面重试');
});

// 游戏逻辑错误处理
try {
    updateGameState(data);
} catch (error) {
    console.error('游戏状态更新失败:', error);
    // 回退到安全状态
    resetGameState();
}
```

### 4. 性能优化

```javascript
// 使用requestAnimationFrame
function gameLoop() {
    update();
    render();
    requestAnimationFrame(gameLoop);
}

// 节流函数
function throttle(func, delay) {
    let lastCall = 0;
    return function(...args) {
        const now = Date.now();
        if (now - lastCall >= delay) {
            lastCall = now;
            func.apply(this, args);
        }
    };
}

// 防抖函数
function debounce(func, delay) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), delay);
    };
}
```

## 🔧 故障排除

### 问题1：文件上传失败

**症状**: 上传时显示错误或超时

**可能原因**:
- 文件大小超过1MB
- 网络连接不稳定
- 服务器资源不足

**解决方案**:
```bash
# 检查文件大小
ls -lh my-game.html

# 压缩文件
gzip my-game.html

# 检查服务器状态
curl http://localhost:8080/health

# 查看服务器资源
curl http://localhost:8080/system/resources
```

### 问题2：安全检查失败

**症状**: 上传被拒绝，显示安全问题

**解决方案**:
1. 查看详细错误信息
2. 移除被标记的危险代码
3. 使用允许的替代方案

**示例**:
```javascript
// ❌ 错误：使用fs模块
const fs = require('fs');
fs.readFile('data.json');

// ✅ 正确：使用fetch API
fetch('/api/data')
    .then(response => response.json())
    .then(data => console.log(data));
```

### 问题3：容器创建失败

**症状**: 上传成功但服务器状态显示"error"

**解决方案**:
```bash
# 查看服务器日志
curl http://localhost:8080/servers/{server_id}/logs

# 检查Docker状态
docker ps -a

# 查看容器日志
docker logs <container_id>

# 检查系统资源
curl http://localhost:8080/system/stats
```

### 问题4：ZIP包结构错误

**症状**: 上传ZIP包后游戏无法访问

**解决方案**:
1. 确保ZIP包根目录包含 `index.html`
2. 检查文件路径大小写
3. 验证ZIP包结构

```bash
# 查看ZIP包内容
unzip -l my-game.zip

# 正确的结构
Archive:  my-game.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
     1234  2025-12-21 10:00   index.html
      567  2025-12-21 10:00   style.css
      890  2025-12-21 10:00   game.js
```

## 📊 上传限制和配额

### 当前限制
- **文件大小**: 1MB
- **最大容器数**: 50个（可配置）
- **上传频率**: 无限制（建议合理使用）

### 查看配额使用
```bash
# 查看当前容器数
curl http://localhost:8080/system/stats

# 响应示例
{
  "game_servers_count": 5,
  "running_containers": 3,
  "stopped_containers": 2,
  "max_containers": 50
}
```

## 🎯 下一步

- [服务器管理指南](server-management.md) - 管理已上传的游戏服务器
- [游戏开发教程](../tutorials/game-development.md) - 开发更复杂的游戏
- [性能优化指南](performance-optimization.md) - 优化游戏性能

---

**相关文档**: [API参考](../reference/api-reference.md) | [故障排除](troubleshooting.md)
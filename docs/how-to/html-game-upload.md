# HTML游戏上传和服务器管理完整指南

本指南详细介绍如何使用AI游戏平台上传HTML游戏文件、创建游戏服务器并进行生命周期管理。

## 目录

1. [HTML游戏文件准备](#html游戏文件准备)
2. [上传方式](#上传方式)
3. [服务器管理](#服务器管理)
4. [游戏开发最佳实践](#游戏开发最佳实践)
5. [故障排除](#故障排除)

## HTML游戏文件准备

### 支持的文件格式

平台支持以下HTML游戏文件格式：

1. **单个HTML文件** (`.html`, `.htm`)
   - 包含完整游戏逻辑的单文件游戏
   - 所有CSS和JavaScript代码内嵌在HTML中
   - 适合简单的游戏项目

2. **ZIP压缩包** (`.zip`)
   - 包含多个文件的完整游戏项目
   - 必须包含 `index.html` 作为入口文件
   - 可以包含CSS、JavaScript、图片等资源文件

### 文件要求

- **文件大小限制**: 最大1MB
- **入口文件**: ZIP包必须包含 `index.html`
- **文件结构**: 推荐使用相对路径引用资源
- **安全要求**: 不能包含服务器端代码或恶意脚本

### HTML游戏示例

#### 简单的单文件游戏

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>简单点击游戏</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            text-align: center;
            padding: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin: 0;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .game-container {
            max-width: 600px;
            margin: 0 auto;
            padding: 30px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            backdrop-filter: blur(10px);
        }
        
        .score {
            font-size: 24px;
            margin-bottom: 20px;
        }
        
        .click-button {
            font-size: 20px;
            padding: 15px 30px;
            background: #ff6b6b;
            color: white;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            margin: 10px;
        }
        
        .click-button:hover {
            background: #ff5252;
            transform: scale(1.05);
        }
        
        .click-button:active {
            transform: scale(0.95);
        }
        
        .stats {
            margin-top: 20px;
            font-size: 16px;
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🎮 简单点击游戏</h1>
        <div class="score">得分: <span id="score">0</span></div>
        <button class="click-button" onclick="click()">点击我！</button>
        <button class="click-button" onclick="reset()">重置游戏</button>
        
        <div class="stats">
            <div>每秒点击数: <span id="cps">0</span></div>
            <div>游戏时间: <span id="time">0</span>秒</div>
        </div>
    </div>

    <script>
        let score = 0;
        let startTime = Date.now();
        let clicks = [];
        
        function updateScore() {
            document.getElementById('score').textContent = score;
            
            // 计算每秒点击数
            const now = Date.now();
            clicks = clicks.filter(time => now - time < 1000);
            document.getElementById('cps').textContent = clicks.length;
            
            // 更新游戏时间
            const gameTime = Math.floor((now - startTime) / 1000);
            document.getElementById('time').textContent = gameTime;
        }
        
        function click() {
            score++;
            clicks.push(Date.now());
            updateScore();
            
            // 添加点击效果
            const button = event.target;
            button.style.background = '#4ecdc4';
            setTimeout(() => {
                button.style.background = '#ff6b6b';
            }, 100);
        }
        
        function reset() {
            score = 0;
            startTime = Date.now();
            clicks = [];
            updateScore();
        }
        
        // 定期更新统计信息
        setInterval(updateScore, 100);
    </script>
</body>
</html>
```

#### 多文件游戏项目结构

```
my-game.zip
├── index.html          # 入口文件
├── css/
│   └── style.css      # 样式文件
├── js/
│   ├── game.js        # 游戏逻辑
│   └── utils.js       # 工具函数
└── assets/
    ├── images/        # 图片资源
    └── sounds/        # 音频资源
```

**index.html示例**:
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的HTML游戏</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <div id="game-container">
        <h1>我的HTML游戏</h1>
        <canvas id="gameCanvas" width="800" height="600"></canvas>
        <div id="ui">
            <button id="startBtn">开始游戏</button>
            <div id="score">得分: 0</div>
        </div>
    </div>
    
    <script src="js/utils.js"></script>
    <script src="js/game.js"></script>
</body>
</html>
```

## 上传方式

### 方式1：使用Flutter客户端上传

#### 步骤1：启动客户端

```bash
cd mobile_app/universal_game_client
flutter run -d macos
```

#### 步骤2：导航到上传页面

1. 在主界面点击 "Upload Code" 按钮
2. 或使用底部导航栏选择上传页面

#### 步骤3：选择文件

1. 点击文件选择区域或"选择文件"按钮
2. 从文件浏览器中选择HTML文件或ZIP压缩包
3. 确认文件大小不超过1MB

#### 步骤4：填写游戏信息

- **游戏名称** (必填): 为您的游戏输入一个描述性名称
- **游戏描述** (可选): 添加游戏的详细描述
- **最大玩家数** (可选): 设置游戏支持的最大玩家数，默认为10

#### 步骤5：上传并创建服务器

1. 点击 "Upload & Create Server" 按钮
2. 等待文件上传和验证完成
3. 系统会自动创建Docker容器并部署游戏
4. 成功后会显示服务器信息并跳转到服务器列表

### 方式2：使用API上传

#### 基本API调用

```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.html" \
  -F "name=我的HTML游戏" \
  -F "description=一个简单的HTML游戏" \
  -F "max_players=20"
```

#### 上传ZIP文件

```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.zip" \
  -F "name=复杂HTML游戏" \
  -F "description=包含多个文件的游戏项目"
```

#### Python脚本示例

```python
import requests

def upload_html_game(file_path, name, description="", max_players=10):
    url = "http://localhost:8080/upload"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'name': name,
            'description': description,
            'max_players': max_players
        }
        
        response = requests.post(url, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"上传成功！服务器ID: {result['server_id']}")
            print(f"访问地址: http://localhost:{result['port']}")
            return result
        else:
            print(f"上传失败: {response.text}")
            return None

# 使用示例
result = upload_html_game(
    file_path="my-game.html",
    name="我的点击游戏",
    description="一个简单的点击计数游戏",
    max_players=50
)
```

#### JavaScript/Node.js示例

```javascript
const FormData = require('form-data');
const fs = require('fs');
const fetch = require('node-fetch');

async function uploadHtmlGame(filePath, name, description = '', maxPlayers = 10) {
    const form = new FormData();
    form.append('file', fs.createReadStream(filePath));
    form.append('name', name);
    form.append('description', description);
    form.append('max_players', maxPlayers.toString());
    
    try {
        const response = await fetch('http://localhost:8080/upload', {
            method: 'POST',
            body: form
        });
        
        if (response.ok) {
            const result = await response.json();
            console.log(`上传成功！服务器ID: ${result.server_id}`);
            console.log(`访问地址: http://localhost:${result.port}`);
            return result;
        } else {
            const error = await response.text();
            console.error(`上传失败: ${error}`);
            return null;
        }
    } catch (error) {
        console.error(`网络错误: ${error.message}`);
        return null;
    }
}

// 使用示例
uploadHtmlGame(
    'my-game.zip',
    '我的HTML游戏',
    '包含多个文件的游戏项目',
    20
);
```

### 文件验证过程

上传的文件会经过以下验证步骤：

1. **文件格式检查**: 验证文件扩展名是否为支持的格式
2. **文件大小检查**: 确保文件不超过1MB限制
3. **文件结构检查**: 
   - 单文件：验证HTML语法
   - ZIP文件：检查是否包含index.html
4. **安全检查**: 扫描潜在的恶意内容
5. **内容验证**: 确保HTML文件可以正常解析

如果任何验证步骤失败，系统会返回详细的错误信息。

## 服务器管理

### 查看服务器列表

#### 使用Flutter客户端

1. 在主界面点击 "My Servers" 标签
2. 查看所有您创建的游戏服务器
3. 每个服务器卡片显示：
   - 游戏名称和描述
   - 服务器状态（运行中/已停止/错误）
   - 端口号和创建时间
   - 快速操作按钮

#### 使用API

```bash
# 获取服务器列表
curl http://localhost:8080/servers

# 响应示例
[
    {
        "server_id": "user_mygame_001",
        "name": "我的HTML游戏",
        "description": "一个简单的点击游戏",
        "status": "running",
        "container_id": "abc123",
        "port": 8081,
        "created_at": "2025-12-21T10:00:00Z",
        "updated_at": "2025-12-21T10:30:00Z"
    }
]
```

### 查看服务器详情

#### 使用Flutter客户端

1. 在服务器列表中点击任意服务器卡片
2. 进入服务器详情页面，查看：
   - **基本信息**: 名称、描述、状态、端口
   - **容器信息**: 容器ID、创建时间、更新时间
   - **访问信息**: 游戏访问URL
   - **操作按钮**: 访问游戏、停止、删除

#### 使用API

```bash
# 获取特定服务器详情
curl http://localhost:8080/servers/{server_id}

# 获取服务器日志
curl http://localhost:8080/servers/{server_id}/logs
```

### 访问游戏

#### 通过客户端访问

1. 在服务器详情页面点击 "访问游戏" 按钮
2. 系统会在浏览器中打开游戏URL
3. 或者复制URL在任意浏览器中访问

#### 直接访问

游戏服务器创建成功后，可以通过以下URL直接访问：

```
http://localhost:{port}/
```

其中 `{port}` 是分配给服务器的端口号。

### 服务器生命周期管理

#### 停止服务器

**使用Flutter客户端**:
1. 进入服务器详情页面
2. 点击 "停止服务器" 按钮
3. 确认操作

**使用API**:
```bash
curl -X POST http://localhost:8080/servers/{server_id}/stop
```

#### 重启服务器

**使用API**:
```bash
curl -X POST http://localhost:8080/servers/{server_id}/start
```

#### 删除服务器

**使用Flutter客户端**:
1. 进入服务器详情页面
2. 点击 "删除服务器" 按钮
3. 确认删除操作（此操作不可撤销）

**使用API**:
```bash
curl -X DELETE http://localhost:8080/servers/{server_id}
```

### 监控和日志

#### 查看服务器日志

**使用API**:
```bash
# 获取最新日志
curl http://localhost:8080/servers/{server_id}/logs

# 获取指定行数的日志
curl "http://localhost:8080/servers/{server_id}/logs?lines=100"
```

#### 监控服务器状态

**使用API**:
```bash
# 获取服务器状态
curl http://localhost:8080/servers/{server_id}/status

# 获取系统统计
curl http://localhost:8080/system/stats
```

## 游戏开发最佳实践

### HTML游戏设计原则

1. **响应式设计**: 确保游戏在不同屏幕尺寸下正常显示
2. **性能优化**: 避免复杂的动画和大量DOM操作
3. **兼容性**: 使用标准的HTML5、CSS3和JavaScript特性
4. **用户体验**: 提供清晰的游戏说明和直观的操作界面

### 推荐的技术栈

1. **HTML5 Canvas**: 用于2D图形渲染
2. **CSS3动画**: 用于简单的UI动画效果
3. **Vanilla JavaScript**: 避免依赖外部库以减小文件大小
4. **Web Audio API**: 用于音效处理
5. **LocalStorage**: 用于保存游戏进度

### 文件组织建议

```
game-project/
├── index.html          # 入口文件
├── css/
│   ├── reset.css      # CSS重置
│   ├── game.css       # 游戏样式
│   └── ui.css         # UI样式
├── js/
│   ├── game.js        # 主游戏逻辑
│   ├── player.js      # 玩家类
│   ├── enemy.js       # 敌人类
│   └── utils.js       # 工具函数
└── assets/
    ├── images/        # 图片资源（使用base64或小图片）
    └── sounds/        # 音频资源（可选）
```

### 性能优化技巧

1. **图片优化**: 
   - 使用适当的图片格式（PNG、JPEG、WebP）
   - 压缩图片大小
   - 考虑使用CSS精灵图

2. **代码优化**:
   - 压缩JavaScript和CSS代码
   - 避免全局变量污染
   - 使用事件委托减少事件监听器

3. **内存管理**:
   - 及时清理不需要的对象引用
   - 避免内存泄漏
   - 合理使用定时器

### 安全注意事项

1. **避免危险操作**: 不要尝试访问文件系统或执行系统命令
2. **输入验证**: 对用户输入进行适当的验证和清理
3. **XSS防护**: 避免直接插入用户输入到DOM中
4. **内容安全**: 不要包含恶意代码或链接

## 故障排除

### 常见上传问题

#### 问题1：文件大小超过限制

**错误信息**: "文件大小超过1MB限制"

**解决方案**:
1. 压缩图片和音频资源
2. 移除不必要的文件
3. 优化代码，删除注释和空白
4. 考虑将大型资源改为在线引用

#### 问题2：ZIP文件缺少index.html

**错误信息**: "ZIP文件中未找到index.html"

**解决方案**:
1. 确保ZIP文件根目录包含index.html
2. 检查文件名拼写是否正确
3. 确保index.html不在子文件夹中

#### 问题3：HTML文件格式错误

**错误信息**: "HTML文件格式无效"

**解决方案**:
1. 使用HTML验证工具检查语法
2. 确保文件编码为UTF-8
3. 检查HTML标签是否正确闭合

### 常见服务器问题

#### 问题1：服务器创建失败

**可能原因**:
- 系统资源不足
- Docker服务未运行
- 网络配置问题

**解决方案**:
```bash
# 检查Docker状态
docker ps

# 检查系统资源
curl http://localhost:8080/system/stats

# 查看错误日志
curl http://localhost:8080/servers/{server_id}/logs
```

#### 问题2：无法访问游戏

**可能原因**:
- 端口被占用
- 防火墙阻止访问
- 服务器未正常启动

**解决方案**:
```bash
# 检查端口占用
lsof -i :{port}

# 检查服务器状态
curl http://localhost:8080/servers/{server_id}

# 重启服务器
curl -X POST http://localhost:8080/servers/{server_id}/restart
```

#### 问题3：游戏运行异常

**可能原因**:
- JavaScript错误
- 资源文件缺失
- 浏览器兼容性问题

**解决方案**:
1. 打开浏览器开发者工具查看控制台错误
2. 检查网络面板确认资源加载情况
3. 在不同浏览器中测试游戏

### 调试技巧

1. **使用浏览器开发者工具**:
   - Console面板查看JavaScript错误
   - Network面板检查资源加载
   - Elements面板调试HTML和CSS

2. **查看服务器日志**:
   ```bash
   curl http://localhost:8080/servers/{server_id}/logs
   ```

3. **测试API端点**:
   ```bash
   # 健康检查
   curl http://localhost:8080/health
   
   # 系统状态
   curl http://localhost:8080/system/stats
   ```

### 获取帮助

如果遇到问题：

1. **查看文档**: 
   - [用户指南](USER_GUIDE.md)
   - [API参考](API_REFERENCE.md)
   - [部署指南](DEPLOYMENT_GUIDE.md)

2. **检查系统状态**:
   ```bash
   make health
   make validate
   ```

3. **查看日志文件**:
   ```bash
   make logs
   ```

4. **提交问题报告**: 
   - 包含详细的错误信息
   - 提供复现步骤
   - 附上相关日志

## 示例游戏集合

### 1. 简单点击游戏

适合初学者的基础游戏，演示基本的交互和状态管理。

### 2. 贪吃蛇游戏

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>贪吃蛇游戏</title>
    <style>
        body {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: #2c3e50;
            font-family: Arial, sans-serif;
        }
        
        .game-container {
            text-align: center;
            color: white;
        }
        
        canvas {
            border: 2px solid #ecf0f1;
            background: #34495e;
        }
        
        .score {
            font-size: 24px;
            margin: 20px 0;
        }
        
        .controls {
            margin-top: 20px;
        }
        
        button {
            padding: 10px 20px;
            font-size: 16px;
            margin: 0 10px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        
        button:hover {
            background: #2980b9;
        }
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🐍 贪吃蛇游戏</h1>
        <div class="score">得分: <span id="score">0</span></div>
        <canvas id="gameCanvas" width="400" height="400"></canvas>
        <div class="controls">
            <button onclick="startGame()">开始游戏</button>
            <button onclick="pauseGame()">暂停</button>
            <button onclick="resetGame()">重置</button>
        </div>
        <div style="margin-top: 20px;">
            <p>使用方向键控制蛇的移动</p>
        </div>
    </div>

    <script>
        const canvas = document.getElementById('gameCanvas');
        const ctx = canvas.getContext('2d');
        const scoreElement = document.getElementById('score');
        
        const gridSize = 20;
        const tileCount = canvas.width / gridSize;
        
        let snake = [
            {x: 10, y: 10}
        ];
        let food = {};
        let dx = 0;
        let dy = 0;
        let score = 0;
        let gameRunning = false;
        
        function generateFood() {
            food = {
                x: Math.floor(Math.random() * tileCount),
                y: Math.floor(Math.random() * tileCount)
            };
        }
        
        function drawGame() {
            // 清空画布
            ctx.fillStyle = '#34495e';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            
            // 绘制蛇
            ctx.fillStyle = '#2ecc71';
            for (let segment of snake) {
                ctx.fillRect(segment.x * gridSize, segment.y * gridSize, gridSize - 2, gridSize - 2);
            }
            
            // 绘制食物
            ctx.fillStyle = '#e74c3c';
            ctx.fillRect(food.x * gridSize, food.y * gridSize, gridSize - 2, gridSize - 2);
        }
        
        function updateGame() {
            if (!gameRunning) return;
            
            const head = {x: snake[0].x + dx, y: snake[0].y + dy};
            
            // 检查碰撞
            if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
                gameOver();
                return;
            }
            
            for (let segment of snake) {
                if (head.x === segment.x && head.y === segment.y) {
                    gameOver();
                    return;
                }
            }
            
            snake.unshift(head);
            
            // 检查是否吃到食物
            if (head.x === food.x && head.y === food.y) {
                score += 10;
                scoreElement.textContent = score;
                generateFood();
            } else {
                snake.pop();
            }
            
            drawGame();
        }
        
        function gameOver() {
            gameRunning = false;
            alert(`游戏结束！最终得分: ${score}`);
        }
        
        function startGame() {
            if (!gameRunning) {
                gameRunning = true;
                generateFood();
                gameLoop();
            }
        }
        
        function pauseGame() {
            gameRunning = !gameRunning;
            if (gameRunning) {
                gameLoop();
            }
        }
        
        function resetGame() {
            gameRunning = false;
            snake = [{x: 10, y: 10}];
            dx = 0;
            dy = 0;
            score = 0;
            scoreElement.textContent = score;
            generateFood();
            drawGame();
        }
        
        function gameLoop() {
            if (gameRunning) {
                updateGame();
                setTimeout(gameLoop, 150);
            }
        }
        
        // 键盘控制
        document.addEventListener('keydown', (e) => {
            if (!gameRunning) return;
            
            switch(e.key) {
                case 'ArrowUp':
                    if (dy !== 1) { dx = 0; dy = -1; }
                    break;
                case 'ArrowDown':
                    if (dy !== -1) { dx = 0; dy = 1; }
                    break;
                case 'ArrowLeft':
                    if (dx !== 1) { dx = -1; dy = 0; }
                    break;
                case 'ArrowRight':
                    if (dx !== -1) { dx = 1; dy = 0; }
                    break;
            }
        });
        
        // 初始化游戏
        resetGame();
    </script>
</body>
</html>
```

### 3. 记忆卡片游戏

演示更复杂的游戏逻辑和动画效果。

这些示例展示了不同复杂度的HTML游戏，可以作为开发参考。

---

**版本**: 1.0.0  
**最后更新**: 2025-12-21  
**适用平台**: AI游戏平台 v2.0.0+
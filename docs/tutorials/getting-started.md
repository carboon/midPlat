# 快速开始教程

欢迎使用AI游戏平台！本教程将在15分钟内带你体验平台的核心功能：上传HTML游戏、创建服务器、管理游戏。

## 🎯 学习目标

完成本教程后，你将能够：
- 部署AI游戏平台
- 上传你的第一个HTML游戏
- 创建和管理游戏服务器
- 通过客户端连接游戏

## 📋 前置条件

- 安装了Docker和Docker Compose
- 基本的命令行操作知识
- 一个简单的HTML文件（我们会提供示例）

## 🚀 第一步：部署平台

### 1.1 克隆项目

```bash
git clone <repository-url>
cd ai-game-platform
```

### 1.2 一键部署

```bash
make deploy
```

这个命令会：
- 初始化Docker网络
- 构建所有服务镜像
- 启动所有服务
- 验证部署状态

等待几分钟，直到看到 ✅ 部署成功的消息。

### 1.3 验证部署

```bash
make health-quick
```

你应该看到所有服务都显示为 "healthy"。

## 🎮 第二步：创建你的第一个HTML游戏

### 2.1 创建游戏文件

创建一个名为 `my-first-game.html` 的文件：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的第一个游戏</title>
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
    </style>
</head>
<body>
    <div class="game-container">
        <h1>🎮 我的第一个游戏</h1>
        <div class="score">得分: <span id="score">0</span></div>
        <button class="click-button" onclick="clickButton()">点击我！</button>
        <button class="click-button" onclick="resetGame()">重置</button>
    </div>

    <script>
        let score = 0;
        
        function clickButton() {
            score++;
            document.getElementById('score').textContent = score;
            
            // 添加点击效果
            const button = event.target;
            button.style.background = '#4ecdc4';
            setTimeout(() => {
                button.style.background = '#ff6b6b';
            }, 100);
        }
        
        function resetGame() {
            score = 0;
            document.getElementById('score').textContent = score;
        }
    </script>
</body>
</html>
```

### 2.2 测试游戏文件

在浏览器中打开 `my-first-game.html`，确保游戏正常工作。

## 📱 第三步：启动Flutter客户端

### 3.1 启动客户端

```bash
cd mobile_app/universal_game_client
flutter pub get
flutter run -d macos
```

等待Flutter应用启动。

### 3.2 熟悉界面

Flutter应用包含三个主要标签：
- **Home** - 浏览可用的游戏房间
- **My Servers** - 管理你创建的游戏服务器
- **Upload Code** - 上传HTML游戏文件

## 📤 第四步：上传游戏

### 4.1 进入上传页面

在Flutter应用中点击 "Upload Code" 标签。

### 4.2 选择文件

1. 点击文件选择区域
2. 选择你刚创建的 `my-first-game.html` 文件

### 4.3 填写信息

- **游戏名称**: "我的第一个游戏"
- **描述**: "一个简单的点击计数游戏"
- **最大玩家数**: 保持默认值 10

### 4.4 上传

点击 "Upload & Create Server" 按钮。

你会看到：
1. 文件上传进度
2. 代码安全检查
3. 容器创建过程
4. 成功后自动跳转到服务器列表

## 🎯 第五步：管理服务器

### 5.1 查看服务器列表

在 "My Servers" 标签中，你应该看到刚创建的服务器：
- 服务器名称
- 状态指示器（绿色表示运行中）
- 端口号
- 创建时间

### 5.2 查看服务器详情

点击服务器卡片，查看详细信息：
- 基本信息（ID、端口、状态）
- 资源使用情况（CPU、内存）
- 实时日志输出

### 5.3 访问游戏

在服务器详情页面，点击 "访问游戏" 按钮，游戏会在浏览器中打开。

## 🌐 第六步：通过房间列表连接

### 6.1 查看房间列表

回到 "Home" 标签，你应该看到你的游戏出现在房间列表中。

### 6.2 连接游戏

点击房间卡片，然后点击 "Join Game" 按钮，游戏会在应用内的WebView中打开。

## 🎉 恭喜！

你已经成功：
- ✅ 部署了AI游戏平台
- ✅ 创建了你的第一个HTML游戏
- ✅ 上传并部署了游戏服务器
- ✅ 通过客户端管理和访问游戏

## 🔄 清理资源

完成教程后，你可以清理创建的资源：

### 删除游戏服务器

在Flutter应用的服务器详情页面，点击 "Delete Server" 按钮。

### 停止平台服务

```bash
make stop
```

## 📚 下一步

现在你已经掌握了基础操作，可以继续学习：

- [第一个HTML游戏教程](first-html-game.md) - 创建更复杂的游戏
- [HTML游戏开发指南](../how-to/develop-html-games.md) - 开发最佳实践
- [服务器管理指南](../how-to/manage-servers.md) - 高级服务器管理

## ❓ 遇到问题？

如果在教程过程中遇到问题：

1. **检查服务状态**
   ```bash
   make health
   ```

2. **查看日志**
   ```bash
   make logs
   ```

3. **重启服务**
   ```bash
   make restart
   ```

4. **查看故障排除指南**
   参考 [故障排除指南](../how-to/troubleshooting.md)

## 💡 小贴士

- 游戏文件大小限制为1MB
- 支持单个HTML文件或ZIP压缩包
- 系统会自动进行安全检查
- 闲置30分钟的服务器会自动停止以节省资源

---

**预计完成时间**: 15分钟  
**难度级别**: 初级  
**下一个教程**: [第一个HTML游戏](first-html-game.md)
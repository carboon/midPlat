# HTML游戏开发教程

本教程将指导您从零开始开发一个完整的HTML游戏，并部署到AI游戏平台上。

## 🎯 学习目标

- 了解HTML游戏开发基础
- 学习WebSocket实时通信
- 掌握多人游戏状态同步
- 实现游戏的部署和测试

## 📋 前置条件

- 完成[快速开始教程](getting-started.md)
- 基本的HTML、CSS、JavaScript知识
- 了解WebSocket概念

## 🎮 项目概述

我们将开发一个名为"彩色方块"的多人实时游戏：
- 玩家可以点击改变方块颜色
- 所有玩家实时看到颜色变化
- 显示在线玩家数量
- 支持玩家昵称

## 🏗️ 第一步：创建基础HTML结构

创建 `color-blocks-game.html`：

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>彩色方块 - 多人游戏</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Arial', sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        .header {
            padding: 20px;
            text-align: center;
            background: rgba(0, 0, 0, 0.2);
        }

        .game-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }

        .player-count {
            background: rgba(255, 255, 255, 0.2);
            padding: 10px 20px;
            border-radius: 20px;
        }

        .game-container {
            flex: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }

        .game-board {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 10px;
            max-width: 400px;
            width: 100%;
        }

        .color-block {
            aspect-ratio: 1;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }

        .color-block:hover {
            transform: scale(1.05);
            border-color: white;
        }

        .controls {
            text-align: center;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
        }

        .nickname-input {
            padding: 10px;
            border: none;
            border-radius: 5px;
            margin-right: 10px;
            font-size: 16px;
        }

        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
            background: #ff6b6b;
            color: white;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        .btn:hover {
            background: #ff5252;
        }

        .status {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
            background: rgba(255, 255, 255, 0.1);
        }

        .connected {
            background: rgba(76, 175, 80, 0.3);
        }

        .disconnected {
            background: rgba(244, 67, 54, 0.3);
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎨 彩色方块</h1>
        <div class="game-info">
            <div class="player-count">
                在线玩家: <span id="playerCount">0</span>
            </div>
            <div id="connectionStatus" class="status disconnected">
                未连接
            </div>
        </div>
    </div>

    <div class="game-container">
        <div class="game-board" id="gameBoard">
            <!-- 方块将通过JavaScript生成 -->
        </div>
    </div>

    <div class="controls">
        <input type="text" id="nicknameInput" class="nickname-input" placeholder="输入你的昵称" maxlength="20">
        <button onclick="setNickname()" class="btn">设置昵称</button>
        <button onclick="resetBoard()" class="btn">重置游戏</button>
        
        <div id="gameStatus" class="status">
            欢迎来到彩色方块游戏！点击方块改变颜色。
        </div>
    </div>

    <!-- Socket.IO客户端库 -->
    <script src="https://cdn.socket.io/4.7.4/socket.io.min.js"></script>
    <script>
        // 游戏状态
        let socket = null;
        let playerNickname = '';
        let gameState = {
            blocks: [],
            players: []
        };

        // 颜色数组
        const colors = [
            '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4',
            '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd',
            '#00d2d3', '#ff9f43', '#10ac84', '#ee5a24'
        ];

        // 初始化游戏
        function initGame() {
            createGameBoard();
            connectToServer();
        }

        // 创建游戏板
        function createGameBoard() {
            const gameBoard = document.getElementById('gameBoard');
            gameBoard.innerHTML = '';
            
            for (let i = 0; i < 16; i++) {
                const block = document.createElement('div');
                block.className = 'color-block';
                block.style.backgroundColor = colors[0];
                block.textContent = i + 1;
                block.onclick = () => changeBlockColor(i);
                gameBoard.appendChild(block);
                
                gameState.blocks[i] = colors[0];
            }
        }

        // 连接到服务器
        function connectToServer() {
            // 在实际部署时，这个URL会自动指向正确的服务器
            socket = io();
            
            socket.on('connect', () => {
                updateConnectionStatus(true);
                updateGameStatus('已连接到游戏服务器');
            });

            socket.on('disconnect', () => {
                updateConnectionStatus(false);
                updateGameStatus('与服务器断开连接');
            });

            socket.on('gameState', (state) => {
                updateGameState(state);
            });

            socket.on('playerJoined', (data) => {
                updateGameStatus(`${data.nickname} 加入了游戏`);
            });

            socket.on('playerLeft', (data) => {
                updateGameStatus(`${data.nickname} 离开了游戏`);
            });

            socket.on('blockChanged', (data) => {
                updateBlock(data.blockIndex, data.color);
                updateGameStatus(`${data.playerNickname} 改变了方块 ${data.blockIndex + 1} 的颜色`);
            });
        }

        // 改变方块颜色
        function changeBlockColor(blockIndex) {
            if (!socket || !socket.connected) {
                updateGameStatus('请先连接到服务器');
                return;
            }

            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            
            socket.emit('changeBlock', {
                blockIndex: blockIndex,
                color: randomColor,
                playerNickname: playerNickname || '匿名玩家'
            });
        }

        // 更新方块
        function updateBlock(blockIndex, color) {
            const blocks = document.querySelectorAll('.color-block');
            if (blocks[blockIndex]) {
                blocks[blockIndex].style.backgroundColor = color;
                gameState.blocks[blockIndex] = color;
            }
        }

        // 更新游戏状态
        function updateGameState(state) {
            if (state.blocks) {
                state.blocks.forEach((color, index) => {
                    updateBlock(index, color);
                });
            }
            
            if (state.playerCount !== undefined) {
                document.getElementById('playerCount').textContent = state.playerCount;
            }
        }

        // 设置昵称
        function setNickname() {
            const input = document.getElementById('nicknameInput');
            const nickname = input.value.trim();
            
            if (nickname) {
                playerNickname = nickname;
                input.disabled = true;
                
                if (socket && socket.connected) {
                    socket.emit('setNickname', { nickname: nickname });
                }
                
                updateGameStatus(`昵称设置为: ${nickname}`);
            }
        }

        // 重置游戏板
        function resetBoard() {
            if (!socket || !socket.connected) {
                updateGameStatus('请先连接到服务器');
                return;
            }

            socket.emit('resetBoard', {
                playerNickname: playerNickname || '匿名玩家'
            });
        }

        // 更新连接状态
        function updateConnectionStatus(connected) {
            const statusElement = document.getElementById('connectionStatus');
            if (connected) {
                statusElement.textContent = '已连接';
                statusElement.className = 'status connected';
            } else {
                statusElement.textContent = '未连接';
                statusElement.className = 'status disconnected';
            }
        }

        // 更新游戏状态消息
        function updateGameStatus(message) {
            const statusElement = document.getElementById('gameStatus');
            statusElement.textContent = message;
            
            // 3秒后清除消息
            setTimeout(() => {
                if (statusElement.textContent === message) {
                    statusElement.textContent = '点击方块改变颜色，与其他玩家一起游戏！';
                }
            }, 3000);
        }

        // 页面加载完成后初始化游戏
        document.addEventListener('DOMContentLoaded', initGame);
    </script>
</body>
</html>
```

## 🔧 第二步：理解代码结构

### 2.1 HTML结构
- **header**: 显示游戏标题和状态信息
- **game-container**: 包含4x4的游戏方块网格
- **controls**: 昵称设置和游戏控制按钮

### 2.2 CSS样式
- 使用CSS Grid创建响应式游戏板
- 渐变背景和现代化UI设计
- 悬停效果和过渡动画

### 2.3 JavaScript功能
- **Socket.IO客户端**: 处理实时通信
- **游戏状态管理**: 同步所有玩家的游戏状态
- **事件处理**: 响应用户交互和服务器事件

## 🌐 第三步：WebSocket事件处理

### 3.1 客户端事件
```javascript
// 发送给服务器的事件
socket.emit('changeBlock', data);    // 改变方块颜色
socket.emit('setNickname', data);    // 设置玩家昵称
socket.emit('resetBoard', data);     // 重置游戏板
```

### 3.2 服务器事件
```javascript
// 从服务器接收的事件
socket.on('gameState', callback);    // 接收完整游戏状态
socket.on('blockChanged', callback); // 接收方块变化
socket.on('playerJoined', callback); // 玩家加入通知
socket.on('playerLeft', callback);   // 玩家离开通知
```

## 📤 第四步：上传和测试

### 4.1 上传游戏

1. 在Flutter客户端中选择 "Upload Code"
2. 选择 `color-blocks-game.html` 文件
3. 填写游戏信息：
   - 名称: "彩色方块"
   - 描述: "多人实时彩色方块游戏"
   - 最大玩家数: 20

### 4.2 测试游戏

1. 上传成功后，在服务器列表中找到你的游戏
2. 点击访问游戏
3. 设置昵称
4. 尝试点击方块改变颜色
5. 在多个浏览器标签页中打开游戏测试多人功能

## 🔍 第五步：调试和优化

### 5.1 查看服务器日志

在Flutter客户端的服务器详情页面查看实时日志，了解：
- WebSocket连接状态
- 玩家加入/离开事件
- 游戏状态变化

### 5.2 常见问题排查

**问题**: WebSocket连接失败
```javascript
// 解决方案：检查Socket.IO版本兼容性
socket.on('connect_error', (error) => {
    console.error('连接错误:', error);
    updateGameStatus('连接失败，请刷新页面重试');
});
```

**问题**: 游戏状态不同步
```javascript
// 解决方案：添加状态验证
socket.on('gameState', (state) => {
    if (state && state.blocks && Array.isArray(state.blocks)) {
        updateGameState(state);
    }
});
```

## 🚀 第六步：高级功能扩展

### 6.1 添加音效

```javascript
// 添加音效支持
function playSound(type) {
    const audio = new Audio();
    switch(type) {
        case 'click':
            audio.src = 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT';
            break;
        case 'join':
            // 玩家加入音效
            break;
    }
    audio.play().catch(() => {}); // 忽略自动播放限制错误
}
```

### 6.2 添加动画效果

```css
@keyframes blockPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.1); }
    100% { transform: scale(1); }
}

.color-block.changed {
    animation: blockPulse 0.3s ease;
}
```

### 6.3 添加游戏统计

```javascript
let gameStats = {
    totalClicks: 0,
    playerClicks: 0,
    sessionStart: Date.now()
};

function updateStats() {
    const sessionTime = Math.floor((Date.now() - gameStats.sessionStart) / 1000);
    document.getElementById('stats').innerHTML = `
        游戏时间: ${sessionTime}秒 | 
        总点击: ${gameStats.totalClicks} | 
        我的点击: ${gameStats.playerClicks}
    `;
}
```

## 📊 第七步：性能优化

### 7.1 减少网络请求

```javascript
// 批量处理状态更新
let pendingUpdates = [];
let updateTimeout = null;

function batchUpdateBlocks(updates) {
    pendingUpdates.push(...updates);
    
    if (updateTimeout) clearTimeout(updateTimeout);
    
    updateTimeout = setTimeout(() => {
        processBatchUpdates(pendingUpdates);
        pendingUpdates = [];
    }, 50); // 50ms批处理间隔
}
```

### 7.2 优化渲染性能

```javascript
// 使用requestAnimationFrame优化动画
function smoothColorTransition(element, fromColor, toColor) {
    let progress = 0;
    
    function animate() {
        progress += 0.1;
        
        if (progress <= 1) {
            const color = interpolateColor(fromColor, toColor, progress);
            element.style.backgroundColor = color;
            requestAnimationFrame(animate);
        }
    }
    
    requestAnimationFrame(animate);
}
```

## 🎉 完成！

恭喜你完成了HTML游戏开发教程！你现在已经：

- ✅ 创建了一个完整的多人实时游戏
- ✅ 掌握了WebSocket实时通信
- ✅ 学会了游戏状态同步
- ✅ 了解了性能优化技巧

## 📚 下一步学习

- [高级游戏开发](advanced-game-development.md) - 学习更复杂的游戏机制
- [游戏部署最佳实践](../how-to/game-deployment-best-practices.md) - 生产环境部署
- [性能优化指南](../how-to/performance-optimization.md) - 深入性能优化

## 💡 开发小贴士

1. **保持简单**: 从简单的游戏机制开始，逐步添加复杂功能
2. **测试优先**: 每添加一个功能都要充分测试
3. **用户体验**: 关注游戏的响应性和视觉反馈
4. **错误处理**: 优雅地处理网络断开和错误情况
5. **性能监控**: 定期检查游戏性能和资源使用

---

**预计完成时间**: 45分钟  
**难度级别**: 中级  
**相关教程**: [快速开始](getting-started.md) | [部署教程](deployment.md)
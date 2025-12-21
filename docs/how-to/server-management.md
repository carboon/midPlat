# 代码上传和服务器管理完整指南

## 目录

1. [概述](#概述)
2. [代码上传指南](#代码上传指南)
3. [服务器管理指南](#服务器管理指南)
4. [最佳实践](#最佳实践)
5. [故障排除](#故障排除)
6. [API参考](#api参考)

## 概述

AI游戏平台提供了完整的代码上传和服务器管理功能，允许开发者上传JavaScript游戏代码并自动创建隔离的游戏服务器容器。本指南详细说明了如何使用这些功能。

### 核心功能

- **代码上传**: 上传JavaScript游戏代码文件
- **自动部署**: 自动创建Docker容器并部署游戏服务器
- **安全检查**: 自动扫描代码中的安全风险
- **生命周期管理**: 启动、停止、删除服务器
- **实时监控**: 查看服务器状态、资源使用和日志
- **自动注册**: 游戏服务器自动注册到撮合服务

## 代码上传指南

### 准备游戏代码

#### 基本结构

您的JavaScript游戏代码应该遵循以下基本结构：

```javascript
// 1. 导入必要的模块
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

// 2. 创建Express应用和HTTP服务器
const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 3. 定义游戏状态
let gameState = {
    players: [],
    gameData: {}
};

// 4. 处理WebSocket连接
io.on('connection', (socket) => {
    console.log('玩家连接:', socket.id);
    
    // 发送当前游戏状态
    socket.emit('gameState', gameState);
    
    // 处理游戏操作
    socket.on('gameAction', (data) => {
        // 处理游戏逻辑
        console.log('收到游戏操作:', data);
        
        // 更新游戏状态
        gameState.gameData = { ...gameState.gameData, ...data };
        
        // 广播给所有客户端
        io.emit('gameState', gameState);
    });
    
    // 处理断开连接
    socket.on('disconnect', () => {
        console.log('玩家断开:', socket.id);
    });
});

// 5. 提供静态文件（可选）
app.use(express.static('public'));

// 6. 启动服务器
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
    console.log(`游戏服务器运行在端口 ${PORT}`);
});
```

#### 环境变量支持

您的代码可以使用以下环境变量：

```javascript
// 服务器配置
const PORT = process.env.PORT || 8080;
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';

// 游戏配置
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;
const GAME_MODE = process.env.GAME_MODE || 'normal';
```

### 代码要求和限制

#### 文件要求

- **文件格式**: `.js` 或 `.mjs`
- **文件大小**: 最大 1MB
- **编码**: UTF-8
- **语法**: 有效的JavaScript ES6+语法

#### 安全限制

系统会自动检测并拒绝包含以下内容的代码：

**禁止的操作（高风险）**:
- 文件系统访问: `require('fs')`, `require('path')`
- 子进程执行: `require('child_process')`, `exec()`, `spawn()`
- 危险函数: `eval()`, `new Function()`
- 进程退出: `process.exit()`

**警告的操作（中等风险）**:
- 直接网络请求: `http.request()`, `https.request()`
- 全局对象操作: `global.*`
- 进程操作: `process.env` (读取允许，修改警告)

#### 推荐的依赖包

您的代码可以使用以下npm包（已预装在容器中）：

- `express`: Web框架
- `socket.io`: WebSocket实时通信
- `axios`: HTTP客户端（用于API调用）
- `lodash`: 工具函数库
- `uuid`: UUID生成

### 使用Flutter客户端上传

#### 步骤1: 启动客户端

```bash
cd mobile_app/universal_game_client
flutter run -d macos
```

#### 步骤2: 导航到上传页面

1. 在主界面点击 "Upload Code" 按钮
2. 或使用底部导航栏选择上传标签

#### 步骤3: 选择文件

1. 点击文件选择区域或"选择文件"按钮
2. 浏览并选择您的JavaScript文件
3. 确认文件大小不超过1MB

#### 步骤4: 填写信息

- **游戏名称** (必填): 为您的游戏输入一个描述性名称
  - 示例: "多人点击游戏", "实时聊天室"
  
- **描述** (可选): 添加游戏的详细描述
  - 示例: "一个简单的多人点击计数游戏，支持实时同步"
  
- **最大玩家数** (可选): 设置房间最大玩家数
  - 默认: 10
  - 范围: 1-100

#### 步骤5: 上传

1. 点击 "Upload & Create Server" 按钮
2. 等待上传和代码分析完成
3. 系统会显示上传进度
4. 成功后自动跳转到服务器列表

#### 上传过程

上传过程包含以下步骤：

1. **文件验证**: 检查文件格式和大小
2. **代码分析**: 语法检查和安全扫描
3. **容器创建**: 创建Docker容器
4. **代码注入**: 将您的代码注入到容器中
5. **服务启动**: 启动游戏服务器
6. **自动注册**: 注册到撮合服务

### 使用API上传

#### 基本上传

```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.js" \
  -F "name=我的游戏" \
  -F "description=游戏描述"
```

#### 完整参数上传

```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.js" \
  -F "name=多人点击游戏" \
  -F "description=一个实时多人点击计数游戏" \
  -F "max_players=20"
```

#### 响应示例

成功响应：
```json
{
  "status": "success",
  "server_id": "user123_mygame_001",
  "message": "游戏服务器创建成功",
  "server": {
    "server_id": "user123_mygame_001",
    "name": "我的游戏",
    "status": "creating",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z"
  }
}
```

失败响应：
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
          "line": 5
        }
      ]
    }
  }
}
```

### 代码安全检查详解

#### 检查流程

1. **语法验证**: 使用AST解析器验证JavaScript语法
2. **模式匹配**: 检测危险的代码模式
3. **依赖分析**: 分析require语句
4. **风险评估**: 根据检测结果评估风险等级

#### 安全检查示例

**会被拒绝的代码**:
```javascript
// ❌ 文件系统访问
const fs = require('fs');
fs.readFileSync('/etc/passwd');

// ❌ 子进程执行
const { exec } = require('child_process');
exec('rm -rf /');

// ❌ eval函数
eval('malicious code');
```

**会发出警告的代码**:
```javascript
// ⚠️ 直接HTTP请求（建议使用axios）
const http = require('http');
http.request('http://external-api.com');

// ⚠️ 全局对象操作
global.myVar = 'value';
```

**安全的代码**:
```javascript
// ✅ 使用Express和Socket.IO
const express = require('express');
const socketIo = require('socket.io');

// ✅ 使用axios进行API调用
const axios = require('axios');
axios.post(process.env.MATCHMAKER_URL + '/register');

// ✅ 使用环境变量
const PORT = process.env.PORT || 8080;
```

## 服务器管理指南

### 查看服务器列表

#### 使用Flutter客户端

1. 在主界面点击 "My Servers" 标签
2. 查看所有您创建的游戏服务器
3. 每个服务器卡片显示：
   - 服务器名称
   - 状态指示器（运行中/已停止/错误）
   - 端口号
   - 创建时间

#### 服务器状态说明

- **creating**: 容器正在创建中
- **running**: 服务器正常运行
- **stopped**: 服务器已停止
- **error**: 服务器出现错误

#### 使用API查询

```bash
# 获取所有服务器
curl http://localhost:8080/servers

# 响应示例
[
  {
    "server_id": "user123_game1_001",
    "name": "我的第一个游戏",
    "status": "running",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z"
  }
]
```

### 查看服务器详情

#### 使用Flutter客户端

1. 在服务器列表中点击任意服务器卡片
2. 进入服务器详情页面
3. 查看详细信息：

**基本信息**:
- 服务器ID
- 游戏名称
- 描述
- 状态
- 端口号
- 容器ID
- 创建时间
- 更新时间

**资源使用**:
- CPU使用率 (%)
- 内存使用 (MB)
- 网络I/O

**服务器日志**:
- 实时日志输出
- 最近100条日志记录
- 自动滚动到最新

#### 使用API查询

```bash
# 获取服务器详情
curl http://localhost:8080/servers/{server_id}

# 响应示例
{
  "server_id": "user123_game1_001",
  "name": "我的第一个游戏",
  "description": "一个简单的点击游戏",
  "status": "running",
  "container_id": "abc123def456",
  "port": 8081,
  "created_at": "2025-12-20T10:00:00Z",
  "updated_at": "2025-12-20T10:30:00Z",
  "resource_usage": {
    "cpu_percent": 15.5,
    "memory_mb": 128,
    "network_io": "1.2MB"
  },
  "logs": [
    "Server started on port 8081",
    "Game initialized",
    "Player connected: socket_abc123"
  ]
}
```

### 停止服务器

#### 使用Flutter客户端

1. 进入服务器详情页面
2. 点击 "Stop Server" 按钮
3. 确认操作
4. 等待服务器停止（通常需要几秒钟）
5. 状态更新为 "stopped"

#### 使用API

```bash
curl -X POST http://localhost:8080/servers/{server_id}/stop

# 响应示例
{
  "status": "success",
  "message": "服务器已停止",
  "server_id": "user123_game1_001"
}
```

#### 停止行为

- 优雅关闭：给予服务器30秒时间完成当前操作
- 断开连接：自动断开所有WebSocket连接
- 保留数据：容器保留，可以重新启动
- 资源释放：释放CPU和内存资源

### 删除服务器

#### 使用Flutter客户端

1. 进入服务器详情页面
2. 点击 "Delete Server" 按钮
3. 确认删除操作（此操作不可撤销）
4. 等待删除完成
5. 自动返回服务器列表

#### 使用API

```bash
curl -X DELETE http://localhost:8080/servers/{server_id}

# 响应示例
{
  "status": "success",
  "message": "服务器已删除",
  "server_id": "user123_game1_001"
}
```

#### 删除行为

- 停止容器：如果正在运行，先停止
- 删除容器：完全删除Docker容器
- 清理资源：释放端口和网络资源
- 注销服务：从撮合服务注销
- 不可恢复：删除后无法恢复

### 查看服务器日志

#### 使用Flutter客户端

在服务器详情页面的日志区域：
- 自动显示最近100条日志
- 支持手动刷新
- 自动滚动到最新日志
- 显示时间戳

#### 使用API

```bash
# 获取服务器日志
curl http://localhost:8080/servers/{server_id}/logs

# 响应示例
{
  "server_id": "user123_game1_001",
  "logs": [
    "[2025-12-20 10:00:00] Server started on port 8081",
    "[2025-12-20 10:00:01] Game initialized",
    "[2025-12-20 10:00:05] Player connected: socket_abc123",
    "[2025-12-20 10:00:10] Game action received: click"
  ]
}
```

### 监控资源使用

#### 实时监控

在服务器详情页面查看实时资源使用：

- **CPU使用率**: 显示当前CPU使用百分比
- **内存使用**: 显示当前内存使用量（MB）
- **网络I/O**: 显示网络传输量

#### 系统级监控

```bash
# 查看所有容器状态
curl http://localhost:8080/containers/status

# 查看系统统计
curl http://localhost:8080/system/stats

# 查看资源管理统计
curl http://localhost:8080/system/resources
```

### 自动资源管理

系统会自动管理服务器资源：

#### 闲置容器清理

- **检测间隔**: 每5分钟检查一次
- **闲置超时**: 默认30分钟无活动
- **自动停止**: 自动停止闲置容器
- **通知**: 通过日志记录清理操作

#### 资源限制

- **最大容器数**: 默认50个（可配置）
- **单容器内存**: 默认512MB
- **单容器CPU**: 默认1.0核心
- **达到限制**: 拒绝创建新服务器

## 最佳实践

### 代码开发

#### 1. 模块化设计

```javascript
// 推荐：将游戏逻辑分离到不同模块
class GameState {
    constructor() {
        this.players = new Map();
        this.gameData = {};
    }
    
    addPlayer(socketId, playerData) {
        this.players.set(socketId, playerData);
    }
    
    removePlayer(socketId) {
        this.players.delete(socketId);
    }
}

class GameLogic {
    static processAction(gameState, action) {
        // 处理游戏逻辑
    }
}
```

#### 2. 错误处理

```javascript
// 推荐：添加适当的错误处理
io.on('connection', (socket) => {
    socket.on('gameAction', (data) => {
        try {
            // 验证输入
            if (!data || !data.type) {
                socket.emit('error', { message: '无效的操作' });
                return;
            }
            
            // 处理操作
            const result = GameLogic.processAction(gameState, data);
            io.emit('gameState', result);
        } catch (error) {
            console.error('处理操作失败:', error);
            socket.emit('error', { message: '操作失败' });
        }
    });
});
```

#### 3. 状态同步

```javascript
// 推荐：定期同步游戏状态
setInterval(() => {
    io.emit('gameState', gameState.getState());
}, 1000); // 每秒同步一次
```

#### 4. 性能优化

```javascript
// 推荐：批量处理更新
let pendingUpdates = [];

socket.on('gameAction', (data) => {
    pendingUpdates.push(data);
});

setInterval(() => {
    if (pendingUpdates.length > 0) {
        // 批量处理
        const updates = pendingUpdates.splice(0);
        updates.forEach(update => {
            GameLogic.processAction(gameState, update);
        });
        
        // 一次性广播
        io.emit('gameState', gameState.getState());
    }
}, 100); // 每100ms处理一次
```

### 服务器管理

#### 1. 及时清理

- 删除不再使用的测试服务器
- 定期检查服务器列表
- 避免创建过多服务器

#### 2. 监控资源

- 定期查看资源使用情况
- 关注CPU和内存使用率
- 注意系统容器数量限制

#### 3. 日志管理

- 定期查看服务器日志
- 关注错误和警告信息
- 使用日志排查问题

#### 4. 测试流程

1. **本地测试**: 在上传前本地测试代码
2. **创建测试服务器**: 先创建测试服务器验证
3. **监控运行**: 观察服务器运行状态
4. **正式部署**: 验证无误后正式使用

### 安全性

#### 1. 输入验证

```javascript
// 推荐：验证所有客户端输入
socket.on('gameAction', (data) => {
    // 验证数据类型
    if (typeof data.value !== 'number') {
        return socket.emit('error', { message: '无效的数值' });
    }
    
    // 验证数据范围
    if (data.value < 0 || data.value > 100) {
        return socket.emit('error', { message: '数值超出范围' });
    }
    
    // 处理有效数据
    processAction(data);
});
```

#### 2. 避免危险操作

```javascript
// ❌ 不要使用文件系统
const fs = require('fs'); // 会被拒绝

// ❌ 不要执行系统命令
const { exec } = require('child_process'); // 会被拒绝

// ✅ 使用安全的API
const axios = require('axios');
axios.post(API_URL, data);
```

#### 3. 限制权限

- 游戏代码在隔离的Docker容器中运行
- 无法访问宿主机文件系统
- 无法执行系统命令
- 网络访问受限

## 故障排除

### 上传问题

#### 问题1: 文件大小超过限制

**症状**: 上传时显示 "文件大小超过限制"

**解决方案**:
1. 检查文件大小是否超过1MB
2. 优化代码，移除不必要的注释
3. 压缩代码（移除空白和换行）
4. 考虑将大型资源分离

#### 问题2: 代码安全检查失败

**症状**: 上传时显示 "代码安全检查失败"

**解决方案**:
1. 查看详细的错误信息
2. 移除被标记为不安全的代码
3. 参考安全限制章节
4. 使用推荐的替代方案

示例：
```javascript
// ❌ 被拒绝
const fs = require('fs');

// ✅ 使用API替代
const axios = require('axios');
axios.post('/api/save', data);
```

#### 问题3: 语法错误

**症状**: 上传时显示 "JavaScript语法错误"

**解决方案**:
1. 使用代码编辑器检查语法
2. 运行本地语法检查工具
3. 确保使用有效的ES6+语法

```bash
# 本地语法检查
node --check my-game.js
```

### 服务器创建问题

#### 问题1: 容器创建失败

**症状**: 服务器状态显示为 "error"

**解决方案**:
1. 查看服务器日志了解详细错误
2. 检查代码是否有运行时错误
3. 确认所有依赖都已声明
4. 检查系统资源是否充足

```bash
# 检查系统资源
curl http://localhost:8080/system/resources
```

#### 问题2: 端口冲突

**症状**: 创建失败，提示端口已被占用

**解决方案**:
1. 系统会自动分配可用端口
2. 如果持续失败，检查端口范围配置
3. 删除不使用的服务器释放端口

#### 问题3: 达到容器限制

**症状**: 无法创建新服务器，提示 "达到最大容器数"

**解决方案**:
1. 删除不需要的服务器
2. 等待闲置容器自动清理
3. 联系管理员调整限制

```bash
# 查看当前容器数
curl http://localhost:8080/system/stats
```

### 运行时问题

#### 问题1: 服务器无响应

**症状**: 客户端无法连接到游戏服务器

**解决方案**:
1. 检查服务器状态是否为 "running"
2. 查看服务器日志是否有错误
3. 确认端口号正确
4. 检查网络连接

```bash
# 测试服务器连接
curl http://localhost:{port}/
```

#### 问题2: 内存使用过高

**症状**: 资源监控显示内存使用率很高

**解决方案**:
1. 检查代码是否有内存泄漏
2. 优化数据结构
3. 限制缓存大小
4. 定期清理不需要的数据

```javascript
// 推荐：定期清理旧数据
setInterval(() => {
    // 清理超过1小时的数据
    const oneHourAgo = Date.now() - 3600000;
    gameState.players.forEach((player, id) => {
        if (player.lastActive < oneHourAgo) {
            gameState.players.delete(id);
        }
    });
}, 300000); // 每5分钟清理一次
```

#### 问题3: WebSocket连接断开

**症状**: 客户端频繁断开连接

**解决方案**:
1. 实现重连机制
2. 添加心跳检测
3. 处理网络波动

```javascript
// 推荐：实现心跳机制
io.on('connection', (socket) => {
    let heartbeatInterval = setInterval(() => {
        socket.emit('ping');
    }, 25000);
    
    socket.on('pong', () => {
        // 收到心跳响应
    });
    
    socket.on('disconnect', () => {
        clearInterval(heartbeatInterval);
    });
});
```

### 日志分析

#### 查看详细日志

```bash
# 查看工厂服务日志
docker-compose logs -f game-server-factory

# 查看特定容器日志
docker logs {container_id}

# 查看最近100行日志
docker logs --tail 100 {container_id}
```

#### 常见日志消息

**正常消息**:
```
Server started on port 8081
Game initialized
Player connected: socket_abc123
```

**警告消息**:
```
Warning: High memory usage detected
Warning: No heartbeat received for 20 seconds
```

**错误消息**:
```
Error: Failed to connect to matchmaker service
Error: Invalid game action received
Error: WebSocket connection failed
```

## API参考

### 代码上传API

#### POST /upload

上传JavaScript游戏代码并创建服务器。

**请求**:
```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@game.js" \
  -F "name=游戏名称" \
  -F "description=游戏描述" \
  -F "max_players=20"
```

**参数**:
- `file` (必填): JavaScript文件
- `name` (必填): 游戏名称
- `description` (可选): 游戏描述
- `max_players` (可选): 最大玩家数，默认10

**响应**:
```json
{
  "status": "success",
  "server_id": "user123_game1_001",
  "message": "游戏服务器创建成功",
  "server": {
    "server_id": "user123_game1_001",
    "name": "游戏名称",
    "status": "creating",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z"
  }
}
```

### 服务器管理API

#### GET /servers

获取所有游戏服务器列表。

**请求**:
```bash
curl http://localhost:8080/servers
```

**响应**:
```json
[
  {
    "server_id": "user123_game1_001",
    "name": "我的游戏",
    "status": "running",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z"
  }
]
```

#### GET /servers/{server_id}

获取特定服务器的详细信息。

**请求**:
```bash
curl http://localhost:8080/servers/{server_id}
```

**响应**:
```json
{
  "server_id": "user123_game1_001",
  "name": "我的游戏",
  "description": "游戏描述",
  "status": "running",
  "container_id": "abc123",
  "port": 8081,
  "created_at": "2025-12-20T10:00:00Z",
  "updated_at": "2025-12-20T10:30:00Z",
  "resource_usage": {
    "cpu_percent": 15.5,
    "memory_mb": 128,
    "network_io": "1.2MB"
  },
  "logs": ["Server started", "Game initialized"]
}
```

#### POST /servers/{server_id}/stop

停止运行中的游戏服务器。

**请求**:
```bash
curl -X POST http://localhost:8080/servers/{server_id}/stop
```

**响应**:
```json
{
  "status": "success",
  "message": "服务器已停止",
  "server_id": "user123_game1_001"
}
```

#### DELETE /servers/{server_id}

删除游戏服务器。

**请求**:
```bash
curl -X DELETE http://localhost:8080/servers/{server_id}
```

**响应**:
```json
{
  "status": "success",
  "message": "服务器已删除",
  "server_id": "user123_game1_001"
}
```

#### GET /servers/{server_id}/logs

获取服务器日志。

**请求**:
```bash
curl http://localhost:8080/servers/{server_id}/logs
```

**响应**:
```json
{
  "server_id": "user123_game1_001",
  "logs": [
    "[2025-12-20 10:00:00] Server started",
    "[2025-12-20 10:00:01] Game initialized"
  ]
}
```

### 系统监控API

#### GET /health

健康检查。

**请求**:
```bash
curl http://localhost:8080/health
```

**响应**:
```json
{
  "status": "healthy",
  "containers": 5,
  "timestamp": "2025-12-20T10:00:00Z"
}
```

#### GET /system/stats

系统统计信息。

**请求**:
```bash
curl http://localhost:8080/system/stats
```

**响应**:
```json
{
  "game_servers_count": 5,
  "running_containers": 3,
  "stopped_containers": 2,
  "total_memory_mb": 640,
  "total_cpu_percent": 45.5
}
```

#### GET /system/resources

资源管理统计。

**请求**:
```bash
curl http://localhost:8080/system/resources
```

**响应**:
```json
{
  "idle_containers": 2,
  "active_containers": 3,
  "available_ports": 45,
  "memory_usage_percent": 65.5
}
```

---

**版本**: 1.0.0  
**最后更新**: 2025-12-20  
**相关文档**: README.md, USER_GUIDE.md, DEPLOYMENT_GUIDE.md

# AI游戏平台用户指南

## 目录

1. [快速开始](#快速开始)
2. [代码上传和服务器创建](#代码上传和服务器创建)
3. [服务器管理](#服务器管理)
4. [游戏开发指南](#游戏开发指南)
5. [故障排除](#故障排除)
6. [最佳实践](#最佳实践)

## 快速开始

### 系统要求

- **操作系统**: macOS 10.15+, Windows 10+, Ubuntu 18.04+
- **内存**: 至少4GB RAM (推荐8GB)
- **存储**: 至少10GB可用空间
- **网络**: 稳定的互联网连接

### 快速部署

使用Makefile快速部署整个平台:

```bash
# 初始化环境并部署所有服务
make deploy

# 或者部署包含示例游戏服务器
make deploy-example
```

部署完成后，您可以通过以下方式访问服务:

- **游戏服务器工厂**: http://localhost:8080
- **撮合服务**: http://localhost:8000
- **API文档**: http://localhost:8080/docs

## 代码上传和服务器创建

### 使用Flutter客户端上传代码

#### 1. 准备JavaScript游戏代码

创建一个JavaScript文件 (例如 `my-game.js`):

```javascript
// 示例游戏代码
const express = require('express');
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 游戏状态
let gameState = {
    clickCount: 0,
    players: []
};

// WebSocket连接处理
io.on('connection', (socket) => {
    console.log('玩家连接:', socket.id);
    
    // 发送当前游戏状态
    socket.emit('gameState', gameState);
    
    // 处理点击事件
    socket.on('click', () => {
        gameState.clickCount++;
        io.emit('gameState', gameState);
    });
    
    // 处理断开连接
    socket.on('disconnect', () => {
        console.log('玩家断开:', socket.id);
    });
});

// 启动服务器
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
    console.log(`游戏服务器运行在端口 ${PORT}`);
});
```

#### 2. 使用Flutter客户端上传

1. **启动Flutter客户端**:
   ```bash
   cd mobile_app/universal_game_client
   flutter run -d macos
   ```

2. **导航到上传页面**:
   - 点击主界面的 "Upload Code" 按钮
   - 或使用导航菜单选择 "Upload Game Code"

3. **选择文件**:
   - 点击文件选择区域
   - 选择您的JavaScript文件 (`.js`)
   - 文件大小限制: 1MB

4. **填写信息**:
   - **游戏名称**: 为您的游戏输入一个名称 (必填)
   - **描述**: 添加游戏描述 (可选)
   - **最大玩家数**: 设置最大玩家数 (默认10)

5. **上传**:
   - 点击 "Upload & Create Server" 按钮
   - 等待上传和容器创建完成
   - 成功后会自动跳转到服务器列表

### 使用API上传代码

您也可以直接使用API上传代码:

```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.js" \
  -F "name=我的游戏" \
  -F "description=一个简单的点击游戏" \
  -F "max_players=20"
```

### 代码安全检查

系统会自动对上传的代码进行安全检查:

- **语法验证**: 检查JavaScript语法错误
- **安全扫描**: 检测潜在的恶意操作
  - 文件系统访问 (`fs`, `path`)
  - 进程操作 (`child_process`, `process.exit`)
  - 网络请求 (`http.request`, `https.request`)
  - 危险函数 (`eval`, `Function`)

如果代码存在安全问题，上传会被拒绝并返回详细的错误信息。

## 服务器管理

### 查看服务器列表

#### 使用Flutter客户端

1. 在主界面点击 "My Servers" 标签
2. 查看所有您创建的游戏服务器
3. 每个服务器显示:
   - 服务器名称和状态
   - 端口号
   - 创建时间
   - 状态指示器 (运行中/已停止/错误)

#### 使用API

```bash
# 获取服务器列表
curl http://localhost:8080/servers

# 获取特定服务器详情
curl http://localhost:8080/servers/{server_id}
```

### 查看服务器详情

#### 使用Flutter客户端

1. 在服务器列表中点击任意服务器
2. 查看详细信息:
   - **状态信息**: 当前运行状态
   - **服务器信息**: ID、端口、容器ID、创建时间
   - **资源使用**: CPU、内存、网络I/O
   - **日志**: 实时服务器日志

3. 可用操作:
   - **刷新**: 更新服务器状态和资源信息
   - **停止**: 停止运行中的服务器
   - **删除**: 删除服务器并清理资源

#### 使用API

```bash
# 获取服务器详情
curl http://localhost:8080/servers/{server_id}

# 获取服务器日志
curl http://localhost:8080/servers/{server_id}/logs
```

### 停止服务器

#### 使用Flutter客户端

1. 进入服务器详情页面
2. 点击 "Stop" 按钮
3. 确认操作
4. 等待服务器停止

#### 使用API

```bash
curl -X POST http://localhost:8080/servers/{server_id}/stop
```

### 删除服务器

#### 使用Flutter客户端

1. 进入服务器详情页面
2. 点击 "Delete" 按钮
3. 确认删除操作 (此操作不可撤销)
4. 服务器和相关资源将被清理

#### 使用API

```bash
curl -X DELETE http://localhost:8080/servers/{server_id}
```

### 监控资源使用

#### 查看系统统计

```bash
# 获取系统统计信息
curl http://localhost:8080/system/stats

# 获取资源管理统计
curl http://localhost:8080/system/resources

# 获取所有容器状态
curl http://localhost:8080/containers/status
```

#### 查看闲置容器

```bash
# 获取闲置容器列表
curl http://localhost:8080/system/idle-containers
```

系统会自动管理闲置容器:
- 默认闲置超时: 30分钟
- 自动停止长时间无活动的容器
- 定期清理已停止的容器

## 游戏开发指南

### 游戏代码结构

您的JavaScript游戏代码应该包含以下基本结构:

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
    // 您的游戏状态
};

// 4. 处理WebSocket连接
io.on('connection', (socket) => {
    // 连接处理逻辑
    
    socket.on('gameAction', (data) => {
        // 游戏操作处理
    });
    
    socket.on('disconnect', () => {
        // 断开连接处理
    });
});

// 5. 启动服务器
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
    console.log(`游戏服务器运行在端口 ${PORT}`);
});
```

### 自动注册到撮合服务

游戏服务器会自动注册到撮合服务。您可以在代码中配置注册信息:

```javascript
// 从环境变量获取撮合服务URL
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;

// 注册到撮合服务
async function registerToMatchmaker() {
    try {
        const response = await fetch(`${MATCHMAKER_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ip: 'localhost',
                port: PORT,
                name: ROOM_NAME,
                max_players: MAX_PLAYERS,
                current_players: 0,
                metadata: {}
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            console.log('注册成功:', data.server_id);
            return data.server_id;
        }
    } catch (error) {
        console.error('注册失败:', error);
    }
}
```

### 心跳机制

保持与撮合服务的连接:

```javascript
// 定期发送心跳
function startHeartbeat(serverId) {
    setInterval(async () => {
        try {
            await fetch(`${MATCHMAKER_URL}/heartbeat/${serverId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    current_players: getCurrentPlayerCount()
                })
            });
        } catch (error) {
            console.error('心跳失败:', error);
        }
    }, 25000); // 每25秒发送一次
}
```

### 游戏状态管理

推荐的游戏状态管理模式:

```javascript
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
    
    updateGameData(data) {
        this.gameData = { ...this.gameData, ...data };
    }
    
    getState() {
        return {
            players: Array.from(this.players.values()),
            gameData: this.gameData
        };
    }
}

const gameState = new GameState();
```

### 客户端连接

客户端可以通过WebSocket连接到您的游戏服务器:

```javascript
// 客户端代码示例
const socket = io('http://localhost:8081'); // 使用您的服务器端口

socket.on('connect', () => {
    console.log('已连接到游戏服务器');
});

socket.on('gameState', (state) => {
    console.log('收到游戏状态:', state);
    // 更新UI
});

// 发送游戏操作
socket.emit('gameAction', { type: 'move', data: { x: 10, y: 20 } });
```

## 故障排除

### 常见问题

#### 1. 代码上传失败

**问题**: 上传时显示 "文件大小超过限制"

**解决方案**:
- 检查文件大小是否超过1MB
- 优化代码，移除不必要的注释和空白
- 考虑将大型资源文件分离

**问题**: 上传时显示 "代码安全检查失败"

**解决方案**:
- 查看详细的错误信息
- 移除被标记为不安全的代码
- 避免使用文件系统操作、进程操作等危险功能

#### 2. 服务器创建失败

**问题**: 服务器状态显示为 "error"

**解决方案**:
- 查看服务器日志了解详细错误
- 检查代码语法是否正确
- 确保所有必需的npm包都已声明
- 检查系统资源是否充足

**问题**: 容器无法启动

**解决方案**:
```bash
# 检查Docker状态
docker ps -a

# 查看容器日志
docker logs <container_id>

# 检查系统资源
curl http://localhost:8080/system/resources
```

#### 3. 网络连接问题

**问题**: Flutter客户端无法连接到服务器

**解决方案**:
- 检查服务器是否正在运行:
  ```bash
  curl http://localhost:8080/health
  ```
- 检查防火墙设置
- 确认端口没有被占用:
  ```bash
  lsof -i :8080
  ```

#### 4. 资源限制

**问题**: 无法创建新服务器，提示 "资源限制"

**解决方案**:
- 检查当前容器数量:
  ```bash
  curl http://localhost:8080/system/stats
  ```
- 删除不需要的服务器
- 等待闲置容器自动清理
- 调整配置文件中的 `MAX_CONTAINERS` 参数

### 日志查看

#### 查看服务日志

```bash
# 游戏服务器工厂日志
docker-compose logs -f game-server-factory

# 撮合服务日志
docker-compose logs -f matchmaker

# 特定游戏服务器日志
docker logs <container_id>
```

#### 查看系统日志

```bash
# 查看日志文件
tail -f game_server_factory.log
tail -f matchmaker_service.log
```

### 健康检查

```bash
# 快速健康检查
make health-quick

# 综合健康检查
make health

# 生成健康报告
./scripts/health-check.sh report
```

## 最佳实践

### 代码开发

1. **模块化设计**: 将游戏逻辑分离到不同的模块
2. **错误处理**: 添加适当的错误处理和日志记录
3. **状态同步**: 确保游戏状态在所有客户端之间正确同步
4. **性能优化**: 避免在主循环中进行重计算

### 资源管理

1. **及时清理**: 删除不再使用的服务器
2. **监控资源**: 定期检查资源使用情况
3. **合理配置**: 根据需求调整容器资源限制

### 安全性

1. **输入验证**: 验证所有客户端输入
2. **避免危险操作**: 不要使用文件系统、进程操作等
3. **限制权限**: 游戏代码在隔离的容器中运行

### 测试

1. **本地测试**: 在上传前本地测试游戏代码
2. **渐进式部署**: 先创建测试服务器，验证后再正式部署
3. **监控日志**: 部署后密切关注服务器日志

### 性能优化

1. **减少网络请求**: 批量处理游戏状态更新
2. **优化数据结构**: 使用高效的数据结构存储游戏状态
3. **限制广播频率**: 避免过于频繁的状态广播

## 高级功能

### 自定义环境变量

在创建服务器时，可以通过环境变量配置游戏:

```javascript
// 在游戏代码中读取环境变量
const GAME_MODE = process.env.GAME_MODE || 'normal';
const DIFFICULTY = process.env.DIFFICULTY || 'medium';
const ENABLE_CHAT = process.env.ENABLE_CHAT === 'true';
```

### 持久化存储

如果需要持久化游戏数据，可以使用容器卷:

```javascript
// 注意: 文件系统操作会被安全检查拦截
// 建议使用外部数据库或API进行数据持久化
```

### 多房间支持

在单个服务器中支持多个游戏房间:

```javascript
const rooms = new Map();

io.on('connection', (socket) => {
    socket.on('joinRoom', (roomId) => {
        socket.join(roomId);
        
        if (!rooms.has(roomId)) {
            rooms.set(roomId, new GameState());
        }
        
        const room = rooms.get(roomId);
        socket.emit('roomState', room.getState());
    });
    
    socket.on('gameAction', (data) => {
        const roomId = Array.from(socket.rooms)[1]; // 获取房间ID
        const room = rooms.get(roomId);
        
        // 处理游戏操作
        room.updateGameData(data);
        
        // 广播到房间内所有客户端
        io.to(roomId).emit('roomState', room.getState());
    });
});
```

## 获取帮助

### 文档资源

- **API文档**: http://localhost:8080/docs
- **代码上传和服务器管理指南**: 查看 `CODE_UPLOAD_SERVER_MANAGEMENT_GUIDE.md` - 完整的代码上传和服务器管理教程
- **部署指南**: 查看 `DEPLOYMENT_GUIDE.md`
- **项目结构**: 查看 `PROJECT_STRUCTURE.md`

### 系统信息

```bash
# 查看系统集成状态
curl http://localhost:8080/system/integration-status

# 运行端到端测试
curl http://localhost:8080/system/end-to-end-test

# 查看API端点列表
curl http://localhost:8080/api/endpoints
```

### 社区支持

如果遇到问题:

1. 查看日志文件获取详细错误信息
2. 运行健康检查诊断系统状态
3. 查阅API文档了解接口使用方法
4. 提交Issue到项目仓库

---

**版本**: 1.0.0  
**最后更新**: 2025-12-20

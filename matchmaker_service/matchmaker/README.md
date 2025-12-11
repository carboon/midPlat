# 撮合服务 (Matchmaker Service)

游戏撮合服务，用于管理和发现活跃的游戏服务器。

## 功能特性

- ✅ 游戏服务器注册与心跳管理
- ✅ 自动清理超时服务器（默认 30 秒无心跳则移除）
- ✅ 实时查询活跃房间列表
- ✅ RESTful API 接口
- ✅ Docker 容器化部署
- ✅ CORS 支持，方便前端调用
- ✅ 环境变量配置支持

## API 接口

### 1. 服务状态
```bash
GET /
```
返回服务基本信息和当前活跃服务器数量。

### 2. 注册游戏服务器
```bash
POST /register
Content-Type: application/json

{
  "ip": "192.168.1.100",
  "port": 8080,
  "name": "我的派对游戏",
  "max_players": 20,
  "current_players": 0,
  "metadata": {
    "game_mode": "party",
    "version": "1.0.0"
  }
}
```

响应：
```json
{
  "status": "success",
  "server_id": "192.168.1.100:8080",
  "message": "Server registered successfully"
}
```

### 3. 发送心跳
```bash
POST /heartbeat/{server_id}?current_players=5
```

保持服务器在线状态，建议每 10-15 秒发送一次。

### 4. 获取所有活跃服务器
```bash
GET /servers
```

响应：
```json
[
  {
    "server_id": "192.168.1.100:8080",
    "ip": "192.168.1.100",
    "port": 8080,
    "name": "我的派对游戏",
    "max_players": 20,
    "current_players": 5,
    "metadata": {},
    "last_heartbeat": "2025-12-08T12:34:56",
    "uptime": 120
  }
]
```

### 5. 获取特定服务器信息
```bash
GET /servers/{server_id}
```

### 6. 注销服务器
```bash
DELETE /servers/{server_id}
```

### 7. 健康检查
```bash
GET /health
```

## 配置文件

服务支持通过 `.env` 文件进行配置：

```bash
# .env 配置文件
PYTHONUNBUFFERED=1
HOST=0.0.0.0
PORT=8000
HEARTBEAT_TIMEOUT=30
CLEANUP_INTERVAL=10
```

## 快速启动

### 方式一：Docker Compose（推荐）
```bash
cd matchmaker
docker-compose up -d
```

服务将在 http://localhost:8000 启动。

### 方式二：本地运行
```bash
cd matchmaker
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python main.py
```

## 测试示例

### 1. 注册一个游戏服务器
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "port": 8080,
    "name": "点击计数游戏",
    "max_players": 10,
    "current_players": 0
  }'
```

### 2. 查看所有活跃服务器
```bash
curl http://localhost:8000/servers
```

### 3. 发送心跳（模拟游戏服务器）
```bash
curl -X POST "http://localhost:8000/heartbeat/192.168.1.100:8080?current_players=3"
```

### 4. 测试自动清理
等待 30 秒后再次查询服务器列表，如果没有心跳，服务器会自动被清理。

## 游戏服务器集成示例

在你的 Node.js 游戏服务器中添加以下代码：

```javascript
const axios = require('axios');

const MATCHMAKER_URL = 'http://localhost:8000';
const SERVER_IP = '192.168.1.100';
const SERVER_PORT = 8080;
const GAME_NAME = '我的派对游戏';

let serverId = null;
let currentPlayers = 0;

async function registerServer() {
  try {
    const response = await axios.post(`${MATCHMAKER_URL}/register`, {
      ip: SERVER_IP,
      port: SERVER_PORT,
      name: GAME_NAME,
      max_players: 20,
      current_players: currentPlayers
    });
    serverId = response.data.server_id;
    console.log('✅ 已注册到撮合服务:', serverId);
  } catch (error) {
    console.error('❌ 注册失败:', error.message);
  }
}

async function sendHeartbeat() {
  if (!serverId) return;
  
  try {
    await axios.post(`${MATCHMAKER_URL}/heartbeat/${serverId}?current_players=${currentPlayers}`);
    console.log('💓 心跳发送成功');
  } catch (error) {
    console.error('❌ 心跳失败:', error.message);
    await registerServer();
  }
}

registerServer();

setInterval(sendHeartbeat, 15000);
```

## 配置说明

- **心跳超时时间**：默认 30 秒，可通过 `HEARTBEAT_TIMEOUT` 环境变量修改
- **清理间隔**：默认 10 秒，可通过 `CLEANUP_INTERVAL` 环境变量修改
- **端口**：默认 8000，可通过 `PORT` 环境变量修改
- **主机**：默认 0.0.0.0，可通过 `HOST` 环境变量修改

## 架构说明

- **内存存储**：MVP 阶段使用内存存储，重启后数据会丢失
- **单实例**：当前设计为单实例运行，适合小规模部署
- **未来扩展**：可以接入 Redis 实现分布式存储和多实例部署

## 日志查看

```bash
docker-compose logs -f matchmaker
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
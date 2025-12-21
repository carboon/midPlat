# AI游戏平台 API参考文档

## 概述

本文档提供AI游戏平台所有API端点的完整参考，包括游戏服务器工厂、撮合服务和游戏服务器的所有接口。

## 基础信息

### 服务端点

- **游戏服务器工厂**: `http://localhost:8080`
- **撮合服务**: `http://localhost:8000`
- **游戏服务器**: `http://localhost:{动态端口}`

### 认证

当前版本不需要认证。未来版本将支持JWT令牌认证。

### 响应格式

所有API响应使用JSON格式。

**成功响应**:
```json
{
  "status": "success",
  "data": { ... }
}
```

**错误响应**:
```json
{
  "error": {
    "code": 400,
    "message": "错误描述",
    "timestamp": "2025-12-20T10:00:00Z",
    "path": "/api/endpoint",
    "details": { ... }
  }
}
```

### HTTP状态码

- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

## 游戏服务器工厂 API

### 服务信息

#### GET /

获取服务基本信息。

**请求示例**:
```bash
curl http://localhost:8080/
```

**响应示例**:
```json
{
  "service": "Game Server Factory",
  "version": "1.0.0",
  "description": "游戏服务器工厂 - JavaScript代码上传和动态游戏服务器创建",
  "environment": "development"
}
```

### 健康检查

#### GET /health

检查服务健康状态。

**请求示例**:
```bash
curl http://localhost:8080/health
```

**响应示例**:
```json
{
  "status": "healthy",
  "containers": 5,
  "timestamp": "2025-12-20T10:00:00Z",
  "components": {
    "docker_manager": "healthy",
    "resource_manager": "healthy",
    "matchmaker_service": "healthy"
  }
}
```

### 代码上传

#### POST /upload

上传JavaScript游戏代码并创建服务器。

**请求参数**:
- `file` (必填, multipart/form-data): JavaScript文件
- `name` (必填, string): 游戏名称
- `description` (可选, string): 游戏描述
- `max_players` (可选, integer): 最大玩家数，默认10

**请求示例**:
```bash
curl -X POST http://localhost:8080/upload \
  -F "file=@my-game.js" \
  -F "name=我的游戏" \
  -F "description=一个简单的点击游戏" \
  -F "max_players=20"
```

**响应示例**:
```json
{
  "status": "success",
  "server_id": "user123_mygame_001",
  "message": "游戏服务器创建成功",
  "server": {
    "server_id": "user123_mygame_001",
    "name": "我的游戏",
    "description": "一个简单的点击游戏",
    "status": "creating",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z"
  }
}
```

**错误响应**:
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

### 服务器列表

#### GET /servers

获取所有游戏服务器列表。

**请求示例**:
```bash
curl http://localhost:8080/servers
```

**响应示例**:
```json
[
  {
    "server_id": "user123_game1_001",
    "name": "我的第一个游戏",
    "description": "点击计数游戏",
    "status": "running",
    "port": 8081,
    "created_at": "2025-12-20T10:00:00Z",
    "updated_at": "2025-12-20T10:30:00Z"
  },
  {
    "server_id": "user123_game2_002",
    "name": "我的第二个游戏",
    "description": "聊天室游戏",
    "status": "stopped",
    "port": 8082,
    "created_at": "2025-12-20T11:00:00Z",
    "updated_at": "2025-12-20T11:30:00Z"
  }
]
```

### 服务器详情

#### GET /servers/{server_id}

获取特定服务器的详细信息。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**请求示例**:
```bash
curl http://localhost:8080/servers/user123_game1_001
```

**响应示例**:
```json
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
    "[2025-12-20 10:00:00] Server started on port 8081",
    "[2025-12-20 10:00:01] Game initialized",
    "[2025-12-20 10:00:05] Player connected: socket_abc123"
  ]
}
```

**错误响应**:
```json
{
  "error": {
    "code": 404,
    "message": "服务器不存在",
    "server_id": "invalid_id"
  }
}
```

### 停止服务器

#### POST /servers/{server_id}/stop

停止运行中的游戏服务器。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**请求示例**:
```bash
curl -X POST http://localhost:8080/servers/user123_game1_001/stop
```

**响应示例**:
```json
{
  "status": "success",
  "message": "服务器已停止",
  "server_id": "user123_game1_001"
}
```

### 删除服务器

#### DELETE /servers/{server_id}

删除游戏服务器。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**请求示例**:
```bash
curl -X DELETE http://localhost:8080/servers/user123_game1_001
```

**响应示例**:
```json
{
  "status": "success",
  "message": "服务器已删除",
  "server_id": "user123_game1_001"
}
```

### 服务器日志

#### GET /servers/{server_id}/logs

获取服务器日志。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**查询参数**:
- `lines` (可选, integer): 返回的日志行数，默认100

**请求示例**:
```bash
curl http://localhost:8080/servers/user123_game1_001/logs?lines=50
```

**响应示例**:
```json
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

### 系统监控

#### GET /system/stats

获取系统统计信息。

**请求示例**:
```bash
curl http://localhost:8080/system/stats
```

**响应示例**:
```json
{
  "game_servers_count": 5,
  "running_containers": 3,
  "stopped_containers": 2,
  "total_memory_mb": 640,
  "total_cpu_percent": 45.5,
  "available_ports": 45
}
```

#### GET /system/resources

获取资源管理统计。

**请求示例**:
```bash
curl http://localhost:8080/system/resources
```

**响应示例**:
```json
{
  "idle_containers": 2,
  "active_containers": 3,
  "available_ports": 45,
  "memory_usage_percent": 65.5,
  "cpu_usage_percent": 45.5,
  "max_containers": 50,
  "current_containers": 5
}
```

#### GET /system/idle-containers

获取闲置容器列表。

**请求示例**:
```bash
curl http://localhost:8080/system/idle-containers
```

**响应示例**:
```json
{
  "idle_containers": [
    {
      "server_id": "user123_game1_001",
      "idle_time_seconds": 1800,
      "last_activity": "2025-12-20T09:30:00Z"
    }
  ]
}
```

#### GET /containers/status

获取所有容器状态。

**请求示例**:
```bash
curl http://localhost:8080/containers/status
```

**响应示例**:
```json
{
  "containers": [
    {
      "container_id": "abc123",
      "server_id": "user123_game1_001",
      "status": "running",
      "uptime_seconds": 3600,
      "resource_usage": {
        "cpu_percent": 15.5,
        "memory_mb": 128
      }
    }
  ]
}
```

#### GET /system/integration-status

获取系统集成状态。

**请求示例**:
```bash
curl http://localhost:8080/system/integration-status
```

**响应示例**:
```json
{
  "status": "healthy",
  "components": {
    "docker_manager": {
      "status": "healthy",
      "containers": 5
    },
    "resource_manager": {
      "status": "healthy",
      "idle_containers": 2
    },
    "matchmaker_service": {
      "status": "healthy",
      "url": "http://matchmaker:8000"
    }
  }
}
```

## 撮合服务 API

### 服务信息

#### GET /

获取服务基本信息。

**请求示例**:
```bash
curl http://localhost:8000/
```

**响应示例**:
```json
{
  "service": "Game Matchmaker",
  "version": "1.0.0",
  "status": "running",
  "active_servers": 3
}
```

### 健康检查

#### GET /health

检查服务健康状态。

**请求示例**:
```bash
curl http://localhost:8000/health
```

**响应示例**:
```json
{
  "status": "healthy"
}
```

### 服务器注册

#### POST /register

注册游戏服务器到撮合服务。

**请求体**:
```json
{
  "ip": "192.168.1.100",
  "port": 8080,
  "name": "我的游戏房间",
  "max_players": 20,
  "current_players": 0,
  "metadata": {
    "game_mode": "party",
    "version": "1.0.0"
  }
}
```

**请求示例**:
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.100",
    "port": 8080,
    "name": "我的游戏房间",
    "max_players": 20,
    "current_players": 0
  }'
```

**响应示例**:
```json
{
  "status": "success",
  "server_id": "192.168.1.100:8080",
  "message": "Server registered successfully"
}
```

### 心跳更新

#### POST /heartbeat/{server_id}

发送心跳保持服务器在线状态。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**查询参数**:
- `current_players` (可选, integer): 当前玩家数

**请求示例**:
```bash
curl -X POST "http://localhost:8000/heartbeat/192.168.1.100:8080?current_players=5"
```

**响应示例**:
```json
{
  "status": "success",
  "message": "Heartbeat received"
}
```

### 服务器列表

#### GET /servers

获取所有活跃游戏服务器列表。

**请求示例**:
```bash
curl http://localhost:8000/servers
```

**响应示例**:
```json
[
  {
    "server_id": "192.168.1.100:8080",
    "ip": "192.168.1.100",
    "port": 8080,
    "name": "我的游戏房间",
    "max_players": 20,
    "current_players": 5,
    "metadata": {
      "game_mode": "party"
    },
    "last_heartbeat": "2025-12-20T10:30:00Z",
    "uptime": 1800
  }
]
```

### 服务器详情

#### GET /servers/{server_id}

获取特定服务器信息。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**请求示例**:
```bash
curl http://localhost:8000/servers/192.168.1.100:8080
```

**响应示例**:
```json
{
  "server_id": "192.168.1.100:8080",
  "ip": "192.168.1.100",
  "port": 8080,
  "name": "我的游戏房间",
  "max_players": 20,
  "current_players": 5,
  "metadata": {},
  "last_heartbeat": "2025-12-20T10:30:00Z",
  "uptime": 1800
}
```

### 注销服务器

#### DELETE /servers/{server_id}

从撮合服务注销游戏服务器。

**路径参数**:
- `server_id` (必填): 服务器唯一标识

**请求示例**:
```bash
curl -X DELETE http://localhost:8000/servers/192.168.1.100:8080
```

**响应示例**:
```json
{
  "status": "success",
  "message": "Server unregistered successfully"
}
```

## 游戏服务器 API

### WebSocket连接

游戏服务器使用Socket.IO提供WebSocket实时通信。

#### 连接

```javascript
const socket = io('http://localhost:8081');

socket.on('connect', () => {
    console.log('已连接到游戏服务器');
});
```

#### 事件

**connection**: 客户端连接
```javascript
io.on('connection', (socket) => {
    console.log('玩家连接:', socket.id);
});
```

**gameState**: 游戏状态更新
```javascript
socket.on('gameState', (state) => {
    console.log('游戏状态:', state);
});
```

**gameAction**: 游戏操作
```javascript
socket.emit('gameAction', {
    type: 'click',
    data: { x: 100, y: 200 }
});
```

**disconnect**: 客户端断开
```javascript
socket.on('disconnect', () => {
    console.log('玩家断开');
});
```

### 静态文件

#### GET /

提供游戏前端页面。

**请求示例**:
```bash
curl http://localhost:8081/
```

**响应**: HTML页面内容

## 数据模型

### GameServerInstance

游戏服务器实例模型。

```typescript
interface GameServerInstance {
  server_id: string;        // 服务器唯一标识
  name: string;             // 游戏名称
  description: string;      // 游戏描述
  status: string;           // 状态: creating, running, stopped, error
  container_id: string;     // Docker容器ID
  port: number;             // 服务器端口
  created_at: string;       // 创建时间 (ISO 8601)
  updated_at: string;       // 更新时间 (ISO 8601)
  resource_usage: {         // 资源使用情况
    cpu_percent: number;    // CPU使用率
    memory_mb: number;      // 内存使用量(MB)
    network_io: string;     // 网络I/O
  };
  logs: string[];           // 服务器日志
}
```

### GameServerInfo

撮合服务中的游戏服务器信息模型。

```typescript
interface GameServerInfo {
  server_id: string;        // 服务器唯一标识
  ip: string;               // 服务器IP地址
  port: number;             // 服务器端口
  name: string;             // 房间名称
  max_players: number;      // 最大玩家数
  current_players: number;  // 当前玩家数
  metadata: object;         // 扩展元数据
  last_heartbeat: string;   // 最后心跳时间 (ISO 8601)
  uptime: number;           // 运行时长(秒)
}
```

### ErrorResponse

错误响应模型。

```typescript
interface ErrorResponse {
  error: {
    code: number;           // HTTP状态码
    message: string;        // 错误消息
    timestamp: string;      // 时间戳 (ISO 8601)
    path: string;           // 请求路径
    details?: object;       // 详细信息
  };
}
```

## 错误代码

### 游戏服务器工厂

- `400`: 请求参数错误
  - 文件格式不支持
  - 文件大小超过限制
  - 代码安全检查失败
  - 语法错误

- `404`: 资源不存在
  - 服务器ID不存在

- `500`: 服务器内部错误
  - Docker容器创建失败
  - 系统资源不足

### 撮合服务

- `400`: 请求参数错误
  - 缺少必需参数
  - 参数格式错误

- `404`: 资源不存在
  - 服务器ID不存在

- `500`: 服务器内部错误
  - 内部处理错误

## 速率限制

当前版本没有速率限制。未来版本将实施以下限制：

- 代码上传: 每小时10次
- API请求: 每分钟100次
- WebSocket连接: 每IP 10个并发连接

## 版本控制

API版本通过URL路径指定（未来版本）：

```
http://localhost:8080/v1/servers
http://localhost:8080/v2/servers
```

当前版本为v1，默认不需要在URL中指定版本号。

## 交互式文档

### Swagger UI

访问交互式API文档：

- 游戏服务器工厂: http://localhost:8080/docs
- 撮合服务: http://localhost:8000/docs

### ReDoc

访问ReDoc格式文档：

- 游戏服务器工厂: http://localhost:8080/redoc
- 撮合服务: http://localhost:8000/redoc

## 示例代码

### Python

```python
import requests

# 上传代码
with open('my-game.js', 'rb') as f:
    files = {'file': f}
    data = {
        'name': '我的游戏',
        'description': '游戏描述',
        'max_players': 20
    }
    response = requests.post('http://localhost:8080/upload', files=files, data=data)
    print(response.json())

# 获取服务器列表
response = requests.get('http://localhost:8080/servers')
servers = response.json()
print(servers)

# 停止服务器
server_id = servers[0]['server_id']
response = requests.post(f'http://localhost:8080/servers/{server_id}/stop')
print(response.json())
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

// 上传代码
async function uploadCode() {
    const form = new FormData();
    form.append('file', fs.createReadStream('my-game.js'));
    form.append('name', '我的游戏');
    form.append('description', '游戏描述');
    form.append('max_players', '20');
    
    const response = await axios.post('http://localhost:8080/upload', form, {
        headers: form.getHeaders()
    });
    console.log(response.data);
}

// 获取服务器列表
async function getServers() {
    const response = await axios.get('http://localhost:8080/servers');
    console.log(response.data);
}

// 停止服务器
async function stopServer(serverId) {
    const response = await axios.post(`http://localhost:8080/servers/${serverId}/stop`);
    console.log(response.data);
}
```

### Dart/Flutter

```dart
import 'package:http/http.dart' as http;
import 'dart:convert';

// 上传代码
Future<void> uploadCode() async {
  var request = http.MultipartRequest(
    'POST',
    Uri.parse('http://localhost:8080/upload'),
  );
  
  request.files.add(await http.MultipartFile.fromPath('file', 'my-game.js'));
  request.fields['name'] = '我的游戏';
  request.fields['description'] = '游戏描述';
  request.fields['max_players'] = '20';
  
  var response = await request.send();
  var responseData = await response.stream.bytesToString();
  print(json.decode(responseData));
}

// 获取服务器列表
Future<void> getServers() async {
  var response = await http.get(Uri.parse('http://localhost:8080/servers'));
  print(json.decode(response.body));
}

// 停止服务器
Future<void> stopServer(String serverId) async {
  var response = await http.post(
    Uri.parse('http://localhost:8080/servers/$serverId/stop'),
  );
  print(json.decode(response.body));
}
```

---

**版本**: 1.0.0  
**最后更新**: 2025-12-20  
**相关文档**: README.md, USER_GUIDE.md, CODE_UPLOAD_SERVER_MANAGEMENT_GUIDE.md

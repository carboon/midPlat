# AI游戏平台 - 设计文档

## 概述

AI游戏平台是一个动态分布式多人游戏基础设施系统，采用微服务架构设计，支持AI生成游戏的代码上传、自动部署、发现和实时游玩。系统由四个核心组件组成：游戏服务器工厂(Game Server Factory)、撮合服务(Matchmaker Service)、游戏服务器模板(Game Server Template)和通用客户端(Universal Client)，通过标准化的API和协议实现从代码到游戏的完整自动化流程。

## 架构

### 系统架构图

```
┌─────────────────┐                     ┌─────────────────┐
│  Universal      │◄──────────────────►│  Matchmaker     │
│  Client         │   Room Discovery    │  Service        │
│  (Flutter)      │   & Game Connection │  (Python/FastAPI)│
└─────────────────┘                     └─────────────────┘
         │                                       ▲
         │ Code Upload &                         │ HTTP Registration
         │ Lifecycle Mgmt                        │ & Heartbeat
         ▼                                       │
┌─────────────────┐                             │
│  Game Server    │─────────────────────────────┘
│  Factory        │
│  (Python/FastAPI)│
└─────────────────┘
         │ Docker Container
         │ Management
         ▼
┌─────────────────┐    WebSocket     ┌─────────────────┐    WebSocket     ┌─────────────────┐
│  Game Server    │◄────────────────│  Game Server    │◄────────────────│  Game Server    │
│  Instance 1     │    Connection    │  Instance 2     │    Connection    │  Instance N     │
│  (Docker)       │    (from Client) │  (Docker)       │    (from Client) │  (Docker)       │
└─────────────────┘                  └─────────────────┘                  └─────────────────┘
         ▲                                    ▲                                    ▲
         │                                    │                                    │
         └────────────────────────────────────┼────────────────────────────────────┘
                    WebSocket Connections from Universal Client
```

**连接说明:**
1. **Client ↔ Matchmaker**: 房间发现和列表获取（保持原有功能）
2. **Client ↔ Game Server Factory**: 代码上传和服务器生命周期管理（新功能）
3. **Client ↔ Game Servers**: WebSocket游戏连接（保持原有功能）
4. **Game Server Factory ↔ Game Servers**: Docker容器管理（新功能）
5. **Game Servers ↔ Matchmaker**: 自动注册和心跳（保持原有功能）

### 技术栈

- **游戏服务器工厂**: Python 3.8+, FastAPI, Docker SDK, AST代码分析
- **撮合服务**: Python 3.8+, FastAPI, Uvicorn, Pydantic
- **游戏服务器**: Node.js, Express, Socket.IO, WebSocket
- **客户端**: Flutter, Dart, Provider状态管理, HTTP客户端, 文件上传
- **容器化**: Docker, Docker Compose, 动态容器管理
- **通信协议**: HTTP/REST, WebSocket, JSON, 文件上传

## 组件和接口

### 1. 游戏服务器工厂 (Game Server Factory)

#### 核心功能
- JavaScript代码接收和验证
- 代码安全分析和语法检查
- Docker容器动态创建和管理
- 游戏服务器生命周期管理

#### 主要接口

```python
# 代码上传
POST /upload
Content-Type: multipart/form-data
{
    "file": "JavaScript文件",
    "name": "游戏名称",
    "description": "游戏描述"
}

# 获取用户的游戏服务器列表
GET /servers
Response: List[GameServerInstance]

# 获取特定服务器详情
GET /servers/{server_id}
Response: GameServerInstance

# 停止游戏服务器
POST /servers/{server_id}/stop

# 删除游戏服务器
DELETE /servers/{server_id}

# 获取服务器日志
GET /servers/{server_id}/logs

# 健康检查
GET /health
Response: {"status": "healthy", "containers": count}
```

#### 数据模型

```python
class GameServerInstance:
    server_id: str
    name: str
    description: str
    status: str  # "creating", "running", "stopped", "error"
    container_id: str
    port: int
    created_at: str
    updated_at: str
    resource_usage: Dict
    logs: List[str]
```

### 2. 撮合服务 (Matchmaker Service)

#### 核心功能
- 游戏服务器注册和发现
- 服务器状态管理和心跳监控
- RESTful API提供
- 自动清理过期服务器

#### 主要接口

```python
# 服务器注册
POST /register
{
    "ip": "string",
    "port": "integer",
    "name": "string", 
    "max_players": "integer",
    "current_players": "integer",
    "metadata": "object"
}

# 获取服务器列表
GET /servers
Response: List[GameServerInfo]

# 心跳更新
POST /heartbeat/{server_id}
{
    "current_players": "integer"
}

# 健康检查
GET /health
Response: {"status": "healthy"}
```

#### 数据模型

```python
class GameServerInfo:
    server_id: str
    ip: str
    port: int
    name: str
    max_players: int
    current_players: int
    metadata: Dict
    last_heartbeat: str
    uptime: int
```

### 3. 游戏服务器模板 (Game Server Template)

#### 核心功能
- WebSocket实时通信
- 游戏状态管理
- 自动注册到撮合服务
- 定期心跳上报

#### 主要接口

```javascript
// WebSocket事件
socket.on('connection', callback)
socket.on('click', callback)
socket.on('disconnect', callback)

// HTTP静态文件服务
GET / -> index.html

// 内部方法
sendHeartbeat() // 定期向撮合服务发送心跳
```

#### 游戏状态模型

```javascript
gameState = {
    clickCount: number,
    // 可扩展其他游戏状态
}
```

### 4. 通用客户端 (Universal Client)

#### 核心功能
- JavaScript代码文件上传
- 游戏服务器生命周期管理
- 房间列表浏览
- WebSocket游戏连接
- 跨平台UI适配

#### 主要组件

```dart
// 数据模型
class GameServerInstance {
    String serverId, name, description, status;
    String containerId;
    int port;
    DateTime createdAt, updatedAt;
    Map<String, dynamic> resourceUsage;
}

class Room {
    String id, name, ip;
    int port, playerCount, maxPlayers;
    Map<String, dynamic> metadata;
    String lastHeartbeat;
    int uptime;
}

// 服务层
class GameServerFactoryService {
    static Future<String> uploadGameCode(File jsFile, String name, String description)
    static Future<List<GameServerInstance>> fetchMyServers()
    static Future<void> stopServer(String serverId)
    static Future<void> deleteServer(String serverId)
}

class MatchmakerService {
    static Future<List<Room>> fetchRooms()
    static Future<Room> fetchRoomById(String id)
}

// 状态管理
class GameServerProvider extends ChangeNotifier {
    List<GameServerInstance> myServers;
    GameServerInstance? currentServer;
}

class RoomProvider extends ChangeNotifier {
    List<Room> rooms;
    Room? currentRoom;
}
```

## 数据模型

### 游戏服务器实例模型 (Game Server Factory)

```json
{
    "server_id": "user123_mygame_001",
    "name": "我的第一个游戏",
    "description": "一个简单的点击游戏",
    "status": "running",
    "container_id": "docker_container_abc123",
    "port": 8081,
    "created_at": "2025-12-17T10:00:00Z",
    "updated_at": "2025-12-17T10:30:00Z",
    "resource_usage": {
        "cpu_percent": 15.5,
        "memory_mb": 128,
        "network_io": "1.2MB"
    },
    "logs": ["Server started on port 8081", "Game initialized"]
}
```

### 游戏服务器信息模型 (Matchmaker)

```json
{
    "server_id": "localhost:8081",
    "ip": "localhost", 
    "port": 8081,
    "name": "我的第一个游戏",
    "max_players": 20,
    "current_players": 2,
    "metadata": {
        "created_by": "user123",
        "game_type": "custom"
    },
    "last_heartbeat": "2025-12-17T10:30:00Z",
    "uptime": 1800
}
```

### 代码上传请求模型

```json
{
    "file": "multipart/form-data",
    "name": "我的游戏",
    "description": "游戏描述",
    "max_players": 10
}
```

### 客户端数据模型

```dart
class GameServerInstance {
    final String serverId;        // 服务器唯一标识
    final String name;            // 游戏名称
    final String description;     // 游戏描述
    final String status;          // 状态: creating, running, stopped, error
    final String containerId;     // Docker容器ID
    final int port;               // 服务器端口
    final DateTime createdAt;     // 创建时间
    final DateTime updatedAt;     // 更新时间
    final Map<String, dynamic> resourceUsage; // 资源使用情况
}

class Room {
    final String id;              // 服务器唯一标识
    final String name;            // 房间显示名称
    final String ip;              // 服务器IP地址
    final int port;               // 服务器端口
    final int playerCount;        // 当前玩家数
    final int maxPlayers;         // 最大玩家数
    final Map<String, dynamic> metadata; // 扩展元数据
    final String lastHeartbeat;   // 最后心跳时间
    final int uptime;             // 运行时长(秒)
}
```

## 正确性属性

*属性是一个特征或行为，应该在系统的所有有效执行中保持为真——本质上是关于系统应该做什么的正式声明。属性作为人类可读规范和机器可验证正确性保证之间的桥梁。*
基于更新的需求文档中的验收标准，我将这些标准转换为可测试的正确性属性。新的架构引入了Game Server Factory组件，增加了代码上传、分析、容器管理等核心功能。

### 属性反思

在完成预工作分析后，我识别出了一些可以合并的冗余属性：

- 属性1.1和4.1都涉及代码验证，可以合并为综合的代码验证属性
- 属性1.3和1.4都涉及容器管理，可以合并为容器生命周期管理属性
- 属性8.1、8.3和8.4都涉及错误处理，可以合并为统一的错误处理属性

### 正确性属性

**属性 1: 代码上传和验证**
*对于任何*上传的JavaScript文件，Game Server Factory应该验证文件格式、大小限制、语法和基本结构
**验证需求: 1.1, 4.1**

**属性 2: 代码安全分析**
*对于任何*JavaScript代码，Game Server Factory应该扫描潜在的恶意操作并在发现安全风险时拒绝代码
**验证需求: 1.2, 4.2, 4.3**

**属性 3: 容器创建和部署**
*对于任何*通过安全检查的代码，Game Server Factory应该创建Docker容器并部署游戏服务器
**验证需求: 1.3, 4.4**

**属性 4: 容器状态监控**
*对于任何*创建的游戏服务器容器，Game Server Factory应该监控容器状态并记录启动日志
**验证需求: 1.4**

**属性 5: 自动服务器注册**
*对于任何*成功启动的游戏服务器容器，服务器应该自动向Matchmaker Service注册
**验证需求: 1.5**

**属性 6: 用户服务器列表管理**
*对于任何*用户创建的游戏服务器，客户端应该显示所有服务器及其状态信息
**验证需求: 2.1**

**属性 7: 容器生命周期控制**
*对于任何*用户的停止或删除请求，Game Server Factory应该优雅关闭容器并清理相关资源
**验证需求: 2.2, 2.3**

**属性 8: 服务器详情显示**
*对于任何*服务器详情查询，客户端应该显示容器状态、资源使用情况和运行日志
**验证需求: 2.4**

**属性 9: 实时状态更新**
*对于任何*服务器状态变化，客户端应该实时更新显示的状态信息
**验证需求: 2.5**

**属性 10: 房间列表查询**
*对于任何*房间列表请求，Matchmaker Service应该返回所有活跃游戏服务器的信息
**验证需求: 3.1**

**属性 11: 房间信息显示完整性**
*对于任何*房间数据，客户端显示应该包含房间名称、当前玩家数、最大玩家数和服务器状态
**验证需求: 3.2**

**属性 12: WebSocket连接建立**
*对于任何*房间选择操作，客户端应该建立WebSocket连接并接收当前游戏状态
**验证需求: 3.3, 3.4**

**属性 13: 游戏操作处理**
*对于任何*玩家游戏操作，游戏服务器应该处理操作并广播状态更新给所有连接的客户端
**验证需求: 3.5**

**属性 14: 系统资源管理**
*对于任何*系统资源状态，Game Server Factory应该管理闲置容器、限制资源使用并处理异常退出
**验证需求: 5.3, 5.4, 5.5**

**属性 15: 定期清理机制**
*对于任何*定期清理任务执行，Matchmaker Service应该检查服务器心跳状态并移除过期条目
**验证需求: 5.1, 5.2**

**属性 16: 健康检查和状态查询**
*对于任何*健康检查或容器状态查询，服务应该返回详细的状态信息和资源使用情况
**验证需求: 6.2, 6.3**

**属性 17: API错误响应格式**
*对于任何*格式错误或不存在资源的API请求，服务应该返回详细的错误信息和适当的状态码
**验证需求: 6.4, 6.5**

**属性 18: 配置参数应用**
*对于任何*环境变量配置，所有服务应该正确读取并应用配置参数
**验证需求: 7.3**

**属性 19: 综合错误处理**
*对于任何*系统错误、网络连接失败、代码分析失败或容器创建失败，系统应该记录详细错误信息并提供用户友好的错误消息
**验证需求: 8.1, 8.2, 8.3, 8.4, 8.5**

## 错误处理

### 错误分类和处理策略

#### 1. 网络错误
- **连接超时**: 实施指数退避重试机制，最大重试3次
- **连接拒绝**: 显示服务不可用消息，提供手动重试选项
- **DNS解析失败**: 检查网络配置，提供网络诊断建议

#### 2. API错误
- **400 Bad Request**: 显示具体的参数验证错误信息
- **401 Unauthorized**: 重定向到登录页面或刷新认证令牌
- **404 Not Found**: 显示资源不存在消息，提供返回主页选项
- **429 Too Many Requests**: 显示速率限制消息，建议稍后重试
- **500 Internal Server Error**: 显示服务器错误消息，记录错误详情

#### 3. WebSocket错误
- **连接失败**: 尝试重新连接，显示连接状态
- **消息发送失败**: 缓存消息并在连接恢复后重发
- **协议错误**: 重新建立连接，记录协议错误详情

#### 4. 客户端错误
- **内存不足**: 清理缓存数据，优化内存使用
- **存储空间不足**: 清理临时文件，提示用户释放空间
- **权限不足**: 引导用户授予必要权限

### 错误恢复机制

```python
# 撮合服务错误处理示例
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        }
    )
```

```dart
// Flutter客户端错误处理示例
class ApiService {
    static Future<T> _handleRequest<T>(Future<T> Function() request) async {
        try {
            return await request();
        } on SocketException {
            throw NetworkException('网络连接失败，请检查网络设置');
        } on TimeoutException {
            throw NetworkException('请求超时，请稍后重试');
        } on FormatException {
            throw ApiException('数据格式错误');
        } catch (e) {
            throw ApiException('未知错误: ${e.toString()}');
        }
    }
}
```

## 测试策略

### 双重测试方法

系统采用单元测试和基于属性的测试相结合的综合测试策略：

#### 单元测试
- 验证特定示例、边界情况和错误条件
- 测试组件间的集成点
- 覆盖具体的业务逻辑场景
- 目标代码覆盖率：80%+

#### 基于属性的测试
- 验证应该在所有输入中保持的通用属性
- 使用随机生成的测试数据验证系统行为
- 每个属性测试运行最少100次迭代
- 使用Hypothesis (Python) 和 fast_check (JavaScript) 作为属性测试库

### 测试框架和工具

#### Python (撮合服务)
- **单元测试**: pytest, pytest-asyncio
- **属性测试**: Hypothesis
- **API测试**: httpx, FastAPI TestClient
- **覆盖率**: pytest-cov

#### Node.js (游戏服务器)
- **单元测试**: Jest
- **属性测试**: fast-check
- **WebSocket测试**: socket.io-client
- **覆盖率**: Istanbul/nyc

#### Flutter (客户端)
- **单元测试**: flutter_test
- **Widget测试**: flutter_test
- **集成测试**: integration_test
- **Mock**: mockito

### 测试标记格式

每个基于属性的测试必须使用以下格式标记：
`**Feature: ai-game-platform, Property {number}: {property_text}**`

示例：
```python
def test_server_registration_validation():
    """
    **Feature: ai-game-platform, Property 1: 服务器注册和验证**
    """
    # 测试实现
```

### 测试数据生成策略

#### 智能生成器设计
- **服务器信息生成器**: 生成有效和无效的IP地址、端口范围、服务器名称
- **心跳数据生成器**: 生成不同时间戳和玩家数量的心跳数据
- **WebSocket消息生成器**: 生成各种游戏操作和状态更新消息
- **错误场景生成器**: 生成网络错误、超时和格式错误的请求

#### 边界值测试
- 端口范围：1-65535
- 玩家数量：0到最大值
- 字符串长度：空字符串到最大长度
- 超时时间：最小到最大超时值
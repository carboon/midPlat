# 配置参考

AI游戏平台的完整配置选项说明。

## 🔧 环境变量配置

### 游戏服务器工厂配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8080` | 服务端口 |
| `MAX_FILE_SIZE` | `1048576` | 最大文件大小(字节) |
| `MAX_CONTAINERS` | `50` | 最大容器数量 |
| `CONTAINER_MEMORY_LIMIT` | `512m` | 容器内存限制 |
| `CONTAINER_CPU_LIMIT` | `1.0` | 容器CPU限制 |
| `IDLE_TIMEOUT_SECONDS` | `1800` | 闲置超时时间(秒) |
| `CLEANUP_INTERVAL_SECONDS` | `300` | 清理间隔时间(秒) |

### 撮合服务配置

| 变量名 | 默认值 | 描述 |
|--------|--------|------|
| `HOST` | `0.0.0.0` | 服务监听地址 |
| `PORT` | `8000` | 服务端口 |
| `HEARTBEAT_TIMEOUT` | `30` | 心跳超时时间(秒) |
| `CLEANUP_INTERVAL` | `10` | 清理间隔时间(秒) |

## 📁 配置文件

### Docker Compose配置

```yaml
# docker-compose.yml
version: '3.8'
services:
  matchmaker:
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
  
  game-server-factory:
    environment:
      - MAX_CONTAINERS=100
      - CONTAINER_MEMORY_LIMIT=1g
```

### Flutter客户端配置

```bash
# mobile_app/universal_game_client/.env
MATCHMAKER_URL=http://127.0.0.1:8000
GAME_SERVER_FACTORY_URL=http://127.0.0.1:8080
APP_NAME=Universal Game Client
ROOM_REFRESH_INTERVAL=30
MAX_FILE_SIZE_MB=1
```

## 🔒 安全配置

### 生产环境安全设置

```bash
# 禁用调试模式
DEBUG=false
SHOW_DETAILED_ERRORS=false

# 配置CORS
ALLOWED_ORIGINS=https://yourdomain.com

# 设置日志级别
LOG_LEVEL=WARNING
```

---

**相关文档**: [部署教程](../tutorials/deployment.md) | [系统架构](../explanation/architecture.md)

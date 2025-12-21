# AI游戏平台部署指南

本指南详细说明了如何部署和配置AI游戏平台的各个组件，包括系统集成、错误处理和环境适配。

## 目录

1. [系统要求](#系统要求)
2. [环境配置](#环境配置)
3. [服务部署](#服务部署)
4. [集成测试](#集成测试)
5. [监控和日志](#监控和日志)
6. [故障排除](#故障排除)
7. [生产环境配置](#生产环境配置)

## 系统要求

### 最低要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10+
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **网络**: 互联网连接（用于拉取依赖）

### 推荐配置
- **CPU**: 4核心或更多
- **内存**: 8GB RAM 或更多
- **存储**: 50GB SSD
- **网络**: 稳定的互联网连接

## 环境配置

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-game-platform
```

### 2. 配置环境变量

复制环境配置模板：

```bash
cp .env.example .env
```

编辑 `.env` 文件，根据您的环境调整配置：

```bash
# 基本配置
ENVIRONMENT=development  # development, staging, production
DEBUG=true
LOG_LEVEL=INFO

# 端口配置
MATCHMAKER_PORT=8000
FACTORY_PORT=8080
BASE_PORT=8082

# 容器配置
MAX_CONTAINERS=50
CONTAINER_MEMORY_LIMIT=512m
CONTAINER_CPU_LIMIT=1.0

# 安全配置（生产环境必须修改）
ALLOWED_ORIGINS=*
```

### 3. 验证配置

运行配置验证脚本：

```bash
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

# 验证必要的环境变量
required_vars = ['ENVIRONMENT', 'MATCHMAKER_PORT', 'FACTORY_PORT']
missing = [var for var in required_vars if not os.getenv(var)]

if missing:
    print(f'缺少环境变量: {missing}')
    exit(1)
else:
    print('环境配置验证通过')
"
```

## 服务部署

### 自动化部署（推荐）

使用提供的部署脚本进行自动化部署：

```bash
# 使用Makefile（最简单）
make deploy

# 或直接使用部署脚本
./scripts/deploy.sh deploy

# 部署包含示例服务器
make deploy-example
# 或
./scripts/deploy.sh deploy example
```

### 开发环境部署

1. **快速开发环境设置**：

```bash
make dev
```

这个命令会自动执行：
- 环境初始化
- 镜像构建
- 服务启动
- 健康检查

2. **手动步骤**：

```bash
# 初始化环境
make setup

# 构建镜像
make build

# 启动服务
make start

# 验证部署
make validate
```

### 生产环境部署

1. **自动化生产部署**：

```bash
make deploy-prod
```

2. **手动生产部署**：

```bash
# 更新环境配置
vim .env

# 使用生产配置启动
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **生产环境检查**：

```bash
make prod-check
```

### 单独服务部署

#### 撮合服务

```bash
cd matchmaker_service/matchmaker
docker build -t matchmaker .
docker run -d \
  --name matchmaker \
  -p 8000:8000 \
  -e ENVIRONMENT=production \
  -e HEARTBEAT_TIMEOUT=30 \
  --network game-network \
  matchmaker
```

#### 游戏服务器工厂

```bash
cd game_server_factory
docker build -t game-server-factory .
docker run -d \
  --name game-server-factory \
  -p 8080:8080 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e ENVIRONMENT=production \
  -e MATCHMAKER_URL=http://matchmaker:8000 \
  --network game-network \
  game-server-factory
```

## 集成测试

### 自动化测试

使用提供的脚本运行完整的验证和测试：

```bash
# 综合部署验证
make validate

# 运行集成测试
make test

# 运行端到端测试
make test-e2e

# 性能测试
make perf
```

### 手动测试

1. **健康检查**：

```bash
# 快速健康检查
make health-quick

# 综合健康检查
make health

# 或使用脚本
./scripts/health-check.sh comprehensive
```

2. **API端点测试**：

```bash
# 获取服务器列表
curl http://localhost:8000/servers
curl http://localhost:8080/servers

# 系统集成状态
curl http://localhost:8080/system/integration-status

# 端到端测试
curl http://localhost:8080/system/end-to-end-test
```

3. **错误处理测试**：

```bash
# 测试404错误响应格式
curl http://localhost:8080/servers/nonexistent

# 测试400错误响应格式
curl -X POST http://localhost:8080/upload
```

## 监控和日志

### 自动化监控

```bash
# 启动监控模式
make monitor

# 查看服务状态
make status

# 生成系统报告
make report
```

### 日志查看

```bash
# 查看所有服务日志
make logs

# 查看特定服务日志
make logs-matchmaker
make logs-factory
make logs-example

# 或使用docker-compose
docker-compose logs -f
docker-compose logs -f matchmaker
docker-compose logs -f game-server-factory
```

### 日志文件位置

- **撮合服务**: `matchmaker_logs/matchmaker_service.log`
- **游戏服务器工厂**: `factory_logs/game_server_factory.log`
- **Docker容器日志**: 通过 `docker logs <container_id>` 查看

### 监控端点

- **撮合服务健康检查**: `http://localhost:8000/health`
- **工厂服务健康检查**: `http://localhost:8080/health`
- **系统统计**: `http://localhost:8080/system/stats`
- **资源监控**: `http://localhost:8080/system/resources`
- **集成状态**: `http://localhost:8080/system/integration-status`

### 性能监控

```bash
# 查看容器资源使用
docker stats

# 查看系统资源
curl http://localhost:8080/system/resources

# 查看闲置容器
curl http://localhost:8080/system/idle-containers
```

## 故障排除

### 常见问题

#### 1. 服务启动失败

**症状**: 容器无法启动或立即退出

**解决方案**:
```bash
# 查看详细错误信息
docker-compose logs <service_name>

# 检查端口占用
netstat -tulpn | grep <port>

# 检查Docker守护进程
sudo systemctl status docker
```

#### 2. 容器创建失败

**症状**: Game Server Factory无法创建游戏容器

**解决方案**:
```bash
# 检查Docker socket权限
ls -la /var/run/docker.sock

# 检查Docker网络
docker network ls
docker network inspect game-network

# 检查资源限制
curl http://localhost:8080/system/resources
```

#### 3. 服务间通信失败

**症状**: 服务无法相互访问

**解决方案**:
```bash
# 检查网络连接
docker-compose exec matchmaker ping game-server-factory

# 检查DNS解析
docker-compose exec matchmaker nslookup game-server-factory

# 检查防火墙设置
sudo ufw status
```

#### 4. 配置错误

**症状**: 服务配置验证失败

**解决方案**:
```bash
# 验证环境变量
docker-compose config

# 检查配置文件语法
python3 -c "from game_server_factory.main import Config; print(Config.validate_config())"

# 重新加载配置
docker-compose restart
```

### 错误日志分析

#### 标准化错误格式

所有服务都使用标准化的错误响应格式：

```json
{
  "error": {
    "code": 404,
    "message": "资源不存在",
    "timestamp": "2025-12-18T10:00:00Z",
    "path": "/servers/invalid_id",
    "details": {
      "server_id": "invalid_id"
    }
  }
}
```

#### 日志级别说明

- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息（默认）
- **WARNING**: 警告信息
- **ERROR**: 错误信息
- **CRITICAL**: 严重错误

## 生产环境配置

### 安全配置

1. **更新CORS设置**：

```bash
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

2. **禁用调试模式**：

```bash
DEBUG=false
SHOW_DETAILED_ERRORS=false
```

3. **配置HTTPS**：

使用反向代理（如Nginx）配置SSL：

```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location /matchmaker/ {
        proxy_pass http://localhost:8000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /factory/ {
        proxy_pass http://localhost:8080/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 性能优化

1. **增加资源限制**：

```bash
MAX_CONTAINERS=200
CONTAINER_MEMORY_LIMIT=1g
CONTAINER_CPU_LIMIT=2.0
```

2. **优化清理间隔**：

```bash
CLEANUP_INTERVAL_SECONDS=180  # 3分钟
IDLE_TIMEOUT_SECONDS=900      # 15分钟
```

3. **配置日志轮转**：

```bash
LOG_MAX_SIZE=52428800    # 50MB
LOG_BACKUP_COUNT=10
```

### 备份和恢复

1. **数据备份**：

```bash
# 备份Docker卷
docker run --rm -v factory_data:/data -v $(pwd):/backup alpine tar czf /backup/factory_data.tar.gz -C /data .

# 备份日志
docker run --rm -v factory_logs:/logs -v $(pwd):/backup alpine tar czf /backup/factory_logs.tar.gz -C /logs .
```

2. **配置备份**：

```bash
# 备份配置文件
cp .env .env.backup
cp docker-compose.yml docker-compose.yml.backup
```

### 监控和告警

1. **设置健康检查监控**：

```bash
# 使用cron定期检查
*/5 * * * * curl -f http://localhost:8000/health || echo "Matchmaker down" | mail -s "Service Alert" admin@yourdomain.com
*/5 * * * * curl -f http://localhost:8080/health || echo "Factory down" | mail -s "Service Alert" admin@yourdomain.com
```

2. **资源监控**：

```bash
# 监控容器数量
*/10 * * * * [ $(curl -s http://localhost:8080/system/stats | jq '.game_servers_count') -gt 180 ] && echo "High container count" | mail -s "Resource Alert" admin@yourdomain.com
```

## 更新和维护

### 服务更新

1. **滚动更新**：

```bash
# 更新单个服务
docker-compose pull matchmaker
docker-compose up -d --no-deps matchmaker

# 更新所有服务
docker-compose pull
docker-compose up -d
```

2. **零停机更新**：

```bash
# 使用蓝绿部署
docker-compose -f docker-compose.blue.yml up -d
# 验证新版本
# 切换流量
docker-compose -f docker-compose.yml down
```

### 定期维护

1. **清理未使用的资源**：

```bash
# 清理Docker资源
docker system prune -f
docker volume prune -f

# 清理旧日志
find /var/log -name "*.log" -mtime +30 -delete
```

2. **检查系统健康**：

```bash
# 运行集成测试
python3 test_integration.py

# 检查资源使用
curl http://localhost:8080/system/resources
```

## 支持和联系

如果您在部署过程中遇到问题，请：

1. 查看本指南的故障排除部分
2. 检查项目的GitHub Issues
3. 运行集成测试脚本获取详细信息
4. 联系技术支持团队

---

**注意**: 本指南假设您具有基本的Docker和Linux系统管理知识。在生产环境中部署前，请确保充分测试所有配置。
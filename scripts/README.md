# AI游戏平台部署脚本

本目录包含AI游戏平台的部署和管理脚本，支持完整的容器化部署、网络配置、健康检查和验证功能。

## 脚本概览

### 核心部署脚本

#### `deploy.sh` - 主部署脚本
完整的部署自动化脚本，支持从环境检查到服务启动的全流程部署。

**功能特性:**
- 自动依赖检查（Docker、Docker Compose）
- 环境配置验证
- 网络创建和配置
- 镜像构建和服务启动
- 健康检查和状态验证
- 多种部署模式支持

**使用方法:**
```bash
# 完整部署
./scripts/deploy.sh deploy

# 部署包含示例服务器
./scripts/deploy.sh deploy example

# 启动服务
./scripts/deploy.sh start

# 停止服务
./scripts/deploy.sh stop

# 查看状态
./scripts/deploy.sh status

# 运行健康检查
./scripts/deploy.sh health
```

#### `health-check.sh` - 健康检查脚本
综合的系统健康检查工具，支持多种检查模式和监控功能。

**功能特性:**
- 快速健康检查
- 综合系统验证
- 实时监控模式
- 资源使用监控
- 日志错误分析
- 健康报告生成

**使用方法:**
```bash
# 快速检查
./scripts/health-check.sh quick

# 综合检查
./scripts/health-check.sh comprehensive

# 监控模式（每30秒检查一次）
./scripts/health-check.sh monitor 30

# 生成健康报告
./scripts/health-check.sh report
```

#### `setup-network.sh` - 网络配置脚本
专门用于Docker网络配置和管理的脚本，支持动态容器网络需求。

**功能特性:**
- 主网络创建和配置
- 动态容器子网络设置
- 服务发现配置
- 网络策略管理
- 网络连通性验证

**使用方法:**
```bash
# 设置网络配置
./scripts/setup-network.sh setup

# 验证网络配置
./scripts/setup-network.sh verify

# 显示网络信息
./scripts/setup-network.sh info

# 重置网络配置
./scripts/setup-network.sh reset
```

#### `validate-deployment.sh` - 部署验证脚本
全面的部署验证工具，确保系统正确部署和配置。

**功能特性:**
- Docker环境验证
- 网络配置检查
- 服务端点测试
- 动态容器创建验证
- 性能基准测试
- 综合验证报告

**使用方法:**
```bash
# 综合验证
./scripts/validate-deployment.sh comprehensive

# 验证动态容器创建
./scripts/validate-deployment.sh dynamic

# 性能测试
./scripts/validate-deployment.sh performance

# 生成验证报告
./scripts/validate-deployment.sh report
```

## 快速开始

### 1. 初始化环境
```bash
# 使用Makefile（推荐）
make setup

# 或手动执行
cp .env.example .env
chmod +x scripts/*.sh
./scripts/setup-network.sh setup
```

### 2. 完整部署
```bash
# 使用Makefile
make deploy

# 或手动执行
./scripts/deploy.sh deploy
```

### 3. 验证部署
```bash
# 使用Makefile
make validate

# 或手动执行
./scripts/validate-deployment.sh comprehensive
```

### 4. 健康检查
```bash
# 使用Makefile
make health

# 或手动执行
./scripts/health-check.sh comprehensive
```

## 部署模式

### 开发环境
```bash
# 完整开发环境设置
make dev

# 或分步执行
make setup
make build
make start
make health-quick
```

### 生产环境
```bash
# 生产环境部署
make deploy-prod

# 生产环境检查
make prod-check
```

### 调试模式
```bash
# 启动调试模式
make debug

# 查看调试日志
make logs
```

## 网络配置

### 网络架构
- **主网络**: `game-network` (172.20.0.0/16)
- **动态网络**: `game-network-dynamic` (172.20.100.0/24)
- **端口范围**: 8081-8131 (动态游戏服务器)

### 网络管理
```bash
# 设置网络
make network-setup

# 查看网络信息
make network-info

# 重置网络
make network-reset
```

## 监控和维护

### 实时监控
```bash
# 启动监控模式
make monitor

# 查看服务状态
make status

# 查看日志
make logs
```

### 健康检查
```bash
# 快速检查
make health-quick

# 综合检查
make health

# 生成报告
make report
```

### 性能测试
```bash
# 运行性能测试
make perf

# 运行集成测试
make test
```

## 故障排除

### 常见问题

#### 1. 端口冲突
```bash
# 检查端口占用
make port-check

# 修改.env文件中的端口配置
vim .env
```

#### 2. 网络问题
```bash
# 验证网络配置
make validate-network

# 重置网络
make network-reset
```

#### 3. 容器启动失败
```bash
# 查看详细日志
make logs

# 检查容器状态
docker-compose ps

# 重启服务
make restart
```

#### 4. 服务不可访问
```bash
# 运行健康检查
make health

# 验证端点
./scripts/validate-deployment.sh endpoints
```

### 调试工具

#### 日志查看
```bash
# 所有服务日志
make logs

# 特定服务日志
make logs-matchmaker
make logs-factory
make logs-example
```

#### 配置检查
```bash
# 检查配置文件
make config-check

# 验证环境变量
./scripts/validate-deployment.sh config
```

## 备份和恢复

### 备份
```bash
# 备份配置和数据
make backup

# 手动备份
mkdir -p backups
cp .env backups/
cp docker-compose.yml backups/
```

### 恢复
```bash
# 从备份恢复
cp backups/.env .
cp backups/docker-compose.yml .
make restart
```

## 更新和维护

### 更新服务
```bash
# 更新镜像
make update

# 重新构建
make build
make restart
```

### 清理资源
```bash
# 标准清理
make clean

# 深度清理（包括镜像）
make clean-all
```

## 环境变量配置

### 关键配置项
- `ENVIRONMENT`: 环境类型 (development/production)
- `MATCHMAKER_PORT`: 撮合服务端口 (默认: 8000)
- `FACTORY_PORT`: 游戏服务器工厂端口 (默认: 8080)
- `BASE_PORT`: 动态服务器基础端口 (默认: 8081)
- `MAX_CONTAINERS`: 最大容器数量 (默认: 50)

### 生产环境配置
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com
MAX_CONTAINERS=200
CONTAINER_MEMORY_LIMIT=1g
```

## 安全注意事项

### 生产环境
1. 修改默认端口
2. 设置正确的CORS策略
3. 禁用调试模式
4. 配置适当的资源限制
5. 设置日志轮转

### 网络安全
1. 使用防火墙限制访问
2. 配置SSL/TLS证书
3. 定期更新镜像
4. 监控异常访问

## 支持和贡献

### 获取帮助
- 查看脚本帮助: `./scripts/<script-name>.sh --help`
- 查看Makefile帮助: `make help`
- 运行验证脚本: `make validate`

### 贡献指南
1. 遵循现有的脚本结构和风格
2. 添加适当的错误处理和日志
3. 更新相关文档
4. 测试所有功能

---

**注意**: 所有脚本都经过测试，但在生产环境使用前请充分验证配置。
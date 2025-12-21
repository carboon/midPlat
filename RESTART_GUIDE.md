# 服务重启指南

## 当前服务状态

系统中运行的服务：
- **matchmaker** (撮合服务) - 端口 8000
- **game-server-factory** (游戏服务器工厂) - 端口 8080

## 重启方式

### 方式 1: 使用 Makefile（推荐）

最简单的方式是使用 Makefile 中的 `restart` 命令：

```bash
make restart
```

这个命令会：
1. 重启所有Docker容器
2. 运行快速健康检查
3. 确保服务正常运行

### 方式 2: 使用 Docker Compose 命令

如果你想更细粒度地控制重启过程：

#### 重启所有服务
```bash
docker-compose restart
```

#### 重启特定服务
```bash
# 重启撮合服务
docker-compose restart matchmaker

# 重启游戏服务器工厂
docker-compose restart game-server-factory
```

#### 停止并重新启动（完整重启）
```bash
# 停止所有服务
docker-compose down

# 启动所有服务
docker-compose up -d
```

### 方式 3: 完整重新部署

如果需要重新构建镜像并部署：

```bash
# 完整部署（包括构建镜像）
make deploy

# 或者使用 Docker Compose
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 验证服务状态

### 查看服务状态
```bash
make status
```

或者：
```bash
docker-compose ps
```

### 运行健康检查
```bash
# 快速健康检查
make health-quick

# 完整健康检查
make health
```

### 查看服务日志
```bash
# 查看所有服务日志
make logs

# 查看特定服务日志
make logs-factory      # 游戏服务器工厂
make logs-matchmaker   # 撮合服务
```

## 修改生效的验证步骤

### 1. 重启服务
```bash
make restart
```

### 2. 验证后端修改
```bash
# 检查 Description 字段是否可选
curl -X POST http://localhost:8080/upload \
  -F "file=@game.html" \
  -F "name=TestGame"
# 注意：不需要提供 description 字段
```

### 3. 验证容器管理修改
```bash
# 上传第一个游戏
curl -X POST http://localhost:8080/upload \
  -F "file=@game1.html" \
  -F "name=Game1"

# 上传第二个游戏
curl -X POST http://localhost:8080/upload \
  -F "file=@game2.html" \
  -F "name=Game2"

# 查看所有服务器
curl http://localhost:8080/servers

# 验证每个容器都有不同的端口
```

### 4. 检查日志
```bash
# 查看游戏服务器工厂的日志
docker-compose logs game-server-factory | tail -50

# 查看是否有端口分配的日志
docker-compose logs game-server-factory | grep "分配端口"
```

## 常见问题

### Q: 重启后服务无法启动？
A: 检查日志：
```bash
docker-compose logs game-server-factory
docker-compose logs matchmaker
```

### Q: 端口已被占用？
A: 检查端口占用情况：
```bash
make port-check
```

### Q: 需要清理旧的容器？
A: 使用清理命令：
```bash
# 清理停止的动态容器
make containers-cleanup

# 完整清理（谨慎使用）
make clean
```

### Q: 如何查看修改是否生效？
A: 
1. 检查日志中是否有新的日志消息
2. 尝试上传不带 Description 的游戏
3. 上传多个游戏，验证端口分配

## 快速重启流程

```bash
# 1. 重启服务
make restart

# 2. 验证状态
make status

# 3. 运行健康检查
make health-quick

# 4. 查看日志（如有问题）
make logs
```

## 生产环境重启

对于生产环境，建议使用以下流程：

```bash
# 1. 备份当前配置
make backup

# 2. 停止服务（优雅关闭）
docker-compose down

# 3. 重新启动
docker-compose up -d

# 4. 验证服务
make health

# 5. 监控日志
make monitor
```

## 修改生效的预期结果

### 修改 1: Description 字段可选
- ✅ 可以不填写 Description 上传游戏
- ✅ 后端返回的 description 字段始终是有效的 String

### 修改 2: 类型转换错误修复
- ✅ 上传成功后不出现类型转换错误
- ✅ Dart 客户端能正确解析所有响应

### 修改 3: 容器管理改进
- ✅ 多次上传的容器都能正常运行
- ✅ 每个容器有唯一的端口（不是 8082）
- ✅ 容器创建失败时能正确清理资源

## 需要帮助？

如果重启后仍有问题，请：

1. 检查日志：`make logs`
2. 运行健康检查：`make health`
3. 验证配置：`make config-check`
4. 查看详细报告：`make report`

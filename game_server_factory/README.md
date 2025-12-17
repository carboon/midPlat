# Game Server Factory

游戏服务器工厂 - 负责接收JavaScript代码、分析优化代码并动态创建游戏服务器Docker容器。

## 功能特性

- **代码上传和验证**: 支持JavaScript文件上传，验证文件格式和大小限制
- **代码安全分析**: 使用AST解析JavaScript代码，检测潜在的恶意操作
- **游戏服务器管理**: 创建、监控、停止和删除游戏服务器实例
- **RESTful API**: 提供完整的API接口用于客户端集成
- **健康检查**: 提供服务状态监控和容器统计信息

## API 端点

### 基础信息
- `GET /` - 服务信息
- `GET /health` - 健康检查
- `GET /docs` - API文档 (Swagger UI)
- `GET /redoc` - API文档 (ReDoc)

### 代码管理
- `POST /upload` - 上传JavaScript游戏代码
- `GET /servers` - 获取用户的游戏服务器列表
- `GET /servers/{server_id}` - 获取特定服务器详情
- `POST /servers/{server_id}/stop` - 停止游戏服务器
- `DELETE /servers/{server_id}` - 删除游戏服务器
- `GET /servers/{server_id}/logs` - 获取服务器日志

## 快速开始

### 本地开发

1. 安装依赖:
```bash
pip install -r requirements.txt
```

2. 配置环境变量:
```bash
cp .env.example .env
# 编辑 .env 文件设置配置
```

3. 启动服务:
```bash
python main.py
```

4. 访问API文档:
```
http://localhost:8080/docs
```

### Docker部署

1. 构建镜像:
```bash
docker build -t game-server-factory .
```

2. 运行容器:
```bash
docker run -p 8080:8080 --env-file .env game-server-factory
```

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| HOST | 0.0.0.0 | 服务器监听地址 |
| PORT | 8080 | 服务器端口 |
| DEBUG | false | 调试模式 |
| MAX_FILE_SIZE | 1048576 | 最大文件大小(字节) |
| ALLOWED_EXTENSIONS | .js,.mjs | 允许的文件扩展名 |
| DOCKER_NETWORK | game-network | Docker网络名称 |
| BASE_PORT | 8081 | 游戏服务器起始端口 |
| LOG_LEVEL | INFO | 日志级别 |

## 代码安全检查

系统会对上传的JavaScript代码进行以下安全检查:

### 高风险操作 (会被拒绝)
- 文件系统访问 (`require('fs')`)
- 子进程执行 (`require('child_process')`)
- eval函数使用 (`eval()`)
- Function构造函数 (`new Function()`)

### 中等风险操作 (会发出警告)
- 网络模块使用 (`require('http')`, `require('https')`)
- 全局对象操作 (`global.*`)
- 进程操作 (`process.*`)

### 建议改进
- 使用 `let`/`const` 替代 `var`
- 使用结构化日志替代 `console.log`
- 避免过多的定时器使用

## 数据模型

### GameServerInstance
```json
{
    "server_id": "服务器唯一标识",
    "name": "游戏名称",
    "description": "游戏描述", 
    "status": "状态 (creating/running/stopped/error)",
    "container_id": "Docker容器ID",
    "port": "服务器端口",
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "resource_usage": "资源使用情况",
    "logs": "服务器日志"
}
```

## 开发指南

### 添加新的安全检查规则

在 `code_analyzer.py` 中的 `dangerous_patterns` 列表添加新的正则表达式模式:

```python
self.dangerous_patterns.append(
    (r'new_dangerous_pattern', "severity", "检测到危险操作")
)
```

### 扩展数据模型

修改 `GameServerInstance` 类添加新字段:

```python
class GameServerInstance(BaseModel):
    # 现有字段...
    new_field: str = Field(..., description="新字段描述")
```

## 测试

运行测试:
```bash
pytest tests/
```

## 日志

日志文件位置: `game_server_factory.log`

日志级别可通过 `LOG_LEVEL` 环境变量配置。

## 贡献

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License
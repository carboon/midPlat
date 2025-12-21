# AI游戏平台

> 轻量级HTML游戏分发和执行平台，支持游戏上传、自动部署、发现和实时游玩的完整解决方案。

[![版本](https://img.shields.io/badge/版本-2.0.0-blue.svg)](https://github.com/your-repo/releases)
[![许可证](https://img.shields.io/badge/许可证-MIT-green.svg)](LICENSE)
[![文档](https://img.shields.io/badge/文档-完整-brightgreen.svg)](docs/README.md)

## ✨ 特性

- 🎮 **HTML游戏支持** - 上传HTML文件或ZIP包，自动创建游戏服务器
- 🚀 **一键部署** - Docker容器化，秒级启动游戏实例
- 🔒 **安全隔离** - 自动代码安全检查，容器隔离运行
- 📱 **跨平台客户端** - Flutter应用支持多平台游戏管理
- 🌐 **实时通信** - WebSocket支持多人实时游戏
- 📊 **智能监控** - 资源监控、自动清理、性能统计

## 🚀 快速开始

### 一键部署

```bash
# 克隆项目
git clone <repository-url>
cd ai-game-platform

# 一键部署所有服务
make deploy

# 验证部署
make health
```

部署完成后访问：
- **游戏服务器工厂**: http://localhost:8080
- **撮合服务**: http://localhost:8000
- **API文档**: http://localhost:8080/docs

### 启动客户端

```bash
cd mobile_app/universal_game_client
flutter pub get
flutter run -d macos
```

## 📚 文档

我们的文档基于 [Diátaxis 框架](https://diataxis.fr/) 组织，为不同需求提供结构化的文档体验：

### 🎯 新用户入门
- [📖 快速开始教程](docs/tutorials/getting-started.md) - 15分钟体验完整功能
- [🎮 游戏开发教程](docs/tutorials/game-development.md) - 开发你的第一个HTML游戏

### 🛠️ 使用指南
- [📤 代码上传指南](docs/how-to/code-upload.md) - 详细的上传和管理流程
- [🔧 故障排除指南](docs/how-to/troubleshooting.md) - 常见问题解决方案

### 📖 技术参考
- [🔌 API参考文档](docs/reference/api-reference.md) - 完整的API接口说明
- [⚙️ 配置参考](docs/reference/configuration.md) - 所有配置选项详解

### 💡 深入理解
- [🏗️ 系统架构](docs/explanation/architecture.md) - 平台架构设计详解
- [🔒 安全模型](docs/explanation/security-model.md) - 安全机制说明

**📋 [完整文档目录](docs/README.md)**

## 🧪 测试

完整的测试套件位于 [TEST](TEST/) 目录，包含 100+ 个测试用例。

### 快速开始测试

```bash
# 运行所有测试
python3 run_all_tests.py

# 运行特定模块测试
bash TEST/scripts/run_component_tests.sh factory      # Game Server Factory
bash TEST/scripts/run_component_tests.sh matchmaker   # Matchmaker Service
bash TEST/scripts/run_component_tests.sh template     # Game Server Template
bash TEST/scripts/run_component_tests.sh mobile       # Mobile App
```

### 测试结构

```
TEST/
├── game_server_factory/    # 游戏服务器工厂测试 (28+ 个)
├── matchmaker_service/     # 撮合服务测试 (7+ 个)
├── game_server_template/   # 游戏服务器模板测试 (8+ 个)
├── mobile_app/             # 移动应用测试 (48+ 个)
└── scripts/                # 测试运行脚本
```

### 测试覆盖

| 模块 | 单元测试 | 集成测试 | 属性测试 | 总计 |
|------|---------|---------|---------|------|
| Game Server Factory | 15+ | 13+ | - | 28+ |
| Matchmaker Service | 4+ | 3+ | - | 7+ |
| Game Server Template | 7+ | 1+ | - | 8+ |
| Mobile App | 30+ | 18+ | - | 48+ |
| **总计** | **56+** | **35+** | **-** | **91+** |

**📋 [完整测试文档](TEST/README.md)** | **📖 [测试使用说明](TEST/USAGE.md)**

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flutter客户端   │    │   游戏服务器工厂   │    │     撮合服务      │
│    :flutter     │◄──►│     :8080      │◄──►│     :8000      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Docker引擎     │
                    │  游戏容器管理     │
                    └─────────────────┘
                              │
                              ▼
        ┌─────────────┬─────────────┬─────────────┐
        │  游戏服务器1  │  游戏服务器2  │  游戏服务器N  │
        │   :8081    │   :8082    │   :808X    │
        └─────────────┴─────────────┴─────────────┘
```

## 🎮 核心功能

### 游戏上传和部署
- 支持单个HTML文件或ZIP压缩包
- 自动JavaScript代码安全检查
- Docker容器自动创建和配置
- 一键部署，秒级启动

### 服务器管理
- 实时监控服务器状态和资源使用
- 支持启动、停止、删除操作
- 自动清理闲置容器节省资源
- 详细的服务器日志查看

### 游戏发现
- 自动注册到撮合服务
- 实时服务器列表更新
- 支持房间浏览和快速加入
- 负载均衡和服务发现

### 实时游戏体验
- WebSocket实时通信
- 多人游戏状态同步
- 跨平台客户端支持
- 流畅的游戏体验

## 🔧 技术栈

| 组件 | 技术栈 | 描述 |
|------|--------|------|
| **游戏服务器工厂** | Python + FastAPI + Docker | 代码上传、安全检查、容器管理 |
| **撮合服务** | Python + FastAPI | 服务器注册、发现、心跳管理 |
| **游戏服务器** | Node.js + Express + Socket.IO | HTML游戏运行、实时通信 |
| **客户端** | Flutter + Dart | 跨平台游戏管理界面 |
| **基础设施** | Docker + Docker Compose | 容器化部署和编排 |

## 📊 系统要求

### 最低要求
- **操作系统**: macOS 10.15+ / Windows 10+ / Ubuntu 18.04+
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **Docker**: 20.10+
- **Docker Compose**: 2.0+

### 推荐配置
- **CPU**: 4核心或更多
- **内存**: 8GB RAM 或更多
- **存储**: 50GB SSD
- **网络**: 稳定的互联网连接

## 🎯 使用场景

### 游戏开发者
- 快速原型验证
- 多人游戏测试
- 游戏分享和展示
- 教学和演示

### 教育机构
- 编程教学平台
- 学生作品展示
- 在线编程竞赛
- 游戏开发课程

### 企业团队
- 团队建设游戏
- 内部工具开发
- 快速原型验证
- 创意展示平台

## 🔒 安全特性

- **代码安全扫描** - 自动检测危险操作和恶意代码
- **容器隔离** - 每个游戏运行在独立的Docker容器中
- **资源限制** - 严格的CPU和内存使用限制
- **网络隔离** - 安全的网络配置和访问控制
- **输入验证** - 严格的文件格式和大小验证

## 📈 性能特点

- **快速部署** - 容器启动时间 < 5秒
- **低延迟** - WebSocket实时通信延迟 < 50ms
- **高并发** - 支持50+并发游戏实例
- **自动扩展** - 基于负载的自动容器管理
- **资源优化** - 智能的闲置容器清理

## 🤝 贡献

我们欢迎所有形式的贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd ai-game-platform

# 设置开发环境
make dev

# 运行测试
make test

# 查看所有可用命令
make help
```

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

## 🔗 相关链接

- [📚 完整文档](docs/README.md)
- [🐛 问题报告](https://github.com/your-repo/issues)
- [💬 讨论区](https://github.com/your-repo/discussions)
- [📦 发布版本](https://github.com/your-repo/releases)

## 📞 支持

- **文档**: [docs/README.md](docs/README.md)
- **FAQ**: [docs/how-to/troubleshooting.md](docs/how-to/troubleshooting.md)
- **邮件**: support@example.com
- **社区**: [GitHub Discussions](https://github.com/your-repo/discussions)

---

**🎮 开始你的游戏开发之旅！** 查看 [快速开始教程](docs/tutorials/getting-started.md) 在15分钟内体验完整功能。
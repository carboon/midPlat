# 📖 TEST 目录使用说明

**最后更新**: 2025-12-21

---

## 🎯 概述

TEST 目录包含 AI 游戏平台的所有测试用例，按模块和测试类型分类组织。

---

## 📁 目录结构详解

### 顶级目录

```
TEST/
├── README.md              # 目录概览
├── USAGE.md              # 本文件 - 使用说明
├── game_server_factory/  # 游戏服务器工厂模块
├── matchmaker_service/   # 撮合服务模块
├── game_server_template/ # 游戏服务器模板模块
├── mobile_app/           # 移动应用模块
└── scripts/              # 测试运行脚本
```

### 模块内部结构

每个模块目录包含：

```
<module>/
├── README.md             # 模块测试说明
├── unit/                 # 单元测试
│   ├── test_*.py        # Python 单元测试
│   └── *.test.js        # JavaScript 单元测试
├── integration/          # 集成测试
│   ├── test_*.py        # Python 集成测试
│   └── *.integration.test.js
└── property/             # 属性测试
    ├── test_*_property.py
    └── *_property.test.js
```

---

## 🚀 运行测试

### 1. 运行所有测试

```bash
# 使用主测试脚本
python3 run_all_tests.py

# 或使用快速测试脚本
bash TEST/scripts/run_all_tests.sh
```

### 2. 运行特定模块测试

```bash
# Game Server Factory
bash TEST/scripts/run_component_tests.sh factory

# Matchmaker Service
bash TEST/scripts/run_component_tests.sh matchmaker

# Game Server Template
bash TEST/scripts/run_component_tests.sh template

# Mobile App
bash TEST/scripts/run_component_tests.sh mobile
```

### 3. 运行特定类型测试

```bash
# 仅运行单元测试
bash TEST/scripts/run_component_tests.sh factory unit

# 仅运行集成测试
bash TEST/scripts/run_component_tests.sh factory integration

# 仅运行属性测试
bash TEST/scripts/run_component_tests.sh factory property
```

### 4. 运行特定测试文件

```bash
# Python 测试
cd TEST/game_server_factory/unit
python3 -m pytest test_api_endpoints.py -v

# JavaScript 测试
cd TEST/game_server_template/unit
npm test -- health-check-response.property.test.js

# Dart 测试
cd TEST/mobile_app/unit
flutter test config_parameters_property_test.dart
```

---

## 📊 模块说明

### Game Server Factory (游戏服务器工厂)

**位置**: `TEST/game_server_factory/`

**功能**: 负责创建、管理和监控游戏服务器容器

**测试覆盖**:
- 容器管理（创建、启动、停止、删除）
- 代码上传验证（Python、JavaScript、HTML）
- 健康检查（响应格式、状态查询）
- 资源管理（内存、CPU、端口）
- API 端点（错误处理、响应格式）
- 自动注册（服务器自动注册到撮合服务）

**测试数量**: 28+ 个（15+ 单元 + 13+ 集成）

**运行方式**:
```bash
cd TEST/game_server_factory
python3 -m pytest . -v --tb=short
```

**关键测试**:
- `test_api_endpoints.py` - API 端点测试
- `test_container_creation_deployment.py` - 容器创建测试
- `test_docker_integration.py` - Docker 集成测试

---

### Matchmaker Service (撮合服务)

**位置**: `TEST/matchmaker_service/`

**功能**: 负责房间管理、玩家匹配和心跳检测

**测试覆盖**:
- 房间管理（创建、加入、离开、删除）
- 玩家匹配（配对算法、匹配规则）
- 心跳检测（玩家在线状态、超时处理）
- 定期清理（过期房间清理、资源释放）
- API 端点（错误处理、响应格式）

**测试数量**: 7+ 个（4+ 单元 + 3+ 集成）

**运行方式**:
```bash
cd TEST/matchmaker_service
python3 -m pytest . -v --tb=short
```

**关键测试**:
- `test_room_list_query.py` - 房间列表查询测试
- `test_matchmaker_integration.py` - 撮合集成测试

---

### Game Server Template (游戏服务器模板)

**位置**: `TEST/game_server_template/`

**功能**: 游戏服务器的标准模板，包含 WebSocket 通信和游戏操作

**测试覆盖**:
- WebSocket 通信（连接、消息、断开）
- 游戏操作（移动、攻击、交互）
- 自动注册（启动时自动注册到撮合服务）
- 配置参数（验证、默认值）
- API 错误处理（错误响应格式）
- 健康检查（响应格式、状态查询）

**测试数量**: 8+ 个（7+ 单元 + 1+ 集成）

**运行方式**:
```bash
cd TEST/game_server_template
npm test
```

**关键测试**:
- `config-parameters.property.test.js` - 配置参数属性测试
- `websocket.property.test.js` - WebSocket 属性测试

---

### Mobile App (移动应用)

**位置**: `TEST/mobile_app/`

**功能**: Flutter 开发的游戏客户端应用

**测试覆盖**:
- 配置参数（验证、默认值）
- 房间信息显示（完整性、格式）
- 实时状态更新（推送、刷新）
- API 服务集成（连接、请求、响应）
- 代码上传生命周期（选择、上传、验证、创建服务器）
- Widget 测试（UI 组件、交互）

**测试数量**: 7+ 个（3+ 单元 + 4+ 集成）

**运行方式**:
```bash
cd TEST/mobile_app
flutter test
```

**关键测试**:
- `config_parameters_property_test.dart` - 配置参数属性测试
- `api_service_integration_test.dart` - API 服务集成测试

**集成测试前置条件**:
```bash
# 启动后端服务
docker-compose up -d matchmaker game-server-factory

# 运行集成测试
flutter test --tags=integration

# 停止后端服务
docker-compose down
```

---

## 🔧 测试框架和工具

### Python 测试

**框架**: pytest  
**版本**: 7.x+

**常用命令**:
```bash
# 运行所有测试
pytest . -v

# 运行特定文件
pytest test_api_endpoints.py -v

# 运行特定测试
pytest test_api_endpoints.py::test_health_check -v

# 显示覆盖率
pytest . --cov=. --cov-report=html

# 运行超时测试
pytest . --timeout=120
```

### JavaScript 测试

**框架**: Jest  
**版本**: 29.x+

**常用命令**:
```bash
# 运行所有测试
npm test

# 运行特定文件
npm test -- health-check-response.property.test.js

# 监视模式
npm test -- --watch

# 显示覆盖率
npm test -- --coverage
```

### Dart 测试

**框架**: Flutter Test  
**版本**: 3.x+

**常用命令**:
```bash
# 运行所有测试
flutter test

# 运行特定文件
flutter test config_parameters_property_test.dart

# 排除集成测试
flutter test --exclude-tags=integration

# 显示覆盖率
flutter test --coverage
```

---

## 📈 测试类型详解

### 单元测试 (Unit Tests)

**目的**: 测试单个函数或方法的正确性

**特点**:
- 快速执行
- 不依赖外部服务
- 高代码覆盖率
- 易于调试

**示例**:
```python
def test_validate_file_size():
    """测试文件大小验证"""
    assert validate_file_size(1024) == True
    assert validate_file_size(1024*1024*2) == False
```

### 集成测试 (Integration Tests)

**目的**: 测试多个组件的交互

**特点**:
- 验证端到端流程
- 可能依赖外部服务
- 执行较慢
- 发现系统级问题

**示例**:
```python
def test_upload_and_create_server():
    """测试上传代码并创建服务器的完整流程"""
    # 1. 上传代码
    # 2. 创建服务器
    # 3. 验证服务器状态
```

### 属性测试 (Property Tests)

**目的**: 验证代码的不变量和属性

**特点**:
- 使用随机数据生成
- 发现边界情况
- 验证数学性质
- 提高代码健壮性

**示例**:
```python
@given(st.integers(min_value=0, max_value=100))
def test_player_count_valid(count):
    """验证玩家数量始终有效"""
    room = create_room(max_players=100)
    assert room.add_player(count) or count > 100
```

---

## ✅ 测试检查清单

运行测试前，请检查：

- [ ] 所有依赖已安装
- [ ] 环境变量已配置
- [ ] Docker 服务已启动（如需要）
- [ ] 数据库已初始化（如需要）
- [ ] 端口未被占用

---

## 🐛 常见问题

### Q: 如何运行单个测试？

**A**: 使用 `-k` 参数指定测试名称：
```bash
pytest . -k "test_health_check" -v
```

### Q: 如何查看测试覆盖率？

**A**: 使用 `--cov` 参数：
```bash
pytest . --cov=. --cov-report=html
```

### Q: 如何跳过某些测试？

**A**: 使用 `@pytest.mark.skip` 装饰器：
```python
@pytest.mark.skip(reason="暂时跳过")
def test_something():
    pass
```

### Q: 如何设置测试超时？

**A**: 使用 `--timeout` 参数：
```bash
pytest . --timeout=120
```

### Q: 如何并行运行测试？

**A**: 使用 `pytest-xdist` 插件：
```bash
pytest . -n auto
```

---

## 📝 测试命名规范

### Python 测试文件

```
test_<功能>.py              # 单元测试
test_<功能>_integration.py  # 集成测试
test_<功能>_property.py     # 属性测试
```

### Python 测试函数

```
def test_<功能>_<场景>():
    """测试描述"""
    pass
```

### JavaScript 测试文件

```
<功能>.test.js              # 单元测试
<功能>.integration.test.js  # 集成测试
<功能>.property.test.js     # 属性测试
```

### Dart 测试文件

```
<功能>_test.dart            # 单元测试
<功能>_integration_test.dart # 集成测试
```

---

## 🔗 相关资源

- **项目 README**: `../README.md`
- **架构文档**: `../docs/explanation/architecture.md`
- **测试策略**: `../.kiro_workspace/docs/test_strategy_comprehensive.md`
- **快速参考**: `../.kiro_workspace/docs/QUICK_REFERENCE.md`

---

## 📞 获取帮助

### 查看模块特定说明

- [Game Server Factory](game_server_factory/README.md)
- [Matchmaker Service](matchmaker_service/README.md)
- [Game Server Template](game_server_template/README.md)
- [Mobile App](mobile_app/README.md)

### 查看故障排查

- 故障排查指南: `../.kiro_workspace/docs/troubleshooting_guide.md`

---

**维护者**: Kiro AI Agent  
**最后更新**: 2025-12-21  
**状态**: ✅ 完成

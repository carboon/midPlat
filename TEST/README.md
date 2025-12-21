# 📋 TEST 目录 - 测试用例管理

**最后更新**: 2025-12-21

---

## 📁 目录结构

```
TEST/
├── README.md (本文件)
├── USAGE.md (使用说明)
├── game_server_factory/
│   ├── README.md
│   ├── unit/
│   ├── integration/
│   └── property/
├── matchmaker_service/
│   ├── README.md
│   ├── unit/
│   ├── integration/
│   └── property/
├── game_server_template/
│   ├── README.md
│   ├── unit/
│   ├── integration/
│   └── property/
├── mobile_app/
│   ├── README.md
│   ├── unit/
│   ├── integration/
│   └── property/
└── scripts/
    ├── run_all_tests.sh
    └── run_component_tests.sh
```

---

## 🎯 目录说明

### 按模块分类

#### 1. **game_server_factory/** - 游戏服务器工厂测试
- **unit/** - 单元测试
- **integration/** - 集成测试
- **property/** - 属性测试

#### 2. **matchmaker_service/** - 撮合服务测试
- **unit/** - 单元测试
- **integration/** - 集成测试
- **property/** - 属性测试

#### 3. **game_server_template/** - 游戏服务器模板测试
- **unit/** - 单元测试
- **integration/** - 集成测试
- **property/** - 属性测试

#### 4. **mobile_app/** - 移动应用测试
- **unit/** - 单元测试
- **integration/** - 集成测试
- **property/** - 属性测试

#### 5. **scripts/** - 测试脚本
- 统一的测试运行脚本
- 跨模块测试协调

---

## 🚀 快速开始

### 前置条件

在运行测试前，请确保：

1. **Python 依赖已安装**
   ```bash
   pip install -r game_server_factory/requirements-test.txt
   pip install -r matchmaker_service/matchmaker/requirements.txt
   ```

2. **Node.js 依赖已安装**
   ```bash
   cd TEST/game_server_template
   npm install
   ```

3. **Flutter 已安装**（用于移动应用测试）
   ```bash
   flutter --version
   ```

4. **Docker 已启动**（用于集成测试）
   ```bash
   docker ps
   ```

### 运行所有测试

```bash
# 从项目根目录运行
python3 run_all_tests.py
```

### 运行特定模块测试

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

### 运行特定类型测试

```bash
# 仅运行单元测试
bash TEST/scripts/run_component_tests.sh factory unit

# 仅运行集成测试
bash TEST/scripts/run_component_tests.sh factory integration

# 仅运行属性测试
bash TEST/scripts/run_component_tests.sh factory property
```

### 快速验证

```bash
# 验证 TEST 目录结构
python3 TEST/scripts/verify_test_completeness.py

# 验证路径映射
python3 TEST/scripts/verify_path_mapping.py

# 验证清理完成
python3 TEST/scripts/verify_cleanup_completion.py
```

---

## 📊 测试统计

| 模块 | 单元测试 | 集成测试 | 属性测试 | 总计 |
|------|---------|---------|---------|------|
| Game Server Factory | 15+ | 13+ | 10+ | 38+ |
| Matchmaker Service | 4+ | 3+ | 5+ | 12+ |
| Game Server Template | 7+ | 1+ | 6+ | 14+ |
| Mobile App | 3+ | 4+ | 0 | 7+ |
| **总计** | **29+** | **21+** | **21+** | **71+** |

**注**: 测试数量会随着项目发展而增加。详见各模块 README.md。

---

## 📖 详细文档

- **[USAGE.md](USAGE.md)** - 详细的使用说明
- **[game_server_factory/README.md](game_server_factory/README.md)** - 工厂模块测试说明
- **[matchmaker_service/README.md](matchmaker_service/README.md)** - 撮合服务测试说明
- **[game_server_template/README.md](game_server_template/README.md)** - 模板模块测试说明
- **[mobile_app/README.md](mobile_app/README.md)** - 移动应用测试说明

---

## ✅ 测试类型说明

### 单元测试 (Unit Tests)
- 测试单个函数或方法
- 不依赖外部服务
- 快速执行
- 高覆盖率

### 集成测试 (Integration Tests)
- 测试多个组件的交互
- 可能依赖外部服务
- 验证端到端流程
- 较慢执行

### 属性测试 (Property Tests)
- 基于属性的测试
- 使用 Hypothesis/QuickCheck
- 验证不变量
- 发现边界情况

---

## 🔧 测试框架

| 模块 | 框架 | 版本 |
|------|------|------|
| Game Server Factory | pytest | 7.x |
| Matchmaker Service | pytest | 7.x |
| Game Server Template | Jest | 29.x |
| Mobile App | Flutter Test | 3.x |

---

## 📝 测试命名规范

### Python 测试
```
test_<功能>_<场景>.py
test_<功能>_<场景>_property.py
```

### JavaScript 测试
```
<功能>.property.test.js
<功能>.integration.test.js
```

### Dart 测试
```
<功能>_test.dart
<功能>_integration_test.dart
```

---

## 🎯 测试覆盖目标

- **单元测试**: 80%+ 代码覆盖
- **集成测试**: 关键流程覆盖
- **属性测试**: 核心算法验证

---

## 📚 相关文档

- **项目 README**: `../README.md`
- **架构文档**: `../docs/explanation/architecture.md`
- **API 参考**: `../docs/reference/api-reference.md`
- **测试策略**: `../.kiro_workspace/docs/test_strategy_comprehensive.md`

---

## 🔗 快速链接

- [使用说明](USAGE.md)
- [Game Server Factory 测试](game_server_factory/README.md)
- [Matchmaker Service 测试](matchmaker_service/README.md)
- [Game Server Template 测试](game_server_template/README.md)
- [Mobile App 测试](mobile_app/README.md)

---

**维护者**: Kiro AI Agent  
**最后更新**: 2025-12-21  
**状态**: ✅ 完成

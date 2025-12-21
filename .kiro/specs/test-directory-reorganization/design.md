# 测试目录重组设计文档

## 概述

本设计文档描述了如何将分散在各个模块中的测试文件集中到 `TEST` 目录，并确保所有测试能够正确执行。设计的核心目标是：

1. 集中管理所有测试文件
2. 确保测试路径映射正确
3. 验证所有测试执行成功
4. 清理原有的模块测试目录
5. 更新测试执行脚本

## 架构

### 当前状态

```
项目根目录/
├── game_server_factory/
│   └── tests/                    # 原有测试目录
│       ├── test_api_endpoints.py
│       ├── test_*.py
│       └── integration/
├── matchmaker_service/
│   └── matchmaker/
│       └── tests/                # 原有测试目录
│           ├── test_*.py
│           └── conftest.py
├── game_server_template/
│   └── tests/                    # 原有测试目录
│       ├── *.test.js
│       └── integration/
├── mobile_app/
│   └── universal_game_client/
│       └── test/                 # 原有测试目录
│           ├── *_test.dart
│           └── *_integration_test.dart
└── run_all_tests.py              # 主测试脚本
```

### 目标状态

```
项目根目录/
├── TEST/                         # 新的集中测试目录
│   ├── README.md
│   ├── USAGE.md
│   ├── game_server_factory/
│   │   ├── README.md
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_api_endpoints.py
│   │   │   ├── test_*.py
│   │   │   └── ...
│   │   ├── integration/
│   │   │   ├── test_*.py
│   │   │   └── ...
│   │   └── property/
│   │       └── ...
│   ├── matchmaker_service/
│   │   ├── README.md
│   │   ├── conftest.py
│   │   ├── unit/
│   │   │   ├── test_*.py
│   │   │   └── ...
│   │   ├── integration/
│   │   │   ├── test_*.py
│   │   │   └── ...
│   │   └── property/
│   │       └── ...
│   ├── game_server_template/
│   │   ├── README.md
│   │   ├── unit/
│   │   │   ├── *.test.js
│   │   │   └── ...
│   │   ├── integration/
│   │   │   ├── *.integration.test.js
│   │   │   └── ...
│   │   └── property/
│   │       ├── *.property.test.js
│   │       └── ...
│   ├── mobile_app/
│   │   ├── README.md
│   │   ├── unit/
│   │   │   ├── *_test.dart
│   │   │   └── ...
│   │   ├── integration/
│   │   │   ├── *_integration_test.dart
│   │   │   └── ...
│   │   └── property/
│   │       └── ...
│   └── scripts/
│       ├── run_all_tests.sh
│       └── run_component_tests.sh
├── game_server_factory/          # 原有目录（tests/ 已删除）
├── matchmaker_service/           # 原有目录（tests/ 已删除）
├── game_server_template/         # 原有目录（tests/ 已删除）
├── mobile_app/                   # 原有目录（test/ 已删除）
└── run_all_tests.py              # 更新后的主测试脚本
```

## 组件和接口

### 1. 测试文件迁移

**目的**: 将所有测试文件从模块目录迁移到 TEST 目录

**实现方式**:
- 按模块和测试类型（unit/integration/property）组织测试文件
- 保持文件名和内容不变
- 复制 conftest.py 和其他配置文件

**关键点**:
- 测试文件的相对导入路径需要调整
- 需要处理不同语言的测试框架（pytest, Jest, Flutter Test）

### 2. 路径映射验证

**目的**: 确保测试文件能够正确访问源代码和依赖

**实现方式**:
- 在 TEST 目录下创建 conftest.py（Python）或等效配置
- 配置 Python path 以支持导入源代码
- 配置 Node.js 和 Dart 的模块解析路径

**关键点**:
- 需要处理相对路径的调整
- 需要支持不同的工作目录

### 3. 测试执行脚本更新

**目的**: 更新测试执行脚本以使用新的 TEST 目录

**实现方式**:
- 更新 `run_all_tests.py` 以从 TEST 目录运行测试
- 更新 `TEST/scripts/run_all_tests.sh` 以支持新的目录结构
- 更新 `TEST/scripts/run_component_tests.sh` 以支持模块特定的测试

**关键点**:
- 需要正确设置工作目录
- 需要处理不同语言的测试命令

### 4. 原有目录清理

**目的**: 删除原有模块目录中已迁移的测试文件

**实现方式**:
- 验证 TEST 目录中存在对应的测试文件
- 删除原有模块目录中的测试文件
- 删除空的测试目录

**关键点**:
- 需要保留必要的配置文件
- 需要验证清理后测试仍能执行

## 数据模型

### 测试文件映射表

```python
{
    "game_server_factory": {
        "unit": [
            "test_api_endpoints.py",
            "test_api_error_response_format_property.py",
            "test_auto_server_registration.py",
            # ... 更多文件
        ],
        "integration": [
            "test_container_status_monitoring.py",
            "test_docker_integration.py",
            # ... 更多文件
        ]
    },
    "matchmaker_service": {
        "unit": [
            "test_api_error_response_format_property.py",
            "test_config_parameters_property.py",
            # ... 更多文件
        ],
        "integration": [
            "test_matchmaker.py",
            "test_room_list_query.py",
            # ... 更多文件
        ]
    },
    # ... 其他模块
}
```

## 正确性属性

一个属性是一个特征或行为，应该在系统的所有有效执行中保持真实。属性充当人类可读规范和机器可验证正确性保证之间的桥梁。

### 属性 1: 测试文件完整性

**验证**: 需求 1.1, 1.2, 1.3

对于任何模块，TEST 目录中的测试文件数量应等于原有模块目录中的测试文件数量。

```
For all modules M:
  count(TEST/M/*/test_*.py) == count(original_module/M/tests/test_*.py)
```

### 属性 2: 测试执行成功率

**验证**: 需求 1.1, 1.2, 1.3

所有从 TEST 目录运行的测试应该与从原有目录运行的测试具有相同的执行结果。

```
For all test files T in TEST directory:
  result(run_test_from_TEST(T)) == result(run_test_from_original(T))
```

### 属性 3: 路径映射正确性

**验证**: 需求 2.1, 2.2, 2.3, 2.4

测试文件中的所有导入语句应该能够正确解析，无论工作目录是项目根目录还是 TEST 目录。

```
For all test files T in TEST directory:
  For all imports I in T:
    resolve_import(I, cwd=project_root) == resolve_import(I, cwd=TEST_dir)
```

### 属性 4: 目录清理完整性

**验证**: 需求 3.1, 3.2, 3.3, 3.4

清理后，原有模块目录中不应存在已迁移到 TEST 目录的测试文件。

```
For all modules M:
  For all test files T in original_module/M/tests:
    if exists(TEST/M/*/T):
      not exists(original_module/M/tests/T)
```

### 属性 5: 脚本执行一致性

**验证**: 需求 4.1, 4.2, 4.3, 4.4

无论使用哪个测试脚本（run_all_tests.py 或 run_all_tests.sh），测试结果应该相同。

```
For all test suites S:
  result(run_all_tests.py S) == result(run_all_tests.sh S)
```

## 错误处理

### 路径错误

**场景**: 测试文件无法找到源代码模块

**处理方式**:
- 检查 Python path 配置
- 验证相对路径是否正确
- 提供清晰的错误消息

### 依赖缺失

**场景**: 测试运行时缺少依赖

**处理方式**:
- 检查依赖是否已安装
- 提供安装命令
- 记录详细的错误信息

### 文件冲突

**场景**: 清理时发现文件冲突

**处理方式**:
- 备份原有文件
- 记录冲突信息
- 提示用户手动处理

## 测试策略

### 单元测试

**目的**: 验证单个组件的正确性

**测试范围**:
- 文件迁移的完整性
- 路径映射的正确性
- 脚本执行的正确性

**示例**:
```python
def test_test_files_migrated():
    """验证所有测试文件已迁移到 TEST 目录"""
    # 检查 TEST 目录中的文件数量
    # 检查原有目录中的文件数量
    # 验证两者相等
    pass

def test_imports_resolve_correctly():
    """验证测试文件中的导入能够正确解析"""
    # 加载测试文件
    # 验证所有导入都能解析
    pass
```

### 集成测试

**目的**: 验证整个测试系统的正确性

**测试范围**:
- 完整的测试执行流程
- 跨模块的测试协调
- 测试结果的一致性

**示例**:
```python
def test_all_tests_pass_from_test_directory():
    """验证从 TEST 目录运行所有测试都通过"""
    # 运行 run_all_tests.py
    # 验证所有测试都通过
    pass

def test_cleanup_preserves_test_functionality():
    """验证清理后测试仍能正确执行"""
    # 清理原有目录
    # 运行测试
    # 验证测试通过
    pass
```

### 属性测试

**目的**: 验证系统的不变量

**测试范围**:
- 文件完整性
- 执行结果一致性
- 路径映射正确性

**示例**:
```python
@given(st.sampled_from(MODULES))
def test_test_count_consistency(module):
    """验证 TEST 目录中的测试文件数量与原有目录一致"""
    test_count_in_test_dir = count_test_files(f"TEST/{module}")
    test_count_in_original = count_test_files(f"{module}/tests")
    assert test_count_in_test_dir == test_count_in_original
```

## 部署考虑

### 向后兼容性

- 保持原有的测试命令可用
- 支持从原有目录运行测试（如果需要）
- 提供迁移指南

### 监控和日志

- 记录所有文件操作
- 记录测试执行结果
- 提供详细的错误信息

### 回滚计划

- 备份原有的测试目录
- 记录所有更改
- 提供回滚脚本

## 相关文件

- `TEST/README.md` - TEST 目录概览
- `TEST/USAGE.md` - 测试使用说明
- `run_all_tests.py` - 主测试执行脚本
- `TEST/scripts/run_all_tests.sh` - 测试运行脚本
- `TEST/scripts/run_component_tests.sh` - 组件测试脚本

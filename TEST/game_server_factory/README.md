# 🏭 Game Server Factory 测试

**模块**: 游戏服务器工厂  
**位置**: `TEST/game_server_factory/`  
**最后更新**: 2025-12-21

---

## 📋 概述

Game Server Factory 是负责创建、管理和监控游戏服务器容器的核心模块。本目录包含该模块的所有测试用例。

---

## 📁 目录结构

```
game_server_factory/
├── README.md (本文件)
├── unit/
│   ├── test_api_endpoints.py
│   ├── test_config_parameters_property.py
│   ├── test_health_check_response_property.py
│   ├── test_health_check_status_query_property.py
│   ├── test_container_status_query_property.py
│   ├── test_api_error_response_format_property.py
│   ├── test_comprehensive_error_handling_property.py
│   ├── test_html_game_file_validation_property.py
│   ├── test_html_game_file_validation_error_handling_property.py
│   ├── test_code_upload_validation.py
│   ├── test_container_creation_deployment.py
│   ├── test_container_lifecycle_control.py
│   ├── test_auto_server_registration.py
│   ├── test_server_details_display.py
│   └── test_user_server_list_management.py
├── integration/
│   ├── test_integration.py
│   ├── test_end_to_end_integration.py
│   ├── test_port_fix_complete.py
│   ├── test_docker_integration.py
│   ├── test_docker_simple.py
│   ├── test_end_to_end.py
│   ├── test_system_integration.py
│   ├── test_system_integration_comprehensive.py
│   ├── test_system_resource_management.py
│   ├── test_container_status_monitoring.py
│   ├── test_health_monitoring_comprehensive.py
│   ├── test_security_integration.py
│   └── test_upload.py
└── property/
    └── (属性测试文件)
```

---

## 🧪 测试覆盖

### 单元测试 (15+ 个)

| 测试 | 功能 | 描述 | 状态 |
|------|------|------|------|
| test_api_endpoints | API 端点 | 验证 API 端点的正确性 | ✅ |
| test_config_parameters_property | 配置参数 | 验证配置参数的有效性 | ✅ |
| test_health_check_response_property | 健康检查响应 | 验证健康检查响应格式 | ✅ |
| test_health_check_status_query_property | 健康检查状态查询 | 验证健康检查状态查询 | ✅ |
| test_container_status_query_property | 容器状态查询 | 验证容器状态查询 | ✅ |
| test_api_error_response_format_property | API 错误响应格式 | 验证 API 错误响应格式 | ✅ |
| test_comprehensive_error_handling_property | 错误处理 | 验证全面的错误处理 | ✅ |
| test_html_game_file_validation_property | HTML 文件验证 | 验证 HTML 游戏文件 | ✅ |
| test_html_game_file_validation_error_handling_property | HTML 文件验证错误处理 | 验证 HTML 文件验证错误处理 | ✅ |
| test_code_upload_validation | 代码上传验证 | 验证代码上传功能 | ✅ |
| test_container_creation_deployment | 容器创建部署 | 验证容器创建和部署 | ✅ |
| test_container_lifecycle_control | 容器生命周期控制 | 验证容器生命周期管理 | ✅ |
| test_auto_server_registration | 自动服务器注册 | 验证自动注册功能 | ✅ |
| test_server_details_display | 服务器详情显示 | 验证服务器详情显示 | ✅ |
| test_user_server_list_management | 用户服务器列表管理 | 验证用户服务器列表管理 | ✅ |

### 集成测试 (13+ 个)

| 测试 | 功能 | 描述 | 状态 |
|------|------|------|------|
| test_integration | 基础集成 | 基础集成测试 | ✅ |
| test_end_to_end_integration | 端到端集成 | 完整的端到端集成测试 | ✅ |
| test_port_fix_complete | 端口修复 | 验证端口修复功能 | ✅ |
| test_docker_integration | Docker 集成 | Docker 集成测试 | ✅ |
| test_docker_simple | Docker 简单测试 | Docker 简单功能测试 | ✅ |
| test_end_to_end | 端到端测试 | 端到端功能测试 | ✅ |
| test_system_integration | 系统集成 | 系统级集成测试 | ✅ |
| test_system_integration_comprehensive | 系统集成综合 | 综合系统集成测试 | ✅ |
| test_system_resource_management | 系统资源管理 | 系统资源管理测试 | ✅ |
| test_container_status_monitoring | 容器状态监控 | 容器状态监控测试 | ✅ |
| test_health_monitoring_comprehensive | 健康监控综合 | 综合健康监控测试 | ✅ |
| test_security_integration | 安全集成 | 安全功能集成测试 | ✅ |
| test_upload | 上传测试 | 文件上传功能测试 | ✅ |

---

## 🚀 运行测试

### 运行所有测试

```bash
cd TEST/game_server_factory
python3 -m pytest . -v --tb=short
```

### 运行单元测试

```bash
cd TEST/game_server_factory
python3 -m pytest unit/ -v
```

### 运行集成测试

```bash
cd TEST/game_server_factory
python3 -m pytest integration/ -v
```

### 运行特定测试

```bash
cd TEST/game_server_factory
python3 -m pytest unit/test_api_endpoints.py -v
```

### 运行特定测试函数

```bash
cd TEST/game_server_factory
python3 -m pytest unit/test_api_endpoints.py::test_health_check -v
```

### 显示覆盖率

```bash
cd TEST/game_server_factory
python3 -m pytest . --cov=. --cov-report=html
```

---

## 📊 测试统计

- **总测试数**: 28+
- **单元测试**: 15+
- **集成测试**: 13+
- **通过率**: 95%+

---

## 🔧 依赖

### Python 依赖

```
pytest>=7.0
pytest-timeout>=2.1.0
pytest-cov>=4.0
hypothesis>=6.0
fastapi>=0.95
httpx>=0.23
docker>=6.0
```

### 系统依赖

- Python 3.9+
- Docker
- Docker Compose

---

## 📝 测试说明

### 单元测试

单元测试验证各个函数和方法的正确性，不依赖外部服务。

**示例**:
```python
def test_validate_file_size():
    """测试文件大小验证"""
    assert validate_file_size(1024) == True
    assert validate_file_size(1024*1024*2) == False
```

### 集成测试

集成测试验证多个组件的交互，可能依赖 Docker 和其他服务。

**示例**:
```python
def test_create_and_monitor_container():
    """测试创建和监控容器的完整流程"""
    # 1. 创建容器
    # 2. 验证容器状态
    # 3. 监控容器健康
    # 4. 清理容器
```

---

## 🐛 常见问题

### Q: Docker 连接失败

**A**: 确保 Docker 守护进程正在运行：
```bash
docker ps
```

### Q: 测试超时

**A**: 增加超时时间：
```bash
pytest . --timeout=300
```

### Q: 端口被占用

**A**: 检查并释放端口：
```bash
lsof -i :8080
kill -9 <PID>
```

---

## 📚 相关文档

- **模块代码**: `../../game_server_factory/`
- **API 参考**: `../../docs/reference/api-reference.md`
- **架构文档**: `../../docs/explanation/architecture.md`

---

**维护者**: Kiro AI Agent  
**最后更新**: 2025-12-21  
**状态**: ✅ 完成

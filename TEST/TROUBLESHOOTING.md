# 📖 TEST 目录故障排查指南

**最后更新**: 2025-12-21

---

## 🎯 快速诊断

### 验证 TEST 目录结构

```bash
# 检查目录完整性
python3 TEST/scripts/verify_test_completeness.py

# 检查路径映射
python3 TEST/scripts/verify_path_mapping.py

# 检查清理完成
python3 TEST/scripts/verify_cleanup_completion.py
```

### 运行快速测试

```bash
# 运行所有测试
python3 run_all_tests.py

# 运行特定模块
bash TEST/scripts/run_component_tests.sh factory
bash TEST/scripts/run_component_tests.sh matchmaker
bash TEST/scripts/run_component_tests.sh template
bash TEST/scripts/run_component_tests.sh mobile
```

---

## 🐛 常见问题

### 1. 导入路径错误

**症状**:
```
ModuleNotFoundError: No module named 'game_server_factory'
ImportError: cannot import name 'validate_file_size' from 'game_server_factory'
```

**原因**:
- Python path 配置不正确
- 测试文件相对路径错误
- conftest.py 未正确配置

**解决方案**:

```bash
# 1. 检查 conftest.py 是否存在
ls -la TEST/game_server_factory/conftest.py

# 2. 验证 Python path 配置
python3 -c "import sys; print(sys.path)"

# 3. 从 TEST 目录运行测试
cd TEST/game_server_factory
python3 -m pytest unit/ -v

# 4. 或从项目根目录运行
cd /path/to/project
python3 -m pytest TEST/game_server_factory/unit/ -v

# 5. 检查导入语句
grep -r "from game_server_factory" TEST/game_server_factory/
grep -r "import game_server_factory" TEST/game_server_factory/
```

**修复步骤**:

```bash
# 确保 conftest.py 包含正确的 Python path 配置
cat TEST/game_server_factory/conftest.py

# 应该包含类似内容:
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

---

### 2. 测试文件未找到

**症状**:
```
ERROR collecting TEST/game_server_factory/unit/test_api_endpoints.py
No such file or directory
```

**原因**:
- 测试文件未迁移到 TEST 目录
- 文件名不匹配
- 目录结构不正确

**解决方案**:

```bash
# 1. 检查文件是否存在
find TEST -name "test_*.py" | head -20

# 2. 检查目录结构
tree TEST/game_server_factory/

# 3. 验证文件完整性
python3 TEST/scripts/verify_test_completeness.py

# 4. 列出所有测试文件
find TEST -type f -name "*.py" | grep test

# 5. 检查原有目录是否仍有测试文件
find game_server_factory -name "test_*.py" 2>/dev/null
```

**修复步骤**:

```bash
# 如果文件仍在原有目录，复制到 TEST 目录
cp game_server_factory/tests/test_*.py TEST/game_server_factory/unit/

# 验证复制成功
ls -la TEST/game_server_factory/unit/
```

---

### 3. 依赖缺失

**症状**:
```
ModuleNotFoundError: No module named 'pytest'
ModuleNotFoundError: No module named 'hypothesis'
```

**原因**:
- 依赖未安装
- 虚拟环境未激活
- 依赖版本不兼容

**解决方案**:

```bash
# 1. 检查 Python 版本
python3 --version  # 应该 >= 3.8

# 2. 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate  # Windows

# 3. 升级 pip
pip install --upgrade pip

# 4. 安装依赖
pip install -r game_server_factory/requirements-test.txt
pip install -r matchmaker_service/matchmaker/requirements.txt

# 5. 验证安装
python3 -m pytest --version
python3 -c "import hypothesis; print(hypothesis.__version__)"

# 6. 列出已安装的包
pip list | grep -E "pytest|hypothesis|fastapi"
```

---

### 4. Docker 相关错误

**症状**:
```
docker.errors.DockerException: Error while fetching server API version
ConnectionError: Error connecting to Docker daemon
```

**原因**:
- Docker 守护进程未运行
- Docker socket 权限问题
- Docker 未安装

**解决方案**:

```bash
# 1. 检查 Docker 状态
docker ps

# 2. 启动 Docker
# macOS:
open -a Docker

# Linux:
sudo systemctl start docker

# 3. 检查 Docker socket 权限
ls -la /var/run/docker.sock

# 4. 添加用户到 docker 组
sudo usermod -aG docker $USER
newgrp docker

# 5. 验证 Docker 连接
docker run hello-world

# 6. 检查 Docker 版本
docker --version
```

---

### 5. 网络配置错误

**症状**:
```
Error response from daemon: network game-network not found
```

**原因**:
- Docker 网络不存在
- Docker daemon 重启后网络丢失

**解决方案**:

```bash
# 1. 检查现有网络
docker network ls

# 2. 创建网络
docker network create game-network

# 3. 验证网络
docker network inspect game-network

# 4. 如果需要删除并重建
docker network rm game-network
docker network create game-network

# 5. 启动 Docker Compose 服务
docker-compose up -d

# 6. 验证容器连接
docker network inspect game-network
```

---

### 6. 端口占用

**症状**:
```
Error: listen EADDRINUSE: address already in use :::8000
```

**原因**:
- 端口已被其他进程占用
- 前一次测试的容器未完全停止

**解决方案**:

```bash
# 1. 检查占用的进程
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# 2. 停止占用的进程
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# 3. 停止所有 Docker 容器
docker-compose down -v

# 4. 清理悬挂的容器
docker container prune -f

# 5. 验证端口已释放
lsof -i :8000  # 应该无输出
```

---

### 7. 测试超时

**症状**:
```
FAILED - Timeout >300s
```

**原因**:
- 测试执行时间过长
- 网络连接缓慢
- 系统资源不足

**解决方案**:

```bash
# 1. 增加超时时间
cd TEST/game_server_factory
python3 -m pytest . --timeout=600 -v

# 2. 运行单个测试
python3 -m pytest unit/test_api_endpoints.py -v

# 3. 检查系统资源
free -h  # Linux
vm_stat  # macOS

# 4. 停止不必要的进程
docker-compose down

# 5. 清理 Docker 资源
docker system prune -a --volumes

# 6. 重新运行测试
python3 -m pytest . -v
```

---

### 8. 属性测试失败

**症状**:
```
Falsifying example: ...
AssertionError: ...
```

**原因**:
- 属性测试发现了代码中的 bug
- 测试生成器配置不正确
- 属性定义有问题

**解决方案**:

```bash
# 1. 查看失败的例子
python3 -m pytest test_*_property.py -v

# 2. 运行特定的属性测试
python3 -m pytest test_config_parameters_property.py::test_config_valid -v

# 3. 增加测试迭代次数
python3 -m pytest test_*_property.py -v --hypothesis-seed=0

# 4. 查看 Hypothesis 统计
python3 -m pytest test_*_property.py -v --hypothesis-show-statistics

# 5. 调试失败的例子
# 在测试中添加 print 语句
# 或使用 pdb 调试器
python3 -m pytest test_*_property.py -v -s --pdb
```

---

### 9. Node.js 测试失败

**症状**:
```
FAIL  config-parameters.property.test.js
```

**原因**:
- npm 依赖未安装
- Node.js 版本不兼容
- Jest 配置错误

**解决方案**:

```bash
# 1. 检查 Node.js 版本
node --version  # 应该 >= 14

# 2. 检查 npm 版本
npm --version  # 应该 >= 6

# 3. 清理依赖
cd TEST/game_server_template
rm -rf node_modules package-lock.json

# 4. 重新安装依赖
npm install

# 5. 运行测试
npm test

# 6. 查看 Jest 配置
cat jest.config.js

# 7. 运行特定测试
npm test -- config-parameters.property.test.js
```

---

### 10. Flutter 测试失败

**症状**:
```
FAIL: test/config_parameters_property_test.dart
```

**原因**:
- Flutter 依赖未安装
- 平台特定实现缺失
- 后端服务未启动（集成测试）

**解决方案**:

```bash
# 1. 检查 Flutter 版本
flutter --version

# 2. 检查 Dart 版本
dart --version

# 3. 清理 Flutter 缓存
cd TEST/mobile_app
flutter clean

# 4. 重新获取依赖
flutter pub get

# 5. 运行单元测试
flutter test --exclude-tags=integration

# 6. 运行集成测试（需要后端服务）
# 先启动后端服务
docker-compose up -d matchmaker game-server-factory

# 然后运行集成测试
flutter test --tags=integration

# 7. 查看详细输出
flutter test -v

# 8. 停止后端服务
docker-compose down
```

---

## 📋 检查清单

运行测试前，请检查：

- [ ] Python 版本 >= 3.8
- [ ] Node.js 版本 >= 14
- [ ] Flutter 版本 >= 3.0
- [ ] Docker 已安装并运行
- [ ] Docker 网络 `game-network` 已创建
- [ ] 所有依赖已安装
- [ ] TEST 目录结构完整
- [ ] 路径映射正确
- [ ] 原有模块目录中的测试文件已清理

---

## 🔍 诊断命令

### 验证环境

```bash
# 完整诊断
python3 TEST/scripts/verify_test_completeness.py
python3 TEST/scripts/verify_path_mapping.py
python3 TEST/scripts/verify_cleanup_completion.py

# 或使用快速脚本
bash .kiro_workspace/scripts/quick_test.sh --verify
```

### 查看日志

```bash
# 查看最新测试日志
tail -f .kiro_workspace/logs/test_execution.log

# 查看 Docker 日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs matchmaker
docker-compose logs game-server-factory
```

### 收集诊断信息

```bash
# 系统信息
uname -a

# Python 版本
python3 --version

# Node.js 版本
node --version

# Docker 版本
docker --version

# Flutter 版本
flutter --version

# 已安装的 Python 包
pip list

# 已安装的 npm 包
npm list -g

# Docker 状态
docker ps
docker network ls
docker volume ls
```

---

## 🔧 完整重置

如果以上方法都不能解决问题，执行完整重置：

```bash
# 1. 停止所有容器
docker-compose down -v

# 2. 清理所有 Docker 资源
docker system prune -a --volumes -f

# 3. 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true

# 4. 清理 Node.js 缓存
rm -rf TEST/game_server_template/node_modules
rm -rf TEST/game_server_template/package-lock.json
npm cache clean --force

# 5. 清理 Flutter 缓存
flutter clean

# 6. 重新创建网络
docker network create game-network

# 7. 重新安装依赖
pip install -r game_server_factory/requirements-test.txt
pip install -r matchmaker_service/matchmaker/requirements.txt
cd TEST/game_server_template && npm install && cd ../..
cd TEST/mobile_app && flutter pub get && cd ../..

# 8. 运行测试
python3 run_all_tests.py
```

---

## 📞 获取帮助

### 查看相关文档

- **TEST 目录概览**: `TEST/README.md`
- **使用说明**: `TEST/USAGE.md`
- **模块说明**: `TEST/*/README.md`
- **完整故障排查**: `../.kiro_workspace/docs/troubleshooting_guide.md`

### 运行诊断脚本

```bash
# 验证 TEST 目录完整性
python3 TEST/scripts/verify_test_completeness.py

# 验证路径映射
python3 TEST/scripts/verify_path_mapping.py

# 验证清理完成
python3 TEST/scripts/verify_cleanup_completion.py
```

### 查看日志

```bash
# 查看最新日志
tail -f .kiro_workspace/logs/test_execution.log

# 查看测试结果
cat .kiro_workspace/logs/test_results.json
```

---

**维护者**: Kiro AI Agent  
**最后更新**: 2025-12-21  
**状态**: ✅ 完成

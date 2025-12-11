# AI游戏平台 - 完整工程搭建指南

这是一个用于AI生成游戏的标准化平台，包含游戏服务器模板、撮合服务和通用客户端三大部分。

## 目录结构

```
.
├── game_server_template/          # 游戏服务器模板
│   ├── Dockerfile                 # Docker配置文件
│   ├── README.md                  # 服务器说明文档
│   ├── docker-compose.yml         # Docker编排文件
│   ├── package-lock.json          # npm依赖锁文件
│   ├── package.json               # npm包配置
│   ├── public/                    # 静态资源目录
│   │   └── index.html             # 主页
│   ├── .env                       # 服务器配置文件
│   └── server.js                  # 服务器主程序
│
├── matchmaker_service/            # 匹配服务
│   └── matchmaker/                # 匹配器模块
│       ├── Dockerfile             # Docker配置文件
│       ├── README.md              # 匹配服务说明文档
│       ├── docker-compose.yml     # Docker编排文件
│       ├── main.py                # 匹配服务主程序
│       ├── requirements.txt       # Python依赖列表
│       ├── .env                   # 服务配置文件
│       └── test_matchmaker.py     # 匹配服务测试
│
├── mobile_app/                    # 移动端应用
│   └── universal_game_client/     # Flutter游戏客户端
│       ├── README.md              # 客户端说明文档
│       ├── android/               # Android原生代码
│       ├── ios/                   # iOS原生代码
│       ├── lib/                   # Dart源代码
│       │   ├── app.dart           # 应用入口
│       │   ├── main.dart          # 主程序文件
│       │   ├── models/            # 数据模型
│       │   ├── providers/         # 状态管理
│       │   ├── routes/            # 路由管理
│       │   ├── screens/           # 页面组件
│       │   ├── services/          # 服务层
│       │   ├── theme/             # 主题配置
│       │   ├── utils/             # 工具类
│       │   └── widgets/           # 自定义组件
│       ├── .env                   # 客户端配置文件
│       └── pubspec.yaml           # Flutter依赖配置
```

## 1. 环境准备

### 1.1 系统要求
- macOS 10.15+ / Windows 10+ / Ubuntu 18.04+
- 至少8GB RAM
- 至少20GB可用磁盘空间

### 1.2 开发工具安装

#### Python环境 (匹配服务)
```bash
# 安装Python 3.8+
# 推荐使用Homebrew (macOS)
brew install python

# 或使用apt (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip

# 或使用choco (Windows)
choco install python
```

#### Node.js环境 (游戏服务器)
```bash
# 推荐使用nvm管理Node.js版本
# 安装nvm (macOS/Linux)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash

# 安装Node.js LTS版本
nvm install --lts
nvm use --lts

# 或直接安装 (Windows)
choco install nodejs
```

#### Flutter环境 (移动端应用)
```bash
# 1. 下载Flutter SDK
# 访问 https://flutter.dev/docs/get-started/install 下载对应平台的SDK

# 2. 配置环境变量
# macOS/Linux: 添加到 ~/.bashrc 或 ~/.zshrc
export PATH="$PATH:[FLUTTER_SDK_PATH]/bin"

# Windows: 添加到系统环境变量PATH

# 3. 验证安装
flutter doctor
```

## 2. 各模块配置

### 2.1 匹配服务配置

#### 环境变量
```bash
# 在 matchmaker_service/matchmaker/.env 文件中配置
PYTHONUNBUFFERED=1
HOST=0.0.0.0
PORT=8000
HEARTBEAT_TIMEOUT=30
CLEANUP_INTERVAL=10
```

#### Docker配置
```yaml
# matchmaker_service/matchmaker/docker-compose.yml
version: '3.8'
services:
  matchmaker:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
```

### 2.2 游戏服务器配置

#### 环境变量
```bash
# 在 game_server_template/.env 文件中配置
MATCHMAKER_URL=http://localhost:8000
ROOM_NAME=默认房间
ROOM_PASSWORD=
PORT=8080
HEARTBEAT_INTERVAL=25000
RETRY_INTERVAL=5000
```

#### Docker配置
```yaml
# game_server_template/docker-compose.yml
version: '3.8'
services:
  game-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      - MATCHMAKER_URL=http://host.docker.internal:8000
      - ROOM_NAME=AI游戏房间
      - ROOM_PASSWORD=123456
```

### 2.3 移动端应用配置

#### 环境变量
```bash
# 在 mobile_app/universal_game_client/.env 文件中配置
MATCHMAKER_URL=http://127.0.0.1:8000
APP_NAME=Universal Game Client
ROOM_REFRESH_INTERVAL=30
```

#### 网络配置
```dart
// mobile_app/universal_game_client/lib/utils/constants.dart
// 配置已通过环境变量动态加载
```

#### 权限配置
```xml
<!-- Android: android/app/src/main/AndroidManifest.xml -->
<uses-permission android:name="android.permission.INTERNET" />

<!-- iOS: ios/Runner/Info.plist -->
<key>NSAppTransportSecurity</key>
<dict>
    <key>NSAllowsArbitraryLoads</key>
    <true/>
</dict>
```

## 3. 服务启动步骤

### 3.1 启动顺序
1. 匹配服务 (matchmaker_service)
2. 游戏服务器 (game_server_template)
3. 移动端应用 (mobile_app/universal_game_client)

### 3.2 匹配服务启动

#### 本地运行方式
```bash
# 1. 进入目录
cd matchmaker_service/matchmaker

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动服务
python main.py
```

#### Docker运行方式
```bash
# 1. 进入目录
cd matchmaker_service/matchmaker

# 2. 构建并启动
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

### 3.3 游戏服务器启动

#### 本地运行方式
```bash
# 1. 进入目录
cd game_server_template

# 2. 安装依赖
npm install

# 3. 启动服务
npm start
```

#### Docker运行方式
```bash
# 1. 进入目录
cd game_server_template

# 2. 构建并启动
docker-compose up --build
```

### 3.4 移动端应用启动

#### 开发模式运行
```bash
# 1. 进入目录
cd mobile_app/universal_game_client

# 2. 获取依赖
flutter pub get

# 3. 运行应用
flutter run
```

#### 构建发布版本
```bash
# macOS
flutter build macos

# Android
flutter build apk

# iOS
flutter build ios
```

## 4. 验证服务正常运行

### 4.1 匹配服务验证
```bash
# 检查服务状态
curl http://localhost:8000/

# 预期响应
{"service":"Game Matchmaker","version":"1.0.0","status":"running","active_servers":1}

# 检查服务器列表
curl http://localhost:8000/servers

# 预期响应
[{"server_id":"localhost:8080","ip":"localhost","port":8080,"name":"默认房间","max_players":20,"current_players":0,"metadata":{},"last_heartbeat":"2025-12-11T15:00:19.837859","uptime":1090}]
```

### 4.2 游戏服务器验证
```bash
# 检查游戏服务器状态
curl http://localhost:8080/

# 预期响应: HTML页面内容

# 检查WebSocket连接
# 可使用浏览器开发者工具查看WebSocket连接状态
```

### 4.3 移动端应用验证
1. 应用成功启动，显示主界面
2. 能够加载房间列表
3. 能够连接到游戏服务器
4. 能够正常进行游戏交互

## 5. 常见问题排查

### 5.1 端口冲突
```bash
# 查找占用端口的进程
lsof -i :8000  # 匹配服务端口
lsof -i :8080  # 游戏服务器端口

# 终止进程
kill [PID]
```

### 5.2 网络连接问题

#### macOS防火墙设置
1. 打开"系统偏好设置" → "安全性与隐私" → "防火墙"
2. 确保允许Flutter应用和Python应用通过防火墙

#### Docker网络问题
```bash
# 检查Docker网络
docker network ls

# 重建网络
docker-compose down
docker-compose up -d
```

### 5.3 依赖安装问题

#### Python虚拟环境问题
```bash
# 删除现有虚拟环境
rm -rf venv

# 重新创建
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Node.js依赖问题
```bash
# 清理缓存
npm cache clean --force

# 删除node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

#### Flutter依赖问题
```bash
# 清理Flutter缓存
flutter pub cache repair

# 清理项目
flutter clean
flutter pub get
```

### 5.4 权限问题

#### macOS应用权限
1. 打开"系统偏好设置" → "安全性与隐私" → "隐私"
2. 检查"完全磁盘访问权限"和"网络"部分
3. 确保Flutter应用有相应权限

### 5.5 国内网络优化

#### Flutter镜像源配置
```bash
# 添加到 ~/.bashrc 或 ~/.zshrc
export PUB_HOSTED_URL=https://pub.flutter-io.cn
export FLUTTER_STORAGE_BASE_URL=https://storage.flutter-io.cn
```

#### pip镜像源配置
```bash
# 创建 ~/.pip/pip.conf 文件
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/

[install]
trusted-host = mirrors.aliyun.com
```

## 6. API文档

### 6.1 匹配服务API
启动匹配服务后，可访问以下地址查看API文档：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 6.2 游戏服务器API
游戏服务器提供以下接口：
- WebSocket连接: 自动建立
- 静态文件服务: `/` (提供index.html)

## 7. 开发建议

### 7.1 代码风格
- Python: 遵循PEP 8规范
- JavaScript: 遵循Airbnb JavaScript Style Guide
- Dart: 遵循Effective Dart规范

### 7.2 版本控制
```bash
# 提交信息格式
git commit -m "feat: 添加新功能"
git commit -m "fix: 修复bug"
git commit -m "docs: 更新文档"
git commit -m "refactor: 重构代码"
```

### 7.3 测试策略
- 单元测试: 针对核心功能模块
- 集成测试: 验证模块间协作
- 端到端测试: 模拟用户操作流程

通过以上步骤，您应该能够成功搭建并运行整个AI游戏平台。如有任何问题，请参考各模块的详细文档或提交issue。
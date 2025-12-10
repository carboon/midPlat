# Flutter客户端网络连接问题解决记录

## 问题描述
在启动Flutter客户端时，应用界面显示"加载失败：ClientException with SocketException: Connection failed (OS Error: Operation not permitted, errno = 1), address = localhost, port = 8000, uri=http://localhost:8000/servers"错误。

## 问题原因分析
1. macOS系统安全机制限制了应用的网络访问权限
2. Flutter macOS应用的Entitlements配置不完整
3. App Sandbox限制了本地网络连接
4. URL解析可能存在DNS问题

## 解决方案

### 1. 网络权限配置
修改以下文件以添加必要的网络权限：

**文件路径**: `mobile_app/universal_game_client/macos/Runner/DebugProfile.entitlements`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>com.apple.security.app-sandbox</key>
	<false/>
	<key>com.apple.security.cs.allow-jit</key>
	<true/>
	<key>com.apple.security.network.server</key>
	<true/>
	<key>com.apple.security.network.client</key>
	<true/>
</dict>
</plist>
```

**文件路径**: `mobile_app/universal_game_client/macos/Runner/Release.entitlements`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>com.apple.security.app-sandbox</key>
	<false/>
	<key>com.apple.security.network.server</key>
	<true/>
	<key>com.apple.security.network.client</key>
	<true/>
</dict>
</plist>
```

关键修改点：
- 添加了`com.apple.security.network.client`权限以允许客户端网络访问
- 将`com.apple.security.app-sandbox`设置为`false`以禁用沙盒限制

### 2. URL配置优化
修改URL配置以避免DNS解析问题：

**文件路径**: `mobile_app/universal_game_client/lib/utils/constants.dart`
```dart
class Constants {
  static const String matchmakerUrl = 'http://127.0.0.1:8000';  // 使用127.0.0.1代替localhost
  static const String appName = 'Universal Game Client';
  static const int roomRefreshInterval = 30; // seconds
}
```

### 3. 确保后端服务正常运行
在启动客户端前，必须确保以下服务正在运行：

1. **匹配服务** (端口8000)
```bash
cd matchmaker_service/matchmaker
source venv/bin/activate
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

2. **游戏服务器** (端口8080)
```bash
cd game_server_template
npm start
```

验证服务状态：
```bash
# 检查匹配服务
curl http://127.0.0.1:8000/servers
```

### 4. 客户端构建和运行
```bash
cd mobile_app/universal_game_client
flutter clean
flutter pub get
flutter run -d macos
```

## 验证结果
通过以上修改，客户端能够成功连接到本地匹配服务并正确显示游戏房间列表。

## 预防措施
1. 在新的开发环境中，首先检查Entitlements文件配置
2. 确保后端服务在客户端启动前已经运行
3. 使用`127.0.0.1`代替`localhost`以避免潜在的DNS解析问题
4. 在macOS系统偏好设置中检查应用的网络权限
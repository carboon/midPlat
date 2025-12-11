# Universal Game Client

这是一个为AI生成游戏设计的通用客户端，支持浏览房间列表、密码加入房间以及通过WebView加载游戏。

## 功能特性

- 房间列表浏览
- 密码加入房间
- WebView游戏加载
- 跨平台支持(iOS/Android)
- 环境变量配置支持

## 目录结构

```
lib/
├── main.dart                   # 应用入口点
├── app.dart                    # 根应用组件
├── routes/                     # 路由管理
│   ├── app_routes.dart         # 路由定义
│   └── route_generator.dart    # 路由生成器
├── models/                     # 数据模型
│   ├── room.dart               # 房间数据模型
│   └── user.dart               # 用户数据模型
├── providers/                  # 状态管理Provider
│   ├── auth_provider.dart      # 认证状态管理
│   ├── room_provider.dart      # 房间状态管理
│   └── game_provider.dart      # 游戏状态管理
├── services/                   # 业务逻辑层
│   ├── api_service.dart        # API服务
│   ├── socket_service.dart     # WebSocket服务
│   └── storage_service.dart    # 存储服务
├── screens/                    # 页面组件
│   ├── home_screen.dart        # 主页(房间列表)
│   ├── room_detail_screen.dart # 房间详情页
│   ├── join_room_screen.dart   # 加入房间页
│   └── game_screen.dart        # 游戏页面
├── widgets/                    # 可复用组件
│   ├── room_card.dart          # 房间卡片组件
│   ├── password_dialog.dart    # 密码输入对话框
│   └── custom_app_bar.dart     # 自定义导航栏
├── utils/                      # 工具类
│   ├── constants.dart          # 常量定义
│   ├── validators.dart         # 表单验证器
│   └── logger.dart             # 日志工具
└── theme/                      # 主题配置
   ├── app_theme.dart          # 应用主题
   └── colors.dart             # 颜色定义
```

## 配置文件

客户端支持通过 `.env` 文件进行配置：

```bash
# .env 配置文件
MATCHMAKER_URL=http://127.0.0.1:8000
APP_NAME=Universal Game Client
ROOM_REFRESH_INTERVAL=30
```

## 环境配置

在 `lib/utils/constants.dart` 中配置通过环境变量动态加载:

```dart
// 配置已通过环境变量动态加载，无需手动修改
```

## 依赖说明

- `provider`: 状态管理
- `http`: HTTP请求
- `webview_flutter`: WebView组件
- `permission_handler`: 权限管理
- `shared_preferences`: 本地数据存储
- `socket_io_client`: WebSocket客户端

## 安装和运行

1. 确保已安装Flutter SDK
2. 安装依赖:
   ```
   flutter pub get
   ```
3. 运行应用:
   ```
   flutter run
   ```

## 构建APK/IPA

### Android
```
flutter build apk
```

### iOS
```
flutter build ios
```

## 注意事项

1. 在Android上使用相机功能需要在`android/app/src/main/AndroidManifest.xml`中添加相机权限:
   ```xml
   <uses-permission android:name="android.permission.CAMERA" />
   ```

2. 在iOS上使用相机功能需要在`ios/Runner/Info.plist`中添加权限描述:
   ```xml
   <key>NSCameraUsageDescription</key>
   <string>Camera permission is required for barcode scanning.</string>
   ```
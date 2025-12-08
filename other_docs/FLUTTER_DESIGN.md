# Flutter App架构设计文档 - 通用AI游戏容器平台

## 1. 概述

本设计文档旨在为通用AI游戏容器平台创建一个跨平台的Flutter应用程序架构。该应用需支持浏览房间列表、通过WebView加载游戏、扫码/密码加入房间等功能，并适配iOS和Android设备。

## 2. 技术选型

### 2.1 核心框架
- Flutter SDK (稳定版)
- Dart语言

### 2.2 状态管理
- Provider (Google推荐的状态管理方案)

### 2.3 网络通信
- http: REST API请求
- socket_io_client: WebSocket连接
- webview_flutter: 游戏页面加载

### 2.4 数据持久化
- shared_preferences: 轻量级数据存储

### 2.5 UI组件库
- flutter/material.dart: Material Design组件
- cupertino_icons: iOS风格图标

### 2.6 其他关键依赖
- qr_code_scanner: 二维码扫描功能
- permission_handler: 权限管理
- flutter_svg: SVG图像支持

## 3. 目录结构

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
│   ├── game_screen.dart        # 游戏页面
│   └── scanner_screen.dart     # 扫码页面
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

## 4. 核心组件设计

### 4.1 主要页面

#### HomeScreen (主页)
- 展示房间列表
- 提供刷新、搜索功能
- 导航至加入房间页面
- 显示用户信息

#### JoinRoomScreen (加入房间)
- 提供扫码加入功能
- 提供密码加入功能
- 输入房间ID/密码表单

#### ScannerScreen (扫码页面)
- 调用相机进行二维码扫描
- 解析房间信息并自动填充

#### RoomDetailScreen (房间详情)
- 显示房间详细信息
- 提供加入按钮
- 显示房间密码(如果需要)

#### GameScreen (游戏页面)
- 使用WebView加载游戏
- 处理游戏与应用的交互
- 提供退出游戏功能

### 4.2 状态管理设计

采用Provider作为核心状态管理方案，创建三个主要的Provider:

#### AuthProvider
- 管理用户认证状态
- 存储用户信息
- 处理登录/登出逻辑

#### RoomProvider
- 管理房间列表数据
- 处理房间搜索和筛选
- 管理当前房间状态

#### GameProvider
- 管理游戏加载状态
- 处理游戏设置
- 管理游戏与应用的数据交换

### 4.3 网络层设计

#### ApiService
- 封装REST API调用
- 处理HTTP请求和响应
- 错误处理和重试机制

#### SocketService
- 管理WebSocket连接
- 处理实时消息收发
- 心跳维持和断线重连

### 4.4 数据模型

#### Room Model
```dart
class Room {
  final String id;
  final String name;
  final String password;
  final int playerCount;
  final int maxPlayers;
  final String status;
  final DateTime createdAt;
  
  // 构造函数和方法...
}
```

#### User Model
```dart
class User {
  final String id;
  final String username;
  final String token;
  
  // 构造函数和方法...
}
```

## 5. 功能模块实现

### 5.1 房间列表浏览
- 从API获取房间列表数据
- 使用ListView展示房间卡片
- 支持下拉刷新和上拉加载更多
- 提供搜索和筛选功能

### 5.2 WebView游戏加载
- 使用webview_flutter插件
- 实现JavaScript通道通信
- 处理页面加载状态和错误
- 支持全屏模式切换

### 5.3 扫码/密码加入房间
- 集成qr_code_scanner实现扫码功能
- 请求相机权限
- 解析二维码中的房间信息
- 提供密码输入界面

### 5.4 跨平台适配
- 使用Material Design和Cupertino组件混合
- 根据平台自动切换UI风格
- 处理不同屏幕尺寸适配
- 遵循各平台设计规范

## 6. 安全性考虑

- 网络请求使用HTTPS
- 敏感数据加密存储
- 权限申请按需进行
- 输入验证和 sanitization

## 7. 性能优化

- 图片懒加载
- 页面缓存策略
- 内存泄漏检测
- 启动时间优化

## 8. 测试策略

- 单元测试: 测试业务逻辑和服务
- Widget测试: 测试UI组件
- 集成测试: 测试完整功能流程
- 性能测试: 监控应用性能指标

## 9. 部署和发布

- 构建配置分离(开发/测试/生产)
- 版本管理和签名配置
- 应用商店发布指南
- 持续集成/持续部署(CI/CD)配置

## 10. 未来扩展性

- 插件化架构支持新功能模块
- 国际化支持
- 主题切换功能
- 社交分享功能
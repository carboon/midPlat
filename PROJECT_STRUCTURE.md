# 项目结构说明

## 目录结构

```
├── game_server_template/          # 游戏服务器模板
│   ├── Dockerfile                 # Docker配置文件
│   ├── README.md                  # 服务器说明文档
│   ├── docker-compose.yml         # Docker编排文件
│   ├── package-lock.json          # npm依赖锁文件
│   ├── package.json               # npm包配置
│   ├── public/                    # 静态资源目录
│   │   └── index.html             # 主页
│   └── server.js                  # 服务器主程序
│
├── matchmaker_service/            # 匹配服务
│   └── matchmaker/                # 匹配器模块
│       ├── Dockerfile             # Docker配置文件
│       ├── README.md              # 匹配服务说明文档
│       ├── docker-compose.yml     # Docker编排文件
│       ├── main.py                # 匹配服务主程序
│       ├── requirements.txt       # Python依赖列表
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
│       └── pubspec.yaml           # Flutter依赖配置
│
└── other_docs/                    # 其他文档
    ├── FLUTTER_DESIGN.md          # Flutter设计文档
    ├── FLUTTER_TASKS.md           # Flutter任务列表
    ├── 开发进度.md                  # 开发进度记录
    └── 总结.md                     # 项目总结
```

## 组件说明

### 1. 游戏服务器模板 (game_server_template/)
- 基于Node.js的WebSocket游戏服务器模板
- 支持Docker容器化部署
- 包含基本的HTML客户端用于测试

### 2. 匹配服务 (matchmaker_service/)
- 基于Python的玩家匹配服务
- 使用WebSocket进行实时通信
- 支持房间创建和加入功能

### 3. 移动端应用 (mobile_app/universal_game_client/)
- 使用Flutter开发的跨平台游戏客户端
- 支持iOS和Android平台
- 实现了用户认证、房间管理和游戏界面

### 4. 文档资料 (other_docs/)
- 包含项目设计文档、任务列表和进度记录
- 提供Flutter开发相关的技术资料
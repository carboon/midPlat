# AI游戏服务器模板

这是一个用于AI生成游戏的标准化服务器模板，基于Node.js和Socket.IO构建，遵循通用AI游戏容器平台的协议规范。

## 功能特性

- 基于Express和Socket.IO的实时通信服务器
- 自动心跳上报到撮合服务
- 简单的点击计数游戏示例
- Docker容器化部署支持
- 环境变量配置支持

## 目录结构

```
.
├── server.js           # 服务器主程序
├── package.json        # 项目依赖配置
├── Dockerfile          # Docker构建文件
├── docker-compose.yml  # Docker Compose配置
└── public/             # 静态文件目录
    └── index.html      # 游戏前端页面
```

## 环境变量

- `MATCHMAKER_URL`: 撮合服务地址 (默认: http://localhost:8000)
- `ROOM_NAME`: 房间名称 (默认: 默认房间)
- `ROOM_PASSWORD`: 房间密码 (默认: 空)
- `PORT`: 服务器监听端口 (默认: 8080)

## 本地开发

1. 安装依赖:
   ```
   npm install
   ```

2. 启动开发服务器:
   ```
   npm run dev
   ```

3. 访问游戏页面:
   打开浏览器访问 http://localhost:8080

## Docker部署

1. 构建并启动容器:
   ```
   docker-compose up --build
   ```

2. 访问游戏页面:
   打开浏览器访问 http://localhost:8080

## API接口

- WebSocket连接: 自动建立
- 静态文件服务: `/` (提供index.html)
- 心跳上报: 自动向撮合服务POST房间信息

## 游戏玩法

打开游戏页面后，点击"点击我!"按钮，所有连接的用户都会看到实时更新的点击计数。
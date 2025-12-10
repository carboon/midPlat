const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const axios = require('axios');

// 初始化 Express 应用
const app = express();
const server = http.createServer(app);
const io = socketIo(server);

// 配置静态文件服务
app.use(express.static(path.join(__dirname, 'public')));

// 存储游戏状态
let gameState = {
  clickCount: 0
};

// WebSocket 连接处理
io.on('connection', (socket) => {
  console.log('用户连接:', socket.id);
  
  // 发送当前游戏状态
  socket.emit('gameState', gameState);
  
  // 处理点击事件
  socket.on('click', () => {
    gameState.clickCount++;
    // 广播更新后的游戏状态
    io.emit('gameState', gameState);
  });
  
  // 处理用户断开连接
  socket.on('disconnect', () => {
    console.log('用户断开连接:', socket.id);
  });
});

// 启动服务器
const PORT = process.env.PORT || 8080;
server.listen(PORT, () => {
  console.log(`游戏服务器运行在端口 ${PORT}`);
  
  // 启动后立即上报心跳
  sendHeartbeat();
});

// 心跳上报逻辑
async function sendHeartbeat() {
  try {
    // 从环境变量获取撮合服务地址和房间信息
    const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
    const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
    const ROOM_PASSWORD = process.env.ROOM_PASSWORD || '';
    
    // 获取本机IP地址
    const os = require('os');
    const networkInterfaces = os.networkInterfaces();
    // 强制使用 localhost 以确保在本地开发环境正常工作
    let ipAddress = 'localhost';
    
    // 上报心跳到撮合服务
    await axios.post(`${MATCHMAKER_URL}/register`, {
      ip: ipAddress,
      port: PORT,
      name: ROOM_NAME,
      max_players: 20,
      current_players: 0
    });
    
    console.log(`心跳上报成功: ${ipAddress}:${PORT} (${ROOM_NAME})`);
    
    // 每隔25秒发送一次心跳 (撮合服务超时时间为30秒)
    setTimeout(sendHeartbeat, 25000);
  } catch (error) {
    console.error('心跳上报失败:', error.message);
    // 5秒后重试
    setTimeout(sendHeartbeat, 5000);
  }
}
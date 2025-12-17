const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

// 初始化 Express 应用
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

// 配置静态文件服务
app.use(express.static(path.join(__dirname, 'public')));

// 从环境变量获取配置
const PORT = process.env.PORT || 8080;
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const ROOM_PASSWORD = process.env.ROOM_PASSWORD || '';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;

// 存储游戏状态
let gameState = {
  clickCount: 0
};

// 连接的玩家数
let connectedPlayers = 0;

// 用户自定义游戏逻辑（可通过代码注入覆盖）
let userGameLogic = null;

/**
 * 设置用户游戏逻辑
 * @param {Object} logic - 包含 initGame 和 handlePlayerAction 方法的对象
 */
function setUserGameLogic(logic) {
  userGameLogic = logic;
  if (userGameLogic && userGameLogic.initGame) {
    gameState = userGameLogic.initGame();
  }
}

/**
 * 获取当前游戏状态
 * @returns {Object} 当前游戏状态
 */
function getGameState() {
  return { ...gameState };
}

/**
 * 获取连接的玩家数
 * @returns {number} 连接的玩家数
 */
function getConnectedPlayers() {
  return connectedPlayers;
}

/**
 * 处理玩家操作
 * @param {string} action - 操作类型
 * @param {Object} data - 操作数据
 * @returns {Object} 更新后的游戏状态
 */
function handlePlayerAction(action, data = {}) {
  try {
    if (userGameLogic && userGameLogic.handlePlayerAction) {
      gameState = userGameLogic.handlePlayerAction(gameState, action, data);
    } else {
      // 默认处理逻辑
      if (action === 'click') {
        gameState.clickCount = (gameState.clickCount || 0) + 1;
      }
    }
    return { ...gameState };
  } catch (error) {
    console.error('处理玩家操作失败:', error);
    throw error;
  }
}

// WebSocket 连接处理
io.on('connection', (socket) => {
  connectedPlayers++;
  console.log('用户连接:', socket.id, '当前玩家数:', connectedPlayers);
  
  // 发送当前游戏状态给新连接的客户端 (需求 3.4)
  socket.emit('gameState', getGameState());
  
  // 处理点击事件（兼容旧版本）
  socket.on('click', () => {
    const newState = handlePlayerAction('click');
    // 广播更新后的游戏状态给所有连接的客户端 (需求 3.5)
    io.emit('gameState', newState);
  });
  
  // 处理玩家操作事件
  socket.on('playerAction', (data) => {
    try {
      const action = data.action || 'click';
      const newState = handlePlayerAction(action, data);
      // 广播更新后的游戏状态给所有连接的客户端 (需求 3.5)
      io.emit('gameState', newState);
    } catch (error) {
      socket.emit('error', { message: '操作处理失败', error: error.message });
    }
  });
  
  // 处理用户断开连接
  socket.on('disconnect', () => {
    connectedPlayers--;
    console.log('用户断开连接:', socket.id, '当前玩家数:', connectedPlayers);
  });
});

// 心跳上报逻辑
let heartbeatTimer = null;
let isRegistered = false;

async function sendHeartbeat() {
  try {
    // 上报心跳到撮合服务 (需求 1.5)
    await axios.post(`${MATCHMAKER_URL}/register`, {
      ip: 'localhost',
      port: PORT,
      name: ROOM_NAME,
      max_players: MAX_PLAYERS,
      current_players: connectedPlayers,
      metadata: {
        created_by: 'game_server_template',
        game_type: 'custom'
      }
    });
    
    isRegistered = true;
    console.log(`心跳上报成功: localhost:${PORT} (${ROOM_NAME})`);
    
    // 每隔指定时间发送一次心跳
    heartbeatTimer = setTimeout(sendHeartbeat, HEARTBEAT_INTERVAL);
  } catch (error) {
    console.error('心跳上报失败:', error.message);
    isRegistered = false;
    // 指定时间后重试
    heartbeatTimer = setTimeout(sendHeartbeat, RETRY_INTERVAL);
  }
}

/**
 * 停止心跳
 */
function stopHeartbeat() {
  if (heartbeatTimer) {
    clearTimeout(heartbeatTimer);
    heartbeatTimer = null;
  }
}

/**
 * 检查是否已注册到撮合服务
 * @returns {boolean} 是否已注册
 */
function isServerRegistered() {
  return isRegistered;
}

// 启动服务器函数
function startServer(port = PORT) {
  return new Promise((resolve, reject) => {
    try {
      server.listen(port, () => {
        console.log(`游戏服务器运行在端口 ${port}`);
        console.log(`房间名称: ${ROOM_NAME}`);
        
        // 启动后立即上报心跳 (需求 1.5)
        sendHeartbeat();
        
        resolve({ server, io, port });
      });
      
      server.on('error', (error) => {
        reject(error);
      });
    } catch (error) {
      reject(error);
    }
  });
}

// 关闭服务器函数
function closeServer() {
  return new Promise((resolve) => {
    stopHeartbeat();
    io.close();
    server.close(() => {
      console.log('服务器已关闭');
      resolve();
    });
  });
}

// 优雅关闭
process.on('SIGTERM', async () => {
  console.log('收到SIGTERM信号，正在关闭服务器...');
  await closeServer();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('收到SIGINT信号，正在关闭服务器...');
  await closeServer();
  process.exit(0);
});

// 如果直接运行此文件，启动服务器
if (require.main === module) {
  startServer();
}

// 导出模块供测试使用
module.exports = {
  app,
  server,
  io,
  startServer,
  closeServer,
  getGameState,
  getConnectedPlayers,
  handlePlayerAction,
  setUserGameLogic,
  sendHeartbeat,
  stopHeartbeat,
  isServerRegistered,
  // 配置常量
  config: {
    PORT,
    MATCHMAKER_URL,
    ROOM_NAME,
    HEARTBEAT_INTERVAL,
    RETRY_INTERVAL,
    MAX_PLAYERS
  }
};

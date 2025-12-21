const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const path = require('path');
const axios = require('axios');
const winston = require('winston');
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

// HTTP请求日志中间件 - 需求 8.1
app.use((_req, res, next) => {
  const start = Date.now();
  
  // 记录请求
  logger.info('HTTP request received', {
    method: _req.method,
    path: _req.path,
    query: _req.query,
    ip: _req.ip,
    user_agent: _req.get('user-agent')
  });
  
  // 监听响应完成
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('HTTP request completed', {
      method: _req.method,
      path: _req.path,
      status: res.statusCode,
      duration_ms: duration
    });
  });
  
  next();
});

// 从环境变量获取配置
const PORT = process.env.PORT || 8080;
const EXTERNAL_PORT = process.env.EXTERNAL_PORT || PORT; // 外部访问端口
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const ROOM_PASSWORD = process.env.ROOM_PASSWORD || '';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;
const LOG_LEVEL = process.env.LOG_LEVEL || 'info';
const LOG_FILE = process.env.LOG_FILE || 'game_server.log';
const NODE_ENV = process.env.NODE_ENV || 'development';

// 配置Winston日志记录器 - 需求 8.1
const logger = winston.createLogger({
  level: LOG_LEVEL,
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.splat(),
    winston.format.json()
  ),
  defaultMeta: { 
    service: 'game-server-template',
    room: ROOM_NAME,
    port: PORT
  },
  transports: [
    // 文件日志 - 错误级别
    new winston.transports.File({ 
      filename: 'error.log', 
      level: 'error',
      maxsize: 10485760, // 10MB
      maxFiles: 5
    }),
    // 文件日志 - 所有级别
    new winston.transports.File({ 
      filename: LOG_FILE,
      maxsize: 10485760, // 10MB
      maxFiles: 5
    })
  ]
});

// 在开发环境添加控制台输出
if (NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: winston.format.combine(
      winston.format.colorize(),
      winston.format.simple()
    )
  }));
}

// 记录启动配置
logger.info('Game Server Template starting', {
  config: {
    port: PORT,
    external_port: EXTERNAL_PORT,
    room_name: ROOM_NAME,
    max_players: MAX_PLAYERS,
    matchmaker_url: MATCHMAKER_URL,
    heartbeat_interval: HEARTBEAT_INTERVAL,
    environment: NODE_ENV,
    log_level: LOG_LEVEL
  }
});

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
  logger.info('Client connected', { 
    socket_id: socket.id, 
    connected_players: connectedPlayers,
    client_address: socket.handshake.address
  });
  
  // 发送当前游戏状态给新连接的客户端 (需求 3.4)
  socket.emit('gameState', getGameState());
  
  // 处理点击事件（兼容旧版本）
  socket.on('click', () => {
    try {
      const newState = handlePlayerAction('click');
      // 广播更新后的游戏状态给所有连接的客户端 (需求 3.5)
      io.emit('gameState', newState);
      logger.debug('Player action processed', { 
        action: 'click', 
        socket_id: socket.id,
        new_state: newState
      });
    } catch (error) {
      logger.error('Failed to process click action', { 
        socket_id: socket.id, 
        error: error.message,
        stack: error.stack
      });
    }
  });
  
  // 处理玩家操作事件
  socket.on('playerAction', (data) => {
    try {
      const action = data.action || 'click';
      const newState = handlePlayerAction(action, data);
      // 广播更新后的游戏状态给所有连接的客户端 (需求 3.5)
      io.emit('gameState', newState);
      logger.debug('Player action processed', { 
        action: action, 
        socket_id: socket.id,
        data: data,
        new_state: newState
      });
    } catch (error) {
      logger.error('Failed to process player action', { 
        socket_id: socket.id, 
        action: data.action,
        error: error.message,
        stack: error.stack
      });
      socket.emit('error', { message: '操作处理失败', error: error.message });
    }
  });
  
  // 处理用户断开连接
  socket.on('disconnect', () => {
    connectedPlayers--;
    logger.info('Client disconnected', { 
      socket_id: socket.id, 
      connected_players: connectedPlayers
    });
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
      port: EXTERNAL_PORT, // 使用外部端口进行注册
      name: ROOM_NAME,
      max_players: MAX_PLAYERS,
      current_players: connectedPlayers,
      metadata: {
        created_by: 'game_server_template',
        game_type: 'custom',
        internal_port: PORT,
        external_port: EXTERNAL_PORT
      }
    });
    
    isRegistered = true;
    logger.debug('Heartbeat sent successfully', {
      matchmaker_url: MATCHMAKER_URL,
      port: EXTERNAL_PORT,
      internal_port: PORT,
      room_name: ROOM_NAME,
      current_players: connectedPlayers
    });
    
    // 每隔指定时间发送一次心跳
    heartbeatTimer = setTimeout(sendHeartbeat, HEARTBEAT_INTERVAL);
  } catch (error) {
    isRegistered = false;
    logger.error('Heartbeat failed', {
      matchmaker_url: MATCHMAKER_URL,
      error: error.message,
      stack: error.stack,
      retry_in_ms: RETRY_INTERVAL
    });
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
        logger.info('Game server started', {
          port: port,
          room_name: ROOM_NAME,
          max_players: MAX_PLAYERS,
          environment: NODE_ENV
        });
        
        // 启动后立即上报心跳 (需求 1.5)
        sendHeartbeat();
        
        resolve({ server, io, port });
      });
      
      server.on('error', (error) => {
        logger.error('Server startup failed', {
          port: port,
          error: error.message,
          stack: error.stack
        });
        reject(error);
      });
    } catch (error) {
      logger.error('Failed to start server', {
        error: error.message,
        stack: error.stack
      });
      reject(error);
    }
  });
}

// 关闭服务器函数
function closeServer() {
  return new Promise((resolve) => {
    logger.info('Shutting down server', {
      port: PORT,
      connected_players: connectedPlayers
    });
    
    stopHeartbeat();
    io.close();
    server.close(() => {
      logger.info('Server closed successfully');
      resolve();
    });
  });
}

// 优雅关闭
process.on('SIGTERM', async () => {
  logger.info('Received SIGTERM signal, shutting down gracefully');
  await closeServer();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('Received SIGINT signal, shutting down gracefully');
  await closeServer();
  process.exit(0);
});

// 捕获未处理的异常 - 需求 8.1
process.on('uncaughtException', (error) => {
  logger.error('Uncaught exception', {
    error: error.message,
    stack: error.stack
  });
  process.exit(1);
});

process.on('unhandledRejection', (reason, promise) => {
  logger.error('Unhandled rejection', {
    reason: reason,
    promise: promise
  });
});

// 健康检查和监控端点 - 需求 6.2, 6.3
app.get('/health', (req, res) => {
  const uptime = process.uptime();
  const memoryUsage = process.memoryUsage();
  
  // 确定健康状态
  let status = 'healthy';
  const issues = [];
  const components = {};
  
  // 检查内存使用率
  const memoryUsagePercent = (memoryUsage.heapUsed / memoryUsage.heapTotal) * 100;
  if (memoryUsagePercent > 90) {
    status = 'degraded';
    issues.push('High memory usage detected');
  }
  
  // 检查各组件状态
  components.websocket_server = io ? 'healthy' : 'unavailable';
  components.http_server = server ? 'healthy' : 'unavailable';
  components.matchmaker_registration = isServerRegistered() ? 'healthy' : 'degraded';
  
  // 检查房间利用率
  const roomUtilization = (getConnectedPlayers() / MAX_PLAYERS) * 100;
  
  const healthData = {
    status: status,
    timestamp: new Date().toISOString(),
    components: components,
    game_metrics: {
      uptime_seconds: Math.floor(uptime),
      game_state: getGameState(),
      connected_players: getConnectedPlayers(),
      max_players: MAX_PLAYERS,
      room_utilization_percent: Math.round(roomUtilization),
      room_name: ROOM_NAME,
      password_protected: ROOM_PASSWORD !== ''
    },
    system_metrics: {
      memory_usage: {
        rss_mb: Math.round(memoryUsage.rss / 1024 / 1024 * 100) / 100,
        heap_used_mb: Math.round(memoryUsage.heapUsed / 1024 / 1024 * 100) / 100,
        heap_total_mb: Math.round(memoryUsage.heapTotal / 1024 / 1024 * 100) / 100,
        external_mb: Math.round(memoryUsage.external / 1024 / 1024 * 100) / 100,
        heap_usage_percent: Math.round(memoryUsagePercent)
      },
      process_id: process.pid,
      node_version: process.version,
      platform: process.platform
    },
    network_status: {
      registered_to_matchmaker: isServerRegistered(),
      matchmaker_url: MATCHMAKER_URL,
      last_heartbeat_attempt: new Date().toISOString() // 简化实现
    },
    configuration: {
      port: PORT,
      external_port: EXTERNAL_PORT,
      heartbeat_interval_ms: HEARTBEAT_INTERVAL,
      retry_interval_ms: RETRY_INTERVAL,
      environment: process.env.NODE_ENV || 'development'
    }
  };
  
  if (issues.length > 0) {
    healthData.issues = issues;
  }
  
  res.json(healthData);
});

// 监控状态端点
app.get('/monitoring/status', (req, res) => {
  const uptime = process.uptime();
  const memoryUsage = process.memoryUsage();
  
  const monitoringData = {
    timestamp: new Date().toISOString(),
    service_status: isServerRegistered() ? 'healthy' : 'degraded',
    game_metrics: {
      connected_players: getConnectedPlayers(),
      max_players: MAX_PLAYERS,
      game_state: getGameState(),
      room_utilization_percent: Math.round((getConnectedPlayers() / MAX_PLAYERS) * 100)
    },
    system_metrics: {
      uptime_seconds: Math.floor(uptime),
      memory_usage_mb: Math.round(memoryUsage.rss / 1024 / 1024 * 100) / 100,
      heap_usage_percent: Math.round((memoryUsage.heapUsed / memoryUsage.heapTotal) * 100)
    },
    network_status: {
      registered_to_matchmaker: isServerRegistered(),
      matchmaker_url: MATCHMAKER_URL,
      last_heartbeat_attempt: new Date().toISOString() // 简化实现
    },
    configuration: {
      room_name: ROOM_NAME,
      port: PORT,
      external_port: EXTERNAL_PORT,
      heartbeat_interval_ms: HEARTBEAT_INTERVAL,
      retry_interval_ms: RETRY_INTERVAL,
      environment: process.env.NODE_ENV || 'development'
    }
  };
  
  res.json(monitoringData);
});

// 详细游戏状态端点
app.get('/monitoring/game-state', (req, res) => {
  const gameStateData = {
    timestamp: new Date().toISOString(),
    current_state: getGameState(),
    player_info: {
      connected_count: getConnectedPlayers(),
      max_capacity: MAX_PLAYERS,
      available_slots: MAX_PLAYERS - getConnectedPlayers()
    },
    room_info: {
      name: ROOM_NAME,
      password_protected: ROOM_PASSWORD !== '',
      uptime_seconds: Math.floor(process.uptime())
    }
  };
  
  res.json(gameStateData);
});

// API文档端点 - 需求 6.1
app.get('/api/documentation', (req, res) => {
  const apiDoc = {
    service: 'Game Server Template',
    version: '1.0.0',
    description: '动态游戏服务器模板 - 支持用户代码注入和WebSocket实时通信',
    endpoints: {
      health_monitoring: {
        'GET /health': {
          description: '基础健康检查，返回服务器状态和系统指标',
          response_example: {
            status: 'healthy',
            game_metrics: {},
            system_metrics: {},
            network_status: {}
          }
        },
        'GET /monitoring/status': {
          description: '详细监控状态，包含性能指标和配置信息',
          response_example: {
            service_status: 'healthy',
            game_metrics: {},
            system_metrics: {}
          }
        },
        'GET /monitoring/game-state': {
          description: '游戏状态详情，包含玩家信息和房间信息',
          response_example: {
            current_state: {},
            player_info: {},
            room_info: {}
          }
        }
      },
      websocket_events: {
        'connection': {
          description: '客户端连接事件，服务器会发送当前游戏状态',
          direction: 'server -> client',
          event: 'gameState'
        },
        'click': {
          description: '点击事件（兼容旧版本）',
          direction: 'client -> server',
          response: '广播更新的游戏状态给所有客户端'
        },
        'playerAction': {
          description: '玩家操作事件，支持自定义游戏逻辑',
          direction: 'client -> server',
          parameters: {
            action: 'string - 操作类型',
            data: 'object - 操作数据'
          },
          response: '广播更新的游戏状态给所有客户端'
        },
        'disconnect': {
          description: '客户端断开连接事件',
          direction: 'client -> server'
        }
      },
      static_files: {
        'GET /': {
          description: '游戏客户端页面 (index.html)',
          content_type: 'text/html'
        }
      }
    },
    configuration: {
      port: PORT,
      external_port: EXTERNAL_PORT,
      room_name: ROOM_NAME,
      max_players: MAX_PLAYERS,
      matchmaker_url: MATCHMAKER_URL,
      heartbeat_interval_ms: HEARTBEAT_INTERVAL
    },
    custom_game_logic: {
      description: '支持通过 setUserGameLogic() 函数注入自定义游戏逻辑',
      required_methods: {
        initGame: '初始化游戏状态，返回初始状态对象',
        handlePlayerAction: '处理玩家操作，接收 (gameState, action, data) 参数，返回新状态'
      }
    }
  };
  
  res.json(apiDoc);
});

// API端点列表
app.get('/api/endpoints', (req, res) => {
  const endpoints = [
    { method: 'GET', path: '/', description: '游戏客户端页面' },
    { method: 'GET', path: '/health', description: '健康检查' },
    { method: 'GET', path: '/monitoring/status', description: '监控状态' },
    { method: 'GET', path: '/monitoring/game-state', description: '游戏状态详情' },
    { method: 'GET', path: '/api/documentation', description: 'API文档' },
    { method: 'GET', path: '/api/endpoints', description: 'API端点列表' },
    { method: 'WebSocket', path: '/', description: 'WebSocket游戏连接' }
  ];
  
  res.json({
    timestamp: new Date().toISOString(),
    total_endpoints: endpoints.length,
    endpoints: endpoints,
    websocket_url: `ws://localhost:${PORT}`,
    documentation_url: `/api/documentation`
  });
});

// 404处理中间件 - 需求 6.3, 6.4
app.use((req, res, next) => {
  // 如果没有路由匹配，返回标准化的404错误响应
  res.status(404).json({
    error: {
      code: 404,
      message: 'Not Found',
      timestamp: new Date().toISOString(),
      path: req.path
    }
  });
});

// 错误处理中间件 - 需求 8.1, 8.2, 8.3
app.use((err, _req, res, _next) => {
  logger.error('Express error handler', {
    error: err.message,
    stack: err.stack,
    path: _req.path,
    method: _req.method
  });
  
  res.status(err.status || 500).json({
    error: {
      code: err.status || 500,
      message: err.message || 'Internal server error',
      timestamp: new Date().toISOString(),
      path: _req.path
    }
  });
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
  logger,
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
    MAX_PLAYERS,
    LOG_LEVEL,
    LOG_FILE,
    NODE_ENV
  }
};

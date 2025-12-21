/**
 * **Feature: ai-game-platform, Property 12: WebSocket连接建立**
 * **验证需求: 3.3, 3.4**
 * 
 * 属性 12: WebSocket连接建立
 * *对于任何*房间选择操作，客户端应该建立WebSocket连接并接收当前游戏状态
 * 
 * 测试验证:
 * - 3.3: WHEN 玩家选择房间时 THEN Universal_Client SHALL 建立与对应游戏服务器的WebSocket连接
 * - 3.4: WHEN WebSocket连接建立时 THEN Game_Server SHALL 发送当前游戏状态给新连接的客户端
 */

const fc = require('fast-check');
const { io: ioClient } = require('socket.io-client');
const http = require('http');
const express = require('express');
const { Server: SocketIOServer } = require('socket.io');

// 测试服务器设置
let testServer = null;
let testIO = null;
let testPort = 0;
let gameState = { clickCount: 0 };
let connectedPlayers = 0;

/**
 * 创建测试服务器
 */
function createTestServer(initialState = { clickCount: 0 }) {
  return new Promise((resolve, reject) => {
    const app = express();
    const server = http.createServer(app);
    const io = new SocketIOServer(server, {
      cors: {
        origin: "*",
        methods: ["GET", "POST"]
      }
    });
    
    gameState = { ...initialState };
    connectedPlayers = 0;
    
    io.on('connection', (socket) => {
      connectedPlayers++;
      
      // 需求 3.4: 发送当前游戏状态给新连接的客户端
      socket.emit('gameState', { ...gameState });
      
      socket.on('click', () => {
        gameState.clickCount = (gameState.clickCount || 0) + 1;
        io.emit('gameState', { ...gameState });
      });
      
      socket.on('playerAction', (data) => {
        if (data.action === 'click') {
          gameState.clickCount = (gameState.clickCount || 0) + 1;
        }
        io.emit('gameState', { ...gameState });
      });
      
      socket.on('disconnect', () => {
        connectedPlayers--;
      });
    });
    
    // 使用随机端口
    server.listen(0, () => {
      const port = server.address().port;
      resolve({ server, io, port });
    });
    
    server.on('error', reject);
  });
}

/**
 * 创建客户端连接并等待游戏状态
 * 需求 3.3: 建立WebSocket连接
 * 需求 3.4: 接收当前游戏状态
 */
function connectAndWaitForState(port, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const client = ioClient(`http://localhost:${port}`, {
      transports: ['websocket'],
      forceNew: true,
      timeout: timeout,
      autoConnect: false  // 不自动连接，先设置监听器
    });
    
    const timer = setTimeout(() => {
      client.disconnect();
      reject(new Error('Timeout waiting for gameState'));
    }, timeout);
    
    // 先设置游戏状态监听器
    client.once('gameState', (state) => {
      clearTimeout(timer);
      resolve({ client, state });
    });
    
    client.on('connect_error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    
    // 然后连接
    client.connect();
  });
}

describe('Property 12: WebSocket连接建立', () => {
  beforeEach(async () => {
    // 每个测试前创建新的服务器
    const result = await createTestServer({ clickCount: 0 });
    testServer = result.server;
    testIO = result.io;
    testPort = result.port;
  });
  
  afterEach(async () => {
    // 清理
    if (testIO) {
      testIO.close();
    }
    if (testServer) {
      await new Promise(resolve => testServer.close(resolve));
    }
    testServer = null;
    testIO = null;
    testPort = 0;
  });
  
  /**
   * **Feature: ai-game-platform, Property 12: WebSocket连接建立**
   * 
   * 属性: 对于任何初始游戏状态，当客户端建立WebSocket连接时，
   * 服务器应该发送当前游戏状态给新连接的客户端
   */
  test('客户端连接后应该接收到当前游戏状态', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的初始点击数 (0-1000)
        fc.integer({ min: 0, max: 1000 }),
        async (initialClickCount) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建带有初始状态的服务器
          const result = await createTestServer({ clickCount: initialClickCount });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          // 创建客户端连接并等待游戏状态 (需求 3.3, 3.4)
          const { client, state } = await connectAndWaitForState(testPort);
          
          try {
            // 验证: 接收到的状态应该与服务器的初始状态一致
            expect(state).toBeDefined();
            expect(state.clickCount).toBe(initialClickCount);
            
            return true;
          } finally {
            client.disconnect();
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 12: WebSocket连接建立**
   * 
   * 属性: 对于任何数量的并发客户端连接，每个客户端都应该接收到当前游戏状态
   */
  test('多个客户端连接后都应该接收到当前游戏状态', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的客户端数量 (1-5) 和初始点击数
        fc.integer({ min: 1, max: 5 }),
        fc.integer({ min: 0, max: 100 }),
        async (numClients, initialClickCount) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建带有初始状态的服务器
          const result = await createTestServer({ clickCount: initialClickCount });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const clients = [];
          const receivedStates = [];
          
          try {
            // 创建多个客户端连接
            for (let i = 0; i < numClients; i++) {
              const { client, state } = await connectAndWaitForState(testPort);
              clients.push(client);
              receivedStates.push(state);
            }
            
            // 验证: 每个客户端都应该接收到游戏状态
            expect(receivedStates.length).toBe(numClients);
            
            // 验证: 每个接收到的状态都应该包含正确的初始点击数
            for (const state of receivedStates) {
              expect(state).toBeDefined();
              expect(state.clickCount).toBe(initialClickCount);
            }
            
            return true;
          } finally {
            // 断开所有客户端
            for (const client of clients) {
              client.disconnect();
            }
          }
        }
      ),
      { numRuns: 50 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 12: WebSocket连接建立**
   * 
   * 属性: 对于任何游戏状态对象结构，客户端都应该接收到完整的状态
   */
  test('客户端应该接收到完整的游戏状态对象', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的游戏状态对象
        fc.record({
          clickCount: fc.integer({ min: 0, max: 10000 }),
          score: fc.integer({ min: 0, max: 1000000 }),
          level: fc.integer({ min: 1, max: 100 }),
          playerName: fc.string({ minLength: 1, maxLength: 20 })
        }),
        async (initialState) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建带有复杂初始状态的服务器
          const result = await createTestServer(initialState);
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const { client, state } = await connectAndWaitForState(testPort);
          
          try {
            // 验证: 接收到的状态应该包含所有字段
            expect(state).toBeDefined();
            expect(state.clickCount).toBe(initialState.clickCount);
            expect(state.score).toBe(initialState.score);
            expect(state.level).toBe(initialState.level);
            expect(state.playerName).toBe(initialState.playerName);
            
            return true;
          } finally {
            client.disconnect();
          }
        }
      ),
      { numRuns: 100 }
    );
  });
});

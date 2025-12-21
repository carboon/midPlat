/**
 * **Feature: ai-game-platform, Property 13: 游戏操作处理**
 * **验证需求: 3.5**
 * 
 * 属性 13: 游戏操作处理
 * *对于任何*玩家游戏操作，游戏服务器应该处理操作并广播状态更新给所有连接的客户端
 * 
 * 测试验证:
 * - 3.5: WHEN 玩家执行游戏操作时 THEN Game_Server SHALL 处理操作并广播状态更新给所有连接的客户端
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
    
    io.on('connection', (socket) => {
      // 发送当前游戏状态给新连接的客户端
      socket.emit('gameState', { ...gameState });
      
      // 处理点击事件
      socket.on('click', () => {
        gameState.clickCount = (gameState.clickCount || 0) + 1;
        // 需求 3.5: 广播状态更新给所有连接的客户端
        io.emit('gameState', { ...gameState });
      });
      
      // 处理玩家操作事件
      socket.on('playerAction', (data) => {
        if (data.action === 'click') {
          gameState.clickCount = (gameState.clickCount || 0) + 1;
        } else if (data.action === 'increment') {
          gameState.clickCount = (gameState.clickCount || 0) + (data.amount || 1);
        } else if (data.action === 'reset') {
          gameState.clickCount = 0;
        }
        // 需求 3.5: 广播状态更新给所有连接的客户端
        io.emit('gameState', { ...gameState });
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
 */
function connectClient(port, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const client = ioClient(`http://localhost:${port}`, {
      transports: ['websocket'],
      forceNew: true,
      timeout: timeout,
      autoConnect: false
    });
    
    const timer = setTimeout(() => {
      client.disconnect();
      reject(new Error('Timeout waiting for connection'));
    }, timeout);
    
    client.once('gameState', (state) => {
      clearTimeout(timer);
      resolve({ client, initialState: state });
    });
    
    client.on('connect_error', (error) => {
      clearTimeout(timer);
      reject(error);
    });
    
    client.connect();
  });
}

/**
 * 等待客户端接收游戏状态更新
 */
function waitForStateUpdate(client, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      reject(new Error('Timeout waiting for state update'));
    }, timeout);
    
    client.once('gameState', (state) => {
      clearTimeout(timer);
      resolve(state);
    });
  });
}

describe('Property 13: 游戏操作处理', () => {
  beforeEach(async () => {
    const result = await createTestServer({ clickCount: 0 });
    testServer = result.server;
    testIO = result.io;
    testPort = result.port;
  });
  
  afterEach(async () => {
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
   * **Feature: ai-game-platform, Property 13: 游戏操作处理**
   * 
   * 属性: 对于任何点击操作，游戏服务器应该处理操作并更新状态
   */
  test('点击操作应该增加点击计数', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的初始点击数和点击次数
        fc.integer({ min: 0, max: 100 }),
        fc.integer({ min: 1, max: 10 }),
        async (initialClickCount, numClicks) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建带有初始状态的服务器
          const result = await createTestServer({ clickCount: initialClickCount });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const { client } = await connectClient(testPort);
          
          try {
            let lastState = null;
            
            // 执行多次点击操作
            for (let i = 0; i < numClicks; i++) {
              const statePromise = waitForStateUpdate(client);
              client.emit('click');
              lastState = await statePromise;
            }
            
            // 验证: 点击计数应该正确增加
            expect(lastState).toBeDefined();
            expect(lastState.clickCount).toBe(initialClickCount + numClicks);
            
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
   * **Feature: ai-game-platform, Property 13: 游戏操作处理**
   * 
   * 属性: 对于任何玩家操作，所有连接的客户端都应该接收到状态更新广播
   */
  test('玩家操作应该广播给所有连接的客户端', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的客户端数量 (2-5)
        fc.integer({ min: 2, max: 5 }),
        async (numClients) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建服务器
          const result = await createTestServer({ clickCount: 0 });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const clients = [];
          
          try {
            // 创建多个客户端连接
            for (let i = 0; i < numClients; i++) {
              const { client } = await connectClient(testPort);
              clients.push(client);
            }
            
            // 设置所有客户端的状态更新监听
            const statePromises = clients.map(client => waitForStateUpdate(client));
            
            // 第一个客户端执行点击操作
            clients[0].emit('click');
            
            // 等待所有客户端接收状态更新
            const receivedStates = await Promise.all(statePromises);
            
            // 验证: 所有客户端都应该接收到相同的状态更新
            expect(receivedStates.length).toBe(numClients);
            for (const state of receivedStates) {
              expect(state).toBeDefined();
              expect(state.clickCount).toBe(1);
            }
            
            return true;
          } finally {
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
   * **Feature: ai-game-platform, Property 13: 游戏操作处理**
   * 
   * 属性: 对于任何playerAction操作，游戏服务器应该正确处理并广播
   */
  test('playerAction操作应该被正确处理', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的操作类型和数据
        fc.oneof(
          fc.constant({ action: 'click' }),
          fc.record({
            action: fc.constant('increment'),
            amount: fc.integer({ min: 1, max: 10 })
          }),
          fc.constant({ action: 'reset' })
        ),
        fc.integer({ min: 0, max: 50 }),
        async (actionData, initialClickCount) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建带有初始状态的服务器
          const result = await createTestServer({ clickCount: initialClickCount });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const { client } = await connectClient(testPort);
          
          try {
            const statePromise = waitForStateUpdate(client);
            client.emit('playerAction', actionData);
            const newState = await statePromise;
            
            // 验证: 状态应该根据操作类型正确更新
            expect(newState).toBeDefined();
            
            if (actionData.action === 'click') {
              expect(newState.clickCount).toBe(initialClickCount + 1);
            } else if (actionData.action === 'increment') {
              expect(newState.clickCount).toBe(initialClickCount + actionData.amount);
            } else if (actionData.action === 'reset') {
              expect(newState.clickCount).toBe(0);
            }
            
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
   * **Feature: ai-game-platform, Property 13: 游戏操作处理**
   * 
   * 属性: 对于任何序列的操作，最终状态应该是所有操作的累积结果
   */
  test('操作序列应该产生正确的累积状态', async () => {
    await fc.assert(
      fc.asyncProperty(
        // 生成随机的操作序列
        fc.array(
          fc.oneof(
            fc.constant({ action: 'click' }),
            fc.record({
              action: fc.constant('increment'),
              amount: fc.integer({ min: 1, max: 5 })
            })
          ),
          { minLength: 1, maxLength: 10 }
        ),
        async (actions) => {
          // 关闭之前的服务器
          if (testIO) testIO.close();
          if (testServer) await new Promise(resolve => testServer.close(resolve));
          
          // 创建服务器
          const result = await createTestServer({ clickCount: 0 });
          testServer = result.server;
          testIO = result.io;
          testPort = result.port;
          
          const { client } = await connectClient(testPort);
          
          try {
            // 计算预期的最终状态
            let expectedClickCount = 0;
            for (const action of actions) {
              if (action.action === 'click') {
                expectedClickCount += 1;
              } else if (action.action === 'increment') {
                expectedClickCount += action.amount;
              }
            }
            
            // 执行所有操作
            let lastState = null;
            for (const action of actions) {
              const statePromise = waitForStateUpdate(client);
              client.emit('playerAction', action);
              lastState = await statePromise;
            }
            
            // 验证: 最终状态应该等于预期的累积结果
            expect(lastState).toBeDefined();
            expect(lastState.clickCount).toBe(expectedClickCount);
            
            return true;
          } finally {
            client.disconnect();
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});

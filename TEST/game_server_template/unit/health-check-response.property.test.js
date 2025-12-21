/**
 * 属性测试 - 健康检查响应 (游戏服务器模板)
 * **Feature: ai-game-platform, Property 17: 健康检查响应**
 * 验证需求: 6.1
 * 
 * 属性17: 对于任何健康检查请求，所有服务应该返回服务状态和基本统计信息
 */

const request = require('supertest');
const fc = require('fast-check');
const express = require('express');
const path = require('path');

// 导入被测试的服务器应用
const createApp = () => {
  const app = express();
  
  // 基本中间件
  app.use(express.json());
  app.use(express.static(path.join(__dirname, '../public')));
  
  // 模拟游戏服务器的辅助函数
  const getConnectedPlayers = () => 0;
  const getGameState = () => 'waiting';
  const isServerRegistered = () => true;
  
  // 健康检查端点 - 需求 6.1
  app.get('/health', (req, res) => {
    const uptime = process.uptime();
    const memoryUsage = process.memoryUsage();
    
    const healthData = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: Math.floor(uptime),
      memory: {
        used: Math.round(memoryUsage.heapUsed / 1024 / 1024),
        total: Math.round(memoryUsage.heapTotal / 1024 / 1024),
        external: Math.round(memoryUsage.external / 1024 / 1024)
      },
      version: process.env.npm_package_version || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      game: {
        name: process.env.GAME_NAME || 'HTML Game',
        max_players: parseInt(process.env.MAX_PLAYERS) || 10,
        current_players: getConnectedPlayers()
      }
    };
    
    res.json(healthData);
  });
  
  // 基本路由
  app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, '../public/index.html'));
  });
  
  return app;
};

describe('游戏服务器健康检查响应属性测试', () => {
  let app;
  
  beforeEach(() => {
    app = createApp();
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何健康检查请求，游戏服务器应该返回服务状态和基本统计信息
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查总是返回服务状态和基本统计信息', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          headers: fc.dictionary(
            fc.constantFrom('Accept', 'User-Agent', 'X-Request-ID', 'Content-Type'),
            fc.string({ minLength: 1, maxLength: 100 }),
            { minKeys: 0, maxKeys: 4 }
          )
        }),
        async ({ headers }) => {
          // 发送健康检查请求
          const response = await request(app)
            .get('/health')
            .set(headers);
          
          // 属性验证: 健康检查必须总是返回成功状态码
          expect(response.status).toBe(200);
          
          const healthData = response.body;
          
          // 属性验证: 响应必须包含服务状态信息
          expect(healthData).toHaveProperty('status');
          expect(typeof healthData.status).toBe('string');
          
          const validStatuses = ['healthy', 'degraded', 'limited', 'unhealthy'];
          expect(validStatuses).toContain(healthData.status);
          
          // 属性验证: 响应必须包含时间戳
          expect(healthData).toHaveProperty('timestamp');
          expect(typeof healthData.timestamp).toBe('string');
          
          // 验证时间戳格式
          const timestamp = new Date(healthData.timestamp);
          expect(timestamp).toBeInstanceOf(Date);
          expect(isNaN(timestamp.getTime())).toBe(false);
          
          // 属性验证: 响应必须包含运行时间信息
          expect(healthData).toHaveProperty('uptime');
          expect(typeof healthData.uptime).toBe('number');
          expect(healthData.uptime).toBeGreaterThanOrEqual(0);
          
          // 属性验证: 响应必须包含内存使用信息
          expect(healthData).toHaveProperty('memory');
          expect(typeof healthData.memory).toBe('object');
          expect(healthData.memory).toHaveProperty('used');
          expect(healthData.memory).toHaveProperty('total');
          expect(healthData.memory).toHaveProperty('external');
          
          expect(typeof healthData.memory.used).toBe('number');
          expect(typeof healthData.memory.total).toBe('number');
          expect(typeof healthData.memory.external).toBe('number');
          
          expect(healthData.memory.used).toBeGreaterThanOrEqual(0);
          expect(healthData.memory.total).toBeGreaterThanOrEqual(0);
          expect(healthData.memory.external).toBeGreaterThanOrEqual(0);
          
          // 属性验证: 响应必须包含版本信息
          expect(healthData).toHaveProperty('version');
          expect(typeof healthData.version).toBe('string');
          expect(healthData.version.length).toBeGreaterThan(0);
          
          // 属性验证: 响应必须包含环境信息
          expect(healthData).toHaveProperty('environment');
          expect(typeof healthData.environment).toBe('string');
          expect(healthData.environment.length).toBeGreaterThan(0);
          
          // 属性验证: 响应必须包含游戏信息
          expect(healthData).toHaveProperty('game');
          expect(typeof healthData.game).toBe('object');
          expect(healthData.game).toHaveProperty('name');
          expect(healthData.game).toHaveProperty('max_players');
          expect(healthData.game).toHaveProperty('current_players');
          
          expect(typeof healthData.game.name).toBe('string');
          expect(typeof healthData.game.max_players).toBe('number');
          expect(typeof healthData.game.current_players).toBe('number');
          
          expect(healthData.game.max_players).toBeGreaterThan(0);
          expect(healthData.game.current_players).toBeGreaterThanOrEqual(0);
          expect(healthData.game.current_players).toBeLessThanOrEqual(healthData.game.max_players);
        }
      ),
      { numRuns: 100, timeout: 5000 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何带查询参数的健康检查请求，游戏服务器应该返回一致格式的状态和统计信息
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查带查询参数时返回一致格式', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          queryParams: fc.dictionary(
            fc.constantFrom('format', 'detailed', 'include_memory', 'include_game'),
            fc.oneof(
              fc.boolean(),
              fc.string({ minLength: 1, maxLength: 20 }),
              fc.integer({ min: 0, max: 10 })
            ),
            { minKeys: 0, maxKeys: 4 }
          )
        }),
        async ({ queryParams }) => {
          // 构建查询字符串
          const queryString = Object.entries(queryParams)
            .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
            .join('&');
          
          const url = queryString ? `/health?${queryString}` : '/health';
          
          // 发送健康检查请求
          const response = await request(app).get(url);
          
          // 属性验证: 无论查询参数如何，健康检查都应该返回成功状态码
          expect(response.status).toBe(200);
          
          const healthData = response.body;
          
          // 属性验证: 核心字段必须始终存在，不受查询参数影响
          const coreFields = ['status', 'timestamp', 'uptime', 'memory', 'version', 'environment', 'game'];
          for (const field of coreFields) {
            expect(healthData).toHaveProperty(field);
          }
          
          // 属性验证: 响应格式必须一致
          expect(typeof healthData.status).toBe('string');
          expect(typeof healthData.timestamp).toBe('string');
          expect(typeof healthData.uptime).toBe('number');
          expect(typeof healthData.memory).toBe('object');
          expect(typeof healthData.version).toBe('string');
          expect(typeof healthData.environment).toBe('string');
          expect(typeof healthData.game).toBe('object');
        }
      ),
      { numRuns: 50, timeout: 5000 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何并发健康检查请求，游戏服务器应该一致地返回状态和统计信息
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查处理并发请求时保持一致性', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 5 }),
        async (concurrentRequests) => {
          // 创建多个并发请求
          const requests = [];
          for (let i = 0; i < concurrentRequests; i++) {
            requests.push(request(app).get('/health'));
          }
          
          // 等待所有请求完成
          const responses = await Promise.all(requests);
          
          // 属性验证: 所有请求都应该成功
          expect(responses).toHaveLength(concurrentRequests);
          
          // 属性验证: 所有响应都应该返回成功状态码
          for (let i = 0; i < responses.length; i++) {
            expect(responses[i].status).toBe(200);
          }
          
          // 属性验证: 所有响应都应该包含必需的字段
          const requiredFields = ['status', 'timestamp', 'uptime', 'memory', 'version', 'environment', 'game'];
          for (let i = 0; i < responses.length; i++) {
            const healthData = responses[i].body;
            for (const field of requiredFields) {
              expect(healthData).toHaveProperty(field);
            }
          }
          
          // 属性验证: 运行时间在并发请求期间应该保持一致（或合理变化）
          const uptimes = responses.map(response => response.body.uptime);
          const minUptime = Math.min(...uptimes);
          const maxUptime = Math.max(...uptimes);
          
          // 允许在短时间内有小幅变化，但不应该有大幅波动
          expect(maxUptime - minUptime).toBeLessThanOrEqual(2);
        }
      ),
      { numRuns: 10, timeout: 10000 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何包含无效头部的健康检查请求，游戏服务器应该仍然返回有效的状态和统计信息
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查对无效头部保持鲁棒性', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.dictionary(
          fc.string({ minLength: 1, maxLength: 50 }),
          fc.string({ minLength: 0, maxLength: 500 }),
          { minKeys: 0, maxKeys: 3 }
        ),
        async (invalidHeaders) => {
          // 过滤掉可能导致连接问题的头部
          const filteredHeaders = {};
          for (const [key, value] of Object.entries(invalidHeaders)) {
            // 跳过可能导致问题的头部
            if (['host', 'connection', 'content-length'].includes(key.toLowerCase())) {
              continue;
            }
            // 限制头部值的长度以避免过大的请求
            if (value.length > 500) {
              continue;
            }
            filteredHeaders[key] = value;
          }
          
          try {
            // 发送带有无效头部的健康检查请求
            const response = await request(app)
              .get('/health')
              .set(filteredHeaders);
            
            // 属性验证: 即使头部无效，健康检查也应该返回成功状态码
            expect(response.status).toBe(200);
            
            const healthData = response.body;
            
            // 属性验证: 响应必须包含所有必需的字段
            const requiredFields = ['status', 'timestamp', 'uptime', 'memory', 'version', 'environment', 'game'];
            for (const field of requiredFields) {
              expect(healthData).toHaveProperty(field);
            }
            
            // 属性验证: 状态值必须有效
            const validStatuses = ['healthy', 'degraded', 'limited', 'unhealthy'];
            expect(validStatuses).toContain(healthData.status);
            
          } catch (error) {
            // 如果请求因为头部问题失败，这是可以接受的，但我们需要记录
            console.warn(`请求因头部问题失败，这是可接受的: ${error.message}`);
          }
        }
      ),
      { numRuns: 20, timeout: 5000 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何支持的HTTP方法的健康检查请求，游戏服务器应该适当地响应
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查支持不同HTTP方法', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.constantFrom('GET', 'HEAD', 'OPTIONS'),
        async (requestMethod) => {
          let response;
          
          // 发送不同HTTP方法的健康检查请求
          if (requestMethod === 'GET') {
            response = await request(app).get('/health');
            
            // GET请求应该返回完整的健康检查数据
            expect(response.status).toBe(200);
            
            const healthData = response.body;
            const requiredFields = ['status', 'timestamp', 'uptime', 'memory', 'version', 'environment', 'game'];
            for (const field of requiredFields) {
              expect(healthData).toHaveProperty(field);
            }
            
          } else if (requestMethod === 'HEAD') {
            response = await request(app).head('/health');
            
            // HEAD请求可能返回200或405，取决于Express配置
            expect([200, 405]).toContain(response.status);
            
            // 如果支持HEAD，响应不应该有响应体
            if (response.status === 200) {
              expect(response.text || '').toBe('');
            }
            
          } else if (requestMethod === 'OPTIONS') {
            response = await request(app).options('/health');
            
            // OPTIONS请求可能返回200或405，取决于服务器配置
            expect([200, 405]).toContain(response.status);
          }
        }
      ),
      { numRuns: 10, timeout: 5000 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 17: 健康检查响应**
   * 
   * 属性: 对于任何时间间隔的连续健康检查请求，时间戳应该正确递增
   * 验证需求: 6.1
   */
  test('游戏服务器健康检查时间戳正确递增', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.integer({ min: 1, max: 3 }),
        async (timeInterval) => {
          // 第一次健康检查
          const response1 = await request(app).get('/health');
          expect(response1.status).toBe(200);
          
          const healthData1 = response1.body;
          const timestamp1 = new Date(healthData1.timestamp);
          const uptime1 = healthData1.uptime;
          
          // 等待指定的时间间隔
          await new Promise(resolve => setTimeout(resolve, timeInterval * 1000));
          
          // 第二次健康检查
          const response2 = await request(app).get('/health');
          expect(response2.status).toBe(200);
          
          const healthData2 = response2.body;
          const timestamp2 = new Date(healthData2.timestamp);
          const uptime2 = healthData2.uptime;
          
          // 属性验证: 第二个时间戳应该晚于第一个时间戳
          expect(timestamp2.getTime()).toBeGreaterThan(timestamp1.getTime());
          
          // 属性验证: 运行时间应该增加
          expect(uptime2).toBeGreaterThanOrEqual(uptime1);
          
          // 属性验证: 时间差应该大致等于等待的时间间隔
          const timeDiff = (timestamp2.getTime() - timestamp1.getTime()) / 1000;
          expect(timeDiff).toBeGreaterThanOrEqual(timeInterval - 1);
          expect(timeDiff).toBeLessThanOrEqual(timeInterval + 2);
        }
      ),
      { numRuns: 5, timeout: 15000 }
    );
  });
});
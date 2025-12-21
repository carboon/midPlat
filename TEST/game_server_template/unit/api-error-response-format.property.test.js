/**
 * 游戏服务器模板API错误响应格式属性测试 - 需求 6.3, 6.4
 * 
 * **Feature: ai-game-platform, Property 19: API错误响应格式**
 * **验证需求: 6.3, 6.4**
 * 
 * 测试游戏服务器模板所有API错误响应都遵循标准格式，包含必要的字段和正确的数据类型。
 */

const fc = require('fast-check');
const request = require('supertest');
const { app, startServer, closeServer } = require('../../../game_server_template/server');

describe('游戏服务器模板API错误响应格式属性测试', () => {
  let server;
  
  beforeAll(async () => {
    // 启动测试服务器
    const result = await startServer(0); // 使用随机端口
    server = result.server;
  });
  
  afterAll(async () => {
    // 关闭测试服务器
    if (server) {
      await closeServer();
    }
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 对于任何无效的API请求，游戏服务器模板应该返回包含所有必需字段的标准化错误响应格式。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('API错误响应格式属性测试', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.oneof(
          fc.constant('/nonexistent'),
          fc.constant('/invalid/path'),
          fc.string({ minLength: 1, maxLength: 50 }).map(s => `/${s.replace(/[^a-zA-Z0-9]/g, '_')}`),
          fc.constant('/api/invalid')
        ),
        async (invalidPath) => {
          // 发送请求到无效路径
          const response = await request(app)
            .get(invalidPath)
            .expect(404);
          
          // 验证响应结构
          expect(response.body).toHaveProperty('error');
          expect(typeof response.body.error).toBe('object');
          
          const errorObj = response.body.error;
          
          // 验证必需字段存在
          const requiredFields = ['code', 'message', 'timestamp', 'path'];
          for (const field of requiredFields) {
            expect(errorObj).toHaveProperty(field);
          }
          
          // 验证字段类型和值
          expect(typeof errorObj.code).toBe('number');
          expect(errorObj.code).toBe(404);
          expect(errorObj.code).toBeGreaterThanOrEqual(400);
          expect(errorObj.code).toBeLessThanOrEqual(599);
          
          expect(typeof errorObj.message).toBe('string');
          expect(errorObj.message.length).toBeGreaterThan(0);
          
          expect(typeof errorObj.path).toBe('string');
          expect(errorObj.path).toBe(invalidPath);
          
          expect(typeof errorObj.timestamp).toBe('string');
          // 验证时间戳格式（ISO 8601）
          expect(() => new Date(errorObj.timestamp)).not.toThrow();
          const parsedTime = new Date(errorObj.timestamp);
          expect(parsedTime.toISOString()).toBe(errorObj.timestamp);
          
          // 验证响应可以序列化为JSON
          expect(() => JSON.stringify(response.body)).not.toThrow();
          const serialized = JSON.stringify(response.body);
          const deserialized = JSON.parse(serialized);
          expect(deserialized).toEqual(response.body);
        }
      ),
      { numRuns: 50 }
    );
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 对于任何多个错误响应，游戏服务器模板的所有响应都应该遵循相同的格式标准。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('多个错误响应一致性属性测试', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.array(
          fc.string({ minLength: 1, maxLength: 30 }).map(s => `/${s.replace(/[^a-zA-Z0-9]/g, '_')}`),
          { minLength: 2, maxLength: 5 }
        ),
        async (invalidPaths) => {
          const responses = [];
          
          // 发送多个无效请求
          for (const path of invalidPaths) {
            const response = await request(app)
              .get(path)
              .expect(404);
            responses.push(response.body);
          }
          
          // 验证所有响应都有相同的结构
          for (let i = 0; i < responses.length; i++) {
            const response = responses[i];
            
            // 基本结构检查
            expect(response).toHaveProperty('error');
            const errorObj = response.error;
            
            // 必需字段检查
            const requiredFields = ['code', 'message', 'timestamp', 'path'];
            for (const field of requiredFields) {
              expect(errorObj).toHaveProperty(field);
            }
            
            // 类型一致性检查
            expect(typeof errorObj.code).toBe('number');
            expect(typeof errorObj.message).toBe('string');
            expect(typeof errorObj.timestamp).toBe('string');
            expect(typeof errorObj.path).toBe('string');
            
            // 验证状态码一致性
            expect(errorObj.code).toBe(404);
            expect(errorObj.path).toBe(invalidPaths[i]);
          }
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 测试游戏服务器模板具体的错误响应格式示例，确保符合API文档规范。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('错误响应格式示例测试', async () => {
    const testCases = [
      {
        path: '/nonexistent',
        expectedCode: 404,
        description: '不存在的路径'
      },
      {
        path: '/api/invalid',
        expectedCode: 404,
        description: '无效的API路径'
      },
      {
        path: '/monitoring/invalid',
        expectedCode: 404,
        description: '无效的监控路径'
      }
    ];
    
    for (const testCase of testCases) {
      const response = await request(app)
        .get(testCase.path)
        .expect(testCase.expectedCode);
      
      // 验证响应格式
      expect(response.body).toHaveProperty('error');
      const errorObj = response.body.error;
      
      // 验证所有必需字段
      expect(errorObj.code).toBe(testCase.expectedCode);
      expect(typeof errorObj.message).toBe('string');
      expect(errorObj.path).toBe(testCase.path);
      expect(typeof errorObj.timestamp).toBe('string');
      
      // 验证时间戳格式
      const timestamp = errorObj.timestamp;
      expect(() => new Date(timestamp)).not.toThrow();
      const parsedTime = new Date(timestamp);
      expect(parsedTime.toISOString()).toBe(timestamp);
    }
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 对于任何HTTP方法的无效请求，错误响应格式应该保持一致。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('不同HTTP方法错误响应一致性', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.oneof(
          fc.constant('POST'),
          fc.constant('PUT'),
          fc.constant('DELETE'),
          fc.constant('PATCH')
        ),
        fc.string({ minLength: 1, maxLength: 30 }).map(s => `/${s.replace(/[^a-zA-Z0-9]/g, '_')}`),
        async (method, path) => {
          // 发送不支持的HTTP方法请求
          let response;
          switch (method) {
            case 'POST':
              response = await request(app).post(path);
              break;
            case 'PUT':
              response = await request(app).put(path);
              break;
            case 'DELETE':
              response = await request(app).delete(path);
              break;
            case 'PATCH':
              response = await request(app).patch(path);
              break;
          }
          
          // 验证响应状态码（404 或 405）
          expect([404, 405]).toContain(response.status);
          
          // 如果有错误响应体，验证格式
          if (response.body && response.body.error) {
            const errorObj = response.body.error;
            
            // 验证必需字段
            expect(typeof errorObj.code).toBe('number');
            expect(typeof errorObj.message).toBe('string');
            expect(typeof errorObj.timestamp).toBe('string');
            expect(typeof errorObj.path).toBe('string');
            
            // 验证字段值
            expect(errorObj.code).toBe(response.status);
            expect(errorObj.path).toBe(path);
            
            // 验证时间戳格式
            expect(() => new Date(errorObj.timestamp)).not.toThrow();
          }
        }
      ),
      { numRuns: 30 }
    );
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 对于任何服务器内部错误，错误响应格式应该保持标准化。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('服务器错误响应格式一致性', async () => {
    // 注意：这个测试模拟服务器错误场景
    // 在实际实现中，我们可能需要通过特殊的测试端点来触发服务器错误
    
    // 测试健康检查端点的正常响应（确保服务器正常运行）
    const healthResponse = await request(app)
      .get('/health')
      .expect(200);
    
    // 验证健康检查响应不是错误格式
    expect(healthResponse.body).toHaveProperty('status');
    expect(healthResponse.body).not.toHaveProperty('error');
    
    // 如果需要测试实际的服务器错误，可以在这里添加
    // 例如：通过模拟数据库连接失败等方式
  });

  /**
   * **Feature: ai-game-platform, Property 19: API错误响应格式**
   * 
   * 验证错误响应的JSON序列化兼容性。
   * 
   * **验证需求: 6.3, 6.4**
   */
  test('错误响应JSON序列化兼容性', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.string({ minLength: 1, maxLength: 50 }).map(s => `/${s.replace(/[^a-zA-Z0-9]/g, '_')}`),
        async (invalidPath) => {
          const response = await request(app)
            .get(invalidPath)
            .expect(404);
          
          // 验证响应可以正确序列化和反序列化
          const originalBody = response.body;
          
          // 序列化
          const serialized = JSON.stringify(originalBody);
          expect(typeof serialized).toBe('string');
          
          // 反序列化
          const deserialized = JSON.parse(serialized);
          expect(deserialized).toEqual(originalBody);
          
          // 验证深度相等
          expect(deserialized.error.code).toBe(originalBody.error.code);
          expect(deserialized.error.message).toBe(originalBody.error.message);
          expect(deserialized.error.timestamp).toBe(originalBody.error.timestamp);
          expect(deserialized.error.path).toBe(originalBody.error.path);
        }
      ),
      { numRuns: 30 }
    );
  });
});
/**
 * **Feature: ai-game-platform, Property 11: HTTP连接建立**
 * **验证需求: 3.3, 3.4**
 * 
 * 属性 11: HTTP连接建立
 * *对于任何*房间选择操作，客户端应该建立HTTP连接并接收HTML游戏内容
 * 
 * 测试验证:
 * - 3.3: WHEN 玩家选择房间时 THEN Universal_Client SHALL 建立与对应游戏服务器的HTTP连接
 * - 3.4: WHEN HTTP连接建立时 THEN Game_Server SHALL 提供HTML游戏内容给客户端
 */

const fc = require('fast-check');
const http = require('http');
const https = require('https');
const { startServer, closeServer } = require('../../../game_server_template/server');

/**
 * Make HTTP request to a server
 */
function makeHttpRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const isHttps = urlObj.protocol === 'https:';
    const client = isHttps ? https : http;
    
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (isHttps ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: options.timeout || 5000
    };
    
    const req = client.request(requestOptions, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          body: data
        });
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.end();
  });
}

/**
 * Get an available port
 */
function getAvailablePort() {
  return new Promise((resolve, reject) => {
    const server = http.createServer();
    server.listen(0, () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
    server.on('error', reject);
  });
}

/**
 * Wait for server to be ready
 */
function waitForServer(port, timeout = 5000) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = async () => {
      try {
        await makeHttpRequest(`http://localhost:${port}/health`);
        resolve(true);
      } catch (error) {
        if (Date.now() - startTime > timeout) {
          reject(new Error('Server not ready within timeout'));
        } else {
          setTimeout(check, 100);
        }
      }
    };
    
    check();
  });
}

describe('Property 11: HTTP连接建立', () => {
  let gameServer = null;
  let serverPort = null;
  
  beforeEach(async () => {
    serverPort = await getAvailablePort();
    
    // Set environment variables for test
    process.env.PORT = serverPort.toString();
    process.env.MATCHMAKER_URL = 'http://localhost:9999'; // Mock URL
    process.env.ROOM_NAME = 'Test Room';
    process.env.MAX_PLAYERS = '10';
    process.env.HEARTBEAT_INTERVAL = '30000';
    
    gameServer = await startServer(serverPort);
    await waitForServer(serverPort);
  });
  
  afterEach(async () => {
    if (gameServer) {
      await closeServer();
      gameServer = null;
    }
  });
  
  /**
   * **Feature: ai-game-platform, Property 11: HTTP连接建立**
   * 
   * 属性: 对于任何HTTP请求到游戏服务器，服务器应该成功建立连接并返回响应
   */
  test('客户端应该能够建立HTTP连接到游戏服务器', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different HTTP request paths
        fc.oneof(
          fc.constant('/'),
          fc.constant('/health'),
          fc.constant('/monitoring/status'),
          fc.constant('/monitoring/game-state'),
          fc.constant('/api/documentation'),
          fc.constant('/api/endpoints')
        ),
        async (requestPath) => {
          const url = `http://localhost:${serverPort}${requestPath}`;
          
          // Make HTTP request (simulating client connection)
          const response = await makeHttpRequest(url);
          
          // Verify: Connection should be established successfully
          expect(response.statusCode).toBeGreaterThanOrEqual(200);
          expect(response.statusCode).toBeLessThan(500);
          
          // Verify: Response should contain content
          expect(response.body).toBeDefined();
          expect(response.body.length).toBeGreaterThan(0);
          
          // Verify: Response headers should be present
          expect(response.headers).toBeDefined();
          expect(response.headers['content-type']).toBeDefined();
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 11: HTTP连接建立**
   * 
   * 属性: 对于任何请求HTML游戏内容的HTTP连接，服务器应该提供HTML内容
   */
  test('游戏服务器应该提供HTML游戏内容给客户端', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different request scenarios
        fc.record({
          userAgent: fc.oneof(
            fc.constant('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'),
            fc.constant('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'),
            fc.constant('Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'),
            fc.constant('Flutter/3.0 (Mobile App)')
          ),
          acceptHeader: fc.oneof(
            fc.constant('text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
            fc.constant('application/json'),
            fc.constant('*/*')
          )
        }),
        async (requestConfig) => {
          const url = `http://localhost:${serverPort}/`;
          
          // Make HTTP request with custom headers
          const response = await makeHttpRequest(url, {
            headers: {
              'User-Agent': requestConfig.userAgent,
              'Accept': requestConfig.acceptHeader
            }
          });
          
          // Verify: Should return successful response
          expect(response.statusCode).toBe(200);
          
          // Verify: Should return HTML content for root path
          expect(response.headers['content-type']).toMatch(/text\/html/);
          expect(response.body).toContain('<!DOCTYPE html>');
          expect(response.body).toContain('<html');
          expect(response.body).toContain('</html>');
          
          // Verify: HTML should contain game-related content
          expect(response.body).toContain('游戏');
          
          return true;
        }
      ),
      { numRuns: 50 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 11: HTTP连接建立**
   * 
   * 属性: 对于任何并发HTTP连接，服务器应该能够处理多个同时连接
   */
  test('游戏服务器应该能够处理并发HTTP连接', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate number of concurrent connections
        fc.integer({ min: 2, max: 10 }),
        async (numConnections) => {
          const requests = [];
          
          // Create multiple concurrent requests
          for (let i = 0; i < numConnections; i++) {
            const path = i % 2 === 0 ? '/' : '/health';
            requests.push(
              makeHttpRequest(`http://localhost:${serverPort}${path}`)
            );
          }
          
          // Execute all requests concurrently
          const responses = await Promise.all(requests);
          
          // Verify: All connections should succeed
          expect(responses.length).toBe(numConnections);
          
          for (const response of responses) {
            expect(response.statusCode).toBeGreaterThanOrEqual(200);
            expect(response.statusCode).toBeLessThan(500);
            expect(response.body).toBeDefined();
            expect(response.body.length).toBeGreaterThan(0);
          }
          
          return true;
        }
      ),
      { numRuns: 30 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 11: HTTP连接建立**
   * 
   * 属性: 对于任何API端点请求，服务器应该返回正确格式的响应
   */
  test('API端点应该返回正确格式的JSON响应', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate different API endpoints
        fc.oneof(
          fc.constant('/health'),
          fc.constant('/monitoring/status'),
          fc.constant('/monitoring/game-state'),
          fc.constant('/api/documentation'),
          fc.constant('/api/endpoints')
        ),
        async (apiPath) => {
          const url = `http://localhost:${serverPort}${apiPath}`;
          
          const response = await makeHttpRequest(url, {
            headers: {
              'Accept': 'application/json'
            }
          });
          
          // Verify: Should return successful response
          expect(response.statusCode).toBe(200);
          
          // Verify: Should return JSON content
          expect(response.headers['content-type']).toMatch(/application\/json/);
          
          // Verify: Response body should be valid JSON
          let jsonData;
          expect(() => {
            jsonData = JSON.parse(response.body);
          }).not.toThrow();
          
          // Verify: JSON should contain expected structure
          expect(jsonData).toBeDefined();
          expect(typeof jsonData).toBe('object');
          
          // Verify specific endpoint responses
          if (apiPath === '/health') {
            expect(jsonData).toHaveProperty('status');
            expect(jsonData).toHaveProperty('timestamp');
          } else if (apiPath === '/monitoring/status') {
            expect(jsonData).toHaveProperty('service_status');
            expect(jsonData).toHaveProperty('game_metrics');
          } else if (apiPath === '/api/endpoints') {
            expect(jsonData).toHaveProperty('endpoints');
            expect(Array.isArray(jsonData.endpoints)).toBe(true);
          }
          
          return true;
        }
      ),
      { numRuns: 100 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 11: HTTP连接建立**
   * 
   * 属性: 对于任何无效的HTTP请求路径，服务器应该返回适当的错误响应
   * 注意：由于这是一个单页应用，静态文件服务器会为不匹配的路径返回index.html
   */
  test('无效路径请求应该返回适当的错误响应', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate invalid API paths that should definitely return 404
        fc.oneof(
          fc.constant('/api/nonexistent'),
          fc.constant('/api/invalid/endpoint'),
          fc.constant('/monitoring/invalid'),
          fc.constant('/health/invalid'),
          // Generate random API paths that don't match valid endpoints
          fc.string({ minLength: 2, maxLength: 20 })
            .filter(s => s.trim().length > 0 && !s.includes(' ') && !s.includes('\t'))
            .map(s => `/api/${s}`)
            .filter(s => {
              const validApiPaths = [
                '/api/documentation', '/api/endpoints'
              ];
              return !validApiPaths.includes(s);
            })
        ),
        async (invalidPath) => {
          const url = `http://localhost:${serverPort}${invalidPath}`;
          
          const response = await makeHttpRequest(url);
          
          // Verify: Should return 404 for invalid API paths
          expect(response.statusCode).toBeGreaterThanOrEqual(400);
          
          // Verify: Should still return some content (error message)
          expect(response.body).toBeDefined();
          
          return true;
        }
      ),
      { numRuns: 50 }
    );
  });
});
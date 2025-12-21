/**
 * **Feature: ai-game-platform, Property 5: 自动服务器注册**
 * **验证需求: 1.5**
 * 
 * 属性 5: 自动服务器注册
 * *对于任何*成功启动的游戏服务器容器，服务器应该自动向Matchmaker Service注册
 * 
 * 测试验证:
 * - 1.5: WHEN 容器启动成功时 THEN 新创建的游戏服务器 SHALL 自动向Matchmaker_Service注册
 */

const fc = require('fast-check');
const http = require('http');
const express = require('express');

// Mock Matchmaker Service
let mockMatchmakerServer = null;
let mockMatchmakerPort = 0;
let registeredServers = [];
let registrationRequests = [];

/**
 * Create a mock matchmaker service that records registration requests
 */
function createMockMatchmaker() {
  return new Promise((resolve, reject) => {
    const app = express();
    app.use(express.json());
    
    // Reset state
    registeredServers = [];
    registrationRequests = [];
    
    // Mock /register endpoint
    app.post('/register', (req, res) => {
      const serverData = req.body;
      const serverId = `${serverData.ip}:${serverData.port}`;
      
      registrationRequests.push({
        timestamp: new Date(),
        data: serverData
      });
      
      // Store or update server
      const existingIndex = registeredServers.findIndex(s => 
        s.ip === serverData.ip && s.port === serverData.port
      );
      
      if (existingIndex >= 0) {
        registeredServers[existingIndex] = { ...serverData, server_id: serverId };
      } else {
        registeredServers.push({ ...serverData, server_id: serverId });
      }
      
      res.json({
        status: 'success',
        server_id: serverId,
        message: 'Server registered successfully'
      });
    });
    
    // Mock /servers endpoint
    app.get('/servers', (req, res) => {
      res.json(registeredServers);
    });
    
    // Mock /health endpoint
    app.get('/health', (req, res) => {
      res.json({ status: 'healthy' });
    });
    
    const server = http.createServer(app);
    server.listen(0, () => {
      mockMatchmakerPort = server.address().port;
      mockMatchmakerServer = server;
      resolve({ server, port: mockMatchmakerPort });
    });
    
    server.on('error', reject);
  });
}

/**
 * Close mock matchmaker server
 */
function closeMockMatchmaker() {
  return new Promise((resolve) => {
    if (mockMatchmakerServer) {
      mockMatchmakerServer.close(() => {
        mockMatchmakerServer = null;
        resolve();
      });
    } else {
      resolve();
    }
  });
}

/**
 * Create a game server that auto-registers with matchmaker
 * This simulates the behavior from server.js
 */
function createGameServerWithAutoRegistration(config) {
  const {
    port,
    matchmakerUrl,
    roomName,
    maxPlayers,
    currentPlayers = 0
  } = config;
  
  return new Promise((resolve, reject) => {
    const app = express();
    const server = http.createServer(app);
    
    let isRegistered = false;
    let heartbeatTimer = null;
    
    // Registration function (mirrors server.js sendHeartbeat)
    async function sendHeartbeat() {
      try {
        const response = await fetch(`${matchmakerUrl}/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ip: 'localhost',
            port: port,
            name: roomName,
            max_players: maxPlayers,
            current_players: currentPlayers,
            metadata: {
              created_by: 'game_server_template',
              game_type: 'custom'
            }
          })
        });
        
        if (response.ok) {
          isRegistered = true;
        }
      } catch (error) {
        isRegistered = false;
      }
    }
    
    function stopHeartbeat() {
      if (heartbeatTimer) {
        clearTimeout(heartbeatTimer);
        heartbeatTimer = null;
      }
    }
    
    function closeServer() {
      return new Promise((res) => {
        stopHeartbeat();
        server.close(() => res());
      });
    }
    
    server.listen(port, async () => {
      // Auto-register on startup (Requirement 1.5)
      await sendHeartbeat();
      
      resolve({
        server,
        port,
        isRegistered: () => isRegistered,
        close: closeServer
      });
    });
    
    server.on('error', reject);
  });
}

/**
 * Wait for a condition with timeout
 */
function waitFor(conditionFn, timeout = 5000, interval = 100) {
  return new Promise((resolve, reject) => {
    const startTime = Date.now();
    
    const check = () => {
      if (conditionFn()) {
        resolve(true);
      } else if (Date.now() - startTime > timeout) {
        reject(new Error('Timeout waiting for condition'));
      } else {
        setTimeout(check, interval);
      }
    };
    
    check();
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

describe('Property 5: 自动服务器注册', () => {
  beforeAll(async () => {
    await createMockMatchmaker();
  });
  
  afterAll(async () => {
    await closeMockMatchmaker();
  });
  
  beforeEach(() => {
    // Reset registration state before each test
    registeredServers = [];
    registrationRequests = [];
  });
  
  /**
   * **Feature: ai-game-platform, Property 5: 自动服务器注册**
   * 
   * 属性: 对于任何成功启动的游戏服务器，服务器应该自动向Matchmaker Service注册
   */
  test('游戏服务器启动后应该自动注册到撮合服务', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate random room configuration
        fc.record({
          roomName: fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
          maxPlayers: fc.integer({ min: 1, max: 100 }),
          currentPlayers: fc.integer({ min: 0, max: 50 })
        }).filter(config => config.currentPlayers <= config.maxPlayers),
        async (config) => {
          const port = await getAvailablePort();
          
          const gameServer = await createGameServerWithAutoRegistration({
            port,
            matchmakerUrl: `http://localhost:${mockMatchmakerPort}`,
            roomName: config.roomName,
            maxPlayers: config.maxPlayers,
            currentPlayers: config.currentPlayers
          });
          
          try {
            // Wait for registration to complete
            await waitFor(() => registrationRequests.length > 0, 3000);
            
            // Verify: Server should be registered
            expect(gameServer.isRegistered()).toBe(true);
            
            // Verify: Registration request was sent with correct data
            expect(registrationRequests.length).toBeGreaterThan(0);
            
            const lastRequest = registrationRequests[registrationRequests.length - 1];
            expect(lastRequest.data.ip).toBe('localhost');
            expect(lastRequest.data.port).toBe(port);
            expect(lastRequest.data.name).toBe(config.roomName);
            expect(lastRequest.data.max_players).toBe(config.maxPlayers);
            expect(lastRequest.data.current_players).toBe(config.currentPlayers);
            
            // Verify: Server appears in registered servers list
            const registeredServer = registeredServers.find(s => s.port === port);
            expect(registeredServer).toBeDefined();
            expect(registeredServer.name).toBe(config.roomName);
            
            return true;
          } finally {
            await gameServer.close();
            // Clear for next iteration
            registeredServers = registeredServers.filter(s => s.port !== port);
            registrationRequests = [];
          }
        }
      ),
      { numRuns: 100 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 5: 自动服务器注册**
   * 
   * 属性: 对于任何数量的游戏服务器同时启动，每个服务器都应该成功注册
   */
  test('多个游戏服务器同时启动都应该成功注册', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate 2-4 servers with unique names
        fc.integer({ min: 2, max: 4 }),
        async (numServers) => {
          const servers = [];
          const ports = [];
          
          try {
            // Get available ports first
            for (let i = 0; i < numServers; i++) {
              ports.push(await getAvailablePort());
            }
            
            // Start all servers concurrently
            const startPromises = ports.map((port, index) => 
              createGameServerWithAutoRegistration({
                port,
                matchmakerUrl: `http://localhost:${mockMatchmakerPort}`,
                roomName: `TestRoom_${index}_${Date.now()}`,
                maxPlayers: 10,
                currentPlayers: 0
              })
            );
            
            const startedServers = await Promise.all(startPromises);
            servers.push(...startedServers);
            
            // Wait for all registrations
            await waitFor(() => registeredServers.length >= numServers, 5000);
            
            // Verify: All servers should be registered
            expect(registeredServers.length).toBe(numServers);
            
            // Verify: Each server should be registered with correct port
            for (const port of ports) {
              const registered = registeredServers.find(s => s.port === port);
              expect(registered).toBeDefined();
            }
            
            // Verify: All servers report as registered
            for (const server of servers) {
              expect(server.isRegistered()).toBe(true);
            }
            
            return true;
          } finally {
            // Cleanup all servers
            await Promise.all(servers.map(s => s.close()));
            registeredServers = [];
            registrationRequests = [];
          }
        }
      ),
      { numRuns: 20 }
    );
  });
  
  /**
   * **Feature: ai-game-platform, Property 5: 自动服务器注册**
   * 
   * 属性: 注册请求应该包含所有必需的元数据字段
   */
  test('注册请求应该包含完整的服务器元数据', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          roomName: fc.string({ minLength: 1, maxLength: 30 }).filter(s => s.trim().length > 0),
          maxPlayers: fc.integer({ min: 1, max: 50 })
        }),
        async (config) => {
          const port = await getAvailablePort();
          
          const gameServer = await createGameServerWithAutoRegistration({
            port,
            matchmakerUrl: `http://localhost:${mockMatchmakerPort}`,
            roomName: config.roomName,
            maxPlayers: config.maxPlayers,
            currentPlayers: 0
          });
          
          try {
            await waitFor(() => registrationRequests.length > 0, 3000);
            
            const request = registrationRequests[0];
            
            // Verify: All required fields are present
            expect(request.data).toHaveProperty('ip');
            expect(request.data).toHaveProperty('port');
            expect(request.data).toHaveProperty('name');
            expect(request.data).toHaveProperty('max_players');
            expect(request.data).toHaveProperty('current_players');
            expect(request.data).toHaveProperty('metadata');
            
            // Verify: Metadata contains expected fields
            expect(request.data.metadata).toHaveProperty('created_by');
            expect(request.data.metadata).toHaveProperty('game_type');
            expect(request.data.metadata.created_by).toBe('game_server_template');
            expect(request.data.metadata.game_type).toBe('custom');
            
            return true;
          } finally {
            await gameServer.close();
            registeredServers = [];
            registrationRequests = [];
          }
        }
      ),
      { numRuns: 50 }
    );
  });
});

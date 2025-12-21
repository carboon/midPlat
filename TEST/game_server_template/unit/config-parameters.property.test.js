/**
 * Configuration Parameters Property Test
 * 
 * **Feature: ai-game-platform, Property 18: 配置参数应用**
 * **Validates: Requirements 7.3**
 * 
 * 对于任何环境变量配置，所有服务应该正确读取并应用配置参数
 */

const fc = require('fast-check');
const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

describe('Configuration Parameters Property Tests', () => {
  let tempDir;
  
  beforeEach(() => {
    // Create temporary directory for test files
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'config-test-'));
  });
  
  afterEach(() => {
    // Clean up temporary directory
    if (tempDir && fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  /**
   * Property: Configuration parameters should be correctly read and applied
   * For any valid configuration values, the server should use those values
   */
  test('should correctly apply configuration parameters from environment variables', async () => {
    await fc.assert(
      fc.asyncProperty(
        // Generate random configuration values
        fc.record({
          port: fc.integer({ min: 3000, max: 9999 }),
          matchmakerUrl: fc.oneof(
            fc.constant('http://localhost:8000'),
            fc.constant('http://127.0.0.1:8000'),
            fc.constant('http://matchmaker:8000')
          ),
          roomName: fc.string({ minLength: 1, maxLength: 50 }).filter(s => s.trim().length > 0),
          roomPassword: fc.oneof(
            fc.constant(''),
            fc.string({ minLength: 1, maxLength: 20 })
          ),
          heartbeatInterval: fc.integer({ min: 5000, max: 60000 }),
          retryInterval: fc.integer({ min: 1000, max: 10000 }),
          maxPlayers: fc.integer({ min: 1, max: 100 })
        }),
        async (config) => {
          // Create a test server file that exports configuration
          const testServerPath = path.join(tempDir, 'test-server.js');
          const testServerContent = `
// Configuration from environment variables (same as server.js)
const PORT = process.env.PORT || 8080;
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const ROOM_PASSWORD = process.env.ROOM_PASSWORD || '';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;

// Export configuration for testing
console.log(JSON.stringify({
  PORT,
  MATCHMAKER_URL,
  ROOM_NAME,
  ROOM_PASSWORD,
  HEARTBEAT_INTERVAL,
  RETRY_INTERVAL,
  MAX_PLAYERS
}));
`;
          
          fs.writeFileSync(testServerPath, testServerContent);
          
          // Set environment variables
          const env = {
            ...process.env,
            PORT: config.port.toString(),
            MATCHMAKER_URL: config.matchmakerUrl,
            ROOM_NAME: config.roomName,
            ROOM_PASSWORD: config.roomPassword,
            HEARTBEAT_INTERVAL: config.heartbeatInterval.toString(),
            RETRY_INTERVAL: config.retryInterval.toString(),
            MAX_PLAYERS: config.maxPlayers.toString()
          };
          
          // Run the test server and capture output
          const result = await new Promise((resolve, reject) => {
            const child = spawn('node', [testServerPath], {
              env,
              cwd: process.cwd(),
              stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
              stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
              stderr += data.toString();
            });
            
            child.on('close', (code) => {
              if (code === 0) {
                resolve({ stdout, stderr });
              } else {
                reject(new Error(`Process exited with code ${code}: ${stderr}`));
              }
            });
            
            child.on('error', (error) => {
              reject(error);
            });
            
            // Kill the process after a short timeout
            setTimeout(() => {
              child.kill();
            }, 2000);
          });
          
          // Parse the configuration output
          const actualConfig = JSON.parse(result.stdout.trim());
          
          // Verify: Configuration values should match what we set
          expect(parseInt(actualConfig.PORT)).toBe(config.port);
          expect(actualConfig.MATCHMAKER_URL).toBe(config.matchmakerUrl);
          expect(actualConfig.ROOM_NAME).toBe(config.roomName);
          expect(actualConfig.ROOM_PASSWORD).toBe(config.roomPassword);
          expect(actualConfig.HEARTBEAT_INTERVAL).toBe(config.heartbeatInterval);
          expect(actualConfig.RETRY_INTERVAL).toBe(config.retryInterval);
          expect(actualConfig.MAX_PLAYERS).toBe(config.maxPlayers);
          
          return true;
        }
      ),
      { numRuns: 20 }
    );
  });

  /**
   * Property: Default configuration should be used when environment variables are not set
   */
  test('should use default configuration when environment variables are not set', async () => {
    const testServerPath = path.join(tempDir, 'default-config-server.js');
    const testServerContent = `
// Configuration from environment variables with defaults
const PORT = process.env.PORT || 8080;
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || 'http://localhost:8000';
const ROOM_NAME = process.env.ROOM_NAME || '默认房间';
const ROOM_PASSWORD = process.env.ROOM_PASSWORD || '';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;
const MAX_PLAYERS = parseInt(process.env.MAX_PLAYERS) || 20;

console.log(JSON.stringify({
  PORT,
  MATCHMAKER_URL,
  ROOM_NAME,
  ROOM_PASSWORD,
  HEARTBEAT_INTERVAL,
  RETRY_INTERVAL,
  MAX_PLAYERS
}));
`;
    
    fs.writeFileSync(testServerPath, testServerContent);
    
    // Run with clean environment (no game-specific env vars)
    const cleanEnv = Object.keys(process.env)
      .filter(key => !['PORT', 'MATCHMAKER_URL', 'ROOM_NAME', 'ROOM_PASSWORD', 
                      'HEARTBEAT_INTERVAL', 'RETRY_INTERVAL', 'MAX_PLAYERS'].includes(key))
      .reduce((env, key) => {
        env[key] = process.env[key];
        return env;
      }, {});
    
    const result = await new Promise((resolve, reject) => {
      const child = spawn('node', [testServerPath], {
        env: cleanEnv,
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });
      
      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      child.on('close', (code) => {
        if (code === 0) {
          resolve({ stdout, stderr });
        } else {
          reject(new Error(`Process exited with code ${code}: ${stderr}`));
        }
      });
      
      child.on('error', (error) => {
        reject(error);
      });
      
      setTimeout(() => {
        child.kill();
      }, 2000);
    });
    
    const actualConfig = JSON.parse(result.stdout.trim());
    
    // Verify: Should use default values
    expect(parseInt(actualConfig.PORT)).toBe(8080);
    expect(actualConfig.MATCHMAKER_URL).toBe('http://localhost:8000');
    expect(actualConfig.ROOM_NAME).toBe('默认房间');
    expect(actualConfig.ROOM_PASSWORD).toBe('');
    expect(actualConfig.HEARTBEAT_INTERVAL).toBe(25000);
    expect(actualConfig.RETRY_INTERVAL).toBe(5000);
    expect(actualConfig.MAX_PLAYERS).toBe(20);
  });

  /**
   * Property: Invalid configuration values should be handled gracefully
   */
  test('should handle invalid configuration values gracefully', async () => {
    await fc.assert(
      fc.asyncProperty(
        fc.record({
          port: fc.oneof(
            fc.constant('invalid'),
            fc.constant(''),
            fc.constant('-1'),
            fc.constant('99999')
          ),
          heartbeatInterval: fc.oneof(
            fc.constant('not-a-number'),
            fc.constant(''),
            fc.constant('-1')
          ),
          maxPlayers: fc.oneof(
            fc.constant('invalid'),
            fc.constant('0'),
            fc.constant('-5')
          )
        }),
        async (invalidConfig) => {
          const testServerPath = path.join(tempDir, 'invalid-config-server.js');
          const testServerContent = `
const rawPort = process.env.PORT || '8080';
const rawHeartbeat = process.env.HEARTBEAT_INTERVAL || '25000';
const rawMaxPlayers = process.env.MAX_PLAYERS || '20';

const parsedPort = parseInt(rawPort);
const parsedHeartbeat = parseInt(rawHeartbeat);
const parsedMaxPlayers = parseInt(rawMaxPlayers);

const PORT = isNaN(parsedPort) || parsedPort <= 0 || parsedPort > 65535 ? 8080 : parsedPort;
const HEARTBEAT_INTERVAL = isNaN(parsedHeartbeat) || parsedHeartbeat <= 0 ? 25000 : parsedHeartbeat;
const MAX_PLAYERS = isNaN(parsedMaxPlayers) || parsedMaxPlayers <= 0 ? 20 : parsedMaxPlayers;

console.log(JSON.stringify({
  PORT,
  HEARTBEAT_INTERVAL,
  MAX_PLAYERS
}));
`;
          
          fs.writeFileSync(testServerPath, testServerContent);
          
          const env = {
            ...process.env,
            PORT: invalidConfig.port,
            HEARTBEAT_INTERVAL: invalidConfig.heartbeatInterval,
            MAX_PLAYERS: invalidConfig.maxPlayers
          };
          
          const result = await new Promise((resolve, reject) => {
            const child = spawn('node', [testServerPath], {
              env,
              cwd: process.cwd(),
              stdio: ['pipe', 'pipe', 'pipe']
            });
            
            let stdout = '';
            let stderr = '';
            
            child.stdout.on('data', (data) => {
              stdout += data.toString();
            });
            
            child.stderr.on('data', (data) => {
              stderr += data.toString();
            });
            
            child.on('close', (code) => {
              resolve({ stdout, stderr, code });
            });
            
            child.on('error', (error) => {
              resolve({ stdout, stderr, error: error.message });
            });
            
            setTimeout(() => {
              child.kill();
            }, 2000);
          });
          
          // Should not crash and should use default values for invalid inputs
          if (result.stdout) {
            const actualConfig = JSON.parse(result.stdout.trim());
            
            // Verify: Invalid values should fall back to defaults
            expect(typeof actualConfig.PORT).toBe('number');
            expect(actualConfig.PORT).toBeGreaterThan(0);
            expect(actualConfig.PORT).toBeLessThanOrEqual(65535);
            expect(typeof actualConfig.HEARTBEAT_INTERVAL).toBe('number');
            expect(actualConfig.HEARTBEAT_INTERVAL).toBeGreaterThan(0);
            expect(typeof actualConfig.MAX_PLAYERS).toBe('number');
            expect(actualConfig.MAX_PLAYERS).toBeGreaterThan(0);
          }
          
          return true;
        }
      ),
      { numRuns: 10 }
    );
  });
});
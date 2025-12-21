/**
 * Configuration Parameters Property Test
 * 
 * **Feature: ai-game-platform, Property 18: 配置参数应用**
 * **Validates: Requirements 7.3**
 * 
 * 对于任何环境变量配置，所有服务应该正确读取并应用配置参数
 */

import 'package:flutter_test/flutter_test.dart';
import 'package:universal_game_client/utils/constants.dart';

void main() {
  group('Configuration Parameters Property Tests', () {
    test('should validate configuration correctly', () {
      // Test configuration validation
      final errors = Constants.validateConfiguration();
      
      // Verify: Configuration should be valid
      expect(errors, isEmpty, reason: 'Configuration should be valid: ${errors.join(", ")}');
    });

    test('should provide valid default configuration values', () {
      // Verify: Environment should be valid
      expect(Constants.environment, isIn(['development', 'staging', 'production']));
      
      // Verify: URLs should be valid
      expect(() => Uri.parse(Constants.matchmakerUrl), returnsNormally);
      expect(() => Uri.parse(Constants.gameServerFactoryUrl), returnsNormally);
      
      // Verify: Numeric values should be positive
      expect(Constants.maxRetries, greaterThan(0));
      expect(Constants.roomRefreshInterval, greaterThan(0));
      expect(Constants.maxFileSizeBytes, greaterThan(0));
      expect(Constants.connectionTimeout.inMilliseconds, greaterThan(0));
      expect(Constants.retryDelay.inMilliseconds, greaterThan(0));
      
      // Verify: App info should be non-empty
      expect(Constants.appName, isNotEmpty);
      expect(Constants.appVersion, isNotEmpty);
    });

    test('should provide environment-specific configuration', () {
      // Verify: Development environment has appropriate settings
      if (Constants.isDevelopment) {
        expect(Constants.enableDebugLogs, isTrue);
        expect(Constants.showDetailedErrors, isTrue);
      }
      
      // Verify: Production environment has appropriate settings
      if (Constants.isProduction) {
        expect(Constants.enablePerformanceMonitoring, isTrue);
      }
    });

    test('should provide valid configuration summary', () {
      final summary = Constants.getConfigurationSummary();
      
      // Verify: Summary should contain all required fields
      expect(summary, containsPair('environment', isNotNull));
      expect(summary, containsPair('app_name', isNotNull));
      expect(summary, containsPair('app_version', isNotNull));
      expect(summary, containsPair('matchmaker_url', isNotNull));
      expect(summary, containsPair('game_server_factory_url', isNotNull));
      expect(summary, containsPair('max_retries', isNotNull));
      expect(summary, containsPair('connection_timeout_ms', isNotNull));
      expect(summary, containsPair('max_file_size_mb', isNotNull));
      expect(summary, containsPair('debug_logs_enabled', isNotNull));
      expect(summary, containsPair('performance_monitoring_enabled', isNotNull));
      
      // Verify: Values should be of correct types
      expect(summary['environment'], isA<String>());
      expect(summary['app_name'], isA<String>());
      expect(summary['app_version'], isA<String>());
      expect(summary['matchmaker_url'], isA<String>());
      expect(summary['game_server_factory_url'], isA<String>());
      expect(summary['max_retries'], isA<int>());
      expect(summary['connection_timeout_ms'], isA<int>());
      expect(summary['max_file_size_mb'], isA<String>());
      expect(summary['debug_logs_enabled'], isA<bool>());
      expect(summary['performance_monitoring_enabled'], isA<bool>());
    });

    test('should handle URL configuration correctly', () {
      // Verify: Matchmaker URL should be valid
      final matchmakerUri = Uri.parse(Constants.matchmakerUrl);
      expect(matchmakerUri.scheme, isIn(['http', 'https']));
      expect(matchmakerUri.host, isNotEmpty);
      
      // Verify: Game Server Factory URL should be valid
      final factoryUri = Uri.parse(Constants.gameServerFactoryUrl);
      expect(factoryUri.scheme, isIn(['http', 'https']));
      expect(factoryUri.host, isNotEmpty);
    });

    test('should provide consistent environment-based defaults', () {
      // Property: For any environment, configuration should be internally consistent
      
      // Verify: Development environment has shorter timeouts
      if (Constants.isDevelopment) {
        expect(Constants.connectionTimeout.inSeconds, lessThanOrEqualTo(30));
        expect(Constants.roomRefreshInterval, lessThanOrEqualTo(30));
      }
      
      // Verify: Production environment has longer timeouts
      if (Constants.isProduction) {
        expect(Constants.connectionTimeout.inSeconds, greaterThanOrEqualTo(30));
        expect(Constants.maxRetries, greaterThanOrEqualTo(3));
      }
      
      // Verify: Retry delay should be reasonable
      expect(Constants.retryDelay.inSeconds, lessThanOrEqualTo(10));
      
      // Verify: Cache expiration should be reasonable
      expect(Constants.cacheExpiration.inMinutes, greaterThan(0));
      expect(Constants.cacheExpiration.inMinutes, lessThanOrEqualTo(60));
    });

    test('should provide valid timeout configurations', () {
      // Property: All timeout values should be positive and reasonable
      
      // Verify: Connection timeout should be between 10 seconds and 2 minutes
      expect(Constants.connectionTimeout.inSeconds, greaterThanOrEqualTo(10));
      expect(Constants.connectionTimeout.inSeconds, lessThanOrEqualTo(120));
      
      // Verify: Retry delay should be between 1 and 10 seconds
      expect(Constants.retryDelay.inSeconds, greaterThanOrEqualTo(1));
      expect(Constants.retryDelay.inSeconds, lessThanOrEqualTo(10));
      
      // Verify: Error display duration should be between 1 and 30 seconds
      expect(Constants.errorDisplayDuration.inSeconds, greaterThanOrEqualTo(1));
      expect(Constants.errorDisplayDuration.inSeconds, lessThanOrEqualTo(30));
      
      // Verify: Cache expiration should be between 1 and 60 minutes
      expect(Constants.cacheExpiration.inMinutes, greaterThanOrEqualTo(1));
      expect(Constants.cacheExpiration.inMinutes, lessThanOrEqualTo(60));
    });

    test('should provide valid file size limits', () {
      // Property: File size limits should be reasonable
      
      // Verify: Max file size should be between 1MB and 100MB
      final maxSizeMB = Constants.maxFileSizeBytes / (1024 * 1024);
      expect(maxSizeMB, greaterThanOrEqualTo(1));
      expect(maxSizeMB, lessThanOrEqualTo(100));
    });

    test('should provide valid retry configuration', () {
      // Property: Retry configuration should be reasonable
      
      // Verify: Max retries should be between 1 and 10
      expect(Constants.maxRetries, greaterThanOrEqualTo(1));
      expect(Constants.maxRetries, lessThanOrEqualTo(10));
      
      // Verify: Room refresh interval should be between 10 and 300 seconds
      expect(Constants.roomRefreshInterval, greaterThanOrEqualTo(10));
      expect(Constants.roomRefreshInterval, lessThanOrEqualTo(300));
    });

    test('should provide boolean configuration flags', () {
      // Property: Boolean flags should be valid booleans
      
      // Verify: All boolean flags should be actual booleans
      expect(Constants.isProduction, isA<bool>());
      expect(Constants.isDevelopment, isA<bool>());
      expect(Constants.enableDebugLogs, isA<bool>());
      expect(Constants.enablePerformanceMonitoring, isA<bool>());
      expect(Constants.showDetailedErrors, isA<bool>());
      
      // Verify: Environment flags should be mutually exclusive (mostly)
      if (Constants.isProduction) {
        expect(Constants.isDevelopment, isFalse);
      }
    });

    test('should handle environment-specific URL defaults', () {
      // Property: URLs should match the environment
      
      if (Constants.isProduction) {
        // Production URLs should use HTTPS
        expect(Constants.matchmakerUrl, startsWith('https://'));
        expect(Constants.gameServerFactoryUrl, startsWith('https://'));
      } else if (Constants.isDevelopment) {
        // Development URLs typically use localhost
        final matchmakerUri = Uri.parse(Constants.matchmakerUrl);
        final factoryUri = Uri.parse(Constants.gameServerFactoryUrl);
        
        expect(
          matchmakerUri.host,
          anyOf(equals('localhost'), equals('127.0.0.1'), equals('matchmaker'))
        );
        expect(
          factoryUri.host,
          anyOf(equals('localhost'), equals('127.0.0.1'), equals('factory'))
        );
      }
    });

    test('should provide consistent configuration across calls', () {
      // Property: Configuration values should be consistent across multiple calls
      
      final env1 = Constants.environment;
      final env2 = Constants.environment;
      expect(env1, equals(env2));
      
      final url1 = Constants.matchmakerUrl;
      final url2 = Constants.matchmakerUrl;
      expect(url1, equals(url2));
      
      final retries1 = Constants.maxRetries;
      final retries2 = Constants.maxRetries;
      expect(retries1, equals(retries2));
    });
  });
}

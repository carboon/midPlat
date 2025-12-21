import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:universal_game_client/services/game_server_factory_service.dart';
import 'package:universal_game_client/models/game_server_instance.dart';
import 'package:universal_game_client/utils/constants.dart';

/// Integration test for code upload and server lifecycle management
/// Tests the complete workflow: upload -> create -> manage -> delete
void main() {
  group('Code Upload and Server Lifecycle Integration Tests', () {
    late File testJsFile;
    late String testServerId;

    setUpAll(() async {
      // Create a test JavaScript file
      testJsFile = File('test_game.js');
      await testJsFile.writeAsString('''
// Simple test game
const gameState = { clickCount: 0 };

function handleClick() {
  gameState.clickCount++;
  return gameState;
}

module.exports = { gameState, handleClick };
''');
    });

    tearDownAll(() async {
      // Clean up test file
      if (await testJsFile.exists()) {
        await testJsFile.delete();
      }
      
      // Clean up test server if it exists
      if (testServerId.isNotEmpty) {
        try {
          await GameServerFactoryService.deleteServer(testServerId);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    });

    test('should successfully upload JavaScript code and create server', () async {
      // Verify Game Server Factory is accessible
      final health = await GameServerFactoryService.checkHealth();
      expect(health['status'], equals('healthy'));

      // Upload the test file
      final server = await GameServerFactoryService.uploadGameCode(
        file: testJsFile,
        name: 'Test Game Server',
        description: 'Integration test server',
        maxPlayers: 5,
      );

      // Verify server was created
      expect(server, isNotNull);
      expect(server.name, equals('Test Game Server'));
      expect(server.description, equals('Integration test server'));
      expect(server.serverId, isNotEmpty);
      expect(server.port, greaterThan(0));
      
      // Store server ID for cleanup
      testServerId = server.serverId;

      // Verify server status is valid
      expect(['creating', 'running'], contains(server.status));
    }, timeout: const Timeout(Duration(seconds: 30)));

    test('should fetch list of user servers', () async {
      // Fetch all servers
      final servers = await GameServerFactoryService.fetchMyServers();
      
      // Verify we get a list
      expect(servers, isA<List<GameServerInstance>>());
      
      // If we created a test server, it should be in the list
      if (testServerId.isNotEmpty) {
        final testServer = servers.where((s) => s.serverId == testServerId);
        expect(testServer, isNotEmpty);
      }
    }, timeout: const Timeout(Duration(seconds: 10)));

    test('should fetch server details', () async {
      // Skip if no test server was created
      if (testServerId.isEmpty) {
        return;
      }

      // Fetch server details
      final server = await GameServerFactoryService.fetchServerDetails(testServerId);
      
      // Verify details
      expect(server.serverId, equals(testServerId));
      expect(server.name, equals('Test Game Server'));
      expect(server.port, greaterThan(0));
      expect(server.createdAt, isNotNull);
      expect(server.updatedAt, isNotNull);
    }, timeout: const Timeout(Duration(seconds: 10)));

    test('should stop a running server', () async {
      // Skip if no test server was created
      if (testServerId.isEmpty) {
        return;
      }

      // Wait a bit for server to be fully running
      await Future.delayed(const Duration(seconds: 2));

      // Stop the server
      await GameServerFactoryService.stopServer(testServerId);
      
      // Verify server was stopped by fetching details
      await Future.delayed(const Duration(seconds: 1));
      final server = await GameServerFactoryService.fetchServerDetails(testServerId);
      expect(server.status, equals('stopped'));
    }, timeout: const Timeout(Duration(seconds: 15)));

    test('should delete a server', () async {
      // Skip if no test server was created
      if (testServerId.isEmpty) {
        return;
      }

      // Delete the server
      await GameServerFactoryService.deleteServer(testServerId);
      
      // Verify server was deleted by trying to fetch it
      await Future.delayed(const Duration(seconds: 1));
      
      try {
        await GameServerFactoryService.fetchServerDetails(testServerId);
        fail('Server should have been deleted');
      } on ApiException catch (e) {
        // Expect 404 error
        expect(e.statusCode, equals(404));
      }
      
      // Clear test server ID since it's been deleted
      testServerId = '';
    }, timeout: const Timeout(Duration(seconds: 10)));

    test('should handle file size validation', () async {
      // Create a file that's too large
      final largeFile = File('large_test.js');
      final largeContent = 'x' * (Constants.maxFileSizeBytes + 1);
      await largeFile.writeAsString(largeContent);

      try {
        await GameServerFactoryService.uploadGameCode(
          file: largeFile,
          name: 'Large File Test',
          description: 'Should fail',
        );
        fail('Should have thrown NetworkException for large file');
      } on NetworkException catch (e) {
        expect(e.message, contains('文件大小超过限制'));
      } finally {
        if (await largeFile.exists()) {
          await largeFile.delete();
        }
      }
    });

    test('should handle network errors gracefully', () async {
      // Try to fetch server with invalid ID
      try {
        await GameServerFactoryService.fetchServerDetails('invalid_server_id');
        fail('Should have thrown ApiException');
      } on ApiException catch (e) {
        expect(e.statusCode, equals(404));
        expect(e.message, contains('资源不存在'));
      }
    });

    test('should handle upload progress callback', () async {
      final progressValues = <double>[];
      
      final server = await GameServerFactoryService.uploadGameCode(
        file: testJsFile,
        name: 'Progress Test Server',
        description: 'Testing progress callback',
        onProgress: (progress) {
          progressValues.add(progress);
        },
      );

      // Verify progress was reported
      expect(progressValues, isNotEmpty);
      expect(progressValues.last, equals(1.0));
      
      // Clean up
      if (server.serverId.isNotEmpty) {
        try {
          await GameServerFactoryService.deleteServer(server.serverId);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
    }, timeout: const Timeout(Duration(seconds: 30)));

    test('should validate configuration parameters', () {
      // Test configuration validation
      final errors = Constants.validateConfiguration();
      expect(errors, isEmpty, reason: 'Configuration should be valid');

      // Test configuration summary
      final summary = Constants.getConfigurationSummary();
      expect(summary['environment'], isNotEmpty);
      expect(summary['game_server_factory_url'], isNotEmpty);
      expect(summary['max_retries'], greaterThan(0));
    });

    test('should handle retry logic for transient failures', () async {
      // This test verifies that the retry mechanism works
      // We can't easily simulate transient failures, but we can verify
      // that successful requests work with the retry wrapper
      
      final servers = await GameServerFactoryService.fetchMyServers();
      expect(servers, isA<List<GameServerInstance>>());
    }, timeout: const Timeout(Duration(seconds: 15)));
  });

  group('Error Handling Tests', () {
    test('should handle invalid file format', () async {
      final invalidFile = File('test.txt');
      await invalidFile.writeAsString('This is not JavaScript');

      try {
        await GameServerFactoryService.uploadGameCode(
          file: invalidFile,
          name: 'Invalid File Test',
          description: 'Should fail',
        );
        fail('Should have thrown exception for invalid file');
      } catch (e) {
        expect(e, isA<Exception>());
      } finally {
        if (await invalidFile.exists()) {
          await invalidFile.delete();
        }
      }
    });

    test('should handle empty server name', () async {
      final testFile = File('empty_name_test.js');
      await testFile.writeAsString('const x = 1;');

      try {
        await GameServerFactoryService.uploadGameCode(
          file: testFile,
          name: '', // Empty name
          description: 'Test',
        );
        fail('Should have thrown exception for empty name');
      } catch (e) {
        expect(e, isA<Exception>());
      } finally {
        if (await testFile.exists()) {
          await testFile.delete();
        }
      }
    });

    test('should handle connection timeout', () async {
      // This test verifies timeout handling
      // We can't easily simulate a timeout, but we can verify the timeout is configured
      expect(Constants.connectionTimeout.inSeconds, greaterThan(0));
      expect(Constants.maxRetries, greaterThan(0));
    });
  });
}

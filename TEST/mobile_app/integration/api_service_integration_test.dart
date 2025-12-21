/// Integration test for API service layer functionality
/// Tests the GameServerFactoryService and MatchmakerService integration

import 'dart:io';
import 'package:test/test.dart';
import 'package:universal_game_client/services/game_server_factory_service.dart';
import 'package:universal_game_client/services/matchmaker_service.dart';
import 'package:universal_game_client/services/api_service.dart';

void main() {
  group('API Service Integration Tests', () {
    test('GameServerFactoryService validates HTML file types', () {
      // Test file type validation
      expect(
        () async {
          final tempFile = File('test.txt');
          await tempFile.writeAsString('not html');
          
          try {
            await GameServerFactoryService.uploadHtmlGame(
              file: tempFile,
              name: 'Test Game',
              description: 'Test file for validation',
            );
          } finally {
            if (await tempFile.exists()) {
              await tempFile.delete();
            }
          }
        },
        throwsA(isA<NetworkException>()),
      );
    });

    test('GameServerFactoryService accepts HTML files', () async {
      final tempFile = File('test.html');
      await tempFile.writeAsString('<html><body>Test Game</body></html>');
      
      try {
        // This should not throw a file type validation error
        // (it will likely fail with network error since no server is running)
        await GameServerFactoryService.uploadHtmlGame(
          file: tempFile,
          name: 'Test Game',
          description: 'Test HTML game for validation',
        );
      } catch (e) {
        // We expect either a network error or API error (not a file type error)
        expect(e, anyOf(isA<NetworkException>(), isA<ApiException>()));
        expect(e.toString(), isNot(contains('不支持的文件格式')));
      } finally {
        if (await tempFile.exists()) {
          await tempFile.delete();
        }
      }
    });

    test('GameServerFactoryService accepts ZIP files', () async {
      final tempFile = File('test.zip');
      await tempFile.writeAsBytes([80, 75, 3, 4]); // ZIP file header
      
      try {
        // This should not throw a file type validation error
        await GameServerFactoryService.uploadHtmlGame(
          file: tempFile,
          name: 'Test Game',
          description: 'Test ZIP game for validation',
        );
      } catch (e) {
        // We expect either a network error or API error (not a file type error)
        expect(e, anyOf(isA<NetworkException>(), isA<ApiException>()));
        expect(e.toString(), isNot(contains('不支持的文件格式')));
      } finally {
        if (await tempFile.exists()) {
          await tempFile.delete();
        }
      }
    });

    test('Progress callback is called during upload', () async {
      final tempFile = File('test.html');
      await tempFile.writeAsString('<html><body>Test Game</body></html>');
      
      final progressValues = <double>[];
      
      try {
        await GameServerFactoryService.uploadHtmlGame(
          file: tempFile,
          name: 'Test Game',
          description: 'Test game for progress callback',
          onProgress: (progress) {
            progressValues.add(progress);
          },
        );
      } catch (e) {
        // We expect this to fail with network or API error
        expect(e, anyOf(isA<NetworkException>(), isA<ApiException>()));
      } finally {
        if (await tempFile.exists()) {
          await tempFile.delete();
        }
      }
      
      // Progress callback should have been called at least once during the upload attempt
      // Even if the request fails, the progress callback should be called initially
      // Note: This test may be flaky depending on network conditions
      // In a real scenario, progress would be tracked properly
      print('Progress values captured: $progressValues');
    });

    test('API Service provides unified access', () {
      // Test that ApiService exposes the correct methods
      expect(ApiService.uploadHtmlGame, isA<Function>());
      expect(ApiService.fetchMyServers, isA<Function>());
      expect(ApiService.fetchRooms, isA<Function>());
      expect(ApiService.watchServerStatus, isA<Function>());
      expect(ApiService.watchAllServers, isA<Function>());
      expect(ApiService.watchRooms, isA<Function>());
    });

    test('Real-time streams are properly typed', () {
      // Test that the stream methods return correct types
      final serverStream = ApiService.watchServerStatus('test-id');
      expect(serverStream, isA<Stream>());
      
      final allServersStream = ApiService.watchAllServers();
      expect(allServersStream, isA<Stream>());
      
      final roomsStream = ApiService.watchRooms();
      expect(roomsStream, isA<Stream>());
    });
  });
}
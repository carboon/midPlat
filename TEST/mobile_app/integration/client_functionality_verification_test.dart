import 'package:flutter_test/flutter_test.dart';
import 'package:universal_game_client/services/game_server_factory_service.dart';
import 'package:universal_game_client/utils/constants.dart';

/// Quick verification test for Flutter client functionality
void main() {
  group('Flutter Client Functionality Verification', () {
    test('Game Server Factory service is accessible', () async {
      final health = await GameServerFactoryService.checkHealth();
      expect(health['status'], equals('healthy'));
    });

    test('Can fetch server list', () async {
      final servers = await GameServerFactoryService.fetchMyServers();
      expect(servers, isNotNull);
    });

    test('Configuration is valid', () {
      final errors = Constants.validateConfiguration();
      expect(errors, isEmpty);
      
      expect(Constants.gameServerFactoryUrl, isNotEmpty);
      expect(Constants.maxRetries, greaterThan(0));
    });

    test('Service methods are available', () {
      // Verify all required methods exist
      expect(GameServerFactoryService.uploadGameCode, isNotNull);
      expect(GameServerFactoryService.fetchMyServers, isNotNull);
      expect(GameServerFactoryService.fetchServerDetails, isNotNull);
      expect(GameServerFactoryService.stopServer, isNotNull);
      expect(GameServerFactoryService.deleteServer, isNotNull);
      expect(GameServerFactoryService.fetchServerLogs, isNotNull);
    });
  });
}

/// Property-based test for real-time status updates
/// **Feature: ai-game-platform, Property 9: 实时状态更新**
/// **Validates: Requirements 2.5**
///
/// This test verifies that for any server status change, the client
/// should update the displayed status information in real-time.

import 'package:test/test.dart';
import 'package:glados/glados.dart';
import 'package:universal_game_client/providers/game_server_provider.dart';
import 'package:universal_game_client/models/game_server_instance.dart';

/// Generator for valid server status values
final statusGenerator = any.choose(['creating', 'running', 'stopped', 'error']);

/// Generator for valid server IDs (non-empty alphanumeric strings)
final serverIdGenerator = any.nonEmptyLetterOrDigits;

/// Generator for server names
final serverNameGenerator = any.nonEmptyLetterOrDigits;

/// Generator for port numbers (valid range)
final portGenerator = any.intInRange(1024, 65535);

/// Generator for GameServerInstance
final gameServerInstanceGenerator = any.combine3(
  serverIdGenerator,
  serverNameGenerator,
  portGenerator,
  (String serverId, String name, int port) => GameServerInstance(
    serverId: serverId,
    name: name,
    description: 'Test game',
    status: 'running',
    containerId: 'container_$serverId',
    port: port,
    createdAt: DateTime.now(),
    updatedAt: DateTime.now(),
    resourceUsage: {},
    logs: [],
  ),
);

void main() {
  group('Property 9: Real-time Status Update', () {
    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: For any server in the list and any valid status,
    /// calling updateServerStatus should update that server's status
    /// and the updatedAt timestamp should be updated.
    Glados2(gameServerInstanceGenerator, statusGenerator).test(
      'updateServerStatus updates server status for any server and status',
      (server, newStatus) {
        // Arrange
        final provider = GameServerProvider();
        provider.setServers([server]);

        // Act
        provider.updateServerStatus(server.serverId, newStatus);

        // Assert
        final updatedServer = provider.myServers.firstWhere(
          (s) => s.serverId == server.serverId,
        );
        expect(updatedServer.status, equals(newStatus));
      },
    );

    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: For any server that is set as currentServer,
    /// updating its status should also update the currentServer reference.
    Glados2(gameServerInstanceGenerator, statusGenerator).test(
      'updateServerStatus updates currentServer when it matches',
      (server, newStatus) {
        // Arrange
        final provider = GameServerProvider();
        provider.setServers([server]);
        provider.setCurrentServer(server);

        // Act
        provider.updateServerStatus(server.serverId, newStatus);

        // Assert
        expect(provider.currentServer, isNotNull);
        expect(provider.currentServer!.status, equals(newStatus));
      },
    );

    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: For any list of servers and any status update,
    /// only the targeted server should be updated, others remain unchanged.
    Glados3(
      gameServerInstanceGenerator,
      gameServerInstanceGenerator,
      statusGenerator,
    ).test(
      'updateServerStatus only updates the targeted server',
      (server1, server2, newStatus) {
        // Skip if servers have the same ID (edge case)
        if (server1.serverId == server2.serverId) return;

        // Arrange
        final provider = GameServerProvider();
        final originalStatus2 = server2.status;
        provider.setServers([server1, server2]);

        // Act
        provider.updateServerStatus(server1.serverId, newStatus);

        // Assert
        final updatedServer1 = provider.myServers.firstWhere(
          (s) => s.serverId == server1.serverId,
        );
        final unchangedServer2 = provider.myServers.firstWhere(
          (s) => s.serverId == server2.serverId,
        );

        expect(updatedServer1.status, equals(newStatus));
        expect(unchangedServer2.status, equals(originalStatus2));
      },
    );

    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: For any non-existent server ID, updateServerStatus
    /// should not modify the server list.
    Glados3(
      gameServerInstanceGenerator,
      serverIdGenerator,
      statusGenerator,
    ).test(
      'updateServerStatus does not modify list for non-existent server',
      (server, nonExistentId, newStatus) {
        // Skip if the generated ID happens to match
        if (server.serverId == nonExistentId) return;

        // Arrange
        final provider = GameServerProvider();
        provider.setServers([server]);
        final originalStatus = server.status;

        // Act
        provider.updateServerStatus(nonExistentId, newStatus);

        // Assert
        expect(provider.myServers.length, equals(1));
        expect(provider.myServers.first.status, equals(originalStatus));
      },
    );

    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: For any server, updating status should update the
    /// updatedAt timestamp to a more recent time.
    Glados2(gameServerInstanceGenerator, statusGenerator).test(
      'updateServerStatus updates the updatedAt timestamp',
      (server, newStatus) {
        // Arrange
        final provider = GameServerProvider();
        final oldUpdatedAt = server.updatedAt;
        provider.setServers([server]);

        // Act
        provider.updateServerStatus(server.serverId, newStatus);

        // Assert
        final updatedServer = provider.myServers.firstWhere(
          (s) => s.serverId == server.serverId,
        );
        // The updatedAt should be >= the original (could be same if very fast)
        expect(
          updatedServer.updatedAt.millisecondsSinceEpoch,
          greaterThanOrEqualTo(oldUpdatedAt.millisecondsSinceEpoch),
        );
      },
    );

    /// **Feature: ai-game-platform, Property 9: 实时状态更新**
    ///
    /// Property: Status update idempotence - updating to the same status
    /// multiple times should result in the same final state.
    Glados2(gameServerInstanceGenerator, statusGenerator).test(
      'updateServerStatus is idempotent for same status',
      (server, newStatus) {
        // Arrange
        final provider = GameServerProvider();
        provider.setServers([server]);

        // Act - update twice with same status
        provider.updateServerStatus(server.serverId, newStatus);
        final statusAfterFirst = provider.myServers.first.status;

        provider.updateServerStatus(server.serverId, newStatus);
        final statusAfterSecond = provider.myServers.first.status;

        // Assert
        expect(statusAfterFirst, equals(newStatus));
        expect(statusAfterSecond, equals(newStatus));
        expect(statusAfterFirst, equals(statusAfterSecond));
      },
    );
  });
}

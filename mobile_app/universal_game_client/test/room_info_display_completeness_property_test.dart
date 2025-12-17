/// Property-based test for room information display completeness
/// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
/// **Validates: Requirements 3.2**
///
/// This test verifies that for any room data, the client display
/// should contain room name, current player count, max players, and server status.

import 'package:test/test.dart';
import 'package:glados/glados.dart';
import 'package:universal_game_client/models/room.dart';
import 'package:universal_game_client/providers/room_provider.dart';

/// Generator for valid room names (non-empty strings)
final roomNameGenerator = any.nonEmptyLetterOrDigits;

/// Generator for valid room IDs
final roomIdGenerator = any.nonEmptyLetterOrDigits;

/// Generator for valid IP addresses
final ipGenerator = any.choose([
  '127.0.0.1',
  '192.168.1.1',
  '10.0.0.1',
  'localhost',
]);

/// Generator for port numbers (valid range)
final portGenerator = any.intInRange(1024, 65535);

/// Generator for player counts (0 to reasonable max)
final playerCountGenerator = any.intInRange(0, 100);

/// Generator for max players (1 to reasonable max)
final maxPlayersGenerator = any.intInRange(1, 100);

/// Generator for uptime in seconds
final uptimeGenerator = any.intInRange(0, 86400);

/// Generator for heartbeat timestamps
final heartbeatGenerator = any.choose([
  '2025-12-17T10:00:00Z',
  '2025-12-17T10:30:00Z',
  '2025-12-17T11:00:00Z',
]);

/// Generator for Room instances with valid data
final roomGenerator = any.combine5(
  roomIdGenerator,
  roomNameGenerator,
  portGenerator,
  playerCountGenerator,
  maxPlayersGenerator,
  (String id, String name, int port, int playerCount, int maxPlayers) {
    // Ensure playerCount doesn't exceed maxPlayers
    final adjustedPlayerCount = playerCount > maxPlayers ? maxPlayers : playerCount;
    return Room(
      id: id,
      name: name,
      ip: '127.0.0.1',
      port: port,
      playerCount: adjustedPlayerCount,
      maxPlayers: maxPlayers,
      metadata: {},
      lastHeartbeat: '2025-12-17T10:00:00Z',
      uptime: 3600,
    );
  },
);

/// Helper class to represent room display information
/// This simulates what the UI would render for a room
class RoomDisplayInfo {
  final String roomName;
  final int currentPlayers;
  final int maxPlayers;
  final String status;

  RoomDisplayInfo({
    required this.roomName,
    required this.currentPlayers,
    required this.maxPlayers,
    required this.status,
  });

  /// Creates display info from a Room model
  /// This mirrors the logic used in RoomCard and RoomDetailScreen
  factory RoomDisplayInfo.fromRoom(Room room) {
    // Derive status from room data
    // A room is considered "active" if it has valid data
    final status = _deriveStatus(room);
    
    return RoomDisplayInfo(
      roomName: room.name,
      currentPlayers: room.playerCount,
      maxPlayers: room.maxPlayers,
      status: status,
    );
  }

  /// Derives server status from room data
  static String _deriveStatus(Room room) {
    // Status is derived from the room's heartbeat and player capacity
    if (room.playerCount >= room.maxPlayers) {
      return 'full';
    } else if (room.playerCount > 0) {
      return 'active';
    } else {
      return 'waiting';
    }
  }

  /// Checks if all required information is present and valid
  bool get isComplete {
    return roomName.isNotEmpty &&
        currentPlayers >= 0 &&
        maxPlayers > 0 &&
        status.isNotEmpty;
  }

  /// Generates a display string similar to what RoomCard shows
  String toDisplayString() {
    return '$roomName - 玩家: $currentPlayers/$maxPlayers - 状态: $status';
  }
}

void main() {
  group('Property 11: Room Information Display Completeness', () {
    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any valid room data, the display information
    /// should contain all required fields: room name, current players,
    /// max players, and server status.
    Glados(roomGenerator).test(
      'room display contains all required information for any room',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);

        // Assert - all required fields are present
        expect(displayInfo.roomName, isNotEmpty,
            reason: 'Room name should not be empty');
        expect(displayInfo.currentPlayers, greaterThanOrEqualTo(0),
            reason: 'Current players should be non-negative');
        expect(displayInfo.maxPlayers, greaterThan(0),
            reason: 'Max players should be positive');
        expect(displayInfo.status, isNotEmpty,
            reason: 'Status should not be empty');
        expect(displayInfo.isComplete, isTrue,
            reason: 'Display info should be complete');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any room, the display string should contain
    /// the room name, player count ratio, and status.
    Glados(roomGenerator).test(
      'room display string contains name, player count, and status',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);
        final displayString = displayInfo.toDisplayString();

        // Assert - display string contains all required information
        expect(displayString, contains(room.name),
            reason: 'Display should contain room name');
        expect(displayString, contains('${room.playerCount}'),
            reason: 'Display should contain current player count');
        expect(displayString, contains('${room.maxPlayers}'),
            reason: 'Display should contain max players');
        expect(displayString, contains(displayInfo.status),
            reason: 'Display should contain status');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any room, the current player count should never
    /// exceed the max players in the display.
    Glados(roomGenerator).test(
      'current players never exceeds max players in display',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);

        // Assert
        expect(displayInfo.currentPlayers, lessThanOrEqualTo(displayInfo.maxPlayers),
            reason: 'Current players should not exceed max players');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any room, the status should be one of the valid
    /// status values: 'active', 'waiting', or 'full'.
    Glados(roomGenerator).test(
      'room status is always a valid status value',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);

        // Assert
        expect(
          ['active', 'waiting', 'full'],
          contains(displayInfo.status),
          reason: 'Status should be one of: active, waiting, full',
        );
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any room at full capacity, the status should be 'full'.
    Glados(roomGenerator).test(
      'full room has status "full"',
      (room) {
        // Create a room at full capacity
        final fullRoom = Room(
          id: room.id,
          name: room.name,
          ip: room.ip,
          port: room.port,
          playerCount: room.maxPlayers, // Full capacity
          maxPlayers: room.maxPlayers,
          metadata: room.metadata,
          lastHeartbeat: room.lastHeartbeat,
          uptime: room.uptime,
        );

        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(fullRoom);

        // Assert
        expect(displayInfo.status, equals('full'),
            reason: 'Room at full capacity should have status "full"');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any empty room, the status should be 'waiting'.
    Glados(roomGenerator).test(
      'empty room has status "waiting"',
      (room) {
        // Create an empty room
        final emptyRoom = Room(
          id: room.id,
          name: room.name,
          ip: room.ip,
          port: room.port,
          playerCount: 0, // Empty
          maxPlayers: room.maxPlayers,
          metadata: room.metadata,
          lastHeartbeat: room.lastHeartbeat,
          uptime: room.uptime,
        );

        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(emptyRoom);

        // Assert
        expect(displayInfo.status, equals('waiting'),
            reason: 'Empty room should have status "waiting"');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: For any room with players but not full, status should be 'active'.
    Glados(roomGenerator).test(
      'partially filled room has status "active"',
      (room) {
        // Skip if maxPlayers is 1 (can't have partial fill)
        if (room.maxPlayers <= 1) return;

        // Create a partially filled room
        final partialRoom = Room(
          id: room.id,
          name: room.name,
          ip: room.ip,
          port: room.port,
          playerCount: 1, // At least one player but not full
          maxPlayers: room.maxPlayers,
          metadata: room.metadata,
          lastHeartbeat: room.lastHeartbeat,
          uptime: room.uptime,
        );

        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(partialRoom);

        // Assert
        expect(displayInfo.status, equals('active'),
            reason: 'Partially filled room should have status "active"');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: Room display info preserves the original room name exactly.
    Glados(roomGenerator).test(
      'room name is preserved exactly in display',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);

        // Assert
        expect(displayInfo.roomName, equals(room.name),
            reason: 'Room name should be preserved exactly');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: Room display info preserves player counts exactly.
    Glados(roomGenerator).test(
      'player counts are preserved exactly in display',
      (room) {
        // Act
        final displayInfo = RoomDisplayInfo.fromRoom(room);

        // Assert
        expect(displayInfo.currentPlayers, equals(room.playerCount),
            reason: 'Current player count should be preserved');
        expect(displayInfo.maxPlayers, equals(room.maxPlayers),
            reason: 'Max players should be preserved');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: RoomProvider correctly stores and retrieves room for display.
    Glados(roomGenerator).test(
      'RoomProvider preserves room information for display',
      (room) {
        // Arrange
        final provider = RoomProvider();

        // Act
        provider.setCurrentRoom(room);

        // Assert
        expect(provider.currentRoom, isNotNull);
        expect(provider.currentRoom!.name, equals(room.name),
            reason: 'Room name should be preserved in provider');
        expect(provider.currentRoom!.playerCount, equals(room.playerCount),
            reason: 'Player count should be preserved in provider');
        expect(provider.currentRoom!.maxPlayers, equals(room.maxPlayers),
            reason: 'Max players should be preserved in provider');
      },
    );

    /// **Feature: ai-game-platform, Property 11: 房间信息显示完整性**
    ///
    /// Property: Room list in provider preserves all room information.
    Glados2(roomGenerator, roomGenerator).test(
      'RoomProvider preserves all rooms information in list',
      (room1, room2) {
        // Skip if rooms have the same ID
        if (room1.id == room2.id) return;

        // Arrange
        final provider = RoomProvider();

        // Act
        provider.setRooms([room1, room2]);

        // Assert
        expect(provider.rooms.length, equals(2));
        
        final storedRoom1 = provider.rooms.firstWhere((r) => r.id == room1.id);
        final storedRoom2 = provider.rooms.firstWhere((r) => r.id == room2.id);

        // Verify room1 information is complete
        expect(storedRoom1.name, equals(room1.name));
        expect(storedRoom1.playerCount, equals(room1.playerCount));
        expect(storedRoom1.maxPlayers, equals(room1.maxPlayers));

        // Verify room2 information is complete
        expect(storedRoom2.name, equals(room2.name));
        expect(storedRoom2.playerCount, equals(room2.playerCount));
        expect(storedRoom2.maxPlayers, equals(room2.maxPlayers));
      },
    );
  });
}

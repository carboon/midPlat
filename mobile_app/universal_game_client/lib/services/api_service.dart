import 'dart:io';
import '../models/room.dart';
import '../models/game_server_instance.dart';
import 'matchmaker_service.dart';
import 'game_server_factory_service.dart';

export 'game_server_factory_service.dart' show NetworkException, ApiException;

/// Unified API service that provides access to both Matchmaker and Game Server Factory.
/// This class serves as a facade for backward compatibility and convenience.
class ApiService {
  // ============ Matchmaker Service Methods ============

  /// Fetches the list of all active game rooms/servers.
  static Future<List<Room>> fetchRooms() => MatchmakerService.fetchRooms();

  /// Fetches details of a specific room by ID.
  static Future<Room> fetchRoomById(String id) => MatchmakerService.fetchRoomById(id);

  /// Checks the health status of the Matchmaker service.
  static Future<Map<String, dynamic>> checkMatchmakerHealth() => MatchmakerService.checkHealth();

  // ============ Game Server Factory Methods ============

  /// Uploads an HTML game file to create a new game server.
  static Future<GameServerInstance> uploadHtmlGame({
    required File file,
    required String name,
    String description = '',
    int maxPlayers = 10,
    void Function(double progress)? onProgress,
  }) => GameServerFactoryService.uploadHtmlGame(
    file: file,
    name: name,
    description: description,
    maxPlayers: maxPlayers,
    onProgress: onProgress,
  );

  /// Legacy method name for backward compatibility
  @Deprecated('Use uploadHtmlGame instead')
  static Future<GameServerInstance> uploadGameCode({
    required File file,
    required String name,
    String description = '',
    int maxPlayers = 10,
    void Function(double progress)? onProgress,
  }) => uploadHtmlGame(
    file: file,
    name: name,
    description: description,
    maxPlayers: maxPlayers,
    onProgress: onProgress,
  );

  /// Fetches the list of game servers created by the current user.
  static Future<List<GameServerInstance>> fetchMyServers() => 
      GameServerFactoryService.fetchMyServers();

  /// Fetches details of a specific game server.
  static Future<GameServerInstance> fetchServerDetails(String serverId) =>
      GameServerFactoryService.fetchServerDetails(serverId);

  /// Stops a running game server.
  static Future<void> stopServer(String serverId) =>
      GameServerFactoryService.stopServer(serverId);

  /// Deletes a game server and cleans up resources.
  static Future<void> deleteServer(String serverId) =>
      GameServerFactoryService.deleteServer(serverId);

  /// Fetches logs for a specific game server.
  static Future<List<String>> fetchServerLogs(String serverId) =>
      GameServerFactoryService.fetchServerLogs(serverId);

  /// Checks the health status of the Game Server Factory service.
  static Future<Map<String, dynamic>> checkFactoryHealth() =>
      GameServerFactoryService.checkHealth();

  // ============ Real-time Status Update Methods ============

  /// Creates a stream that periodically fetches server status updates.
  /// This enables real-time status monitoring for the UI.
  static Stream<GameServerInstance> watchServerStatus(
    String serverId, {
    Duration interval = const Duration(seconds: 5),
  }) => GameServerFactoryService.watchServerStatus(serverId, interval: interval);

  /// Creates a stream that periodically fetches all user servers.
  /// This enables real-time monitoring of all servers in the UI.
  static Stream<List<GameServerInstance>> watchAllServers({
    Duration interval = const Duration(seconds: 10),
  }) => GameServerFactoryService.watchAllServers(interval: interval);

  /// Creates a stream that periodically fetches room list updates.
  /// This enables real-time room discovery in the UI.
  static Stream<List<Room>> watchRooms({
    Duration interval = const Duration(seconds: 30),
  }) => MatchmakerService.watchRooms(interval: interval);

  /// Creates a stream that monitors a specific room for updates.
  static Stream<Room> watchRoom(
    String roomId, {
    Duration interval = const Duration(seconds: 10),
  }) => MatchmakerService.watchRoom(roomId, interval: interval);

  // ============ Legacy Methods (for backward compatibility) ============

  /// Join room - in the new architecture, this is handled via WebSocket connection.
  static Future<bool> joinRoom(String roomId, String password) async {
    // In the new architecture, joining is done via direct WebSocket connection
    return true;
  }
}
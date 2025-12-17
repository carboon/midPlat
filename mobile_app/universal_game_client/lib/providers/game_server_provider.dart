import 'package:flutter/foundation.dart';
import '../models/game_server_instance.dart';

/// Provider for managing game server instances created by the user.
/// Handles state for server list, current server selection, and upload status.
class GameServerProvider with ChangeNotifier {
  List<GameServerInstance> _myServers = [];
  GameServerInstance? _currentServer;
  bool _isLoading = false;
  bool _isUploading = false;
  double _uploadProgress = 0.0;
  String? _errorMessage;

  // Getters
  List<GameServerInstance> get myServers => _myServers;
  GameServerInstance? get currentServer => _currentServer;
  bool get isLoading => _isLoading;
  bool get isUploading => _isUploading;
  double get uploadProgress => _uploadProgress;
  String? get errorMessage => _errorMessage;

  /// Returns servers filtered by status
  List<GameServerInstance> getServersByStatus(String status) {
    return _myServers.where((s) => s.status == status).toList();
  }

  /// Returns count of running servers
  int get runningServerCount =>
      _myServers.where((s) => s.isRunning).length;

  /// Sets the list of user's game servers
  void setServers(List<GameServerInstance> servers) {
    _myServers = servers;
    _errorMessage = null;
    notifyListeners();
  }

  /// Adds a new server to the list
  void addServer(GameServerInstance server) {
    _myServers.add(server);
    notifyListeners();
  }

  /// Updates an existing server in the list
  void updateServer(GameServerInstance updatedServer) {
    final index = _myServers.indexWhere(
      (s) => s.serverId == updatedServer.serverId,
    );
    if (index != -1) {
      _myServers[index] = updatedServer;
      if (_currentServer?.serverId == updatedServer.serverId) {
        _currentServer = updatedServer;
      }
      notifyListeners();
    }
  }

  /// Removes a server from the list
  void removeServer(String serverId) {
    _myServers.removeWhere((s) => s.serverId == serverId);
    if (_currentServer?.serverId == serverId) {
      _currentServer = null;
    }
    notifyListeners();
  }

  /// Sets the currently selected server
  void setCurrentServer(GameServerInstance? server) {
    _currentServer = server;
    notifyListeners();
  }

  /// Clears the current server selection
  void clearCurrentServer() {
    _currentServer = null;
    notifyListeners();
  }

  /// Sets the loading state
  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  /// Sets the uploading state
  void setUploading(bool uploading) {
    _isUploading = uploading;
    if (!uploading) {
      _uploadProgress = 0.0;
    }
    notifyListeners();
  }

  /// Updates the upload progress (0.0 to 1.0)
  void setUploadProgress(double progress) {
    _uploadProgress = progress.clamp(0.0, 1.0);
    notifyListeners();
  }

  /// Sets an error message
  void setError(String? message) {
    _errorMessage = message;
    notifyListeners();
  }

  /// Clears the error message
  void clearError() {
    _errorMessage = null;
    notifyListeners();
  }

  /// Updates server status locally (for real-time updates)
  void updateServerStatus(String serverId, String newStatus) {
    final index = _myServers.indexWhere((s) => s.serverId == serverId);
    if (index != -1) {
      _myServers[index] = _myServers[index].copyWith(
        status: newStatus,
        updatedAt: DateTime.now(),
      );
      if (_currentServer?.serverId == serverId) {
        _currentServer = _myServers[index];
      }
      notifyListeners();
    }
  }
}

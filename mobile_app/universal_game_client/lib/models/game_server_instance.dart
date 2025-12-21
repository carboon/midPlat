/// Represents a game server instance created by the Game Server Factory.
/// This model tracks the lifecycle and status of dynamically created game servers.
class GameServerInstance {
  final String serverId;
  final String name;
  final String description;
  final String status; // "creating", "running", "stopped", "error"
  final String containerId;
  final int port;
  final DateTime createdAt;
  final DateTime updatedAt;
  final Map<String, dynamic> resourceUsage;
  final List<String> logs;

  GameServerInstance({
    required this.serverId,
    required this.name,
    required this.description,
    required this.status,
    required this.containerId,
    required this.port,
    required this.createdAt,
    required this.updatedAt,
    required this.resourceUsage,
    this.logs = const [],
  });

  factory GameServerInstance.fromJson(Map<String, dynamic> json) {
    // 安全地提取字段，确保类型正确
    final description = json['description'];
    final containerId = json['container_id'];
    
    return GameServerInstance(
      serverId: (json['server_id'] ?? '').toString(),
      name: (json['name'] ?? '').toString(),
      description: description is String ? description : (description?.toString() ?? ''),
      status: (json['status'] ?? 'unknown').toString(),
      containerId: containerId is String ? containerId : (containerId?.toString() ?? ''),
      port: (json['port'] as int?) ?? 0,
      createdAt: _parseDateTime(json['created_at']),
      updatedAt: _parseDateTime(json['updated_at']),
      resourceUsage: (json['resource_usage'] as Map<String, dynamic>?) ?? {},
      logs: _parseLogsList(json['logs']),
    );
  }

  static DateTime _parseDateTime(dynamic value) {
    if (value is String) {
      try {
        return DateTime.parse(value);
      } catch (e) {
        return DateTime.now();
      }
    }
    return DateTime.now();
  }

  static List<String> _parseLogsList(dynamic value) {
    if (value is List) {
      return value.whereType<String>().toList();
    }
    return [];
  }

  Map<String, dynamic> toJson() {
    return {
      'server_id': serverId,
      'name': name,
      'description': description,
      'status': status,
      'container_id': containerId,
      'port': port,
      'created_at': createdAt.toIso8601String(),
      'updated_at': updatedAt.toIso8601String(),
      'resource_usage': resourceUsage,
      'logs': logs,
    };
  }

  /// Returns true if the server is in a running state
  bool get isRunning => status == 'running';

  /// Returns true if the server is being created
  bool get isCreating => status == 'creating';

  /// Returns true if the server has stopped
  bool get isStopped => status == 'stopped';

  /// Returns true if the server encountered an error
  bool get hasError => status == 'error';

  /// Creates a copy of this instance with updated fields
  GameServerInstance copyWith({
    String? serverId,
    String? name,
    String? description,
    String? status,
    String? containerId,
    int? port,
    DateTime? createdAt,
    DateTime? updatedAt,
    Map<String, dynamic>? resourceUsage,
    List<String>? logs,
  }) {
    return GameServerInstance(
      serverId: serverId ?? this.serverId,
      name: name ?? this.name,
      description: description ?? this.description,
      status: status ?? this.status,
      containerId: containerId ?? this.containerId,
      port: port ?? this.port,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      resourceUsage: resourceUsage ?? this.resourceUsage,
      logs: logs ?? this.logs,
    );
  }
}

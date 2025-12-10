class Room {
  final String id;
  final String name;
  final String ip;
  final int port;
  final int playerCount;
  final int maxPlayers;
  final Map<String, dynamic> metadata;
  final String lastHeartbeat;
  final int uptime;

  Room({
    required this.id,
    required this.name,
    required this.ip,
    required this.port,
    required this.playerCount,
    required this.maxPlayers,
    required this.metadata,
    required this.lastHeartbeat,
    required this.uptime,
  });

  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['server_id'] as String,
      name: json['name'] as String,
      ip: json['ip'] as String,
      port: json['port'] as int,
      playerCount: json['current_players'] as int,
      maxPlayers: json['max_players'] as int,
      metadata: json['metadata'] as Map<String, dynamic>,
      lastHeartbeat: json['last_heartbeat'] as String,
      uptime: json['uptime'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'server_id': id,
      'name': name,
      'ip': ip,
      'port': port,
      'current_players': playerCount,
      'max_players': maxPlayers,
      'metadata': metadata,
      'last_heartbeat': lastHeartbeat,
      'uptime': uptime,
    };
  }
}
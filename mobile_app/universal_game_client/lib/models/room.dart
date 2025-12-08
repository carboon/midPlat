class Room {
  final String id;
  final String name;
  final String password;
  final int playerCount;
  final int maxPlayers;
  final String status;
  final DateTime createdAt;

  Room({
    required this.id,
    required this.name,
    required this.password,
    required this.playerCount,
    required this.maxPlayers,
    required this.status,
    required this.createdAt,
  });

  factory Room.fromJson(Map<String, dynamic> json) {
    return Room(
      id: json['id'] as String,
      name: json['name'] as String,
      password: json['password'] as String,
      playerCount: json['playerCount'] as int,
      maxPlayers: json['maxPlayers'] as int,
      status: json['status'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'password': password,
      'playerCount': playerCount,
      'maxPlayers': maxPlayers,
      'status': status,
      'createdAt': createdAt.toIso8601String(),
    };
  }
}
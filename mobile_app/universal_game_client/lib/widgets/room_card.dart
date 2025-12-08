import 'package:flutter/material.dart';

class RoomCard extends StatelessWidget {
  final String roomName;
  final int playerCount;
  final int maxPlayers;
  final VoidCallback onTap;

  const RoomCard({
    super.key,
    required this.roomName,
    required this.playerCount,
    required this.maxPlayers,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 4,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: ListTile(
        title: Text(roomName),
        subtitle: Text('玩家: $playerCount/$maxPlayers'),
        trailing: const Icon(Icons.arrow_forward_ios),
        onTap: onTap,
      ),
    );
  }
}
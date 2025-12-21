import 'package:flutter/material.dart';

class RoomCard extends StatelessWidget {
  final String roomName;
  final int playerCount;
  final int maxPlayers;
  final String? serverStatus; // 添加服务器状态
  final VoidCallback onTap;

  const RoomCard({
    super.key,
    required this.roomName,
    required this.playerCount,
    required this.maxPlayers,
    this.serverStatus,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isFull = playerCount >= maxPlayers;
    final fillPercentage = maxPlayers > 0 ? playerCount / maxPlayers : 0.0;
    
    return Card(
      elevation: 4,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Row(
            children: [
              // 房间图标
              Container(
                width: 56,
                height: 56,
                decoration: BoxDecoration(
                  color: isFull ? Colors.red[100] : Colors.green[100],
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  isFull ? Icons.lock : Icons.videogame_asset,
                  size: 32,
                  color: isFull ? Colors.red[700] : Colors.green[700],
                ),
              ),
              const SizedBox(width: 16),
              
              // 房间信息
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      roomName,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(
                          Icons.people,
                          size: 16,
                          color: Colors.grey[600],
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '$playerCount/$maxPlayers',
                          style: TextStyle(
                            fontSize: 14,
                            color: Colors.grey[600],
                          ),
                        ),
                        const SizedBox(width: 16),
                        if (isFull)
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 8,
                              vertical: 2,
                            ),
                            decoration: BoxDecoration(
                              color: Colors.red[100],
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Text(
                              '已满',
                              style: TextStyle(
                                fontSize: 12,
                                color: Colors.red[700],
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    // 服务器状态显示
                    if (serverStatus != null) ...[
                      Row(
                        children: [
                          Icon(
                            Icons.dns,
                            size: 16,
                            color: Colors.grey[600],
                          ),
                          const SizedBox(width: 4),
                          Text(
                            '状态: $serverStatus',
                            style: TextStyle(
                              fontSize: 12,
                              color: Colors.grey[600],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 8),
                    ],
                    // 玩家数量进度条
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: fillPercentage,
                        backgroundColor: Colors.grey[300],
                        valueColor: AlwaysStoppedAnimation<Color>(
                          isFull ? Colors.red : Colors.green,
                        ),
                        minHeight: 4,
                      ),
                    ),
                  ],
                ),
              ),
              
              // 箭头图标
              Icon(
                Icons.arrow_forward_ios,
                size: 20,
                color: Colors.grey[400],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
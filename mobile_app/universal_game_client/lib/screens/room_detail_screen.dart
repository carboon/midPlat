import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/room_provider.dart';
import '../widgets/custom_app_bar.dart';
import '../routes/app_routes.dart';
import '../theme/colors.dart';

class RoomDetailScreen extends StatelessWidget {
  const RoomDetailScreen({super.key});

  String _formatUptime(int seconds) {
    final hours = seconds ~/ 3600;
    final minutes = (seconds % 3600) ~/ 60;
    final secs = seconds % 60;
    
    if (hours > 0) {
      return '$hours小时 $minutes分钟';
    } else if (minutes > 0) {
      return '$minutes分钟 $secs秒';
    } else {
      return '$secs秒';
    }
  }

  @override
  Widget build(BuildContext context) {
    final room = Provider.of<RoomProvider>(context).currentRoom;

    if (room == null) {
      return Scaffold(
        appBar: CustomAppBar(title: '房间详情'),
        body: const Center(child: Text('房间信息不存在')),
      );
    }

    final isFull = room.playerCount >= room.maxPlayers;

    return Scaffold(
      appBar: CustomAppBar(title: room.name),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 房间状态卡片
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          isFull ? Icons.lock : Icons.lock_open,
                          color: isFull ? Colors.red : Colors.green,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          isFull ? '房间已满' : '可加入',
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                            color: isFull ? Colors.red : Colors.green,
                          ),
                        ),
                      ],
                    ),
                    const Divider(height: 24),
                    _buildInfoRow(Icons.people, '玩家数量', '${room.playerCount}/${room.maxPlayers}'),
                    const SizedBox(height: 12),
                    _buildInfoRow(Icons.timer, '运行时间', _formatUptime(room.uptime)),
                    const SizedBox(height: 12),
                    _buildInfoRow(Icons.access_time, '最后心跳', room.lastHeartbeat),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // 服务器信息卡片
            Card(
              elevation: 4,
              child: Padding(
                padding: const EdgeInsets.all(16.0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      '服务器信息',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Divider(height: 24),
                    _buildInfoRow(Icons.dns, '房间ID', room.id),
                    const SizedBox(height: 12),
                    _buildInfoRow(Icons.computer, 'IP地址', room.ip),
                    const SizedBox(height: 12),
                    _buildInfoRow(Icons.settings_ethernet, '端口', room.port.toString()),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            
            // 元数据卡片（如果有）
            if (room.metadata.isNotEmpty)
              Card(
                elevation: 4,
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '游戏信息',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Divider(height: 24),
                      ...room.metadata.entries.map((entry) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12.0),
                          child: _buildInfoRow(
                            Icons.info_outline,
                            entry.key,
                            entry.value.toString(),
                          ),
                        );
                      }).toList(),
                    ],
                  ),
                ),
              ),
            const SizedBox(height: 24),
            
            // 加入游戏按钮
            Center(
              child: SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: isFull ? null : () => _joinRoom(context),
                  icon: const Icon(Icons.play_arrow, size: 28),
                  label: Text(
                    isFull ? '房间已满' : '加入游戏',
                    style: const TextStyle(fontSize: 20),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: isFull ? Colors.grey : AppColors.primary,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 20, color: Colors.grey[600]),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: TextStyle(
                  fontSize: 14,
                  color: Colors.grey[600],
                ),
              ),
              const SizedBox(height: 4),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _joinRoom(BuildContext context) {
    // 直接进入游戏
    Navigator.pushNamed(context, AppRoutes.game);
  }
}
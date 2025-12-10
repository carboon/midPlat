import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/room_provider.dart';
import '../widgets/custom_app_bar.dart';
import '../routes/app_routes.dart';
import '../models/room.dart';

class RoomDetailScreen extends StatelessWidget {
  const RoomDetailScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final room = Provider.of<RoomProvider>(context).currentRoom;

    if (room == null) {
      return Scaffold(
        appBar: CustomAppBar(title: '房间详情'),
        body: const Center(child: Text('房间信息不存在')),
      );
    }

    return Scaffold(
      appBar: CustomAppBar(title: room.name),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('房间名称: ${room.name}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('房间ID: ${room.id}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('IP地址: ${room.ip}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('端口: ${room.port}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('玩家数量: ${room.playerCount}/${room.maxPlayers}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('最后心跳: ${room.lastHeartbeat}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('运行时间: ${room.uptime}秒', style: const TextStyle(fontSize: 18)),
            const Spacer(),
            Center(
              child: ElevatedButton(
                onPressed: () => _joinRoom(context),
                child: const Text('加入游戏', style: TextStyle(fontSize: 20)),
              ),
            ),
          ],
        ),
      ),
    );
  }

  void _joinRoom(BuildContext context) {
    // 直接进入游戏，不再检查密码
    Navigator.pushNamed(context, AppRoutes.game);
  }

  void _showPasswordDialog(BuildContext context) {
    // 不再需要密码对话框
  }
}
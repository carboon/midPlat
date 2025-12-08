import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/room_provider.dart';
import '../widgets/custom_app_bar.dart';
import '../routes/app_routes.dart';

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
            Text('玩家数量: ${room.playerCount}/${room.maxPlayers}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('状态: ${room.status}', style: const TextStyle(fontSize: 18)),
            const SizedBox(height: 10),
            Text('创建时间: ${room.createdAt}', style: const TextStyle(fontSize: 18)),
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
    // 如果房间有密码，先弹出密码输入框
    final room = Provider.of<RoomProvider>(context, listen: false).currentRoom;
    if (room != null && room.password.isNotEmpty) {
      _showPasswordDialog(context);
    } else {
      // 直接进入游戏
      Navigator.pushNamed(context, AppRoutes.game);
    }
  }

  void _showPasswordDialog(BuildContext context) {
    final room = Provider.of<RoomProvider>(context, listen: false).currentRoom;
    if (room == null) return;

    showDialog<String>(
      context: context,
      builder: (BuildContext context) {
        return AlertDialog(
          title: const Text('输入房间密码'),
          content: TextField(
            obscureText: true,
            decoration: const InputDecoration(hintText: '请输入密码'),
            onSubmitted: (value) {
              Navigator.of(context).pop(value);
            },
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('取消'),
            ),
          ],
        );
      },
    ).then((password) {
      if (password != null) {
        // 验证密码并进入游戏
        Navigator.pushNamed(context, AppRoutes.game);
      }
    });
  }
}
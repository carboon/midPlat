import 'package:flutter/material.dart';
import '../widgets/custom_app_bar.dart';
import '../routes/app_routes.dart';

class JoinRoomScreen extends StatelessWidget {
  const JoinRoomScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(title: '加入房间'),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            ElevatedButton(
              onPressed: () => _showPasswordDialog(context),
              child: const Text('密码加入', style: TextStyle(fontSize: 20)),
            ),
          ],
        ),
      ),
    );
  }

  void _showPasswordDialog(BuildContext context) {
    showDialog<String>(
      context: context,
      builder: (BuildContext context) {
        final roomIdController = TextEditingController();
        final passwordController = TextEditingController();

        return AlertDialog(
          title: const Text('密码加入'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: roomIdController,
                decoration: const InputDecoration(hintText: '房间ID'),
              ),
              const SizedBox(height: 10),
              TextField(
                controller: passwordController,
                decoration: const InputDecoration(hintText: '房间密码'),
                obscureText: true,
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('取消'),
            ),
            TextButton(
              onPressed: () {
                Navigator.of(context).pop([roomIdController.text, passwordController.text]);
              },
              child: const Text('加入'),
            ),
          ],
        );
      },
    ).then((values) {
      if (values != null && values.length == 2) {
        // 处理加入房间逻辑
        Navigator.pushNamed(context, AppRoutes.game);
      }
    });
  }
}
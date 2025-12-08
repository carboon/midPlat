import 'package:flutter/material.dart';

class PasswordDialog extends StatefulWidget {
  final String roomId;

  const PasswordDialog({super.key, required this.roomId});

  @override
  State<PasswordDialog> createState() => _PasswordDialogState();
}

class _PasswordDialogState extends State<PasswordDialog> {
  final TextEditingController _passwordController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: const Text('输入房间密码'),
      content: TextField(
        controller: _passwordController,
        decoration: const InputDecoration(hintText: '请输入密码'),
        obscureText: true,
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('取消'),
        ),
        TextButton(
          onPressed: () {
            Navigator.of(context).pop(_passwordController.text);
          },
          child: const Text('确定'),
        ),
      ],
    );
  }
}
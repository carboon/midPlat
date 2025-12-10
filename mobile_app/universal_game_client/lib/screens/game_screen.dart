import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:provider/provider.dart';
import '../providers/game_provider.dart';
import '../providers/room_provider.dart';
import '../widgets/custom_app_bar.dart';
import '../models/room.dart';

class GameScreen extends StatefulWidget {
  const GameScreen({super.key});

  @override
  State<GameScreen> createState() => _GameScreenState();
}

class _GameScreenState extends State<GameScreen> {
  late final WebViewController _controller;

  @override
  void initState() {
    super.initState();
    
    // 获取当前房间信息
    final room = Provider.of<RoomProvider>(context, listen: false).currentRoom;
    
    // 初始化WebView控制器
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (String url) {
            Provider.of<GameProvider>(context, listen: false).setLoading(true);
          },
          onPageFinished: (String url) {
            Provider.of<GameProvider>(context, listen: false).setLoading(false);
          },
          onWebResourceError: (WebResourceError error) {
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(content: Text('加载错误: ${error.description}')),
            );
          },
        ),
      )
      ..loadRequest(Uri.parse('http://${room?.ip ?? 'localhost'}:${room?.port ?? 8080}'));
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: '游戏加载中...',
        actions: [
          IconButton(
            icon: const Icon(Icons.close),
            onPressed: () => Navigator.of(context).pop(),
          ),
        ],
      ),
      body: Consumer<GameProvider>(
        builder: (context, gameProvider, child) {
          return Stack(
            children: [
              WebViewWidget(controller: _controller),
              if (gameProvider.isLoading)
                const Center(child: CircularProgressIndicator()),
            ],
          );
        },
      ),
    );
  }
}
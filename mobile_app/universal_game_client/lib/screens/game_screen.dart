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
    // 使用Docker容器中的服务地址
    final url = 'http://localhost:8080';
    
    print('=== GameScreen 初始化 ===');
    print('房间信息: ${room?.name}');
    print('加载 URL: $url');
    
    // 初始化WebView控制器
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (String url) {
            print('页面开始加载: $url');
            Provider.of<GameProvider>(context, listen: false).setLoading(true);
          },
          onPageFinished: (String url) {
            print('页面加载完成: $url');
            Provider.of<GameProvider>(context, listen: false).setLoading(false);
          },
          onWebResourceError: (WebResourceError error) {
            print('WebView 错误: ${error.errorCode} - ${error.description}');
            print('错误类型: ${error.errorType}');
            ScaffoldMessenger.of(context).showSnackBar(
              SnackBar(
                content: Text('加载错误: ${error.description}'),
                backgroundColor: Colors.red,
                duration: const Duration(seconds: 5),
              ),
            );
          },
          onNavigationRequest: (NavigationRequest request) {
            print('导航请求: ${request.url}');
            return NavigationDecision.navigate;
          },
        ),
      )
      ..loadRequest(Uri.parse(url));
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
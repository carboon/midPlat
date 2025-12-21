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
  Room? _room;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    
    // 获取当前房间信息
    _room = Provider.of<RoomProvider>(context, listen: false).currentRoom;
    
    if (_room == null) {
      _errorMessage = '未选择房间';
      print('错误: 未找到房间信息');
      return;
    }
    
    // 构建游戏服务器URL - 使用房间的实际IP和端口
    final url = 'http://${_room!.ip}:${_room!.port}';
    
    print('=== GameScreen 初始化 ===');
    print('房间名称: ${_room!.name}');
    print('房间ID: ${_room!.id}');
    print('服务器地址: ${_room!.ip}:${_room!.port}');
    print('加载 URL: $url');
    
    // 初始化WebView控制器
    _controller = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..setNavigationDelegate(
        NavigationDelegate(
          onPageStarted: (String url) {
            print('页面开始加载: $url');
            if (mounted) {
              Provider.of<GameProvider>(context, listen: false).setLoading(true);
            }
          },
          onPageFinished: (String url) {
            print('页面加载完成: $url');
            if (mounted) {
              Provider.of<GameProvider>(context, listen: false).setLoading(false);
            }
          },
          onWebResourceError: (WebResourceError error) {
            print('WebView 错误: ${error.errorCode} - ${error.description}');
            print('错误类型: ${error.errorType}');
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content: Text('加载错误: ${error.description}'),
                  backgroundColor: Colors.red,
                  duration: const Duration(seconds: 5),
                ),
              );
            }
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
    // 如果没有房间信息或有错误，显示错误页面
    if (_room == null || _errorMessage != null) {
      return Scaffold(
        appBar: CustomAppBar(
          title: '游戏',
          actions: [
            IconButton(
              icon: const Icon(Icons.close),
              onPressed: () => Navigator.of(context).pop(),
            ),
          ],
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 64, color: Colors.red),
              const SizedBox(height: 16),
              Text(_errorMessage ?? '未知错误'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('返回'),
              ),
            ],
          ),
        ),
      );
    }

    return Scaffold(
      appBar: CustomAppBar(
        title: _room!.name,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () {
              _controller.reload();
            },
          ),
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
                const Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      CircularProgressIndicator(),
                      SizedBox(height: 16),
                      Text('正在连接游戏服务器...'),
                    ],
                  ),
                ),
            ],
          );
        },
      ),
    );
  }
}
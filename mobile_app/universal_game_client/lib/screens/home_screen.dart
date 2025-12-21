import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/room_provider.dart';
import '../services/api_service.dart';
import '../widgets/room_card.dart';
import '../widgets/custom_app_bar.dart';
import '../routes/app_routes.dart';
import '../models/room.dart';
import '../theme/colors.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  late Future<List<Room>> _roomsFuture;
  bool _isRefreshing = false;

  @override
  void initState() {
    super.initState();
    _roomsFuture = _fetchRooms();
  }

  Future<List<Room>> _fetchRooms() async {
    try {
      final rooms = await ApiService.fetchRooms();
      // 更新provider中的房间列表
      if (mounted) {
        Provider.of<RoomProvider>(context, listen: false).setRooms(rooms);
      }
      return rooms;
    } catch (e) {
      print('获取房间列表失败: $e');
      rethrow;
    }
  }

  String _getErrorMessage(dynamic error) {
    if (error is NetworkException) {
      return error.message;
    } else if (error is ApiException) {
      return error.message;
    }
    return '加载失败: ${error.toString()}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: CustomAppBar(
        title: '游戏房间',
        actions: [
          IconButton(
            icon: const Icon(Icons.dns),
            tooltip: '我的服务器',
            onPressed: () => Navigator.pushNamed(context, AppRoutes.myServers),
          ),
          IconButton(
            icon: const Icon(Icons.upload_file),
            tooltip: '上传代码',
            onPressed: () => Navigator.pushNamed(context, AppRoutes.uploadCode),
          ),
          IconButton(
            icon: _isRefreshing 
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                    ),
                  )
                : const Icon(Icons.refresh),
            onPressed: _isRefreshing ? null : _refreshRooms,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _refreshRooms,
        child: FutureBuilder<List<Room>>(
          future: _roomsFuture,
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return const Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 16),
                    Text('正在加载房间列表...'),
                  ],
                ),
              );
            } else if (snapshot.hasError) {
              return Center(
                child: Padding(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.error_outline, size: 64, color: AppColors.error),
                      const SizedBox(height: 16),
                      Text(
                        _getErrorMessage(snapshot.error),
                        textAlign: TextAlign.center,
                        style: const TextStyle(fontSize: 16),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: _refreshRooms,
                        icon: const Icon(Icons.refresh),
                        label: const Text('重试'),
                      ),
                    ],
                  ),
                ),
              );
            } else if (snapshot.hasData) {
              final rooms = snapshot.data!;
              if (rooms.isEmpty) {
                return Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.inbox, size: 64, color: Colors.grey[400]),
                      const SizedBox(height: 16),
                      Text(
                        '暂无可用房间',
                        style: TextStyle(fontSize: 18, color: Colors.grey[600]),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '下拉刷新或创建新的游戏服务器',
                        style: TextStyle(fontSize: 14, color: Colors.grey[500]),
                      ),
                      const SizedBox(height: 24),
                      ElevatedButton.icon(
                        onPressed: () => Navigator.pushNamed(context, AppRoutes.uploadCode),
                        icon: const Icon(Icons.add),
                        label: const Text('创建游戏服务器'),
                      ),
                    ],
                  ),
                );
              }
              return ListView.builder(
                padding: const EdgeInsets.only(bottom: 80),
                itemCount: rooms.length,
                itemBuilder: (context, index) {
                  final room = rooms[index];
                  // 根据房间状态推导服务器状态
                  String serverStatus = 'active';
                  if (room.playerCount >= room.maxPlayers) {
                    serverStatus = 'full';
                  } else if (room.playerCount == 0) {
                    serverStatus = 'waiting';
                  }
                  
                  return RoomCard(
                    roomName: room.name,
                    playerCount: room.playerCount,
                    maxPlayers: room.maxPlayers,
                    serverStatus: serverStatus,
                    onTap: () => _onRoomTap(context, room),
                  );
                },
              );
            } else {
              return const Center(child: Text('暂无房间'));
            }
          },
        ),
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _navigateToJoinRoom,
        icon: const Icon(Icons.add),
        label: const Text('加入房间'),
      ),
    );
  }

  Future<void> _refreshRooms() async {
    if (_isRefreshing) return;
    
    setState(() {
      _isRefreshing = true;
    });

    try {
      setState(() {
        _roomsFuture = _fetchRooms();
      });
      await _roomsFuture;
    } finally {
      if (mounted) {
        setState(() {
          _isRefreshing = false;
        });
      }
    }
  }

  void _onRoomTap(BuildContext context, Room room) {
    // 设置当前房间
    Provider.of<RoomProvider>(context, listen: false).setCurrentRoom(room);
    
    // 导航到房间详情页
    Navigator.pushNamed(context, AppRoutes.roomDetail);
  }

  void _navigateToJoinRoom() {
    Navigator.pushNamed(context, AppRoutes.joinRoom);
  }
}
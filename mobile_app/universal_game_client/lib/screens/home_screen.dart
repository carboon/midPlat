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

  @override
  void initState() {
    super.initState();
    _roomsFuture = ApiService.fetchRooms();
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
            icon: const Icon(Icons.refresh),
            onPressed: _refreshRooms,
          ),
        ],
      ),
      body: FutureBuilder<List<Room>>(
        future: _roomsFuture,
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          } else if (snapshot.hasError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.error_outline, size: 64, color: AppColors.error),
                  const SizedBox(height: 16),
                  Text(_getErrorMessage(snapshot.error)),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: _refreshRooms,
                    child: const Text('重试'),
                  ),
                ],
              ),
            );
          } else if (snapshot.hasData) {
            final rooms = snapshot.data!;
            if (rooms.isEmpty) {
              return const Center(child: Text('暂无房间'));
            }
            return ListView.builder(
              itemCount: rooms.length,
              itemBuilder: (context, index) {
                final room = rooms[index];
                return RoomCard(
                  roomName: room.name,
                  playerCount: room.playerCount,
                  maxPlayers: room.maxPlayers,
                  onTap: () => _onRoomTap(context, room),
                );
              },
            );
          } else {
            return const Center(child: Text('暂无房间'));
          }
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _navigateToJoinRoom,
        child: const Icon(Icons.add),
      ),
    );
  }

  void _refreshRooms() {
    setState(() {
      _roomsFuture = ApiService.fetchRooms();
    });
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
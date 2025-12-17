import 'package:flutter/material.dart';
import 'app_routes.dart';
import '../screens/home_screen.dart';
import '../screens/room_detail_screen.dart';
import '../screens/join_room_screen.dart';
import '../screens/game_screen.dart';
import '../screens/my_servers_screen.dart';
import '../screens/upload_code_screen.dart';
import '../screens/server_detail_screen.dart';

class RouteGenerator {
  static Route<dynamic> generateRoute(RouteSettings settings) {
    switch (settings.name) {
      case AppRoutes.home:
        return MaterialPageRoute(builder: (_) => const HomeScreen());
      case AppRoutes.roomDetail:
        return MaterialPageRoute(builder: (_) => const RoomDetailScreen());
      case AppRoutes.joinRoom:
        return MaterialPageRoute(builder: (_) => const JoinRoomScreen());
      case AppRoutes.game:
        return MaterialPageRoute(builder: (_) => const GameScreen());
      case AppRoutes.myServers:
        return MaterialPageRoute(builder: (_) => const MyServersScreen());
      case AppRoutes.uploadCode:
        return MaterialPageRoute(builder: (_) => const UploadCodeScreen());
      case AppRoutes.serverDetail:
        return MaterialPageRoute(builder: (_) => const ServerDetailScreen());
      default:
        return _errorRoute();
    }
  }

  static Route<dynamic> _errorRoute() {
    return MaterialPageRoute(builder: (_) {
      return Scaffold(
        appBar: AppBar(title: const Text('Page Not Found')),
        body: const Center(child: Text('Page not found')),
      );
    });
  }
}
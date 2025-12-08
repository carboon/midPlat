import 'package:flutter/material.dart';
import 'app_routes.dart';
import '../screens/home_screen.dart';
import '../screens/room_detail_screen.dart';
import '../screens/join_room_screen.dart';
import '../screens/game_screen.dart';

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
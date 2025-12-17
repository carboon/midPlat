import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'app.dart';
import 'providers/room_provider.dart';
import 'providers/auth_provider.dart';
import 'providers/game_provider.dart';
import 'providers/game_server_provider.dart';

void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthProvider()),
        ChangeNotifierProvider(create: (_) => RoomProvider()),
        ChangeNotifierProvider(create: (_) => GameProvider()),
        ChangeNotifierProvider(create: (_) => GameServerProvider()),
      ],
      child: const MyApp(),
    ),
  );
}
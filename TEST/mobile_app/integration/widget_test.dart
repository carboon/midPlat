// Basic Flutter widget test for Universal Game Client.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

import 'package:universal_game_client/app.dart';
import 'package:universal_game_client/providers/auth_provider.dart';
import 'package:universal_game_client/providers/room_provider.dart';
import 'package:universal_game_client/providers/game_provider.dart';
import 'package:universal_game_client/providers/game_server_provider.dart';

void main() {
  testWidgets('App renders home screen', (WidgetTester tester) async {
    // Build our app with providers and trigger a frame.
    await tester.pumpWidget(
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

    // Verify that the app renders without errors
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}

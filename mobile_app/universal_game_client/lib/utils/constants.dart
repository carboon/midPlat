import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

class Constants {
  static String get matchmakerUrl {
    // 检查是否设置了环境变量
    if (const bool.fromEnvironment('MATCHMAKER_URL') != null) {
      return const String.fromEnvironment('MATCHMAKER_URL');
    }
    
    // 默认值
    return 'http://127.0.0.1:8000';
  }
  
  static String get appName {
    // 检查是否设置了环境变量
    if (const bool.fromEnvironment('APP_NAME') != null) {
      return const String.fromEnvironment('APP_NAME');
    }
    
    // 默认值
    return 'Universal Game Client';
  }
  
  static int get roomRefreshInterval {
    // 检查是否设置了环境变量
    if (const bool.fromEnvironment('ROOM_REFRESH_INTERVAL') != null) {
      return const int.fromEnvironment('ROOM_REFRESH_INTERVAL');
    }
    
    // 默认值
    return 30; // seconds
  }
}
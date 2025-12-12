import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:io' show Platform;

class Constants {
  static String get matchmakerUrl {
    // 检查是否设置了环境变量
    const envUrl = String.fromEnvironment('MATCHMAKER_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    
    // 默认值
    return 'http://127.0.0.1:8000';
  }
  
  static String get appName {
    // 检查是否设置了环境变量
    const envName = String.fromEnvironment('APP_NAME');
    if (envName.isNotEmpty) {
      return envName;
    }
    
    // 默认值
    return 'Universal Game Client';
  }
  
  static int get roomRefreshInterval {
    // 检查是否设置了环境变量
    const envInterval = int.fromEnvironment('ROOM_REFRESH_INTERVAL');
    if (envInterval > 0) {
      return envInterval;
    }
    
    // 默认值
    return 30; // seconds
  }
}
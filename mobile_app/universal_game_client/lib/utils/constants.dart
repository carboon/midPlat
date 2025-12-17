class Constants {
  static String get matchmakerUrl {
    const envUrl = String.fromEnvironment('MATCHMAKER_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    return 'http://127.0.0.1:8000';
  }

  static String get gameServerFactoryUrl {
    const envUrl = String.fromEnvironment('GAME_SERVER_FACTORY_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    return 'http://127.0.0.1:8001';
  }
  
  static String get appName {
    const envName = String.fromEnvironment('APP_NAME');
    if (envName.isNotEmpty) {
      return envName;
    }
    return 'Universal Game Client';
  }
  
  static int get roomRefreshInterval {
    const envInterval = int.fromEnvironment('ROOM_REFRESH_INTERVAL');
    if (envInterval > 0) {
      return envInterval;
    }
    return 30; // seconds
  }

  // Network configuration
  static const int maxRetries = 3;
  static const Duration retryDelay = Duration(seconds: 2);
  static const Duration connectionTimeout = Duration(seconds: 30);
  static const int maxFileSizeBytes = 10 * 1024 * 1024; // 10MB
}
/// 增强配置管理类 - 需求 7.3
class Constants {
  // 环境配置
  static String get environment {
    const env = String.fromEnvironment('ENVIRONMENT');
    return env.isNotEmpty ? env : 'development';
  }
  
  static bool get isProduction => environment == 'production';
  static bool get isDevelopment => environment == 'development';
  
  // 服务URL配置
  static String get matchmakerUrl {
    const envUrl = String.fromEnvironment('MATCHMAKER_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    // 根据环境返回不同的默认URL
    switch (environment) {
      case 'production':
        return 'https://matchmaker.yourdomain.com';
      case 'staging':
        return 'https://staging-matchmaker.yourdomain.com';
      default:
        return 'http://127.0.0.1:8000';
    }
  }

  static String get gameServerFactoryUrl {
    const envUrl = String.fromEnvironment('GAME_SERVER_FACTORY_URL');
    if (envUrl.isNotEmpty) {
      return envUrl;
    }
    // 根据环境返回不同的默认URL
    switch (environment) {
      case 'production':
        return 'https://factory.yourdomain.com';
      case 'staging':
        return 'https://staging-factory.yourdomain.com';
      default:
        return 'http://127.0.0.1:8080';
    }
  }
  
  // 应用配置
  static String get appName {
    const envName = String.fromEnvironment('APP_NAME');
    if (envName.isNotEmpty) {
      return envName;
    }
    return 'Universal Game Client';
  }
  
  static String get appVersion {
    const version = String.fromEnvironment('APP_VERSION');
    return version.isNotEmpty ? version : '1.0.0';
  }
  
  // 功能配置
  static int get roomRefreshInterval {
    const envInterval = int.fromEnvironment('ROOM_REFRESH_INTERVAL');
    if (envInterval > 0) {
      return envInterval;
    }
    return isProduction ? 60 : 30; // 生产环境刷新频率更低
  }

  // 网络配置 - 根据环境调整
  static int get maxRetries {
    const retries = int.fromEnvironment('MAX_RETRIES');
    if (retries > 0) return retries;
    return isProduction ? 5 : 3;
  }
  
  static Duration get retryDelay {
    const delayMs = int.fromEnvironment('RETRY_DELAY_MS');
    if (delayMs > 0) return Duration(milliseconds: delayMs);
    return Duration(seconds: isProduction ? 3 : 2);
  }
  
  static Duration get connectionTimeout {
    const timeoutMs = int.fromEnvironment('CONNECTION_TIMEOUT_MS');
    if (timeoutMs > 0) return Duration(milliseconds: timeoutMs);
    return Duration(seconds: isProduction ? 60 : 30);
  }
  
  static int get maxFileSizeBytes {
    const maxSize = int.fromEnvironment('MAX_FILE_SIZE_BYTES');
    if (maxSize > 0) return maxSize;
    return 10 * 1024 * 1024; // 10MB
  }

  // 调试和日志配置
  static bool get enableDebugLogs {
    const debug = String.fromEnvironment('ENABLE_DEBUG_LOGS');
    return debug.toLowerCase() == 'true' || isDevelopment;
  }
  
  static bool get enablePerformanceMonitoring {
    const monitoring = String.fromEnvironment('ENABLE_PERFORMANCE_MONITORING');
    return monitoring.toLowerCase() == 'true' || isProduction;
  }

  // 错误处理配置
  static bool get showDetailedErrors {
    const detailed = String.fromEnvironment('SHOW_DETAILED_ERRORS');
    return detailed.toLowerCase() == 'true' || isDevelopment;
  }
  
  static Duration get errorDisplayDuration {
    const durationMs = int.fromEnvironment('ERROR_DISPLAY_DURATION_MS');
    if (durationMs > 0) return Duration(milliseconds: durationMs);
    return const Duration(seconds: 5);
  }

  // 缓存配置
  static Duration get cacheExpiration {
    const expirationMs = int.fromEnvironment('CACHE_EXPIRATION_MS');
    if (expirationMs > 0) return Duration(milliseconds: expirationMs);
    return Duration(minutes: isProduction ? 10 : 5);
  }

  /// 验证配置参数 - 需求 7.3
  static List<String> validateConfiguration() {
    final errors = <String>[];
    
    // 验证URL格式
    try {
      Uri.parse(matchmakerUrl);
    } catch (e) {
      errors.add('Invalid MATCHMAKER_URL: $matchmakerUrl');
    }
    
    try {
      Uri.parse(gameServerFactoryUrl);
    } catch (e) {
      errors.add('Invalid GAME_SERVER_FACTORY_URL: $gameServerFactoryUrl');
    }
    
    // 验证数值配置
    if (maxRetries <= 0) {
      errors.add('MAX_RETRIES must be positive, got $maxRetries');
    }
    
    if (roomRefreshInterval <= 0) {
      errors.add('ROOM_REFRESH_INTERVAL must be positive, got $roomRefreshInterval');
    }
    
    if (maxFileSizeBytes <= 0) {
      errors.add('MAX_FILE_SIZE_BYTES must be positive, got $maxFileSizeBytes');
    }
    
    // 验证环境配置
    const validEnvironments = ['development', 'staging', 'production'];
    if (!validEnvironments.contains(environment)) {
      errors.add('ENVIRONMENT must be one of $validEnvironments, got $environment');
    }
    
    return errors;
  }
  
  /// 获取配置摘要
  static Map<String, dynamic> getConfigurationSummary() {
    return {
      'environment': environment,
      'app_name': appName,
      'app_version': appVersion,
      'matchmaker_url': matchmakerUrl,
      'game_server_factory_url': gameServerFactoryUrl,
      'max_retries': maxRetries,
      'connection_timeout_ms': connectionTimeout.inMilliseconds,
      'max_file_size_mb': (maxFileSizeBytes / (1024 * 1024)).toStringAsFixed(1),
      'debug_logs_enabled': enableDebugLogs,
      'performance_monitoring_enabled': enablePerformanceMonitoring,
    };
  }
}
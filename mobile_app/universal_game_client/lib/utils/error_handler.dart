import 'dart:developer' as developer;
import 'package:flutter/foundation.dart';
import '../services/api_service.dart';
import 'constants.dart';

/// 标准化错误类型 - 需求 8.1, 8.2, 8.3, 8.4, 8.5
enum ErrorType {
  network,
  api,
  validation,
  permission,
  fileSystem,
  unknown
}

/// 标准化错误模型
class AppError {
  final ErrorType type;
  final String message;
  final String? details;
  final int? statusCode;
  final DateTime timestamp;
  final String? stackTrace;

  AppError({
    required this.type,
    required this.message,
    this.details,
    this.statusCode,
    DateTime? timestamp,
    this.stackTrace,
  }) : timestamp = timestamp ?? DateTime.now();

  /// 从异常创建AppError
  factory AppError.fromException(dynamic exception, {ErrorType? type}) {
    if (exception is NetworkException) {
      return AppError(
        type: ErrorType.network,
        message: exception.message,
        details: exception.details,
        statusCode: exception.statusCode,
      );
    } else if (exception is ApiException) {
      return AppError(
        type: ErrorType.api,
        message: exception.message,
        statusCode: exception.statusCode,
        details: exception.errorBody?.toString(),
      );
    } else {
      return AppError(
        type: type ?? ErrorType.unknown,
        message: exception.toString(),
        stackTrace: kDebugMode ? StackTrace.current.toString() : null,
      );
    }
  }

  /// 获取用户友好的错误消息
  String get userFriendlyMessage {
    switch (type) {
      case ErrorType.network:
        if (message.contains('timeout') || message.contains('超时')) {
          return '网络连接超时，请检查网络设置后重试';
        } else if (message.contains('connection') || message.contains('连接')) {
          return '网络连接失败，请检查网络设置';
        }
        return '网络错误：$message';
      
      case ErrorType.api:
        if (statusCode == 400) {
          return '请求参数错误，请检查输入信息';
        } else if (statusCode == 401) {
          return '身份验证失败，请重新登录';
        } else if (statusCode == 403) {
          return '没有权限执行此操作';
        } else if (statusCode == 404) {
          return '请求的资源不存在';
        } else if (statusCode == 429) {
          return '请求过于频繁，请稍后重试';
        } else if (statusCode == 500) {
          return '服务器内部错误，请稍后重试';
        }
        return Constants.showDetailedErrors ? message : '服务器错误，请稍后重试';
      
      case ErrorType.validation:
        return '输入验证失败：$message';
      
      case ErrorType.permission:
        return '权限不足：$message';
      
      case ErrorType.fileSystem:
        return '文件操作失败：$message';
      
      case ErrorType.unknown:
      default:
        return Constants.showDetailedErrors ? message : '发生未知错误，请稍后重试';
    }
  }

  /// 转换为JSON格式（用于日志记录）
  Map<String, dynamic> toJson() {
    return {
      'type': type.toString(),
      'message': message,
      'details': details,
      'status_code': statusCode,
      'timestamp': timestamp.toIso8601String(),
      'stack_trace': stackTrace,
    };
  }
}

/// 全局错误处理器 - 需求 8.1, 8.2, 8.3, 8.4, 8.5
class ErrorHandler {
  static final List<AppError> _errorHistory = [];
  static const int _maxHistorySize = 100;

  /// 处理错误并返回用户友好的消息
  static String handleError(dynamic error, {ErrorType? type}) {
    final appError = AppError.fromException(error, type: type);
    
    // 记录错误
    _logError(appError);
    
    // 添加到历史记录
    _addToHistory(appError);
    
    return appError.userFriendlyMessage;
  }

  /// 记录错误到日志
  static void _logError(AppError error) {
    if (Constants.enableDebugLogs) {
      developer.log(
        'Error: ${error.message}',
        name: 'ErrorHandler',
        error: error.details,
        stackTrace: error.stackTrace != null 
            ? StackTrace.fromString(error.stackTrace!) 
            : null,
      );
    }
    
    // 在调试模式下打印详细信息
    if (kDebugMode) {
      print('=== ERROR DETAILS ===');
      print('Type: ${error.type}');
      print('Message: ${error.message}');
      print('Status Code: ${error.statusCode}');
      print('Details: ${error.details}');
      print('Timestamp: ${error.timestamp}');
      if (error.stackTrace != null) {
        print('Stack Trace: ${error.stackTrace}');
      }
      print('====================');
    }
  }

  /// 添加错误到历史记录
  static void _addToHistory(AppError error) {
    _errorHistory.add(error);
    
    // 保持历史记录大小限制
    if (_errorHistory.length > _maxHistorySize) {
      _errorHistory.removeAt(0);
    }
  }

  /// 获取错误历史记录
  static List<AppError> getErrorHistory() {
    return List.unmodifiable(_errorHistory);
  }

  /// 清除错误历史记录
  static void clearErrorHistory() {
    _errorHistory.clear();
  }

  /// 获取错误统计信息
  static Map<String, dynamic> getErrorStatistics() {
    final now = DateTime.now();
    final last24Hours = now.subtract(const Duration(hours: 24));
    final lastHour = now.subtract(const Duration(hours: 1));
    
    final recent24h = _errorHistory.where((e) => e.timestamp.isAfter(last24Hours));
    final recent1h = _errorHistory.where((e) => e.timestamp.isAfter(lastHour));
    
    final typeCount = <ErrorType, int>{};
    for (final error in recent24h) {
      typeCount[error.type] = (typeCount[error.type] ?? 0) + 1;
    }
    
    return {
      'total_errors': _errorHistory.length,
      'errors_last_24h': recent24h.length,
      'errors_last_hour': recent1h.length,
      'error_types_24h': typeCount.map((k, v) => MapEntry(k.toString(), v)),
      'most_recent_error': _errorHistory.isNotEmpty 
          ? _errorHistory.last.toJson() 
          : null,
    };
  }

  /// 检查是否应该显示错误详情
  static bool shouldShowDetailedError(AppError error) {
    // 在开发环境或配置允许时显示详细错误
    return Constants.showDetailedErrors || 
           (kDebugMode && error.type != ErrorType.network);
  }

  /// 创建网络错误
  static AppError createNetworkError(String message, {String? details}) {
    return AppError(
      type: ErrorType.network,
      message: message,
      details: details,
    );
  }

  /// 创建API错误
  static AppError createApiError(String message, int statusCode, {String? details}) {
    return AppError(
      type: ErrorType.api,
      message: message,
      statusCode: statusCode,
      details: details,
    );
  }

  /// 创建验证错误
  static AppError createValidationError(String message, {String? details}) {
    return AppError(
      type: ErrorType.validation,
      message: message,
      details: details,
    );
  }

  /// 创建权限错误
  static AppError createPermissionError(String message, {String? details}) {
    return AppError(
      type: ErrorType.permission,
      message: message,
      details: details,
    );
  }

  /// 创建文件系统错误
  static AppError createFileSystemError(String message, {String? details}) {
    return AppError(
      type: ErrorType.fileSystem,
      message: message,
      details: details,
    );
  }
}

/// 错误处理扩展方法
extension ErrorHandling on Future {
  /// 为Future添加标准化错误处理
  Future<T> handleErrors<T>({ErrorType? errorType}) async {
    try {
      return await this;
    } catch (error) {
      final message = ErrorHandler.handleError(error, type: errorType);
      throw AppError.fromException(error, type: errorType);
    }
  }
}
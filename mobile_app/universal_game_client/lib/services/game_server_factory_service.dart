import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/game_server_instance.dart';
import '../utils/constants.dart';

/// Custom exception for network-related errors
class NetworkException implements Exception {
  final String message;
  final int? statusCode;
  final String? details;

  NetworkException(this.message, {this.statusCode, this.details});

  @override
  String toString() => 'NetworkException: $message${statusCode != null ? ' (Status: $statusCode)' : ''}';
}

/// Custom exception for API-related errors
class ApiException implements Exception {
  final String message;
  final int statusCode;
  final Map<String, dynamic>? errorBody;

  ApiException(this.message, this.statusCode, {this.errorBody});

  @override
  String toString() => 'ApiException: $message (Status: $statusCode)';
}

/// Service class for interacting with the Game Server Factory API.
/// Handles code upload, server management, and lifecycle operations.
class GameServerFactoryService {
  static String get _baseUrl => Constants.gameServerFactoryUrl;

  /// Uploads a JavaScript game code file to the Game Server Factory.
  /// Returns the created GameServerInstance on success.
  /// 
  /// [file] - The JavaScript file to upload
  /// [name] - Name for the game server
  /// [description] - Description of the game
  /// [onProgress] - Optional callback for upload progress (0.0 to 1.0)
  static Future<GameServerInstance> uploadGameCode({
    required File file,
    required String name,
    String description = '',
    int maxPlayers = 10,
    void Function(double progress)? onProgress,
  }) async {
    // Validate file size
    final fileSize = await file.length();
    if (fileSize > Constants.maxFileSizeBytes) {
      throw NetworkException(
        '文件大小超过限制 (最大 ${Constants.maxFileSizeBytes ~/ (1024 * 1024)}MB)',
      );
    }

    return _withRetry(() async {
      final uri = Uri.parse('$_baseUrl/upload');
      final request = http.MultipartRequest('POST', uri);
      
      // Add file
      request.files.add(await http.MultipartFile.fromPath('file', file.path));
      
      // Add form fields
      request.fields['name'] = name;
      request.fields['description'] = description;
      request.fields['max_players'] = maxPlayers.toString();

      // Send request with progress tracking
      final streamedResponse = await request.send().timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('上传超时，请检查网络连接'),
      );

      // Simulate progress for now (actual progress tracking requires custom implementation)
      onProgress?.call(0.5);

      final response = await http.Response.fromStream(streamedResponse);
      onProgress?.call(1.0);

      if (response.statusCode == 200 || response.statusCode == 201) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return GameServerInstance.fromJson(data);
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Fetches the list of game servers created by the current user.
  static Future<List<GameServerInstance>> fetchMyServers() async {
    return _withRetry(() async {
      final response = await http.get(
        Uri.parse('$_baseUrl/servers'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => GameServerInstance.fromJson(json)).toList();
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Fetches details of a specific game server.
  static Future<GameServerInstance> fetchServerDetails(String serverId) async {
    return _withRetry(() async {
      final response = await http.get(
        Uri.parse('$_baseUrl/servers/$serverId'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return GameServerInstance.fromJson(data);
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }


  /// Stops a running game server.
  static Future<void> stopServer(String serverId) async {
    return _withRetry(() async {
      final response = await http.post(
        Uri.parse('$_baseUrl/servers/$serverId/stop'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode != 200) {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Deletes a game server and cleans up resources.
  static Future<void> deleteServer(String serverId) async {
    return _withRetry(() async {
      final response = await http.delete(
        Uri.parse('$_baseUrl/servers/$serverId'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode != 200 && response.statusCode != 204) {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Fetches logs for a specific game server.
  static Future<List<String>> fetchServerLogs(String serverId) async {
    return _withRetry(() async {
      final response = await http.get(
        Uri.parse('$_baseUrl/servers/$serverId/logs'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        if (data is List) {
          return data.cast<String>();
        } else if (data is Map && data.containsKey('logs')) {
          return (data['logs'] as List).cast<String>();
        }
        return [];
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Checks the health status of the Game Server Factory service.
  static Future<Map<String, dynamic>> checkHealth() async {
    final response = await http.get(
      Uri.parse('$_baseUrl/health'),
    ).timeout(
      const Duration(seconds: 5),
      onTimeout: () => throw NetworkException('健康检查超时'),
    );

    if (response.statusCode == 200) {
      return json.decode(response.body) as Map<String, dynamic>;
    } else {
      throw _handleErrorResponse(response);
    }
  }


  /// Handles error responses and converts them to appropriate exceptions.
  static Exception _handleErrorResponse(http.Response response) {
    Map<String, dynamic>? errorBody;
    String message;

    try {
      errorBody = json.decode(response.body) as Map<String, dynamic>;
      message = errorBody['detail'] ?? errorBody['message'] ?? '未知错误';
    } catch (_) {
      message = response.body.isNotEmpty ? response.body : '服务器错误';
    }

    switch (response.statusCode) {
      case 400:
        return ApiException('请求参数错误: $message', response.statusCode, errorBody: errorBody);
      case 401:
        return ApiException('未授权访问', response.statusCode, errorBody: errorBody);
      case 404:
        return ApiException('资源不存在: $message', response.statusCode, errorBody: errorBody);
      case 413:
        return ApiException('文件过大', response.statusCode, errorBody: errorBody);
      case 422:
        return ApiException('数据验证失败: $message', response.statusCode, errorBody: errorBody);
      case 429:
        return ApiException('请求过于频繁，请稍后重试', response.statusCode, errorBody: errorBody);
      case 500:
        return ApiException('服务器内部错误', response.statusCode, errorBody: errorBody);
      default:
        return ApiException(message, response.statusCode, errorBody: errorBody);
    }
  }

  /// Executes a request with retry logic for transient failures.
  static Future<T> _withRetry<T>(Future<T> Function() request) async {
    int attempts = 0;
    
    while (true) {
      try {
        return await request();
      } on SocketException catch (e) {
        attempts++;
        if (attempts >= Constants.maxRetries) {
          throw NetworkException('网络连接失败，请检查网络设置', details: e.message);
        }
        await Future.delayed(Constants.retryDelay * attempts);
      } on TimeoutException {
        attempts++;
        if (attempts >= Constants.maxRetries) {
          throw NetworkException('请求超时，请稍后重试');
        }
        await Future.delayed(Constants.retryDelay * attempts);
      } on ApiException {
        rethrow; // Don't retry API errors
      } on NetworkException {
        rethrow; // Don't retry network exceptions we've already created
      } catch (e) {
        attempts++;
        if (attempts >= Constants.maxRetries) {
          throw NetworkException('请求失败: ${e.toString()}');
        }
        await Future.delayed(Constants.retryDelay * attempts);
      }
    }
  }
}

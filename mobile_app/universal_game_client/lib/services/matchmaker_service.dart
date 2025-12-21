import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../models/room.dart';
import '../utils/constants.dart';
import 'game_server_factory_service.dart';

/// Service class for interacting with the Matchmaker Service API.
/// Handles room discovery and server listing operations.
class MatchmakerService {
  static String get _baseUrl => Constants.matchmakerUrl;

  /// Fetches the list of all active game rooms/servers.
  static Future<List<Room>> fetchRooms() async {
    return _withRetry(() async {
      final response = await http.get(
        Uri.parse('$_baseUrl/servers'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = json.decode(response.body);
        return data.map((json) => Room.fromJson(json)).toList();
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }

  /// Fetches details of a specific room by ID.
  static Future<Room> fetchRoomById(String id) async {
    return _withRetry(() async {
      final response = await http.get(
        Uri.parse('$_baseUrl/servers/$id'),
      ).timeout(
        Constants.connectionTimeout,
        onTimeout: () => throw NetworkException('请求超时，请检查网络连接'),
      );

      if (response.statusCode == 200) {
        final data = json.decode(response.body) as Map<String, dynamic>;
        return Room.fromJson(data);
      } else {
        throw _handleErrorResponse(response);
      }
    });
  }


  /// Checks the health status of the Matchmaker service.
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

  /// Creates a stream that periodically fetches room list updates.
  /// This enables real-time room discovery in the UI.
  /// 
  /// [interval] - How often to refresh the room list (default: 30 seconds)
  static Stream<List<Room>> watchRooms({
    Duration interval = const Duration(seconds: 30),
  }) async* {
    while (true) {
      try {
        final rooms = await fetchRooms();
        yield rooms;
        await Future.delayed(interval);
      } catch (e) {
        // Continue trying even if there's an error
        await Future.delayed(interval);
      }
    }
  }

  /// Creates a stream that monitors a specific room for updates.
  /// 
  /// [roomId] - The room ID to monitor
  /// [interval] - How often to check for updates (default: 10 seconds)
  static Stream<Room> watchRoom(
    String roomId, {
    Duration interval = const Duration(seconds: 10),
  }) async* {
    while (true) {
      try {
        final room = await fetchRoomById(roomId);
        yield room;
        await Future.delayed(interval);
      } catch (e) {
        // If room doesn't exist anymore, stop watching
        if (e is ApiException && e.statusCode == 404) {
          break;
        }
        await Future.delayed(interval);
      }
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
      case 404:
        return ApiException('房间不存在', response.statusCode, errorBody: errorBody);
      case 500:
        return ApiException('服务器内部错误', response.statusCode, errorBody: errorBody);
      default:
        return ApiException(message, response.statusCode, errorBody: errorBody);
    }
  }

  /// Executes a request with retry logic for transient failures.
  static Future<T> _withRetry<T>(Future<T> Function() request) async {
    int attempts = 0;
    Exception? lastException;
    
    while (attempts < Constants.maxRetries) {
      try {
        return await request();
      } on SocketException catch (e) {
        lastException = NetworkException('网络连接失败，请检查网络设置', details: e.message);
        attempts++;
        if (attempts >= Constants.maxRetries) break;
        
        // Exponential backoff with jitter
        final delay = Constants.retryDelay * attempts;
        final jitter = Duration(milliseconds: (delay.inMilliseconds * 0.1).round());
        await Future.delayed(delay + jitter);
      } on TimeoutException {
        lastException = NetworkException('请求超时，请稍后重试');
        attempts++;
        if (attempts >= Constants.maxRetries) break;
        
        await Future.delayed(Constants.retryDelay * attempts);
      } on HttpException catch (e) {
        lastException = NetworkException('HTTP错误: ${e.message}');
        attempts++;
        if (attempts >= Constants.maxRetries) break;
        
        await Future.delayed(Constants.retryDelay * attempts);
      } on FormatException catch (e) {
        // Don't retry format exceptions - they won't succeed on retry
        throw NetworkException('响应格式错误: ${e.message}');
      } on ApiException {
        rethrow; // Don't retry API errors - they're usually permanent
      } on NetworkException {
        rethrow; // Don't retry network exceptions we've already created
      } catch (e) {
        lastException = NetworkException('请求失败: ${e.toString()}');
        attempts++;
        if (attempts >= Constants.maxRetries) break;
        
        await Future.delayed(Constants.retryDelay * attempts);
      }
    }
    
    // If we've exhausted all retries, throw the last exception
    throw lastException ?? NetworkException('请求失败，已达到最大重试次数');
  }
}

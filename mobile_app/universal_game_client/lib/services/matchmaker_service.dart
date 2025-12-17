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
        rethrow;
      } on NetworkException {
        rethrow;
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

import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/room.dart';
import '../utils/constants.dart';

class ApiService {
  static String get _baseUrl => Constants.matchmakerUrl;

  // 获取房间列表
  static Future<List<Room>> fetchRooms() async {
    final response = await http.get(Uri.parse('$_baseUrl/servers'));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Room.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load rooms');
    }
  }

  // 根据ID获取房间详情
  static Future<Room> fetchRoomById(String id) async {
    final response = await http.get(Uri.parse('$_baseUrl/servers/$id'));

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return Room.fromJson(data);
    } else {
      throw Exception('Failed to load room');
    }
  }

  // 加入房间 - 这个功能在新的API中可能需要调整
  static Future<bool> joinRoom(String roomId, String password) async {
    // 在新的架构中，我们可能不需要显式的"加入"操作，
    // 而是直接连接到游戏服务器
    return true;
  }
}
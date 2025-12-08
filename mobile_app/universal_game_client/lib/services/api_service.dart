import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/room.dart';
import '../utils/constants.dart';

class ApiService {
  static const String _baseUrl = Constants.matchmakerUrl;

  // 获取房间列表
  static Future<List<Room>> fetchRooms() async {
    final response = await http.get(Uri.parse('$_baseUrl/rooms'));

    if (response.statusCode == 200) {
      final List<dynamic> data = json.decode(response.body);
      return data.map((json) => Room.fromJson(json)).toList();
    } else {
      throw Exception('Failed to load rooms');
    }
  }

  // 根据ID获取房间详情
  static Future<Room> fetchRoomById(String id) async {
    final response = await http.get(Uri.parse('$_baseUrl/rooms/$id'));

    if (response.statusCode == 200) {
      final Map<String, dynamic> data = json.decode(response.body);
      return Room.fromJson(data);
    } else {
      throw Exception('Failed to load room');
    }
  }

  // 加入房间
  static Future<bool> joinRoom(String roomId, String password) async {
    final response = await http.post(
      Uri.parse('$_baseUrl/rooms/$roomId/join'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(<String, String>{
        'password': password,
      }),
    );

    return response.statusCode == 200;
  }
}
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _userIdKey = 'user_id';
  static const String _usernameKey = 'username';
  static const String _tokenKey = 'token';

  // 保存用户信息
  static Future<void> saveUserInfo(String id, String username, String token) async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString(_userIdKey, id);
    await prefs.setString(_usernameKey, username);
    await prefs.setString(_tokenKey, token);
  }

  // 获取用户信息
  static Future<Map<String, String?>> getUserInfo() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    return {
      'id': prefs.getString(_userIdKey),
      'username': prefs.getString(_usernameKey),
      'token': prefs.getString(_tokenKey),
    };
  }

  // 清除用户信息
  static Future<void> clearUserInfo() async {
    final SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.remove(_userIdKey);
    await prefs.remove(_usernameKey);
    await prefs.remove(_tokenKey);
  }
}
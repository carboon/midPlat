import 'package:flutter/foundation.dart';

class GameProvider with ChangeNotifier {
  bool _isLoading = false;
  String _gameUrl = '';

  bool get isLoading => _isLoading;
  String get gameUrl => _gameUrl;

  void setLoading(bool loading) {
    _isLoading = loading;
    notifyListeners();
  }

  void setGameUrl(String url) {
    _gameUrl = url;
    notifyListeners();
  }
}
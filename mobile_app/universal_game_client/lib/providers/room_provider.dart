import 'package:flutter/foundation.dart';
import '../models/room.dart';

class RoomProvider with ChangeNotifier {
  List<Room> _rooms = [];
  Room? _currentRoom;

  List<Room> get rooms => _rooms;
  Room? get currentRoom => _currentRoom;

  void setRooms(List<Room> rooms) {
    _rooms = rooms;
    notifyListeners();
  }

  void setCurrentRoom(Room room) {
    _currentRoom = room;
    notifyListeners();
  }

  void clearCurrentRoom() {
    _currentRoom = null;
    notifyListeners();
  }
}
import 'package:socket_io_client/socket_io_client.dart' as io;

class SocketService {
  static io.Socket? _socket;

  static io.Socket get socket {
    if (_socket == null) {
      throw Exception('Socket not initialized. Call initialize() first.');
    }
    return _socket!;
  }

  // 初始化WebSocket连接
  static void initialize(String serverUrl) {
    _socket = io.io(
      serverUrl,
      io.OptionBuilder()
          .setTransports(['websocket'])
          .disableAutoConnect()
          .build(),
    );
    _socket!.connect();
  }

  // 断开连接
  static void disconnect() {
    _socket?.disconnect();
    _socket = null;
  }
}
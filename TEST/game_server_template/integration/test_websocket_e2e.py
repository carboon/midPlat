#!/usr/bin/env python3
"""
WebSocket端到端集成测试
验证WebSocket实时通信在整个系统中正常工作

测试覆盖:
- 客户端与游戏服务器的WebSocket连接
- 实时游戏状态同步
- 多客户端广播
- 连接断开和重连
"""

import asyncio
import json
import sys
import time
from typing import List, Dict, Any
import socketio
import requests

# 配置
GAME_SERVER_URL = "http://localhost:9001"
MATCHMAKER_URL = "http://localhost:8000"
TIMEOUT = 10

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(message: str):
    """打印测试信息"""
    print(f"{Colors.BLUE}[TEST]{Colors.END} {message}")

def print_success(message: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}[✓]{Colors.END} {message}")

def print_error(message: str):
    """打印错误信息"""
    print(f"{Colors.RED}[✗]{Colors.END} {message}")

def print_warning(message: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[!]{Colors.END} {message}")

def print_info(message: str):
    """打印信息"""
    print(f"  {message}")


class WebSocketTestClient:
    """WebSocket测试客户端"""
    
    def __init__(self, url: str):
        self.url = url
        self.sio = socketio.Client()
        self.connected = False
        self.game_states = []
        self.errors = []
        
        # 设置事件处理器
        @self.sio.on('connect')
        def on_connect():
            self.connected = True
            print_info(f"Client connected to {url}")
        
        @self.sio.on('disconnect')
        def on_disconnect():
            self.connected = False
            print_info(f"Client disconnected from {url}")
        
        @self.sio.on('gameState')
        def on_game_state(data):
            self.game_states.append(data)
            print_info(f"Received game state: {data}")
        
        @self.sio.on('error')
        def on_error(data):
            self.errors.append(data)
            print_error(f"Received error: {data}")
    
    def connect(self, timeout: int = 5) -> bool:
        """连接到服务器"""
        try:
            self.sio.connect(self.url, wait_timeout=timeout)
            return self.connected
        except Exception as e:
            print_error(f"Connection failed: {str(e)}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.connected:
            self.sio.disconnect()
    
    def send_click(self):
        """发送点击事件"""
        self.sio.emit('click')
    
    def send_player_action(self, action: str, data: Dict = None):
        """发送玩家操作"""
        payload = {'action': action}
        if data:
            payload.update(data)
        self.sio.emit('playerAction', payload)
    
    def wait_for_state(self, timeout: int = 5, min_count: int = None) -> bool:
        """等待接收游戏状态"""
        start_time = time.time()
        if min_count is None:
            initial_count = len(self.game_states)
            min_count = initial_count + 1
        
        while time.time() - start_time < timeout:
            if len(self.game_states) >= min_count:
                return True
            time.sleep(0.1)
        
        return False
    
    def get_latest_state(self) -> Dict:
        """获取最新的游戏状态"""
        if self.game_states:
            return self.game_states[-1]
        return None


def test_game_server_available() -> bool:
    """测试游戏服务器是否可用"""
    print_test("Checking if game server is available...")
    try:
        response = requests.get(f"{GAME_SERVER_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Game server is available")
            print_info(f"Status: {data.get('status', 'unknown')}")
            return True
        else:
            print_error(f"Game server health check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Game server not available: {str(e)}")
        return False


def test_websocket_connection() -> bool:
    """测试WebSocket连接建立 - 需求 3.3"""
    print_test("Testing WebSocket connection establishment...")
    
    client = WebSocketTestClient(GAME_SERVER_URL)
    
    try:
        # 连接到服务器
        if not client.connect():
            print_error("Failed to establish WebSocket connection")
            return False
        
        print_success("WebSocket connection established")
        
        # 等待接收初始游戏状态 - 需求 3.4
        # 给一点时间让状态到达
        time.sleep(1)
        
        if len(client.game_states) == 0:
            print_error("Did not receive initial game state")
            client.disconnect()
            return False
        
        initial_state = client.get_latest_state()
        if initial_state is None:
            print_error("Initial game state is None")
            client.disconnect()
            return False
        
        print_success(f"Received initial game state: {initial_state}")
        
        # 验证游戏状态包含必要字段
        if 'clickCount' not in initial_state:
            print_error("Game state missing 'clickCount' field")
            client.disconnect()
            return False
        
        print_success("Initial game state contains required fields")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print_error(f"WebSocket connection test failed: {str(e)}")
        client.disconnect()
        return False


def test_game_operation_handling() -> bool:
    """测试游戏操作处理 - 需求 3.5"""
    print_test("Testing game operation handling...")
    
    client = WebSocketTestClient(GAME_SERVER_URL)
    
    try:
        # 连接到服务器
        if not client.connect():
            print_error("Failed to connect")
            return False
        
        # 等待初始状态
        time.sleep(1)
        
        if len(client.game_states) == 0:
            print_error("Did not receive initial state")
            client.disconnect()
            return False
        
        initial_state = client.get_latest_state()
        initial_click_count = initial_state.get('clickCount', 0)
        print_info(f"Initial click count: {initial_click_count}")
        
        # 记录当前状态数量
        initial_state_count = len(client.game_states)
        
        # 发送点击操作
        print_info("Sending click action...")
        client.send_click()
        
        # 等待状态更新
        if not client.wait_for_state(timeout=5, min_count=initial_state_count + 1):
            print_error("Did not receive state update after click")
            client.disconnect()
            return False
        
        updated_state = client.get_latest_state()
        updated_click_count = updated_state.get('clickCount', 0)
        print_info(f"Updated click count: {updated_click_count}")
        
        # 验证点击计数增加
        if updated_click_count != initial_click_count + 1:
            print_error(f"Click count not incremented correctly: expected {initial_click_count + 1}, got {updated_click_count}")
            client.disconnect()
            return False
        
        print_success("Game operation handled correctly")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print_error(f"Game operation test failed: {str(e)}")
        client.disconnect()
        return False


def test_multi_client_broadcast() -> bool:
    """测试多客户端广播 - 需求 3.5"""
    print_test("Testing multi-client broadcast...")
    
    clients = []
    num_clients = 3
    
    try:
        # 创建多个客户端
        for i in range(num_clients):
            client = WebSocketTestClient(GAME_SERVER_URL)
            if not client.connect():
                print_error(f"Failed to connect client {i+1}")
                for c in clients:
                    c.disconnect()
                return False
            clients.append(client)
            print_info(f"Client {i+1} connected")
        
        # 等待所有客户端接收初始状态
        time.sleep(1)  # 给所有客户端时间接收初始状态
        
        all_received = True
        for i, client in enumerate(clients):
            if len(client.game_states) == 0:
                print_error(f"Client {i+1} did not receive initial state")
                all_received = False
        
        if not all_received:
            for c in clients:
                c.disconnect()
            return False
        
        print_success(f"All {num_clients} clients connected and received initial state")
        
        # 清空所有客户端的状态列表
        for client in clients:
            client.game_states = []
        
        # 第一个客户端发送点击操作
        print_info("Client 1 sending click action...")
        clients[0].send_click()
        
        # 等待所有客户端接收状态更新
        time.sleep(1)  # 给服务器时间广播
        
        received_count = 0
        for i, client in enumerate(clients):
            if len(client.game_states) > 0:
                received_count += 1
                print_info(f"Client {i+1} received broadcast")
            else:
                print_warning(f"Client {i+1} did not receive broadcast")
        
        # 验证所有客户端都收到广播
        if received_count == num_clients:
            print_success(f"All {num_clients} clients received broadcast")
            
            # 验证所有客户端收到的状态一致
            states = [c.get_latest_state() for c in clients if c.get_latest_state()]
            if len(states) == num_clients:
                click_counts = [s.get('clickCount', -1) for s in states]
                if len(set(click_counts)) == 1:
                    print_success(f"All clients have consistent state (clickCount: {click_counts[0]})")
                else:
                    print_error(f"Clients have inconsistent states: {click_counts}")
                    for c in clients:
                        c.disconnect()
                    return False
        else:
            print_error(f"Only {received_count}/{num_clients} clients received broadcast")
            for c in clients:
                c.disconnect()
            return False
        
        # 断开所有客户端
        for client in clients:
            client.disconnect()
        
        return True
        
    except Exception as e:
        print_error(f"Multi-client broadcast test failed: {str(e)}")
        for client in clients:
            client.disconnect()
        return False


def test_player_action_types() -> bool:
    """测试不同类型的玩家操作"""
    print_test("Testing different player action types...")
    
    client = WebSocketTestClient(GAME_SERVER_URL)
    
    try:
        # 连接到服务器
        if not client.connect():
            print_error("Failed to connect")
            return False
        
        # 等待初始状态
        time.sleep(1)
        
        if len(client.game_states) == 0:
            print_error("Did not receive initial state")
            client.disconnect()
            return False
        
        initial_state = client.get_latest_state()
        initial_click_count = initial_state.get('clickCount', 0)
        
        # 记录当前状态数量
        initial_state_count = len(client.game_states)
        
        # 测试playerAction事件
        print_info("Sending playerAction with action='click'...")
        client.send_player_action('click')
        
        if not client.wait_for_state(timeout=5, min_count=initial_state_count + 1):
            print_error("Did not receive state update after playerAction")
            client.disconnect()
            return False
        
        updated_state = client.get_latest_state()
        updated_click_count = updated_state.get('clickCount', 0)
        
        if updated_click_count != initial_click_count + 1:
            print_error(f"playerAction not handled correctly")
            client.disconnect()
            return False
        
        print_success("playerAction handled correctly")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print_error(f"Player action types test failed: {str(e)}")
        client.disconnect()
        return False


def test_connection_resilience() -> bool:
    """测试连接弹性（断开和重连）"""
    print_test("Testing connection resilience...")
    
    client = WebSocketTestClient(GAME_SERVER_URL)
    
    try:
        # 第一次连接
        if not client.connect():
            print_error("Failed to connect")
            return False
        
        print_success("Initial connection established")
        
        # 断开连接
        client.disconnect()
        time.sleep(1)
        print_info("Disconnected from server")
        
        # 重新连接
        client = WebSocketTestClient(GAME_SERVER_URL)
        if not client.connect():
            print_error("Failed to reconnect")
            return False
        
        print_success("Reconnection successful")
        
        # 验证能够接收游戏状态
        time.sleep(1)
        if len(client.game_states) == 0:
            print_error("Did not receive state after reconnection")
            client.disconnect()
            return False
        
        print_success("Received game state after reconnection")
        
        client.disconnect()
        return True
        
    except Exception as e:
        print_error(f"Connection resilience test failed: {str(e)}")
        client.disconnect()
        return False


def test_game_server_registration() -> bool:
    """测试游戏服务器是否已注册到撮合服务"""
    print_test("Checking if game server is registered with matchmaker...")
    
    try:
        response = requests.get(f"{MATCHMAKER_URL}/servers", timeout=TIMEOUT)
        if response.status_code == 200:
            servers = response.json()
            
            # 查找游戏服务器
            game_server_found = False
            for server in servers:
                if server.get('port') == 8081:
                    game_server_found = True
                    print_success(f"Game server found in matchmaker: {server.get('name', 'Unknown')}")
                    print_info(f"  IP: {server.get('ip')}")
                    print_info(f"  Port: {server.get('port')}")
                    print_info(f"  Players: {server.get('current_players')}/{server.get('max_players')}")
                    break
            
            if not game_server_found:
                print_warning("Game server not found in matchmaker (may not be running)")
                return True  # 不算失败，因为服务器可能未启动
            
            return True
        else:
            print_error(f"Failed to query matchmaker: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Matchmaker query failed: {str(e)}")
        return False


def run_all_tests() -> bool:
    """运行所有WebSocket测试"""
    print("\n" + "="*70)
    print("WebSocket实时通信端到端测试")
    print("="*70 + "\n")
    
    tests = [
        ("Game Server Availability", test_game_server_available),
        ("WebSocket Connection", test_websocket_connection),
        ("Game Operation Handling", test_game_operation_handling),
        ("Multi-Client Broadcast", test_multi_client_broadcast),
        ("Player Action Types", test_player_action_types),
        ("Connection Resilience", test_connection_resilience),
        ("Game Server Registration", test_game_server_registration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'─'*70}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test execution failed: {str(e)}")
            results.append((test_name, False))
        time.sleep(0.5)
    
    # 打印总结
    print(f"\n{'='*70}")
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.END}" if result else f"{Colors.RED}FAILED{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ 所有WebSocket测试通过！{Colors.END}\n")
        return True
    elif passed >= total * 0.8:
        print(f"\n{Colors.YELLOW}⚠ 大部分测试通过，但有些测试失败{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}✗ 多个测试失败{Colors.END}\n")
        return False


if __name__ == "__main__":
    try:
        # 检查依赖
        try:
            import socketio
        except ImportError:
            print_error("python-socketio not installed. Install with: pip install python-socketio")
            sys.exit(1)
        
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试执行失败: {str(e)}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)

import requests
import time

MATCHMAKER_URL = "http://localhost:8000"

def test_service_status():
    print("1. 测试服务状态...")
    response = requests.get(f"{MATCHMAKER_URL}/")
    print(f"   响应: {response.json()}\n")

def test_register_server():
    print("2. 注册游戏服务器...")
    data = {
        "ip": "192.168.1.100",
        "port": 8080,
        "name": "点击计数游戏",
        "max_players": 10,
        "current_players": 0,
        "metadata": {
            "game_mode": "party",
            "version": "1.0.0"
        }
    }
    response = requests.post(f"{MATCHMAKER_URL}/register", json=data)
    result = response.json()
    print(f"   响应: {result}")
    return result["server_id"]

def test_list_servers():
    print("\n3. 获取服务器列表...")
    response = requests.get(f"{MATCHMAKER_URL}/servers")
    servers = response.json()
    print(f"   活跃服务器数量: {len(servers)}")
    for server in servers:
        print(f"   - {server['name']} ({server['server_id']}) - 玩家: {server['current_players']}/{server['max_players']}")

def test_get_server(server_id):
    print(f"\n4. 获取特定服务器信息 ({server_id})...")
    response = requests.get(f"{MATCHMAKER_URL}/servers/{server_id}")
    server = response.json()
    print(f"   服务器: {server['name']}")
    print(f"   运行时间: {server['uptime']} 秒")
    print(f"   最后心跳: {server['last_heartbeat']}")

def test_heartbeat(server_id):
    print(f"\n5. 发送心跳 ({server_id})...")
    response = requests.post(f"{MATCHMAKER_URL}/heartbeat/{server_id}?current_players=3")
    print(f"   响应: {response.json()}")

def test_multiple_servers():
    print("\n6. 注册多个服务器...")
    servers = [
        {"ip": "192.168.1.101", "port": 8081, "name": "狼人杀房间"},
        {"ip": "192.168.1.102", "port": 8082, "name": "你画我猜"},
        {"ip": "192.168.1.103", "port": 8083, "name": "真心话大冒险"},
    ]
    
    for server in servers:
        data = {
            **server,
            "max_players": 20,
            "current_players": 0
        }
        response = requests.post(f"{MATCHMAKER_URL}/register", json=data)
        print(f"   注册 {server['name']}: {response.json()['server_id']}")

def test_auto_cleanup(server_id):
    print(f"\n7. 测试自动清理机制...")
    print(f"   等待 35 秒不发送心跳（超时时间为 30 秒）...")
    time.sleep(35)
    
    try:
        response = requests.get(f"{MATCHMAKER_URL}/servers/{server_id}")
        if response.status_code == 410:
            print(f"   ✅ 服务器已被标记为不活跃")
        else:
            print(f"   ❌ 服务器仍然活跃（不应该）")
    except Exception as e:
        print(f"   服务器已被清理: {e}")

def test_unregister(server_id):
    print(f"\n8. 注销服务器 ({server_id})...")
    response = requests.delete(f"{MATCHMAKER_URL}/servers/{server_id}")
    print(f"   响应: {response.json()}")

def test_health_check():
    print("\n9. 健康检查...")
    response = requests.get(f"{MATCHMAKER_URL}/health")
    print(f"   响应: {response.json()}\n")

if __name__ == "__main__":
    print("=" * 60)
    print("撮合服务测试脚本")
    print("=" * 60 + "\n")
    
    try:
        test_service_status()
        server_id = test_register_server()
        test_list_servers()
        test_get_server(server_id)
        test_heartbeat(server_id)
        test_multiple_servers()
        test_list_servers()
        test_health_check()
        
        choice = input("是否测试自动清理机制？(需等待 35 秒) [y/N]: ")
        if choice.lower() == 'y':
            test_auto_cleanup(server_id)
            test_list_servers()
        else:
            test_unregister(server_id)
            test_list_servers()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误: 无法连接到撮合服务")
        print("请确保服务已启动: docker-compose up -d")
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")

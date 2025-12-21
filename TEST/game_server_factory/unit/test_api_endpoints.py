#!/usr/bin/env python3
"""
测试所有API端点 - 分解为多个小测试

这个文件包含了原来的 test_all_api_endpoints 分解后的多个小测试。
每个测试只测试一个 API 端点，提高了测试的执行速度和可维护性。
"""

import pytest
from fastapi.testclient import TestClient
from main import app, game_servers, GameServerInstance
from datetime import datetime


@pytest.fixture
def client():
    """提供 FastAPI TestClient"""
    return TestClient(app)


@pytest.fixture
def test_server(client):
    """创建一个测试服务器"""
    test_server_id = "test_server_001"
    test_server = GameServerInstance(
        server_id=test_server_id,
        name="测试服务器",
        description="用于API测试的服务器",
        status="running",
        container_id=None,  # 虚拟服务器不设置 container_id
        port=8081,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        resource_usage={"cpu_percent": 15.5, "memory_mb": 256},
        logs=["服务器已启动", "容器运行正常", "准备接受连接"]
    )
    game_servers[test_server_id] = test_server
    yield test_server
    # 清理
    if test_server_id in game_servers:
        del game_servers[test_server_id]


def test_root_endpoint(client):
    """测试 GET /"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


def test_health_check_endpoint(client):
    """测试 GET /health"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "containers" in data


def test_get_servers_empty(client):
    """测试 GET /servers (空列表)"""
    response = client.get("/servers")
    assert response.status_code == 200
    servers = response.json()
    assert isinstance(servers, list)
    assert len(servers) == 0


def test_get_servers_with_data(client, test_server):
    """测试 GET /servers (有数据)"""
    response = client.get("/servers")
    assert response.status_code == 200
    servers = response.json()
    assert len(servers) == 1
    assert servers[0]["name"] == "测试服务器"
    assert servers[0]["status"] == "running"


def test_get_server_details(client, test_server):
    """测试 GET /servers/{server_id}"""
    response = client.get(f"/servers/{test_server.server_id}")
    assert response.status_code == 200
    server = response.json()
    assert server["name"] == "测试服务器"
    assert server["status"] == "running"
    assert server["port"] == 8081
    assert len(server["logs"]) == 3


def test_get_nonexistent_server(client):
    """测试 GET /servers/nonexistent"""
    response = client.get("/servers/nonexistent")
    assert response.status_code == 404
    error = response.json()
    assert "detail" in error or "error" in error


def test_get_server_logs(client, test_server):
    """测试 GET /servers/{server_id}/logs"""
    response = client.get(f"/servers/{test_server.server_id}/logs")
    assert response.status_code == 200
    logs_data = response.json()
    assert "log_count" in logs_data
    assert "logs" in logs_data
    assert logs_data["log_count"] == 3


def test_stop_server(client, test_server):
    """测试 POST /servers/{server_id}/stop"""
    response = client.post(f"/servers/{test_server.server_id}/stop")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    assert result["status"] == "stopped"
    
    # 验证服务器状态已更新
    detail_response = client.get(f"/servers/{test_server.server_id}")
    assert detail_response.status_code == 200
    server = detail_response.json()
    assert server["status"] == "stopped"


def test_stop_nonexistent_server(client):
    """测试 POST /servers/nonexistent/stop"""
    response = client.post("/servers/nonexistent/stop")
    assert response.status_code == 404


def test_delete_server(client, test_server):
    """测试 DELETE /servers/{server_id}"""
    server_id = test_server.server_id
    response = client.delete(f"/servers/{server_id}")
    assert response.status_code == 200
    result = response.json()
    assert "message" in result
    
    # 验证服务器已被删除
    detail_response = client.get(f"/servers/{server_id}")
    assert detail_response.status_code == 404


def test_delete_nonexistent_server(client):
    """测试 DELETE /servers/nonexistent"""
    response = client.delete("/servers/nonexistent")
    assert response.status_code == 404


def test_system_stats_endpoint(client):
    """测试 GET /system/stats"""
    response = client.get("/system/stats")
    assert response.status_code == 200
    stats = response.json()
    assert "game_servers_count" in stats
    assert "docker_available" in stats
    assert "resource_manager_available" in stats


def test_containers_status_endpoint(client):
    """测试 GET /containers/status"""
    response = client.get("/containers/status")
    assert response.status_code == 200
    containers = response.json()
    assert "total_containers" in containers


def test_api_endpoints_list(client):
    """测试 GET /api/endpoints"""
    response = client.get("/api/endpoints")
    assert response.status_code == 200
    endpoints = response.json()
    assert "total_endpoints" in endpoints


def test_upload_html_game(client, monkeypatch):
    """测试 POST /upload"""
    from unittest.mock import Mock, patch
    
    # Arrange - Mock Docker管理器
    mock_docker_manager = Mock()
    mock_docker_manager.create_html_game_server.return_value = (
        'test_container_id_123',
        8084,
        'test_image_id_456'
    )
    
    # Mock资源管理器
    mock_resource_manager = Mock()
    mock_resource_manager.can_create_container.return_value = (True, "可以创建容器")
    
    # 替换全局对象
    monkeypatch.setattr('main.docker_manager', mock_docker_manager)
    monkeypatch.setattr('main.resource_manager', mock_resource_manager)
    
    # Act
    html_content = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    files = {'file': ('test.html', html_content, 'text/html')}
    data = {'name': 'API测试游戏', 'description': '用于API测试', 'max_players': 5}
    
    response = client.post('/upload', files=files, data=data)
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "server_id" in result
    assert "message" in result
    assert "validation_result" in result
    
    # 验证Docker管理器被调用
    mock_docker_manager.create_html_game_server.assert_called_once()
    
    # 清理创建的服务器
    server_id = result.get('server_id')
    if server_id and server_id in game_servers:
        del game_servers[server_id]
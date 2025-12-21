"""
端到端集成测试 - 需求 6.1, 8.1, 8.2, 8.3, 8.4, 8.5
测试系统各组件的集成和端到端工作流程
"""

import pytest
import sys
import time
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

# 添加父目录到路径
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def test_client():
    """提供测试客户端"""
    from main import app
    return TestClient(app)


def test_service_health(test_client):
    """测试服务健康状态"""
    # Arrange & Act
    response = test_client.get("/health")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "timestamp" in data


def test_error_response_format(test_client):
    """测试错误响应格式标准化 - 需求 6.4, 6.5"""
    # Arrange & Act
    response = test_client.get("/servers/nonexistent_server")
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    
    # 验证错误响应结构
    assert "error" in data
    error = data["error"]
    
    required_fields = ['code', 'message', 'timestamp', 'path']
    for field in required_fields:
        assert field in error, f"Missing required field: {field}"
    
    assert error["code"] == 404


def test_configuration_validation(test_client):
    """测试配置验证 - 需求 7.3"""
    # Arrange & Act
    response = test_client.get("/system/stats")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    
    # 验证包含配置信息
    assert "timestamp" in data
    assert "game_servers_count" in data


def test_servers_list_endpoint(test_client):
    """测试服务器列表端点"""
    # Arrange & Act
    response = test_client.get("/servers")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_root_endpoint(test_client):
    """测试根端点"""
    # Arrange & Act
    response = test_client.get("/")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "version" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

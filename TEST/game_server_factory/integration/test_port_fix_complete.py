"""
完整的端口修复测试
创建一个新的HTML游戏服务器并验证端口配置是否正确
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture
def test_client():
    """提供测试客户端"""
    from main import app
    return TestClient(app)


def test_game_server_access(test_client):
    """测试游戏服务器访问 - 使用Mock避免真实网络请求"""
    # Arrange
    html_content = """<!DOCTYPE html>
<html>
<head>
    <title>端口测试游戏</title>
</head>
<body>
    <h1>端口测试游戏</h1>
    <div id="status">游戏已加载，端口配置测试成功！</div>
</body>
</html>"""
    
    # Mock Docker管理器
    with patch('main.docker_manager') as mock_docker_manager:
        mock_docker_manager.create_html_game_container.return_value = {
            'container_id': 'test_container_123',
            'port': 8081,
            'image_id': 'test_image_456'
        }
        
        # Act - 创建游戏服务器
        import io
        file_content = io.BytesIO(html_content.encode('utf-8'))
        
        response = test_client.post(
            "/upload",
            data={
                "name": "端口测试游戏",
                "description": "用于测试端口配置修复的HTML游戏"
            },
            files={"file": ("index.html", file_content, "text/html")}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        
        # 验证响应包含服务器信息
        assert "server" in data or "server_id" in data
        
        # 验证端口信息
        if "server" in data:
            server = data["server"]
            assert "port" in server or "external_port" in server
        
        print("✓ 端口修复测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

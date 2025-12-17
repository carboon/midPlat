"""
Docker集成测试
测试Docker容器管理功能
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from docker_manager import DockerManager, ContainerInfo

class TestDockerManager:
    """Docker管理器测试"""
    
    def test_dockerfile_generation(self):
        """测试Dockerfile生成"""
        # 模拟Docker客户端
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            # 模拟网络不存在，然后创建成功
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # 测试Dockerfile生成
            user_code = """
function initGame() {
    return { score: 0 };
}

function handlePlayerAction(gameState, action, data) {
    if (action === 'click') {
        gameState.score++;
    }
    return gameState;
}
"""
            
            dockerfile = manager._generate_dockerfile(user_code, "测试游戏")
            
            # 验证Dockerfile内容
            assert "FROM node:16-alpine" in dockerfile
            assert "WORKDIR /usr/src/app" in dockerfile
            assert "npm install express socket.io axios dotenv" in dockerfile
            assert "COPY server.js ./" in dockerfile
            assert "COPY user_game.js ./" in dockerfile
            assert "EXPOSE 8080" in dockerfile
            assert 'ENV ROOM_NAME="测试游戏"' in dockerfile
    
    def test_server_template_generation(self):
        """测试服务器模板生成"""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            user_code = "console.log('Hello World');"
            server_template = manager._generate_server_template(
                user_code, "测试游戏", "http://localhost:8000"
            )
            
            # 验证服务器模板内容
            assert "const express = require('express');" in server_template
            assert "const socketIo = require('socket.io');" in server_template
            assert "require('./user_game.js')" in server_template
            assert "测试游戏" in server_template
            assert "http://localhost:8000" in server_template
            assert "socket.on('playerAction'" in server_template
    
    def test_user_code_preparation(self):
        """测试用户代码准备"""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # 测试没有module.exports的代码
            user_code_without_exports = """
function initGame() {
    return { score: 0 };
}
"""
            
            prepared_code = manager._prepare_user_code(user_code_without_exports)
            assert "module.exports" in prepared_code
            assert "initGame" in prepared_code
            
            # 测试已有module.exports的代码
            user_code_with_exports = """
function initGame() {
    return { score: 0 };
}

module.exports = { initGame };
"""
            
            prepared_code = manager._prepare_user_code(user_code_with_exports)
            assert prepared_code == user_code_with_exports
    
    def test_port_finding(self):
        """测试端口查找功能"""
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # 模拟socket
            with patch('socket.socket') as mock_socket:
                mock_socket_instance = Mock()
                mock_socket_instance.__enter__ = Mock(return_value=mock_socket_instance)
                mock_socket_instance.__exit__ = Mock(return_value=None)
                mock_socket_instance.bind.return_value = None
                mock_socket.return_value = mock_socket_instance
                
                port = manager._find_available_port()
                assert port >= manager.base_port
                assert port < manager.base_port + 1000

class TestContainerInfo:
    """容器信息测试"""
    
    def test_container_info_creation(self):
        """测试容器信息创建"""
        # 模拟Docker容器
        mock_container = Mock()
        mock_container.id = "abc123"
        mock_container.short_id = "abc123"[:12]
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.attrs = {"Created": "2025-12-17T10:00:00Z"}
        
        container_info = ContainerInfo(mock_container)
        
        assert container_info.id == "abc123"
        assert container_info.name == "test-container"
        assert container_info.status == "running"
    
    def test_container_stats(self):
        """测试容器统计信息"""
        mock_container = Mock()
        mock_container.id = "abc123"
        mock_container.short_id = "abc123"[:12]
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.attrs = {"Created": "2025-12-17T10:00:00Z"}
        
        # 模拟统计数据
        mock_stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 1000000, "percpu_usage": [500000, 500000]},
                "system_cpu_usage": 10000000
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 900000},
                "system_cpu_usage": 9000000
            },
            "memory_stats": {
                "usage": 134217728,  # 128MB
                "limit": 268435456   # 256MB
            },
            "networks": {
                "eth0": {
                    "rx_bytes": 1048576,  # 1MB
                    "tx_bytes": 2097152   # 2MB
                }
            }
        }
        
        mock_container.stats.return_value = mock_stats
        
        container_info = ContainerInfo(mock_container)
        stats = container_info.get_stats()
        
        assert "cpu_percent" in stats
        assert "memory_usage_mb" in stats
        assert "network_rx_mb" in stats
        assert stats["memory_usage_mb"] == 128.0
        assert stats["network_rx_mb"] == 1.0
    
    def test_container_logs(self):
        """测试容器日志获取"""
        mock_container = Mock()
        mock_container.id = "abc123"
        mock_container.short_id = "abc123"[:12]
        mock_container.name = "test-container"
        mock_container.status = "running"
        mock_container.attrs = {"Created": "2025-12-17T10:00:00Z"}
        
        # 模拟日志
        mock_logs = b"2025-12-17T10:00:00Z Server started\n2025-12-17T10:00:01Z Game initialized"
        mock_container.logs.return_value = mock_logs
        
        container_info = ContainerInfo(mock_container)
        logs = container_info.get_logs()
        
        assert len(logs) == 2
        assert "Server started" in logs[0]
        assert "Game initialized" in logs[1]

if __name__ == "__main__":
    # 运行基本测试
    print("运行Docker管理器测试...")
    
    test_manager = TestDockerManager()
    test_container = TestContainerInfo()
    
    try:
        test_manager.test_dockerfile_generation()
        print("✓ Dockerfile生成测试通过")
        
        test_manager.test_server_template_generation()
        print("✓ 服务器模板生成测试通过")
        
        test_manager.test_user_code_preparation()
        print("✓ 用户代码准备测试通过")
        
        test_manager.test_port_finding()
        print("✓ 端口查找测试通过")
        
        test_container.test_container_info_creation()
        print("✓ 容器信息创建测试通过")
        
        test_container.test_container_stats()
        print("✓ 容器统计信息测试通过")
        
        test_container.test_container_logs()
        print("✓ 容器日志测试通过")
        
        print("\n所有测试通过! ✓")
        
    except Exception as e:
        print(f"\n测试失败: {e}")
        import traceback
        traceback.print_exc()
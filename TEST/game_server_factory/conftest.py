"""
Pytest configuration and fixtures for Game Server Factory tests

This module provides a comprehensive testing framework for Game Server Factory,
including fixtures for test setup, cleanup, and server management.
"""

import pytest
import sys
import os
from typing import Dict, Optional, Any
from datetime import datetime

# Add game_server_factory source directory to path for imports
# This allows tests to import from the game_server_factory module
game_server_factory_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    'game_server_factory'
)
sys.path.insert(0, game_server_factory_path)


# ============================================================================
# Pytest-xdist 串行执行配置
# ============================================================================

def pytest_collection_modifyitems(items):
    """
    修改测试收集，将标记为serial的测试移到最后并禁用并行执行
    """
    serial_tests = []
    parallel_tests = []
    
    for item in items:
        if item.get_closest_marker('serial'):
            # 为串行测试添加xdist_group标记，确保它们在同一个worker中执行
            item.add_marker(pytest.mark.xdist_group(name="serial"))
            serial_tests.append(item)
        else:
            parallel_tests.append(item)
    
    # 重新排序：先执行并行测试，再执行串行测试
    items[:] = parallel_tests + serial_tests


# ============================================================================
# 测试服务器工厂类 - 用于创建和管理测试服务器
# ============================================================================

class TestServerFactory:
    """
    测试服务器工厂类，提供便捷的方法来创建和管理测试服务器。
    
    这个类简化了测试代码，避免重复的服务器创建逻辑。
    """
    
    def __init__(self):
        """初始化工厂"""
        self.created_servers = []
    
    def create_test_server(
        self,
        server_id: str,
        name: str = "Test Server",
        description: str = "A test server",
        status: str = "running",
        container_id: Optional[str] = None,
        port: Optional[int] = None,
        resource_usage: Optional[Dict[str, Any]] = None,
        logs: Optional[list] = None
    ) -> 'GameServerInstance':
        """
        创建一个测试服务器实例。
        
        Args:
            server_id: 服务器唯一标识
            name: 服务器名称
            description: 服务器描述
            status: 服务器状态 (creating, running, stopped, error)
            container_id: Docker 容器 ID（虚拟服务器默认为 None）
            port: 服务器端口
            resource_usage: 资源使用情况
            logs: 服务器日志
        
        Returns:
            GameServerInstance: 创建的服务器实例
        
        Example:
            >>> factory = TestServerFactory()
            >>> server = factory.create_test_server("test_001")
            >>> assert server.server_id == "test_001"
        """
        from main import GameServerInstance, game_servers
        
        # ✅ 修复：虚拟服务器不设置 container_id
        # 这样 API 就不会尝试查询不存在的 Docker 容器
        # 如果用户显式传入 container_id，则使用用户提供的值
        
        # 生成默认的端口
        if port is None:
            port = 8000 + (hash(server_id) % 1000)
        
        # 生成默认的资源使用情况
        if resource_usage is None:
            resource_usage = {
                "cpu_percent": 10.5,
                "memory_mb": 128,
                "memory_limit_mb": 512,
                "network_rx_mb": 0.5,
                "network_tx_mb": 0.3
            }
        
        # 生成默认的日志
        if logs is None:
            logs = [
                f"Server {server_id} started",
                "Game initialized",
                "Ready to accept connections"
            ]
        
        # 创建服务器实例
        server = GameServerInstance(
            server_id=server_id,
            name=name,
            description=description,
            status=status,
            container_id=container_id,  # 虚拟服务器的 container_id 为 None
            port=port,
            resource_usage=resource_usage,
            logs=logs
        )
        
        # 添加到全局字典
        game_servers[server_id] = server
        
        # 记录创建的服务器
        self.created_servers.append(server_id)
        
        return server
    
    def create_multiple_test_servers(
        self,
        count: int,
        prefix: str = "test_server",
        **kwargs
    ) -> list:
        """
        创建多个测试服务器。
        
        Args:
            count: 要创建的服务器数量
            prefix: 服务器 ID 前缀
            **kwargs: 传递给 create_test_server 的其他参数
        
        Returns:
            list: 创建的服务器实例列表
        
        Example:
            >>> factory = TestServerFactory()
            >>> servers = factory.create_multiple_test_servers(3)
            >>> assert len(servers) == 3
        """
        servers = []
        for i in range(count):
            server_id = f"{prefix}_{i:03d}"
            server = self.create_test_server(server_id, **kwargs)
            servers.append(server)
        return servers
    
    def cleanup(self):
        """
        清理所有创建的测试服务器。
        
        Example:
            >>> factory = TestServerFactory()
            >>> factory.create_test_server("test_001")
            >>> factory.cleanup()
            >>> # 所有服务器已被删除
        """
        from main import game_servers
        
        for server_id in self.created_servers:
            if server_id in game_servers:
                del game_servers[server_id]
        
        self.created_servers.clear()


# ============================================================================
# Pytest 固件 - 提供测试所需的资源
# ============================================================================

@pytest.fixture(autouse=True)
def clear_game_servers():
    """
    自动清空全局 game_servers 字典，防止测试之间的状态污染。
    
    这个固件在每个测试前后都会运行。
    """
    from main import game_servers
    
    # 测试前清空
    game_servers.clear()
    
    yield
    
    # 测试后清空
    game_servers.clear()


@pytest.fixture(autouse=True)
def reset_docker_manager():
    """
    重置 Docker 管理器的状态（如需要）。
    """
    yield


@pytest.fixture(autouse=True, scope="function")
def cleanup_test_containers():
    """
    清理测试期间创建的任何容器。
    这在每个测试后运行，以确保没有容器污染。
    """
    yield
    
    # 测试后：清理任何测试容器
    try:
        from main import docker_manager
        if docker_manager:
            # 获取所有游戏容器
            containers = docker_manager.list_game_containers()
            for container in containers:
                try:
                    # 仅清理测试容器（名称中包含 'test'）
                    if 'test' in container.name.lower():
                        docker_manager.stop_container(container.id)
                        docker_manager.remove_container(container.id)
                except Exception:
                    # 忽略清理期间的错误
                    pass
    except Exception:
        # 如果 docker_manager 不可用，忽略错误
        pass


@pytest.fixture
def test_client():
    """
    提供 FastAPI TestClient 用于发送请求。
    
    Returns:
        TestClient: FastAPI 测试客户端
    
    Example:
        >>> def test_health_check(test_client):
        ...     response = test_client.get("/health")
        ...     assert response.status_code == 200
    """
    from fastapi.testclient import TestClient
    from main import app
    
    return TestClient(app)


@pytest.fixture
def server_factory():
    """
    提供测试服务器工厂，用于创建和管理测试服务器。
    
    Returns:
        TestServerFactory: 测试服务器工厂实例
    
    Example:
        >>> def test_server_details(server_factory, test_client):
        ...     # 创建测试服务器
        ...     server = server_factory.create_test_server("test_001")
        ...     
        ...     # 查询服务器
        ...     response = test_client.get(f"/servers/{server.server_id}")
        ...     assert response.status_code == 200
        ...     
        ...     # 清理
        ...     server_factory.cleanup()
    """
    factory = TestServerFactory()
    yield factory
    factory.cleanup()


# ============================================================================
# 便捷函数 - 简化测试代码
# ============================================================================

def setup_test_server(
    server_id: str,
    name: str = "Test Server",
    description: str = "A test server",
    status: str = "running",
    container_id: Optional[str] = None,
    port: Optional[int] = None,
    resource_usage: Optional[Dict[str, Any]] = None,
    logs: Optional[list] = None
) -> 'GameServerInstance':
    """
    便捷函数：创建一个测试服务器。
    
    这是一个全局函数，可以在测试中直接使用，无需创建工厂实例。
    
    Args:
        server_id: 服务器唯一标识
        name: 服务器名称
        description: 服务器描述
        status: 服务器状态
        container_id: Docker 容器 ID
        port: 服务器端口
        resource_usage: 资源使用情况
        logs: 服务器日志
    
    Returns:
        GameServerInstance: 创建的服务器实例
    
    Example:
        >>> from conftest import setup_test_server
        >>> server = setup_test_server("test_001")
        >>> assert server.server_id == "test_001"
    """
    factory = TestServerFactory()
    return factory.create_test_server(
        server_id=server_id,
        name=name,
        description=description,
        status=status,
        container_id=container_id,
        port=port,
        resource_usage=resource_usage,
        logs=logs
    )


def setup_multiple_test_servers(
    count: int,
    prefix: str = "test_server",
    **kwargs
) -> list:
    """
    便捷函数：创建多个测试服务器。
    
    Args:
        count: 要创建的服务器数量
        prefix: 服务器 ID 前缀
        **kwargs: 传递给 setup_test_server 的其他参数
    
    Returns:
        list: 创建的服务器实例列表
    
    Example:
        >>> from conftest import setup_multiple_test_servers
        >>> servers = setup_multiple_test_servers(3)
        >>> assert len(servers) == 3
    """
    factory = TestServerFactory()
    return factory.create_multiple_test_servers(count=count, prefix=prefix, **kwargs)


# ============================================================================
# Mock 固件 - 用于性能优化（方案 2）
# ============================================================================

@pytest.fixture
def mock_docker_manager(monkeypatch):
    """
    提供 Mock Docker 管理器，用于性能优化。
    
    这个 fixture 使用 monkeypatch 来替换真实的 Docker 操作，
    从而大幅提高测试执行速度。
    
    Returns:
        MagicMock: Mock Docker 管理器
    
    Example:
        >>> def test_with_mock(mock_docker_manager):
        ...     # 使用 Mock Docker 管理器
        ...     result = mock_docker_manager.create_html_game_container(...)
        ...     assert result['container_id'] == 'test_container_id_123'
    """
    from unittest.mock import MagicMock, patch
    
    # 创建 Mock 对象
    mock_manager = MagicMock()
    
    # Mock 容器创建
    mock_manager.create_html_game_container.return_value = {
        'container_id': 'test_container_id_123',
        'port': 8081,
        'image_id': 'test_image_id_456'
    }
    
    # Mock 容器查询
    mock_manager.get_container_info.return_value = {
        'Id': 'test_container_id_123',
        'State': {
            'Running': True,
            'Status': 'running'
        },
        'Config': {
            'Env': ['PORT=8081']
        },
        'NetworkSettings': {
            'Ports': {
                '8080/tcp': [{'HostPort': '8081'}]
            }
        }
    }
    
    # Mock 容器停止
    mock_manager.stop_container.return_value = True
    
    # Mock 容器删除
    mock_manager.remove_container.return_value = True
    
    # Mock 镜像构建
    mock_manager.build_image.return_value = 'test_image_id_456'
    
    # Mock 容器列表
    mock_manager.list_game_containers.return_value = []
    
    # Mock 容器状态查询
    mock_manager.get_container_status.return_value = {
        'status': 'running',
        'cpu_percent': 10.5,
        'memory_mb': 128
    }
    
    return mock_manager


@pytest.fixture
def mock_docker_client(monkeypatch):
    """
    提供 Mock Docker 客户端。
    
    Returns:
        MagicMock: Mock Docker 客户端
    """
    from unittest.mock import MagicMock
    
    mock_client = MagicMock()
    
    # Mock 容器操作
    mock_client.containers.create.return_value = MagicMock(
        id='test_container_id_123',
        name='html-game-server-test'
    )
    
    mock_client.containers.get.return_value = MagicMock(
        id='test_container_id_123',
        status='running'
    )
    
    mock_client.images.build.return_value = (
        MagicMock(id='test_image_id_456'),
        []
    )
    
    return mock_client


@pytest.fixture
def mock_resource_manager(monkeypatch):
    """
    提供 Mock 资源管理器。
    
    Returns:
        MagicMock: Mock 资源管理器
    """
    from unittest.mock import MagicMock
    
    mock_manager = MagicMock()
    
    # Mock 资源查询
    mock_manager.get_resource_usage.return_value = {
        'cpu_percent': 10.5,
        'memory_mb': 128,
        'memory_limit_mb': 512,
        'network_rx_mb': 0.5,
        'network_tx_mb': 0.3
    }
    
    # Mock 资源分配
    mock_manager.allocate_resources.return_value = True
    
    # Mock 资源释放
    mock_manager.release_resources.return_value = True
    
    return mock_manager


@pytest.fixture
def mock_html_validator(monkeypatch):
    """
    提供 Mock HTML 验证器。
    
    Returns:
        MagicMock: Mock HTML 验证器
    """
    from unittest.mock import MagicMock
    
    mock_validator = MagicMock()
    
    # Mock 验证方法
    mock_validator.validate_html_file.return_value = {
        'valid': True,
        'errors': []
    }
    
    mock_validator.validate_zip_file.return_value = {
        'valid': True,
        'errors': []
    }
    
    return mock_validator


@pytest.fixture
def mock_code_analyzer(monkeypatch):
    """
    提供 Mock 代码分析器。
    
    Returns:
        MagicMock: Mock 代码分析器
    """
    from unittest.mock import MagicMock
    
    mock_analyzer = MagicMock()
    
    # Mock 安全分析
    mock_analyzer.analyze_security.return_value = {
        'safe': True,
        'issues': []
    }
    
    # Mock 代码分析
    mock_analyzer.analyze_code.return_value = {
        'valid': True,
        'errors': []
    }
    
    return mock_analyzer


# ============================================================================
# 性能优化辅助函数
# ============================================================================

def use_mock_docker(monkeypatch):
    """
    辅助函数：在测试中使用 Mock Docker。
    
    这个函数可以在测试中调用，以启用 Mock Docker 操作。
    
    Args:
        monkeypatch: pytest 的 monkeypatch fixture
    
    Example:
        >>> def test_with_mock_docker(monkeypatch):
        ...     use_mock_docker(monkeypatch)
        ...     # 现在所有 Docker 操作都是 Mock 的
    """
    from unittest.mock import MagicMock, patch
    
    # 创建 Mock Docker 管理器
    mock_manager = MagicMock()
    mock_manager.create_html_game_container.return_value = {
        'container_id': 'test_container_id_123',
        'port': 8081
    }
    
    # 替换 Docker 管理器
    monkeypatch.setattr('docker_manager.DockerManager', lambda: mock_manager)


# ============================================================================
# Pytest 标记定义
# ============================================================================

def pytest_configure(config):
    """
    配置 pytest 标记。
    
    这个函数在 pytest 启动时调用，用于注册自定义标记。
    """
    config.addinivalue_line(
        "markers", "serial: 标记测试为串行执行（不适合并行执行）"
    )
    config.addinivalue_line(
        "markers", "slow: 标记测试为慢速测试"
    )
    config.addinivalue_line(
        "markers", "fast: 标记测试为快速测试"
    )

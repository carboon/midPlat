"""
示例测试文件 - 展示如何使用改进的测试框架

这个文件演示了如何使用新的 setup_test_server() 方法和 server_factory 固件
来简化测试代码并避免 HTTP 404 错误。

**Feature: ai-game-platform, Framework: Improved Test Framework**
"""

import pytest
from hypothesis import given, strategies as st, settings


class TestServerDetailsWithNewFramework:
    """使用新测试框架的服务器详情测试"""
    
    def test_get_server_details_basic(self, server_factory, test_client):
        """
        基本测试：获取服务器详情
        
        这个测试演示了如何使用 server_factory 固件创建测试服务器。
        """
        # 1. 创建测试服务器
        server = server_factory.create_test_server(
            server_id="test_001",
            name="Test Game",
            description="A test game server"
        )
        
        # 2. 查询服务器详情
        response = test_client.get(f"/servers/{server.server_id}")
        
        # 3. 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["server_id"] == "test_001"
        assert data["name"] == "Test Game"
        assert data["status"] == "running"
    
    def test_get_server_with_custom_status(self, server_factory, test_client):
        """
        测试：获取不同状态的服务器
        
        这个测试演示了如何创建具有不同状态的测试服务器。
        """
        # 创建停止状态的服务器
        server = server_factory.create_test_server(
            server_id="test_stopped",
            status="stopped"
        )
        
        # 查询服务器
        response = test_client.get(f"/servers/{server.server_id}")
        
        # 验证状态
        assert response.status_code == 200
        assert response.json()["status"] == "stopped"
    
    def test_get_server_with_custom_resources(self, server_factory, test_client):
        """
        测试：获取具有自定义资源的服务器
        
        这个测试演示了如何创建具有自定义资源使用情况的测试服务器。
        """
        # 创建具有自定义资源的服务器
        server = server_factory.create_test_server(
            server_id="test_resources",
            resource_usage={
                "cpu_percent": 75.5,
                "memory_mb": 256,
                "memory_limit_mb": 512,
                "network_rx_mb": 10.5,
                "network_tx_mb": 5.2
            }
        )
        
        # 查询服务器
        response = test_client.get(f"/servers/{server.server_id}")
        
        # 验证资源信息
        assert response.status_code == 200
        data = response.json()
        assert data["resource_usage"]["cpu_percent"] == 75.5
        assert data["resource_usage"]["memory_mb"] == 256


class TestMultipleServersWithNewFramework:
    """使用新测试框架的多服务器测试"""
    
    def test_list_multiple_servers(self, server_factory, test_client):
        """
        测试：列出多个服务器
        
        这个测试演示了如何创建多个测试服务器。
        """
        # 1. 创建多个测试服务器
        servers = server_factory.create_multiple_test_servers(3)
        
        # 2. 查询服务器列表
        response = test_client.get("/servers")
        
        # 3. 验证响应
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_list_servers_with_custom_prefix(self, server_factory, test_client):
        """
        测试：使用自定义前缀创建多个服务器
        
        这个测试演示了如何使用自定义前缀创建多个测试服务器。
        """
        # 创建具有自定义前缀的服务器
        servers = server_factory.create_multiple_test_servers(
            count=5,
            prefix="game_server"
        )
        
        # 验证服务器 ID
        for i, server in enumerate(servers):
            assert server.server_id == f"game_server_{i:03d}"


class TestPropertyBasedWithNewFramework:
    """使用新测试框架的属性测试"""
    
    @given(
        server_id=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789_.-',
            min_size=5,
            max_size=30
        ),
        name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
            min_size=1,
            max_size=100
        )
    )
    @settings(max_examples=10, suppress_health_check=[])
    def test_server_details_property(self, server_id, name):
        """
        属性测试：验证服务器详情
        
        这个测试演示了如何在属性测试中创建测试服务器。
        
        **Feature: ai-game-platform, Property: Server Details Display**
        **Validates: Requirement 2.4**
        """
        # ✅ 修复：不使用 fixture，直接创建服务器
        from conftest import setup_test_server
        from fastapi.testclient import TestClient
        from main import app
        
        # 确保 server_id 不以 . 或 - 开头
        if server_id.startswith(('.', '-')):
            server_id = 'a' + server_id[1:]
        
        # 创建测试服务器
        server = setup_test_server(server_id, name=name)
        
        # 创建测试客户端
        test_client = TestClient(app)
        
        # 查询服务器
        response = test_client.get(f"/servers/{server_id}")
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["server_id"] == server_id
        assert data["name"] == name
        assert data["status"] == "running"
    
    @given(
        count=st.integers(min_value=1, max_value=5),
        status=st.sampled_from(["running", "stopped", "error"])
    )
    @settings(max_examples=10, suppress_health_check=[])
    def test_multiple_servers_property(self, count, status):
        """
        属性测试：验证多个服务器
        
        这个测试演示了如何在属性测试中创建多个服务器。
        
        **Feature: ai-game-platform, Property: Multiple Servers Management**
        **Validates: Requirement 2.5**
        """
        # ✅ 修复：不使用 fixture，直接创建服务器
        from conftest import setup_multiple_test_servers
        from fastapi.testclient import TestClient
        from main import app
        
        # 创建多个具有相同状态的服务器
        servers = setup_multiple_test_servers(count=count, status=status)
        
        # 创建测试客户端
        test_client = TestClient(app)
        
        # 验证服务器数量
        assert len(servers) == count
        
        # 验证每个服务器的状态
        for server in servers:
            assert server.status == status


class TestErrorHandlingWithNewFramework:
    """使用新测试框架的错误处理测试"""
    
    def test_get_nonexistent_server_returns_404(self, test_client):
        """
        测试：查询不存在的服务器返回 404
        
        这个测试演示了如何测试 404 错误处理。
        注意：这个测试不需要创建测试服务器。
        """
        # 查询不存在的服务器
        response = test_client.get("/servers/nonexistent_server_id")
        
        # 验证 404 错误
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert "服务器不存在" in data["error"]["message"]
    
    def test_server_details_consistency(self, server_factory, test_client):
        """
        测试：服务器详情一致性
        
        这个测试演示了如何验证服务器详情的一致性。
        """
        # 创建测试服务器
        server = server_factory.create_test_server("test_consistency")
        
        # 多次查询服务器
        response1 = test_client.get(f"/servers/{server.server_id}")
        response2 = test_client.get(f"/servers/{server.server_id}")
        
        # 验证响应一致
        assert response1.json() == response2.json()


# ============================================================================
# 使用便捷函数的示例
# ============================================================================

def test_using_setup_function(test_client):
    """
    示例：使用 setup_test_server() 便捷函数
    
    这个测试演示了如何使用全局便捷函数创建测试服务器。
    """
    from conftest import setup_test_server
    
    # 创建测试服务器
    server = setup_test_server("test_function")
    
    # 查询服务器
    response = test_client.get(f"/servers/{server.server_id}")
    
    # 验证响应
    assert response.status_code == 200


def test_using_multiple_servers_function(test_client):
    """
    示例：使用 setup_multiple_test_servers() 便捷函数
    
    这个测试演示了如何使用全局便捷函数创建多个测试服务器。
    """
    from conftest import setup_multiple_test_servers
    
    # 创建多个测试服务器
    servers = setup_multiple_test_servers(3)
    
    # 查询服务器列表
    response = test_client.get("/servers")
    
    # 验证响应
    assert response.status_code == 200
    assert len(response.json()) == 3


# ============================================================================
# 总结
# ============================================================================

"""
这个示例文件展示了如何使用改进的测试框架：

1. **基本用法**
   - 使用 server_factory 固件创建单个服务器
   - 使用 server_factory 固件创建多个服务器
   - 自动清理（无需手动调用 cleanup()）

2. **高级用法**
   - 创建具有自定义状态的服务器
   - 创建具有自定义资源的服务器
   - 在属性测试中使用 server_factory

3. **错误处理**
   - 测试 404 错误处理
   - 验证服务器详情一致性

4. **便捷函数**
   - 使用 setup_test_server() 快速创建服务器
   - 使用 setup_multiple_test_servers() 批量创建服务器

关键优势：
✅ 代码简洁：从 10+ 行减少到 1 行
✅ 自动清理：无需手动调用 cleanup()
✅ 类型安全：完整的类型提示
✅ 易于维护：集中管理服务器创建逻辑
✅ 避免 404 错误：确保服务器存在再查询
"""

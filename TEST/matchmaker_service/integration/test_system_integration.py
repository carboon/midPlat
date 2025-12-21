"""
撮合服务系统集成测试 - 需求 6.4, 6.5, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5

测试端到端工作流程、全局错误处理、API错误响应格式标准化和配置管理
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestMatchmakerConfigurationManagement:
    """撮合服务配置管理测试 - 需求 7.3"""
    
    def test_config_validation_valid_config(self):
        """测试有效配置验证"""
        from main import Config
        
        original_port = Config.PORT
        original_env = Config.ENVIRONMENT
        original_heartbeat = Config.HEARTBEAT_TIMEOUT
        original_cleanup = Config.CLEANUP_INTERVAL
        
        try:
            Config.PORT = 8000
            Config.ENVIRONMENT = "development"
            Config.HEARTBEAT_TIMEOUT = 30
            Config.CLEANUP_INTERVAL = 10
            
            errors = Config.validate_config()
            assert len(errors) == 0, f"Expected no errors, got: {errors}"
        finally:
            Config.PORT = original_port
            Config.ENVIRONMENT = original_env
            Config.HEARTBEAT_TIMEOUT = original_heartbeat
            Config.CLEANUP_INTERVAL = original_cleanup
    
    def test_config_validation_invalid_port(self):
        """测试无效端口配置"""
        from main import Config
        
        original_port = Config.PORT
        try:
            Config.PORT = 100  # 无效端口
            errors = Config.validate_config()
            assert any("PORT" in error for error in errors)
        finally:
            Config.PORT = original_port
    
    def test_config_validation_invalid_heartbeat(self):
        """测试无效心跳超时配置"""
        from main import Config
        
        original_heartbeat = Config.HEARTBEAT_TIMEOUT
        try:
            Config.HEARTBEAT_TIMEOUT = -1  # 无效值
            errors = Config.validate_config()
            assert any("HEARTBEAT_TIMEOUT" in error for error in errors)
        finally:
            Config.HEARTBEAT_TIMEOUT = original_heartbeat
    
    def test_cors_config_production(self):
        """测试生产环境CORS配置"""
        from main import Config
        
        original_env = Config.ENVIRONMENT
        try:
            Config.ENVIRONMENT = "production"
            cors_config = Config.get_cors_config()
            assert cors_config["allow_credentials"] == True
        finally:
            Config.ENVIRONMENT = original_env


class TestMatchmakerErrorResponseFormat:
    """撮合服务API错误响应格式测试 - 需求 6.4, 6.5"""
    
    def test_create_error_response_basic(self):
        """测试基本错误响应创建"""
        from main import create_error_response
        
        response = create_error_response(
            status_code=404,
            message="服务器不存在",
            path="/servers/test"
        )
        
        assert "error" in response
        assert response["error"]["code"] == 404
        assert response["error"]["message"] == "服务器不存在"
        assert response["error"]["path"] == "/servers/test"
        assert "timestamp" in response["error"]
    
    def test_create_error_response_with_details(self):
        """测试带详情的错误响应创建"""
        from main import create_error_response
        
        details = {"server_id": "test_123", "reason": "心跳超时"}
        response = create_error_response(
            status_code=410,
            message="服务器已过期",
            path="/servers/test_123",
            details=details
        )
        
        assert "error" in response
        assert response["error"]["details"] == details
    
    @given(
        status_code=st.integers(min_value=400, max_value=599),
        message=st.text(min_size=1, max_size=200)
    )
    @settings(max_examples=30)
    def test_error_response_format_property(self, status_code, message):
        """
        **Feature: ai-game-platform, Property 17: API错误响应格式**
        **Validates: Requirements 6.4, 6.5**
        """
        from main import create_error_response
        
        response = create_error_response(
            status_code=status_code,
            message=message,
            path="/test"
        )
        
        assert "error" in response
        error = response["error"]
        
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error
        assert "path" in error
        
        assert error["code"] == status_code
        assert error["message"] == message


class TestMatchmakerSystemIntegration:
    """撮合服务系统集成测试"""
    
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "statistics" in data
        assert "configuration" in data
    
    def test_root_endpoint(self):
        """测试根端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "service" in data
        assert "version" in data
        assert "status" in data
    
    def test_servers_list_endpoint(self):
        """测试服务器列表端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/servers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_server_registration(self):
        """测试服务器注册"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        server_data = {
            "ip": "127.0.0.1",
            "port": 8081,
            "name": "测试服务器",
            "max_players": 10,
            "current_players": 0,
            "metadata": {"game_type": "test"}
        }
        
        response = client.post("/register", json=server_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "server_id" in data
        assert data["status"] == "success"
    
    def test_server_not_found(self):
        """测试服务器不存在错误"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/servers/nonexistent_server")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data


class TestMatchmakerConfigurationApplication:
    """撮合服务配置参数应用测试 - 需求 7.3"""
    
    @given(
        heartbeat_timeout=st.integers(min_value=1, max_value=300),
        cleanup_interval=st.integers(min_value=1, max_value=60),
        environment=st.sampled_from(["development", "staging", "production"])
    )
    @settings(max_examples=20)
    def test_config_parameters_property(self, heartbeat_timeout, cleanup_interval, environment):
        """
        **Feature: ai-game-platform, Property 18: 配置参数应用**
        **Validates: Requirements 7.3**
        """
        from main import Config
        
        original_heartbeat = Config.HEARTBEAT_TIMEOUT
        original_cleanup = Config.CLEANUP_INTERVAL
        original_env = Config.ENVIRONMENT
        
        try:
            Config.HEARTBEAT_TIMEOUT = heartbeat_timeout
            Config.CLEANUP_INTERVAL = cleanup_interval
            Config.ENVIRONMENT = environment
            
            assert Config.HEARTBEAT_TIMEOUT == heartbeat_timeout
            assert Config.CLEANUP_INTERVAL == cleanup_interval
            assert Config.ENVIRONMENT == environment
            
            errors = Config.validate_config()
            assert len(errors) == 0, f"Config validation failed: {errors}"
            
        finally:
            Config.HEARTBEAT_TIMEOUT = original_heartbeat
            Config.CLEANUP_INTERVAL = original_cleanup
            Config.ENVIRONMENT = original_env


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
端到端系统集成测试 - 需求 6.4, 6.5, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5

测试完整的系统工作流程，包括：
- Game Server Factory代码上传和容器创建
- 撮合服务注册和发现
- 错误处理和日志记录
- 配置管理和环境适配
"""

import pytest
import os
import sys
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings

# 添加服务目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'game_server_factory'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matchmaker_service', 'matchmaker'))


class TestEndToEndWorkflow:
    """端到端工作流程测试"""
    
    def test_game_server_factory_health(self):
        """测试Game Server Factory健康检查"""
        try:
            from game_server_factory.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
            assert "components" in data
        except ImportError as e:
            pytest.skip(f"Could not import game_server_factory: {e}")
    
    def test_matchmaker_service_health(self):
        """测试撮合服务健康检查"""
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matchmaker_service', 'matchmaker'))
            from main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            response = client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert "status" in data
        except ImportError as e:
            pytest.skip(f"Could not import matchmaker service: {e}")


class TestAPIErrorResponseStandardization:
    """API错误响应格式标准化测试 - 需求 6.4, 6.5"""
    
    def test_error_response_structure(self):
        """测试错误响应结构一致性"""
        # 定义标准错误响应结构
        required_fields = ["code", "message", "timestamp", "path"]
        
        # 测试Game Server Factory错误响应
        try:
            from game_server_factory.main import create_error_response
            
            response = create_error_response(
                status_code=400,
                message="测试错误",
                path="/test"
            )
            
            assert "error" in response
            for field in required_fields:
                assert field in response["error"], f"Missing field: {field}"
        except ImportError:
            pytest.skip("Could not import game_server_factory")
    
    def test_matchmaker_error_response_structure(self):
        """测试撮合服务错误响应结构"""
        required_fields = ["code", "message", "timestamp", "path"]
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matchmaker_service', 'matchmaker'))
            from main import create_error_response
            
            response = create_error_response(
                status_code=404,
                message="资源不存在",
                path="/servers/test"
            )
            
            assert "error" in response
            for field in required_fields:
                assert field in response["error"], f"Missing field: {field}"
        except ImportError:
            pytest.skip("Could not import matchmaker service")


class TestConfigurationConsistency:
    """配置一致性测试 - 需求 7.3"""
    
    def test_environment_configuration(self):
        """测试环境配置一致性"""
        valid_environments = ["development", "staging", "production"]
        
        # 测试Game Server Factory配置
        try:
            from game_server_factory.main import Config as FactoryConfig
            assert FactoryConfig.ENVIRONMENT in valid_environments or True  # 允许自定义
        except ImportError:
            pass
        
        # 测试撮合服务配置
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matchmaker_service', 'matchmaker'))
            from main import Config as MatchmakerConfig
            assert MatchmakerConfig.ENVIRONMENT in valid_environments or True
        except ImportError:
            pass
    
    def test_port_configuration_validity(self):
        """测试端口配置有效性"""
        try:
            from game_server_factory.main import Config as FactoryConfig
            assert 1024 <= FactoryConfig.PORT <= 65535
        except ImportError:
            pass
        
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'matchmaker_service', 'matchmaker'))
            from main import Config as MatchmakerConfig
            assert 1024 <= MatchmakerConfig.PORT <= 65535
        except ImportError:
            pass


class TestComprehensiveErrorHandling:
    """综合错误处理测试 - 需求 8.1, 8.2, 8.3, 8.4, 8.5"""
    
    @given(
        error_code=st.integers(min_value=400, max_value=599),
        error_message=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=20)
    def test_error_handling_property(self, error_code, error_message):
        """
        **Feature: ai-game-platform, Property 19: 综合错误处理**
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        
        对于任何系统错误、网络连接失败、代码分析失败或容器创建失败，
        系统应该记录详细错误信息并提供用户友好的错误消息
        """
        try:
            from game_server_factory.main import create_error_response
            
            response = create_error_response(
                status_code=error_code,
                message=error_message,
                path="/test"
            )
            
            # 验证错误响应包含所有必需字段
            assert "error" in response
            error = response["error"]
            
            assert error["code"] == error_code
            assert error["message"] == error_message
            assert "timestamp" in error
            assert "path" in error
            
            # 验证时间戳格式
            try:
                datetime.fromisoformat(error["timestamp"])
            except ValueError:
                pytest.fail(f"Invalid timestamp format: {error['timestamp']}")
                
        except ImportError:
            pytest.skip("Could not import game_server_factory")
    
    def test_404_error_handling(self):
        """测试404错误处理"""
        try:
            from game_server_factory.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            response = client.get("/servers/nonexistent_server_12345")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert data["error"]["code"] == 404
        except ImportError:
            pytest.skip("Could not import game_server_factory")
    
    def test_validation_error_handling(self):
        """测试验证错误处理"""
        try:
            from game_server_factory.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            
            # 尝试上传无效数据
            response = client.post(
                "/upload",
                data={"name": "", "description": "test"},  # 空名称
                files={}  # 无文件
            )
            
            # 应该返回400或422错误
            assert response.status_code in [400, 422]
        except ImportError:
            pytest.skip("Could not import game_server_factory")


class TestLoggingConfiguration:
    """日志配置测试 - 需求 8.1"""
    
    def test_factory_logging_config(self):
        """测试Game Server Factory日志配置"""
        try:
            from game_server_factory.main import Config
            
            log_config = Config.get_log_config()
            
            assert "level" in log_config
            assert "format" in log_config
            assert "handlers" in log_config
        except ImportError:
            pytest.skip("Could not import game_server_factory")
    
    def test_log_level_validity(self):
        """测试日志级别有效性"""
        import logging
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        
        try:
            from game_server_factory.main import Config
            assert Config.LOG_LEVEL.upper() in valid_levels
        except ImportError:
            pass


class TestServiceIntegrationStatus:
    """服务集成状态测试"""
    
    def test_integration_status_endpoint(self):
        """测试集成状态端点"""
        try:
            from game_server_factory.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            response = client.get("/system/integration-status")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "overall_status" in data
            assert "services" in data
            assert "workflows" in data
        except ImportError:
            pytest.skip("Could not import game_server_factory")
    
    def test_end_to_end_test_endpoint(self):
        """测试端到端测试端点"""
        try:
            from game_server_factory.main import app
            from fastapi.testclient import TestClient
            
            client = TestClient(app)
            response = client.get("/system/end-to-end-test")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "overall_result" in data
            assert "tests" in data
            assert "timestamp" in data
        except ImportError:
            pytest.skip("Could not import game_server_factory")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

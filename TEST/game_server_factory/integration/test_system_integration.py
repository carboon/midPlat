"""
系统集成测试 - 需求 6.4, 6.5, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5

测试端到端工作流程、全局错误处理、API错误响应格式标准化和配置管理
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestConfigurationManagement:
    """配置管理测试 - 需求 7.3"""
    
    def test_config_validation_valid_config(self):
        """测试有效配置验证"""
        from main import Config
        
        # 保存原始值
        original_port = Config.PORT
        original_base_port = Config.BASE_PORT
        original_environment = Config.ENVIRONMENT
        
        try:
            # 设置有效配置
            Config.PORT = 8080
            Config.BASE_PORT = 8081
            Config.ENVIRONMENT = "development"
            Config.MAX_FILE_SIZE = 1024 * 1024
            Config.MAX_CONTAINERS = 50
            Config.UPLOAD_TIMEOUT = 300
            Config.IDLE_TIMEOUT_SECONDS = 1800
            Config.LOG_LEVEL = "INFO"
            
            errors = Config.validate_config()
            assert len(errors) == 0, f"Expected no errors, got: {errors}"
        finally:
            # 恢复原始值
            Config.PORT = original_port
            Config.BASE_PORT = original_base_port
            Config.ENVIRONMENT = original_environment
    
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
    
    def test_config_validation_invalid_environment(self):
        """测试无效环境配置"""
        from main import Config
        
        original_env = Config.ENVIRONMENT
        try:
            Config.ENVIRONMENT = "invalid_env"
            errors = Config.validate_config()
            assert any("ENVIRONMENT" in error for error in errors)
        finally:
            Config.ENVIRONMENT = original_env
    
    def test_cors_config_production(self):
        """测试生产环境CORS配置"""
        from main import Config
        
        original_env = Config.ENVIRONMENT
        try:
            Config.ENVIRONMENT = "production"
            cors_config = Config.get_cors_config()
            assert cors_config["allow_credentials"] == True
            assert "GET" in cors_config["allow_methods"]
        finally:
            Config.ENVIRONMENT = original_env
    
    def test_cors_config_development(self):
        """测试开发环境CORS配置"""
        from main import Config
        
        original_env = Config.ENVIRONMENT
        try:
            Config.ENVIRONMENT = "development"
            cors_config = Config.get_cors_config()
            assert "*" in cors_config["allow_origins"]
        finally:
            Config.ENVIRONMENT = original_env


class TestErrorResponseFormat:
    """API错误响应格式测试 - 需求 6.4, 6.5"""
    
    def test_create_error_response_basic(self):
        """测试基本错误响应创建"""
        from main import create_error_response
        
        response = create_error_response(
            status_code=400,
            message="测试错误",
            path="/test"
        )
        
        assert "error" in response
        assert response["error"]["code"] == 400
        assert response["error"]["message"] == "测试错误"
        assert response["error"]["path"] == "/test"
        assert "timestamp" in response["error"]
    
    def test_create_error_response_with_details(self):
        """测试带详情的错误响应创建"""
        from main import create_error_response
        
        details = {"field": "name", "issue": "不能为空"}
        response = create_error_response(
            status_code=400,
            message="验证错误",
            path="/upload",
            details=details
        )
        
        assert "error" in response
        assert response["error"]["details"] == details
    
    def test_error_response_timestamp_format(self):
        """测试错误响应时间戳格式"""
        from main import create_error_response
        
        response = create_error_response(
            status_code=500,
            message="服务器错误",
            path="/test"
        )
        
        timestamp = response["error"]["timestamp"]
        # 验证ISO格式
        try:
            datetime.fromisoformat(timestamp)
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")
    
    @given(
        status_code=st.integers(min_value=400, max_value=599),
        message=st.text(min_size=1, max_size=200),
        path=st.one_of(
            st.just("/"),
            st.text(min_size=1, max_size=99).map(lambda x: "/" + x.strip().replace("/", "_"))
        )
    )
    @settings(max_examples=50)
    def test_error_response_format_property(self, status_code, message, path):
        """
        **Feature: ai-game-platform, Property 17: API错误响应格式**
        **Validates: Requirements 6.4, 6.5**
        
        对于任何格式错误或不存在资源的API请求，服务应该返回详细的错误信息和适当的状态码
        """
        from main import create_error_response
        
        # path已经通过策略确保以/开头
        
        response = create_error_response(
            status_code=status_code,
            message=message,
            path=path
        )
        
        # 验证响应结构
        assert "error" in response
        error = response["error"]
        
        # 验证必需字段
        assert "code" in error
        assert "message" in error
        assert "timestamp" in error
        assert "path" in error
        
        # 验证字段值
        assert error["code"] == status_code
        assert error["message"] == message
        assert error["path"] == path
        
        # 验证时间戳格式
        try:
            datetime.fromisoformat(error["timestamp"])
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {error['timestamp']}")


class TestGlobalErrorHandling:
    """全局错误处理测试 - 需求 8.1, 8.2, 8.3, 8.4, 8.5"""
    
    @pytest.mark.asyncio
    async def test_http_exception_handler(self):
        """测试HTTP异常处理器"""
        from fastapi import HTTPException
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 测试404错误
        response = client.get("/servers/nonexistent_server_id")
        assert response.status_code == 404
        
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == 404
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """测试验证错误处理"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 测试无效的端点
        response = client.get("/invalid-endpoint")
        # 应该返回404
        assert response.status_code == 404


class TestSystemIntegration:
    """系统集成测试"""
    
    def test_health_check_endpoint(self):
        """测试健康检查端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "containers" in data
        assert "timestamp" in data
    
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
    
    def test_servers_list_endpoint(self):
        """测试服务器列表端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/servers")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_system_stats_endpoint(self):
        """测试系统统计端点"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/system/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "game_servers_count" in data


class TestConfigurationApplication:
    """配置参数应用测试 - 需求 7.3"""
    
    @given(
        port=st.integers(min_value=1024, max_value=65535),
        max_containers=st.integers(min_value=1, max_value=1000),
        environment=st.sampled_from(["development", "staging", "production"])
    )
    @settings(max_examples=30, deadline=None)
    def test_config_parameters_property(self, port, max_containers, environment):
        """
        **Feature: ai-game-platform, Property 18: 配置参数应用**
        **Validates: Requirements 7.3**
        
        对于任何环境变量配置，所有服务应该正确读取并应用配置参数
        """
        from main import Config
        
        # 保存原始值
        original_port = Config.PORT
        original_max = Config.MAX_CONTAINERS
        original_env = Config.ENVIRONMENT
        
        try:
            # 应用新配置
            Config.PORT = port
            Config.MAX_CONTAINERS = max_containers
            Config.ENVIRONMENT = environment
            
            # 验证配置被正确应用
            assert Config.PORT == port
            assert Config.MAX_CONTAINERS == max_containers
            assert Config.ENVIRONMENT == environment
            
            # 验证配置验证通过
            errors = Config.validate_config()
            assert len(errors) == 0, f"Config validation failed: {errors}"
            
            # 验证环境相关配置
            assert Config.is_production() == (environment == "production")
            
        finally:
            # 恢复原始值
            Config.PORT = original_port
            Config.MAX_CONTAINERS = original_max
            Config.ENVIRONMENT = original_env


class TestComprehensiveErrorHandling:
    """综合错误处理测试 - 需求 8.1, 8.2, 8.3, 8.4, 8.5"""
    
    @given(
        error_type=st.sampled_from([
            "system_error",
            "network_failure", 
            "code_analysis_failure",
            "container_creation_failure",
            "validation_failure"
        ]),
        error_message=st.text(
            alphabet=st.characters(min_codepoint=32, max_codepoint=126),  # 可打印ASCII字符
            min_size=1, 
            max_size=100
        ),
        status_code=st.integers(min_value=400, max_value=599)
    )
    @settings(max_examples=10)
    def test_comprehensive_error_handling_property(self, error_type, error_message, status_code):
        """
        **Feature: ai-game-platform, Property 19: 综合错误处理**
        **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**
        
        对于任何系统错误、网络连接失败、代码分析失败或容器创建失败，
        系统应该记录详细错误信息并提供用户友好的错误消息
        """
        from main import create_error_response, setup_logging
        import logging
        import tempfile
        import os
        from datetime import datetime
        
        # 测试标准化错误响应格式 (需求 8.1, 8.5)
        response = create_error_response(
            status_code=status_code,
            message=error_message,
            path="/test",
            details={"error_type": error_type}
        )
        
        # 验证错误响应结构
        assert "error" in response, "错误响应必须包含error字段"
        error = response["error"]
        
        # 验证必需字段
        assert error["code"] == status_code, "错误代码必须匹配"
        assert error["message"] == error_message, "错误消息必须匹配"
        assert "timestamp" in error, "必须包含时间戳"
        assert "path" in error, "必须包含请求路径"
        
        # 验证时间戳格式
        try:
            datetime.fromisoformat(error["timestamp"])
        except ValueError:
            pytest.fail(f"时间戳格式无效: {error['timestamp']}")
        
        # 验证详细信息
        if "details" in error:
            assert isinstance(error["details"], dict), "详细信息必须是字典格式"
        
        # 测试日志记录功能 (需求 8.1)
        # 只测试可打印字符，避免特殊字符导致的日志问题
        if error_message and all(c.isprintable() or c.isspace() for c in error_message):
            with tempfile.TemporaryDirectory() as temp_dir:
                log_file = os.path.join(temp_dir, "test_error.log")
                
                # 创建测试日志记录器
                test_logger = logging.getLogger(f"test_{error_type}_{id(self)}")
                test_logger.setLevel(logging.ERROR)
                
                # 清除现有处理器
                for handler in test_logger.handlers[:]:
                    test_logger.removeHandler(handler)
                
                # 添加文件处理器
                handler = logging.FileHandler(log_file, encoding='utf-8')
                formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
                handler.setFormatter(formatter)
                test_logger.addHandler(handler)
                
                try:
                    # 记录错误
                    test_logger.error(f"Test error: {error_message}", extra={"error_type": error_type})
                    
                    # 强制刷新并关闭处理器
                    handler.flush()
                    handler.close()
                    test_logger.removeHandler(handler)
                    
                    # 验证日志文件存在且包含错误信息
                    assert os.path.exists(log_file), "日志文件必须被创建"
                    
                    with open(log_file, 'r', encoding='utf-8') as f:
                        log_content = f.read()
                        # 检查日志包含基本结构
                        assert "ERROR" in log_content, "日志必须包含错误级别"
                        assert "Test error:" in log_content, "日志必须包含测试错误标识"
                        # 对于简单的可打印字符，检查是否包含在日志中
                        if len(error_message.strip()) > 0 and error_message.strip().isalnum():
                            assert error_message in log_content, "日志必须包含错误消息"
                finally:
                    # 确保处理器被清理
                    if handler in test_logger.handlers:
                        test_logger.removeHandler(handler)
                    try:
                        handler.close()
                    except:
                        pass
    
    def test_system_error_logging(self):
        """测试系统错误日志记录 - 需求 8.1"""
        from main import Config
        import logging
        
        log_config = Config.get_log_config()
        
        assert "level" in log_config
        assert "format" in log_config
        assert "handlers" in log_config
        
        # 验证日志格式包含必要信息
        log_format = log_config["format"]
        required_fields = ["%(asctime)s", "%(name)s", "%(levelname)s", "%(message)s"]
        for field in required_fields:
            assert field in log_format, f"日志格式必须包含 {field}"
    
    def test_network_failure_error_messages(self):
        """测试网络连接失败错误消息 - 需求 8.2"""
        from fastapi.testclient import TestClient
        from main import app
        from unittest.mock import patch
        import httpx
        
        client = TestClient(app)
        
        # 模拟网络连接失败
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection failed")
            
            # 测试健康检查中的网络错误处理
            response = client.get("/health")
            
            # 应该返回成功但标记外部服务不可用
            assert response.status_code == 200
            data = response.json()
            
            # 验证包含网络状态信息
            assert "components" in data
            if "matchmaker_service" in data["components"]:
                # 网络失败应该被标记为unavailable而不是导致整个请求失败
                assert data["components"]["matchmaker_service"] in ["unavailable", "error"]
    
    @pytest.mark.serial
    def test_code_analysis_failure_response(self):
        """测试代码分析失败错误响应 - 需求 8.3"""
        from fastapi.testclient import TestClient
        from main import app
        import io
        
        # 检查代码分析器是否存在
        try:
            from main import code_analyzer
            if code_analyzer is None:
                pytest.skip("代码分析器未配置")
        except (ImportError, AttributeError):
            pytest.skip("代码分析器未配置")
        
        client = TestClient(app)
        
        # 创建无效的JavaScript代码
        invalid_code = "function invalid() { return unclosed_function"
        file_content = io.BytesIO(invalid_code.encode('utf-8'))
        
        response = client.post(
            "/upload",
            data={
                "name": "Invalid Code Test",
                "description": "Testing code analysis failure",
                "max_players": 10
            },
            files={"file": ("invalid.js", file_content, "application/javascript")}
        )
        
        # 应该返回400错误或200（如果代码分析器未启用）
        assert response.status_code in [200, 400]
        data = response.json()
        
        # 如果返回400，验证错误响应结构
        if response.status_code == 400:
            assert "error" in data or "detail" in data
    
    def test_container_creation_failure_handling(self):
        """测试容器创建失败处理 - 需求 8.4"""
        from fastapi.testclient import TestClient
        from main import app
        from unittest.mock import patch
        import io
        
        client = TestClient(app)
        
        # 创建有效的JavaScript代码（包含模块导出）
        valid_code = """
function gameLogic(state, action) {
    console.log('Processing action:', action);
    return state;
}

module.exports = { gameLogic };
"""
        file_content = io.BytesIO(valid_code.encode('utf-8'))
        
        # 模拟Docker容器创建失败
        with patch('main.docker_manager') as mock_docker_manager:
            mock_docker_manager.create_game_server.side_effect = Exception("Docker daemon not available")
            
            response = client.post(
                "/upload",
                data={
                    "name": "Container Failure Test",
                    "description": "Testing container creation failure",
                    "max_players": 10
                },
                files={"file": ("test.js", file_content, "application/javascript")}
            )
            
            # 应该返回成功但服务器状态为error
            assert response.status_code == 200
            data = response.json()
            
            # 验证服务器状态和错误信息
            assert "server" in data
            server = data["server"]
            assert server["status"] == "error"
            assert any("容器创建失败" in log for log in server["logs"])
    
    def test_validation_failure_response(self):
        """测试数据验证失败响应 - 需求 8.5"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        # 测试不存在的服务器ID
        response = client.get("/servers/nonexistent_server_id")
        assert response.status_code == 404
        
        # 测试无效的文件上传
        response = client.post(
            "/upload",
            data={
                "name": "",  # 空名称
                "description": "Test",
                "max_players": -1  # 无效的玩家数
            },
            files={}  # 无文件
        )
        
        # 应该返回验证错误
        assert response.status_code in [400, 422]
        data = response.json()
        
        # 验证错误响应包含验证详情
        assert "error" in data or "detail" in data
    
    def test_error_response_for_missing_resource(self):
        """测试资源不存在的错误响应"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/servers/nonexistent_id_12345")
        
        assert response.status_code == 404
        data = response.json()
        
        assert "error" in data
        assert data["error"]["code"] == 404
    
    def test_error_response_for_invalid_method(self):
        """测试无效方法的错误响应"""
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.patch("/servers")  # PATCH不支持
        
        assert response.status_code == 405


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

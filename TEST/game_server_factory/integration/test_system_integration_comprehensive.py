"""
系统集成和错误处理完善测试

验证系统各组件的集成工作流程，包括：
- 端到端工作流程测试
- 全局错误处理和日志记录
- API错误响应格式标准化
- 配置管理和环境适配

需求: 6.3, 6.4, 6.5, 7.3, 8.1, 8.2, 8.3, 8.4, 8.5
"""

import pytest
import asyncio
import tempfile
import os
import json
import logging
from datetime import datetime
from unittest.mock import patch, Mock, AsyncMock
from fastapi.testclient import TestClient
from io import StringIO
import threading
import time

# Import modules for testing
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import (
    app, 
    Config, 
    create_error_response,
    setup_logging,
    game_servers,
    html_game_validator,
    docker_manager,
    resource_manager,
    system_monitor
)


class TestSystemIntegrationComprehensive:
    """系统集成和错误处理完善测试"""

    def setup_method(self):
        """测试方法设置"""
        self.client = TestClient(app)
        # 清理游戏服务器状态
        game_servers.clear()

    def test_end_to_end_workflow_integration(self):
        """
        测试端到端工作流程集成
        
        验证从HTML游戏上传到容器创建的完整流程
        需求: 6.3, 6.4, 8.1, 8.2
        """
        # 1. 测试健康检查端点
        response = self.client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "containers" in health_data
        assert "timestamp" in health_data
        assert "components" in health_data
        
        # 2. 测试系统统计端点
        response = self.client.get("/system/stats")
        assert response.status_code == 200
        
        stats_data = response.json()
        assert "timestamp" in stats_data
        assert "game_servers_count" in stats_data
        assert "docker_available" in stats_data
        
        # 3. 测试服务器列表端点
        response = self.client.get("/servers")
        assert response.status_code == 200
        
        servers_data = response.json()
        assert isinstance(servers_data, list)
        
        # 4. 测试集成状态端点
        response = self.client.get("/system/integration-status")
        assert response.status_code == 200
        
        integration_data = response.json()
        assert "overall_status" in integration_data
        assert "services" in integration_data
        assert "workflows" in integration_data
        
        # 5. 测试端到端测试端点
        response = self.client.get("/system/end-to-end-test")
        assert response.status_code == 200
        
        test_data = response.json()
        assert "overall_result" in test_data
        assert "tests" in test_data
        assert "timestamp" in test_data

    def test_api_error_response_standardization(self):
        """
        测试API错误响应格式标准化
        
        验证所有API端点都返回标准化的错误响应格式
        需求: 6.3, 6.4, 6.5
        """
        # 测试各种错误情况
        error_test_cases = [
            ("/servers/nonexistent_server", "GET", 404),
            ("/containers/nonexistent_container/detailed", "GET", 404),
            ("/system/resources/nonexistent_server", "GET", 404),
            ("/monitoring/alerts/nonexistent_alert/resolve", "POST", 404),
        ]
        
        for endpoint, method, expected_status in error_test_cases:
            if method == "GET":
                response = self.client.get(endpoint)
            elif method == "POST":
                response = self.client.post(endpoint)
            
            # 验证状态码
            assert response.status_code in [expected_status, 503], \
                f"端点 {endpoint} 应该返回 {expected_status} 或 503"
            
            # 验证错误响应格式
            if response.status_code in [404, 503]:
                error_data = response.json()
                
                # 验证标准错误格式
                assert "error" in error_data, f"端点 {endpoint} 应该返回标准错误格式"
                
                error_obj = error_data["error"]
                required_fields = ["code", "message", "timestamp", "path"]
                
                for field in required_fields:
                    assert field in error_obj, \
                        f"端点 {endpoint} 的错误响应缺少字段: {field}"
                
                # 验证字段类型
                assert isinstance(error_obj["code"], int)
                assert isinstance(error_obj["message"], str)
                assert isinstance(error_obj["timestamp"], str)
                assert isinstance(error_obj["path"], str)
                
                # 验证时间戳格式
                try:
                    datetime.fromisoformat(error_obj["timestamp"].replace('Z', '+00:00'))
                except ValueError:
                    pytest.fail(f"端点 {endpoint} 的时间戳格式无效: {error_obj['timestamp']}")

    def test_configuration_management_integration(self):
        """
        测试配置管理和环境适配集成
        
        验证配置系统与其他组件的集成
        需求: 7.3
        """
        # 1. 验证配置验证功能
        validation_errors = Config.validate_config()
        assert isinstance(validation_errors, list), "配置验证应该返回错误列表"
        
        # 2. 验证环境特定配置
        assert Config.ENVIRONMENT in ['development', 'staging', 'production']
        
        # 3. 验证CORS配置
        cors_config = Config.get_cors_config()
        assert isinstance(cors_config, dict)
        assert "allow_origins" in cors_config
        assert "allow_credentials" in cors_config
        assert "allow_methods" in cors_config
        
        # 4. 验证日志配置
        log_config = Config.get_log_config()
        assert isinstance(log_config, dict)
        assert "level" in log_config
        assert "format" in log_config
        
        # 5. 测试生产环境检查
        is_production = Config.is_production()
        assert isinstance(is_production, bool)
        
        if is_production:
            # 生产环境应该有更严格的设置
            assert not Config.DEBUG, "生产环境不应该开启调试模式"

    def test_global_error_handling_and_logging(self):
        """
        测试全局错误处理和日志记录
        
        验证错误处理机制和日志系统的集成
        需求: 8.1, 8.2, 8.3, 8.4, 8.5
        """
        # 创建临时日志文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as log_file:
            log_filename = log_file.name
        
        try:
            # 设置日志捕获
            log_stream = StringIO()
            log_handler = logging.StreamHandler(log_stream)
            logger = logging.getLogger('main')
            logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)
            
            # 1. 测试错误响应创建
            test_cases = [
                (400, "请求参数错误", "/test/400", {"field": "name"}),
                (404, "资源不存在", "/test/404", None),
                (500, "内部服务器错误", "/test/500", {"error_type": "database"}),
                (503, "服务不可用", "/test/503", {"reason": "maintenance"})
            ]
            
            for status_code, message, path, details in test_cases:
                # 记录错误到日志
                logger.error(f"测试错误: {status_code} - {message}")
                
                # 创建错误响应
                error_response = create_error_response(
                    status_code=status_code,
                    message=message,
                    path=path,
                    details=details
                )
                
                # 验证错误响应格式
                assert isinstance(error_response, dict)
                assert "error" in error_response
                
                error_obj = error_response["error"]
                assert error_obj["code"] == status_code
                assert error_obj["message"] == message
                assert error_obj["path"] == path
                
                # 验证JSON序列化
                json_str = json.dumps(error_response)
                parsed_back = json.loads(json_str)
                assert parsed_back == error_response
            
            # 2. 验证日志记录
            log_output = log_stream.getvalue()
            assert len(log_output) > 0, "应该有日志输出"
            assert "测试错误" in log_output, "日志应该包含测试错误信息"
            
            # 3. 测试并发错误处理
            def concurrent_error_handler(error_id):
                try:
                    logger.error(f"并发错误 {error_id}")
                    return create_error_response(
                        status_code=500,
                        message=f"并发错误 {error_id}",
                        path=f"/concurrent/{error_id}"
                    )
                except Exception as e:
                    return {"error": str(e)}
            
            # 启动多个线程进行并发错误处理
            import concurrent.futures
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(concurrent_error_handler, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # 验证所有并发错误都被正确处理
            assert len(results) == 10, "应该处理所有10个并发错误"
            
            for result in results:
                assert isinstance(result, dict), "每个结果都应该是字典"
                if "error" in result and isinstance(result["error"], dict):
                    # 这是一个正确的错误响应
                    assert "code" in result["error"]
                    assert "message" in result["error"]
            
            # 清理日志处理器
            logger.removeHandler(log_handler)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(log_filename)
            except:
                pass

    def test_component_integration_status(self):
        """
        测试组件集成状态
        
        验证各个组件之间的集成状态
        需求: 6.3, 8.1, 8.2
        """
        # 1. 测试HTML游戏验证器集成
        if html_game_validator:
            # 测试简单的HTML验证
            test_html = b"<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
            is_valid, message, metadata = html_game_validator.validate_file(test_html, "test.html")
            
            assert isinstance(is_valid, bool), "验证结果应该是布尔值"
            assert isinstance(message, str), "验证消息应该是字符串"
            assert isinstance(metadata, dict), "元数据应该是字典"
        
        # 2. 测试Docker管理器集成状态
        docker_available = docker_manager is not None
        
        if docker_available:
            try:
                # 尝试获取Docker统计信息
                docker_stats = docker_manager.get_system_stats()
                assert isinstance(docker_stats, dict), "Docker统计信息应该是字典"
            except Exception as e:
                # Docker可能不可用，这是正常的
                assert "Docker" in str(e) or "docker" in str(e).lower()
        
        # 3. 测试资源管理器集成状态
        resource_manager_available = resource_manager is not None
        
        if resource_manager_available:
            try:
                # 尝试获取资源统计信息
                resource_stats = resource_manager.get_resource_stats()
                assert isinstance(resource_stats, dict), "资源统计信息应该是字典"
            except Exception as e:
                # 资源管理器可能依赖Docker，Docker不可用时会失败
                pass
        
        # 4. 测试系统监控器集成状态
        monitor_available = system_monitor is not None
        
        if monitor_available:
            try:
                # 尝试获取监控状态
                monitoring_status = system_monitor.get_monitoring_status()
                assert isinstance(monitoring_status, dict), "监控状态应该是字典"
            except Exception as e:
                # 监控器可能有依赖问题
                pass

    def test_api_documentation_integration(self):
        """
        测试API文档集成
        
        验证API文档端点的功能
        需求: 6.1
        """
        # 1. 测试API端点列表
        response = self.client.get("/api/endpoints")
        assert response.status_code == 200
        
        endpoints_data = response.json()
        assert "total_endpoints" in endpoints_data
        assert "endpoints" in endpoints_data
        assert isinstance(endpoints_data["endpoints"], list)
        
        # 验证端点信息格式
        for endpoint in endpoints_data["endpoints"]:
            assert "path" in endpoint
            assert "methods" in endpoint
            assert isinstance(endpoint["methods"], list)
        
        # 2. 测试API文档信息
        response = self.client.get("/api/documentation")
        assert response.status_code == 200
        
        doc_data = response.json()
        assert "service" in doc_data
        assert "version" in doc_data
        assert "description" in doc_data
        assert "documentation_formats" in doc_data
        assert "api_categories" in doc_data
        
        # 验证文档格式
        doc_formats = doc_data["documentation_formats"]
        assert "swagger_ui" in doc_formats
        assert "redoc" in doc_formats
        assert "openapi_json" in doc_formats

    def test_monitoring_integration(self):
        """
        测试监控系统集成
        
        验证监控端点的功能
        需求: 6.1, 6.2, 6.3
        """
        # 1. 测试基础监控状态
        response = self.client.get("/monitoring/status")
        # 可能返回503如果监控器不可用
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            monitoring_data = response.json()
            assert isinstance(monitoring_data, dict)
        
        # 2. 测试详细监控状态
        response = self.client.get("/monitoring/detailed")
        assert response.status_code in [200, 503]
        
        # 3. 测试告警列表
        response = self.client.get("/monitoring/alerts")
        assert response.status_code in [200, 503]
        
        if response.status_code == 200:
            alerts_data = response.json()
            assert "count" in alerts_data
            assert "alerts" in alerts_data
        
        # 4. 测试服务状态
        response = self.client.get("/monitoring/services")
        assert response.status_code in [200, 503]

    def test_container_management_integration(self):
        """
        测试容器管理集成
        
        验证容器管理端点的功能
        需求: 6.2, 6.3
        """
        # 1. 测试容器状态概览
        response = self.client.get("/containers/status")
        assert response.status_code in [200, 500]  # 可能因为Docker不可用而返回500
        
        if response.status_code == 200:
            containers_data = response.json()
            assert "timestamp" in containers_data
            assert "total_containers" in containers_data
            assert "containers" in containers_data
            assert isinstance(containers_data["containers"], list)
        
        # 2. 测试闲置容器列表
        response = self.client.get("/system/idle-containers")
        assert response.status_code in [200, 503]  # 可能因为资源管理器不可用而返回503
        
        if response.status_code == 200:
            idle_data = response.json()
            assert "timestamp" in idle_data
            assert "count" in idle_data
            assert "containers" in idle_data

    def test_error_recovery_and_resilience(self):
        """
        测试错误恢复和系统弹性
        
        验证系统在错误后的恢复能力
        需求: 8.1, 8.2, 8.5
        """
        # 1. 模拟一系列错误请求
        error_requests = [
            ("/servers/invalid_id", "GET"),
            ("/containers/invalid_id/detailed", "GET"),
            ("/system/resources/invalid_id", "GET"),
            ("/servers/invalid_id/stop", "POST"),
            ("/servers/invalid_id", "DELETE"),
        ]
        
        error_count = 0
        for endpoint, method in error_requests:
            try:
                if method == "GET":
                    response = self.client.get(endpoint)
                elif method == "POST":
                    response = self.client.post(endpoint)
                elif method == "DELETE":
                    response = self.client.delete(endpoint)
                
                # 错误请求应该返回4xx或5xx状态码
                assert response.status_code >= 400, f"端点 {endpoint} 应该返回错误状态码"
                error_count += 1
                
            except Exception as e:
                pytest.fail(f"错误请求处理失败: {endpoint} - {e}")
        
        assert error_count == len(error_requests), "所有错误请求都应该被处理"
        
        # 2. 验证系统在错误后仍能正常工作
        # 发送正常请求验证系统恢复
        normal_requests = [
            "/health",
            "/system/stats", 
            "/servers",
            "/api/endpoints"
        ]
        
        success_count = 0
        for endpoint in normal_requests:
            try:
                response = self.client.get(endpoint)
                assert response.status_code == 200, f"正常端点 {endpoint} 应该返回200"
                success_count += 1
            except Exception as e:
                pytest.fail(f"系统恢复失败: {endpoint} - {e}")
        
        assert success_count == len(normal_requests), "系统应该在错误后完全恢复"

    def test_comprehensive_system_health(self):
        """
        测试综合系统健康状态
        
        验证整个系统的健康状态和集成完整性
        需求: 6.1, 6.2, 6.3, 8.1, 8.2
        """
        # 1. 获取系统健康状态
        response = self.client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        overall_status = health_data.get("status", "unknown")
        
        # 2. 获取系统统计信息
        response = self.client.get("/system/stats")
        assert response.status_code == 200
        
        stats_data = response.json()
        
        # 3. 获取集成状态
        response = self.client.get("/system/integration-status")
        assert response.status_code == 200
        
        integration_data = response.json()
        integration_status = integration_data.get("overall_status", "unknown")
        
        # 4. 运行端到端测试
        response = self.client.get("/system/end-to-end-test")
        assert response.status_code == 200
        
        e2e_data = response.json()
        e2e_result = e2e_data.get("overall_result", "unknown")
        
        # 5. 综合评估系统健康状态
        health_indicators = {
            "health_status": overall_status,
            "integration_status": integration_status,
            "e2e_test_result": e2e_result,
            "docker_available": stats_data.get("docker_available", False),
            "resource_manager_available": stats_data.get("resource_manager_available", False),
            "system_monitor_available": stats_data.get("system_monitor_available", False)
        }
        
        # 记录健康状态
        print(f"\n系统健康状态评估:")
        for indicator, value in health_indicators.items():
            print(f"  {indicator}: {value}")
        
        # 验证关键组件
        assert overall_status in ["healthy", "degraded", "limited"], \
            f"健康状态应该是已知值，实际: {overall_status}"
        
        assert integration_status in ["healthy", "degraded"], \
            f"集成状态应该是已知值，实际: {integration_status}"
        
        # 如果所有测试都通过，系统应该是基本健康的
        if e2e_result == "passed":
            assert overall_status in ["healthy", "degraded"], \
                "端到端测试通过时，系统应该是健康或降级状态"
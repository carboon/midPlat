"""
综合健康检查和监控功能测试 - 需求 6.1, 6.2, 6.3
验证所有服务的健康检查端点、容器状态查询、API文档生成和服务状态监控功能
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

# 导入被测试的模块
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, system_monitor, docker_manager, resource_manager
from monitoring import SystemMonitor, MonitoringConfig, AlertType, AlertSeverity


class TestHealthMonitoringComprehensive:
    """综合健康检查和监控功能测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.client = TestClient(app)
    
    def test_health_check_endpoint_comprehensive(self):
        """
        测试健康检查端点的综合功能
        验证需求 6.2: 调用健康检查接口时所有服务应返回服务状态和基本统计信息
        """
        response = self.client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        # 验证必需的字段存在
        required_fields = ["status", "containers", "timestamp", "components", "configuration"]
        for field in required_fields:
            assert field in health_data, f"健康检查响应缺少必需字段: {field}"
        
        # 验证状态值有效
        valid_statuses = ["healthy", "degraded", "limited", "unhealthy"]
        assert health_data["status"] in valid_statuses, f"无效的健康状态: {health_data['status']}"
        
        # 验证组件状态
        assert "components" in health_data
        components = health_data["components"]
        
        # 验证各组件状态格式
        for component_name, component_status in components.items():
            assert isinstance(component_name, str), "组件名称应为字符串"
            assert isinstance(component_status, str), "组件状态应为字符串"
        
        # 验证配置信息
        assert "configuration" in health_data
        config = health_data["configuration"]
        assert "environment" in config
        assert "max_containers" in config
        assert "debug_mode" in config
        
        # 验证时间戳格式
        timestamp = health_data["timestamp"]
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))  # 验证ISO格式
    
    def test_container_status_query_detailed(self):
        """
        测试容器状态查询和详细信息返回
        验证需求 6.3: 查询容器状态时应返回详细的容器运行信息和资源使用情况
        """
        response = self.client.get("/containers/status")
        
        assert response.status_code == 200
        container_data = response.json()
        
        # 验证响应结构
        required_fields = ["timestamp", "total_containers", "containers"]
        for field in required_fields:
            assert field in container_data, f"容器状态响应缺少必需字段: {field}"
        
        # 验证容器列表结构
        containers = container_data["containers"]
        assert isinstance(containers, list), "容器列表应为数组"
        
        # 如果有容器，验证容器信息结构
        for container in containers:
            container_required_fields = [
                "container_id", "container_name", "status", 
                "created", "stats"
            ]
            for field in container_required_fields:
                assert field in container, f"容器信息缺少必需字段: {field}"
            
            # 验证统计信息存在
            assert "stats" in container
            stats = container["stats"]
            assert isinstance(stats, dict), "容器统计信息应为对象"
    
    def test_api_documentation_auto_generation(self):
        """
        测试API文档自动生成功能
        验证需求 6.1: 访问API文档端点时应提供Swagger UI和ReDoc格式的API文档
        """
        # 测试Swagger UI
        swagger_response = self.client.get("/docs")
        assert swagger_response.status_code == 200
        assert "text/html" in swagger_response.headers.get("content-type", "")
        
        # 测试ReDoc
        redoc_response = self.client.get("/redoc")
        assert redoc_response.status_code == 200
        assert "text/html" in redoc_response.headers.get("content-type", "")
        
        # 测试OpenAPI JSON规范
        openapi_response = self.client.get("/openapi.json")
        assert openapi_response.status_code == 200
        assert "application/json" in openapi_response.headers.get("content-type", "")
        
        openapi_data = openapi_response.json()
        
        # 验证OpenAPI规范结构
        required_openapi_fields = ["openapi", "info", "paths"]
        for field in required_openapi_fields:
            assert field in openapi_data, f"OpenAPI规范缺少必需字段: {field}"
        
        # 验证API信息
        info = openapi_data["info"]
        assert "title" in info
        assert "version" in info
        assert "description" in info
        
        # 验证路径定义
        paths = openapi_data["paths"]
        assert isinstance(paths, dict), "API路径应为对象"
        
        # 验证关键端点存在
        key_endpoints = ["/health", "/servers", "/upload", "/monitoring/status"]
        for endpoint in key_endpoints:
            assert any(endpoint in path for path in paths.keys()), f"关键端点缺失: {endpoint}"
    
    def test_service_status_monitoring(self):
        """
        测试服务状态监控功能
        验证监控状态端点返回正确的监控信息
        """
        response = self.client.get("/monitoring/status")
        
        if response.status_code == 503:
            # 系统监控器不可用是可接受的（在测试环境中）
            pytest.skip("系统监控器在测试环境中不可用")
        
        assert response.status_code == 200
        monitoring_data = response.json()
        
        # 验证监控状态结构
        required_fields = [
            "timestamp", "monitoring_active", "active_alerts_count",
            "services_monitored", "services_healthy", "services_degraded", "services_down"
        ]
        for field in required_fields:
            assert field in monitoring_data, f"监控状态响应缺少必需字段: {field}"
        
        # 验证数值字段类型
        numeric_fields = [
            "active_alerts_count", "services_monitored", 
            "services_healthy", "services_degraded", "services_down"
        ]
        for field in numeric_fields:
            assert isinstance(monitoring_data[field], int), f"字段 {field} 应为整数"
            assert monitoring_data[field] >= 0, f"字段 {field} 应为非负数"
        
        # 验证布尔字段
        assert isinstance(monitoring_data["monitoring_active"], bool), "monitoring_active应为布尔值"
    
    def test_detailed_monitoring_status(self):
        """
        测试详细监控状态端点
        """
        response = self.client.get("/monitoring/detailed")
        
        if response.status_code == 503:
            pytest.skip("系统监控器在测试环境中不可用")
        
        assert response.status_code == 200
        detailed_data = response.json()
        
        # 验证详细监控数据结构
        expected_sections = ["monitoring_status", "active_alerts", "service_statuses", "alert_history"]
        for section in expected_sections:
            assert section in detailed_data, f"详细监控数据缺少部分: {section}"
    
    def test_alert_management_endpoints(self):
        """
        测试告警管理端点
        """
        # 测试活跃告警列表
        alerts_response = self.client.get("/monitoring/alerts")
        
        if alerts_response.status_code == 503:
            pytest.skip("系统监控器在测试环境中不可用")
        
        assert alerts_response.status_code == 200
        alerts_data = alerts_response.json()
        
        assert "count" in alerts_data
        assert "alerts" in alerts_data
        assert isinstance(alerts_data["alerts"], list)
        
        # 测试告警历史
        history_response = self.client.get("/monitoring/alerts/history?hours=24")
        
        if history_response.status_code == 503:
            pytest.skip("系统监控器在测试环境中不可用")
        
        assert history_response.status_code == 200
        history_data = history_response.json()
        
        assert "hours" in history_data
        assert "count" in history_data
        assert "alerts" in history_data
        assert history_data["hours"] == 24
    
    def test_system_stats_endpoint(self):
        """
        测试系统统计信息端点
        验证系统统计信息的完整性和准确性
        """
        response = self.client.get("/system/stats")
        
        assert response.status_code == 200
        stats_data = response.json()
        
        # 验证基本统计信息
        required_fields = [
            "timestamp", "game_servers_count", "docker_available",
            "resource_manager_available", "system_monitor_available"
        ]
        for field in required_fields:
            assert field in stats_data, f"系统统计信息缺少必需字段: {field}"
        
        # 验证布尔字段
        boolean_fields = ["docker_available", "resource_manager_available", "system_monitor_available"]
        for field in boolean_fields:
            assert isinstance(stats_data[field], bool), f"字段 {field} 应为布尔值"
        
        # 验证数值字段
        assert isinstance(stats_data["game_servers_count"], int)
        assert stats_data["game_servers_count"] >= 0
        
        # 验证服务器状态分布
        if "server_status_distribution" in stats_data:
            distribution = stats_data["server_status_distribution"]
            assert isinstance(distribution, dict)
            
            # 验证状态计数
            for status, count in distribution.items():
                assert isinstance(status, str)
                assert isinstance(count, int)
                assert count >= 0
    
    def test_integration_status_endpoint(self):
        """
        测试系统集成状态端点
        验证端到端工作流程检查
        """
        response = self.client.get("/system/integration-status")
        
        assert response.status_code == 200
        integration_data = response.json()
        
        # 验证集成状态结构
        required_fields = ["timestamp", "overall_status", "services", "workflows"]
        for field in required_fields:
            assert field in integration_data, f"集成状态响应缺少必需字段: {field}"
        
        # 验证整体状态
        valid_overall_statuses = ["healthy", "degraded"]
        assert integration_data["overall_status"] in valid_overall_statuses
        
        # 验证服务状态
        services = integration_data["services"]
        assert isinstance(services, dict)
        
        expected_services = ["game_server_factory", "matchmaker_service", "docker_environment"]
        for service in expected_services:
            assert service in services, f"缺少服务状态: {service}"
            assert "status" in services[service]
        
        # 验证工作流程状态
        workflows = integration_data["workflows"]
        assert isinstance(workflows, dict)
        
        expected_workflows = ["code_upload_to_container", "container_to_matchmaker", "resource_management"]
        for workflow in expected_workflows:
            assert workflow in workflows, f"缺少工作流程状态: {workflow}"
            assert "status" in workflows[workflow]
    
    def test_end_to_end_system_test(self):
        """
        测试端到端系统测试端点
        验证完整的系统测试功能
        """
        response = self.client.get("/system/end-to-end-test")
        
        assert response.status_code == 200
        test_data = response.json()
        
        # 验证测试结果结构
        required_fields = ["timestamp", "test_id", "overall_result", "tests"]
        for field in required_fields:
            assert field in test_data, f"端到端测试响应缺少必需字段: {field}"
        
        # 验证测试结果
        valid_results = ["passed", "failed"]
        assert test_data["overall_result"] in valid_results
        
        # 验证测试项目
        tests = test_data["tests"]
        assert isinstance(tests, dict)
        
        expected_test_categories = ["configuration", "service_dependencies", "api_endpoints", "error_handling"]
        for category in expected_test_categories:
            assert category in tests, f"缺少测试类别: {category}"
            assert "result" in tests[category]
            assert tests[category]["result"] in valid_results
    
    def test_api_endpoints_listing(self):
        """
        测试API端点列表功能
        验证API端点自动发现和文档生成
        """
        response = self.client.get("/api/endpoints")
        
        assert response.status_code == 200
        endpoints_data = response.json()
        
        # 验证端点列表结构
        required_fields = ["timestamp", "total_endpoints", "endpoints", "documentation"]
        for field in required_fields:
            assert field in endpoints_data, f"API端点列表缺少必需字段: {field}"
        
        # 验证端点数量
        assert isinstance(endpoints_data["total_endpoints"], int)
        assert endpoints_data["total_endpoints"] > 0
        
        # 验证端点列表
        endpoints = endpoints_data["endpoints"]
        assert isinstance(endpoints, list)
        assert len(endpoints) == endpoints_data["total_endpoints"]
        
        # 验证端点信息结构
        for endpoint in endpoints:
            required_endpoint_fields = ["path", "methods", "name", "description"]
            for field in required_endpoint_fields:
                assert field in endpoint, f"端点信息缺少必需字段: {field}"
        
        # 验证文档链接
        documentation = endpoints_data["documentation"]
        doc_links = ["swagger_ui", "redoc", "openapi_schema"]
        for link in doc_links:
            assert link in documentation
    
    def test_error_handling_standardization(self):
        """
        测试错误处理标准化
        验证需求 6.4, 6.5: API请求格式错误和不存在资源时的错误响应
        """
        # 测试404错误 - 不存在的服务器
        response = self.client.get("/servers/nonexistent_server")
        assert response.status_code == 404
        
        error_data = response.json()
        assert "error" in error_data
        
        error = error_data["error"]
        required_error_fields = ["code", "message", "timestamp", "path"]
        for field in required_error_fields:
            assert field in error, f"错误响应缺少必需字段: {field}"
        
        assert error["code"] == 404
        assert "服务器不存在" in error["message"]
        
        # 测试400错误 - 无效参数
        response = self.client.get("/monitoring/alerts/history?hours=-1")
        if response.status_code == 400:
            error_data = response.json()
            assert "error" in error_data
            error = error_data["error"]
            assert error["code"] == 400
    
    def test_monitoring_configuration_validation(self):
        """
        测试监控配置验证
        验证监控系统配置的正确性
        """
        # 测试配置端点
        response = self.client.get("/")
        assert response.status_code == 200
        
        root_data = response.json()
        
        # 验证监控端点配置
        if "monitoring_endpoints" in root_data:
            monitoring_endpoints = root_data["monitoring_endpoints"]
            expected_monitoring_endpoints = [
                "monitoring_status", "active_alerts", "service_statuses"
            ]
            for endpoint in expected_monitoring_endpoints:
                assert endpoint in monitoring_endpoints
    
    @pytest.mark.asyncio
    async def test_monitoring_system_initialization(self):
        """
        测试监控系统初始化
        验证监控系统能够正确初始化和配置
        """
        # 创建测试监控配置
        config = MonitoringConfig()
        config.external_services = {"test_service": "http://localhost:8000/health"}
        
        # 初始化监控系统
        monitor = SystemMonitor(config)
        
        # 验证监控系统配置
        assert monitor.config.health_check_interval > 0
        assert monitor.config.health_check_timeout > 0
        assert monitor.config.max_consecutive_failures > 0
        
        # 验证告警管理器
        assert monitor.alert_manager is not None
        assert monitor.service_monitor is not None
        
        # 测试监控状态获取
        status = monitor.get_monitoring_status()
        assert isinstance(status, dict)
        assert "timestamp" in status
        assert "monitoring_active" in status


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
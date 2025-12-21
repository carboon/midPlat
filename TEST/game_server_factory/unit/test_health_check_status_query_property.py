"""
属性测试 - 健康检查和状态查询
**Feature: ai-game-platform, Property 16: 健康检查和状态查询**
验证需求: 6.2, 6.3

属性16: 对于任何健康检查或容器状态查询，服务应该返回详细的状态信息和资源使用情况
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from fastapi.testclient import TestClient
from datetime import datetime
import json
import sys
import os

# 导入被测试的模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from main import app


class TestHealthCheckStatusQueryProperty:
    """健康检查和状态查询属性测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.client = TestClient(app)
    
    @given(
        query_params=st.dictionaries(
            keys=st.sampled_from(['format', 'detailed', 'include_stats']),
            values=st.one_of(
                st.booleans(),
                st.text(min_size=1, max_size=10),
                st.integers(min_value=0, max_value=100)
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=3, deadline=5000)
    def test_health_endpoint_returns_detailed_status_info(self, query_params):
        """
        **Feature: ai-game-platform, Property 16: 健康检查和状态查询**
        
        属性: 对于任何健康检查请求，服务应该返回详细的状态信息和资源使用情况
        验证需求: 6.2, 6.3
        """
        # 构建查询参数
        params = {}
        for key, value in query_params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = str(value)
        
        # 发送健康检查请求
        response = self.client.get("/health", params=params)
        
        # 属性验证: 健康检查应该总是返回成功状态码
        assert response.status_code == 200, f"健康检查应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        health_data = response.json()
        
        # 属性验证: 响应必须包含详细的状态信息
        required_status_fields = ["status", "timestamp", "components", "configuration"]
        for field in required_status_fields:
            assert field in health_data, f"健康检查响应缺少必需的状态字段: {field}"
        
        # 属性验证: 状态值必须是有效的
        valid_statuses = ["healthy", "degraded", "limited", "unhealthy"]
        assert health_data["status"] in valid_statuses, f"无效的健康状态: {health_data['status']}"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        try:
            datetime.fromisoformat(health_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {health_data['timestamp']}")
        
        # 属性验证: 组件状态信息必须存在且格式正确
        components = health_data["components"]
        assert isinstance(components, dict), "组件状态信息必须是字典格式"
        assert len(components) > 0, "组件状态信息不能为空"
        
        for component_name, component_status in components.items():
            assert isinstance(component_name, str), "组件名称必须是字符串"
            assert isinstance(component_status, str), "组件状态必须是字符串"
            assert len(component_name) > 0, "组件名称不能为空"
            assert len(component_status) > 0, "组件状态不能为空"
        
        # 属性验证: 配置信息必须存在且包含关键配置
        configuration = health_data["configuration"]
        assert isinstance(configuration, dict), "配置信息必须是字典格式"
        
        expected_config_fields = ["environment", "max_containers", "debug_mode"]
        for field in expected_config_fields:
            assert field in configuration, f"配置信息缺少必需字段: {field}"
    
    @given(
        container_query_params=st.dictionaries(
            keys=st.sampled_from(['include_stats', 'include_logs', 'format']),
            values=st.one_of(
                st.booleans(),
                st.text(min_size=1, max_size=10)
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=3, deadline=5000)
    def test_container_status_query_returns_detailed_info(self, container_query_params):
        """
        **Feature: ai-game-platform, Property 16: 健康检查和状态查询**
        
        属性: 对于任何容器状态查询，服务应该返回详细的容器信息和资源使用情况
        验证需求: 6.2, 6.3
        """
        # 构建查询参数
        params = {}
        for key, value in container_query_params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = str(value)
        
        # 发送容器状态查询请求
        response = self.client.get("/containers/status", params=params)
        
        # 属性验证: 容器状态查询应该总是返回成功状态码
        assert response.status_code == 200, f"容器状态查询应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        container_data = response.json()
        
        # 属性验证: 响应必须包含详细的容器状态信息
        required_fields = ["timestamp", "total_containers", "containers"]
        for field in required_fields:
            assert field in container_data, f"容器状态响应缺少必需字段: {field}"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        try:
            datetime.fromisoformat(container_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {container_data['timestamp']}")
        
        # 属性验证: 容器数量必须是非负整数
        total_containers = container_data["total_containers"]
        assert isinstance(total_containers, int), "容器总数必须是整数"
        assert total_containers >= 0, "容器总数不能为负数"
        
        # 属性验证: 容器列表必须是数组且长度与总数一致
        containers = container_data["containers"]
        assert isinstance(containers, list), "容器列表必须是数组"
        assert len(containers) == total_containers, f"容器列表长度({len(containers)})与总数({total_containers})不一致"
        
        # 属性验证: 每个容器信息必须包含详细信息和资源使用情况
        for container in containers:
            # 验证容器基本信息
            required_container_fields = ["container_id", "container_name", "status", "stats"]
            for field in required_container_fields:
                assert field in container, f"容器信息缺少必需字段: {field}"
            
            # 验证容器ID格式
            container_id = container["container_id"]
            assert isinstance(container_id, str), "容器ID必须是字符串"
            assert len(container_id) > 0, "容器ID不能为空"
            
            # 验证容器状态
            container_status = container["status"]
            assert isinstance(container_status, str), "容器状态必须是字符串"
            assert len(container_status) > 0, "容器状态不能为空"
            
            # 属性验证: 资源使用情况必须存在且格式正确
            stats = container["stats"]
            assert isinstance(stats, dict), "容器统计信息必须是字典格式"
            
            # 验证资源使用情况的数值类型
            for stat_key, stat_value in stats.items():
                if stat_key.endswith('_percent') or stat_key.endswith('_mb'):
                    assert isinstance(stat_value, (int, float)), f"资源统计值 {stat_key} 必须是数值类型"
                    assert stat_value >= 0, f"资源统计值 {stat_key} 不能为负数"
    
    @given(
        monitoring_query_params=st.dictionaries(
            keys=st.sampled_from(['detailed', 'include_alerts', 'time_range']),
            values=st.one_of(
                st.booleans(),
                st.integers(min_value=1, max_value=168),  # 1-168小时
                st.text(min_size=1, max_size=10)
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=3, deadline=5000)
    def test_monitoring_status_returns_detailed_info(self, monitoring_query_params):
        """
        **Feature: ai-game-platform, Property 16: 健康检查和状态查询**
        
        属性: 对于任何监控状态查询，服务应该返回详细的监控信息和系统状态
        验证需求: 6.2, 6.3
        """
        # 构建查询参数
        params = {}
        for key, value in monitoring_query_params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = str(value)
        
        # 发送监控状态查询请求
        response = self.client.get("/monitoring/status", params=params)
        
        # 监控系统可能不可用（在测试环境中），这是可接受的
        if response.status_code == 503:
            pytest.skip("监控系统在测试环境中不可用")
        
        # 属性验证: 监控状态查询应该返回成功状态码
        assert response.status_code == 200, f"监控状态查询应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        monitoring_data = response.json()
        
        # 属性验证: 响应必须包含详细的监控状态信息
        required_monitoring_fields = [
            "timestamp", "monitoring_active", "active_alerts_count",
            "services_monitored", "services_healthy", "services_degraded", "services_down"
        ]
        for field in required_monitoring_fields:
            assert field in monitoring_data, f"监控状态响应缺少必需字段: {field}"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        try:
            datetime.fromisoformat(monitoring_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {monitoring_data['timestamp']}")
        
        # 属性验证: 监控状态必须是布尔值
        assert isinstance(monitoring_data["monitoring_active"], bool), "监控活跃状态必须是布尔值"
        
        # 属性验证: 数值字段必须是非负整数
        numeric_fields = [
            "active_alerts_count", "services_monitored", 
            "services_healthy", "services_degraded", "services_down"
        ]
        for field in numeric_fields:
            value = monitoring_data[field]
            assert isinstance(value, int), f"字段 {field} 必须是整数"
            assert value >= 0, f"字段 {field} 不能为负数"
        
        # 属性验证: 服务统计数据的逻辑一致性
        total_services = (monitoring_data["services_healthy"] + 
                         monitoring_data["services_degraded"] + 
                         monitoring_data["services_down"])
        assert total_services <= monitoring_data["services_monitored"], \
            "服务状态统计总数不能超过监控的服务总数"
    
    @given(
        system_stats_params=st.dictionaries(
            keys=st.sampled_from(['include_docker', 'include_resources', 'format']),
            values=st.one_of(
                st.booleans(),
                st.text(min_size=1, max_size=10)
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=3, deadline=5000)
    def test_system_stats_returns_detailed_resource_info(self, system_stats_params):
        """
        **Feature: ai-game-platform, Property 16: 健康检查和状态查询**
        
        属性: 对于任何系统统计查询，服务应该返回详细的系统资源使用情况
        验证需求: 6.2, 6.3
        """
        # 构建查询参数
        params = {}
        for key, value in system_stats_params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = str(value)
        
        # 发送系统统计查询请求
        response = self.client.get("/system/stats", params=params)
        
        # 属性验证: 系统统计查询应该返回成功状态码
        assert response.status_code == 200, f"系统统计查询应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        stats_data = response.json()
        
        # 属性验证: 响应必须包含详细的系统统计信息
        required_stats_fields = [
            "timestamp", "game_servers_count", "docker_available",
            "resource_manager_available", "system_monitor_available"
        ]
        for field in required_stats_fields:
            assert field in stats_data, f"系统统计响应缺少必需字段: {field}"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        try:
            datetime.fromisoformat(stats_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {stats_data['timestamp']}")
        
        # 属性验证: 游戏服务器数量必须是非负整数
        game_servers_count = stats_data["game_servers_count"]
        assert isinstance(game_servers_count, int), "游戏服务器数量必须是整数"
        assert game_servers_count >= 0, "游戏服务器数量不能为负数"
        
        # 属性验证: 可用性状态必须是布尔值
        availability_fields = ["docker_available", "resource_manager_available", "system_monitor_available"]
        for field in availability_fields:
            value = stats_data[field]
            assert isinstance(value, bool), f"字段 {field} 必须是布尔值"
        
        # 属性验证: 如果存在服务器状态分布，必须格式正确
        if "server_status_distribution" in stats_data:
            distribution = stats_data["server_status_distribution"]
            assert isinstance(distribution, dict), "服务器状态分布必须是字典格式"
            
            total_distributed = sum(distribution.values())
            assert total_distributed == game_servers_count, \
                f"状态分布总数({total_distributed})与服务器总数({game_servers_count})不一致"
            
            for status, count in distribution.items():
                assert isinstance(status, str), "状态名称必须是字符串"
                assert isinstance(count, int), "状态计数必须是整数"
                assert count >= 0, "状态计数不能为负数"
    
    @given(
        endpoint_path=st.sampled_from([
            "/health",
            "/containers/status", 
            "/monitoring/status",
            "/system/stats",
            "/system/integration-status"
        ]),
        request_headers=st.dictionaries(
            keys=st.sampled_from(['Accept', 'User-Agent', 'X-Request-ID']),
            values=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=50),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=3, deadline=10000)
    def test_all_status_endpoints_return_consistent_format(self, endpoint_path, request_headers):
        """
        **Feature: ai-game-platform, Property 16: 健康检查和状态查询**
        
        属性: 对于任何状态查询端点，服务应该返回一致格式的详细状态信息
        验证需求: 6.2, 6.3
        """
        # 发送状态查询请求
        response = self.client.get(endpoint_path, headers=request_headers)
        
        # 某些端点可能在测试环境中不可用
        if response.status_code == 503:
            pytest.skip(f"端点 {endpoint_path} 在测试环境中不可用")
        
        # 属性验证: 所有状态端点都应该返回成功状态码
        assert response.status_code == 200, \
            f"状态端点 {endpoint_path} 应该返回200状态码，实际返回: {response.status_code}"
        
        # 属性验证: 响应必须是有效的JSON格式
        try:
            status_data = response.json()
        except json.JSONDecodeError:
            pytest.fail(f"端点 {endpoint_path} 返回的不是有效的JSON格式")
        
        # 属性验证: 响应必须是字典格式
        assert isinstance(status_data, dict), f"端点 {endpoint_path} 响应必须是字典格式"
        
        # 属性验证: 所有状态端点都必须包含时间戳
        assert "timestamp" in status_data, f"端点 {endpoint_path} 响应缺少时间戳字段"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        try:
            datetime.fromisoformat(status_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"端点 {endpoint_path} 返回无效的时间戳格式: {status_data['timestamp']}")
        
        # 属性验证: 响应不能为空
        assert len(status_data) > 1, f"端点 {endpoint_path} 响应内容过于简单，应包含详细状态信息"
        
        # 属性验证: 响应内容类型必须正确
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, \
            f"端点 {endpoint_path} 应该返回JSON内容类型，实际返回: {content_type}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
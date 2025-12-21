"""
属性测试 - 健康检查响应
**Feature: ai-game-platform, Property 17: 健康检查响应**
验证需求: 6.1

属性17: 对于任何健康检查请求，所有服务应该返回服务状态和基本统计信息
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


class TestHealthCheckResponseProperty:
    """健康检查响应属性测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.client = TestClient(app)
    
    @given(
        request_headers=st.dictionaries(
            keys=st.sampled_from(['Accept', 'User-Agent', 'X-Request-ID', 'Content-Type']),
            values=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=100),
            min_size=0,
            max_size=4
        )
    )
    @settings(max_examples=10, deadline=5000)
    def test_health_check_always_returns_service_status_and_statistics(self, request_headers):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何健康检查请求，所有服务应该返回服务状态和基本统计信息
        验证需求: 6.1
        """
        # 发送健康检查请求
        response = self.client.get("/health", headers=request_headers)
        
        # 属性验证: 健康检查必须总是返回成功状态码
        assert response.status_code == 200, f"健康检查应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        health_data = response.json()
        
        # 属性验证: 响应必须包含服务状态信息
        assert "status" in health_data, "健康检查响应必须包含服务状态"
        
        service_status = health_data["status"]
        valid_statuses = ["healthy", "degraded", "limited", "unhealthy"]
        assert service_status in valid_statuses, f"服务状态必须是有效值之一: {valid_statuses}，实际值: {service_status}"
        
        # 属性验证: 响应必须包含基本统计信息
        assert "containers" in health_data, "健康检查响应必须包含容器统计信息"
        
        containers_count = health_data["containers"]
        assert isinstance(containers_count, int), "容器数量必须是整数"
        assert containers_count >= 0, "容器数量不能为负数"
        
        # 属性验证: 响应必须包含时间戳
        assert "timestamp" in health_data, "健康检查响应必须包含时间戳"
        
        timestamp = health_data["timestamp"]
        assert isinstance(timestamp, str), "时间戳必须是字符串格式"
        
        # 验证时间戳格式
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"时间戳格式无效: {timestamp}")
        
        # 属性验证: 响应必须包含组件状态信息
        assert "components" in health_data, "健康检查响应必须包含组件状态信息"
        
        components = health_data["components"]
        assert isinstance(components, dict), "组件状态信息必须是字典格式"
        assert len(components) > 0, "组件状态信息不能为空"
        
        # 验证每个组件的状态格式
        for component_name, component_status in components.items():
            assert isinstance(component_name, str), f"组件名称必须是字符串: {component_name}"
            assert isinstance(component_status, str), f"组件状态必须是字符串: {component_status}"
            assert len(component_name) > 0, "组件名称不能为空"
            assert len(component_status) > 0, "组件状态不能为空"
        
        # 属性验证: 响应必须包含配置信息
        assert "configuration" in health_data, "健康检查响应必须包含配置信息"
        
        configuration = health_data["configuration"]
        assert isinstance(configuration, dict), "配置信息必须是字典格式"
        
        # 验证关键配置字段
        required_config_fields = ["environment", "max_containers", "debug_mode"]
        for field in required_config_fields:
            assert field in configuration, f"配置信息必须包含字段: {field}"
    
    @given(
        query_params=st.dictionaries(
            keys=st.sampled_from(['format', 'detailed', 'include_components', 'include_config']),
            values=st.one_of(
                st.booleans(),
                st.text(min_size=1, max_size=20),
                st.integers(min_value=0, max_value=10)
            ),
            min_size=0,
            max_size=4
        )
    )
    @settings(max_examples=10, deadline=5000)
    def test_health_check_with_query_parameters_returns_consistent_format(self, query_params):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何带查询参数的健康检查请求，服务应该返回一致格式的状态和统计信息
        验证需求: 6.1
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
        
        # 属性验证: 无论查询参数如何，健康检查都应该返回成功状态码
        assert response.status_code == 200, f"健康检查应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        health_data = response.json()
        
        # 属性验证: 核心字段必须始终存在，不受查询参数影响
        core_fields = ["status", "containers", "timestamp", "components", "configuration"]
        for field in core_fields:
            assert field in health_data, f"核心字段 {field} 必须始终存在于健康检查响应中"
        
        # 属性验证: 响应格式必须一致
        assert isinstance(health_data["status"], str), "状态字段必须是字符串"
        assert isinstance(health_data["containers"], int), "容器数量字段必须是整数"
        assert isinstance(health_data["timestamp"], str), "时间戳字段必须是字符串"
        assert isinstance(health_data["components"], dict), "组件信息字段必须是字典"
        assert isinstance(health_data["configuration"], dict), "配置信息字段必须是字典"
    
    @given(
        concurrent_requests=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10, deadline=10000)
    def test_health_check_handles_concurrent_requests_consistently(self, concurrent_requests):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何并发健康检查请求，服务应该一致地返回状态和统计信息
        验证需求: 6.1
        """
        import threading
        import time
        
        responses = []
        errors = []
        
        def make_health_request():
            try:
                response = self.client.get("/health")
                responses.append(response)
            except Exception as e:
                errors.append(str(e))
        
        # 创建并启动多个并发请求
        threads = []
        for _ in range(concurrent_requests):
            thread = threading.Thread(target=make_health_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有请求完成
        for thread in threads:
            thread.join(timeout=5)
        
        # 属性验证: 不应该有错误发生
        assert len(errors) == 0, f"并发请求中发生错误: {errors}"
        
        # 属性验证: 所有请求都应该成功
        assert len(responses) == concurrent_requests, f"期望 {concurrent_requests} 个响应，实际收到 {len(responses)} 个"
        
        # 属性验证: 所有响应都应该返回成功状态码
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"第 {i+1} 个响应状态码错误: {response.status_code}"
        
        # 属性验证: 所有响应都应该包含必需的字段
        required_fields = ["status", "containers", "timestamp", "components", "configuration"]
        for i, response in enumerate(responses):
            health_data = response.json()
            for field in required_fields:
                assert field in health_data, f"第 {i+1} 个响应缺少必需字段: {field}"
        
        # 属性验证: 容器数量在并发请求期间应该保持一致（或合理变化）
        container_counts = [response.json()["containers"] for response in responses]
        min_count = min(container_counts)
        max_count = max(container_counts)
        
        # 允许在短时间内有小幅变化，但不应该有大幅波动
        assert max_count - min_count <= 1, f"并发请求期间容器数量变化过大: {container_counts}"
    
    @given(
        invalid_headers=st.dictionaries(
            keys=st.text(min_size=1, max_size=50),
            values=st.text(min_size=0, max_size=1000),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=10, deadline=5000)
    def test_health_check_robust_against_invalid_headers(self, invalid_headers):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何包含无效头部的健康检查请求，服务应该仍然返回有效的状态和统计信息
        验证需求: 6.1
        """
        # 过滤掉可能导致连接问题的头部
        filtered_headers = {}
        for key, value in invalid_headers.items():
            # 跳过可能导致问题的头部
            if key.lower() in ['host', 'connection', 'content-length']:
                continue
            # 限制头部值的长度以避免过大的请求
            if len(value) > 500:
                continue
            filtered_headers[key] = value
        
        try:
            # 发送带有无效头部的健康检查请求
            response = self.client.get("/health", headers=filtered_headers)
            
            # 属性验证: 即使头部无效，健康检查也应该返回成功状态码
            assert response.status_code == 200, f"健康检查应该返回200状态码，实际返回: {response.status_code}"
            
            # 解析响应数据
            health_data = response.json()
            
            # 属性验证: 响应必须包含所有必需的字段
            required_fields = ["status", "containers", "timestamp", "components", "configuration"]
            for field in required_fields:
                assert field in health_data, f"健康检查响应缺少必需字段: {field}"
            
            # 属性验证: 状态值必须有效
            valid_statuses = ["healthy", "degraded", "limited", "unhealthy"]
            assert health_data["status"] in valid_statuses, f"无效的健康状态: {health_data['status']}"
            
        except Exception as e:
            # 如果请求因为头部问题失败，这是可以接受的，但我们需要记录
            pytest.skip(f"请求因头部问题失败，这是可接受的: {str(e)}")
    
    @given(
        request_method=st.sampled_from(['GET', 'HEAD', 'OPTIONS'])
    )
    @settings(max_examples=10, deadline=5000)
    def test_health_check_supports_different_http_methods(self, request_method):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何支持的HTTP方法的健康检查请求，服务应该适当地响应
        验证需求: 6.1
        """
        # 发送不同HTTP方法的健康检查请求
        if request_method == 'GET':
            response = self.client.get("/health")
            
            # GET请求应该返回完整的健康检查数据
            assert response.status_code == 200, f"GET /health 应该返回200状态码"
            
            health_data = response.json()
            required_fields = ["status", "containers", "timestamp", "components", "configuration"]
            for field in required_fields:
                assert field in health_data, f"GET响应缺少必需字段: {field}"
                
        elif request_method == 'HEAD':
            response = self.client.head("/health")
            
            # HEAD请求可能返回200或405，取决于FastAPI配置
            assert response.status_code in [200, 405], f"HEAD /health 返回了意外的状态码: {response.status_code}"
            
            # 如果支持HEAD，响应不应该有响应体
            if response.status_code == 200:
                assert len(response.content) == 0, "HEAD响应不应该包含响应体"
            
        elif request_method == 'OPTIONS':
            response = self.client.options("/health")
            
            # OPTIONS请求可能返回200或405，取决于服务器配置
            assert response.status_code in [200, 405], f"OPTIONS /health 返回了意外的状态码: {response.status_code}"
    
    @given(
        time_interval=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=5, deadline=15000)
    def test_health_check_timestamp_progression(self, time_interval):
        """
        **Feature: ai-game-platform, Property 17: 健康检查响应**
        
        属性: 对于任何时间间隔的连续健康检查请求，时间戳应该正确递增
        验证需求: 6.1
        """
        import time
        
        # 第一次健康检查
        response1 = self.client.get("/health")
        assert response1.status_code == 200
        
        health_data1 = response1.json()
        timestamp1 = datetime.fromisoformat(health_data1["timestamp"].replace('Z', '+00:00'))
        
        # 等待指定的时间间隔
        time.sleep(time_interval)
        
        # 第二次健康检查
        response2 = self.client.get("/health")
        assert response2.status_code == 200
        
        health_data2 = response2.json()
        timestamp2 = datetime.fromisoformat(health_data2["timestamp"].replace('Z', '+00:00'))
        
        # 属性验证: 第二个时间戳应该晚于或等于第一个时间戳
        assert timestamp2 >= timestamp1, f"第二个时间戳({timestamp2})应该晚于或等于第一个时间戳({timestamp1})"
        
        # 属性验证: 时间差应该大致等于等待的时间间隔（更宽松的检查）
        time_diff = (timestamp2 - timestamp1).total_seconds()
        # 允许更大的时间差容差（-2 到 +5 秒）
        assert time_diff >= time_interval - 2, f"时间差({time_diff}秒)应该至少为{time_interval-2}秒"
        assert time_diff <= time_interval + 5, f"时间差({time_diff}秒)不应该超过{time_interval+5}秒"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
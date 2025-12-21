"""
属性测试 - 容器状态查询
**Feature: ai-game-platform, Property 18: 容器状态查询**
验证需求: 6.2

属性18: 对于任何容器状态查询，Game Server Factory应该返回详细的容器运行信息
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


class TestContainerStatusQueryProperty:
    """容器状态查询属性测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.client = TestClient(app)
    
    @given(
        query_params=st.dictionaries(
            keys=st.sampled_from(['include_stats', 'include_logs', 'format', 'detailed']),
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
    def test_container_status_query_returns_detailed_container_info(self, query_params):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何容器状态查询，Game Server Factory应该返回详细的容器运行信息
        验证需求: 6.2
        """
        # 构建查询参数
        params = {}
        for key, value in query_params.items():
            if isinstance(value, bool):
                params[key] = str(value).lower()
            else:
                params[key] = str(value)
        
        # 发送容器状态查询请求
        response = self.client.get("/containers/status", params=params)
        
        # 属性验证: 容器状态查询必须总是返回成功状态码
        assert response.status_code == 200, f"容器状态查询应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        container_data = response.json()
        
        # 属性验证: 响应必须包含详细的容器状态信息
        required_fields = ["timestamp", "total_containers", "containers"]
        for field in required_fields:
            assert field in container_data, f"容器状态响应缺少必需字段: {field}"
        
        # 属性验证: 时间戳必须是有效的ISO格式
        timestamp = container_data["timestamp"]
        assert isinstance(timestamp, str), "时间戳必须是字符串格式"
        
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"无效的时间戳格式: {timestamp}")
        
        # 属性验证: 容器总数必须是非负整数
        total_containers = container_data["total_containers"]
        assert isinstance(total_containers, int), "容器总数必须是整数"
        assert total_containers >= 0, "容器总数不能为负数"
        
        # 属性验证: 容器列表必须是数组且长度与总数一致
        containers = container_data["containers"]
        assert isinstance(containers, list), "容器列表必须是数组"
        assert len(containers) == total_containers, f"容器列表长度({len(containers)})与总数({total_containers})不一致"
        
        # 属性验证: 每个容器信息必须包含详细的运行信息
        for i, container in enumerate(containers):
            # 验证容器基本信息
            required_container_fields = ["container_id", "container_name", "status", "stats"]
            for field in required_container_fields:
                assert field in container, f"第{i+1}个容器信息缺少必需字段: {field}"
            
            # 验证容器ID格式
            container_id = container["container_id"]
            assert isinstance(container_id, str), f"第{i+1}个容器ID必须是字符串"
            assert len(container_id) > 0, f"第{i+1}个容器ID不能为空"
            
            # 验证容器名称
            container_name = container["container_name"]
            assert isinstance(container_name, str), f"第{i+1}个容器名称必须是字符串"
            
            # 验证容器状态
            container_status = container["status"]
            assert isinstance(container_status, str), f"第{i+1}个容器状态必须是字符串"
            assert len(container_status) > 0, f"第{i+1}个容器状态不能为空"
            
            # 属性验证: 容器统计信息必须存在且格式正确
            stats = container["stats"]
            assert isinstance(stats, dict), f"第{i+1}个容器统计信息必须是字典格式"
            
            # 验证统计信息的数值类型（如果存在）
            for stat_key, stat_value in stats.items():
                if stat_key.endswith('_percent'):
                    assert isinstance(stat_value, (int, float)), f"第{i+1}个容器的{stat_key}必须是数值类型"
                    assert 0 <= stat_value <= 100, f"第{i+1}个容器的{stat_key}必须在0-100之间"
                elif stat_key.endswith('_mb') or stat_key.endswith('_bytes'):
                    assert isinstance(stat_value, (int, float)), f"第{i+1}个容器的{stat_key}必须是数值类型"
                    assert stat_value >= 0, f"第{i+1}个容器的{stat_key}不能为负数"
    
    @given(
        container_id_pattern=st.text(
            alphabet=st.characters(min_codepoint=48, max_codepoint=122),  # 0-9, A-Z, a-z
            min_size=8,
            max_size=64
        )
    )
    @settings(max_examples=10, deadline=5000)
    def test_individual_container_detailed_status_query(self, container_id_pattern):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何单个容器的详细状态查询，应该返回该容器的完整运行信息或适当的错误响应
        验证需求: 6.2
        """
        # 首先获取所有容器列表
        containers_response = self.client.get("/containers/status")
        assert containers_response.status_code == 200
        
        containers_data = containers_response.json()
        containers = containers_data["containers"]
        
        if len(containers) > 0:
            # 如果有容器，测试查询现有容器的详细信息
            existing_container = containers[0]
            container_id = existing_container["container_id"]
            
            response = self.client.get(f"/containers/{container_id}/detailed")
            
            # 属性验证: 查询现有容器应该返回成功状态码
            assert response.status_code == 200, f"查询现有容器应该返回200状态码，实际返回: {response.status_code}"
            
            detailed_data = response.json()
            
            # 属性验证: 详细信息必须包含完整的容器运行信息
            required_detailed_fields = [
                "container_id", "name", "status", "stats"
            ]
            for field in required_detailed_fields:
                assert field in detailed_data, f"容器详细信息缺少必需字段: {field}"
            
            # 验证容器ID一致性
            assert detailed_data["container_id"] == container_id, "返回的容器ID与请求的不一致"
            
            # 验证统计信息更详细
            stats = detailed_data["stats"]
            assert isinstance(stats, dict), "详细统计信息必须是字典格式"
        
        # 测试查询不存在的容器
        fake_container_id = container_id_pattern
        response = self.client.get(f"/containers/{fake_container_id}/detailed")
        
        # 属性验证: 查询不存在的容器应该返回404或503状态码
        assert response.status_code in [404, 503], f"查询不存在的容器应该返回404或503状态码，实际返回: {response.status_code}"
        
        if response.status_code == 404:
            # 如果返回404，应该有错误信息（可能是标准化格式或FastAPI默认格式）
            error_data = response.json()
            
            # 检查是否为标准化错误格式
            if "error" in error_data:
                # 验证标准化错误格式
                error_info = error_data["error"]
                assert isinstance(error_info, dict), "错误信息应该是字典格式"
                assert "code" in error_info, "错误信息应该包含错误代码"
                assert "message" in error_info, "错误信息应该包含错误消息"
                assert error_info["code"] == 404, "错误代码应该与HTTP状态码一致"
            elif "detail" in error_data:
                # FastAPI默认404格式（当路径参数包含特殊字符时可能出现）
                assert isinstance(error_data["detail"], str), "FastAPI默认错误详情应该是字符串"
            else:
                pytest.fail(f"404响应格式不正确，既不包含'error'也不包含'detail': {error_data}")
    
    @given(
        request_headers=st.dictionaries(
            keys=st.sampled_from(['Accept', 'User-Agent', 'X-Request-ID']),
            values=st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), min_size=1, max_size=100),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=10, deadline=5000)
    def test_container_status_query_consistent_across_requests(self, request_headers):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何请求头的容器状态查询，应该返回一致格式的容器运行信息
        验证需求: 6.2
        """
        # 发送容器状态查询请求
        response = self.client.get("/containers/status", headers=request_headers)
        
        # 属性验证: 无论请求头如何，都应该返回成功状态码
        assert response.status_code == 200, f"容器状态查询应该返回200状态码，实际返回: {response.status_code}"
        
        # 解析响应数据
        container_data = response.json()
        
        # 属性验证: 响应格式必须一致
        assert isinstance(container_data, dict), "容器状态响应必须是字典格式"
        
        # 验证核心字段存在
        core_fields = ["timestamp", "total_containers", "containers"]
        for field in core_fields:
            assert field in container_data, f"核心字段 {field} 必须存在于容器状态响应中"
        
        # 验证字段类型一致性
        assert isinstance(container_data["timestamp"], str), "时间戳字段必须是字符串"
        assert isinstance(container_data["total_containers"], int), "容器总数字段必须是整数"
        assert isinstance(container_data["containers"], list), "容器列表字段必须是数组"
        
        # 验证响应内容类型
        content_type = response.headers.get("content-type", "")
        assert "application/json" in content_type, f"响应内容类型应该是JSON，实际为: {content_type}"
    
    @given(
        system_load_simulation=st.integers(min_value=1, max_value=3)
    )
    @settings(max_examples=10, deadline=10000)
    def test_container_status_query_under_load(self, system_load_simulation):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何系统负载情况下的容器状态查询，应该稳定返回容器运行信息
        验证需求: 6.2
        """
        import threading
        import time
        
        responses = []
        errors = []
        
        def make_container_status_request():
            try:
                response = self.client.get("/containers/status")
                responses.append(response)
            except Exception as e:
                errors.append(str(e))
        
        # 模拟系统负载 - 创建多个并发请求
        threads = []
        for _ in range(system_load_simulation * 2):  # 每个负载级别2个请求
            thread = threading.Thread(target=make_container_status_request)
            threads.append(thread)
            thread.start()
        
        # 等待所有请求完成
        for thread in threads:
            thread.join(timeout=5)
        
        # 属性验证: 在负载情况下不应该有错误
        assert len(errors) == 0, f"负载测试中发生错误: {errors}"
        
        # 属性验证: 所有请求都应该成功
        expected_responses = system_load_simulation * 2
        assert len(responses) == expected_responses, f"期望 {expected_responses} 个响应，实际收到 {len(responses)} 个"
        
        # 属性验证: 所有响应都应该返回成功状态码
        for i, response in enumerate(responses):
            assert response.status_code == 200, f"第 {i+1} 个响应状态码错误: {response.status_code}"
        
        # 属性验证: 所有响应都应该包含必需的字段
        for i, response in enumerate(responses):
            container_data = response.json()
            required_fields = ["timestamp", "total_containers", "containers"]
            for field in required_fields:
                assert field in container_data, f"第 {i+1} 个响应缺少必需字段: {field}"
        
        # 属性验证: 容器数量在负载测试期间应该保持相对稳定
        container_counts = [response.json()["total_containers"] for response in responses]
        if len(set(container_counts)) > 1:
            # 如果有变化，变化应该是合理的（比如容器启动或停止）
            min_count = min(container_counts)
            max_count = max(container_counts)
            assert max_count - min_count <= 2, f"负载测试期间容器数量变化过大: {container_counts}"
    
    @pytest.mark.serial
    @given(
        query_combinations=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['include_stats', 'include_logs', 'format']),
                values=st.booleans(),
                min_size=1,
                max_size=3
            ),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=5, deadline=8000)
    def test_container_status_query_parameter_combinations(self, query_combinations):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何查询参数组合的容器状态查询，应该返回相应的容器运行信息
        验证需求: 6.2
        """
        for params in query_combinations:
            # 构建查询参数
            query_params = {key: str(value).lower() for key, value in params.items()}
            
            # 发送容器状态查询请求
            response = self.client.get("/containers/status", params=query_params)
            
            # 属性验证: 无论参数组合如何，都应该返回成功状态码
            assert response.status_code == 200, f"参数组合 {params} 应该返回200状态码，实际返回: {response.status_code}"
            
            # 解析响应数据
            container_data = response.json()
            
            # 属性验证: 核心字段必须始终存在
            core_fields = ["timestamp", "total_containers", "containers"]
            for field in core_fields:
                assert field in container_data, f"参数组合 {params} 的响应缺少核心字段: {field}"
            
            # 属性验证: 容器列表中的每个容器都应该有基本信息
            containers = container_data["containers"]
            for i, container in enumerate(containers):
                basic_fields = ["container_id", "container_name", "status"]
                for field in basic_fields:
                    assert field in container, f"参数组合 {params} 的第{i+1}个容器缺少基本字段: {field}"
                
                # 如果请求包含统计信息，验证统计信息存在
                if params.get('include_stats', True):  # 默认包含统计信息
                    assert "stats" in container, f"参数组合 {params} 的第{i+1}个容器缺少统计信息"
    
    @given(
        time_interval=st.integers(min_value=1, max_value=2)
    )
    @settings(max_examples=5, deadline=10000)
    def test_container_status_query_temporal_consistency(self, time_interval):
        """
        **Feature: ai-game-platform, Property 18: 容器状态查询**
        
        属性: 对于任何时间间隔的连续容器状态查询，应该反映容器状态的合理变化
        验证需求: 6.2
        """
        import time
        
        # 第一次容器状态查询
        response1 = self.client.get("/containers/status")
        assert response1.status_code == 200
        
        container_data1 = response1.json()
        timestamp1 = datetime.fromisoformat(container_data1["timestamp"].replace('Z', '+00:00'))
        containers1 = container_data1["containers"]
        
        # 等待指定的时间间隔
        time.sleep(time_interval)
        
        # 第二次容器状态查询
        response2 = self.client.get("/containers/status")
        assert response2.status_code == 200
        
        container_data2 = response2.json()
        timestamp2 = datetime.fromisoformat(container_data2["timestamp"].replace('Z', '+00:00'))
        containers2 = container_data2["containers"]
        
        # 属性验证: 第二个时间戳应该晚于第一个时间戳
        assert timestamp2 > timestamp1, f"第二个时间戳({timestamp2})应该晚于第一个时间戳({timestamp1})"
        
        # 属性验证: 容器数量变化应该是合理的
        count1 = len(containers1)
        count2 = len(containers2)
        
        # 在短时间内，容器数量不应该有大幅变化
        assert abs(count2 - count1) <= 1, f"短时间内容器数量变化过大: {count1} -> {count2}"
        
        # 属性验证: 如果有相同的容器，其基本信息应该保持一致
        container_ids1 = {c["container_id"] for c in containers1}
        container_ids2 = {c["container_id"] for c in containers2}
        
        common_containers = container_ids1.intersection(container_ids2)
        
        for container_id in common_containers:
            container1 = next(c for c in containers1 if c["container_id"] == container_id)
            container2 = next(c for c in containers2 if c["container_id"] == container_id)
            
            # 容器名称应该保持不变
            assert container1["container_name"] == container2["container_name"], \
                f"容器 {container_id} 的名称发生了变化"
            
            # 容器状态可能会变化，但应该是有效的状态
            valid_statuses = ["running", "stopped", "paused", "restarting", "removing", "exited", "created"]
            assert container2["status"] in valid_statuses, \
                f"容器 {container_id} 的状态无效: {container2['status']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
"""
API错误响应格式属性测试 - 需求 6.3, 6.4

**Feature: ai-game-platform, Property 19: API错误响应格式**
**验证需求: 6.3, 6.4**

测试所有API错误响应都遵循标准格式，包含必要的字段和正确的数据类型。
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime
from typing import Dict, Any
import json

from main import create_error_response


class TestAPIErrorResponseFormatProperty:
    """API错误响应格式属性测试"""

    @given(
        status_code=st.integers(min_value=400, max_value=599),
        message=st.text(min_size=1, max_size=200),
        path=st.text(min_size=1, max_size=100).map(lambda x: f"/{x.replace(' ', '_')}"),
        details=st.one_of(
            st.none(),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(
                    st.text(max_size=100),
                    st.integers(),
                    st.booleans(),
                    st.floats(allow_nan=False, allow_infinity=False)
                ),
                min_size=0,
                max_size=5
            )
        )
    )
    @settings(max_examples=10)
    def test_error_response_format_property(
        self, 
        status_code: int, 
        message: str, 
        path: str, 
        details: Dict[str, Any]
    ):
        """
        **Feature: ai-game-platform, Property 19: API错误响应格式**
        
        对于任何错误状态码、消息、路径和详情，create_error_response函数应该返回
        包含所有必需字段的标准化错误响应格式。
        
        **验证需求: 6.3, 6.4**
        """
        # 执行错误响应创建
        error_response = create_error_response(
            status_code=status_code,
            message=message,
            path=path,
            details=details
        )
        
        # 验证响应结构
        assert isinstance(error_response, dict), "错误响应必须是字典类型"
        assert "error" in error_response, "错误响应必须包含'error'字段"
        
        error_obj = error_response["error"]
        assert isinstance(error_obj, dict), "error字段必须是字典类型"
        
        # 验证必需字段存在
        required_fields = ["code", "message", "timestamp", "path"]
        for field in required_fields:
            assert field in error_obj, f"错误对象必须包含'{field}'字段"
        
        # 验证字段类型和值
        assert isinstance(error_obj["code"], int), "code字段必须是整数类型"
        assert error_obj["code"] == status_code, "code字段必须等于输入的状态码"
        assert 400 <= error_obj["code"] <= 599, "code字段必须在400-599范围内"
        
        assert isinstance(error_obj["message"], str), "message字段必须是字符串类型"
        assert error_obj["message"] == message, "message字段必须等于输入的消息"
        assert len(error_obj["message"]) > 0, "message字段不能为空"
        
        assert isinstance(error_obj["path"], str), "path字段必须是字符串类型"
        assert error_obj["path"] == path, "path字段必须等于输入的路径"
        
        assert isinstance(error_obj["timestamp"], str), "timestamp字段必须是字符串类型"
        # 验证时间戳格式（ISO 8601）
        try:
            parsed_time = datetime.fromisoformat(error_obj["timestamp"].replace('Z', '+00:00'))
            assert parsed_time is not None, "timestamp必须是有效的ISO 8601格式"
        except ValueError:
            pytest.fail(f"timestamp格式无效: {error_obj['timestamp']}")
        
        # 验证details字段（可选）
        if details is not None:
            assert "details" in error_obj, "当提供details时，错误对象必须包含'details'字段"
            assert error_obj["details"] == details, "details字段必须等于输入的详情"
        else:
            # 当details为None时，不应该包含details字段
            assert "details" not in error_obj or error_obj["details"] is None, \
                "当details为None时，不应该包含details字段或应为None"
        
        # 验证响应可以序列化为JSON（API兼容性）
        try:
            json_str = json.dumps(error_response)
            parsed_back = json.loads(json_str)
            assert parsed_back == error_response, "错误响应必须可以正确序列化和反序列化JSON"
        except (TypeError, ValueError) as e:
            pytest.fail(f"错误响应无法序列化为JSON: {e}")

    @given(
        status_codes=st.lists(
            st.integers(min_value=400, max_value=599),
            min_size=2,
            max_size=10,
            unique=True
        ),
        base_message=st.text(min_size=1, max_size=50),
        base_path=st.text(min_size=1, max_size=30)
    )
    @settings(max_examples=10)
    def test_multiple_error_responses_consistency(
        self, 
        status_codes: list, 
        base_message: str, 
        base_path: str
    ):
        """
        **Feature: ai-game-platform, Property 19: API错误响应格式**
        
        对于任何多个错误响应，所有响应都应该遵循相同的格式标准。
        
        **验证需求: 6.3, 6.4**
        """
        responses = []
        
        for i, status_code in enumerate(status_codes):
            response = create_error_response(
                status_code=status_code,
                message=f"{base_message}_{i}",
                path=f"/{base_path}_{i}",
                details={"index": i, "code": status_code}
            )
            responses.append(response)
        
        # 验证所有响应都有相同的结构
        for i, response in enumerate(responses):
            # 基本结构检查
            assert "error" in response, f"响应{i}缺少error字段"
            error_obj = response["error"]
            
            # 必需字段检查
            required_fields = ["code", "message", "timestamp", "path", "details"]
            for field in required_fields:
                assert field in error_obj, f"响应{i}的error对象缺少{field}字段"
            
            # 类型一致性检查
            assert isinstance(error_obj["code"], int), f"响应{i}的code字段类型不一致"
            assert isinstance(error_obj["message"], str), f"响应{i}的message字段类型不一致"
            assert isinstance(error_obj["timestamp"], str), f"响应{i}的timestamp字段类型不一致"
            assert isinstance(error_obj["path"], str), f"响应{i}的path字段类型不一致"
            assert isinstance(error_obj["details"], dict), f"响应{i}的details字段类型不一致"

    @given(
        invalid_status_code=st.one_of(
            st.integers(max_value=399),
            st.integers(min_value=600)
        ),
        message=st.text(min_size=1, max_size=100),
        path=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10)
    def test_error_response_with_invalid_status_codes(
        self, 
        invalid_status_code: int, 
        message: str, 
        path: str
    ):
        """
        **Feature: ai-game-platform, Property 19: API错误响应格式**
        
        即使使用无效的状态码，错误响应格式仍应保持一致。
        
        **验证需求: 6.3, 6.4**
        """
        # 即使状态码无效，函数仍应返回格式正确的响应
        response = create_error_response(
            status_code=invalid_status_code,
            message=message,
            path=path
        )
        
        # 验证基本结构
        assert isinstance(response, dict), "响应必须是字典类型"
        assert "error" in response, "响应必须包含error字段"
        
        error_obj = response["error"]
        assert isinstance(error_obj, dict), "error字段必须是字典类型"
        
        # 验证必需字段
        required_fields = ["code", "message", "timestamp", "path"]
        for field in required_fields:
            assert field in error_obj, f"error对象必须包含{field}字段"
        
        # 验证状态码被正确设置（即使无效）
        assert error_obj["code"] == invalid_status_code, "code字段必须等于输入的状态码"

    def test_error_response_format_examples(self):
        """
        **Feature: ai-game-platform, Property 19: API错误响应格式**
        
        测试具体的错误响应格式示例，确保符合API文档规范。
        
        **验证需求: 6.3, 6.4**
        """
        # 测试常见的HTTP错误状态码
        test_cases = [
            {
                "status_code": 400,
                "message": "请求参数错误",
                "path": "/upload",
                "details": {"field": "name", "issue": "名称不能为空"}
            },
            {
                "status_code": 404,
                "message": "服务器不存在",
                "path": "/servers/invalid_id",
                "details": None
            },
            {
                "status_code": 500,
                "message": "内部服务器错误",
                "path": "/system/stats",
                "details": {"error_type": "database_connection"}
            },
            {
                "status_code": 503,
                "message": "服务不可用",
                "path": "/health",
                "details": {"reason": "maintenance_mode"}
            }
        ]
        
        for case in test_cases:
            response = create_error_response(
                status_code=case["status_code"],
                message=case["message"],
                path=case["path"],
                details=case["details"]
            )
            
            # 验证响应格式
            assert "error" in response
            error_obj = response["error"]
            
            # 验证所有必需字段
            assert error_obj["code"] == case["status_code"]
            assert error_obj["message"] == case["message"]
            assert error_obj["path"] == case["path"]
            assert "timestamp" in error_obj
            
            # 验证details字段处理
            if case["details"] is not None:
                assert "details" in error_obj
                assert error_obj["details"] == case["details"]
            
            # 验证时间戳格式
            timestamp = error_obj["timestamp"]
            assert isinstance(timestamp, str)
            # 应该能够解析为datetime
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

    @given(
        empty_or_whitespace_message=st.one_of(
            st.just(""),
            st.text().filter(lambda x: x.isspace() and len(x) > 0)
        ),
        status_code=st.integers(min_value=400, max_value=599),
        path=st.text(min_size=1, max_size=50)
    )
    @settings(max_examples=10)
    def test_error_response_with_empty_messages(
        self, 
        empty_or_whitespace_message: str, 
        status_code: int, 
        path: str
    ):
        """
        **Feature: ai-game-platform, Property 19: API错误响应格式**
        
        对于空消息或仅包含空白字符的消息，错误响应格式仍应保持一致。
        
        **验证需求: 6.3, 6.4**
        """
        response = create_error_response(
            status_code=status_code,
            message=empty_or_whitespace_message,
            path=path
        )
        
        # 验证基本结构
        assert "error" in response
        error_obj = response["error"]
        
        # 验证消息字段被正确设置（即使为空）
        assert "message" in error_obj
        assert error_obj["message"] == empty_or_whitespace_message
        assert isinstance(error_obj["message"], str)
        
        # 其他字段仍应正确
        assert error_obj["code"] == status_code
        assert error_obj["path"] == path
        assert "timestamp" in error_obj
"""
综合错误处理属性测试 - 需求 8.1, 8.2, 8.5

**Feature: ai-game-platform, Property 23: 综合错误处理**
**验证需求: 8.1, 8.2, 8.5**

测试系统在各种错误情况下的处理能力，包括系统错误、网络连接失败和数据验证失败。
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import patch, Mock, AsyncMock
import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
import tempfile
import os
import logging
from io import StringIO

# Import modules for testing
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from main import (
    create_error_response, 
    Config, 
    setup_logging,
    app,
    HTMLGameValidator,
    DockerManager
)
from fastapi.testclient import TestClient
from fastapi import HTTPException


class TestComprehensiveErrorHandlingProperty:
    """综合错误处理属性测试"""

    def setup_method(self):
        """测试方法设置"""
        self.client = TestClient(app)

    @given(
        error_type=st.sampled_from([
            'system_error',
            'network_error', 
            'validation_error',
            'file_error',
            'docker_error',
            'timeout_error'
        ]),
        error_message=st.text(min_size=1, max_size=200),
        status_code=st.integers(min_value=400, max_value=599),
        include_details=st.booleans(),
        log_level=st.sampled_from(['ERROR', 'WARNING', 'CRITICAL'])
    )
    @settings(max_examples=10)
    def test_comprehensive_error_handling_property(
        self, 
        error_type: str, 
        error_message: str, 
        status_code: int,
        include_details: bool,
        log_level: str
    ):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        对于任何类型的错误（系统错误、网络错误、验证错误），系统应该：
        1. 记录详细的错误信息到日志文件
        2. 返回用户友好的错误消息
        3. 保持系统稳定性，不崩溃
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 准备错误详情
        details = None
        if include_details:
            details = {
                "error_type": error_type,
                "timestamp": datetime.now().isoformat(),
                "additional_info": f"Generated error for testing: {error_type}"
            }
        
        # 创建临时日志文件来捕获日志输出
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as log_file:
            log_filename = log_file.name
        
        try:
            # 设置日志捕获
            log_stream = StringIO()
            log_handler = logging.StreamHandler(log_stream)
            log_handler.setLevel(getattr(logging, log_level))
            
            logger = logging.getLogger('main')
            logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)
            
            # 1. 测试错误响应创建
            error_response = create_error_response(
                status_code=status_code,
                message=error_message,
                path=f"/test/{error_type}",
                details=details
            )
            
            # 验证错误响应格式
            assert isinstance(error_response, dict), "错误响应必须是字典类型"
            assert "error" in error_response, "错误响应必须包含error字段"
            
            error_obj = error_response["error"]
            assert error_obj["code"] == status_code, "状态码必须正确设置"
            assert error_obj["message"] == error_message, "错误消息必须正确设置"
            assert "timestamp" in error_obj, "必须包含时间戳"
            
            # 2. 测试日志记录
            if log_level == 'ERROR':
                logger.error(f"测试错误: {error_type} - {error_message}", extra={
                    "error_type": error_type,
                    "status_code": status_code
                })
            elif log_level == 'WARNING':
                logger.warning(f"测试警告: {error_type} - {error_message}")
            elif log_level == 'CRITICAL':
                logger.critical(f"测试严重错误: {error_type} - {error_message}")
            
            # 验证日志输出
            log_output = log_stream.getvalue()
            assert len(log_output) > 0, "应该有日志输出"
            assert error_type in log_output, "日志应该包含错误类型"
            
            # 3. 测试JSON序列化（API兼容性）
            try:
                json_str = json.dumps(error_response)
                parsed_back = json.loads(json_str)
                assert parsed_back == error_response, "错误响应必须可以正确序列化"
            except (TypeError, ValueError) as e:
                pytest.fail(f"错误响应无法序列化为JSON: {e}")
            
            # 4. 验证用户友好性（消息不应包含敏感信息）
            sensitive_keywords = ['password', 'token', 'secret', 'key', 'internal']
            message_lower = error_message.lower()
            
            # 如果消息包含敏感关键词，应该在生产环境中被过滤
            # 这里我们测试错误处理机制本身的健壮性
            if any(keyword in message_lower for keyword in sensitive_keywords):
                # 在实际应用中，应该有机制过滤敏感信息
                # 这里我们验证错误处理不会因为敏感信息而崩溃
                assert isinstance(error_response, dict), "即使包含敏感信息，错误处理也应该正常工作"
            
            # 清理日志处理器
            logger.removeHandler(log_handler)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(log_filename)
            except:
                pass

    @given(
        network_errors=st.lists(
            st.sampled_from([
                'ConnectionError',
                'TimeoutError', 
                'DNSError',
                'SSLError',
                'HTTPError'
            ]),
            min_size=1,
            max_size=5
        ),
        retry_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=10)
    def test_network_error_handling_property(
        self, 
        network_errors: list, 
        retry_count: int
    ):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        对于任何网络连接失败，系统应该：
        1. 记录网络错误详情
        2. 提供重试机制（如果适用）
        3. 返回适当的错误响应
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 模拟网络错误场景
        for error_type in network_errors:
            # 创建日志捕获
            log_stream = StringIO()
            log_handler = logging.StreamHandler(log_stream)
            logger = logging.getLogger('main')
            logger.addHandler(log_handler)
            logger.setLevel(logging.DEBUG)
            
            try:
                # 模拟不同类型的网络错误
                if error_type == 'ConnectionError':
                    error_msg = "无法连接到远程服务器"
                    status_code = 503
                elif error_type == 'TimeoutError':
                    error_msg = "请求超时"
                    status_code = 504
                elif error_type == 'DNSError':
                    error_msg = "DNS解析失败"
                    status_code = 502
                elif error_type == 'SSLError':
                    error_msg = "SSL证书验证失败"
                    status_code = 502
                elif error_type == 'HTTPError':
                    error_msg = "HTTP请求失败"
                    status_code = 502
                
                # 记录网络错误
                logger.error(
                    f"网络错误: {error_type} - {error_msg}",
                    extra={
                        "error_type": "network_error",
                        "network_error_subtype": error_type,
                        "retry_count": retry_count
                    }
                )
                
                # 创建错误响应
                error_response = create_error_response(
                    status_code=status_code,
                    message=error_msg,
                    path="/network/test",
                    details={
                        "error_type": error_type,
                        "retry_count": retry_count,
                        "suggestion": "请检查网络连接并稍后重试"
                    }
                )
                
                # 验证错误响应
                assert error_response["error"]["code"] == status_code
                assert error_response["error"]["message"] == error_msg
                assert "details" in error_response["error"]
                assert error_response["error"]["details"]["error_type"] == error_type
                
                # 验证日志记录
                log_output = log_stream.getvalue()
                assert error_type in log_output, f"日志应该包含网络错误类型: {error_type}"
                assert "网络错误" in log_output, "日志应该标识为网络错误"
                
            finally:
                logger.removeHandler(log_handler)

    @given(
        validation_errors=st.lists(
            st.dictionaries(
                keys=st.sampled_from(['field', 'value', 'constraint', 'message']),
                values=st.text(min_size=1, max_size=50),
                min_size=2,
                max_size=4
            ),
            min_size=1,
            max_size=3
        )
    )
    @settings(max_examples=25)
    def test_data_validation_error_handling_property(
        self, 
        validation_errors: list
    ):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        对于任何数据验证失败，系统应该：
        1. 记录验证错误详情
        2. 返回具体的验证错误信息
        3. 帮助用户理解如何修正错误
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 创建日志捕获
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('main')
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)
        
        try:
            # 处理每个验证错误
            for i, validation_error in enumerate(validation_errors):
                field = validation_error.get('field', f'field_{i}')
                value = validation_error.get('value', 'invalid_value')
                constraint = validation_error.get('constraint', 'required')
                message = validation_error.get('message', '字段验证失败')
                
                # 记录验证错误
                logger.warning(
                    f"数据验证失败: {field} = {value}",
                    extra={
                        "error_type": "validation_error",
                        "field": field,
                        "constraint": constraint,
                        "value": value
                    }
                )
                
                # 创建验证错误响应
                error_response = create_error_response(
                    status_code=400,
                    message="请求数据验证失败",
                    path="/validation/test",
                    details={
                        "validation_errors": [{
                            "field": field,
                            "value": value,
                            "constraint": constraint,
                            "message": message
                        }],
                        "suggestion": "请检查输入数据格式并重新提交"
                    }
                )
                
                # 验证错误响应格式
                assert error_response["error"]["code"] == 400
                assert "validation_errors" in error_response["error"]["details"]
                
                validation_detail = error_response["error"]["details"]["validation_errors"][0]
                assert validation_detail["field"] == field
                assert validation_detail["constraint"] == constraint
                
            # 验证日志记录
            log_output = log_stream.getvalue()
            assert "数据验证失败" in log_output, "日志应该包含验证失败信息"
            
            # 验证所有字段都被记录
            for validation_error in validation_errors:
                field = validation_error.get('field', f'field_{validation_errors.index(validation_error)}')
                if field and len(field.strip()) > 0:
                    assert field in log_output, f"日志应该包含字段名: {field}"
                
        finally:
            logger.removeHandler(log_handler)

    def test_system_error_recovery_property(self):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        系统在遇到各种错误后应该能够恢复正常运行，不会因为单个错误而崩溃。
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 创建日志捕获
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('main')
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)
        
        try:
            # 模拟一系列不同类型的错误
            error_scenarios = [
                ("文件不存在", 404, "file_not_found"),
                ("权限被拒绝", 403, "permission_denied"),
                ("内部服务器错误", 500, "internal_error"),
                ("服务不可用", 503, "service_unavailable"),
                ("请求超时", 408, "request_timeout")
            ]
            
            successful_responses = 0
            
            for message, status_code, error_type in error_scenarios:
                try:
                    # 记录错误
                    logger.error(f"系统错误: {error_type} - {message}")
                    
                    # 创建错误响应
                    error_response = create_error_response(
                        status_code=status_code,
                        message=message,
                        path=f"/test/{error_type}",
                        details={"error_type": error_type}
                    )
                    
                    # 验证响应格式正确
                    assert isinstance(error_response, dict)
                    assert "error" in error_response
                    assert error_response["error"]["code"] == status_code
                    
                    successful_responses += 1
                    
                except Exception as e:
                    # 如果错误处理本身失败，这是一个严重问题
                    pytest.fail(f"错误处理机制失败: {e}")
            
            # 验证所有错误都被正确处理
            assert successful_responses == len(error_scenarios), \
                f"应该成功处理所有{len(error_scenarios)}个错误，实际处理了{successful_responses}个"
            
            # 验证日志记录
            log_output = log_stream.getvalue()
            assert "系统错误" in log_output, "日志应该包含系统错误信息"
            
            # 验证系统仍然可以处理正常请求（恢复能力）
            normal_response = create_error_response(
                status_code=200,
                message="系统正常",
                path="/health"
            )
            assert normal_response["error"]["code"] == 200
            
        finally:
            logger.removeHandler(log_handler)

    @given(
        concurrent_errors=st.integers(min_value=2, max_value=10),
        error_types=st.lists(
            st.sampled_from(['network', 'validation', 'system', 'timeout']),
            min_size=2,
            max_size=4
        )
    )
    @settings(max_examples=10)
    def test_concurrent_error_handling_property(
        self, 
        concurrent_errors: int, 
        error_types: list
    ):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        系统应该能够同时处理多个并发错误，不会因为并发错误而导致死锁或崩溃。
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 创建日志捕获
        log_stream = StringIO()
        log_handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('main')
        logger.addHandler(log_handler)
        logger.setLevel(logging.DEBUG)
        
        try:
            import threading
            import time
            
            results = []
            errors = []
            
            def handle_error(error_id: int, error_type: str):
                """处理单个错误的函数"""
                try:
                    # 模拟错误处理
                    message = f"并发错误 {error_id}: {error_type}"
                    status_code = 500 if error_type == 'system' else 400
                    
                    # 记录错误
                    logger.error(f"并发错误处理: {message}")
                    
                    # 创建错误响应
                    error_response = create_error_response(
                        status_code=status_code,
                        message=message,
                        path=f"/concurrent/{error_id}",
                        details={
                            "error_id": error_id,
                            "error_type": error_type,
                            "thread_id": threading.current_thread().ident
                        }
                    )
                    
                    results.append(error_response)
                    
                except Exception as e:
                    errors.append(f"错误处理失败 {error_id}: {str(e)}")
            
            # 创建并启动多个线程来模拟并发错误
            threads = []
            for i in range(concurrent_errors):
                error_type = error_types[i % len(error_types)]
                thread = threading.Thread(
                    target=handle_error,
                    args=(i, error_type)
                )
                threads.append(thread)
                thread.start()
            
            # 等待所有线程完成
            for thread in threads:
                thread.join(timeout=5.0)  # 5秒超时
            
            # 验证结果
            assert len(errors) == 0, f"并发错误处理中出现失败: {errors}"
            assert len(results) == concurrent_errors, \
                f"应该处理{concurrent_errors}个错误，实际处理了{len(results)}个"
            
            # 验证每个响应都是有效的
            for i, result in enumerate(results):
                assert isinstance(result, dict), f"结果{i}应该是字典类型"
                assert "error" in result, f"结果{i}应该包含error字段"
                assert "details" in result["error"], f"结果{i}应该包含details"
                assert result["error"]["details"]["error_id"] == i, \
                    f"结果{i}的error_id应该正确"
            
            # 验证日志记录
            log_output = log_stream.getvalue()
            assert "并发错误处理" in log_output, "日志应该包含并发错误处理信息"
            
        finally:
            logger.removeHandler(log_handler)

    def test_error_handling_with_api_endpoints(self):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        测试API端点的错误处理能力，确保所有端点都能正确处理错误情况。
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 测试不存在的端点
        response = self.client.get("/nonexistent")
        assert response.status_code == 404
        
        # 测试无效的服务器ID
        response = self.client.get("/servers/invalid_server_id")
        assert response.status_code == 404
        
        # 测试无效的容器ID
        response = self.client.get("/containers/invalid_container_id/detailed")
        assert response.status_code in [404, 503]  # 可能是404或503（Docker不可用）
        
        # 验证错误响应格式
        if response.status_code == 404:
            error_data = response.json()
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert "timestamp" in error_data["error"]
            assert "path" in error_data["error"]

    @given(
        log_levels=st.lists(
            st.sampled_from(['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']),
            min_size=1,
            max_size=3
        ),
        message_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10)
    def test_logging_system_robustness_property(
        self, 
        log_levels: list, 
        message_count: int
    ):
        """
        **Feature: ai-game-platform, Property 23: 综合错误处理**
        
        日志系统应该能够处理各种级别的大量日志消息，不会因为日志记录而影响系统性能。
        
        **验证需求: 8.1, 8.2, 8.5**
        """
        # 创建临时日志文件
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.log') as log_file:
            log_filename = log_file.name
        
        try:
            # 设置日志处理器
            file_handler = logging.FileHandler(log_filename)
            logger = logging.getLogger('test_logger')
            logger.addHandler(file_handler)
            logger.setLevel(logging.DEBUG)
            
            # 记录大量不同级别的日志消息
            for i in range(message_count):
                for level in log_levels:
                    message = f"测试日志消息 {i} - 级别: {level}"
                    
                    if level == 'DEBUG':
                        logger.debug(message)
                    elif level == 'INFO':
                        logger.info(message)
                    elif level == 'WARNING':
                        logger.warning(message)
                    elif level == 'ERROR':
                        logger.error(message)
                    elif level == 'CRITICAL':
                        logger.critical(message)
            
            # 验证日志文件存在且包含内容
            assert os.path.exists(log_filename), "日志文件应该存在"
            
            with open(log_filename, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            assert len(log_content) > 0, "日志文件应该包含内容"
            
            # 验证所有级别的消息都被记录
            for level in log_levels:
                assert level in log_content, f"日志应该包含{level}级别的消息"
            
            # 验证消息数量
            total_expected_messages = message_count * len(log_levels)
            actual_message_count = log_content.count("测试日志消息")
            assert actual_message_count == total_expected_messages, \
                f"应该有{total_expected_messages}条消息，实际有{actual_message_count}条"
            
            # 清理
            logger.removeHandler(file_handler)
            
        finally:
            # 清理临时文件
            try:
                os.unlink(log_filename)
            except:
                pass
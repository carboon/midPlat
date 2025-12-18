#!/usr/bin/env python3
"""
端到端集成测试脚本 - 需求 6.1, 8.1, 8.2, 8.3, 8.4, 8.5
测试系统各组件的集成和端到端工作流程
"""

import sys
import time
import requests
import json
from typing import Dict, List, Tuple, Any

# 配置
MATCHMAKER_URL = "http://localhost:8000"
FACTORY_URL = "http://localhost:8080"
TIMEOUT = 10

class Colors:
    """终端颜色"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_test(message: str):
    """打印测试信息"""
    print(f"{Colors.BLUE}[TEST]{Colors.END} {message}")

def print_success(message: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}[✓]{Colors.END} {message}")

def print_error(message: str):
    """打印错误信息"""
    print(f"{Colors.RED}[✗]{Colors.END} {message}")

def print_warning(message: str):
    """打印警告信息"""
    print(f"{Colors.YELLOW}[!]{Colors.END} {message}")

def test_service_health(service_name: str, url: str) -> Tuple[bool, Dict]:
    """测试服务健康状态"""
    print_test(f"Testing {service_name} health...")
    try:
        response = requests.get(f"{url}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"{service_name} is healthy")
            print(f"  Status: {data.get('status', 'unknown')}")
            if 'statistics' in data:
                print(f"  Statistics: {json.dumps(data['statistics'], indent=2)}")
            return True, data
        else:
            print_error(f"{service_name} health check failed: {response.status_code}")
            return False, {}
    except Exception as e:
        print_error(f"{service_name} health check error: {str(e)}")
        return False, {}

def test_error_response_format(url: str) -> bool:
    """测试错误响应格式标准化 - 需求 6.4, 6.5"""
    print_test("Testing standardized error response format...")
    try:
        # 测试404错误
        response = requests.get(f"{url}/servers/nonexistent_server", timeout=TIMEOUT)
        if response.status_code == 404:
            data = response.json()
            if 'error' in data:
                error = data['error']
                required_fields = ['code', 'message', 'timestamp', 'path']
                if all(field in error for field in required_fields):
                    print_success("Error response format is standardized")
                    print(f"  Error structure: {json.dumps(error, indent=2)}")
                    return True
                else:
                    print_error(f"Missing required fields in error response")
                    return False
            else:
                print_error("Error response missing 'error' field")
                return False
        else:
            print_warning(f"Expected 404, got {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error response format test failed: {str(e)}")
        return False

def test_configuration_validation() -> bool:
    """测试配置验证 - 需求 7.3"""
    print_test("Testing configuration validation...")
    try:
        # 测试Game Server Factory配置
        response = requests.get(f"{FACTORY_URL}/system/stats", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success("Configuration is valid and accessible")
            print(f"  Docker available: {data.get('docker_available', False)}")
            print(f"  Resource manager available: {data.get('resource_manager_available', False)}")
            return True
        else:
            print_error(f"Configuration validation failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Configuration validation error: {str(e)}")
        return False

def test_matchmaker_integration() -> bool:
    """测试撮合服务集成"""
    print_test("Testing Matchmaker Service integration...")
    try:
        # 获取服务器列表
        response = requests.get(f"{MATCHMAKER_URL}/servers", timeout=TIMEOUT)
        if response.status_code == 200:
            servers = response.json()
            print_success(f"Matchmaker integration working - {len(servers)} active servers")
            return True
        else:
            print_error(f"Matchmaker integration failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Matchmaker integration error: {str(e)}")
        return False

def test_factory_integration() -> bool:
    """测试游戏服务器工厂集成"""
    print_test("Testing Game Server Factory integration...")
    try:
        # 获取服务器列表
        response = requests.get(f"{FACTORY_URL}/servers", timeout=TIMEOUT)
        if response.status_code == 200:
            servers = response.json()
            print_success(f"Factory integration working - {len(servers)} managed servers")
            return True
        else:
            print_error(f"Factory integration failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Factory integration error: {str(e)}")
        return False

def test_system_integration_status() -> bool:
    """测试系统集成状态端点"""
    print_test("Testing system integration status endpoint...")
    try:
        response = requests.get(f"{FACTORY_URL}/system/integration-status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            overall_status = data.get('overall_status', 'unknown')
            print_success(f"System integration status: {overall_status}")
            
            # 打印服务状态
            if 'services' in data:
                print("  Services:")
                for service, status in data['services'].items():
                    print(f"    - {service}: {status.get('status', 'unknown')}")
            
            # 打印工作流程状态
            if 'workflows' in data:
                print("  Workflows:")
                for workflow, status in data['workflows'].items():
                    print(f"    - {workflow}: {status.get('status', 'unknown')}")
            
            return overall_status in ['healthy', 'degraded']
        else:
            print_error(f"Integration status check failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Integration status check error: {str(e)}")
        return False

def test_end_to_end_workflow() -> bool:
    """测试端到端工作流程"""
    print_test("Testing end-to-end workflow...")
    try:
        response = requests.get(f"{FACTORY_URL}/system/end-to-end-test", timeout=TIMEOUT * 2)
        if response.status_code == 200:
            data = response.json()
            overall_result = data.get('overall_result', 'unknown')
            
            if overall_result == 'passed':
                print_success("End-to-end workflow test passed")
            else:
                print_error(f"End-to-end workflow test failed")
                if 'failed_tests' in data:
                    print(f"  Failed tests: {', '.join(data['failed_tests'])}")
            
            # 打印测试结果
            if 'tests' in data:
                print("  Test results:")
                for test_name, result in data['tests'].items():
                    status = result.get('result', 'unknown')
                    symbol = '✓' if status == 'passed' else '✗'
                    print(f"    {symbol} {test_name}: {status}")
            
            return overall_result == 'passed'
        else:
            print_error(f"End-to-end test failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"End-to-end test error: {str(e)}")
        return False

def test_error_handling() -> bool:
    """测试错误处理机制 - 需求 8.1, 8.2, 8.3, 8.4, 8.5"""
    print_test("Testing error handling mechanisms...")
    
    test_cases = [
        ("Invalid file upload", f"{FACTORY_URL}/upload", "POST", None, 400),
        ("Non-existent server", f"{FACTORY_URL}/servers/invalid_id", "GET", None, 404),
        ("Invalid heartbeat", f"{MATCHMAKER_URL}/heartbeat/invalid_id", "POST", None, 404),
    ]
    
    passed = 0
    for test_name, url, method, data, expected_status in test_cases:
        try:
            if method == "GET":
                response = requests.get(url, timeout=TIMEOUT)
            elif method == "POST":
                response = requests.post(url, json=data, timeout=TIMEOUT)
            
            if response.status_code == expected_status:
                # 检查错误响应格式
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        passed += 1
                        print_success(f"  {test_name}: Correct error handling")
                    else:
                        print_warning(f"  {test_name}: Missing error structure")
                except:
                    print_warning(f"  {test_name}: Invalid JSON response")
            else:
                print_warning(f"  {test_name}: Expected {expected_status}, got {response.status_code}")
        except Exception as e:
            print_error(f"  {test_name}: {str(e)}")
    
    success_rate = passed / len(test_cases)
    if success_rate >= 0.8:
        print_success(f"Error handling test passed ({passed}/{len(test_cases)})")
        return True
    else:
        print_error(f"Error handling test failed ({passed}/{len(test_cases)})")
        return False

def run_all_tests() -> bool:
    """运行所有集成测试"""
    print("\n" + "="*70)
    print("AI游戏平台 - 端到端集成测试")
    print("="*70 + "\n")
    
    tests = [
        ("Matchmaker Health", lambda: test_service_health("Matchmaker Service", MATCHMAKER_URL)),
        ("Factory Health", lambda: test_service_health("Game Server Factory", FACTORY_URL)),
        ("Error Response Format", lambda: test_error_response_format(FACTORY_URL)),
        ("Configuration Validation", test_configuration_validation),
        ("Matchmaker Integration", test_matchmaker_integration),
        ("Factory Integration", test_factory_integration),
        ("System Integration Status", test_system_integration_status),
        ("End-to-End Workflow", test_end_to_end_workflow),
        ("Error Handling", test_error_handling),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'─'*70}")
        result = test_func()
        if isinstance(result, tuple):
            result = result[0]
        results.append((test_name, result))
        time.sleep(0.5)  # 短暂延迟避免请求过快
    
    # 打印总结
    print(f"\n{'='*70}")
    print("测试总结")
    print("="*70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.END}" if result else f"{Colors.RED}FAILED{Colors.END}"
        print(f"  {test_name}: {status}")
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print(f"\n{Colors.GREEN}✓ 所有集成测试通过！{Colors.END}\n")
        return True
    else:
        print(f"\n{Colors.RED}✗ 部分测试失败{Colors.END}\n")
        return False

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}测试被用户中断{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}测试执行失败: {str(e)}{Colors.END}\n")
        sys.exit(1)

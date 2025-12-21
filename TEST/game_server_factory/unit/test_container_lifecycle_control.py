"""
容器生命周期控制属性测试
**Feature: ai-game-platform, Property 6: 容器生命周期控制**
**验证需求: 2.2, 2.3**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch
from docker.errors import NotFound, APIError
import logging

# 导入被测试的模块
from docker_manager import DockerManager, ContainerInfo

logger = logging.getLogger(__name__)

# 测试数据生成策略
@st.composite
def container_lifecycle_data(draw):
    """生成容器生命周期测试数据"""
    server_id = draw(st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))))
    container_id = draw(st.text(min_size=10, max_size=64, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    timeout = draw(st.integers(min_value=1, max_value=30))
    
    return {
        'server_id': server_id,
        'container_id': container_id,
        'timeout': timeout
    }

@st.composite
def container_status_data(draw):
    """生成容器状态数据"""
    status = draw(st.sampled_from(['running', 'stopped', 'exited', 'paused', 'restarting']))
    container_name = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))))
    
    return {
        'status': status,
        'container_name': container_name
    }

class TestContainerLifecycleControl:
    """容器生命周期控制属性测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 创建模拟的Docker客户端
        self.mock_docker_client = Mock()
        self.mock_container = Mock()
        
        # 设置模拟返回值
        self.mock_container.id = "test_container_id_123"
        self.mock_container.short_id = "test_123"
        self.mock_container.name = "test-container"
        self.mock_container.status = "running"
        self.mock_container.attrs = {'Created': '2025-12-20T10:00:00Z'}
        
        # 模拟容器操作
        self.mock_container.stop.return_value = None
        self.mock_container.remove.return_value = None
        self.mock_container.reload.return_value = None
        
        # 模拟Docker客户端方法
        self.mock_docker_client.containers.get.return_value = self.mock_container
        self.mock_docker_client.containers.list.return_value = [self.mock_container]
        self.mock_docker_client.networks.get.return_value = Mock()
        self.mock_docker_client.ping.return_value = True
        
        # 模拟镜像操作
        self.mock_docker_client.images.remove.return_value = None
        
        # 重置调用计数
        self.mock_docker_client.reset_mock()
        self.mock_container.reset_mock()

    @given(lifecycle_data=container_lifecycle_data())
    @settings(max_examples=10, deadline=20000)
    def test_container_stop_operation_property(self, lifecycle_data):
        """
        属性测试：容器停止操作
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2**
        
        对于任何运行中的容器，系统应该能够安全地停止容器
        """
        assume(lifecycle_data['container_id'].strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            try:
                # 创建DockerManager实例
                docker_manager = DockerManager()
                
                # 测试容器停止操作
                result = docker_manager.stop_container(
                    container_id=lifecycle_data['container_id'],
                    timeout=lifecycle_data['timeout']
                )
                
                # 验证停止操作结果
                assert result is True, "容器停止操作应该返回True表示成功"
                
                # 验证Docker客户端调用
                assert self.mock_docker_client.containers.get.called, "应该调用containers.get获取容器"
                assert self.mock_container.stop.called, "应该调用容器的stop方法"
                
                # 验证停止调用的参数
                if self.mock_container.stop.call_args:
                    stop_call = self.mock_container.stop.call_args
                    if 'timeout' in stop_call.kwargs:
                        assert stop_call.kwargs['timeout'] == lifecycle_data['timeout'], f"超时参数应匹配: {stop_call.kwargs['timeout']} != {lifecycle_data['timeout']}"
                
                logger.info(f"容器停止测试成功: {lifecycle_data['container_id']}")
                
            except Exception as e:
                logger.error(f"容器停止测试失败: {str(e)}")
                logger.error(f"测试数据: {lifecycle_data}")
                raise

    @given(lifecycle_data=container_lifecycle_data())
    @settings(max_examples=10, deadline=15000)
    def test_container_remove_operation_property(self, lifecycle_data):
        """
        属性测试：容器删除操作
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.3**
        
        对于任何容器，系统应该能够安全地删除容器
        """
        assume(lifecycle_data['container_id'].strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            try:
                docker_manager = DockerManager()
                
                # 测试容器删除操作
                result = docker_manager.remove_container(
                    container_id=lifecycle_data['container_id'],
                    force=True
                )
                
                # 验证删除操作结果
                assert result is True, "容器删除操作应该返回True表示成功"
                
                # 验证Docker客户端调用
                assert self.mock_docker_client.containers.get.called, "应该调用containers.get获取容器"
                assert self.mock_container.remove.called, "应该调用容器的remove方法"
                
                # 验证删除调用的参数
                if self.mock_container.remove.call_args:
                    remove_call = self.mock_container.remove.call_args
                    if 'force' in remove_call.kwargs:
                        assert remove_call.kwargs['force'] is True, "应该使用force=True参数"
                
                logger.info(f"容器删除测试成功: {lifecycle_data['container_id']}")
                
            except Exception as e:
                logger.error(f"容器删除测试失败: {str(e)}")
                logger.error(f"测试数据: {lifecycle_data}")
                raise

    @given(lifecycle_data=container_lifecycle_data())
    @settings(max_examples=40, deadline=20000)
    def test_server_resource_cleanup_property(self, lifecycle_data):
        """
        属性测试：服务器资源清理
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2, 2.3**
        
        对于任何服务器ID，系统应该能够清理所有相关资源（容器和镜像）
        """
        assume(lifecycle_data['server_id'].strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            # 设置容器列表模拟（包含匹配的标签）
            mock_container_with_label = Mock()
            mock_container_with_label.status = 'running'
            mock_container_with_label.id = lifecycle_data['container_id']
            mock_container_with_label.stop.return_value = None
            mock_container_with_label.remove.return_value = None
            
            self.mock_docker_client.containers.list.return_value = [mock_container_with_label]
            
            try:
                docker_manager = DockerManager()
                
                # 测试服务器资源清理
                result = docker_manager.cleanup_server_resources(lifecycle_data['server_id'])
                
                # 验证清理操作结果
                assert result is True, "服务器资源清理应该返回True表示成功"
                
                # 验证Docker客户端调用
                assert self.mock_docker_client.containers.list.called, "应该调用containers.list查找相关容器"
                assert self.mock_docker_client.images.remove.called, "应该调用images.remove删除镜像"
                
                # 验证容器列表调用的过滤参数
                if self.mock_docker_client.containers.list.call_args:
                    list_call = self.mock_docker_client.containers.list.call_args
                    if 'filters' in list_call.kwargs:
                        filters = list_call.kwargs['filters']
                        expected_label = f"server_id={lifecycle_data['server_id']}"
                        assert 'label' in filters, "应该使用标签过滤器"
                        assert filters['label'] == expected_label, f"标签过滤器应匹配: {filters['label']} != {expected_label}"
                
                logger.info(f"服务器资源清理测试成功: {lifecycle_data['server_id']}")
                
            except Exception as e:
                logger.error(f"服务器资源清理测试失败: {str(e)}")
                logger.error(f"测试数据: {lifecycle_data}")
                raise

    @given(
        container_id=st.text(min_size=10, max_size=64, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        status_data=container_status_data()
    )
    @settings(max_examples=10, deadline=15000)
    def test_container_info_retrieval_property(self, container_id, status_data):
        """
        属性测试：容器信息获取
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2, 2.3**
        
        对于任何容器ID，系统应该能够获取容器的详细信息
        """
        assume(container_id.strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            # 设置容器状态
            self.mock_container.status = status_data['status']
            self.mock_container.name = status_data['container_name']
            
            try:
                docker_manager = DockerManager()
                
                # 测试容器信息获取
                container_info = docker_manager.get_container_info(container_id)
                
                # 验证容器信息
                assert container_info is not None, "应该返回容器信息对象"
                assert isinstance(container_info, ContainerInfo), "应该返回ContainerInfo实例"
                
                # 验证容器信息属性
                assert container_info.id == self.mock_container.id, "容器ID应匹配"
                assert container_info.status == status_data['status'], f"容器状态应匹配: {container_info.status} != {status_data['status']}"
                assert container_info.name == status_data['container_name'], f"容器名称应匹配: {container_info.name} != {status_data['container_name']}"
                
                # 验证Docker客户端调用
                assert self.mock_docker_client.containers.get.called, "应该调用containers.get获取容器"
                
                logger.info(f"容器信息获取测试成功: {container_id}")
                
            except Exception as e:
                logger.error(f"容器信息获取测试失败: {str(e)}")
                logger.error(f"测试数据: container_id={container_id}, status_data={status_data}")
                raise

    @given(container_id=st.text(min_size=10, max_size=64, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    @settings(max_examples=10, deadline=10000)
    def test_container_not_found_handling_property(self, container_id):
        """
        属性测试：容器不存在时的处理
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2, 2.3**
        
        对于不存在的容器ID，系统应该正确处理NotFound异常
        """
        assume(container_id.strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            # 设置容器不存在的情况
            self.mock_docker_client.containers.get.side_effect = NotFound("Container not found")
            
            try:
                docker_manager = DockerManager()
                
                # 测试获取不存在的容器信息
                container_info = docker_manager.get_container_info(container_id)
                assert container_info is None, "不存在的容器应该返回None"
                
                # 测试停止不存在的容器
                stop_result = docker_manager.stop_container(container_id)
                assert stop_result is False, "停止不存在的容器应该返回False"
                
                # 测试删除不存在的容器
                remove_result = docker_manager.remove_container(container_id)
                assert remove_result is False, "删除不存在的容器应该返回False"
                
                logger.info(f"容器不存在处理测试成功: {container_id}")
                
            except Exception as e:
                logger.error(f"容器不存在处理测试失败: {str(e)}")
                logger.error(f"测试数据: container_id={container_id}")
                raise

    def test_container_lifecycle_integration(self):
        """
        集成测试：完整的容器生命周期
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2, 2.3**
        """
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            docker_manager = DockerManager()
            test_container_id = "integration_test_container_123"
            
            # 1. 获取容器信息
            container_info = docker_manager.get_container_info(test_container_id)
            assert container_info is not None, "应该能够获取容器信息"
            
            # 2. 停止容器
            stop_result = docker_manager.stop_container(test_container_id, timeout=10)
            assert stop_result is True, "应该能够停止容器"
            
            # 3. 删除容器
            remove_result = docker_manager.remove_container(test_container_id, force=True)
            assert remove_result is True, "应该能够删除容器"
            
            # 验证调用顺序和参数
            assert self.mock_docker_client.containers.get.call_count >= 3, "应该多次调用containers.get"
            assert self.mock_container.stop.called, "应该调用容器停止方法"
            assert self.mock_container.remove.called, "应该调用容器删除方法"
            
            logger.info("容器生命周期集成测试成功")

    @given(
        server_ids=st.lists(
            st.text(min_size=5, max_size=30, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc'))),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=10, deadline=15000)
    def test_multiple_containers_cleanup_property(self, server_ids):
        """
        属性测试：多容器清理
        
        **Feature: ai-game-platform, Property 6: 容器生命周期控制**
        **验证需求: 2.2, 2.3**
        
        对于多个服务器ID，系统应该能够批量清理所有相关资源
        """
        with patch('docker.DockerClient') as mock_docker_class:
            # 为每次测试创建新的mock实例
            fresh_mock_docker_client = Mock()
            fresh_mock_docker_client.networks.get.return_value = Mock()
            fresh_mock_docker_client.ping.return_value = True
            
            # 为每个server_id创建模拟容器
            mock_containers = []
            for i, server_id in enumerate(server_ids):
                mock_container = Mock()
                mock_container.id = f"container_{i}_{server_id}"
                mock_container.status = 'running'
                mock_container.stop.return_value = None
                mock_container.remove.return_value = None
                mock_containers.append(mock_container)
            
            fresh_mock_docker_client.containers.list.return_value = mock_containers
            fresh_mock_docker_client.images.remove.return_value = None
            
            mock_docker_class.return_value = fresh_mock_docker_client
            
            try:
                docker_manager = DockerManager()
                
                # 清理所有服务器资源
                cleanup_results = []
                for server_id in enumerate(server_ids):
                    result = docker_manager.cleanup_server_resources(server_id[1])  # server_id[1] 是实际的server_id
                    cleanup_results.append(result)
                
                # 验证所有清理操作都成功
                assert all(cleanup_results), "所有服务器资源清理都应该成功"
                
                # 验证调用次数（每个服务器ID应该调用一次containers.list和images.remove）
                expected_calls = len(server_ids)
                actual_list_calls = fresh_mock_docker_client.containers.list.call_count
                actual_remove_calls = fresh_mock_docker_client.images.remove.call_count
                
                assert actual_list_calls == expected_calls, f"containers.list调用次数应匹配服务器数量: {actual_list_calls} != {expected_calls}"
                assert actual_remove_calls == expected_calls, f"images.remove调用次数应匹配服务器数量: {actual_remove_calls} != {expected_calls}"
                
                logger.info(f"多容器清理测试成功: {len(server_ids)} 个服务器")
                
            except Exception as e:
                logger.error(f"多容器清理测试失败: {str(e)}")
                logger.error(f"测试数据: server_ids={server_ids}")
                raise

if __name__ == "__main__":
    # 运行属性测试
    pytest.main([__file__, "-v", "--tb=short"])
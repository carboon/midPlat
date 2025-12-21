"""
Property-based tests for system resource management
**Feature: ai-game-platform, Property 14: 系统资源管理**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from resource_manager import ResourceManager, ResourceLimits, ContainerActivity, ContainerState


class TestSystemResourceManagement:
    """Property-based tests for system resource management"""
    
    def setup_method(self):
        """Setup test fixtures"""
        pass
    
    @given(
        idle_timeout_seconds=st.integers(min_value=60, max_value=7200),
        time_since_activity_seconds=st.integers(min_value=0, max_value=10000),
        connection_count=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=10)
    def test_property_14_idle_container_detection(self, idle_timeout_seconds, time_since_activity_seconds, connection_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.3**
        
        Property: For any container with no activity for longer than idle_timeout_seconds
        and zero connections, the system should identify it as idle
        """
        # Create resource manager with specific idle timeout
        config = ResourceLimits(idle_timeout_seconds=idle_timeout_seconds)
        manager = ResourceManager(docker_manager=None, config=config)
        
        # Register a container
        server_id = "test_server_idle"
        container_id = "container_abc123"
        manager.register_container(server_id, container_id)
        
        # Manually set the last activity time
        activity = manager.container_activities[server_id]
        activity.last_activity = datetime.now() - timedelta(seconds=time_since_activity_seconds)
        activity.connection_count = connection_count
        
        # Get idle containers
        idle_containers = manager.get_idle_containers()
        
        # Property: Container should be marked as idle if and only if:
        # 1. Time since last activity > idle_timeout_seconds (strictly greater than)
        # 2. Connection count is 0
        should_be_idle = (time_since_activity_seconds > idle_timeout_seconds) and (connection_count == 0)
        
        if should_be_idle:
            assert len(idle_containers) == 1
            assert idle_containers[0].server_id == server_id
            assert idle_containers[0].is_idle is True
        else:
            assert len(idle_containers) == 0
    
    @pytest.mark.serial
    @given(
        max_containers=st.integers(min_value=1, max_value=100),
        current_container_count=st.integers(min_value=0, max_value=150)
    )
    @settings(max_examples=10)
    def test_property_14_container_creation_limit(self, max_containers, current_container_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.4**
        
        Property: For any system resource state, Game Server Factory should
        limit new container creation when max_containers limit is reached
        """
        # Create resource manager with specific max containers limit
        config = ResourceLimits(max_containers=max_containers)
        manager = ResourceManager(docker_manager=None, config=config)
        
        # Register containers up to current_container_count
        for i in range(min(current_container_count, 200)):  # Cap at 200 to avoid slow tests
            server_id = f"test_server_{i}"
            container_id = f"container_{i}"
            manager.register_container(server_id, container_id)
        
        # Check if new container can be created
        can_create, reason = manager.can_create_container()
        
        # Property: Can create container if and only if current count < max_containers
        actual_count = len(manager.container_activities)
        if actual_count >= max_containers:
            assert can_create is False
            assert "最大容器数量限制" in reason
        else:
            assert can_create is True
            assert "可以创建容器" in reason
    
    @given(
        max_error_count=st.integers(min_value=1, max_value=20),
        error_count=st.integers(min_value=0, max_value=30)
    )
    @settings(max_examples=10)
    def test_property_14_error_container_detection(self, max_error_count, error_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.5**
        
        Property: For any container with error_count >= max_error_count,
        the system should identify it for cleanup
        """
        # Create resource manager with specific max error count
        config = ResourceLimits(max_error_count=max_error_count)
        manager = ResourceManager(docker_manager=None, config=config)
        
        # Register a container
        server_id = "test_server_error"
        container_id = "container_error123"
        manager.register_container(server_id, container_id)
        
        # Record errors
        for i in range(error_count):
            manager.record_error(server_id, f"Error {i}")
        
        # Get error containers
        error_containers = manager.get_error_containers()
        
        # Property: Container should be in error list if and only if error_count >= max_error_count
        if error_count >= max_error_count:
            assert len(error_containers) == 1
            assert error_containers[0].server_id == server_id
            assert error_containers[0].error_count == error_count
        else:
            assert len(error_containers) == 0

    
    @pytest.mark.serial
    def test_property_14_idle_container_auto_stop_simple(self):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.3**
        
        Simple test: For idle containers, the system should automatically stop them
        """
        # Arrange
        mock_docker_manager = Mock()
        mock_docker_manager.stop_container.return_value = True
        
        config = ResourceLimits(idle_timeout_seconds=300)
        manager = ResourceManager(docker_manager=mock_docker_manager, config=config)
        
        stopped_containers = []
        def on_stopped(server_id, reason):
            stopped_containers.append((server_id, reason))
        
        manager.set_callbacks(on_container_stopped=on_stopped)
        
        # 注册两个容器
        manager.register_container("server_0", "container_0")
        manager.register_container("server_1", "container_1")
        
        # 标记第一个为闲置（使用固定的过去时间）
        past_time = datetime.now() - timedelta(seconds=500)
        activity_0 = manager.container_activities["server_0"]
        activity_0.last_activity = past_time
        activity_0.connection_count = 0
        
        # Act
        stopped_servers = manager._stop_idle_containers()
        
        # Assert
        assert "server_0" in stopped_servers, f"Expected server_0 in {stopped_servers}"
        assert mock_docker_manager.stop_container.call_count == 1
        assert len(stopped_containers) == 1
        assert stopped_containers[0] == ("server_0", "idle_timeout")
    
    @pytest.mark.serial
    @given(
        server_ids=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
            min_size=2,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=5)
    def test_property_14_idle_container_auto_stop(self, server_ids):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.3**
        
        Property: For any idle containers, the system should automatically stop them
        to save resources
        """
        # Arrange - 使用固定的闲置超时时间
        idle_timeout_seconds = 300
        mock_docker_manager = Mock()
        mock_docker_manager.stop_container.return_value = True
        
        config = ResourceLimits(idle_timeout_seconds=idle_timeout_seconds)
        manager = ResourceManager(docker_manager=mock_docker_manager, config=config)
        
        # 跟踪停止的容器
        stopped_containers = []
        def on_stopped(server_id, reason):
            stopped_containers.append((server_id, reason))
        
        manager.set_callbacks(on_container_stopped=on_stopped)
        
        # 注册容器并标记某些为闲置
        idle_server_ids = []
        now = datetime.now()
        for i, server_id in enumerate(server_ids):
            container_id = f"container_{server_id}"
            manager.register_container(server_id, container_id)
            
            # 每隔一个容器标记为闲置
            if i % 2 == 0:
                activity = manager.container_activities[server_id]
                # 设置为明确的过期时间（超过idle_timeout_seconds）
                activity.last_activity = now - timedelta(seconds=idle_timeout_seconds + 100)
                activity.connection_count = 0
                idle_server_ids.append(server_id)
        
        # 确保至少有一个闲置容器
        if not idle_server_ids:
            first_server_id = server_ids[0]
            activity = manager.container_activities[first_server_id]
            activity.last_activity = now - timedelta(seconds=idle_timeout_seconds + 100)
            activity.connection_count = 0
            idle_server_ids.append(first_server_id)
        
        # Act - 停止闲置容器
        stopped_servers = manager._stop_idle_containers()
        
        # Assert
        assert set(stopped_servers) == set(idle_server_ids), \
            f"Expected {idle_server_ids}, got {stopped_servers}"
        assert mock_docker_manager.stop_container.call_count == len(idle_server_ids)
        assert len(stopped_containers) == len(idle_server_ids)
    
    @given(
        server_ids=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
            min_size=1,
            max_size=10,
            unique=True
        ),
        max_error_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10)
    def test_property_14_error_container_cleanup(self, server_ids, max_error_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.5**
        
        Property: For any container with excessive errors, the system should
        clean up related resources and notify the user
        """
        # Create mock docker manager
        mock_docker_manager = Mock()
        mock_docker_manager.stop_container.return_value = True
        
        config = ResourceLimits(max_error_count=max_error_count)
        manager = ResourceManager(docker_manager=mock_docker_manager, config=config)
        
        # Track error notifications via callback
        error_notifications = []
        def on_error(server_id, container_id, error):
            error_notifications.append((server_id, container_id, error))
        
        manager.set_callbacks(on_container_error=on_error)
        
        # Register containers and make some have excessive errors
        error_server_ids = []
        for i, server_id in enumerate(server_ids):
            container_id = f"container_{server_id}"
            manager.register_container(server_id, container_id)
            
            # Make every other container have excessive errors
            if i % 2 == 0:
                for j in range(max_error_count):
                    manager.record_error(server_id, f"Error {j}")
                error_server_ids.append(server_id)
        
        # Cleanup error containers
        cleaned_servers = manager._cleanup_error_containers()
        
        # Property 1: All error containers should be cleaned
        assert set(cleaned_servers) == set(error_server_ids)
        
        # Property 2: Docker manager should be called for each error container
        assert mock_docker_manager.stop_container.call_count == len(error_server_ids)
        
        # Property 3: Error callbacks should be triggered for each cleaned container
        assert len(error_notifications) == len(error_server_ids)
        for server_id, container_id, error in error_notifications:
            assert server_id in error_server_ids
    
    @pytest.mark.serial
    @given(
        server_id=st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_id=st.text(min_size=12, max_size=20).filter(lambda x: x.isalnum()),
        connection_count=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=5)
    def test_property_14_activity_update_resets_idle(self, server_id, container_id, connection_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.3**
        
        Property: For any container, updating activity should reset idle status
        and update last activity time
        """
        # Arrange
        config = ResourceLimits(idle_timeout_seconds=300)
        manager = ResourceManager(docker_manager=None, config=config)
        
        # 注册容器并标记为闲置
        manager.register_container(server_id, container_id)
        activity = manager.container_activities[server_id]
        activity.last_activity = datetime.now() - timedelta(seconds=600)
        activity.is_idle = True
        activity.connection_count = 0
        
        # 验证初始状态为闲置
        idle_before = manager.get_idle_containers()
        assert len(idle_before) == 1
        
        # Act - 更新活动
        time_before_update = datetime.now()
        manager.update_activity(server_id, connection_count=connection_count)
        
        # Assert
        assert activity.is_idle is False
        assert activity.last_activity >= time_before_update
        assert activity.connection_count == connection_count
        
        # 容器不应该再在闲置列表中
        idle_after = manager.get_idle_containers()
        assert len(idle_after) == 0
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_id=st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum())
    )
    @settings(max_examples=10)
    def test_property_14_force_cleanup(self, server_id, container_id):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.5**
        
        Property: For any container, force cleanup should stop the container,
        clean up resources, and unregister from the manager
        """
        # Create mock docker manager
        mock_docker_manager = Mock()
        mock_docker_manager.stop_container.return_value = True
        mock_docker_manager.cleanup_server_resources.return_value = True
        
        manager = ResourceManager(docker_manager=mock_docker_manager)
        
        # Register container
        manager.register_container(server_id, container_id)
        assert server_id in manager.container_activities
        
        # Force cleanup
        result = manager.force_cleanup(server_id)
        
        # Property 1: Force cleanup should succeed
        assert result is True
        
        # Property 2: Docker manager should stop the container
        mock_docker_manager.stop_container.assert_called_once_with(container_id)
        
        # Property 3: Docker manager should cleanup server resources
        mock_docker_manager.cleanup_server_resources.assert_called_once_with(server_id)
        
        # Property 4: Container should be unregistered
        assert server_id not in manager.container_activities
    
    @pytest.mark.serial
    @given(
        total_containers=st.integers(min_value=1, max_value=20),
        idle_count=st.integers(min_value=0, max_value=10),
        error_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=5)
    def test_property_14_resource_stats_accuracy(self, total_containers, idle_count, error_count):
        """
        **Feature: ai-game-platform, Property 14: 系统资源管理**
        **Validates: Requirements 5.3, 5.4, 5.5**
        
        Property: Resource stats should accurately reflect the current state
        of all containers
        """
        # Arrange - 确保idle_count和error_count不超过total
        idle_count = min(idle_count, total_containers)
        error_count = min(error_count, total_containers - idle_count)
        
        config = ResourceLimits(
            max_containers=100,
            idle_timeout_seconds=300,
            max_error_count=5
        )
        manager = ResourceManager(docker_manager=None, config=config)
        
        # 注册容器并设置不同的状态
        now = datetime.now()
        for i in range(total_containers):
            server_id = f"server_{i}"
            container_id = f"container_{i}"
            manager.register_container(server_id, container_id)
            
            activity = manager.container_activities[server_id]
            
            if i < idle_count:
                # 标记为闲置
                activity.last_activity = now - timedelta(seconds=600)
                activity.connection_count = 0
            elif i < idle_count + error_count:
                # 标记为错误
                for j in range(5):
                    manager.record_error(server_id, f"Error {j}")
        
        # Act - 获取资源统计
        stats = manager.get_resource_stats()
        
        # Assert
        assert stats["total_containers"] == total_containers
        assert stats["idle_containers"] == idle_count
        assert stats["error_containers"] == error_count
        assert stats["max_containers"] == config.max_containers
        assert stats["idle_timeout_seconds"] == config.idle_timeout_seconds

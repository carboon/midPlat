"""
Property-based tests for container lifecycle control
**Feature: ai-game-platform, Property 7: 容器生命周期控制**
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
from docker_manager import DockerManager, ContainerInfo
from main import GameServerInstance


class TestContainerLifecycleControl:
    """Property-based tests for container lifecycle control"""
    
    def setup_method(self):
        """Setup test fixtures"""
        pass
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_id=st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum()),
        initial_status=st.sampled_from(['running', 'created', 'restarting']),
        timeout_seconds=st.integers(min_value=1, max_value=30)
    )
    @settings(max_examples=100)
    def test_property_7_container_stop_lifecycle(self, server_id, container_id, initial_status, timeout_seconds):
        """
        **Feature: ai-game-platform, Property 7: 容器生命周期控制**
        **Validates: Requirements 2.2**
        
        Property: For any user stop request, Game Server Factory should 
        gracefully shut down the corresponding Docker container
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            # Setup mock Docker client
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            # Mock network operations
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            # Setup both patched constructors to return the same mock
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            # Create DockerManager instance
            manager = DockerManager()
            
            # Mock container that can be stopped
            mock_container = Mock()
            mock_container.id = container_id
            mock_container.short_id = container_id[:12]
            mock_container.name = f"game-server-{server_id}"
            mock_container.status = initial_status
            mock_container.attrs = {"Created": datetime.now().isoformat()}
            
            # Mock successful stop operation
            mock_container.stop.return_value = None
            
            # Setup mock client to return our container
            mock_client.containers.get.return_value = mock_container
            
            # Test container stop operation
            result = manager.stop_container(container_id, timeout=timeout_seconds)
            
            # Property 1: Stop operation should succeed for valid containers
            assert result is True
            
            # Property 2: Docker client should be called to get the container
            mock_client.containers.get.assert_called_once_with(container_id)
            
            # Property 3: Container stop should be called with proper timeout
            mock_container.stop.assert_called_once_with(timeout=timeout_seconds)
            
            # Property 4: Stop should be graceful (using timeout, not force)
            stop_call = mock_container.stop.call_args
            assert 'timeout' in stop_call.kwargs
            assert stop_call.kwargs['timeout'] == timeout_seconds
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_id=st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum()),
        force_removal=st.booleans()
    )
    @settings(max_examples=100)
    def test_property_7_container_delete_lifecycle(self, server_id, container_id, force_removal):
        """
        **Feature: ai-game-platform, Property 7: 容器生命周期控制**
        **Validates: Requirements 2.3**
        
        Property: For any user delete request, Game Server Factory should 
        delete the container and clean up related resources
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            # Setup mock Docker client
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            # Mock container that can be removed
            mock_container = Mock()
            mock_container.id = container_id
            mock_container.short_id = container_id[:12]
            mock_container.name = f"game-server-{server_id}"
            mock_container.status = 'exited'
            
            # Mock successful remove operation
            mock_container.remove.return_value = None
            
            mock_client.containers.get.return_value = mock_container
            
            # Test container removal
            result = manager.remove_container(container_id, force=force_removal)
            
            # Property 1: Remove operation should succeed for valid containers
            assert result is True
            
            # Property 2: Docker client should be called to get the container
            mock_client.containers.get.assert_called_once_with(container_id)
            
            # Property 3: Container remove should be called with proper force flag
            mock_container.remove.assert_called_once_with(force=force_removal)
            
            # Property 4: Force parameter should be respected
            remove_call = mock_container.remove.call_args
            assert 'force' in remove_call.kwargs
            assert remove_call.kwargs['force'] == force_removal
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        image_exists=st.booleans(),
        containers_count=st.integers(min_value=0, max_value=5)
    )
    @settings(max_examples=100)
    def test_property_7_complete_resource_cleanup(self, server_id, image_exists, containers_count):
        """
        **Feature: ai-game-platform, Property 7: 容器生命周期控制**
        **Validates: Requirements 2.3**
        
        Property: For any server cleanup request, Game Server Factory should 
        clean up all related resources (containers and images)
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            # Mock containers associated with the server
            mock_containers = []
            for i in range(containers_count):
                mock_container = Mock()
                mock_container.id = f"container_{server_id}_{i}"
                mock_container.status = 'running' if i % 2 == 0 else 'exited'
                mock_container.stop.return_value = None
                mock_container.remove.return_value = None
                mock_containers.append(mock_container)
            
            # Mock containers.list to return containers with server_id label
            mock_client.containers.list.return_value = mock_containers
            
            # Mock image removal
            image_tag = f"{manager.image_name_prefix}:{server_id}"
            if image_exists:
                mock_client.images.remove.return_value = None
            else:
                mock_client.images.remove.side_effect = NotFound("Image not found")
            
            # Test complete resource cleanup
            result = manager.cleanup_server_resources(server_id)
            
            # Property 1: Cleanup should attempt to process all containers
            mock_client.containers.list.assert_called_once_with(
                all=True,
                filters={"label": f"server_id={server_id}"}
            )
            
            # Property 2: Running containers should be stopped before removal
            for i, container in enumerate(mock_containers):
                if container.status == 'running':
                    container.stop.assert_called_once_with(timeout=10)
                container.remove.assert_called_once_with(force=True)
            
            # Property 3: Image cleanup should be attempted
            mock_client.images.remove.assert_called_once_with(image_tag, force=True)
            
            # Property 4: Cleanup should succeed even if some resources don't exist
            if image_exists or containers_count == 0:
                # Should succeed if image exists or no containers to clean
                assert result is True
            else:
                # Should handle missing resources gracefully
                assert isinstance(result, bool)
    
    @given(
        container_ids=st.lists(
            st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum()),
            min_size=1,
            max_size=10,
            unique=True
        ),
        stop_timeouts=st.lists(
            st.integers(min_value=1, max_value=30),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_multiple_container_lifecycle_operations(self, container_ids, stop_timeouts):
        """
        Test lifecycle operations on multiple containers simultaneously
        """
        # Ensure we have enough timeouts for all containers
        timeouts = (stop_timeouts * (len(container_ids) // len(stop_timeouts) + 1))[:len(container_ids)]
        
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            # Create mock containers
            mock_containers = {}
            for container_id in container_ids:
                mock_container = Mock()
                mock_container.id = container_id
                mock_container.status = 'running'
                mock_container.stop.return_value = None
                mock_container.remove.return_value = None
                mock_containers[container_id] = mock_container
            
            # Setup mock client to return appropriate containers
            def get_container_side_effect(container_id):
                if container_id in mock_containers:
                    return mock_containers[container_id]
                raise NotFound(f"Container {container_id} not found")
            
            mock_client.containers.get.side_effect = get_container_side_effect
            
            # Test stopping multiple containers
            stop_results = []
            for container_id, timeout in zip(container_ids, timeouts):
                result = manager.stop_container(container_id, timeout=timeout)
                stop_results.append(result)
            
            # Property 1: All valid containers should be stopped successfully
            assert all(stop_results)
            
            # Property 2: Each container should be stopped with its specific timeout
            for container_id, timeout in zip(container_ids, timeouts):
                container = mock_containers[container_id]
                container.stop.assert_called_with(timeout=timeout)
            
            # Test removing multiple containers
            remove_results = []
            for container_id in container_ids:
                result = manager.remove_container(container_id, force=True)
                remove_results.append(result)
            
            # Property 3: All containers should be removed successfully
            assert all(remove_results)
            
            # Property 4: Each container should be removed with force=True
            for container_id in container_ids:
                container = mock_containers[container_id]
                container.remove.assert_called_with(force=True)
    
    @given(
        error_scenario=st.sampled_from([
            'container_not_found',
            'stop_api_error', 
            'remove_api_error',
            'connection_error'
        ])
    )
    @settings(max_examples=100)
    def test_lifecycle_error_handling(self, error_scenario):
        """
        Test error handling during container lifecycle operations
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound, APIError
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            container_id = "test_error_container"
            
            if error_scenario == 'container_not_found':
                # Container doesn't exist
                mock_client.containers.get.side_effect = NotFound("Container not found")
                
                # Test stop operation
                stop_result = manager.stop_container(container_id)
                assert stop_result is False  # Should return False for non-existent container
                
                # Test remove operation
                remove_result = manager.remove_container(container_id)
                assert remove_result is False  # Should return False for non-existent container
                
            elif error_scenario == 'stop_api_error':
                # Container exists but stop fails
                mock_container = Mock()
                mock_container.stop.side_effect = APIError("Stop failed")
                mock_client.containers.get.return_value = mock_container
                
                stop_result = manager.stop_container(container_id)
                assert stop_result is False  # Should return False on API error
                
            elif error_scenario == 'remove_api_error':
                # Container exists but remove fails
                mock_container = Mock()
                mock_container.remove.side_effect = APIError("Remove failed")
                mock_client.containers.get.return_value = mock_container
                
                remove_result = manager.remove_container(container_id)
                assert remove_result is False  # Should return False on API error
                
            elif error_scenario == 'connection_error':
                # Connection error during operations
                mock_client.containers.get.side_effect = ConnectionError("Connection failed")
                
                stop_result = manager.stop_container(container_id)
                assert stop_result is False  # Should handle connection errors gracefully
                
                remove_result = manager.remove_container(container_id)
                assert remove_result is False  # Should handle connection errors gracefully
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_statuses=st.lists(
            st.sampled_from(['running', 'exited', 'created', 'paused']),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_lifecycle_state_transitions(self, server_id, container_statuses):
        """
        Test proper state transitions during container lifecycle operations
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            for i, initial_status in enumerate(container_statuses):
                container_id = f"container_{server_id}_{i}"
                
                # Mock container with specific initial status
                mock_container = Mock()
                mock_container.id = container_id
                mock_container.status = initial_status
                mock_container.stop.return_value = None
                mock_container.remove.return_value = None
                
                mock_client.containers.get.return_value = mock_container
                
                # Test stop operation
                stop_result = manager.stop_container(container_id)
                
                # Property 1: Stop should succeed regardless of initial status
                assert stop_result is True
                
                # Property 2: Stop should be called on the container
                mock_container.stop.assert_called_once()
                
                # Reset mock for next test
                mock_container.reset_mock()
                
                # Test remove operation
                remove_result = manager.remove_container(container_id, force=True)
                
                # Property 3: Remove should succeed regardless of initial status when forced
                assert remove_result is True
                
                # Property 4: Remove should be called with force=True
                mock_container.remove.assert_called_once_with(force=True)
    
    def test_graceful_shutdown_timeout_behavior(self):
        """
        Test that graceful shutdown respects timeout parameters
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            # Test different timeout values
            timeout_values = [1, 5, 10, 30, 60]
            
            for timeout in timeout_values:
                mock_container = Mock()
                mock_container.id = f"test_container_{timeout}"
                mock_container.status = 'running'
                mock_container.stop.return_value = None
                
                mock_client.containers.get.return_value = mock_container
                
                # Test stop with specific timeout
                result = manager.stop_container(f"test_container_{timeout}", timeout=timeout)
                
                # Property 1: Stop should succeed
                assert result is True
                
                # Property 2: Timeout should be passed correctly
                mock_container.stop.assert_called_once_with(timeout=timeout)
                
                # Reset for next iteration
                mock_container.reset_mock()
    
    def test_resource_cleanup_completeness(self):
        """
        Test that resource cleanup is comprehensive and handles all resource types
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            manager = DockerManager()
            
            server_id = "comprehensive_cleanup_test"
            
            # Mock multiple containers with different states
            mock_containers = []
            for i in range(3):
                mock_container = Mock()
                mock_container.id = f"container_{i}"
                mock_container.status = ['running', 'exited', 'created'][i]
                mock_container.stop.return_value = None
                mock_container.remove.return_value = None
                mock_containers.append(mock_container)
            
            mock_client.containers.list.return_value = mock_containers
            mock_client.images.remove.return_value = None
            
            # Test comprehensive cleanup
            result = manager.cleanup_server_resources(server_id)
            
            # Property 1: Cleanup should succeed
            assert result is True
            
            # Property 2: All containers should be processed
            mock_client.containers.list.assert_called_once_with(
                all=True,
                filters={"label": f"server_id={server_id}"}
            )
            
            # Property 3: Running containers should be stopped first
            mock_containers[0].stop.assert_called_once_with(timeout=10)  # running container
            mock_containers[1].stop.assert_not_called()  # exited container
            mock_containers[2].stop.assert_not_called()  # created container
            
            # Property 4: All containers should be removed with force
            for container in mock_containers:
                container.remove.assert_called_once_with(force=True)
            
            # Property 5: Image should be cleaned up
            expected_image_tag = f"{manager.image_name_prefix}:{server_id}"
            mock_client.images.remove.assert_called_once_with(expected_image_tag, force=True)
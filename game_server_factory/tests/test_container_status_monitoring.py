"""
Property-based tests for container status monitoring
**Feature: ai-game-platform, Property 4: 容器状态监控**
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime
from docker_manager import DockerManager, ContainerInfo
from main import GameServerInstance


class TestContainerStatusMonitoring:
    """Property-based tests for container status monitoring"""
    
    def setup_method(self):
        """Setup test fixtures"""
        pass
    
    @given(
        container_status=st.sampled_from(['running', 'exited', 'created', 'restarting', 'paused', 'dead']),
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum()),
        container_id=st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum()),
        logs_count=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100)
    def test_property_4_container_status_monitoring(self, container_status, server_id, container_id, logs_count):
        """
        **Feature: ai-game-platform, Property 4: 容器状态监控**
        **Validates: Requirements 1.4**
        
        Property: For any created game server container, Game Server Factory 
        should monitor container status and record startup logs
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
            
            # Mock container with the given status
            mock_container = Mock()
            mock_container.id = container_id
            mock_container.short_id = container_id[:12]
            mock_container.name = f"game-server-{server_id}"
            mock_container.status = container_status
            mock_container.attrs = {"Created": datetime.now().isoformat()}
            
            # Mock container stats
            mock_stats = {
                "cpu_stats": {
                    "cpu_usage": {"total_usage": 1000000, "percpu_usage": [500000, 500000]},
                    "system_cpu_usage": 10000000
                },
                "precpu_stats": {
                    "cpu_usage": {"total_usage": 900000},
                    "system_cpu_usage": 9000000
                },
                "memory_stats": {
                    "usage": 134217728,  # 128MB
                    "limit": 268435456   # 256MB
                },
                "networks": {
                    "eth0": {
                        "rx_bytes": 1048576,  # 1MB
                        "tx_bytes": 2097152   # 2MB
                    }
                }
            }
            mock_container.stats.return_value = mock_stats
            
            # Mock container logs
            log_lines = [f"Log line {i}: Container {container_status}" for i in range(logs_count)]
            mock_logs = "\n".join(log_lines).encode('utf-8')
            mock_container.logs.return_value = mock_logs
            
            # Mock reload method
            mock_container.reload.return_value = None
            
            # Setup mock client to return our container
            mock_client.containers.get.return_value = mock_container
            
            # Test container info retrieval and monitoring
            container_info = manager.get_container_info(container_id)
            
            # Property 1: Container info should be successfully retrieved
            assert container_info is not None
            assert isinstance(container_info, ContainerInfo)
            
            # Property 2: Container status should be monitored and accessible
            assert container_info.status == container_status
            assert container_info.id == container_id
            assert container_info.name == f"game-server-{server_id}"
            
            # Property 3: Container stats should be retrievable for monitoring
            stats = container_info.get_stats()
            assert isinstance(stats, dict)
            
            # For running containers, stats should contain monitoring data
            if container_status == 'running':
                assert 'cpu_percent' in stats
                assert 'memory_usage_mb' in stats
                assert 'network_rx_mb' in stats
                assert 'network_tx_mb' in stats
                
                # Stats should be numeric values
                assert isinstance(stats['cpu_percent'], (int, float))
                assert isinstance(stats['memory_usage_mb'], (int, float))
                assert isinstance(stats['network_rx_mb'], (int, float))
                assert isinstance(stats['network_tx_mb'], (int, float))
                
                # Memory stats should be reasonable
                assert stats['memory_usage_mb'] >= 0
                assert stats['memory_limit_mb'] >= stats['memory_usage_mb']
            
            # Property 4: Container logs should be retrievable and recorded
            logs = container_info.get_logs()
            assert isinstance(logs, list)
            
            # If there are logs, they should match the expected count
            if logs_count > 0:
                assert len(logs) == logs_count
                for i, log in enumerate(logs):
                    assert f"Log line {i}" in log
                    assert container_status in log
            else:
                # Empty logs should return empty list
                assert len(logs) == 0
            
            # Property 5: Container status refresh should work
            original_status = container_info.status
            container_info.refresh()
            # Status should remain consistent after refresh
            assert container_info.status == original_status
            
            # Verify Docker client was called for monitoring operations
            mock_client.containers.get.assert_called_with(container_id)
            mock_container.stats.assert_called_once_with(stream=False)
            mock_container.logs.assert_called_once()
    
    @given(
        server_instances=st.lists(
            st.tuples(
                st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isalnum()),  # server_id
                st.text(min_size=12, max_size=64).filter(lambda x: x.isalnum()),  # container_id
                st.sampled_from(['running', 'exited', 'created', 'stopped'])  # status
            ),
            min_size=1,
            max_size=10
        )
    )
    @settings(max_examples=100)
    def test_multiple_container_monitoring(self, server_instances):
        """
        Test monitoring multiple containers simultaneously
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
            
            # Create mock containers for each server instance
            mock_containers = []
            for server_id, container_id, status in server_instances:
                mock_container = Mock()
                mock_container.id = container_id
                mock_container.short_id = container_id[:12]
                mock_container.name = f"game-server-{server_id}"
                mock_container.status = status
                mock_container.attrs = {"Created": datetime.now().isoformat()}
                
                # Mock stats and logs
                mock_container.stats.return_value = {
                    "cpu_stats": {"cpu_usage": {"total_usage": 1000000, "percpu_usage": [500000]}, "system_cpu_usage": 10000000},
                    "precpu_stats": {"cpu_usage": {"total_usage": 900000}, "system_cpu_usage": 9000000},
                    "memory_stats": {"usage": 134217728, "limit": 268435456},
                    "networks": {"eth0": {"rx_bytes": 1048576, "tx_bytes": 2097152}}
                }
                mock_container.logs.return_value = f"Container {container_id} is {status}".encode('utf-8')
                mock_container.reload.return_value = None
                
                mock_containers.append((container_id, mock_container))
            
            # Setup mock client to return appropriate containers
            def get_container_side_effect(container_id):
                for cid, container in mock_containers:
                    if cid == container_id:
                        return container
                raise NotFound(f"Container {container_id} not found")
            
            mock_client.containers.get.side_effect = get_container_side_effect
            
            # Test monitoring all containers
            monitored_containers = []
            for server_id, container_id, expected_status in server_instances:
                container_info = manager.get_container_info(container_id)
                
                # Property 1: Each container should be successfully monitored
                assert container_info is not None
                assert container_info.id == container_id
                assert container_info.status == expected_status
                
                # Property 2: Stats should be available for each container
                stats = container_info.get_stats()
                assert isinstance(stats, dict)
                
                # Property 3: Logs should be available for each container
                logs = container_info.get_logs()
                assert isinstance(logs, list)
                if logs:
                    assert container_id in logs[0]
                    assert expected_status in logs[0]
                
                monitored_containers.append(container_info)
            
            # Property 4: All containers should be independently monitorable
            assert len(monitored_containers) == len(server_instances)
            
            # Property 5: Container IDs should be unique
            container_ids = [c.id for c in monitored_containers]
            assert len(container_ids) == len(set(container_ids))
    
    @given(
        error_type=st.sampled_from(['NotFound', 'APIError', 'ConnectionError', 'TimeoutError'])
    )
    @settings(max_examples=100)
    def test_container_monitoring_error_handling(self, error_type):
        """
        Test error handling during container monitoring
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
            
            # Setup error conditions
            if error_type == 'NotFound':
                mock_client.containers.get.side_effect = NotFound("Container not found")
            elif error_type == 'APIError':
                mock_client.containers.get.side_effect = APIError("API Error")
            elif error_type == 'ConnectionError':
                mock_client.containers.get.side_effect = ConnectionError("Connection failed")
            elif error_type == 'TimeoutError':
                mock_client.containers.get.side_effect = TimeoutError("Request timeout")
            
            # Test error handling
            container_info = manager.get_container_info("nonexistent_container")
            
            # Property 1: Error conditions should be handled gracefully
            if error_type == 'NotFound':
                # NotFound should return None (expected behavior)
                assert container_info is None
            else:
                # Other errors should also return None (graceful degradation)
                assert container_info is None
    
    @given(
        refresh_count=st.integers(min_value=1, max_value=10),
        status_changes=st.lists(
            st.sampled_from(['running', 'exited', 'restarting', 'paused']),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_container_status_refresh_properties(self, refresh_count, status_changes):
        """
        Test properties of container status refresh functionality
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
            
            # Create mock container with changing status
            mock_container = Mock()
            mock_container.id = "test_container_123"
            mock_container.short_id = "test_container_123"[:12]
            mock_container.name = "game-server-test"
            mock_container.attrs = {"Created": datetime.now().isoformat()}
            
            # Setup status changes
            status_cycle = status_changes * (refresh_count // len(status_changes) + 1)
            status_iter = iter(status_cycle[:refresh_count])
            
            def reload_side_effect():
                try:
                    mock_container.status = next(status_iter)
                except StopIteration:
                    mock_container.status = status_changes[-1]
            
            mock_container.reload.side_effect = reload_side_effect
            mock_container.status = status_changes[0]  # Initial status
            
            mock_client.containers.get.return_value = mock_container
            
            # Test container status monitoring with refresh
            container_info = manager.get_container_info("test_container_123")
            assert container_info is not None
            
            initial_status = container_info.status
            
            # Property 1: Status should be trackable through multiple refreshes
            previous_status = initial_status
            for i in range(refresh_count):
                container_info.refresh()
                current_status = container_info.status
                
                # Property 2: Status should be one of the valid statuses
                assert current_status in status_changes
                
                # Property 3: Refresh should update the status
                # (Status may or may not change, but refresh should complete successfully)
                assert isinstance(current_status, str)
                assert len(current_status) > 0
                
                previous_status = current_status
            
            # Property 4: Reload should be called for each refresh
            assert mock_container.reload.call_count == refresh_count
    
    def test_container_logs_monitoring_properties(self):
        """
        Test properties of container logs monitoring
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
            
            # Test different log scenarios
            log_scenarios = [
                ("", []),  # Empty logs
                ("Single line log", ["Single line log"]),  # Single line
                ("Line 1\nLine 2\nLine 3", ["Line 1", "Line 2", "Line 3"]),  # Multiple lines
                ("2025-12-17T10:00:00Z Server started\n2025-12-17T10:00:01Z Ready", 
                 ["2025-12-17T10:00:00Z Server started", "2025-12-17T10:00:01Z Ready"]),  # Timestamped logs
            ]
            
            for log_content, expected_lines in log_scenarios:
                mock_container = Mock()
                mock_container.id = "test_container"
                mock_container.short_id = "test_container"[:12]
                mock_container.name = "game-server-test"
                mock_container.status = "running"
                mock_container.attrs = {"Created": datetime.now().isoformat()}
                mock_container.logs.return_value = log_content.encode('utf-8')
                
                mock_client.containers.get.return_value = mock_container
                
                container_info = manager.get_container_info("test_container")
                logs = container_info.get_logs()
                
                # Property 1: Logs should be returned as list of strings
                assert isinstance(logs, list)
                for log_line in logs:
                    assert isinstance(log_line, str)
                
                # Property 2: Log content should match expected lines
                if expected_lines:
                    assert len(logs) == len(expected_lines)
                    for actual, expected in zip(logs, expected_lines):
                        assert actual == expected
                else:
                    assert len(logs) == 0
    
    @given(
        tail_size=st.integers(min_value=1, max_value=1000)
    )
    @settings(max_examples=100)
    def test_log_tail_functionality(self, tail_size):
        """
        Test log tail functionality for monitoring
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
            
            # Create container with proper tail behavior
            # Mock the logs method to simulate Docker's tail behavior
            def mock_logs_with_tail(tail=100, timestamps=True):
                # Simulate Docker's tail behavior - return only the last 'tail' lines
                total_lines = tail + 50  # More lines available
                all_log_lines = [f"Log line {i}" for i in range(total_lines)]
                # Docker's tail returns the last N lines
                tailed_lines = all_log_lines[-tail:] if tail < len(all_log_lines) else all_log_lines
                return "\n".join(tailed_lines).encode('utf-8')
            
            mock_container = Mock()
            mock_container.id = "test_container"
            mock_container.short_id = "test_container"[:12]
            mock_container.name = "game-server-test"
            mock_container.status = "running"
            mock_container.attrs = {"Created": datetime.now().isoformat()}
            mock_container.logs.side_effect = mock_logs_with_tail
            
            mock_client.containers.get.return_value = mock_container
            
            container_info = manager.get_container_info("test_container")
            logs = container_info.get_logs(tail=tail_size)
            
            # Property 1: Tail should limit the number of log lines
            assert len(logs) <= tail_size
            
            # Property 2: When tail is specified, logs method should be called with tail parameter
            mock_container.logs.assert_called_with(tail=tail_size, timestamps=True)
            
            # Property 3: All returned logs should be strings
            for log_line in logs:
                assert isinstance(log_line, str)
                assert len(log_line) > 0
            
            # Property 4: The number of logs should match the tail size (when there are enough logs)
            assert len(logs) == tail_size
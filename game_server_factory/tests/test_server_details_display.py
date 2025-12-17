"""
Property-based tests for server details display
**Feature: ai-game-platform, Property 8: 服务器详情显示**
**Validates: Requirement 2.4**

Property: For any server details query, the client should display 
container status, resource usage, and running logs.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, game_servers, GameServerInstance
from docker_manager import ContainerInfo


class TestServerDetailsDisplay:
    """Property-based tests for server details display (Property 8)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        game_servers.clear()
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Cleanup after each test"""
        game_servers.clear()
    
    # Strategy for generating valid server IDs
    server_id_strategy = st.builds(
        lambda prefix, suffix: f"{prefix}_{suffix}",
        prefix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=3, max_size=15
        ),
        suffix=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')),
            min_size=3, max_size=15
        )
    )

    # Strategy for generating resource usage data
    resource_usage_strategy = st.fixed_dictionaries({
        'cpu_percent': st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        'memory_usage_mb': st.floats(min_value=0.0, max_value=16384.0, allow_nan=False),
        'memory_limit_mb': st.floats(min_value=128.0, max_value=32768.0, allow_nan=False),
        'network_rx_mb': st.floats(min_value=0.0, max_value=1000.0, allow_nan=False),
        'network_tx_mb': st.floats(min_value=0.0, max_value=1000.0, allow_nan=False)
    })
    
    # Strategy for generating log entries
    log_entry_strategy = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
        min_size=5, max_size=100
    )
    
    @given(
        server_id=server_id_strategy,
        name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
            min_size=1, max_size=50
        ),
        description=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
            min_size=1, max_size=100
        ),
        container_status=st.sampled_from(['running', 'exited', 'created', 'paused']),
        resource_usage=resource_usage_strategy,
        log_entries=st.lists(log_entry_strategy, min_size=1, max_size=10)
    )
    @settings(max_examples=100)
    def test_property_8_server_details_display(
        self, server_id, name, description, container_status, resource_usage, log_entries
    ):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        **Validates: Requirement 2.4**
        
        Property: For any server details query, the response should display:
        1. Container status
        2. Resource usage information
        3. Running logs
        """
        game_servers.clear()
        
        # Create a server instance with container
        container_id = f"container_{hash(server_id) % 1000000:012x}"
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name=name,
            description=description,
            status='running',
            container_id=container_id,
            port=8081,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={},
            logs=['Server initialized']
        )
        game_servers[server_id] = server_instance
        
        # Mock Docker manager to return container info
        with patch('main.docker_manager') as mock_docker_manager:
            mock_container = Mock(spec=ContainerInfo)
            mock_container.status = container_status
            mock_container.refresh.return_value = None
            mock_container.get_stats.return_value = resource_usage
            mock_container.get_logs.return_value = log_entries
            mock_docker_manager.get_container_info.return_value = mock_container
            
            # Query server details
            response = self.client.get(f"/servers/{server_id}")
            
            # Property 1: API should return successful response
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            response_data = response.json()
            
            # Property 2: Response should contain container status
            assert 'status' in response_data, "Response must contain 'status' field"
            # Map container status to server status
            expected_status_map = {
                'running': 'running',
                'exited': 'stopped',
                'created': 'created',
                'paused': 'paused'
            }
            expected_status = expected_status_map.get(container_status, container_status)
            assert response_data['status'] == expected_status, \
                f"Status should be '{expected_status}', got '{response_data['status']}'"
            
            # Property 3: Response should contain resource usage information
            assert 'resource_usage' in response_data, "Response must contain 'resource_usage' field"
            assert isinstance(response_data['resource_usage'], dict), \
                "resource_usage must be a dictionary"
            
            # Verify resource usage contains expected fields
            returned_usage = response_data['resource_usage']
            assert 'cpu_percent' in returned_usage, "resource_usage must contain 'cpu_percent'"
            assert 'memory_usage_mb' in returned_usage, "resource_usage must contain 'memory_usage_mb'"
            
            # Property 4: Response should contain running logs
            assert 'logs' in response_data, "Response must contain 'logs' field"
            assert isinstance(response_data['logs'], list), "logs must be a list"
            assert len(response_data['logs']) > 0, "logs should not be empty"

    @given(
        server_id=server_id_strategy,
        cpu_percent=st.floats(min_value=0.0, max_value=100.0, allow_nan=False),
        memory_mb=st.floats(min_value=0.0, max_value=8192.0, allow_nan=False),
        network_rx=st.floats(min_value=0.0, max_value=500.0, allow_nan=False),
        network_tx=st.floats(min_value=0.0, max_value=500.0, allow_nan=False)
    )
    @settings(max_examples=100)
    def test_resource_usage_accuracy(
        self, server_id, cpu_percent, memory_mb, network_rx, network_tx
    ):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test that resource usage values are accurately returned from container stats.
        """
        game_servers.clear()
        
        container_id = f"container_{hash(server_id) % 1000000:012x}"
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name="Resource Test Server",
            description="Testing resource usage accuracy",
            status='running',
            container_id=container_id,
            port=8082,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={},
            logs=['Server started']
        )
        game_servers[server_id] = server_instance
        
        # Mock container with specific resource values
        expected_stats = {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage_mb': round(memory_mb, 2),
            'memory_limit_mb': 4096.0,
            'network_rx_mb': round(network_rx, 2),
            'network_tx_mb': round(network_tx, 2)
        }
        
        with patch('main.docker_manager') as mock_docker_manager:
            mock_container = Mock(spec=ContainerInfo)
            mock_container.status = 'running'
            mock_container.refresh.return_value = None
            mock_container.get_stats.return_value = expected_stats
            mock_container.get_logs.return_value = ['Log entry']
            mock_docker_manager.get_container_info.return_value = mock_container
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Verify resource usage values match what container reported
            returned_usage = response_data['resource_usage']
            assert returned_usage['cpu_percent'] == expected_stats['cpu_percent'], \
                f"CPU percent mismatch: expected {expected_stats['cpu_percent']}, got {returned_usage['cpu_percent']}"
            assert returned_usage['memory_usage_mb'] == expected_stats['memory_usage_mb'], \
                f"Memory usage mismatch: expected {expected_stats['memory_usage_mb']}, got {returned_usage['memory_usage_mb']}"

    @given(
        server_id=server_id_strategy,
        log_count=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=100)
    def test_logs_display_completeness(self, server_id, log_count):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test that logs are properly retrieved and displayed.
        """
        game_servers.clear()
        
        container_id = f"container_{hash(server_id) % 1000000:012x}"
        
        # Create server with initial logs
        initial_logs = [f"Initial log {i}" for i in range(min(5, log_count))]
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name="Log Test Server",
            description="Testing log display",
            status='running',
            container_id=container_id,
            port=8083,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={},
            logs=initial_logs
        )
        game_servers[server_id] = server_instance
        
        # Generate container logs
        container_logs = [f"Container log entry {i}" for i in range(log_count)]
        
        with patch('main.docker_manager') as mock_docker_manager:
            mock_container = Mock(spec=ContainerInfo)
            mock_container.status = 'running'
            mock_container.refresh.return_value = None
            mock_container.get_stats.return_value = {'cpu_percent': 10.0, 'memory_usage_mb': 256.0}
            mock_container.get_logs.return_value = container_logs
            mock_docker_manager.get_container_info.return_value = mock_container
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Verify logs are present
            assert 'logs' in response_data
            assert isinstance(response_data['logs'], list)
            
            # Logs should contain entries (either initial or container logs)
            assert len(response_data['logs']) > 0, "Logs should not be empty"

    @given(
        server_id=server_id_strategy,
        container_status=st.sampled_from(['running', 'exited', 'created', 'paused', 'restarting'])
    )
    @settings(max_examples=100)
    def test_container_status_mapping(self, server_id, container_status):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test that container status is correctly mapped to server status.
        """
        game_servers.clear()
        
        container_id = f"container_{hash(server_id) % 1000000:012x}"
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name="Status Test Server",
            description="Testing status mapping",
            status='creating',  # Initial status
            container_id=container_id,
            port=8084,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={},
            logs=['Server created']
        )
        game_servers[server_id] = server_instance
        
        with patch('main.docker_manager') as mock_docker_manager:
            mock_container = Mock(spec=ContainerInfo)
            mock_container.status = container_status
            mock_container.refresh.return_value = None
            mock_container.get_stats.return_value = {'cpu_percent': 5.0, 'memory_usage_mb': 128.0}
            mock_container.get_logs.return_value = ['Status log']
            mock_docker_manager.get_container_info.return_value = mock_container
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Verify status is present and valid
            assert 'status' in response_data
            
            # Status should be mapped correctly
            status_mapping = {
                'running': 'running',
                'exited': 'stopped',
                'created': 'created',
                'paused': 'paused',
                'restarting': 'restarting'
            }
            expected_status = status_mapping.get(container_status, container_status)
            assert response_data['status'] == expected_status, \
                f"Expected status '{expected_status}' for container status '{container_status}', got '{response_data['status']}'"

    def test_server_details_without_container(self):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test server details display when container is not available.
        """
        game_servers.clear()
        
        server_id = "no_container_server"
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name="No Container Server",
            description="Server without container",
            status='error',
            container_id=None,  # No container
            port=None,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={'cpu_percent': 0, 'memory_usage_mb': 0},
            logs=['Server creation failed', 'No container available']
        )
        game_servers[server_id] = server_instance
        
        with patch('main.docker_manager') as mock_docker_manager:
            mock_docker_manager.get_container_info.return_value = None
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Should still return server details
            assert response_data['server_id'] == server_id
            assert response_data['status'] == 'error'
            assert 'resource_usage' in response_data
            assert 'logs' in response_data
            assert len(response_data['logs']) > 0

    def test_nonexistent_server_details(self):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test that querying non-existent server returns 404.
        """
        game_servers.clear()
        
        response = self.client.get("/servers/nonexistent_server_xyz")
        
        assert response.status_code == 404
        response_data = response.json()
        
        # Should return error information
        if 'detail' in response_data:
            assert '服务器不存在' in response_data['detail']
        elif 'error' in response_data:
            assert '服务器不存在' in response_data['error']['message']

    @given(
        server_id=server_id_strategy,
        name=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
            min_size=1, max_size=50
        ),
        description=st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')),
            min_size=1, max_size=100
        ),
        port=st.integers(min_value=1024, max_value=65535)
    )
    @settings(max_examples=100)
    def test_server_details_completeness(self, server_id, name, description, port):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test that all required fields are present in server details response.
        """
        game_servers.clear()
        
        container_id = f"container_{hash(server_id) % 1000000:012x}"
        created_at = datetime.now().isoformat()
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name=name,
            description=description,
            status='running',
            container_id=container_id,
            port=port,
            created_at=created_at,
            updated_at=created_at,
            resource_usage={'cpu_percent': 20.0, 'memory_usage_mb': 512.0},
            logs=['Server started successfully']
        )
        game_servers[server_id] = server_instance
        
        with patch('main.docker_manager') as mock_docker_manager:
            mock_container = Mock(spec=ContainerInfo)
            mock_container.status = 'running'
            mock_container.refresh.return_value = None
            mock_container.get_stats.return_value = {
                'cpu_percent': 25.0,
                'memory_usage_mb': 600.0,
                'memory_limit_mb': 2048.0,
                'network_rx_mb': 10.5,
                'network_tx_mb': 5.2
            }
            mock_container.get_logs.return_value = ['Container running']
            mock_docker_manager.get_container_info.return_value = mock_container
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Verify all required fields are present
            required_fields = [
                'server_id', 'name', 'description', 'status',
                'container_id', 'port', 'created_at', 'updated_at',
                'resource_usage', 'logs'
            ]
            
            for field in required_fields:
                assert field in response_data, f"Missing required field: {field}"
            
            # Verify field values match
            assert response_data['server_id'] == server_id
            assert response_data['name'] == name
            assert response_data['description'] == description
            assert response_data['container_id'] == container_id
            assert response_data['port'] == port

    def test_container_missing_after_creation(self):
        """
        **Feature: ai-game-platform, Property 8: 服务器详情显示**
        
        Test server details when container was created but is now missing.
        """
        game_servers.clear()
        
        server_id = "missing_container_server"
        container_id = "container_that_was_deleted"
        
        server_instance = GameServerInstance(
            server_id=server_id,
            name="Missing Container Server",
            description="Container was deleted externally",
            status='running',
            container_id=container_id,
            port=8085,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={'cpu_percent': 15.0},
            logs=['Server was running']
        )
        game_servers[server_id] = server_instance
        
        with patch('main.docker_manager') as mock_docker_manager:
            # Container no longer exists
            mock_docker_manager.get_container_info.return_value = None
            
            response = self.client.get(f"/servers/{server_id}")
            
            assert response.status_code == 200
            response_data = response.json()
            
            # Status should be updated to error
            assert response_data['status'] == 'error'
            
            # Logs should contain error message about missing container
            assert any('容器不存在' in log or '已被删除' in log for log in response_data['logs'])

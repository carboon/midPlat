"""
Property-based tests for room list query
**Feature: ai-game-platform, Property 10: 房间列表查询**
**Validates: Requirement 3.1**

Property: For any room list request, Matchmaker Service should return 
all active game server information.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from hypothesis import given, strategies as st, settings, assume
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, store, GameServerRegister, GameServerInfo


class TestRoomListQuery:
    """Property-based tests for room list query (Property 10)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        store.servers.clear()
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Cleanup after each test"""
        store.servers.clear()
    
    # Strategy for generating valid IP addresses
    ip_strategy = st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        a=st.integers(min_value=1, max_value=254),
        b=st.integers(min_value=0, max_value=255),
        c=st.integers(min_value=0, max_value=255),
        d=st.integers(min_value=1, max_value=254)
    )
    
    # Strategy for generating valid ports
    port_strategy = st.integers(min_value=1024, max_value=65535)
    
    # Strategy for generating server names
    name_strategy = st.text(
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')),
        min_size=1, max_size=50
    )

    @given(
        server_data_list=st.lists(
            st.fixed_dictionaries({
                'ip': ip_strategy,
                'port': port_strategy,
                'name': name_strategy,
                'max_players': st.integers(min_value=1, max_value=100),
                'current_players': st.integers(min_value=0, max_value=50)
            }),
            min_size=0,
            max_size=10,
            unique_by=lambda x: f"{x['ip']}:{x['port']}"
        )
    )
    @settings(max_examples=100)
    def test_property_10_room_list_query(self, server_data_list):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        **Validates: Requirement 3.1**
        
        Property: For any room list request, Matchmaker Service should return 
        all active game server information.
        """
        store.servers.clear()
        
        # Register servers
        registered_server_ids = []
        for server_data in server_data_list:
            # Ensure current_players <= max_players
            server_data['current_players'] = min(
                server_data['current_players'], 
                server_data['max_players']
            )
            
            response = self.client.post("/register", json={
                "ip": server_data['ip'],
                "port": server_data['port'],
                "name": server_data['name'],
                "max_players": server_data['max_players'],
                "current_players": server_data['current_players'],
                "metadata": {}
            })
            
            assert response.status_code == 200
            result = response.json()
            registered_server_ids.append(result['server_id'])
        
        # Query room list
        response = self.client.get("/servers")
        
        # Property 1: API should return successful response
        assert response.status_code == 200
        
        # Property 2: Response should be a list
        response_data = response.json()
        assert isinstance(response_data, list)
        
        # Property 3: Response should contain exactly the same number of servers
        assert len(response_data) == len(server_data_list)
        
        # Property 4: All registered servers should be present
        response_server_ids = {server['server_id'] for server in response_data}
        assert response_server_ids == set(registered_server_ids)
        
        # Property 5: Each server should have required fields
        required_fields = [
            'server_id', 'ip', 'port', 'name', 
            'max_players', 'current_players', 'metadata',
            'last_heartbeat', 'uptime'
        ]
        
        for server in response_data:
            for field in required_fields:
                assert field in server, f"Missing required field: {field}"

    @given(
        active_count=st.integers(min_value=1, max_value=5),
        stale_count=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=100)
    def test_only_active_servers_returned(self, active_count, stale_count):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        
        Test that only active servers (with recent heartbeat) are returned.
        """
        store.servers.clear()
        
        now = datetime.now()
        
        # Create active servers (recent heartbeat)
        for i in range(active_count):
            server_id = f"192.168.1.{i+1}:{8080+i}"
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": f"192.168.1.{i+1}",
                "port": 8080 + i,
                "name": f"Active Server {i}",
                "max_players": 20,
                "current_players": i,
                "metadata": {},
                "registered_at": now,
                "last_heartbeat": now  # Recent heartbeat
            }
        
        # Create stale servers (old heartbeat)
        stale_time = now - timedelta(seconds=store.heartbeat_timeout + 10)
        for i in range(stale_count):
            server_id = f"10.0.0.{i+1}:{9090+i}"
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": f"10.0.0.{i+1}",
                "port": 9090 + i,
                "name": f"Stale Server {i}",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": stale_time,
                "last_heartbeat": stale_time  # Old heartbeat
            }
        
        # Query room list
        response = self.client.get("/servers")
        
        assert response.status_code == 200
        response_data = response.json()
        
        # Property: Only active servers should be returned
        assert len(response_data) == active_count
        
        # Verify all returned servers are active ones
        for server in response_data:
            assert server['ip'].startswith('192.168.1.')

    @given(
        name=name_strategy,
        max_players=st.integers(min_value=1, max_value=100),
        current_players=st.integers(min_value=0, max_value=50)
    )
    @settings(max_examples=100)
    def test_server_info_completeness(self, name, max_players, current_players):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        
        Test that server information is complete and accurate.
        """
        store.servers.clear()
        
        # Ensure current_players <= max_players
        current_players = min(current_players, max_players)
        
        # Register a server
        response = self.client.post("/register", json={
            "ip": "192.168.1.100",
            "port": 8080,
            "name": name,
            "max_players": max_players,
            "current_players": current_players,
            "metadata": {"game_type": "test"}
        })
        
        assert response.status_code == 200
        
        # Query room list
        response = self.client.get("/servers")
        assert response.status_code == 200
        
        servers = response.json()
        assert len(servers) == 1
        
        server = servers[0]
        
        # Verify server information matches registration
        assert server['name'] == name
        assert server['max_players'] == max_players
        assert server['current_players'] == current_players
        assert server['ip'] == "192.168.1.100"
        assert server['port'] == 8080
        assert server['metadata'] == {"game_type": "test"}
        
        # Verify uptime is non-negative
        assert server['uptime'] >= 0
        
        # Verify last_heartbeat is a valid ISO format string
        assert 'last_heartbeat' in server
        datetime.fromisoformat(server['last_heartbeat'])

    def test_empty_server_list(self):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        
        Test that empty list is returned when no servers are registered.
        """
        store.servers.clear()
        
        response = self.client.get("/servers")
        
        assert response.status_code == 200
        response_data = response.json()
        
        assert isinstance(response_data, list)
        assert len(response_data) == 0

    @given(
        update_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_heartbeat_updates_reflected(self, update_count):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        
        Test that heartbeat updates are reflected in room list.
        """
        store.servers.clear()
        
        # Register a server
        response = self.client.post("/register", json={
            "ip": "192.168.1.100",
            "port": 8080,
            "name": "Test Server",
            "max_players": 20,
            "current_players": 0,
            "metadata": {}
        })
        
        assert response.status_code == 200
        server_id = response.json()['server_id']
        
        # Send heartbeats with updated player count
        for i in range(update_count):
            new_player_count = i + 1
            response = self.client.post(
                f"/heartbeat/{server_id}",
                params={"current_players": new_player_count}
            )
            assert response.status_code == 200
        
        # Query room list
        response = self.client.get("/servers")
        assert response.status_code == 200
        
        servers = response.json()
        assert len(servers) == 1
        
        # Verify player count reflects last heartbeat
        assert servers[0]['current_players'] == update_count

    def test_health_check_returns_statistics(self):
        """
        **Feature: ai-game-platform, Property 10: 房间列表查询**
        
        Test that health check returns service statistics.
        """
        store.servers.clear()
        
        # Register some servers
        for i in range(3):
            self.client.post("/register", json={
                "ip": f"192.168.1.{i+1}",
                "port": 8080 + i,
                "name": f"Server {i}",
                "max_players": 20,
                "current_players": i * 2,
                "metadata": {}
            })
        
        # Check health
        response = self.client.get("/health")
        
        assert response.status_code == 200
        health_data = response.json()
        
        assert health_data['status'] == 'healthy'
        assert 'timestamp' in health_data
        assert 'statistics' in health_data
        
        stats = health_data['statistics']
        assert stats['active_servers'] == 3
        assert stats['total_players'] == 0 + 2 + 4  # 0 + 2 + 4 = 6

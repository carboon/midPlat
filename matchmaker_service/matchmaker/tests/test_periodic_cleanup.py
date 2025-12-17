"""
Property-based tests for periodic cleanup mechanism
**Feature: ai-game-platform, Property 15: 定期清理机制**
**Validates: Requirements 5.1, 5.2**

Property: For any periodic cleanup task execution, Matchmaker Service should 
check server heartbeat status and remove expired entries.
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app, store, GameServerStore


class TestPeriodicCleanup:
    """Property-based tests for periodic cleanup mechanism (Property 15)"""
    
    def setup_method(self):
        """Setup test fixtures"""
        store.servers.clear()
        self.client = TestClient(app)
    
    def teardown_method(self):
        """Cleanup after each test"""
        store.servers.clear()

    @given(
        active_count=st.integers(min_value=0, max_value=10),
        stale_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100)
    def test_property_15_periodic_cleanup(self, active_count, stale_count):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        **Validates: Requirements 5.1, 5.2**
        
        Property: Cleanup should remove all stale servers and keep all active servers.
        """
        store.servers.clear()
        
        now = datetime.now()
        
        # Create active servers (recent heartbeat)
        active_server_ids = set()
        for i in range(active_count):
            server_id = f"active_{i}:8080"
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": f"active_{i}",
                "port": 8080,
                "name": f"Active Server {i}",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": now,
                "last_heartbeat": now  # Recent heartbeat
            }
            active_server_ids.add(server_id)
        
        # Create stale servers (old heartbeat - beyond timeout)
        stale_server_ids = set()
        stale_time = now - timedelta(seconds=store.heartbeat_timeout + 10)
        for i in range(stale_count):
            server_id = f"stale_{i}:9090"
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": f"stale_{i}",
                "port": 9090,
                "name": f"Stale Server {i}",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": stale_time,
                "last_heartbeat": stale_time  # Old heartbeat
            }
            stale_server_ids.add(server_id)
        
        # Verify initial state
        assert len(store.servers) == active_count + stale_count
        
        # Run cleanup
        removed_count = store.cleanup_stale_servers()
        
        # Property 1: Cleanup should remove exactly the stale servers
        assert removed_count == stale_count
        
        # Property 2: Only active servers should remain
        assert len(store.servers) == active_count
        
        # Property 3: All remaining servers should be active ones
        remaining_ids = set(store.servers.keys())
        assert remaining_ids == active_server_ids
        
        # Property 4: No stale servers should remain
        for stale_id in stale_server_ids:
            assert stale_id not in store.servers

    @given(
        timeout_seconds=st.integers(min_value=10, max_value=60)
    )
    @settings(max_examples=100)
    def test_heartbeat_timeout_clearly_stale(self, timeout_seconds):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        
        Test that clearly stale servers (well past timeout) are removed.
        """
        import os
        # Temporarily clear the environment variable to use the passed timeout
        old_env = os.environ.pop('HEARTBEAT_TIMEOUT', None)
        try:
            test_store = GameServerStore(heartbeat_timeout=timeout_seconds)
            
            now = datetime.now()
            # Heartbeat is clearly past timeout (timeout + 10 seconds)
            stale_time = now - timedelta(seconds=timeout_seconds + 10)
            
            server_id = "stale:8080"
            test_store.servers[server_id] = {
                "server_id": server_id,
                "ip": "stale",
                "port": 8080,
                "name": "Stale Server",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": stale_time,
                "last_heartbeat": stale_time
            }
            
            removed_count = test_store.cleanup_stale_servers()
            
            assert removed_count == 1
            assert server_id not in test_store.servers
        finally:
            if old_env is not None:
                os.environ['HEARTBEAT_TIMEOUT'] = old_env

    @given(
        timeout_seconds=st.integers(min_value=10, max_value=60)
    )
    @settings(max_examples=100)
    def test_heartbeat_timeout_clearly_active(self, timeout_seconds):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        
        Test that clearly active servers (well within timeout) are preserved.
        """
        import os
        # Temporarily clear the environment variable to use the passed timeout
        old_env = os.environ.pop('HEARTBEAT_TIMEOUT', None)
        try:
            test_store = GameServerStore(heartbeat_timeout=timeout_seconds)
            
            now = datetime.now()
            # Heartbeat is clearly within timeout (only 1 second ago)
            recent_time = now - timedelta(seconds=1)
            
            server_id = "active:8080"
            test_store.servers[server_id] = {
                "server_id": server_id,
                "ip": "active",
                "port": 8080,
                "name": "Active Server",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": recent_time,
                "last_heartbeat": recent_time
            }
            
            removed_count = test_store.cleanup_stale_servers()
            
            assert removed_count == 0
            assert server_id in test_store.servers
        finally:
            if old_env is not None:
                os.environ['HEARTBEAT_TIMEOUT'] = old_env

    @given(
        server_count=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100)
    def test_cleanup_idempotence(self, server_count):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        
        Test that running cleanup multiple times is idempotent.
        """
        store.servers.clear()
        
        now = datetime.now()
        stale_time = now - timedelta(seconds=store.heartbeat_timeout + 10)
        
        # Create stale servers
        for i in range(server_count):
            server_id = f"stale_{i}:8080"
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": f"stale_{i}",
                "port": 8080,
                "name": f"Stale Server {i}",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": stale_time,
                "last_heartbeat": stale_time
            }
        
        # First cleanup
        first_removed = store.cleanup_stale_servers()
        assert first_removed == server_count
        assert len(store.servers) == 0
        
        # Second cleanup (should be idempotent)
        second_removed = store.cleanup_stale_servers()
        assert second_removed == 0
        assert len(store.servers) == 0
        
        # Third cleanup
        third_removed = store.cleanup_stale_servers()
        assert third_removed == 0
        assert len(store.servers) == 0

    @given(
        active_count=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100)
    def test_active_servers_preserved_after_cleanup(self, active_count):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        
        Test that active servers are preserved after cleanup.
        """
        store.servers.clear()
        
        now = datetime.now()
        
        # Create active servers
        original_data = {}
        for i in range(active_count):
            server_id = f"active_{i}:8080"
            server_data = {
                "server_id": server_id,
                "ip": f"active_{i}",
                "port": 8080,
                "name": f"Active Server {i}",
                "max_players": 20 + i,
                "current_players": i,
                "metadata": {"index": i},
                "registered_at": now,
                "last_heartbeat": now
            }
            store.servers[server_id] = server_data.copy()
            original_data[server_id] = server_data
        
        # Run cleanup
        removed_count = store.cleanup_stale_servers()
        
        # Property 1: No servers should be removed
        assert removed_count == 0
        
        # Property 2: All servers should be preserved
        assert len(store.servers) == active_count
        
        # Property 3: Server data should be unchanged
        for server_id, original in original_data.items():
            current = store.servers[server_id]
            assert current['name'] == original['name']
            assert current['max_players'] == original['max_players']
            assert current['current_players'] == original['current_players']
            assert current['metadata'] == original['metadata']

    def test_cleanup_with_mixed_heartbeat_times(self):
        """
        **Feature: ai-game-platform, Property 15: 定期清理机制**
        
        Test cleanup with servers having various heartbeat times.
        """
        store.servers.clear()
        
        now = datetime.now()
        
        # Create servers with different heartbeat ages
        test_cases = [
            ("fresh:8080", 0, True),      # Just now - should stay
            ("recent:8080", 15, True),    # 15 seconds ago - should stay
            ("borderline:8080", 29, True), # Just under timeout - should stay
            ("expired:8080", 31, False),   # Just over timeout - should be removed
            ("old:8080", 60, False),       # 60 seconds ago - should be removed
            ("ancient:8080", 300, False),  # 5 minutes ago - should be removed
        ]
        
        for server_id, seconds_ago, should_stay in test_cases:
            heartbeat_time = now - timedelta(seconds=seconds_ago)
            store.servers[server_id] = {
                "server_id": server_id,
                "ip": server_id.split(':')[0],
                "port": 8080,
                "name": f"Server {server_id}",
                "max_players": 20,
                "current_players": 0,
                "metadata": {},
                "registered_at": heartbeat_time,
                "last_heartbeat": heartbeat_time
            }
        
        # Run cleanup
        removed_count = store.cleanup_stale_servers()
        
        # Verify results
        assert removed_count == 3  # expired, old, ancient
        
        for server_id, _, should_stay in test_cases:
            if should_stay:
                assert server_id in store.servers, f"{server_id} should have stayed"
            else:
                assert server_id not in store.servers, f"{server_id} should have been removed"

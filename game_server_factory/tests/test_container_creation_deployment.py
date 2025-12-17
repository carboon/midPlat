"""
Property-based tests for container creation and deployment
**Feature: ai-game-platform, Property 3: 容器创建和部署**
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from docker_manager import DockerManager
from code_analyzer import JavaScriptCodeAnalyzer


class TestContainerCreationDeployment:
    """Property-based tests for container creation and deployment"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.analyzer = JavaScriptCodeAnalyzer()
    
    @given(
        server_name=st.text(min_size=1, max_size=50).filter(lambda x: x.strip() and x.isascii()),
        user_code=st.sampled_from([
            '''
            module.exports = {
                initGame: function() {
                    return { score: 0, players: [] };
                },
                handlePlayerAction: function(gameState, action, data) {
                    if (action === 'click') {
                        gameState.score++;
                    }
                    return gameState;
                }
            };
            ''',
            '''
            const gameState = { clickCount: 0 };
            
            module.exports = {
                initGame: () => gameState,
                handlePlayerAction: (state, action) => {
                    if (action === 'increment') {
                        state.clickCount++;
                    }
                    return state;
                }
            };
            ''',
            '''
            module.exports = {
                initGame: function() {
                    return { 
                        board: Array(9).fill(null),
                        currentPlayer: 'X'
                    };
                },
                handlePlayerAction: function(gameState, action, data) {
                    if (action === 'move' && data.position >= 0 && data.position < 9) {
                        gameState.board[data.position] = gameState.currentPlayer;
                        gameState.currentPlayer = gameState.currentPlayer === 'X' ? 'O' : 'X';
                    }
                    return gameState;
                }
            };
            '''
        ]),
        matchmaker_url=st.sampled_from([
            "http://localhost:8000",
            "http://matchmaker:8000", 
            "http://127.0.0.1:8000"
        ])
    )
    @settings(max_examples=100)
    def test_property_3_container_creation_and_deployment(self, server_name, user_code, matchmaker_url):
        """
        **Feature: ai-game-platform, Property 3: 容器创建和部署**
        **Validates: Requirements 1.3, 4.4**
        
        Property: For any code that passes security checks, Game Server Factory 
        should create Docker container and deploy game server
        """
        # First verify the code passes security analysis
        analysis_result = self.analyzer.analyze_code(user_code)
        assume(analysis_result.is_valid)  # Only test with valid code
        
        # Generate a unique server ID
        server_id = f"test_{hash(server_name + user_code) % 10000}"
        
        # Mock Docker client and components
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            # Setup mock Docker client
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            # Mock network operations
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            # Mock image building
            mock_image = Mock()
            mock_image.id = f"sha256:{'a' * 64}"
            build_logs = [{"stream": "Step 1/8 : FROM node:16-alpine\n"}]
            mock_client.images.build.return_value = (mock_image, build_logs)
            
            # Mock container creation
            mock_container = Mock()
            mock_container.id = f"container_{'b' * 12}"
            mock_container.short_id = mock_container.id[:12]
            mock_container.name = f"game-server-{server_id}"
            mock_container.status = "running"
            mock_client.containers.run.return_value = mock_container
            
            # Setup mock returns
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            # Create DockerManager instance
            manager = DockerManager()
            
            # Test container creation
            container_id, port, image_id = manager.create_game_server(
                server_id=server_id,
                user_code=user_code,
                server_name=server_name,
                matchmaker_url=matchmaker_url
            )
            
            # Property 1: Container creation should return valid identifiers
            assert isinstance(container_id, str)
            assert len(container_id) > 0
            assert isinstance(image_id, str) 
            assert len(image_id) > 0
            
            # Property 2: Port should be in valid range
            assert isinstance(port, int)
            assert 1024 <= port <= 65535
            
            # Property 3: Docker client should be called to build image
            mock_client.images.build.assert_called_once()
            build_call = mock_client.images.build.call_args
            assert 'tag' in build_call.kwargs
            assert server_id in build_call.kwargs['tag']
            
            # Property 4: Docker client should be called to run container
            mock_client.containers.run.assert_called_once()
            run_call = mock_client.containers.run.call_args
            
            # Verify container configuration
            assert 'ports' in run_call.kwargs
            assert '8080/tcp' in run_call.kwargs['ports']
            assert run_call.kwargs['ports']['8080/tcp'] == port
            
            # Verify environment variables
            assert 'environment' in run_call.kwargs
            env = run_call.kwargs['environment']
            assert env['PORT'] == '8080'
            assert env['ROOM_NAME'] == server_name
            assert env['MATCHMAKER_URL'] == matchmaker_url
            
            # Property 5: Container should have proper labels
            assert 'labels' in run_call.kwargs
            labels = run_call.kwargs['labels']
            assert labels['created_by'] == 'game_server_factory'
            assert labels['server_id'] == server_id
            assert labels['server_name'] == server_name
    
    @given(
        server_id=st.text(min_size=1, max_size=30).filter(lambda x: x.strip() and x.replace('_', '').replace('-', '').isalnum())
    )
    @settings(max_examples=100)
    def test_dockerfile_generation_consistency(self, server_id):
        """
        Test that Dockerfile generation is consistent and contains required elements
        """
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            user_code = "console.log('test');"
            server_name = f"test-game-{server_id}"
            
            # Generate Dockerfile
            dockerfile = manager._generate_dockerfile(user_code, server_name)
            
            # Property 1: Dockerfile should contain essential elements
            required_elements = [
                "FROM node:16-alpine",
                "WORKDIR /usr/src/app", 
                "COPY package.json ./",
                "RUN npm install",
                "COPY server.js ./",
                "COPY user_game.js ./",
                "EXPOSE 8080",
                "CMD [\"node\", \"server.js\"]"
            ]
            
            for element in required_elements:
                assert element in dockerfile, f"Dockerfile missing required element: {element}"
            
            # Property 2: Server name should be properly escaped in environment
            assert f'ENV ROOM_NAME="{server_name}"' in dockerfile
    
    @given(
        user_code=st.sampled_from([
            'module.exports = { test: true };',
            'const x = 1; module.exports = { x };',
            'function test() {} module.exports = { test };',
            'module.exports = { init: () => ({}) };',
            'let state = {}; module.exports = { state };'
        ])
    )
    @settings(max_examples=100)
    def test_user_code_preparation_properties(self, user_code):
        """
        Test properties of user code preparation
        """
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # Prepare user code
            prepared_code = manager._prepare_user_code(user_code)
            
            # Property 1: Prepared code should always contain module.exports
            assert 'module.exports' in prepared_code
            
            # Property 2: If original code had module.exports, it should be unchanged
            if 'module.exports' in user_code:
                assert prepared_code == user_code
            
            # Property 3: Prepared code should be valid JavaScript-like structure
            assert isinstance(prepared_code, str)
            assert len(prepared_code) > 0
    
    def test_port_allocation_properties(self):
        """
        Test properties of port allocation
        """
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # Mock socket to simulate available ports
            with patch('socket.socket') as mock_socket:
                mock_socket_instance = Mock()
                mock_socket_instance.__enter__ = Mock(return_value=mock_socket_instance)
                mock_socket_instance.__exit__ = Mock(return_value=None)
                mock_socket_instance.bind.return_value = None
                mock_socket.return_value = mock_socket_instance
                
                # Test multiple port allocations
                ports = []
                for _ in range(10):
                    port = manager._find_available_port()
                    ports.append(port)
                
                # Property 1: All ports should be in valid range
                for port in ports:
                    assert isinstance(port, int)
                    assert 1024 <= port <= 65535
                    assert port >= manager.base_port
                
                # Property 2: Port should be within reasonable range from base
                for port in ports:
                    assert port < manager.base_port + 1000
    
    @given(
        server_names=st.lists(
            st.text(min_size=1, max_size=20).filter(lambda x: x.strip() and x.isascii()),
            min_size=1,
            max_size=5
        )
    )
    @settings(max_examples=100)
    def test_server_template_generation_properties(self, server_names):
        """
        Test properties of server template generation
        """
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            for server_name in server_names:
                user_code = "console.log('test');"
                matchmaker_url = "http://localhost:8000"
                
                # Generate server template
                template = manager._generate_server_template(user_code, server_name, matchmaker_url)
                
                # Property 1: Template should contain required Node.js imports
                required_imports = [
                    "const express = require('express');",
                    "const http = require('http');", 
                    "const socketIo = require('socket.io');",
                    "const axios = require('axios');"
                ]
                
                for import_stmt in required_imports:
                    assert import_stmt in template, f"Template missing import: {import_stmt}"
                
                # Property 2: Template should reference user code
                assert "require('./user_game.js')" in template
                
                # Property 3: Template should contain server name and matchmaker URL
                assert server_name in template
                assert matchmaker_url in template
                
                # Property 4: Template should have WebSocket event handlers
                assert "socket.on('playerAction'" in template
                assert "socket.on('disconnect'" in template
                
                # Property 5: Template should have heartbeat functionality
                assert "sendHeartbeat" in template
                assert "axios.post" in template
    
    def test_container_creation_error_handling(self):
        """
        Test error handling during container creation
        """
        with patch('docker.from_env') as mock_docker:
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound, APIError
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_client.networks.create.return_value = Mock()
            
            # Simulate Docker build failure
            mock_client.images.build.side_effect = APIError("Build failed")
            mock_docker.return_value = mock_client
            
            manager = DockerManager()
            
            # Test that container creation handles errors gracefully
            with pytest.raises(RuntimeError) as exc_info:
                manager.create_game_server(
                    server_id="test_error",
                    user_code="console.log('test');",
                    server_name="Error Test",
                    matchmaker_url="http://localhost:8000"
                )
            
            # Property: Error should be wrapped in RuntimeError with descriptive message
            assert "容器创建失败" in str(exc_info.value)
    
    def test_network_creation_properties(self):
        """
        Test properties of Docker network creation
        """
        with patch('docker.from_env') as mock_docker_env, \
             patch('docker.DockerClient') as mock_docker_client:
            
            mock_client = Mock()
            mock_client.ping.return_value = True
            
            from docker.errors import NotFound
            
            # Test network creation when network doesn't exist
            mock_client.networks.get.side_effect = NotFound("Network not found")
            mock_network = Mock()
            mock_client.networks.create.return_value = mock_network
            
            # Setup both patched constructors to return the same mock
            mock_docker_env.return_value = mock_client
            mock_docker_client.return_value = mock_client
            
            # Create manager (should trigger network creation)
            manager = DockerManager()
            
            # Property 1: Network creation should be attempted
            mock_client.networks.create.assert_called_once()
            
            # Property 2: Network should be created with correct parameters
            create_call = mock_client.networks.create.call_args
            assert create_call.args[0] == manager.network_name
            assert create_call.kwargs['driver'] == 'bridge'
            assert 'labels' in create_call.kwargs
            assert create_call.kwargs['labels']['created_by'] == 'game_server_factory'
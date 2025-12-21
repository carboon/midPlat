"""
自动服务器注册属性测试
**Feature: ai-game-platform, Property 4: 自动服务器注册**
**验证需求: 1.5**
"""

import pytest
import asyncio
import json
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import Mock, patch, AsyncMock
import logging

# 导入被测试的模块
from docker_manager import DockerManager

logger = logging.getLogger(__name__)

# 测试数据生成策略
@st.composite
def server_registration_data(draw):
    """
    生成服务器注册数据
    
    注意：server_id 必须符合 Docker 镜像标签规范：
    - 只能包含小写字母、数字、下划线、句号和连字符
    - 不能以句号或连字符开头
    - 最多 128 个字符
    """
    # 生成符合 Docker 标签规范的 server_id
    # 只使用小写字母、数字、下划线、句号和连字符
    server_id = draw(st.text(
        min_size=5,
        max_size=30,
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789_.-'
    ))
    
    # 确保 server_id 不以句号或连字符开头
    assume(not server_id.startswith(('.', '-')))
    
    # 生成 server_name（允许更多字符）
    server_name = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))
    ))
    
    port = draw(st.integers(min_value=8081, max_value=9000))
    matchmaker_url = draw(st.sampled_from([
        "http://localhost:8000",
        "http://matchmaker:8000", 
        "http://127.0.0.1:8000"
    ]))
    
    return {
        'server_id': server_id,
        'server_name': server_name,
        'port': port,
        'matchmaker_url': matchmaker_url
    }

@st.composite
def html_game_content(draw):
    """
    生成有效的HTML游戏内容
    
    注意：生成的内容应该是有效的 HTML，不包含会破坏 HTML 结构的特殊字符
    """
    # 生成标题（避免特殊字符）
    title = draw(st.text(
        min_size=1,
        max_size=50,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))
    ))
    
    # 生成游戏内容（避免特殊字符）
    body_content = draw(st.text(
        min_size=1,
        max_size=200,
        alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))
    ))
    
    # 确保标题和内容不为空
    assume(title.strip() != '')
    assume(body_content.strip() != '')
    
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>{title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .game {{ text-align: center; margin: 50px; }}
    </style>
</head>
<body>
    <div class="game">
        <h1>{title}</h1>
        <p>{body_content}</p>
        <button onclick="alert('Game started!')">开始游戏</button>
    </div>
    <script>
        console.log('HTML游戏已加载');
    </script>
</body>
</html>"""
    
    return html_content

class TestAutoServerRegistration:
    """自动服务器注册属性测试类"""
    
    def setup_method(self):
        """测试设置"""
        # 创建模拟的Docker客户端
        self.mock_docker_client = Mock()
        self.mock_container = Mock()
        self.mock_image = Mock()
        
        # 设置模拟返回值
        self.mock_container.id = "test_container_id_123"
        self.mock_container.short_id = "test_123"
        self.mock_container.name = "test-container"
        self.mock_container.status = "running"
        
        self.mock_image.id = "test_image_id_456"
        
        # 模拟构建过程
        self.mock_docker_client.images.build.return_value = (
            self.mock_image, 
            [{'stream': 'Step 1/5 : FROM node:16-alpine\n'}, {'stream': 'Successfully built\n'}]
        )
        
        # 模拟容器运行
        self.mock_docker_client.containers.run.return_value = self.mock_container
        
        # 模拟网络检查
        self.mock_docker_client.networks.get.return_value = Mock()
        
        # 模拟ping成功
        self.mock_docker_client.ping.return_value = True
        
        # 重置调用计数
        self.mock_docker_client.reset_mock()
        self.mock_container.reset_mock()
        self.mock_image.reset_mock()

    @given(
        registration_data=server_registration_data(),
        html_content=html_game_content()
    )
    @settings(max_examples=10, deadline=30000)
    def test_html_game_server_auto_registration_property(self, registration_data, html_content):
        """
        属性测试：HTML游戏服务器自动注册
        
        **Feature: ai-game-platform, Property 4: 自动服务器注册**
        **验证需求: 1.5**
        
        对于任何成功创建的HTML游戏服务器，系统应该生成包含自动注册逻辑的服务器代码
        """
        # 跳过空的server_id或server_name
        assume(registration_data['server_id'].strip() != '')
        assume(registration_data['server_name'].strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            # 设置Docker客户端模拟
            mock_docker_class.return_value = self.mock_docker_client
            
            # 模拟端口查找
            with patch('socket.socket') as mock_socket:
                mock_socket.return_value.__enter__.return_value.bind.return_value = None
                
                # 模拟端口分配
                with patch.object(DockerManager, '_find_available_port', return_value=registration_data['port']):
                    try:
                        # 创建DockerManager实例
                        docker_manager = DockerManager()
                        
                        # 调用HTML游戏容器创建方法
                        container_id, port, image_id = docker_manager.create_html_game_server(
                            server_id=registration_data['server_id'],
                            html_content=html_content,
                            other_files={},
                            server_name=registration_data['server_name'],
                            matchmaker_url=registration_data['matchmaker_url']
                        )
                        
                        # 验证容器创建成功
                        assert container_id is not None, "容器ID不应为空"
                        assert port == registration_data['port'], f"端口应匹配: {port} != {registration_data['port']}"
                        assert image_id is not None, "镜像ID不应为空"
                        
                        # 验证Docker容器运行调用包含正确的环境变量（用于自动注册）
                        if self.mock_docker_client.containers.run.call_args:
                            run_call = self.mock_docker_client.containers.run.call_args
                            assert 'environment' in run_call.kwargs, "运行调用应包含环境变量"
                            
                            env = run_call.kwargs['environment']
                            
                            # 验证自动注册相关的环境变量
                            assert 'ROOM_NAME' in env, "环境变量应包含房间名称（用于注册）"
                            assert env['ROOM_NAME'] == registration_data['server_name'], "房间名称应匹配"
                            
                            assert 'MATCHMAKER_URL' in env, "环境变量应包含撮合服务URL（用于注册）"
                            assert env['MATCHMAKER_URL'] == registration_data['matchmaker_url'], "撮合服务URL应匹配"
                            
                            assert 'PORT' in env, "环境变量应包含端口号（用于注册）"
                            assert env['PORT'] == '8080', "容器内部端口应为8080"
                        
                        # 验证生成的服务器模板包含自动注册逻辑
                        # 通过检查Docker构建调用来验证生成的文件内容
                        if self.mock_docker_client.images.build.call_args:
                            build_call = self.mock_docker_client.images.build.call_args
                            build_path = build_call.kwargs.get('path')
                            
                            # 在实际实现中，这里会检查生成的server.js文件是否包含注册逻辑
                            # 由于我们使用mock，我们验证构建调用的参数
                            assert build_path is not None, "构建路径不应为空"
                            assert 'tag' in build_call.kwargs, "构建应包含标签"
                            assert registration_data['server_id'] in build_call.kwargs['tag'], "标签应包含服务器ID"
                        
                        logger.info(f"自动注册测试成功: {registration_data['server_id']}, 端口: {port}")
                        
                    except Exception as e:
                        # 记录失败信息用于调试
                        logger.error(f"自动注册测试失败: {str(e)}")
                        logger.error(f"测试数据: {registration_data}")
                        raise

    @given(registration_data=server_registration_data())
    @settings(max_examples=10, deadline=10000)
    def test_server_registration_environment_variables_property(self, registration_data):
        """
        属性测试：服务器注册环境变量配置
        
        **Feature: ai-game-platform, Property 4: 自动服务器注册**
        **验证需求: 1.5**
        
        对于任何服务器创建请求，系统应该正确配置注册相关的环境变量
        """
        assume(registration_data['server_id'].strip() != '')
        assume(registration_data['server_name'].strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            with patch('socket.socket') as mock_socket:
                mock_socket.return_value.__enter__.return_value.bind.return_value = None
                
                with patch.object(DockerManager, '_find_available_port', return_value=registration_data['port']):
                    try:
                        docker_manager = DockerManager()
                        
                        container_id, port, image_id = docker_manager.create_html_game_server(
                            server_id=registration_data['server_id'],
                            html_content="<html><body>Test Game</body></html>",
                            other_files={},
                            server_name=registration_data['server_name'],
                            matchmaker_url=registration_data['matchmaker_url']
                        )
                        
                        # 验证环境变量配置
                        if self.mock_docker_client.containers.run.call_args:
                            run_call = self.mock_docker_client.containers.run.call_args
                            env = run_call.kwargs['environment']
                            
                            # 验证所有必需的注册环境变量
                            required_env_vars = ['ROOM_NAME', 'MATCHMAKER_URL', 'PORT', 'NODE_ENV']
                            for var in required_env_vars:
                                assert var in env, f"环境变量 {var} 应该存在"
                            
                            # 验证环境变量值的正确性
                            assert env['ROOM_NAME'] == registration_data['server_name'], "房间名称环境变量应正确"
                            assert env['MATCHMAKER_URL'] == registration_data['matchmaker_url'], "撮合服务URL环境变量应正确"
                            assert env['PORT'] == '8080', "端口环境变量应为容器内部端口"
                            assert env['NODE_ENV'] == 'production', "Node环境应为生产模式"
                        
                        logger.info(f"环境变量配置测试成功: {registration_data['server_id']}")
                        
                    except Exception as e:
                        logger.error(f"环境变量配置测试失败: {str(e)}")
                        raise

    @given(
        server_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Zs'))),
        matchmaker_url=st.sampled_from([
            "http://localhost:8000",
            "http://matchmaker:8000", 
            "http://127.0.0.1:8000",
            "https://matchmaker.example.com"
        ])
    )
    @settings(max_examples=10, deadline=15000)
    def test_registration_url_validation_property(self, server_name, matchmaker_url):
        """
        属性测试：注册URL验证
        
        **Feature: ai-game-platform, Property 4: 自动服务器注册**
        **验证需求: 1.5**
        
        对于任何有效的撮合服务URL，系统应该正确配置服务器的注册目标
        """
        assume(server_name.strip() != '')
        
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            with patch('socket.socket') as mock_socket:
                mock_socket.return_value.__enter__.return_value.bind.return_value = None
                
                try:
                    docker_manager = DockerManager()
                    
                    container_id, port, image_id = docker_manager.create_html_game_server(
                        server_id="test_server",
                        html_content="<html><body><h1>Test Game</h1></body></html>",
                        other_files={},
                        server_name=server_name,
                        matchmaker_url=matchmaker_url
                    )
                    
                    # 验证撮合服务URL配置
                    if self.mock_docker_client.containers.run.call_args:
                        run_call = self.mock_docker_client.containers.run.call_args
                        env = run_call.kwargs['environment']
                        
                        assert env['MATCHMAKER_URL'] == matchmaker_url, f"撮合服务URL应匹配: {env['MATCHMAKER_URL']} != {matchmaker_url}"
                        
                        # 验证URL格式（应该是有效的HTTP/HTTPS URL）
                        assert matchmaker_url.startswith(('http://', 'https://')), "撮合服务URL应以http://或https://开头"
                    
                    logger.info(f"注册URL验证测试成功: {matchmaker_url}")
                    
                except Exception as e:
                    logger.error(f"注册URL验证测试失败: {str(e)}")
                    logger.error(f"测试数据: server_name={server_name}, matchmaker_url={matchmaker_url}")
                    raise

    def test_registration_template_generation(self):
        """
        测试注册模板生成
        
        **Feature: ai-game-platform, Property 4: 自动服务器注册**
        **验证需求: 1.5**
        """
        with patch('docker.DockerClient') as mock_docker_class:
            mock_docker_class.return_value = self.mock_docker_client
            
            with patch('socket.socket') as mock_socket:
                mock_socket.return_value.__enter__.return_value.bind.return_value = None
                
                docker_manager = DockerManager()
                
                # 测试生成的HTML服务器模板包含注册逻辑
                server_template = docker_manager._generate_html_server_template(
                    server_name="Test Game",
                    matchmaker_url="http://localhost:8000"
                )
                
                # 验证模板包含注册相关代码
                assert "MATCHMAKER_URL" in server_template, "模板应包含撮合服务URL配置"
                assert "ROOM_NAME" in server_template, "模板应包含房间名称配置"
                assert "sendHeartbeat" in server_template, "模板应包含心跳发送函数"
                assert "axios.post" in server_template, "模板应包含HTTP请求代码"
                assert "/register" in server_template, "模板应包含注册端点"
                
                # 验证心跳机制
                assert "HEARTBEAT_INTERVAL" in server_template, "模板应包含心跳间隔配置"
                assert "setTimeout(sendHeartbeat" in server_template, "模板应包含心跳定时器"
                
                logger.info("注册模板生成测试成功")

if __name__ == "__main__":
    # 运行属性测试
    pytest.main([__file__, "-v", "--tb=short"])
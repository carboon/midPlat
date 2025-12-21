"""
Docker容器管理器
负责Docker容器的创建、监控、生命周期管理和日志收集
"""

import os
import json
import tempfile
import shutil
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import docker
from docker.errors import DockerException, APIError, NotFound
from docker.models.containers import Container
from docker.models.images import Image

logger = logging.getLogger(__name__)

class ContainerInfo:
    """容器信息类"""
    
    def __init__(self, container: Container):
        self.container = container
        self.id = container.id
        self.short_id = container.short_id
        self.name = container.name
        self.status = container.status
        self.created = container.attrs.get('Created', '')
        
    def get_stats(self) -> Dict[str, Any]:
        """获取容器资源使用统计"""
        try:
            stats = self.container.stats(stream=False)
            
            # 计算CPU使用率
            cpu_percent = 0.0
            if 'cpu_stats' in stats and 'precpu_stats' in stats:
                cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                           stats['precpu_stats']['cpu_usage']['total_usage']
                system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                              stats['precpu_stats']['system_cpu_usage']
                
                if system_delta > 0 and cpu_delta > 0:
                    cpu_percent = (cpu_delta / system_delta) * \
                                 len(stats['cpu_stats']['cpu_usage']['percpu_usage']) * 100.0
            
            # 计算内存使用
            memory_usage = 0
            memory_limit = 0
            if 'memory_stats' in stats:
                memory_usage = stats['memory_stats'].get('usage', 0)
                memory_limit = stats['memory_stats'].get('limit', 0)
            
            # 网络IO统计
            network_rx = 0
            network_tx = 0
            if 'networks' in stats:
                for interface in stats['networks'].values():
                    network_rx += interface.get('rx_bytes', 0)
                    network_tx += interface.get('tx_bytes', 0)
            
            return {
                'cpu_percent': round(cpu_percent, 2),
                'memory_usage_mb': round(memory_usage / (1024 * 1024), 2),
                'memory_limit_mb': round(memory_limit / (1024 * 1024), 2),
                'network_rx_mb': round(network_rx / (1024 * 1024), 2),
                'network_tx_mb': round(network_tx / (1024 * 1024), 2)
            }
        except Exception as e:
            logger.error(f"获取容器统计信息失败: {e}")
            return {}
    
    def get_logs(self, tail: int = 100) -> List[str]:
        """获取容器日志"""
        try:
            logs = self.container.logs(tail=tail, timestamps=True).decode('utf-8')
            return logs.strip().split('\n') if logs.strip() else []
        except Exception as e:
            logger.error(f"获取容器日志失败: {e}")
            return [f"日志获取失败: {str(e)}"]
    
    def refresh(self):
        """刷新容器状态"""
        try:
            self.container.reload()
            self.status = self.container.status
        except Exception as e:
            logger.error(f"刷新容器状态失败: {e}")
            self.status = "unknown"

class DockerManager:
    """Docker容器管理器"""
    
    def __init__(self):
        """初始化Docker客户端"""
        try:
            import os
            
            # 打印调试信息
            logger.info(f"DOCKER_HOST环境变量: {os.environ.get('DOCKER_HOST', 'Not set')}")
            
            # 尝试直接使用Unix socket
            socket_path = '/var/run/docker.sock'
            logger.info(f"尝试连接Docker socket: {socket_path}")
            
            # 检查socket文件是否存在
            if not os.path.exists(socket_path):
                raise RuntimeError(f"Docker socket不存在: {socket_path}")
            
            # 使用unix://前缀
            base_url = f'unix://{socket_path}'
            logger.info(f"使用base_url: {base_url}")
            
            self.client = docker.DockerClient(base_url=base_url)
            
            # 测试连接
            self.client.ping()
            logger.info("Docker客户端连接成功")
        except DockerException as e:
            logger.error(f"Docker客户端连接失败: {e}")
            raise RuntimeError(f"无法连接到Docker: {e}")
        
        # 配置
        self.network_name = os.getenv("DOCKER_NETWORK", "game-network")
        self.base_port = int(os.getenv("BASE_PORT", 8081))
        self.image_name_prefix = "game-server"
        
        # 确保网络存在
        self._ensure_network_exists()
    
    def _ensure_network_exists(self):
        """确保Docker网络存在"""
        try:
            self.client.networks.get(self.network_name)
            logger.info(f"Docker网络 '{self.network_name}' 已存在")
        except NotFound:
            try:
                self.client.networks.create(
                    self.network_name,
                    driver="bridge",
                    labels={"created_by": "game_server_factory"}
                )
                logger.info(f"创建Docker网络: {self.network_name}")
            except APIError as e:
                logger.error(f"创建Docker网络失败: {e}")
                raise
    
    def _find_available_port(self) -> int:
        """查找可用端口，考虑Docker容器已使用的端口"""
        import socket
        
        # 获取所有已使用的端口（包括Docker容器）
        used_ports = self._get_used_ports()
        
        port = self.base_port
        while port < self.base_port + 1000:  # 最多尝试1000个端口
            if port not in used_ports:
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.bind(('', port))
                        logger.info(f"分配端口: {port}")
                        return port
                except OSError:
                    pass
            port += 1
        
        raise RuntimeError("无法找到可用端口")
    
    def _get_used_ports(self) -> set:
        """获取所有已使用的端口（包括Docker容器）"""
        used_ports = set()
        
        try:
            # 获取所有游戏容器
            containers = self.list_game_containers()
            for container in containers:
                # 从容器端口映射中提取端口
                if container.container.ports:
                    for port_mapping in container.container.ports.values():
                        if port_mapping:
                            for mapping in port_mapping:
                                if 'HostPort' in mapping:
                                    try:
                                        port = int(mapping['HostPort'])
                                        used_ports.add(port)
                                        logger.debug(f"容器 {container.short_id} 使用端口: {port}")
                                    except (ValueError, TypeError):
                                        pass
        except Exception as e:
            logger.warning(f"获取已使用端口失败: {e}")
        
        return used_ports
    
    def _sanitize_docker_tag(self, tag: str) -> str:
        """清理Docker标签，确保符合Docker规范
        
        Docker标签只能包含小写字母、数字、下划线、句点和连字符
        不能包含中文字符或其他特殊字符
        """
        import re
        # 移除所有非ASCII字符和不允许的字符
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', tag)
        # 转换为小写
        sanitized = sanitized.lower()
        # 确保不为空
        if not sanitized:
            sanitized = "game"
        # 确保长度不超过128字符（Docker限制）
        if len(sanitized) > 128:
            sanitized = sanitized[:128]
        return sanitized
    
    def _generate_html_dockerfile(self, server_name: str) -> str:
        """生成HTML游戏服务器的Dockerfile"""
        dockerfile_content = f"""# HTML游戏服务器Dockerfile
FROM node:16-alpine

# 设置工作目录
WORKDIR /usr/src/app

# 复制package.json
COPY package.json ./

# 安装依赖
RUN npm install

# 复制应用文件
COPY server.js ./
COPY game ./game

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV NODE_ENV=production
ENV ROOM_NAME="{server_name}"

# 启动应用
CMD ["node", "server.js"]
"""
        return dockerfile_content

    def _generate_html_server_template(self, server_name: str, matchmaker_url: str) -> str:
        """生成HTML游戏服务器模板代码"""
        server_template = f"""const express = require('express');
const http = require('http');
const path = require('path');
const axios = require('axios');
require('dotenv').config();

// 初始化 Express 应用
const app = express();
const server = http.createServer(app);

// 从环境变量获取配置
const PORT = process.env.PORT || 8080;
const EXTERNAL_PORT = process.env.EXTERNAL_PORT || PORT; // 外部访问端口
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || '{matchmaker_url}';
const ROOM_NAME = process.env.ROOM_NAME || '{server_name}';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;

// 提供静态HTML游戏文件
app.use(express.static(path.join(__dirname, 'game')));

// 基础路由
app.get('/', (req, res) => {{
    res.sendFile(path.join(__dirname, 'game', 'index.html'));
}});

// 健康检查端点
app.get('/health', (req, res) => {{
    res.json({{ status: 'healthy', room: ROOM_NAME, port: PORT, external_port: EXTERNAL_PORT }});
}});

// 启动服务器
server.listen(PORT, () => {{
    console.log(`HTML游戏服务器运行在端口 ${{PORT}}`);
    console.log(`外部访问端口: ${{EXTERNAL_PORT}}`);
    console.log(`房间名称: ${{ROOM_NAME}}`);
    
    // 启动后立即上报心跳
    sendHeartbeat();
}});

// 心跳上报逻辑
async function sendHeartbeat() {{
    try {{
        const response = await axios.post(`${{MATCHMAKER_URL}}/register`, {{
            ip: 'localhost',
            port: EXTERNAL_PORT, // 使用外部端口进行注册
            name: ROOM_NAME,
            max_players: 20,
            current_players: 0,
            metadata: {{
                created_by: 'game_server_factory',
                game_type: 'html',
                internal_port: PORT,
                external_port: EXTERNAL_PORT
            }}
        }});
        
        console.log(`心跳上报成功: localhost:${{EXTERNAL_PORT}} (${{ROOM_NAME}})`);
        
        // 每隔指定时间发送一次心跳
        setTimeout(sendHeartbeat, HEARTBEAT_INTERVAL);
    }} catch (error) {{
        console.error('心跳上报失败:', error.message);
        // 指定时间后重试
        setTimeout(sendHeartbeat, RETRY_INTERVAL);
    }}
}}

// 优雅关闭
process.on('SIGTERM', () => {{
    console.log('收到SIGTERM信号，正在关闭服务器...');
    server.close(() => {{
        console.log('服务器已关闭');
        process.exit(0);
    }});
}});
"""
        return server_template

    def _generate_dockerfile(self, user_code: str, server_name: str) -> str:
        """生成动态Dockerfile内容"""
        dockerfile_content = f"""# 动态生成的游戏服务器Dockerfile
FROM node:16-alpine

# 设置工作目录
WORKDIR /usr/src/app

# 复制package.json
COPY package.json ./

# 安装依赖
RUN npm install

# 复制应用文件
COPY server.js ./
COPY user_game.js ./

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV NODE_ENV=production
ENV ROOM_NAME="{server_name}"

# 启动应用
CMD ["node", "server.js"]
"""
        return dockerfile_content
    
    def _generate_server_template(self, user_code: str, server_name: str, matchmaker_url: str) -> str:
        """生成服务器模板代码，集成用户代码"""
        server_template = f"""const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const axios = require('axios');
require('dotenv').config();

// 初始化 Express 应用
const app = express();
const server = http.createServer(app);
const io = socketIo(server, {{
    cors: {{
        origin: "*",
        methods: ["GET", "POST"]
    }}
}});

// 从环境变量获取配置
const PORT = process.env.PORT || 8080;
const EXTERNAL_PORT = process.env.EXTERNAL_PORT || PORT; // 外部访问端口
const MATCHMAKER_URL = process.env.MATCHMAKER_URL || '{matchmaker_url}';
const ROOM_NAME = process.env.ROOM_NAME || '{server_name}';
const HEARTBEAT_INTERVAL = parseInt(process.env.HEARTBEAT_INTERVAL) || 25000;
const RETRY_INTERVAL = parseInt(process.env.RETRY_INTERVAL) || 5000;

// 用户游戏代码
let userGameLogic;
try {{
    userGameLogic = require('./user_game.js');
}} catch (error) {{
    console.error('加载用户游戏代码失败:', error);
    userGameLogic = {{
        initGame: () => ({{ clickCount: 0 }}),
        handlePlayerAction: (gameState, action, data) => {{
            if (action === 'click') {{
                gameState.clickCount = (gameState.clickCount || 0) + 1;
            }}
            return gameState;
        }}
    }};
}}

// 初始化游戏状态
let gameState = userGameLogic.initGame ? userGameLogic.initGame() : {{ clickCount: 0 }};
let connectedPlayers = 0;

// 基础路由
app.get('/', (req, res) => {{
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>${{ROOM_NAME}}</title>
            <script src="/socket.io/socket.io.js"></script>
        </head>
        <body>
            <h1>${{ROOM_NAME}}</h1>
            <div id="gameState"></div>
            <button onclick="sendClick()">点击</button>
            <script>
                const socket = io();
                
                socket.on('gameState', (state) => {{
                    document.getElementById('gameState').innerHTML = 
                        '<pre>' + JSON.stringify(state, null, 2) + '</pre>';
                }});
                
                function sendClick() {{
                    socket.emit('playerAction', {{ action: 'click' }});
                }}
            </script>
        </body>
        </html>
    `);
}});

// WebSocket 连接处理
io.on('connection', (socket) => {{
    connectedPlayers++;
    console.log('用户连接:', socket.id, '当前玩家数:', connectedPlayers);
    
    // 发送当前游戏状态
    socket.emit('gameState', gameState);
    
    // 处理玩家操作
    socket.on('playerAction', (data) => {{
        try {{
            if (userGameLogic.handlePlayerAction) {{
                gameState = userGameLogic.handlePlayerAction(gameState, data.action, data);
            }} else {{
                // 默认处理逻辑
                if (data.action === 'click') {{
                    gameState.clickCount = (gameState.clickCount || 0) + 1;
                }}
            }}
            
            // 广播更新后的游戏状态
            io.emit('gameState', gameState);
        }} catch (error) {{
            console.error('处理玩家操作失败:', error);
            socket.emit('error', {{ message: '操作处理失败' }});
        }}
    }});
    
    // 处理用户断开连接
    socket.on('disconnect', () => {{
        connectedPlayers--;
        console.log('用户断开连接:', socket.id, '当前玩家数:', connectedPlayers);
    }});
}});

// 启动服务器
server.listen(PORT, () => {{
    console.log(`游戏服务器运行在端口 ${{PORT}}`);
    console.log(`外部访问端口: ${{EXTERNAL_PORT}}`);
    console.log(`房间名称: ${{ROOM_NAME}}`);
    
    // 启动后立即上报心跳
    sendHeartbeat();
}});

// 心跳上报逻辑
async function sendHeartbeat() {{
    try {{
        const response = await axios.post(`${{MATCHMAKER_URL}}/register`, {{
            ip: 'localhost',
            port: EXTERNAL_PORT, // 使用外部端口进行注册
            name: ROOM_NAME,
            max_players: 20,
            current_players: connectedPlayers,
            metadata: {{
                created_by: 'game_server_factory',
                game_type: 'custom',
                internal_port: PORT,
                external_port: EXTERNAL_PORT
            }}
        }});
        
        console.log(`心跳上报成功: localhost:${{EXTERNAL_PORT}} (${{ROOM_NAME}})`);
        
        // 每隔指定时间发送一次心跳
        setTimeout(sendHeartbeat, HEARTBEAT_INTERVAL);
    }} catch (error) {{
        console.error('心跳上报失败:', error.message);
        // 指定时间后重试
        setTimeout(sendHeartbeat, RETRY_INTERVAL);
    }}
}}

// 优雅关闭
process.on('SIGTERM', () => {{
    console.log('收到SIGTERM信号，正在关闭服务器...');
    server.close(() => {{
        console.log('服务器已关闭');
        process.exit(0);
    }});
}});
"""
        return server_template
    
    def _prepare_user_code(self, user_code: str) -> str:
        """准备用户代码，确保符合模块导出格式"""
        # 检查用户代码是否已经有module.exports
        if 'module.exports' not in user_code:
            # 如果没有，包装用户代码
            wrapped_code = f"""
// 用户游戏代码
{user_code}

// 默认导出
module.exports = {{
    initGame: typeof initGame !== 'undefined' ? initGame : () => ({{ clickCount: 0 }}),
    handlePlayerAction: typeof handlePlayerAction !== 'undefined' ? handlePlayerAction : 
        (gameState, action, data) => {{
            if (action === 'click') {{
                gameState.clickCount = (gameState.clickCount || 0) + 1;
            }}
            return gameState;
        }}
}};
"""
            return wrapped_code
        else:
            return user_code
    
    def create_html_game_server(
        self, 
        server_id: str, 
        html_content: str,
        other_files: Dict[str, str],
        server_name: str,
        matchmaker_url: str = "http://localhost:8000"
    ) -> Tuple[str, int, str]:
        """
        创建HTML游戏服务器容器，带有完整的错误处理和清理
        
        Args:
            server_id: 服务器唯一标识
            html_content: HTML游戏的index.html内容
            other_files: 其他游戏文件（CSS、JS等）
            server_name: 服务器名称
            matchmaker_url: 撮合服务URL
            
        Returns:
            Tuple[container_id, port, image_id]: 容器ID、端口号、镜像ID
        """
        container_id = None
        image_tag = None
        image_id = None
        
        try:
            logger.info(f"开始创建HTML游戏服务器容器: {server_id}")
            
            # 查找可用端口
            port = self._find_available_port()
            logger.info(f"为服务器 {server_id} 分配端口: {port}")
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 生成package.json
                package_json = {
                    "name": "html-game-server",
                    "version": "1.0.0",
                    "main": "server.js",
                    "scripts": {
                        "start": "node server.js"
                    },
                    "dependencies": {
                        "express": "^4.18.2",
                        "axios": "^1.6.0",
                        "dotenv": "^16.3.1"
                    }
                }
                
                package_json_path = os.path.join(temp_dir, 'package.json')
                with open(package_json_path, 'w', encoding='utf-8') as f:
                    json.dump(package_json, f, indent=2)
                
                # 生成Dockerfile
                dockerfile_content = self._generate_html_dockerfile(server_name)
                dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
                with open(dockerfile_path, 'w', encoding='utf-8') as f:
                    f.write(dockerfile_content)
                
                # 生成HTML游戏服务器代码
                server_template = self._generate_html_server_template(server_name, matchmaker_url)
                server_path = os.path.join(temp_dir, 'server.js')
                with open(server_path, 'w', encoding='utf-8') as f:
                    f.write(server_template)
                
                # 创建游戏文件目录
                game_dir = os.path.join(temp_dir, 'game')
                os.makedirs(game_dir, exist_ok=True)
                
                # 写入HTML游戏文件
                index_path = os.path.join(game_dir, 'index.html')
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                # 写入其他游戏文件
                for filename, content in other_files.items():
                    file_path = os.path.join(game_dir, filename)
                    # 确保目录存在
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    if isinstance(content, str):
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                    else:
                        with open(file_path, 'wb') as f:
                            f.write(content)
                
                # 构建Docker镜像 - 确保标签符合Docker规范
                safe_server_id = self._sanitize_docker_tag(server_id)
                image_tag = f"{self.image_name_prefix}:{safe_server_id}"
                logger.info(f"构建Docker镜像: {image_tag} (原始ID: {server_id})")
                
                try:
                    image, build_logs = self.client.images.build(
                        path=temp_dir,
                        tag=image_tag,
                        rm=True,
                        forcerm=True
                    )
                    
                    # 记录构建日志
                    build_log_lines = []
                    for log in build_logs:
                        if 'stream' in log:
                            log_line = log['stream'].strip()
                            if log_line:
                                build_log_lines.append(log_line)
                                logger.debug(f"镜像构建: {log_line}")
                    
                    image_id = image.id
                    logger.info(f"Docker镜像构建完成: {image_id}")
                    
                except Exception as build_error:
                    logger.error(f"Docker镜像构建失败: {build_error}")
                    # 尝试清理镜像
                    if image_tag:
                        try:
                            self.client.images.remove(image_tag, force=True)
                            logger.info(f"已清理失败的镜像: {image_tag}")
                        except Exception as cleanup_error:
                            logger.warning(f"清理镜像失败: {cleanup_error}")
                    raise RuntimeError(f"镜像构建失败: {str(build_error)}")
            
            # 创建并启动容器
            container_name = f"html-game-server-{server_id}"
            
            try:
                logger.info(f"创建容器: {container_name} (端口: {port})")
                
                container = self.client.containers.run(
                    image=image_tag,
                    name=container_name,
                    ports={'8080/tcp': port},
                    environment={
                        'PORT': '8080',
                        'EXTERNAL_PORT': str(port),
                        'ROOM_NAME': server_name,
                        'MATCHMAKER_URL': matchmaker_url,
                        'NODE_ENV': 'production'
                    },
                    network=self.network_name,
                    detach=True,
                    restart_policy={"Name": "unless-stopped"},
                    labels={
                        "created_by": "game_server_factory",
                        "server_id": server_id,
                        "server_name": server_name,
                        "game_type": "html"
                    }
                )
                
                container_id = container.id
                logger.info(f"容器创建成功: {container_id}")
                
                # 验证容器是否正常运行
                container.reload()
                if container.status != 'running':
                    logger.warning(f"容器创建后状态异常: {container.status}")
                    raise RuntimeError(f"容器创建后状态异常: {container.status}")
                
                logger.info(f"HTML游戏容器启动成功: {container_id} (端口: {port})")
                
                return container_id, port, image_id
                
            except Exception as container_error:
                logger.error(f"容器创建或启动失败: {container_error}")
                
                # 清理已创建的容器
                if container_id:
                    try:
                        container = self.client.containers.get(container_id)
                        container.stop(timeout=5)
                        container.remove(force=True)
                        logger.info(f"已清理失败的容器: {container_id}")
                    except Exception as cleanup_error:
                        logger.error(f"清理容器失败: {cleanup_error}")
                
                # 清理镜像
                if image_tag:
                    try:
                        self.client.images.remove(image_tag, force=True)
                        logger.info(f"已清理镜像: {image_tag}")
                    except Exception as cleanup_error:
                        logger.warning(f"清理镜像失败: {cleanup_error}")
                
                raise RuntimeError(f"容器创建失败: {str(container_error)}")
            
        except Exception as e:
            logger.error(f"创建HTML游戏服务器容器失败: {e}")
            raise

    def create_game_server(
        self, 
        server_id: str, 
        user_code: str, 
        server_name: str,
        matchmaker_url: str = "http://localhost:8000"
    ) -> Tuple[str, int, str]:
        """
        创建游戏服务器容器（JavaScript代码版本）
        
        Args:
            server_id: 服务器唯一标识
            user_code: 用户JavaScript代码
            server_name: 服务器名称
            matchmaker_url: 撮合服务URL
            
        Returns:
            Tuple[container_id, port, image_id]: 容器ID、端口号、镜像ID
        """
        try:
            logger.info(f"开始创建游戏服务器容器: {server_id}")
            
            # 查找可用端口
            port = self._find_available_port()
            
            # 创建临时目录
            with tempfile.TemporaryDirectory() as temp_dir:
                # 生成package.json
                package_json = {
                    "name": "game-server",
                    "version": "1.0.0",
                    "main": "server.js",
                    "scripts": {
                        "start": "node server.js"
                    },
                    "dependencies": {
                        "express": "^4.18.2",
                        "socket.io": "^4.7.2",
                        "axios": "^1.6.0",
                        "dotenv": "^16.3.1"
                    }
                }
                
                package_json_path = os.path.join(temp_dir, 'package.json')
                with open(package_json_path, 'w', encoding='utf-8') as f:
                    json.dump(package_json, f, indent=2)
                
                # 生成Dockerfile
                dockerfile_content = self._generate_dockerfile(user_code, server_name)
                dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
                with open(dockerfile_path, 'w', encoding='utf-8') as f:
                    f.write(dockerfile_content)
                
                # 生成服务器模板代码
                server_template = self._generate_server_template(user_code, server_name, matchmaker_url)
                server_path = os.path.join(temp_dir, 'server.js')
                with open(server_path, 'w', encoding='utf-8') as f:
                    f.write(server_template)
                
                # 准备用户代码
                prepared_user_code = self._prepare_user_code(user_code)
                user_code_path = os.path.join(temp_dir, 'user_game.js')
                with open(user_code_path, 'w', encoding='utf-8') as f:
                    f.write(prepared_user_code)
                
                # 构建Docker镜像 - 确保标签符合Docker规范
                safe_server_id = self._sanitize_docker_tag(server_id)
                image_tag = f"{self.image_name_prefix}:{safe_server_id}"
                logger.info(f"构建Docker镜像: {image_tag} (原始ID: {server_id})")
                
                image, build_logs = self.client.images.build(
                    path=temp_dir,
                    tag=image_tag,
                    rm=True,
                    forcerm=True
                )
                
                # 记录构建日志
                build_log_lines = []
                for log in build_logs:
                    if 'stream' in log:
                        build_log_lines.append(log['stream'].strip())
                
                logger.info(f"Docker镜像构建完成: {image.id}")
            
            # 创建并启动容器
            container_name = f"game-server-{server_id}"
            
            container = self.client.containers.run(
                image=image_tag,
                name=container_name,
                ports={'8080/tcp': port},
                environment={
                    'PORT': '8080',
                    'EXTERNAL_PORT': str(port),  # 传递外部端口
                    'ROOM_NAME': server_name,
                    'MATCHMAKER_URL': matchmaker_url,  # 使用传入的 matchmaker_url
                    'NODE_ENV': 'production'
                },
                network=self.network_name,
                detach=True,
                restart_policy={"Name": "unless-stopped"},
                labels={
                    "created_by": "game_server_factory",
                    "server_id": server_id,
                    "server_name": server_name
                }
            )
            
            logger.info(f"容器创建成功: {container.id} (端口: {port})")
            
            return container.id, port, image.id
            
        except Exception as e:
            logger.error(f"创建游戏服务器容器失败: {e}")
            raise RuntimeError(f"容器创建失败: {str(e)}")
    
    def get_container_info(self, container_id: str) -> Optional[ContainerInfo]:
        """获取容器信息"""
        try:
            container = self.client.containers.get(container_id)
            return ContainerInfo(container)
        except NotFound:
            logger.warning(f"容器不存在: {container_id}")
            return None
        except Exception as e:
            logger.error(f"获取容器信息失败: {e}")
            return None
    
    def stop_container(self, container_id: str, timeout: int = 10) -> bool:
        """停止容器"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"容器已停止: {container_id}")
            return True
        except NotFound:
            logger.warning(f"容器不存在: {container_id}")
            return False
        except Exception as e:
            logger.error(f"停止容器失败: {e}")
            return False
    
    def remove_container(self, container_id: str, force: bool = False) -> bool:
        """删除容器"""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"容器已删除: {container_id}")
            return True
        except NotFound:
            logger.warning(f"容器不存在: {container_id}")
            return False
        except Exception as e:
            logger.error(f"删除容器失败: {e}")
            return False
    
    def cleanup_server_resources(self, server_id: str) -> bool:
        """清理服务器相关资源（容器和镜像）"""
        try:
            success = True
            
            # 查找并删除相关容器
            containers = self.client.containers.list(
                all=True,
                filters={"label": f"server_id={server_id}"}
            )
            
            for container in containers:
                try:
                    if container.status == 'running':
                        container.stop(timeout=10)
                    container.remove(force=True)
                    logger.info(f"清理容器: {container.id}")
                except Exception as e:
                    logger.error(f"清理容器失败: {e}")
                    success = False
            
            # 删除相关镜像
            try:
                safe_server_id = self._sanitize_docker_tag(server_id)
                image_tag = f"{self.image_name_prefix}:{safe_server_id}"
                self.client.images.remove(image_tag, force=True)
                logger.info(f"清理镜像: {image_tag}")
            except NotFound:
                logger.info(f"镜像不存在，跳过清理: {image_tag}")
            except Exception as e:
                logger.error(f"清理镜像失败: {e}")
                success = False
            
            return success
            
        except Exception as e:
            logger.error(f"清理服务器资源失败: {e}")
            return False
    
    def list_game_containers(self) -> List[ContainerInfo]:
        """列出所有游戏服务器容器"""
        try:
            containers = self.client.containers.list(
                all=True,
                filters={"label": "created_by=game_server_factory"}
            )
            
            return [ContainerInfo(container) for container in containers]
            
        except Exception as e:
            logger.error(f"列出容器失败: {e}")
            return []
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            # Docker系统信息
            system_info = self.client.info()
            
            # 容器统计
            all_containers = self.client.containers.list(all=True)
            game_containers = self.client.containers.list(
                all=True,
                filters={"label": "created_by=game_server_factory"}
            )
            
            running_containers = [c for c in game_containers if c.status == 'running']
            
            return {
                'docker_version': system_info.get('ServerVersion', 'unknown'),
                'total_containers': len(all_containers),
                'game_containers': len(game_containers),
                'running_game_containers': len(running_containers),
                'system_memory_gb': round(system_info.get('MemTotal', 0) / (1024**3), 2),
                'available_cpus': system_info.get('NCPU', 0)
            }
            
        except Exception as e:
            logger.error(f"获取系统统计信息失败: {e}")
            return {}
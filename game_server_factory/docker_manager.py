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
            # 清除可能有问题的环境变量
            import os
            docker_host = os.environ.get('DOCKER_HOST')
            if docker_host and 'http+docker' in docker_host:
                del os.environ['DOCKER_HOST']
            
            # 尝试多种连接方式
            try:
                # 首先尝试使用Unix socket
                self.client = docker.DockerClient(base_url='unix:///var/run/docker.sock')
            except DockerException:
                try:
                    # 尝试使用环境变量
                    self.client = docker.from_env()
                except DockerException:
                    # 尝试Docker Desktop的socket路径
                    self.client = docker.DockerClient(base_url='unix:///Users/yes/.docker/run/docker.sock')
            
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
        """查找可用端口"""
        import socket
        
        port = self.base_port
        while port < self.base_port + 1000:  # 最多尝试1000个端口
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
        
        raise RuntimeError("无法找到可用端口")
    
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
    console.log(`房间名称: ${{ROOM_NAME}}`);
    
    // 启动后立即上报心跳
    sendHeartbeat();
}});

// 心跳上报逻辑
async function sendHeartbeat() {{
    try {{
        const response = await axios.post(`${{MATCHMAKER_URL}}/register`, {{
            ip: 'localhost',
            port: PORT,
            name: ROOM_NAME,
            max_players: 20,
            current_players: connectedPlayers,
            metadata: {{
                created_by: 'game_server_factory',
                game_type: 'custom'
            }}
        }});
        
        console.log(`心跳上报成功: localhost:${{PORT}} (${{ROOM_NAME}})`);
        
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
    
    def create_game_server(
        self, 
        server_id: str, 
        user_code: str, 
        server_name: str,
        matchmaker_url: str = "http://localhost:8000"
    ) -> Tuple[str, int, str]:
        """
        创建游戏服务器容器
        
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
                
                # 构建Docker镜像
                image_tag = f"{self.image_name_prefix}:{server_id}"
                logger.info(f"构建Docker镜像: {image_tag}")
                
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
                image_tag = f"{self.image_name_prefix}:{server_id}"
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
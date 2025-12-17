"""
Game Server Factory - 游戏服务器工厂
负责接收JavaScript代码、分析优化代码并动态创建游戏服务器Docker容器
"""

import os
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
from dotenv import load_dotenv

from code_analyzer import JavaScriptCodeAnalyzer, validate_file_upload, AnalysisResult
from docker_manager import DockerManager, ContainerInfo
from resource_manager import ResourceManager, ResourceLimits

# 加载环境变量
load_dotenv()

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('game_server_factory.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# GameServerInstance数据模型
class GameServerInstance(BaseModel):
    """游戏服务器实例数据模型"""
    server_id: str = Field(..., description="服务器唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="游戏名称")
    description: str = Field(..., max_length=500, description="游戏描述")
    status: str = Field(default="creating", description="状态: creating, running, stopped, error")
    container_id: Optional[str] = Field(None, description="Docker容器ID")
    port: Optional[int] = Field(None, ge=1024, le=65535, description="服务器端口")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="创建时间")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat(), description="更新时间")
    resource_usage: Dict[str, Any] = Field(default_factory=dict, description="资源使用情况")
    logs: List[str] = Field(default_factory=list, description="服务器日志")

    @validator('status')
    def validate_status(cls, v):
        valid_statuses = ["creating", "running", "stopped", "error"]
        if v not in valid_statuses:
            raise ValueError(f"状态必须是以下之一: {valid_statuses}")
        return v

    class Config:
        schema_extra = {
            "example": {
                "server_id": "user123_mygame_001",
                "name": "我的第一个游戏",
                "description": "一个简单的点击游戏",
                "status": "running",
                "container_id": "docker_container_abc123",
                "port": 8081,
                "created_at": "2025-12-17T10:00:00Z",
                "updated_at": "2025-12-17T10:30:00Z",
                "resource_usage": {
                    "cpu_percent": 15.5,
                    "memory_mb": 128,
                    "network_io": "1.2MB"
                },
                "logs": ["Server started on port 8081", "Game initialized"]
            }
        }

class CodeUploadRequest(BaseModel):
    """代码上传请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="游戏名称")
    description: str = Field(..., max_length=500, description="游戏描述")
    max_players: int = Field(default=10, ge=1, le=100, description="最大玩家数")

class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="服务状态")
    containers: int = Field(..., description="容器数量")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: Dict[str, Any] = Field(..., description="错误信息")

# 配置管理
class Config:
    """应用配置管理"""
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1024 * 1024))  # 1MB
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".js,.mjs").split(",")
    
    # Docker配置
    DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "game-network")
    BASE_PORT = int(os.getenv("BASE_PORT", 8081))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# 创建FastAPI应用
app = FastAPI(
    title="Game Server Factory",
    description="游戏服务器工厂 - 负责JavaScript代码上传、分析和动态游戏服务器创建",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 在生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理器
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(f"HTTP error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": 500,
                "message": "内部服务器错误",
                "timestamp": datetime.now().isoformat(),
                "path": str(request.url)
            }
        }
    )

# 基础路由
@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径 - 服务信息"""
    return {
        "service": "Game Server Factory",
        "version": "1.0.0",
        "description": "游戏服务器工厂 - JavaScript代码上传和动态游戏服务器创建",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    try:
        container_count = 0
        
        if docker_manager:
            # 获取游戏容器数量
            game_containers = docker_manager.list_game_containers()
            container_count = len([c for c in game_containers if c.status == 'running'])
        
        return HealthResponse(
            status="healthy" if docker_manager else "limited",
            containers=container_count
        )
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="服务不可用")

# 临时存储 - 在实际实现中应该使用数据库
game_servers: Dict[str, GameServerInstance] = {}

# 初始化代码分析器和Docker管理器
code_analyzer = JavaScriptCodeAnalyzer()
docker_manager = None
resource_manager = None

# 初始化Docker管理器
try:
    docker_manager = DockerManager()
    logger.info("Docker管理器初始化成功")
except Exception as e:
    logger.error(f"Docker管理器初始化失败: {e}")
    # 在生产环境中，这里可能需要退出应用
    # 在开发环境中，我们允许继续运行但功能受限

# 初始化资源管理器
try:
    resource_manager = ResourceManager(docker_manager=docker_manager)
    
    # 设置回调函数
    def on_container_stopped(server_id: str, reason: str):
        """容器停止回调"""
        if server_id in game_servers:
            game_servers[server_id].status = "stopped"
            game_servers[server_id].logs.append(f"容器已停止 (原因: {reason}): {datetime.now().isoformat()}")
            game_servers[server_id].updated_at = datetime.now().isoformat()
            logger.info(f"容器停止回调: {server_id}, 原因: {reason}")
    
    def on_container_error(server_id: str, container_id: str, error: str):
        """容器错误回调"""
        if server_id in game_servers:
            game_servers[server_id].status = "error"
            game_servers[server_id].logs.append(f"容器错误: {error}: {datetime.now().isoformat()}")
            game_servers[server_id].updated_at = datetime.now().isoformat()
            logger.error(f"容器错误回调: {server_id}, 错误: {error}")
    
    resource_manager.set_callbacks(
        on_container_stopped=on_container_stopped,
        on_container_error=on_container_error
    )
    
    # 启动资源监控
    resource_manager.start_monitoring()
    logger.info("资源管理器初始化成功并已启动监控")
except Exception as e:
    logger.error(f"资源管理器初始化失败: {e}")

@app.get("/servers", response_model=List[GameServerInstance])
async def get_servers():
    """获取用户的游戏服务器列表"""
    try:
        # 更新容器状态信息
        if docker_manager:
            for server_id, server in game_servers.items():
                if server.container_id:
                    container_info = docker_manager.get_container_info(server.container_id)
                    if container_info:
                        # 更新状态
                        container_info.refresh()
                        if container_info.status == 'running':
                            server.status = 'running'
                        elif container_info.status == 'exited':
                            server.status = 'stopped'
                        else:
                            server.status = container_info.status
                        
                        # 更新资源使用情况
                        server.resource_usage = container_info.get_stats()
                        server.updated_at = datetime.now().isoformat()
                    else:
                        server.status = 'error'
                        server.logs.append(f"容器不存在或已被删除: {datetime.now().isoformat()}")
        
        return list(game_servers.values())
    except Exception as e:
        logger.error(f"Failed to get servers: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务器列表失败")

@app.get("/servers/{server_id}", response_model=GameServerInstance)
async def get_server(server_id: str):
    """获取特定服务器详情"""
    try:
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        server = game_servers[server_id]
        
        # 更新容器状态和资源信息
        if docker_manager and server.container_id:
            container_info = docker_manager.get_container_info(server.container_id)
            if container_info:
                container_info.refresh()
                if container_info.status == 'running':
                    server.status = 'running'
                elif container_info.status == 'exited':
                    server.status = 'stopped'
                else:
                    server.status = container_info.status
                
                # 更新资源使用情况
                server.resource_usage = container_info.get_stats()
                
                # 获取最新日志
                container_logs = container_info.get_logs(tail=50)
                if container_logs:
                    # 合并容器日志和服务器日志
                    server.logs = server.logs[:10] + container_logs  # 保留前10条服务器日志
                
                server.updated_at = datetime.now().isoformat()
            else:
                server.status = 'error'
                server.logs.append(f"容器不存在或已被删除: {datetime.now().isoformat()}")
        
        return server
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server {server_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务器详情失败")

@app.post("/upload")
async def upload_game_code(
    file: UploadFile = File(..., description="JavaScript游戏代码文件"),
    name: str = Form(..., description="游戏名称"),
    description: str = Form(..., description="游戏描述"),
    max_players: int = Form(default=10, description="最大玩家数")
):
    """上传JavaScript游戏代码并创建游戏服务器"""
    try:
        logger.info(f"接收到代码上传请求: {name}")
        
        # 检查资源限制
        if resource_manager:
            can_create, reason = resource_manager.can_create_container()
            if not can_create:
                logger.warning(f"资源限制阻止创建容器: {reason}")
                raise HTTPException(status_code=503, detail=f"无法创建服务器: {reason}")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证文件
        is_valid, validation_message = validate_file_upload(file_content, file.filename)
        if not is_valid:
            logger.warning(f"文件验证失败: {validation_message}")
            raise HTTPException(status_code=400, detail=validation_message)
        
        # 解码文件内容
        try:
            code = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="文件编码无效，请使用UTF-8编码")
        
        # 分析代码
        analysis_result = code_analyzer.analyze_code(code)
        
        # 检查分析结果
        if not analysis_result.is_valid:
            error_details = {
                "message": "代码分析失败",
                "syntax_errors": analysis_result.syntax_errors,
                "security_issues": [
                    {
                        "severity": issue.severity,
                        "message": issue.message,
                        "line": issue.line,
                        "code_snippet": issue.code_snippet
                    }
                    for issue in analysis_result.security_issues
                ],
                "suggestions": analysis_result.suggestions
            }
            logger.warning(f"代码分析失败: {error_details}")
            raise HTTPException(status_code=400, detail=error_details)
        
        # 生成服务器ID
        server_id = f"user_{hash(name + description) % 10000}_{name.replace(' ', '_').lower()}_{len(game_servers) + 1:03d}"
        
        # 创建游戏服务器实例
        server_instance = GameServerInstance(
            server_id=server_id,
            name=name,
            description=description,
            status="creating",
            container_id=None,
            port=None,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            resource_usage={},
            logs=[
                f"代码上传成功: {file.filename}",
                f"代码分析通过: {len(analysis_result.warnings)} 个警告",
                "开始创建Docker容器..."
            ]
        )
        
        # 存储服务器实例
        game_servers[server_id] = server_instance
        
        # 创建Docker容器
        if docker_manager:
            try:
                # 获取撮合服务URL
                matchmaker_url = os.getenv("MATCHMAKER_URL", "http://localhost:8000")
                
                # 创建容器
                container_id, port, image_id = docker_manager.create_game_server(
                    server_id=server_id,
                    user_code=code,
                    server_name=name,
                    matchmaker_url=matchmaker_url
                )
                
                # 更新服务器实例
                server_instance.container_id = container_id
                server_instance.port = port
                server_instance.status = "running"
                server_instance.updated_at = datetime.now().isoformat()
                server_instance.logs.append(f"Docker容器创建成功: {container_id[:12]}")
                server_instance.logs.append(f"服务器运行在端口: {port}")
                server_instance.logs.append(f"镜像ID: {image_id[:12]}")
                
                # 注册到资源管理器
                if resource_manager:
                    resource_manager.register_container(server_id, container_id)
                
                logger.info(f"游戏服务器容器创建成功: {server_id} -> {container_id}")
                
            except Exception as container_error:
                # 容器创建失败
                server_instance.status = "error"
                server_instance.logs.append(f"容器创建失败: {str(container_error)}")
                logger.error(f"容器创建失败: {container_error}")
                
                # 不抛出异常，返回错误状态的服务器实例
        else:
            # Docker管理器不可用
            server_instance.status = "error"
            server_instance.logs.append("Docker管理器不可用，无法创建容器")
            logger.warning("Docker管理器不可用，无法创建容器")
        
        logger.info(f"游戏服务器处理完成: {server_id}")
        
        # 返回创建结果
        return {
            "server_id": server_id,
            "message": "代码上传成功" + (
                "，游戏服务器正在运行" if server_instance.status == "running" 
                else "，但容器创建失败" if server_instance.status == "error"
                else "，游戏服务器正在创建中"
            ),
            "analysis_result": {
                "warnings": analysis_result.warnings,
                "suggestions": analysis_result.suggestions
            },
            "server": server_instance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"代码上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"代码上传失败: {str(e)}")

@app.post("/servers/{server_id}/stop")
async def stop_server(server_id: str):
    """停止游戏服务器"""
    try:
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        server = game_servers[server_id]
        
        # 停止Docker容器
        if docker_manager and server.container_id:
            success = docker_manager.stop_container(server.container_id)
            if success:
                server.status = "stopped"
                server.logs.append(f"Docker容器已停止: {datetime.now().isoformat()}")
                logger.info(f"服务器容器已停止: {server_id} -> {server.container_id}")
            else:
                server.status = "error"
                server.logs.append(f"停止容器失败: {datetime.now().isoformat()}")
                logger.error(f"停止容器失败: {server_id}")
        else:
            # 没有容器ID或Docker管理器不可用
            server.status = "stopped"
            server.logs.append(f"服务器标记为已停止: {datetime.now().isoformat()}")
        
        server.updated_at = datetime.now().isoformat()
        
        return {"message": "服务器已停止", "server_id": server_id, "status": server.status}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail="停止服务器失败")

@app.delete("/servers/{server_id}")
async def delete_server(server_id: str):
    """删除游戏服务器"""
    try:
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        server = game_servers[server_id]
        
        # 从资源管理器注销
        if resource_manager:
            resource_manager.unregister_container(server_id)
        
        # 清理Docker资源
        if docker_manager:
            success = docker_manager.cleanup_server_resources(server_id)
            if success:
                logger.info(f"服务器资源清理成功: {server_id}")
            else:
                logger.warning(f"服务器资源清理部分失败: {server_id}")
        
        # 从内存中删除服务器记录
        del game_servers[server_id]
        
        logger.info(f"服务器已删除: {server_id}")
        
        return {"message": "服务器已删除", "server_id": server_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail="删除服务器失败")

@app.get("/servers/{server_id}/logs")
async def get_server_logs(server_id: str, tail: int = 100):
    """获取服务器日志"""
    try:
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        server = game_servers[server_id]
        all_logs = server.logs.copy()
        
        # 获取容器日志
        if docker_manager and server.container_id:
            container_info = docker_manager.get_container_info(server.container_id)
            if container_info:
                container_logs = container_info.get_logs(tail=tail)
                if container_logs:
                    all_logs.extend([f"[容器] {log}" for log in container_logs])
        
        # 限制日志数量
        if len(all_logs) > tail:
            all_logs = all_logs[-tail:]
        
        return {
            "server_id": server_id,
            "logs": all_logs,
            "log_count": len(all_logs),
            "container_id": server.container_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务器日志失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务器日志失败")

@app.get("/system/stats")
async def get_system_stats():
    """获取系统统计信息"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "game_servers_count": len(game_servers),
            "docker_available": docker_manager is not None,
            "resource_manager_available": resource_manager is not None
        }
        
        if docker_manager:
            docker_stats = docker_manager.get_system_stats()
            stats.update(docker_stats)
        
        if resource_manager:
            resource_stats = resource_manager.get_resource_stats()
            stats["resource_management"] = resource_stats
        
        return stats
        
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取系统统计信息失败")


@app.get("/system/resources")
async def get_resource_stats():
    """获取资源管理统计信息"""
    try:
        if not resource_manager:
            raise HTTPException(status_code=503, detail="资源管理器不可用")
        
        return resource_manager.get_resource_stats()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取资源统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取资源统计信息失败")


@app.get("/system/resources/{server_id}")
async def get_container_resource_details(server_id: str):
    """获取特定容器的资源详情"""
    try:
        if not resource_manager:
            raise HTTPException(status_code=503, detail="资源管理器不可用")
        
        details = resource_manager.get_container_details(server_id)
        if not details:
            raise HTTPException(status_code=404, detail="服务器不存在或未被资源管理器跟踪")
        
        return details
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取容器资源详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取容器资源详情失败")


@app.get("/system/idle-containers")
async def get_idle_containers():
    """获取闲置容器列表"""
    try:
        if not resource_manager:
            raise HTTPException(status_code=503, detail="资源管理器不可用")
        
        idle_containers = resource_manager.get_idle_containers()
        
        return {
            "count": len(idle_containers),
            "idle_timeout_seconds": resource_manager.config.idle_timeout_seconds,
            "containers": [
                {
                    "server_id": c.server_id,
                    "container_id": c.container_id[:12],
                    "last_activity": c.last_activity.isoformat(),
                    "connection_count": c.connection_count
                }
                for c in idle_containers
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取闲置容器列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取闲置容器列表失败")


@app.post("/system/cleanup/{server_id}")
async def force_cleanup_server(server_id: str):
    """强制清理指定服务器的资源"""
    try:
        if not resource_manager:
            raise HTTPException(status_code=503, detail="资源管理器不可用")
        
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        success = resource_manager.force_cleanup(server_id)
        
        if success:
            # 更新服务器状态
            if server_id in game_servers:
                game_servers[server_id].status = "stopped"
                game_servers[server_id].logs.append(f"强制清理完成: {datetime.now().isoformat()}")
            
            return {"message": "服务器资源已强制清理", "server_id": server_id}
        else:
            raise HTTPException(status_code=500, detail="强制清理失败")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"强制清理服务器失败: {str(e)}")
        raise HTTPException(status_code=500, detail="强制清理服务器失败")


@app.post("/servers/{server_id}/activity")
async def update_server_activity(server_id: str, connection_count: int = 0):
    """更新服务器活动状态（用于心跳或连接数更新）"""
    try:
        if server_id not in game_servers:
            raise HTTPException(status_code=404, detail="服务器不存在")
        
        if resource_manager:
            resource_manager.update_activity(server_id, connection_count)
        
        return {"message": "活动状态已更新", "server_id": server_id, "connection_count": connection_count}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新服务器活动状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="更新服务器活动状态失败")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理工作"""
    logger.info("应用正在关闭...")
    
    # 停止资源监控
    if resource_manager:
        resource_manager.stop_monitoring()
        logger.info("资源监控已停止")
    
    logger.info("应用关闭完成")


if __name__ == "__main__":
    logger.info(f"Starting Game Server Factory on {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )
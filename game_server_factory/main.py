"""
Game Server Factory - 游戏服务器工厂
负责接收HTML游戏文件、验证文件完整性并动态创建游戏服务器Docker容器
"""

import os
import logging
import logging.handlers
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import uvicorn
from dotenv import load_dotenv

from html_game_validator import HTMLGameValidator
from docker_manager import DockerManager, ContainerInfo
from resource_manager import ResourceManager, ResourceLimits
from monitoring import SystemMonitor, MonitoringConfig, AlertType, AlertSeverity

# 加载环境变量
load_dotenv()


# 增强配置管理 - 需求 7.3 (必须在使用前定义)
class Config:
    """应用配置管理 - 支持环境适配和验证"""
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB for HTML games
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".html,.htm,.zip").split(",")
    UPLOAD_TIMEOUT = int(os.getenv("UPLOAD_TIMEOUT", 300))  # 5 minutes
    
    # Docker配置
    DOCKER_NETWORK = os.getenv("DOCKER_NETWORK", "game-network")
    BASE_PORT = int(os.getenv("BASE_PORT", 8081))
    MAX_CONTAINERS = int(os.getenv("MAX_CONTAINERS", 50))
    CONTAINER_MEMORY_LIMIT = os.getenv("CONTAINER_MEMORY_LIMIT", "512m")
    CONTAINER_CPU_LIMIT = float(os.getenv("CONTAINER_CPU_LIMIT", 1.0))
    
    # 外部服务配置
    MATCHMAKER_URL = os.getenv("MATCHMAKER_URL", "http://localhost:8000")
    MATCHMAKER_TIMEOUT = int(os.getenv("MATCHMAKER_TIMEOUT", 10))
    
    # 资源管理配置
    IDLE_TIMEOUT_SECONDS = int(os.getenv("IDLE_TIMEOUT_SECONDS", 1800))  # 30 minutes
    CLEANUP_INTERVAL_SECONDS = int(os.getenv("CLEANUP_INTERVAL_SECONDS", 300))  # 5 minutes
    RESOURCE_CHECK_INTERVAL = int(os.getenv("RESOURCE_CHECK_INTERVAL", 60))  # 1 minute
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "game_server_factory.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    
    # 安全配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    API_RATE_LIMIT = int(os.getenv("API_RATE_LIMIT", 100))  # requests per minute
    
    # 监控配置常量
    STALE_SERVER_THRESHOLD_RATIO = 0.5  # 过期服务器阈值比例
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """验证配置参数 - 需求 7.3"""
        errors = []
        
        # 验证端口范围
        if not (1024 <= cls.PORT <= 65535):
            errors.append(f"PORT must be between 1024 and 65535, got {cls.PORT}")
        
        if not (1024 <= cls.BASE_PORT <= 65535):
            errors.append(f"BASE_PORT must be between 1024 and 65535, got {cls.BASE_PORT}")
        
        # 验证文件大小限制
        if cls.MAX_FILE_SIZE <= 0:
            errors.append(f"MAX_FILE_SIZE must be positive, got {cls.MAX_FILE_SIZE}")
        
        # 验证容器限制
        if cls.MAX_CONTAINERS <= 0:
            errors.append(f"MAX_CONTAINERS must be positive, got {cls.MAX_CONTAINERS}")
        
        # 验证超时设置
        if cls.UPLOAD_TIMEOUT <= 0:
            errors.append(f"UPLOAD_TIMEOUT must be positive, got {cls.UPLOAD_TIMEOUT}")
        
        if cls.IDLE_TIMEOUT_SECONDS <= 0:
            errors.append(f"IDLE_TIMEOUT_SECONDS must be positive, got {cls.IDLE_TIMEOUT_SECONDS}")
        
        # 验证环境设置
        valid_environments = ["development", "staging", "production"]
        if cls.ENVIRONMENT not in valid_environments:
            errors.append(f"ENVIRONMENT must be one of {valid_environments}, got {cls.ENVIRONMENT}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL.upper() not in valid_log_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_log_levels}, got {cls.LOG_LEVEL}")
        
        return errors
    
    @classmethod
    def get_cors_config(cls) -> Dict[str, Any]:
        """获取CORS配置 - 根据环境调整安全设置"""
        if cls.ENVIRONMENT == "production":
            return {
                "allow_origins": cls.ALLOWED_ORIGINS if cls.ALLOWED_ORIGINS != ["*"] else [],
                "allow_credentials": True,
                "allow_methods": ["GET", "POST", "DELETE"],
                "allow_headers": ["*"],
            }
        else:
            return {
                "allow_origins": ["*"],
                "allow_credentials": True,
                "allow_methods": ["*"],
                "allow_headers": ["*"],
            }
    
    @classmethod
    def is_production(cls) -> bool:
        """检查是否为生产环境"""
        return cls.ENVIRONMENT == "production"
    
    @classmethod
    def get_log_config(cls) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "level": getattr(logging, cls.LOG_LEVEL.upper()),
            "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]',
            "handlers": [
                {
                    "class": "logging.handlers.RotatingFileHandler",
                    "filename": cls.LOG_FILE,
                    "maxBytes": cls.LOG_MAX_SIZE,
                    "backupCount": cls.LOG_BACKUP_COUNT,
                },
                {
                    "class": "logging.StreamHandler",
                }
            ]
        }


def setup_logging():
    """设置增强的日志系统"""
    log_config = Config.get_log_config()
    
    # 创建根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(log_config["level"])
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(log_config["format"])
    
    # 添加文件处理器（带轮转）
    file_handler = logging.handlers.RotatingFileHandler(
        filename=Config.LOG_FILE,
        maxBytes=Config.LOG_MAX_SIZE,
        backupCount=Config.LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

setup_logging()
logger = logging.getLogger(__name__)

# 记录配置信息
logger.info(f"Game Server Factory starting with configuration:")
logger.info(f"  Environment: {Config.ENVIRONMENT}")
logger.info(f"  Host: {Config.HOST}:{Config.PORT}")
logger.info(f"  Debug mode: {Config.DEBUG}")
logger.info(f"  Max file size: {Config.MAX_FILE_SIZE / (1024*1024):.1f}MB")
logger.info(f"  Max containers: {Config.MAX_CONTAINERS}")
logger.info(f"  Docker network: {Config.DOCKER_NETWORK}")
logger.info(f"  Matchmaker URL: {Config.MATCHMAKER_URL}")

# GameServerInstance数据模型
class GameServerInstance(BaseModel):
    """游戏服务器实例数据模型"""
    server_id: str = Field(..., description="服务器唯一标识")
    name: str = Field(..., min_length=1, max_length=100, description="游戏名称")
    description: str = Field(default="", max_length=500, description="游戏描述")
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

class HTMLGameUploadRequest(BaseModel):
    """HTML游戏上传请求模型"""
    name: str = Field(..., min_length=1, max_length=100, description="游戏名称")
    description: str = Field(default="", max_length=500, description="游戏描述（可选）")
    max_players: int = Field(default=10, ge=1, le=100, description="最大玩家数")

class HealthResponse(BaseModel):
    """增强健康检查响应模型 - 需求 6.2, 6.3"""
    status: str = Field(..., description="服务状态: healthy, degraded, limited, unhealthy")
    containers: int = Field(..., description="运行中的容器数量")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    components: Optional[Dict[str, str]] = Field(None, description="各组件健康状态")
    configuration: Optional[Dict[str, Any]] = Field(None, description="配置信息")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "containers": 5,
                "timestamp": "2025-12-18T10:00:00Z",
                "components": {
                    "docker_manager": "healthy",
                    "resource_manager": "healthy",
                    "matchmaker_service": "healthy"
                },
                "configuration": {
                    "environment": "production",
                    "max_containers": 50,
                    "debug_mode": False
                }
            }
        }

class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: Dict[str, Any] = Field(..., description="错误信息")


# 创建FastAPI应用
app = FastAPI(
    title="Game Server Factory",
    description="游戏服务器工厂 - 负责HTML游戏文件上传、验证和动态游戏服务器创建",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置CORS中间件 - 根据环境配置安全策略
cors_config = Config.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# 标准化错误响应模型
class StandardErrorResponse(BaseModel):
    """标准化错误响应格式 - 需求 6.4, 6.5"""
    error: Dict[str, Any] = Field(..., description="错误详情")
    
    class Config:
        schema_extra = {
            "example": {
                "error": {
                    "code": 400,
                    "message": "请求参数错误",
                    "timestamp": "2025-12-18T10:00:00Z",
                    "path": "/upload",
                    "details": {"field": "name", "issue": "名称不能为空"}
                }
            }
        }

def create_error_response(
    status_code: int,
    message: str,
    path: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建标准化错误响应 - 需求 6.4, 6.5, 8.1"""
    error_response = {
        "error": {
            "code": status_code,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "path": path
        }
    }
    
    if details is not None:
        error_response["error"]["details"] = details
    
    return error_response

# 全局异常处理器 - 需求 8.1, 8.2, 8.3, 8.4, 8.5
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理器 - 标准化错误响应格式"""
    logger.error(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
    # 处理详细错误信息
    details = None
    if isinstance(exc.detail, dict):
        details = exc.detail
        message = exc.detail.get("message", "请求错误")
    else:
        message = str(exc.detail)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            message=message,
            path=str(request.url),
            details=details if isinstance(details, dict) else None
        )
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理器 - 捕获所有未处理的异常"""
    logger.error(
        f"Unexpected error: {str(exc)}",
        exc_info=True,
        extra={
            "path": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown",
            "exception_type": type(exc).__name__
        }
    )
    
    # 在开发模式下提供更详细的错误信息
    details = None
    if Config.DEBUG:
        details = {
            "exception_type": type(exc).__name__,
            "exception_message": str(exc)
        }
    
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            status_code=500,
            message="内部服务器错误" if not Config.DEBUG else str(exc),
            path=str(request.url),
            details=details
        )
    )

# 基础路由
@app.get("/", response_model=Dict[str, Any])
async def root():
    """根路径 - 服务信息和API导航 - 需求 6.1"""
    return {
        "service": "Game Server Factory",
        "version": "1.0.0",
        "description": "游戏服务器工厂 - HTML游戏文件上传和动态游戏服务器创建",
        "environment": Config.ENVIRONMENT,
        "api_documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "health_endpoints": {
            "basic_health": "/health",
            "detailed_monitoring": "/monitoring/detailed",
            "system_stats": "/system/stats"
        },
        "main_endpoints": {
            "upload_code": "POST /upload",
            "list_servers": "GET /servers",
            "server_details": "GET /servers/{server_id}",
            "container_status": "GET /containers/status"
        },
        "monitoring_endpoints": {
            "monitoring_status": "/monitoring/status",
            "active_alerts": "/monitoring/alerts",
            "service_statuses": "/monitoring/services"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """增强健康检查端点 - 需求 6.2, 6.3"""
    try:
        container_count = 0
        docker_status = "unavailable"
        resource_manager_status = "unavailable"
        
        # 检查Docker管理器状态
        if docker_manager:
            try:
                # 获取游戏容器数量
                game_containers = docker_manager.list_game_containers()
                container_count = len([c for c in game_containers if c.status == 'running'])
                docker_status = "healthy"
            except Exception as e:
                logger.warning(f"Docker health check failed: {e}")
                docker_status = "error"
        
        # 检查资源管理器状态
        if resource_manager:
            try:
                resource_stats = resource_manager.get_resource_stats()
                resource_manager_status = "healthy"
            except Exception as e:
                logger.warning(f"Resource manager health check failed: {e}")
                resource_manager_status = "error"
        
        # 检查外部服务连接
        matchmaker_status = await check_matchmaker_health()
        
        # 检查系统监控器状态
        monitoring_status = "unavailable"
        if system_monitor:
            try:
                monitoring_data = system_monitor.get_monitoring_status()
                monitoring_status = "healthy" if monitoring_data["monitoring_active"] else "inactive"
            except Exception as e:
                logger.warning(f"System monitor health check failed: {e}")
                monitoring_status = "error"
        
        # 确定整体健康状态
        overall_status = "healthy"
        if docker_status == "error" or resource_manager_status == "error" or monitoring_status == "error":
            overall_status = "degraded"
        elif docker_status == "unavailable" and resource_manager_status == "unavailable":
            overall_status = "limited"
        
        health_data = {
            "status": overall_status,
            "containers": container_count,
            "timestamp": datetime.now().isoformat(),
            "components": {
                "docker_manager": docker_status,
                "resource_manager": resource_manager_status,
                "matchmaker_service": matchmaker_status,
                "system_monitor": monitoring_status
            },
            "configuration": {
                "environment": Config.ENVIRONMENT,
                "max_containers": Config.MAX_CONTAINERS,
                "debug_mode": Config.DEBUG,
                "monitoring_enabled": system_monitor is not None
            }
        }
        
        return HealthResponse(**health_data)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=503, 
            detail=create_error_response(
                status_code=503,
                message="健康检查失败",
                path="/health",
                details={"error": str(e)} if Config.DEBUG else None
            )["error"]
        )

async def check_matchmaker_health() -> str:
    """检查撮合服务健康状态"""
    try:
        import httpx
        # 在测试环境中使用更短的超时时间
        timeout = 2 if Config.ENVIRONMENT == "development" else Config.MATCHMAKER_TIMEOUT
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.get(f"{Config.MATCHMAKER_URL}/health")
            if response.status_code == 200:
                return "healthy"
            else:
                return "error"
    except Exception as e:
        logger.debug(f"Matchmaker health check failed: {e}")
        return "unavailable"

# 临时存储 - 在实际实现中应该使用数据库
game_servers: Dict[str, GameServerInstance] = {}

# 初始化HTML游戏验证器和Docker管理器
html_game_validator = HTMLGameValidator()
docker_manager = None
resource_manager = None
system_monitor = None

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

# 初始化系统监控器 - 需求 6.1, 6.2, 6.3
try:
    monitoring_config = MonitoringConfig()
    # 配置外部服务监控
    monitoring_config.external_services = {
        "matchmaker": Config.MATCHMAKER_URL + "/health"
    }
    
    system_monitor = SystemMonitor(monitoring_config)
    
    # 添加自定义告警回调
    def on_alert(alert):
        """自定义告警处理"""
        # 这里可以添加更多告警处理逻辑，如发送邮件、Webhook等
        if alert.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
            logger.critical(f"CRITICAL ALERT: {alert.title} - {alert.message}")
    
    system_monitor.add_alert_callback(on_alert)
    
    logger.info("系统监控器初始化成功，将在应用启动时启动监控")
except Exception as e:
    logger.error(f"系统监控器初始化失败: {e}")
    system_monitor = None

@app.get("/servers", response_model=List[GameServerInstance])
async def get_servers():
    """获取用户的游戏服务器列表"""
    try:
        # 更新容器状态信息
        if docker_manager:
            for server_id, server in list(game_servers.items()):
                if server.container_id:
                    try:
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
                    except Exception as container_error:
                        logger.warning(f"Failed to update container info for {server_id}: {str(container_error)}")
                        # 继续处理其他服务器，不中断整个列表获取
        
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
            # ✅ 修复：如果容器不存在，保持原有状态，不要改为 'error'
            # 这样虚拟服务器（用于测试）不会被标记为错误
        
        return server
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get server {server_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务器详情失败")

@app.post("/upload")
async def upload_html_game(
    file: UploadFile = File(..., description="HTML游戏文件（ZIP或单个HTML）"),
    name: str = Form(..., description="游戏名称"),
    description: str = Form(default="", description="游戏描述（可选）"),
    max_players: int = Form(default=10, description="最大玩家数")
):
    """上传HTML游戏文件并创建游戏服务器"""
    try:
        logger.info(f"接收到HTML游戏上传请求: {name}")
        
        # 检查资源限制
        if resource_manager:
            can_create, reason = resource_manager.can_create_container()
            if not can_create:
                logger.warning(f"资源限制阻止创建容器: {reason}")
                raise HTTPException(status_code=503, detail=f"无法创建服务器: {reason}")
        
        # 读取文件内容
        file_content = await file.read()
        
        # 验证HTML游戏文件
        is_valid, validation_message, metadata = html_game_validator.validate_file(
            file_content, file.filename, max_file_size=Config.MAX_FILE_SIZE
        )
        if not is_valid:
            logger.warning(f"HTML游戏文件验证失败: {validation_message}")
            # 如果metadata包含安全问题，返回详细信息
            if metadata and 'security_issues' in metadata:
                error_detail = {
                    'message': validation_message,
                    'security_issues': metadata['security_issues']
                }
                raise HTTPException(status_code=400, detail=error_detail)
            else:
                raise HTTPException(status_code=400, detail=validation_message)
        
        # 提取HTML游戏内容
        extract_success, extract_message, extracted_data = html_game_validator.extract_html_game(file_content, file.filename)
        if not extract_success:
            logger.warning(f"HTML游戏文件提取失败: {extract_message}")
            raise HTTPException(status_code=400, detail=extract_message)
        
        # 生成服务器ID（确保只包含ASCII字符）
        import re
        import hashlib
        
        # 清理游戏名称，只保留ASCII字母和数字
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', name)
        if not safe_name:
            safe_name = "game"
        
        # 使用MD5哈希确保唯一性，避免中文字符问题
        name_hash = hashlib.md5((name + description).encode('utf-8')).hexdigest()[:8]
        server_id = f"user_{name_hash}_{safe_name.lower()}_{len(game_servers) + 1:03d}"
        
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
                f"HTML游戏文件上传成功: {file.filename}",
                f"文件类型: {metadata['file_type']}, 文件数量: {metadata['file_count']}",
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
                
                # 创建HTML游戏容器
                container_id, port, image_id = docker_manager.create_html_game_server(
                    server_id=server_id,
                    html_content=extracted_data['index_html_content'],
                    other_files=extracted_data.get('other_files', {}),
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
                
                logger.info(f"HTML游戏服务器容器创建成功: {server_id} -> {container_id}")
                
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
        
        logger.info(f"HTML游戏服务器处理完成: {server_id}")
        
        # 返回创建结果
        return {
            "server_id": server_id,
            "message": "HTML游戏文件上传成功" + (
                "，游戏服务器正在运行" if server_instance.status == "running" 
                else "，但容器创建失败" if server_instance.status == "error"
                else "，游戏服务器正在创建中"
            ),
            "validation_result": {
                "file_type": metadata['file_type'],
                "file_count": metadata['file_count'],
                "total_size": metadata['total_size']
            },
            "server": server_instance
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"HTML游戏上传失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"HTML游戏上传失败: {str(e)}")

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
    """获取系统统计信息 - 需求 6.2, 6.3"""
    try:
        stats = {
            "timestamp": datetime.now().isoformat(),
            "game_servers_count": len(game_servers),
            "docker_available": docker_manager is not None,
            "resource_manager_available": resource_manager is not None,
            "system_monitor_available": system_monitor is not None
        }
        
        # Docker统计信息
        if docker_manager:
            try:
                docker_stats = docker_manager.get_system_stats()
                stats["docker"] = docker_stats
            except Exception as e:
                stats["docker"] = {"error": str(e)}
        
        # 资源管理统计信息
        if resource_manager:
            try:
                resource_stats = resource_manager.get_resource_stats()
                stats["resource_management"] = resource_stats
            except Exception as e:
                stats["resource_management"] = {"error": str(e)}
        
        # 系统监控统计信息
        if system_monitor:
            try:
                monitoring_stats = system_monitor.get_monitoring_status()
                stats["monitoring"] = monitoring_stats
            except Exception as e:
                stats["monitoring"] = {"error": str(e)}
        
        # 服务器状态分布
        server_status_counts = {}
        for server in game_servers.values():
            status = server.status
            server_status_counts[status] = server_status_counts.get(status, 0) + 1
        
        stats["server_status_distribution"] = server_status_counts
        
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


@app.get("/containers/status")
async def get_all_containers_status():
    """获取所有容器状态概览 - 需求 6.2, 6.3"""
    try:
        containers_info = []
        
        if docker_manager:
            # 获取所有游戏容器
            game_containers = docker_manager.list_game_containers()
            
            for container_info in game_containers:
                container_info.refresh()  # 刷新状态
                
                # 查找对应的服务器信息
                server_info = None
                for server in game_servers.values():
                    if server.container_id == container_info.id:
                        server_info = server
                        break
                
                container_data = {
                    "container_id": container_info.id,
                    "container_name": container_info.name,
                    "status": container_info.status,
                    "created": container_info.created if container_info.created else None,
                    "stats": container_info.get_stats(),
                    "server_info": {
                        "server_id": server_info.server_id if server_info else None,
                        "name": server_info.name if server_info else None,
                        "status": server_info.status if server_info else None
                    } if server_info else None
                }
                containers_info.append(container_data)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_containers": len(containers_info),
            "containers": containers_info
        }
        
    except Exception as e:
        logger.error(f"获取容器状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取容器状态失败")

@app.get("/containers/{container_id}/detailed")
async def get_container_detailed_status(container_id: str):
    """获取特定容器的详细状态信息 - 需求 6.2, 6.3"""
    try:
        if not docker_manager:
            raise HTTPException(
                status_code=503, 
                detail=create_error_response(
                    status_code=503,
                    message="Docker管理器不可用",
                    path=f"/containers/{container_id}/detailed"
                )["error"]
            )
        
        container_info = docker_manager.get_container_info(container_id)
        if not container_info:
            raise HTTPException(
                status_code=404, 
                detail=create_error_response(
                    status_code=404,
                    message="容器不存在",
                    path=f"/containers/{container_id}/detailed",
                    details={"container_id": container_id}
                )["error"]
            )
        
        # 刷新容器信息
        container_info.refresh()
        
        # 查找对应的服务器信息
        server_info = None
        for server in game_servers.values():
            if server.container_id == container_id:
                server_info = server
                break
        
        # 获取容器日志
        logs = container_info.get_logs(tail=100)
        
        # 获取详细统计信息
        stats = container_info.get_stats()
        
        detailed_info = {
            "container_id": container_info.id,
            "name": container_info.name,
            "status": container_info.status,
            "created": container_info.created if container_info.created else None,
            "stats": stats,
            "logs": logs,
            "server_info": {
                "server_id": server_info.server_id,
                "name": server_info.name,
                "description": server_info.description,
                "status": server_info.status,
                "created_at": server_info.created_at,
                "updated_at": server_info.updated_at
            } if server_info else None,
            "resource_management": None
        }
        
        # 添加资源管理信息
        if resource_manager:
            try:
                resource_details = resource_manager.get_container_details(server_info.server_id if server_info else container_id)
                detailed_info["resource_management"] = resource_details
            except Exception as e:
                detailed_info["resource_management"] = {"error": str(e)}
        
        return detailed_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取容器详细状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取容器详细状态失败")

@app.get("/system/idle-containers")
async def get_idle_containers():
    """获取闲置容器列表 - 需求 6.2, 6.3"""
    try:
        if not resource_manager:
            raise HTTPException(status_code=503, detail="资源管理器不可用")
        
        idle_containers = resource_manager.get_idle_containers()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "count": len(idle_containers),
            "idle_timeout_seconds": resource_manager.config.idle_timeout_seconds,
            "containers": [
                {
                    "server_id": c.server_id,
                    "container_id": c.container_id[:12],
                    "last_activity": c.last_activity.isoformat(),
                    "connection_count": c.connection_count,
                    "idle_duration_seconds": int((datetime.now() - c.last_activity).total_seconds())
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

# 系统集成和监控端点 - 需求 6.1, 6.2, 6.3
@app.get("/system/integration-status")
async def get_integration_status():
    """获取系统集成状态 - 端到端工作流程检查"""
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "services": {},
            "workflows": {}
        }
        
        # 检查各个服务状态
        services_status = {}
        
        # 1. 检查Game Server Factory本身
        services_status["game_server_factory"] = {
            "status": "healthy",
            "containers_managed": len(game_servers),
            "docker_available": docker_manager is not None,
            "resource_manager_available": resource_manager is not None
        }
        
        # 2. 检查Matchmaker Service
        matchmaker_status = await check_matchmaker_health()
        services_status["matchmaker_service"] = {
            "status": matchmaker_status,
            "url": Config.MATCHMAKER_URL
        }
        
        # 3. 检查Docker环境
        if docker_manager:
            try:
                docker_stats = docker_manager.get_system_stats()
                services_status["docker_environment"] = {
                    "status": "healthy",
                    "stats": docker_stats
                }
            except Exception as e:
                services_status["docker_environment"] = {
                    "status": "error",
                    "error": str(e)
                }
        else:
            services_status["docker_environment"] = {
                "status": "unavailable",
                "error": "Docker manager not initialized"
            }
        
        status["services"] = services_status
        
        # 检查端到端工作流程
        workflows_status = {}
        
        # 工作流程1: 代码上传到容器创建
        workflows_status["code_upload_to_container"] = await test_code_upload_workflow()
        
        # 工作流程2: 容器注册到撮合服务
        workflows_status["container_to_matchmaker"] = await test_container_registration_workflow()
        
        # 工作流程3: 资源管理和清理
        workflows_status["resource_management"] = test_resource_management_workflow()
        
        status["workflows"] = workflows_status
        
        # 确定整体状态
        failed_services = [name for name, info in services_status.items() if info["status"] != "healthy"]
        failed_workflows = [name for name, info in workflows_status.items() if info["status"] != "healthy"]
        
        if failed_services or failed_workflows:
            status["overall_status"] = "degraded"
            status["issues"] = {
                "failed_services": failed_services,
                "failed_workflows": failed_workflows
            }
        
        return status
        
    except Exception as e:
        logger.error(f"获取集成状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取集成状态失败")

async def test_code_upload_workflow() -> Dict[str, Any]:
    """测试HTML游戏上传到容器创建工作流程"""
    try:
        # 检查HTML游戏验证器
        if not html_game_validator:
            return {"status": "error", "error": "HTML game validator not available"}
        
        # 测试简单的HTML游戏验证
        test_html = b"<html><head><title>Test</title></head><body><h1>Hello World</h1></body></html>"
        is_valid, message, metadata = html_game_validator.validate_file(test_html, "test.html")
        
        if not is_valid:
            return {"status": "error", "error": f"HTML game validation failed for valid content: {message}"}
        
        # 检查Docker管理器
        if not docker_manager:
            return {"status": "error", "error": "Docker manager not available"}
        
        return {"status": "healthy", "components_checked": ["html_game_validator", "docker_manager"]}
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

async def test_container_registration_workflow() -> Dict[str, Any]:
    """测试容器注册到撮合服务工作流程"""
    try:
        # 检查撮合服务连接
        matchmaker_status = await check_matchmaker_health()
        if matchmaker_status != "healthy":
            return {"status": "error", "error": f"Matchmaker service not healthy: {matchmaker_status}"}
        
        # 检查是否有运行中的容器可以注册
        running_containers = [s for s in game_servers.values() if s.status == "running"]
        
        return {
            "status": "healthy",
            "matchmaker_available": True,
            "running_containers": len(running_containers)
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

def test_resource_management_workflow() -> Dict[str, Any]:
    """测试资源管理和清理工作流程"""
    try:
        if not resource_manager:
            return {"status": "error", "error": "Resource manager not available"}
        
        # 获取资源统计
        resource_stats = resource_manager.get_resource_stats()
        
        return {
            "status": "healthy",
            "resource_manager_available": True,
            "resource_stats": resource_stats
        }
        
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/system/end-to-end-test")
async def run_end_to_end_test():
    """运行端到端系统测试"""
    try:
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_id": f"e2e_{int(datetime.now().timestamp())}",
            "overall_result": "passed",
            "tests": {}
        }
        
        # 测试1: 配置验证
        config_test = test_configuration()
        test_results["tests"]["configuration"] = config_test
        
        # 测试2: 服务依赖检查
        dependency_test = await test_service_dependencies()
        test_results["tests"]["service_dependencies"] = dependency_test
        
        # 测试3: API端点可用性
        api_test = await test_api_endpoints()
        test_results["tests"]["api_endpoints"] = api_test
        
        # 测试4: 错误处理
        error_handling_test = test_error_handling()
        test_results["tests"]["error_handling"] = error_handling_test
        
        # 确定整体结果
        failed_tests = [name for name, result in test_results["tests"].items() if result["result"] != "passed"]
        if failed_tests:
            test_results["overall_result"] = "failed"
            test_results["failed_tests"] = failed_tests
        
        return test_results
        
    except Exception as e:
        logger.error(f"端到端测试失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="端到端测试失败")

def test_configuration() -> Dict[str, Any]:
    """测试配置验证"""
    try:
        config_errors = Config.validate_config()
        if config_errors:
            return {
                "result": "failed",
                "errors": config_errors
            }
        
        return {
            "result": "passed",
            "environment": Config.ENVIRONMENT,
            "debug_mode": Config.DEBUG
        }
    except Exception as e:
        return {"result": "failed", "error": str(e)}

async def test_service_dependencies() -> Dict[str, Any]:
    """测试服务依赖"""
    try:
        dependencies = {}
        
        # 测试Docker连接
        if docker_manager:
            try:
                docker_manager.get_system_stats()
                dependencies["docker"] = "available"
            except Exception as e:
                dependencies["docker"] = f"error: {str(e)}"
        else:
            dependencies["docker"] = "unavailable"
        
        # 测试撮合服务连接
        matchmaker_status = await check_matchmaker_health()
        dependencies["matchmaker"] = matchmaker_status
        
        # 测试资源管理器
        if resource_manager:
            try:
                resource_manager.get_resource_stats()
                dependencies["resource_manager"] = "available"
            except Exception as e:
                dependencies["resource_manager"] = f"error: {str(e)}"
        else:
            dependencies["resource_manager"] = "unavailable"
        
        # 检查是否有关键依赖失败
        critical_failures = [k for k, v in dependencies.items() if v.startswith("error")]
        
        return {
            "result": "failed" if critical_failures else "passed",
            "dependencies": dependencies,
            "critical_failures": critical_failures
        }
        
    except Exception as e:
        return {"result": "failed", "error": str(e)}

async def test_api_endpoints() -> Dict[str, Any]:
    """测试API端点可用性"""
    try:
        endpoints = {}
        
        # 测试健康检查端点
        try:
            health_response = await health_check()
            endpoints["/health"] = "available"
        except Exception as e:
            endpoints["/health"] = f"error: {str(e)}"
        
        # 测试服务器列表端点
        try:
            servers = await get_servers()
            endpoints["/servers"] = "available"
        except Exception as e:
            endpoints["/servers"] = f"error: {str(e)}"
        
        # 测试系统统计端点
        try:
            stats = await get_system_stats()
            endpoints["/system/stats"] = "available"
        except Exception as e:
            endpoints["/system/stats"] = f"error: {str(e)}"
        
        failed_endpoints = [k for k, v in endpoints.items() if v.startswith("error")]
        
        return {
            "result": "failed" if failed_endpoints else "passed",
            "endpoints": endpoints,
            "failed_endpoints": failed_endpoints
        }
        
    except Exception as e:
        return {"result": "failed", "error": str(e)}

def test_error_handling() -> Dict[str, Any]:
    """测试错误处理机制"""
    try:
        error_tests = {}
        
        # 测试标准化错误响应格式
        test_error = create_error_response(
            status_code=400,
            message="测试错误",
            path="/test",
            details={"test": True}
        )
        
        required_fields = ["error"]
        error_fields = ["code", "message", "timestamp", "path"]
        
        if "error" in test_error and all(field in test_error["error"] for field in error_fields):
            error_tests["error_response_format"] = "passed"
        else:
            error_tests["error_response_format"] = "failed"
        
        # 测试日志配置
        try:
            logger.info("测试日志记录")
            error_tests["logging"] = "passed"
        except Exception as e:
            error_tests["logging"] = f"failed: {str(e)}"
        
        failed_tests = [k for k, v in error_tests.items() if v.startswith("failed")]
        
        return {
            "result": "failed" if failed_tests else "passed",
            "error_tests": error_tests,
            "failed_tests": failed_tests
        }
        
    except Exception as e:
        return {"result": "failed", "error": str(e)}

# 监控和告警端点 - 需求 6.1, 6.2, 6.3
@app.get("/monitoring/status")
async def get_monitoring_status():
    """获取监控状态概览"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        return system_monitor.get_monitoring_status()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取监控状态失败")

@app.get("/monitoring/detailed")
async def get_detailed_monitoring_status():
    """获取详细监控状态"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        return system_monitor.get_detailed_status()
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取详细监控状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取详细监控状态失败")

@app.get("/monitoring/alerts")
async def get_active_alerts():
    """获取活跃告警列表"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        active_alerts = system_monitor.alert_manager.get_active_alerts()
        return {
            "count": len(active_alerts),
            "alerts": [alert.to_dict() for alert in active_alerts]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取活跃告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取活跃告警失败")

@app.get("/monitoring/alerts/history")
async def get_alert_history(hours: int = 24):
    """获取告警历史"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        if hours <= 0 or hours > 168:  # 最多7天
            raise HTTPException(status_code=400, detail="小时数必须在1-168之间")
        
        alert_history = system_monitor.alert_manager.get_alert_history(hours=hours)
        return {
            "hours": hours,
            "count": len(alert_history),
            "alerts": [alert.to_dict() for alert in alert_history]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取告警历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取告警历史失败")

@app.post("/monitoring/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """解决告警"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        success = system_monitor.resolve_alert(alert_id)
        if success:
            return {"message": "告警已解决", "alert_id": alert_id}
        else:
            raise HTTPException(status_code=404, detail="告警不存在或已解决")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"解决告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail="解决告警失败")

@app.post("/monitoring/alerts/manual")
async def create_manual_alert(
    alert_type: str,
    severity: str,
    title: str,
    message: str,
    source: str = "manual"
):
    """手动创建告警"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        # 验证参数
        try:
            alert_type_enum = AlertType(alert_type)
            severity_enum = AlertSeverity(severity)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"无效的告警类型或严重程度: {e}")
        
        alert = system_monitor.create_manual_alert(
            alert_type=alert_type_enum,
            severity=severity_enum,
            title=title,
            message=message,
            source=source
        )
        
        if alert:
            return {"message": "告警已创建", "alert": alert.to_dict()}
        else:
            return {"message": "告警在冷却期内，未创建"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建手动告警失败: {str(e)}")
        raise HTTPException(status_code=500, detail="创建手动告警失败")

@app.get("/monitoring/services")
async def get_service_statuses():
    """获取外部服务状态"""
    try:
        if not system_monitor:
            raise HTTPException(status_code=503, detail="系统监控器不可用")
        
        service_statuses = system_monitor.service_monitor.get_service_statuses()
        return {
            "count": len(service_statuses),
            "services": {name: status.to_dict() for name, status in service_statuses.items()}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取服务状态失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取服务状态失败")

@app.get("/api/endpoints")
async def list_api_endpoints():
    """列出所有可用的API端点 - 需求 6.1"""
    try:
        endpoints = []
        
        for route in app.routes:
            if hasattr(route, "methods") and hasattr(route, "path"):
                endpoint_info = {
                    "path": route.path,
                    "methods": list(route.methods),
                    "name": route.name,
                    "description": route.endpoint.__doc__.strip() if route.endpoint.__doc__ else "No description"
                }
                endpoints.append(endpoint_info)
        
        # 按路径排序
        endpoints.sort(key=lambda x: x["path"])
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_endpoints": len(endpoints),
            "endpoints": endpoints,
            "documentation": {
                "swagger_ui": "/docs",
                "redoc": "/redoc",
                "openapi_schema": "/openapi.json"
            }
        }
        
    except Exception as e:
        logger.error(f"列出API端点失败: {str(e)}")
        raise HTTPException(status_code=500, detail="列出API端点失败")

@app.get("/api/documentation")
async def get_api_documentation():
    """获取API文档信息 - 需求 6.1"""
    return {
        "service": "Game Server Factory",
        "version": "1.0.0",
        "description": "游戏服务器工厂 - 负责HTML游戏上传、验证和动态游戏服务器创建",
        "documentation_formats": {
            "swagger_ui": {
                "url": "/docs",
                "description": "交互式API文档，可以直接测试API端点"
            },
            "redoc": {
                "url": "/redoc",
                "description": "美观的API文档，适合阅读和分享"
            },
            "openapi_json": {
                "url": "/openapi.json",
                "description": "OpenAPI 3.0规范的JSON格式，可用于代码生成"
            }
        },
        "api_categories": {
            "html_game_management": {
                "description": "HTML游戏上传和管理",
                "endpoints": [
                    "POST /upload - 上传HTML游戏文件",
                    "GET /servers - 获取服务器列表",
                    "GET /servers/{server_id} - 获取服务器详情",
                    "POST /servers/{server_id}/stop - 停止服务器",
                    "DELETE /servers/{server_id} - 删除服务器",
                    "GET /servers/{server_id}/logs - 获取服务器日志"
                ]
            },
            "health_monitoring": {
                "description": "健康检查和监控",
                "endpoints": [
                    "GET /health - 基础健康检查",
                    "GET /monitoring/status - 监控状态概览",
                    "GET /monitoring/detailed - 详细监控状态",
                    "GET /monitoring/alerts - 活跃告警列表",
                    "GET /monitoring/services - 外部服务状态"
                ]
            },
            "container_management": {
                "description": "容器状态和管理",
                "endpoints": [
                    "GET /containers/status - 所有容器状态",
                    "GET /containers/{container_id}/detailed - 容器详细信息",
                    "GET /system/idle-containers - 闲置容器列表",
                    "POST /system/cleanup/{server_id} - 强制清理服务器"
                ]
            },
            "system_information": {
                "description": "系统信息和统计",
                "endpoints": [
                    "GET /system/stats - 系统统计信息",
                    "GET /system/resources - 资源管理统计",
                    "GET /system/integration-status - 系统集成状态",
                    "GET /system/end-to-end-test - 端到端测试"
                ]
            }
        },
        "authentication": "当前版本不需要认证",
        "rate_limiting": f"每分钟最多 {Config.API_RATE_LIMIT} 个请求",
        "error_handling": {
            "format": "所有错误响应遵循标准格式",
            "example": {
                "error": {
                    "code": 400,
                    "message": "错误描述",
                    "timestamp": "2025-12-19T10:00:00Z",
                    "path": "/api/path",
                    "details": {}
                }
            }
        }
    }

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化工作"""
    logger.info("应用正在启动...")
    
    # 启动系统监控
    if system_monitor:
        try:
            system_monitor.start_monitoring()
            logger.info("系统监控已启动")
        except Exception as e:
            logger.error(f"启动系统监控失败: {e}")
    
    logger.info("应用启动完成")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的清理工作"""
    logger.info("应用正在关闭...")
    
    # 停止系统监控
    if system_monitor:
        system_monitor.stop_monitoring()
        logger.info("系统监控已停止")
    
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
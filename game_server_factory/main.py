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

# 验证配置 - 需求 7.3
config_errors = Config.validate_config()
if config_errors:
    print("Configuration errors found:")
    for error in config_errors:
        print(f"  - {error}")
    exit(1)

# 配置增强日志系统 - 需求 8.1
import logging.handlers

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

# 增强配置管理 - 需求 7.3
class Config:
    """应用配置管理 - 支持环境适配和验证"""
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8080))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    
    # 文件上传配置
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 1024 * 1024))  # 1MB
    ALLOWED_EXTENSIONS = os.getenv("ALLOWED_EXTENSIONS", ".js,.mjs").split(",")
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

# 创建FastAPI应用
app = FastAPI(
    title="Game Server Factory",
    description="游戏服务器工厂 - 负责JavaScript代码上传、分析和动态游戏服务器创建",
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
    
    if details:
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
        
        # 确定整体健康状态
        overall_status = "healthy"
        if docker_status == "error" or resource_manager_status == "error":
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
                "matchmaker_service": matchmaker_status
            },
            "configuration": {
                "environment": Config.ENVIRONMENT,
                "max_containers": Config.MAX_CONTAINERS,
                "debug_mode": Config.DEBUG
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
        async with httpx.AsyncClient(timeout=Config.MATCHMAKER_TIMEOUT) as client:
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
    """测试代码上传到容器创建工作流程"""
    try:
        # 检查代码分析器
        if not code_analyzer:
            return {"status": "error", "error": "Code analyzer not available"}
        
        # 测试简单的代码分析
        test_code = "console.log('Hello World');"
        analysis_result = code_analyzer.analyze_code(test_code)
        
        if not analysis_result.is_valid:
            return {"status": "error", "error": "Code analysis failed for valid code"}
        
        # 检查Docker管理器
        if not docker_manager:
            return {"status": "error", "error": "Docker manager not available"}
        
        return {"status": "healthy", "components_checked": ["code_analyzer", "docker_manager"]}
        
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
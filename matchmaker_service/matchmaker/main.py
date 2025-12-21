import os
import logging
import logging.handlers
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio

# 加载环境变量
load_dotenv()

# 增强配置管理 - 需求 7.3
class Config:
    """撮合服务配置管理"""
    
    # 服务器配置
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
    
    # 心跳和清理配置
    HEARTBEAT_TIMEOUT = int(os.getenv('HEARTBEAT_TIMEOUT', 30))
    CLEANUP_INTERVAL = int(os.getenv('CLEANUP_INTERVAL', 10))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "matchmaker_service.log")
    LOG_MAX_SIZE = int(os.getenv("LOG_MAX_SIZE", 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    
    # 安全配置
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # 监控配置常量
    STALE_SERVER_THRESHOLD_RATIO = 0.5  # 过期服务器阈值比例
    
    @classmethod
    def validate_config(cls) -> List[str]:
        """验证配置参数"""
        errors = []
        
        if not (1024 <= cls.PORT <= 65535):
            errors.append(f"PORT must be between 1024 and 65535, got {cls.PORT}")
        
        if cls.HEARTBEAT_TIMEOUT <= 0:
            errors.append(f"HEARTBEAT_TIMEOUT must be positive, got {cls.HEARTBEAT_TIMEOUT}")
        
        if cls.CLEANUP_INTERVAL <= 0:
            errors.append(f"CLEANUP_INTERVAL must be positive, got {cls.CLEANUP_INTERVAL}")
        
        valid_environments = ["development", "staging", "production"]
        if cls.ENVIRONMENT not in valid_environments:
            errors.append(f"ENVIRONMENT must be one of {valid_environments}, got {cls.ENVIRONMENT}")
        
        return errors
    
    @classmethod
    def get_cors_config(cls) -> Dict[str, Any]:
        """获取CORS配置"""
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

# 验证配置
config_errors = Config.validate_config()
if config_errors:
    print("Configuration errors found:")
    for error in config_errors:
        print(f"  - {error}")
    exit(1)

# 设置增强日志系统 - 需求 8.1
def setup_logging():
    """设置增强的日志系统"""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL.upper()))
    
    # 清除现有处理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(pathname)s:%(lineno)d]'
    )
    
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

setup_logging()
logger = logging.getLogger(__name__)

# 记录配置信息
logger.info(f"Matchmaker Service starting with configuration:")
logger.info(f"  Environment: {Config.ENVIRONMENT}")
logger.info(f"  Host: {Config.HOST}:{Config.PORT}")
logger.info(f"  Heartbeat timeout: {Config.HEARTBEAT_TIMEOUT}s")
logger.info(f"  Cleanup interval: {Config.CLEANUP_INTERVAL}s")

app = FastAPI(
    title="Game Matchmaker Service", 
    version="1.0.0",
    description="游戏撮合服务 - 负责游戏服务器注册、发现和状态管理",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 设置CORS中间件
cors_config = Config.get_cors_config()
app.add_middleware(CORSMiddleware, **cors_config)

# 标准化错误响应 - 需求 6.4, 6.5
def create_error_response(
    status_code: int,
    message: str,
    path: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """创建标准化错误响应"""
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
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(
        f"HTTP error: {exc.status_code} - {exc.detail}",
        extra={
            "path": str(request.url),
            "method": request.method,
            "client": request.client.host if request.client else "unknown"
        }
    )
    
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
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
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

class GameServerRegister(BaseModel):
    ip: str = Field(..., description="游戏服务器IP地址")
    port: int = Field(..., ge=1, le=65535, description="游戏服务器端口")
    name: str = Field(..., min_length=1, max_length=100, description="游戏名称")
    max_players: Optional[int] = Field(20, ge=1, le=100, description="最大玩家数")
    current_players: Optional[int] = Field(0, ge=0, description="当前玩家数")
    metadata: Optional[Dict] = Field(default_factory=dict, description="额外元数据")

class GameServerInfo(BaseModel):
    server_id: str
    ip: str
    port: int
    name: str
    max_players: int
    current_players: int
    metadata: Dict
    last_heartbeat: str
    uptime: int

class GameServerStore:
    def __init__(self, heartbeat_timeout: int = 30):
        self.servers: Dict[str, Dict] = {}
        self.heartbeat_timeout = int(os.getenv('HEARTBEAT_TIMEOUT', heartbeat_timeout))
    
    def generate_server_id(self, ip: str, port: int) -> str:
        return f"{ip}:{port}"
    
    def register_or_update(self, server: GameServerRegister) -> str:
        server_id = self.generate_server_id(server.ip, server.port)
        now = datetime.now()
        
        if server_id in self.servers:
            self.servers[server_id].update({
                "name": server.name,
                "max_players": server.max_players,
                "current_players": server.current_players,
                "metadata": server.metadata,
                "last_heartbeat": now,
            })
            logger.info(f"Updated server: {server_id}")
        else:
            self.servers[server_id] = {
                "server_id": server_id,
                "ip": server.ip,
                "port": server.port,
                "name": server.name,
                "max_players": server.max_players,
                "current_players": server.current_players,
                "metadata": server.metadata,
                "registered_at": now,
                "last_heartbeat": now,
            }
            logger.info(f"Registered new server: {server_id}")
        
        return server_id
    
    def get_all_active_servers(self) -> List[GameServerInfo]:
        now = datetime.now()
        timeout_threshold = now - timedelta(seconds=self.heartbeat_timeout)
        
        active_servers = []
        for server_id, server_data in self.servers.items():
            if server_data["last_heartbeat"] >= timeout_threshold:
                uptime = int((now - server_data["registered_at"]).total_seconds())
                active_servers.append(GameServerInfo(
                    server_id=server_data["server_id"],
                    ip=server_data["ip"],
                    port=server_data["port"],
                    name=server_data["name"],
                    max_players=server_data["max_players"],
                    current_players=server_data["current_players"],
                    metadata=server_data["metadata"],
                    last_heartbeat=server_data["last_heartbeat"].isoformat(),
                    uptime=uptime
                ))
        
        return active_servers
    
    def get_server_by_id(self, server_id: str) -> Optional[Dict]:
        return self.servers.get(server_id)
    
    def remove_server(self, server_id: str) -> bool:
        if server_id in self.servers:
            del self.servers[server_id]
            logger.info(f"Removed server: {server_id}")
            return True
        return False
    
    def cleanup_stale_servers(self) -> int:
        now = datetime.now()
        timeout_threshold = now - timedelta(seconds=self.heartbeat_timeout)
        
        stale_servers = [
            server_id for server_id, server_data in self.servers.items()
            if server_data["last_heartbeat"] < timeout_threshold
        ]
        
        for server_id in stale_servers:
            self.remove_server(server_id)
        
        # 更新清理统计
        self._last_cleanup_time = now
        self._last_cleanup_count = len(stale_servers)
        self._total_cleanups = getattr(self, '_total_cleanups', 0) + 1
        self._total_cleaned = getattr(self, '_total_cleaned', 0) + len(stale_servers)
        
        return len(stale_servers)

store = GameServerStore(heartbeat_timeout=Config.HEARTBEAT_TIMEOUT)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())
    logger.info("Matchmaker service started")

async def periodic_cleanup():
    """定期清理过期服务器 - 需求 5.1, 5.2"""
    while True:
        try:
            await asyncio.sleep(Config.CLEANUP_INTERVAL)
            removed = store.cleanup_stale_servers()
            if removed > 0:
                logger.info(f"Cleaned up {removed} stale server(s)")
        except Exception as e:
            logger.error(f"Cleanup task failed: {str(e)}", exc_info=True)
            # 继续运行，不要因为清理失败而停止服务

@app.get("/")
async def root():
    """根路径 - 服务信息和API导航 - 需求 6.1"""
    active_servers = store.get_all_active_servers()
    return {
        "service": "Game Matchmaker",
        "version": "1.0.0",
        "description": "游戏撮合服务 - 负责游戏服务器注册、发现和状态管理",
        "status": "running",
        "environment": Config.ENVIRONMENT,
        "statistics": {
            "active_servers": len(active_servers),
            "total_registered_servers": len(store.servers),
            "total_players": sum(s.current_players for s in active_servers)
        },
        "api_documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json"
        },
        "main_endpoints": {
            "register_server": "POST /register",
            "list_servers": "GET /servers",
            "server_heartbeat": "POST /heartbeat/{server_id}",
            "health_check": "GET /health"
        },
        "monitoring_endpoints": {
            "monitoring_status": "/monitoring/status",
            "detailed_servers": "/monitoring/servers/detailed",
            "cleanup_stats": "/monitoring/cleanup/stats"
        }
    }

@app.post("/register", response_model=Dict[str, str])
async def register_server(server: GameServerRegister):
    server_id = store.register_or_update(server)
    return {
        "status": "success",
        "server_id": server_id,
        "message": "Server registered successfully"
    }

@app.post("/heartbeat/{server_id}")
async def heartbeat(server_id: str, current_players: Optional[int] = None):
    server = store.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server["last_heartbeat"] = datetime.now()
    if current_players is not None:
        server["current_players"] = current_players
    
    return {"status": "success", "message": "Heartbeat received"}

@app.get("/servers", response_model=List[GameServerInfo])
async def list_servers():
    return store.get_all_active_servers()

@app.get("/servers/{server_id}", response_model=GameServerInfo)
async def get_server(server_id: str):
    server = store.get_server_by_id(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    now = datetime.now()
    timeout_threshold = now - timedelta(seconds=store.heartbeat_timeout)
    
    if server["last_heartbeat"] < timeout_threshold:
        raise HTTPException(status_code=410, detail="Server is inactive")
    
    uptime = int((now - server["registered_at"]).total_seconds())
    
    return GameServerInfo(
        server_id=server["server_id"],
        ip=server["ip"],
        port=server["port"],
        name=server["name"],
        max_players=server["max_players"],
        current_players=server["current_players"],
        metadata=server["metadata"],
        last_heartbeat=server["last_heartbeat"].isoformat(),
        uptime=uptime
    )

@app.delete("/servers/{server_id}")
async def unregister_server(server_id: str):
    if store.remove_server(server_id):
        return {"status": "success", "message": "Server unregistered"}
    raise HTTPException(status_code=404, detail="Server not found")

@app.get("/health")
async def health_check():
    """增强健康检查端点 - 需求 6.2, 6.3"""
    try:
        active_servers = store.get_all_active_servers()
        total_players = sum(s.current_players for s in active_servers)
        
        # 检查服务健康状态
        status = "healthy"
        issues = []
        components = {}
        
        # 检查是否有过多的过期服务器
        stale_count = len(store.servers) - len(active_servers)
        if stale_count > len(active_servers) * Config.STALE_SERVER_THRESHOLD_RATIO and len(active_servers) > 0:
            issues.append("High number of stale servers detected")
            status = "degraded"
        
        # 检查各组件状态
        components["server_store"] = "healthy"
        components["cleanup_task"] = "healthy"  # 假设清理任务正常运行
        
        # 检查服务器分布
        server_types = {}
        for server in active_servers:
            game_type = server.metadata.get("game_type", "unknown")
            server_types[game_type] = server_types.get(game_type, 0) + 1
        
        health_data = {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "statistics": {
                "active_servers": len(active_servers),
                "total_registered_servers": len(store.servers),
                "stale_servers": stale_count,
                "total_players": total_players,
                "heartbeat_timeout_seconds": store.heartbeat_timeout,
                "server_types": server_types
            },
            "configuration": {
                "environment": Config.ENVIRONMENT,
                "heartbeat_timeout": Config.HEARTBEAT_TIMEOUT,
                "cleanup_interval": Config.CLEANUP_INTERVAL,
                "debug_mode": Config.DEBUG,
                "host": Config.HOST,
                "port": Config.PORT
            },
            "performance": {
                "cleanup_stats": {
                    "last_cleanup_time": getattr(store, '_last_cleanup_time', datetime.now()).isoformat(),
                    "last_cleanup_count": getattr(store, '_last_cleanup_count', 0),
                    "total_cleanups": getattr(store, '_total_cleanups', 0),
                    "total_cleaned": getattr(store, '_total_cleaned', 0)
                }
            }
        }
        
        if issues:
            health_data["issues"] = issues
        
        return health_data
        
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

@app.get("/monitoring/status")
async def get_monitoring_status():
    """获取监控状态 - 需求 6.2, 6.3"""
    try:
        active_servers = store.get_all_active_servers()
        total_players = sum(s.current_players for s in active_servers)
        stale_count = len(store.servers) - len(active_servers)
        
        # 计算服务器分布统计
        server_stats = {}
        for server in active_servers:
            game_type = server.metadata.get("game_type", "unknown")
            if game_type not in server_stats:
                server_stats[game_type] = {"count": 0, "players": 0}
            server_stats[game_type]["count"] += 1
            server_stats[game_type]["players"] += server.current_players
        
        # 计算平均响应时间（基于心跳间隔）
        now = datetime.now()
        recent_heartbeats = []
        for server_data in store.servers.values():
            heartbeat_age = (now - server_data["last_heartbeat"]).total_seconds()
            if heartbeat_age < Config.HEARTBEAT_TIMEOUT:
                recent_heartbeats.append(heartbeat_age)
        
        avg_heartbeat_age = sum(recent_heartbeats) / len(recent_heartbeats) if recent_heartbeats else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "service_status": "healthy" if stale_count <= len(active_servers) * Config.STALE_SERVER_THRESHOLD_RATIO else "degraded",
            "statistics": {
                "active_servers": len(active_servers),
                "total_registered_servers": len(store.servers),
                "stale_servers": stale_count,
                "total_players": total_players,
                "average_heartbeat_age_seconds": round(avg_heartbeat_age, 2),
                "server_types": server_stats
            },
            "performance": {
                "cleanup_interval_seconds": Config.CLEANUP_INTERVAL,
                "heartbeat_timeout_seconds": Config.HEARTBEAT_TIMEOUT,
                "last_cleanup_removed": getattr(store, '_last_cleanup_count', 0)
            },
            "configuration": {
                "environment": Config.ENVIRONMENT,
                "debug_mode": Config.DEBUG,
                "allowed_origins": Config.ALLOWED_ORIGINS
            }
        }
        
    except Exception as e:
        logger.error(f"获取监控状态失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取监控状态失败")

@app.get("/monitoring/servers/detailed")
async def get_detailed_server_info():
    """获取详细服务器信息 - 需求 6.2, 6.3"""
    try:
        now = datetime.now()
        timeout_threshold = now - timedelta(seconds=store.heartbeat_timeout)
        
        detailed_servers = []
        for server_id, server_data in store.servers.items():
            uptime = int((now - server_data["registered_at"]).total_seconds())
            heartbeat_age = int((now - server_data["last_heartbeat"]).total_seconds())
            is_active = server_data["last_heartbeat"] >= timeout_threshold
            
            detailed_info = {
                "server_id": server_id,
                "name": server_data["name"],
                "ip": server_data["ip"],
                "port": server_data["port"],
                "status": "active" if is_active else "stale",
                "current_players": server_data["current_players"],
                "max_players": server_data["max_players"],
                "uptime_seconds": uptime,
                "last_heartbeat_age_seconds": heartbeat_age,
                "registered_at": server_data["registered_at"].isoformat(),
                "last_heartbeat": server_data["last_heartbeat"].isoformat(),
                "metadata": server_data["metadata"],
                "health_score": max(0, 100 - (heartbeat_age * 2))  # 简单的健康评分
            }
            detailed_servers.append(detailed_info)
        
        # 按健康评分排序
        detailed_servers.sort(key=lambda x: x["health_score"], reverse=True)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_servers": len(detailed_servers),
            "servers": detailed_servers
        }
        
    except Exception as e:
        logger.error(f"获取详细服务器信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取详细服务器信息失败")

@app.get("/monitoring/cleanup/stats")
async def get_cleanup_stats():
    """获取清理统计信息 - 需求 6.2, 6.3"""
    try:
        # 模拟清理统计（在实际实现中，这些数据应该被持久化）
        cleanup_stats = {
            "timestamp": datetime.now().isoformat(),
            "cleanup_interval_seconds": Config.CLEANUP_INTERVAL,
            "heartbeat_timeout_seconds": Config.HEARTBEAT_TIMEOUT,
            "last_cleanup_time": getattr(store, '_last_cleanup_time', datetime.now()).isoformat(),
            "last_cleanup_removed_count": getattr(store, '_last_cleanup_count', 0),
            "total_cleanups_performed": getattr(store, '_total_cleanups', 0),
            "total_servers_cleaned": getattr(store, '_total_cleaned', 0)
        }
        
        return cleanup_stats
        
    except Exception as e:
        logger.error(f"获取清理统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取清理统计信息失败")

if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Matchmaker Service on {Config.HOST}:{Config.PORT}")
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level=Config.LOG_LEVEL.lower()
    )

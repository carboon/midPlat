import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import asyncio
import logging

# 加载环境变量
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Game Matchmaker Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
        
        return len(stale_servers)

store = GameServerStore(heartbeat_timeout=30)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(periodic_cleanup())
    logger.info("Matchmaker service started")

async def periodic_cleanup():
    cleanup_interval = int(os.getenv('CLEANUP_INTERVAL', 10))
    while True:
        await asyncio.sleep(cleanup_interval)
        removed = store.cleanup_stale_servers()
        if removed > 0:
            logger.info(f"Cleaned up {removed} stale server(s)")

@app.get("/")
async def root():
    return {
        "service": "Game Matchmaker",
        "version": "1.0.0",
        "status": "running",
        "active_servers": len(store.get_all_active_servers())
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
    """健康检查端点 - 返回服务状态和基本统计信息"""
    active_servers = store.get_all_active_servers()
    total_players = sum(s.current_players for s in active_servers)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "statistics": {
            "active_servers": len(active_servers),
            "total_registered_servers": len(store.servers),
            "total_players": total_players,
            "heartbeat_timeout_seconds": store.heartbeat_timeout
        }
    }

if __name__ == "__main__":
    import uvicorn
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)

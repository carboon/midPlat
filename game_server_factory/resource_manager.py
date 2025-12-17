"""
资源管理器
负责系统资源监控、闲置容器自动停止、资源限制和异常处理
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading
import time

logger = logging.getLogger(__name__)


class ContainerState(Enum):
    """容器状态枚举"""
    RUNNING = "running"
    STOPPED = "stopped"
    IDLE = "idle"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class ContainerActivity:
    """容器活动记录"""
    container_id: str
    server_id: str
    last_activity: datetime = field(default_factory=datetime.now)
    connection_count: int = 0
    cpu_usage: float = 0.0
    memory_usage_mb: float = 0.0
    is_idle: bool = False
    error_count: int = 0
    last_error: Optional[str] = None


@dataclass
class ResourceLimits:
    """资源限制配置"""
    max_containers: int = 50
    max_cpu_percent: float = 80.0
    max_memory_percent: float = 80.0
    idle_timeout_seconds: int = 1800  # 30分钟
    max_error_count: int = 5
    cleanup_interval_seconds: int = 60


class ResourceManager:
    """资源管理器 - 负责监控和管理系统资源"""
    
    def __init__(self, docker_manager=None, config: Optional[ResourceLimits] = None):
        """
        初始化资源管理器
        
        Args:
            docker_manager: Docker管理器实例
            config: 资源限制配置
        """
        self.docker_manager = docker_manager
        self.config = config or ResourceLimits()
        
        # 从环境变量加载配置
        self._load_config_from_env()
        
        # 容器活动跟踪
        self.container_activities: Dict[str, ContainerActivity] = {}
        
        # 回调函数
        self._on_container_stopped: Optional[Callable[[str, str], None]] = None
        self._on_container_error: Optional[Callable[[str, str, str], None]] = None
        
        # 后台任务控制
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        
        logger.info(f"资源管理器初始化完成，配置: max_containers={self.config.max_containers}, "
                   f"idle_timeout={self.config.idle_timeout_seconds}s")
    
    def _load_config_from_env(self):
        """从环境变量加载配置"""
        self.config.max_containers = int(os.getenv("MAX_CONTAINERS", self.config.max_containers))
        self.config.max_cpu_percent = float(os.getenv("MAX_CPU_PERCENT", self.config.max_cpu_percent))
        self.config.max_memory_percent = float(os.getenv("MAX_MEMORY_PERCENT", self.config.max_memory_percent))
        self.config.idle_timeout_seconds = int(os.getenv("IDLE_TIMEOUT_SECONDS", self.config.idle_timeout_seconds))
        self.config.max_error_count = int(os.getenv("MAX_ERROR_COUNT", self.config.max_error_count))
        self.config.cleanup_interval_seconds = int(os.getenv("CLEANUP_INTERVAL_SECONDS", self.config.cleanup_interval_seconds))
    
    def set_callbacks(
        self,
        on_container_stopped: Optional[Callable[[str, str], None]] = None,
        on_container_error: Optional[Callable[[str, str, str], None]] = None
    ):
        """
        设置回调函数
        
        Args:
            on_container_stopped: 容器停止时的回调 (server_id, reason)
            on_container_error: 容器错误时的回调 (server_id, container_id, error)
        """
        self._on_container_stopped = on_container_stopped
        self._on_container_error = on_container_error
    
    def register_container(self, server_id: str, container_id: str):
        """
        注册容器到资源管理器
        
        Args:
            server_id: 服务器ID
            container_id: 容器ID
        """
        with self._lock:
            self.container_activities[server_id] = ContainerActivity(
                container_id=container_id,
                server_id=server_id,
                last_activity=datetime.now()
            )
        logger.info(f"容器已注册到资源管理器: {server_id} -> {container_id[:12]}")
    
    def unregister_container(self, server_id: str):
        """
        从资源管理器注销容器
        
        Args:
            server_id: 服务器ID
        """
        with self._lock:
            if server_id in self.container_activities:
                del self.container_activities[server_id]
                logger.info(f"容器已从资源管理器注销: {server_id}")
    
    def update_activity(self, server_id: str, connection_count: int = 0):
        """
        更新容器活动状态
        
        Args:
            server_id: 服务器ID
            connection_count: 当前连接数
        """
        with self._lock:
            if server_id in self.container_activities:
                activity = self.container_activities[server_id]
                activity.last_activity = datetime.now()
                activity.connection_count = connection_count
                activity.is_idle = False
    
    def _record_error_unlocked(self, server_id: str, error_message: str):
        """
        记录容器错误（内部方法，不加锁）
        
        Args:
            server_id: 服务器ID
            error_message: 错误信息
        """
        if server_id in self.container_activities:
            activity = self.container_activities[server_id]
            activity.error_count += 1
            activity.last_error = error_message
            logger.warning(f"容器错误记录: {server_id}, 错误次数: {activity.error_count}, 错误: {error_message}")
    
    def record_error(self, server_id: str, error_message: str):
        """
        记录容器错误
        
        Args:
            server_id: 服务器ID
            error_message: 错误信息
        """
        with self._lock:
            self._record_error_unlocked(server_id, error_message)
    
    def can_create_container(self) -> tuple[bool, str]:
        """
        检查是否可以创建新容器
        
        Returns:
            (can_create, reason): 是否可以创建及原因
        """
        # 检查容器数量限制
        current_count = len(self.container_activities)
        if current_count >= self.config.max_containers:
            return False, f"已达到最大容器数量限制 ({self.config.max_containers})"
        
        # 检查系统资源
        if self.docker_manager:
            try:
                stats = self.docker_manager.get_system_stats()
                # 这里可以添加更多的资源检查逻辑
            except Exception as e:
                logger.warning(f"获取系统统计信息失败: {e}")
        
        return True, "可以创建容器"
    
    def _get_idle_containers_unlocked(self) -> List[ContainerActivity]:
        """
        获取闲置容器列表（内部方法，不加锁）
        
        Returns:
            闲置容器活动记录列表
        """
        idle_containers = []
        now = datetime.now()
        idle_threshold = timedelta(seconds=self.config.idle_timeout_seconds)
        
        for activity in self.container_activities.values():
            time_since_activity = now - activity.last_activity
            if time_since_activity > idle_threshold and activity.connection_count == 0:
                activity.is_idle = True
                idle_containers.append(activity)
        
        return idle_containers
    
    def get_idle_containers(self) -> List[ContainerActivity]:
        """
        获取闲置容器列表
        
        Returns:
            闲置容器活动记录列表
        """
        with self._lock:
            return self._get_idle_containers_unlocked()
    
    def _get_error_containers_unlocked(self) -> List[ContainerActivity]:
        """
        获取错误次数过多的容器列表（内部方法，不加锁）
        
        Returns:
            错误容器活动记录列表
        """
        error_containers = []
        
        for activity in self.container_activities.values():
            if activity.error_count >= self.config.max_error_count:
                error_containers.append(activity)
        
        return error_containers
    
    def get_error_containers(self) -> List[ContainerActivity]:
        """
        获取错误次数过多的容器列表
        
        Returns:
            错误容器活动记录列表
        """
        with self._lock:
            return self._get_error_containers_unlocked()
    
    def _update_container_stats(self):
        """更新所有容器的资源使用统计"""
        if not self.docker_manager:
            return
        
        with self._lock:
            for server_id, activity in list(self.container_activities.items()):
                try:
                    container_info = self.docker_manager.get_container_info(activity.container_id)
                    if container_info:
                        container_info.refresh()
                        
                        # 检查容器状态
                        if container_info.status != 'running':
                            logger.warning(f"容器状态异常: {server_id} -> {container_info.status}")
                            self._record_error_unlocked(server_id, f"容器状态异常: {container_info.status}")
                            continue
                        
                        # 获取资源使用统计
                        stats = container_info.get_stats()
                        if stats:
                            activity.cpu_usage = stats.get('cpu_percent', 0.0)
                            activity.memory_usage_mb = stats.get('memory_usage_mb', 0.0)
                    else:
                        # 容器不存在
                        logger.warning(f"容器不存在: {server_id} -> {activity.container_id}")
                        self._record_error_unlocked(server_id, "容器不存在")
                        
                except Exception as e:
                    logger.error(f"更新容器统计失败: {server_id} - {e}")
                    self._record_error_unlocked(server_id, str(e))
    
    def _stop_idle_containers(self) -> List[str]:
        """
        停止闲置容器
        
        Returns:
            已停止的服务器ID列表
        """
        stopped_servers = []
        idle_containers = self.get_idle_containers()
        
        for activity in idle_containers:
            try:
                logger.info(f"停止闲置容器: {activity.server_id} (闲置时间超过 {self.config.idle_timeout_seconds}s)")
                
                if self.docker_manager:
                    success = self.docker_manager.stop_container(activity.container_id)
                    if success:
                        stopped_servers.append(activity.server_id)
                        
                        # 触发回调
                        if self._on_container_stopped:
                            self._on_container_stopped(activity.server_id, "idle_timeout")
                        
                        logger.info(f"闲置容器已停止: {activity.server_id}")
                    else:
                        logger.error(f"停止闲置容器失败: {activity.server_id}")
                        
            except Exception as e:
                logger.error(f"停止闲置容器异常: {activity.server_id} - {e}")
        
        return stopped_servers
    
    def _cleanup_error_containers(self) -> List[str]:
        """
        清理错误容器
        
        Returns:
            已清理的服务器ID列表
        """
        cleaned_servers = []
        error_containers = self.get_error_containers()
        
        for activity in error_containers:
            try:
                logger.info(f"清理错误容器: {activity.server_id} (错误次数: {activity.error_count})")
                
                if self.docker_manager:
                    # 先停止容器
                    self.docker_manager.stop_container(activity.container_id)
                    
                    # 触发回调
                    if self._on_container_error:
                        self._on_container_error(
                            activity.server_id,
                            activity.container_id,
                            activity.last_error or "错误次数过多"
                        )
                    
                    cleaned_servers.append(activity.server_id)
                    logger.info(f"错误容器已清理: {activity.server_id}")
                    
            except Exception as e:
                logger.error(f"清理错误容器异常: {activity.server_id} - {e}")
        
        return cleaned_servers
    
    def _check_exited_containers(self) -> List[str]:
        """
        检查并处理异常退出的容器
        
        Returns:
            异常退出的服务器ID列表
        """
        exited_servers = []
        
        if not self.docker_manager:
            return exited_servers
        
        with self._lock:
            for server_id, activity in list(self.container_activities.items()):
                try:
                    container_info = self.docker_manager.get_container_info(activity.container_id)
                    
                    if container_info is None:
                        # 容器已被删除
                        logger.warning(f"容器已被外部删除: {server_id}")
                        exited_servers.append(server_id)
                        
                        if self._on_container_error:
                            self._on_container_error(server_id, activity.container_id, "容器已被外部删除")
                        continue
                    
                    container_info.refresh()
                    
                    if container_info.status == 'exited':
                        # 容器异常退出
                        logger.warning(f"容器异常退出: {server_id}")
                        exited_servers.append(server_id)
                        
                        # 获取退出日志
                        logs = container_info.get_logs(tail=10)
                        error_msg = f"容器异常退出，最后日志: {logs[-1] if logs else '无'}"
                        
                        if self._on_container_error:
                            self._on_container_error(server_id, activity.container_id, error_msg)
                            
                except Exception as e:
                    logger.error(f"检查容器状态失败: {server_id} - {e}")
        
        return exited_servers
    
    def _monitor_loop(self):
        """监控循环"""
        logger.info("资源监控循环已启动")
        
        while self._running:
            try:
                # 更新容器统计
                self._update_container_stats()
                
                # 检查异常退出的容器
                exited = self._check_exited_containers()
                if exited:
                    logger.info(f"检测到 {len(exited)} 个异常退出的容器")
                
                # 停止闲置容器
                stopped = self._stop_idle_containers()
                if stopped:
                    logger.info(f"已停止 {len(stopped)} 个闲置容器")
                
                # 清理错误容器
                cleaned = self._cleanup_error_containers()
                if cleaned:
                    logger.info(f"已清理 {len(cleaned)} 个错误容器")
                
            except Exception as e:
                logger.error(f"监控循环异常: {e}")
            
            # 等待下一次检查
            time.sleep(self.config.cleanup_interval_seconds)
        
        logger.info("资源监控循环已停止")
    
    def start_monitoring(self):
        """启动资源监控"""
        if self._running:
            logger.warning("资源监控已在运行中")
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("资源监控已启动")
    
    def stop_monitoring(self):
        """停止资源监控"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
            self._monitor_thread = None
        logger.info("资源监控已停止")
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """
        获取资源统计信息
        
        Returns:
            资源统计字典
        """
        with self._lock:
            total_containers = len(self.container_activities)
            idle_containers = len(self._get_idle_containers_unlocked())
            error_containers = len(self._get_error_containers_unlocked())
            
            total_cpu = sum(a.cpu_usage for a in self.container_activities.values())
            total_memory = sum(a.memory_usage_mb for a in self.container_activities.values())
            
            return {
                "timestamp": datetime.now().isoformat(),
                "total_containers": total_containers,
                "idle_containers": idle_containers,
                "error_containers": error_containers,
                "max_containers": self.config.max_containers,
                "total_cpu_usage": round(total_cpu, 2),
                "total_memory_usage_mb": round(total_memory, 2),
                "idle_timeout_seconds": self.config.idle_timeout_seconds,
                "monitoring_active": self._running
            }
    
    def get_container_details(self, server_id: str) -> Optional[Dict[str, Any]]:
        """
        获取容器详细信息
        
        Args:
            server_id: 服务器ID
            
        Returns:
            容器详细信息字典
        """
        with self._lock:
            if server_id not in self.container_activities:
                return None
            
            activity = self.container_activities[server_id]
            now = datetime.now()
            idle_time = (now - activity.last_activity).total_seconds()
            
            return {
                "server_id": activity.server_id,
                "container_id": activity.container_id,
                "last_activity": activity.last_activity.isoformat(),
                "idle_time_seconds": round(idle_time, 2),
                "connection_count": activity.connection_count,
                "cpu_usage": activity.cpu_usage,
                "memory_usage_mb": activity.memory_usage_mb,
                "is_idle": activity.is_idle,
                "error_count": activity.error_count,
                "last_error": activity.last_error
            }
    
    def force_cleanup(self, server_id: str) -> bool:
        """
        强制清理指定服务器的资源
        
        Args:
            server_id: 服务器ID
            
        Returns:
            是否成功清理
        """
        with self._lock:
            if server_id not in self.container_activities:
                return False
            
            activity = self.container_activities[server_id]
        
        try:
            if self.docker_manager:
                # 停止并删除容器
                self.docker_manager.stop_container(activity.container_id)
                self.docker_manager.cleanup_server_resources(server_id)
            
            # 从活动记录中移除
            self.unregister_container(server_id)
            
            logger.info(f"强制清理完成: {server_id}")
            return True
            
        except Exception as e:
            logger.error(f"强制清理失败: {server_id} - {e}")
            return False

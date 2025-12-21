"""
监控和告警系统 - 需求 6.1, 6.2, 6.3
实现服务状态监控和告警机制
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import httpx

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """告警严重程度"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertType(Enum):
    """告警类型"""
    SERVICE_DOWN = "service_down"
    SERVICE_DEGRADED = "service_degraded"
    HIGH_RESOURCE_USAGE = "high_resource_usage"
    CONTAINER_FAILURE = "container_failure"
    HEALTH_CHECK_FAILED = "health_check_failed"
    EXTERNAL_SERVICE_UNAVAILABLE = "external_service_unavailable"


@dataclass
class Alert:
    """告警信息"""
    id: str
    type: AlertType
    severity: AlertSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        data['type'] = self.type.value
        data['severity'] = self.severity.value
        return data


@dataclass
class ServiceStatus:
    """服务状态"""
    name: str
    url: str
    status: str  # healthy, degraded, down
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    consecutive_failures: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        data = asdict(self)
        data['last_check'] = self.last_check.isoformat()
        return data


class MonitoringConfig:
    """监控配置"""
    
    def __init__(self):
        # 健康检查配置
        self.health_check_interval = 30  # 秒
        self.health_check_timeout = 10   # 秒
        self.max_consecutive_failures = 3
        
        # 告警配置
        self.alert_cooldown_minutes = 5  # 相同告警的冷却时间
        self.max_alerts_per_hour = 20    # 每小时最大告警数
        
        # 监控的外部服务
        self.external_services = {
            "matchmaker": "http://localhost:8000/health"
        }
        
        # 资源使用率阈值
        self.cpu_threshold_warning = 80.0    # CPU使用率警告阈值
        self.cpu_threshold_critical = 95.0   # CPU使用率严重阈值
        self.memory_threshold_warning = 80.0  # 内存使用率警告阈值
        self.memory_threshold_critical = 95.0 # 内存使用率严重阈值
        
        # 容器监控配置
        self.container_check_interval = 60   # 容器检查间隔（秒）
        self.max_container_restart_attempts = 3


class AlertManager:
    """告警管理器"""
    
    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.alert_callbacks: List[Callable[[Alert], None]] = []
        self.alert_cooldowns: Dict[str, datetime] = {}
        self._lock = threading.Lock()
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加告警回调函数"""
        self.alert_callbacks.append(callback)
    
    def create_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """创建告警"""
        
        # 检查冷却时间
        cooldown_key = f"{alert_type.value}:{source}"
        now = datetime.now()
        
        with self._lock:
            if cooldown_key in self.alert_cooldowns:
                cooldown_end = self.alert_cooldowns[cooldown_key] + timedelta(
                    minutes=self.config.alert_cooldown_minutes
                )
                if now < cooldown_end:
                    logger.debug(f"Alert {cooldown_key} is in cooldown period")
                    return None
            
            # 检查每小时告警限制
            recent_alerts = [
                alert for alert in self.alert_history
                if alert.timestamp > now - timedelta(hours=1)
            ]
            if len(recent_alerts) >= self.config.max_alerts_per_hour:
                logger.warning("Alert rate limit exceeded, skipping alert")
                return None
            
            # 创建告警
            alert_id = f"{alert_type.value}_{source}_{int(now.timestamp())}"
            alert = Alert(
                id=alert_id,
                type=alert_type,
                severity=severity,
                title=title,
                message=message,
                source=source,
                timestamp=now,
                metadata=metadata or {}
            )
            
            # 存储告警
            self.alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.alert_cooldowns[cooldown_key] = now
            
            # 触发回调
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")
            
            logger.warning(f"Alert created: {alert.title} - {alert.message}")
            return alert
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert.title}")
                return True
            return False
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """获取告警历史"""
        cutoff = datetime.now() - timedelta(hours=hours)
        with self._lock:
            return [alert for alert in self.alert_history if alert.timestamp > cutoff]
    
    def clear_resolved_alerts(self):
        """清理已解决的告警"""
        with self._lock:
            self.alerts = {
                alert_id: alert for alert_id, alert in self.alerts.items()
                if not alert.resolved
            }


class ServiceMonitor:
    """服务监控器"""
    
    def __init__(self, config: MonitoringConfig, alert_manager: AlertManager):
        self.config = config
        self.alert_manager = alert_manager
        self.service_statuses: Dict[str, ServiceStatus] = {}
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = threading.Lock()
    
    async def check_service_health(self, name: str, url: str) -> ServiceStatus:
        """检查单个服务健康状态"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient(timeout=self.config.health_check_timeout) as client:
                response = await client.get(url)
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    status = ServiceStatus(
                        name=name,
                        url=url,
                        status="healthy",
                        last_check=datetime.now(),
                        response_time_ms=response_time,
                        consecutive_failures=0
                    )
                else:
                    status = ServiceStatus(
                        name=name,
                        url=url,
                        status="degraded",
                        last_check=datetime.now(),
                        response_time_ms=response_time,
                        error_message=f"HTTP {response.status_code}",
                        consecutive_failures=self.service_statuses.get(name, ServiceStatus(name, url, "unknown", datetime.now())).consecutive_failures + 1
                    )
                    
        except Exception as e:
            status = ServiceStatus(
                name=name,
                url=url,
                status="down",
                last_check=datetime.now(),
                error_message=str(e),
                consecutive_failures=self.service_statuses.get(name, ServiceStatus(name, url, "unknown", datetime.now())).consecutive_failures + 1
            )
        
        # 检查是否需要发送告警
        await self._check_service_alerts(status)
        
        return status
    
    async def _check_service_alerts(self, status: ServiceStatus):
        """检查服务告警条件"""
        previous_status = self.service_statuses.get(status.name)
        
        # 服务从健康变为不健康
        if previous_status and previous_status.status == "healthy" and status.status != "healthy":
            severity = AlertSeverity.HIGH if status.status == "down" else AlertSeverity.MEDIUM
            alert_type = AlertType.SERVICE_DOWN if status.status == "down" else AlertType.SERVICE_DEGRADED
            
            self.alert_manager.create_alert(
                alert_type=alert_type,
                severity=severity,
                title=f"Service {status.name} is {status.status}",
                message=f"Service {status.name} at {status.url} is {status.status}. Error: {status.error_message}",
                source=status.name,
                metadata={
                    "url": status.url,
                    "consecutive_failures": status.consecutive_failures,
                    "response_time_ms": status.response_time_ms
                }
            )
        
        # 连续失败次数过多
        elif status.consecutive_failures >= self.config.max_consecutive_failures:
            self.alert_manager.create_alert(
                alert_type=AlertType.HEALTH_CHECK_FAILED,
                severity=AlertSeverity.CRITICAL,
                title=f"Service {status.name} health check failed repeatedly",
                message=f"Service {status.name} has failed {status.consecutive_failures} consecutive health checks",
                source=status.name,
                metadata={
                    "url": status.url,
                    "consecutive_failures": status.consecutive_failures,
                    "last_error": status.error_message
                }
            )
        
        # 服务恢复
        elif previous_status and previous_status.status != "healthy" and status.status == "healthy":
            # 解决相关告警
            for alert in self.alert_manager.get_active_alerts():
                if alert.source == status.name and alert.type in [AlertType.SERVICE_DOWN, AlertType.SERVICE_DEGRADED, AlertType.HEALTH_CHECK_FAILED]:
                    self.alert_manager.resolve_alert(alert.id)
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info("Service monitoring started")
        
        while self._running:
            try:
                # 检查所有配置的外部服务
                for name, url in self.config.external_services.items():
                    status = await self.check_service_health(name, url)
                    with self._lock:
                        self.service_statuses[name] = status
                
                # 等待下次检查
                await asyncio.sleep(self.config.health_check_interval)
                
            except Exception as e:
                logger.error(f"Service monitoring loop error: {e}")
                await asyncio.sleep(5)  # 短暂等待后重试
        
        logger.info("Service monitoring stopped")
    
    def start_monitoring(self):
        """启动服务监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Service monitoring task created")
    
    def stop_monitoring(self):
        """停止服务监控"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            self._monitor_task = None
        logger.info("Service monitoring stopped")
    
    def get_service_statuses(self) -> Dict[str, ServiceStatus]:
        """获取所有服务状态"""
        with self._lock:
            return self.service_statuses.copy()


class SystemMonitor:
    """系统监控器 - 整合所有监控功能"""
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        self.config = config or MonitoringConfig()
        self.alert_manager = AlertManager(self.config)
        self.service_monitor = ServiceMonitor(self.config, self.alert_manager)
        
        # 设置默认告警回调
        self.alert_manager.add_alert_callback(self._log_alert)
    
    def _log_alert(self, alert: Alert):
        """默认告警回调 - 记录到日志"""
        log_level = {
            AlertSeverity.LOW: logging.INFO,
            AlertSeverity.MEDIUM: logging.WARNING,
            AlertSeverity.HIGH: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.WARNING)
        
        logger.log(log_level, f"ALERT [{alert.severity.value.upper()}] {alert.title}: {alert.message}")
    
    def start_monitoring(self):
        """启动所有监控"""
        self.service_monitor.start_monitoring()
        logger.info("System monitoring started")
    
    def stop_monitoring(self):
        """停止所有监控"""
        self.service_monitor.stop_monitoring()
        logger.info("System monitoring stopped")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态概览"""
        active_alerts = self.alert_manager.get_active_alerts()
        service_statuses = self.service_monitor.get_service_statuses()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_active": self.service_monitor._running,
            "active_alerts_count": len(active_alerts),
            "services_monitored": len(service_statuses),
            "services_healthy": len([s for s in service_statuses.values() if s.status == "healthy"]),
            "services_degraded": len([s for s in service_statuses.values() if s.status == "degraded"]),
            "services_down": len([s for s in service_statuses.values() if s.status == "down"]),
            "alert_rate_limit_remaining": max(0, self.config.max_alerts_per_hour - len(self.alert_manager.get_alert_history(hours=1)))
        }
    
    def get_detailed_status(self) -> Dict[str, Any]:
        """获取详细监控状态"""
        return {
            "monitoring_status": self.get_monitoring_status(),
            "active_alerts": [alert.to_dict() for alert in self.alert_manager.get_active_alerts()],
            "service_statuses": {name: status.to_dict() for name, status in self.service_monitor.get_service_statuses().items()},
            "alert_history": [alert.to_dict() for alert in self.alert_manager.get_alert_history(hours=24)],
            "configuration": {
                "health_check_interval": self.config.health_check_interval,
                "health_check_timeout": self.config.health_check_timeout,
                "max_consecutive_failures": self.config.max_consecutive_failures,
                "alert_cooldown_minutes": self.config.alert_cooldown_minutes,
                "max_alerts_per_hour": self.config.max_alerts_per_hour
            }
        }
    
    def create_manual_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        title: str,
        message: str,
        source: str = "manual",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Alert]:
        """手动创建告警"""
        return self.alert_manager.create_alert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            source=source,
            metadata=metadata
        )
    
    def resolve_alert(self, alert_id: str) -> bool:
        """解决告警"""
        return self.alert_manager.resolve_alert(alert_id)
    
    def add_alert_callback(self, callback: Callable[[Alert], None]):
        """添加自定义告警回调"""
        self.alert_manager.add_alert_callback(callback)
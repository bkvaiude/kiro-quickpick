"""Database monitoring service for tracking performance metrics over time."""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import deque
from dataclasses import dataclass, asdict

from app.database.health import health_checker
from app.database.manager import database_manager

logger = logging.getLogger(__name__)


@dataclass
class MetricSnapshot:
    """Represents a point-in-time snapshot of database metrics."""
    timestamp: datetime
    healthy: bool
    response_time_seconds: float
    connection_pool_utilization: float
    active_connections: Optional[int] = None
    total_connections: Optional[int] = None
    database_size: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class DatabaseMonitoringService:
    """Service for monitoring database performance and health over time."""
    
    def __init__(self, max_snapshots: int = 100):
        self.max_snapshots = max_snapshots
        self._snapshots: deque = deque(maxlen=max_snapshots)
        self._monitoring_task: Optional[asyncio.Task] = None
        self._monitoring_interval = 60  # seconds
        self._is_monitoring = False
    
    async def start_monitoring(self, interval_seconds: int = 60):
        """Start continuous monitoring of database metrics."""
        if self._is_monitoring:
            logger.warning("Database monitoring is already running")
            return
        
        self._monitoring_interval = interval_seconds
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Started database monitoring with {interval_seconds}s interval")
    
    async def stop_monitoring(self):
        """Stop continuous monitoring."""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped database monitoring")
    
    async def _monitoring_loop(self):
        """Main monitoring loop that collects metrics periodically."""
        while self._is_monitoring:
            try:
                await self.collect_snapshot()
                await asyncio.sleep(self._monitoring_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self._monitoring_interval)
    
    async def collect_snapshot(self) -> MetricSnapshot:
        """Collect a single snapshot of current database metrics."""
        try:
            # Get health check results
            health_result = await health_checker.check_health()
            
            # Get connection pool metrics
            pool_metrics = await health_checker.get_connection_pool_metrics()
            
            # Get performance metrics
            performance_metrics = await health_checker.get_performance_metrics()
            
            # Extract relevant values
            utilization = pool_metrics.get("utilization_percent", 0.0)
            metrics_data = performance_metrics.get("metrics", {})
            
            snapshot = MetricSnapshot(
                timestamp=datetime.now(timezone.utc),
                healthy=health_result["healthy"],
                response_time_seconds=health_result["check_duration_seconds"],
                connection_pool_utilization=utilization,
                active_connections=metrics_data.get("active_connections"),
                total_connections=metrics_data.get("total_connections"),
                database_size=metrics_data.get("database_size")
            )
            
            # Store the snapshot
            self._snapshots.append(snapshot)
            
            # Log warning if metrics indicate issues
            if not snapshot.healthy:
                logger.warning(f"Database health check failed: response_time={snapshot.response_time_seconds}s")
            elif snapshot.connection_pool_utilization > 80:
                logger.warning(f"High connection pool utilization: {snapshot.connection_pool_utilization}%")
            elif snapshot.response_time_seconds > 1.0:
                logger.warning(f"Slow database response: {snapshot.response_time_seconds}s")
            
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to collect database snapshot: {e}")
            # Create a failed snapshot
            snapshot = MetricSnapshot(
                timestamp=datetime.now(timezone.utc),
                healthy=False,
                response_time_seconds=0.0,
                connection_pool_utilization=0.0
            )
            self._snapshots.append(snapshot)
            return snapshot
    
    def get_recent_snapshots(self, minutes: int = 60) -> List[MetricSnapshot]:
        """Get snapshots from the last N minutes."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        return [
            snapshot for snapshot in self._snapshots
            if snapshot.timestamp >= cutoff_time
        ]
    
    def get_all_snapshots(self) -> List[MetricSnapshot]:
        """Get all stored snapshots."""
        return list(self._snapshots)
    
    def get_summary_statistics(self, minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for the specified time period."""
        snapshots = self.get_recent_snapshots(minutes)
        
        if not snapshots:
            return {
                "period_minutes": minutes,
                "snapshot_count": 0,
                "status": "no_data"
            }
        
        # Calculate statistics
        response_times = [s.response_time_seconds for s in snapshots if s.healthy]
        utilizations = [s.connection_pool_utilization for s in snapshots]
        healthy_count = sum(1 for s in snapshots if s.healthy)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        avg_utilization = sum(utilizations) / len(utilizations) if utilizations else 0
        max_utilization = max(utilizations) if utilizations else 0
        
        uptime_percentage = (healthy_count / len(snapshots)) * 100
        
        return {
            "period_minutes": minutes,
            "snapshot_count": len(snapshots),
            "uptime_percentage": round(uptime_percentage, 2),
            "response_time": {
                "average_seconds": round(avg_response_time, 3),
                "maximum_seconds": round(max_response_time, 3)
            },
            "connection_pool": {
                "average_utilization_percent": round(avg_utilization, 2),
                "maximum_utilization_percent": round(max_utilization, 2)
            },
            "health_status": "healthy" if uptime_percentage > 95 else "degraded" if uptime_percentage > 80 else "unhealthy"
        }
    
    def clear_snapshots(self):
        """Clear all stored snapshots."""
        self._snapshots.clear()
        logger.info("Cleared all monitoring snapshots")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get the current status of the monitoring service."""
        return {
            "is_monitoring": self._is_monitoring,
            "interval_seconds": self._monitoring_interval,
            "snapshots_stored": len(self._snapshots),
            "max_snapshots": self.max_snapshots,
            "oldest_snapshot": self._snapshots[0].timestamp.isoformat() if self._snapshots else None,
            "newest_snapshot": self._snapshots[-1].timestamp.isoformat() if self._snapshots else None
        }


# Global monitoring service instance
monitoring_service = DatabaseMonitoringService()
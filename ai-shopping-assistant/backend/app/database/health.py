"""Database health check utilities."""

import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from sqlalchemy import text

from .manager import database_manager

logger = logging.getLogger(__name__)


class DatabaseHealthChecker:
    """Comprehensive database health monitoring."""
    
    def __init__(self):
        self._last_check_time: Optional[datetime] = None
        self._last_check_result: bool = False
        self._check_cache_duration = 30  # Cache health check results for 30 seconds
    
    async def check_health(self, force_check: bool = False) -> Dict[str, Any]:
        """
        Perform comprehensive database health check.
        
        Args:
            force_check: If True, bypass cache and perform fresh check
            
        Returns:
            Dictionary with health status and metrics
        """
        now = datetime.now(timezone.utc)
        
        # Use cached result if recent and not forcing check
        if (not force_check and 
            self._last_check_time and 
            (now - self._last_check_time).total_seconds() < self._check_cache_duration):
            return {
                "healthy": self._last_check_result,
                "cached": True,
                "last_check": self._last_check_time.isoformat(),
                "check_duration_seconds": 0
            }
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Basic connectivity check
            is_healthy = await database_manager.health_check()
            
            # Get connection pool information
            connection_info = await database_manager.get_connection_info()
            
            # Calculate check duration
            check_duration = asyncio.get_event_loop().time() - start_time
            
            # Update cache
            self._last_check_time = now
            self._last_check_result = is_healthy
            
            result = {
                "healthy": is_healthy,
                "cached": False,
                "last_check": now.isoformat(),
                "check_duration_seconds": round(check_duration, 3),
                "connection_pool": connection_info
            }
            
            if is_healthy:
                logger.debug(f"Database health check passed in {check_duration:.3f}s")
            else:
                logger.warning(f"Database health check failed in {check_duration:.3f}s")
            
            return result
            
        except Exception as e:
            check_duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Database health check error in {check_duration:.3f}s: {e}")
            
            # Update cache with failure
            self._last_check_time = now
            self._last_check_result = False
            
            return {
                "healthy": False,
                "cached": False,
                "last_check": now.isoformat(),
                "check_duration_seconds": round(check_duration, 3),
                "error": str(e),
                "connection_pool": {"status": "error"}
            }
    
    async def check_basic_connectivity(self) -> bool:
        """Simple connectivity check for quick health verification."""
        try:
            return await database_manager.health_check()
        except Exception as e:
            logger.error(f"Basic connectivity check failed: {e}")
            return False
    
    async def get_detailed_status(self) -> Dict[str, Any]:
        """Get detailed database status including metrics."""
        try:
            connection_info = await database_manager.get_connection_info()
            health_result = await self.check_health()
            performance_metrics = await self.get_performance_metrics()
            
            return {
                "database": {
                    "healthy": health_result["healthy"],
                    "last_check": health_result["last_check"],
                    "response_time_seconds": health_result["check_duration_seconds"]
                },
                "connection_pool": connection_info,
                "performance": performance_metrics,
                "initialized": database_manager._initialized
            }
            
        except Exception as e:
            logger.error(f"Failed to get detailed database status: {e}")
            return {
                "database": {
                    "healthy": False,
                    "error": str(e)
                },
                "connection_pool": {"status": "error"},
                "performance": {"status": "error"},
                "initialized": False
            }
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get database performance metrics."""
        try:
            if not database_manager._initialized:
                return {"status": "not_initialized"}
            
            session = await database_manager.get_session()
            try:
                # Get basic database statistics
                stats_queries = [
                    ("active_connections", "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"),
                    ("total_connections", "SELECT count(*) FROM pg_stat_activity"),
                    ("database_size", "SELECT pg_size_pretty(pg_database_size(current_database()))"),
                    ("uptime_seconds", "SELECT EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time()))"),
                ]
                
                metrics = {}
                for metric_name, query in stats_queries:
                    try:
                        result = await session.execute(text(query))
                        value = result.scalar()
                        metrics[metric_name] = value
                    except Exception as e:
                        logger.warning(f"Failed to get metric {metric_name}: {e}")
                        metrics[metric_name] = None
                
                # Get table statistics for main tables
                table_stats = await self._get_table_statistics(session)
                metrics["table_statistics"] = table_stats
                
                return {
                    "status": "available",
                    "metrics": metrics,
                    "collected_at": datetime.now(timezone.utc).isoformat()
                }
                
            finally:
                await session.close()
                
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_table_statistics(self, session) -> Dict[str, Any]:
        """Get statistics for main application tables."""
        try:
            table_names = ['user_credits', 'credit_transactions', 'user_consents', 'query_cache']
            stats = {}
            
            for table_name in table_names:
                try:
                    # Get row count
                    count_result = await session.execute(
                        text(f"SELECT COUNT(*) FROM {table_name}")
                    )
                    row_count = count_result.scalar()
                    
                    # Get table size
                    size_result = await session.execute(
                        text(f"SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))")
                    )
                    table_size = size_result.scalar()
                    
                    stats[table_name] = {
                        "row_count": row_count,
                        "size": table_size
                    }
                    
                except Exception as e:
                    logger.warning(f"Failed to get stats for table {table_name}: {e}")
                    stats[table_name] = {"error": str(e)}
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get table statistics: {e}")
            return {"error": str(e)}
    
    async def get_connection_pool_metrics(self) -> Dict[str, Any]:
        """Get detailed connection pool metrics."""
        try:
            connection_info = await database_manager.get_connection_info()
            
            if connection_info.get("status") != "initialized":
                return connection_info
            
            # Calculate additional metrics
            pool_size = connection_info.get("pool_size", 0)
            checked_out = connection_info.get("checked_out", 0)
            checked_in = connection_info.get("checked_in", 0)
            overflow = connection_info.get("overflow", 0)
            
            utilization = (checked_out / pool_size * 100) if pool_size > 0 else 0
            available = pool_size - checked_out
            
            return {
                **connection_info,
                "utilization_percent": round(utilization, 2),
                "available_connections": available,
                "total_capacity": pool_size + overflow,
                "health_status": "healthy" if utilization < 80 else "warning" if utilization < 95 else "critical"
            }
            
        except Exception as e:
            logger.error(f"Failed to get connection pool metrics: {e}")
            return {"status": "error", "error": str(e)}


# Global health checker instance
health_checker = DatabaseHealthChecker()
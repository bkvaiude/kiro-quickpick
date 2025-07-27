"""Database maintenance service for automated cleanup and maintenance tasks."""

import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from app.database.manager import database_manager, get_db_session
from app.database.repositories.cache_repository import CacheRepository
from app.database.repositories.credit_repository import CreditRepository
from app.database.models import CreditTransactionDB, QueryCacheDB

logger = logging.getLogger(__name__)


@dataclass
class MaintenanceResult:
    """Result of a maintenance operation."""
    task_name: str
    success: bool
    items_processed: int
    duration_seconds: float
    error_message: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class DatabaseMaintenanceService:
    """Service for automated database maintenance tasks."""
    
    def __init__(self):
        self._maintenance_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._maintenance_interval = 3600  # 1 hour default
        self._last_maintenance_run: Optional[datetime] = None
        self._maintenance_history: List[MaintenanceResult] = []
        self._max_history_entries = 100
    
    async def start_maintenance_scheduler(self, interval_seconds: int = 3600):
        """Start the automated maintenance scheduler."""
        if self._is_running:
            logger.warning("Database maintenance scheduler is already running")
            return
        
        self._maintenance_interval = interval_seconds
        self._is_running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.info(f"Started database maintenance scheduler with {interval_seconds}s interval")
    
    async def stop_maintenance_scheduler(self):
        """Stop the automated maintenance scheduler."""
        if not self._is_running:
            return
        
        self._is_running = False
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped database maintenance scheduler")
    
    async def _maintenance_loop(self):
        """Main maintenance loop that runs periodically."""
        while self._is_running:
            try:
                await self.run_maintenance_cycle()
                await asyncio.sleep(self._maintenance_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in maintenance loop: {e}")
                await asyncio.sleep(self._maintenance_interval)
    
    async def run_maintenance_cycle(self) -> List[MaintenanceResult]:
        """Run a complete maintenance cycle with all cleanup tasks."""
        logger.info("Starting database maintenance cycle")
        start_time = datetime.now(timezone.utc)
        
        results = []
        
        # Run all maintenance tasks
        maintenance_tasks = [
            self.cleanup_expired_cache,
            self.cleanup_old_transaction_history,
            self.cleanup_old_cache_entries,
            self.optimize_cache_size,
        ]
        
        for task in maintenance_tasks:
            try:
                result = await task()
                results.append(result)
                
                # Add to history
                self._maintenance_history.append(result)
                if len(self._maintenance_history) > self._max_history_entries:
                    self._maintenance_history.pop(0)
                
            except Exception as e:
                logger.error(f"Maintenance task {task.__name__} failed: {e}")
                error_result = MaintenanceResult(
                    task_name=task.__name__,
                    success=False,
                    items_processed=0,
                    duration_seconds=0.0,
                    error_message=str(e)
                )
                results.append(error_result)
                self._maintenance_history.append(error_result)
        
        self._last_maintenance_run = start_time
        
        # Log summary
        successful_tasks = sum(1 for r in results if r.success)
        total_items = sum(r.items_processed for r in results)
        total_duration = (datetime.now(timezone.utc) - start_time).total_seconds()
        
        logger.info(
            f"Maintenance cycle completed: {successful_tasks}/{len(results)} tasks successful, "
            f"{total_items} items processed in {total_duration:.2f}s"
        )
        
        return results
    
    async def cleanup_expired_cache(self) -> MaintenanceResult:
        """Clean up expired cache entries."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async for session in get_db_session():
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_expired_cache()
                
                duration = asyncio.get_event_loop().time() - start_time
                
                result = MaintenanceResult(
                    task_name="cleanup_expired_cache",
                    success=True,
                    items_processed=deleted_count,
                    duration_seconds=duration,
                    details={"deleted_entries": deleted_count}
                )
                
                logger.info(f"Cleaned up {deleted_count} expired cache entries in {duration:.2f}s")
                return result
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Failed to cleanup expired cache: {e}")
            return MaintenanceResult(
                task_name="cleanup_expired_cache",
                success=False,
                items_processed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def cleanup_old_transaction_history(self, days_to_keep: int = 90) -> MaintenanceResult:
        """Clean up old credit transaction history."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async for session in get_db_session():
                credit_repo = CreditRepository(session)
                deleted_count = await credit_repo.cleanup_old_transactions(days_to_keep)
                
                duration = asyncio.get_event_loop().time() - start_time
                
                result = MaintenanceResult(
                    task_name="cleanup_old_transaction_history",
                    success=True,
                    items_processed=deleted_count,
                    duration_seconds=duration,
                    details={
                        "deleted_transactions": deleted_count,
                        "days_kept": days_to_keep
                    }
                )
                
                logger.info(f"Cleaned up {deleted_count} old transaction records in {duration:.2f}s")
                return result
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Failed to cleanup old transaction history: {e}")
            return MaintenanceResult(
                task_name="cleanup_old_transaction_history",
                success=False,
                items_processed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def cleanup_old_cache_entries(self, days_to_keep: int = 7) -> MaintenanceResult:
        """Clean up old cache entries regardless of expiration."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async for session in get_db_session():
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_old_cache(days_to_keep)
                
                duration = asyncio.get_event_loop().time() - start_time
                
                result = MaintenanceResult(
                    task_name="cleanup_old_cache_entries",
                    success=True,
                    items_processed=deleted_count,
                    duration_seconds=duration,
                    details={
                        "deleted_entries": deleted_count,
                        "days_kept": days_to_keep
                    }
                )
                
                logger.info(f"Cleaned up {deleted_count} old cache entries in {duration:.2f}s")
                return result
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Failed to cleanup old cache entries: {e}")
            return MaintenanceResult(
                task_name="cleanup_old_cache_entries",
                success=False,
                items_processed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def optimize_cache_size(self, max_entries: int = 10000) -> MaintenanceResult:
        """Optimize cache size by removing oldest entries if over limit."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async for session in get_db_session():
                cache_repo = CacheRepository(session)
                deleted_count = await cache_repo.cleanup_cache_by_size_limit(max_entries)
                
                duration = asyncio.get_event_loop().time() - start_time
                
                result = MaintenanceResult(
                    task_name="optimize_cache_size",
                    success=True,
                    items_processed=deleted_count,
                    duration_seconds=duration,
                    details={
                        "deleted_entries": deleted_count,
                        "max_entries": max_entries
                    }
                )
                
                if deleted_count > 0:
                    logger.info(f"Optimized cache size: removed {deleted_count} entries in {duration:.2f}s")
                else:
                    logger.debug(f"Cache size optimization: no entries removed in {duration:.2f}s")
                
                return result
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Failed to optimize cache size: {e}")
            return MaintenanceResult(
                task_name="optimize_cache_size",
                success=False,
                items_processed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def run_database_vacuum(self) -> MaintenanceResult:
        """Run database vacuum operation (PostgreSQL specific)."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async for session in get_db_session():
                # Run VACUUM on main tables
                tables_to_vacuum = ['query_cache', 'credit_transactions', 'user_credits', 'user_consents']
                
                for table in tables_to_vacuum:
                    try:
                        await session.execute(f"VACUUM ANALYZE {table}")
                        logger.debug(f"Vacuumed table {table}")
                    except Exception as e:
                        logger.warning(f"Failed to vacuum table {table}: {e}")
                
                duration = asyncio.get_event_loop().time() - start_time
                
                result = MaintenanceResult(
                    task_name="run_database_vacuum",
                    success=True,
                    items_processed=len(tables_to_vacuum),
                    duration_seconds=duration,
                    details={"tables_vacuumed": tables_to_vacuum}
                )
                
                logger.info(f"Database vacuum completed for {len(tables_to_vacuum)} tables in {duration:.2f}s")
                return result
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Failed to run database vacuum: {e}")
            return MaintenanceResult(
                task_name="run_database_vacuum",
                success=False,
                items_processed=0,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def get_maintenance_statistics(self) -> Dict[str, Any]:
        """Get statistics about maintenance operations."""
        try:
            # Get cache statistics
            async for session in get_db_session():
                cache_repo = CacheRepository(session)
                cache_stats = await cache_repo.get_cache_statistics()
                cache_size_info = await cache_repo.get_cache_size_info()
                
                # Get credit transaction statistics
                credit_repo = CreditRepository(session)
                transaction_stats = await credit_repo.get_transaction_statistics()
                
                # Compile maintenance history statistics
                recent_results = self._maintenance_history[-10:] if self._maintenance_history else []
                successful_runs = sum(1 for r in recent_results if r.success)
                
                return {
                    "maintenance_scheduler": {
                        "is_running": self._is_running,
                        "interval_seconds": self._maintenance_interval,
                        "last_run": self._last_maintenance_run.isoformat() if self._last_maintenance_run else None,
                        "history_entries": len(self._maintenance_history)
                    },
                    "recent_performance": {
                        "last_10_runs": len(recent_results),
                        "successful_runs": successful_runs,
                        "success_rate": (successful_runs / len(recent_results) * 100) if recent_results else 0
                    },
                    "cache_status": {
                        **cache_stats,
                        **cache_size_info
                    },
                    "transaction_status": transaction_stats
                }
                
        except Exception as e:
            logger.error(f"Failed to get maintenance statistics: {e}")
            return {
                "error": str(e),
                "maintenance_scheduler": {
                    "is_running": self._is_running,
                    "interval_seconds": self._maintenance_interval,
                    "last_run": self._last_maintenance_run.isoformat() if self._last_maintenance_run else None
                }
            }
    
    def get_maintenance_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent maintenance history."""
        recent_history = self._maintenance_history[-limit:] if self._maintenance_history else []
        return [
            {
                "task_name": result.task_name,
                "success": result.success,
                "items_processed": result.items_processed,
                "duration_seconds": result.duration_seconds,
                "error_message": result.error_message,
                "details": result.details
            }
            for result in recent_history
        ]
    
    async def run_manual_maintenance_task(self, task_name: str, **kwargs) -> MaintenanceResult:
        """Run a specific maintenance task manually."""
        task_map = {
            "cleanup_expired_cache": self.cleanup_expired_cache,
            "cleanup_old_transaction_history": lambda: self.cleanup_old_transaction_history(
                kwargs.get("days_to_keep", 90)
            ),
            "cleanup_old_cache_entries": lambda: self.cleanup_old_cache_entries(
                kwargs.get("days_to_keep", 7)
            ),
            "optimize_cache_size": lambda: self.optimize_cache_size(
                kwargs.get("max_entries", 10000)
            ),
            "run_database_vacuum": self.run_database_vacuum
        }
        
        if task_name not in task_map:
            return MaintenanceResult(
                task_name=task_name,
                success=False,
                items_processed=0,
                duration_seconds=0.0,
                error_message=f"Unknown maintenance task: {task_name}"
            )
        
        try:
            result = await task_map[task_name]()
            self._maintenance_history.append(result)
            if len(self._maintenance_history) > self._max_history_entries:
                self._maintenance_history.pop(0)
            return result
        except Exception as e:
            logger.error(f"Manual maintenance task {task_name} failed: {e}")
            error_result = MaintenanceResult(
                task_name=task_name,
                success=False,
                items_processed=0,
                duration_seconds=0.0,
                error_message=str(e)
            )
            self._maintenance_history.append(error_result)
            return error_result


# Global maintenance service instance
maintenance_service = DatabaseMaintenanceService()
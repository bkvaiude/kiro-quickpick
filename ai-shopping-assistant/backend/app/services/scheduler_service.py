import asyncio
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional
from app.config import settings

logger = logging.getLogger(__name__)


class SchedulerService:
    """
    Simple background task scheduler for periodic tasks
    """
    
    def __init__(self):
        self._tasks: Dict[str, Dict] = {}
        self._running = False
        self._task_handle: Optional[asyncio.Task] = None
    
    def schedule_daily_task(self, name: str, task_func: Callable, hour: int = 0, minute: int = 0):
        """
        Schedule a task to run daily at a specific time
        
        Args:
            name: Unique name for the task
            task_func: Function to execute
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        self._tasks[name] = {
            "func": task_func,
            "type": "daily",
            "hour": hour,
            "minute": minute,
            "last_run": None
        }
        logger.info(f"Scheduled daily task '{name}' to run at {hour:02d}:{minute:02d}")
    
    def schedule_interval_task(self, name: str, task_func: Callable, interval_hours: int):
        """
        Schedule a task to run at regular intervals
        
        Args:
            name: Unique name for the task
            task_func: Function to execute
            interval_hours: Hours between executions
        """
        self._tasks[name] = {
            "func": task_func,
            "type": "interval",
            "interval_hours": interval_hours,
            "last_run": None
        }
        logger.info(f"Scheduled interval task '{name}' to run every {interval_hours} hours")
    
    async def start(self):
        """Start the scheduler"""
        if self._running:
            logger.warning("Scheduler is already running")
            return
        
        self._running = True
        self._task_handle = asyncio.create_task(self._run_scheduler())
        logger.info("Scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if not self._running:
            return
        
        self._running = False
        if self._task_handle:
            self._task_handle.cancel()
            try:
                await self._task_handle
            except asyncio.CancelledError:
                pass
        
        logger.info("Scheduler stopped")
    
    async def _run_scheduler(self):
        """Main scheduler loop"""
        while self._running:
            try:
                await self._check_and_run_tasks()
                # Check every minute
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                await asyncio.sleep(60)  # Continue after error
    
    async def _check_and_run_tasks(self):
        """Check if any tasks need to be run"""
        now = datetime.utcnow()
        
        for name, task_info in self._tasks.items():
            try:
                if self._should_run_task(task_info, now):
                    logger.info(f"Running scheduled task: {name}")
                    
                    # Run the task
                    if asyncio.iscoroutinefunction(task_info["func"]):
                        await task_info["func"]()
                    else:
                        task_info["func"]()
                    
                    # Update last run time
                    task_info["last_run"] = now
                    logger.info(f"Completed scheduled task: {name}")
                    
            except Exception as e:
                logger.error(f"Error running scheduled task '{name}': {e}")
    
    def _should_run_task(self, task_info: Dict, now: datetime) -> bool:
        """Check if a task should be run based on its schedule"""
        last_run = task_info.get("last_run")
        
        if task_info["type"] == "daily":
            # Check if it's time for daily task
            target_time = now.replace(
                hour=task_info["hour"],
                minute=task_info["minute"],
                second=0,
                microsecond=0
            )
            
            # If target time has passed today and we haven't run today
            if now >= target_time:
                if last_run is None or last_run.date() < now.date():
                    return True
        
        elif task_info["type"] == "interval":
            # Check if interval has passed
            if last_run is None:
                return True
            
            interval = timedelta(hours=task_info["interval_hours"])
            if now - last_run >= interval:
                return True
        
        return False
    
    def get_task_status(self) -> Dict:
        """Get status of all scheduled tasks"""
        status = {
            "running": self._running,
            "tasks": {}
        }
        
        for name, task_info in self._tasks.items():
            status["tasks"][name] = {
                "type": task_info["type"],
                "last_run": task_info.get("last_run"),
                "next_run": self._calculate_next_run(task_info)
            }
        
        return status
    
    def _calculate_next_run(self, task_info: Dict) -> Optional[datetime]:
        """Calculate when a task will next run"""
        now = datetime.utcnow()
        
        if task_info["type"] == "daily":
            target_time = now.replace(
                hour=task_info["hour"],
                minute=task_info["minute"],
                second=0,
                microsecond=0
            )
            
            if now >= target_time:
                # Next run is tomorrow
                return target_time + timedelta(days=1)
            else:
                # Next run is today
                return target_time
        
        elif task_info["type"] == "interval":
            last_run = task_info.get("last_run")
            if last_run:
                return last_run + timedelta(hours=task_info["interval_hours"])
            else:
                return now  # Will run immediately
        
        return None


# Create a singleton instance
scheduler_service = SchedulerService()
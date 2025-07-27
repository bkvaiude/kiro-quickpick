import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock, MagicMock
from app.services.scheduler_service import SchedulerService


class TestSchedulerService:
    """Test cases for SchedulerService"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.scheduler = SchedulerService()
        # Clear any existing tasks
        self.scheduler._tasks = {}
        self.scheduler._running = False
    
    def test_schedule_daily_task(self):
        """Test scheduling a daily task"""
        task_func = MagicMock()
        
        self.scheduler.schedule_daily_task("test_daily", task_func, hour=10, minute=30)
        
        assert "test_daily" in self.scheduler._tasks
        task_info = self.scheduler._tasks["test_daily"]
        assert task_info["func"] == task_func
        assert task_info["type"] == "daily"
        assert task_info["hour"] == 10
        assert task_info["minute"] == 30
        assert task_info["last_run"] is None
    
    def test_schedule_interval_task(self):
        """Test scheduling an interval task"""
        task_func = MagicMock()
        
        self.scheduler.schedule_interval_task("test_interval", task_func, interval_hours=6)
        
        assert "test_interval" in self.scheduler._tasks
        task_info = self.scheduler._tasks["test_interval"]
        assert task_info["func"] == task_func
        assert task_info["type"] == "interval"
        assert task_info["interval_hours"] == 6
        assert task_info["last_run"] is None
    
    @patch('app.services.scheduler_service.datetime')
    def test_should_run_daily_task_first_time(self, mock_datetime):
        """Test that daily task should run the first time when time has passed"""
        # Set current time to 11:00
        current_time = datetime(2025, 7, 24, 11, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30,
            "last_run": None
        }
        
        # Should run because it's past 10:30 and never run before
        assert self.scheduler._should_run_task(task_info, current_time) is True
    
    @patch('app.services.scheduler_service.datetime')
    def test_should_run_daily_task_not_time_yet(self, mock_datetime):
        """Test that daily task should not run when time hasn't come yet"""
        # Set current time to 09:00
        current_time = datetime(2025, 7, 24, 9, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30,
            "last_run": None
        }
        
        # Should not run because it's before 10:30
        assert self.scheduler._should_run_task(task_info, current_time) is False
    
    @patch('app.services.scheduler_service.datetime')
    def test_should_run_daily_task_already_run_today(self, mock_datetime):
        """Test that daily task should not run if already run today"""
        # Set current time to 15:00
        current_time = datetime(2025, 7, 24, 15, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        # Task was already run today at 11:00
        last_run = datetime(2025, 7, 24, 11, 0, 0)
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30,
            "last_run": last_run
        }
        
        # Should not run because it already ran today
        assert self.scheduler._should_run_task(task_info, current_time) is False
    
    @patch('app.services.scheduler_service.datetime')
    def test_should_run_daily_task_next_day(self, mock_datetime):
        """Test that daily task should run the next day"""
        # Set current time to 11:00 next day
        current_time = datetime(2025, 7, 25, 11, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        # Task was run yesterday
        last_run = datetime(2025, 7, 24, 11, 0, 0)
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30,
            "last_run": last_run
        }
        
        # Should run because it's a new day and past the scheduled time
        assert self.scheduler._should_run_task(task_info, current_time) is True
    
    def test_should_run_interval_task_first_time(self):
        """Test that interval task should run the first time"""
        current_time = datetime(2025, 7, 24, 12, 0, 0)
        
        task_info = {
            "type": "interval",
            "interval_hours": 6,
            "last_run": None
        }
        
        # Should run because it never ran before
        assert self.scheduler._should_run_task(task_info, current_time) is True
    
    def test_should_run_interval_task_interval_passed(self):
        """Test that interval task should run when interval has passed"""
        current_time = datetime(2025, 7, 24, 18, 0, 0)
        last_run = datetime(2025, 7, 24, 11, 0, 0)  # 7 hours ago
        
        task_info = {
            "type": "interval",
            "interval_hours": 6,
            "last_run": last_run
        }
        
        # Should run because 7 hours > 6 hours interval
        assert self.scheduler._should_run_task(task_info, current_time) is True
    
    def test_should_run_interval_task_interval_not_passed(self):
        """Test that interval task should not run when interval hasn't passed"""
        current_time = datetime(2025, 7, 24, 16, 0, 0)
        last_run = datetime(2025, 7, 24, 11, 0, 0)  # 5 hours ago
        
        task_info = {
            "type": "interval",
            "interval_hours": 6,
            "last_run": last_run
        }
        
        # Should not run because 5 hours < 6 hours interval
        assert self.scheduler._should_run_task(task_info, current_time) is False
    
    @patch('app.services.scheduler_service.datetime')
    def test_calculate_next_run_daily(self, mock_datetime):
        """Test calculating next run time for daily task"""
        current_time = datetime(2025, 7, 24, 15, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30
        }
        
        # Next run should be tomorrow at 10:30
        next_run = self.scheduler._calculate_next_run(task_info)
        expected = datetime(2025, 7, 25, 10, 30, 0)
        assert next_run == expected
    
    @patch('app.services.scheduler_service.datetime')
    def test_calculate_next_run_daily_before_time(self, mock_datetime):
        """Test calculating next run time for daily task when before scheduled time"""
        current_time = datetime(2025, 7, 24, 9, 0, 0)
        mock_datetime.utcnow.return_value = current_time
        
        task_info = {
            "type": "daily",
            "hour": 10,
            "minute": 30
        }
        
        # Next run should be today at 10:30
        next_run = self.scheduler._calculate_next_run(task_info)
        expected = datetime(2025, 7, 24, 10, 30, 0)
        assert next_run == expected
    
    def test_calculate_next_run_interval(self):
        """Test calculating next run time for interval task"""
        last_run = datetime(2025, 7, 24, 12, 0, 0)
        
        task_info = {
            "type": "interval",
            "interval_hours": 6,
            "last_run": last_run
        }
        
        # Next run should be 6 hours after last run
        next_run = self.scheduler._calculate_next_run(task_info)
        expected = datetime(2025, 7, 24, 18, 0, 0)
        assert next_run == expected
    
    def test_get_task_status(self):
        """Test getting task status"""
        task_func = MagicMock()
        self.scheduler.schedule_daily_task("test_daily", task_func, hour=10, minute=30)
        self.scheduler.schedule_interval_task("test_interval", task_func, interval_hours=6)
        
        status = self.scheduler.get_task_status()
        
        assert status["running"] is False
        assert "test_daily" in status["tasks"]
        assert "test_interval" in status["tasks"]
        assert status["tasks"]["test_daily"]["type"] == "daily"
        assert status["tasks"]["test_interval"]["type"] == "interval"
    
    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self):
        """Test starting and stopping the scheduler"""
        # Start scheduler
        await self.scheduler.start()
        assert self.scheduler._running is True
        assert self.scheduler._task_handle is not None
        
        # Stop scheduler
        await self.scheduler.stop()
        assert self.scheduler._running is False
    
    @pytest.mark.asyncio
    async def test_run_sync_task(self):
        """Test running a synchronous task"""
        task_func = MagicMock()
        self.scheduler.schedule_interval_task("test_sync", task_func, interval_hours=1)
        
        # Mock the should_run_task to return True
        with patch.object(self.scheduler, '_should_run_task', return_value=True):
            await self.scheduler._check_and_run_tasks()
        
        # Task should have been called
        task_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_run_async_task(self):
        """Test running an asynchronous task"""
        task_func = AsyncMock()
        self.scheduler.schedule_interval_task("test_async", task_func, interval_hours=1)
        
        # Mock the should_run_task to return True
        with patch.object(self.scheduler, '_should_run_task', return_value=True):
            await self.scheduler._check_and_run_tasks()
        
        # Task should have been called
        task_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_task_error_handling(self):
        """Test that task errors are handled gracefully"""
        def failing_task():
            raise Exception("Task failed")
        
        self.scheduler.schedule_interval_task("failing_task", failing_task, interval_hours=1)
        
        # Mock the should_run_task to return True
        with patch.object(self.scheduler, '_should_run_task', return_value=True):
            # Should not raise exception
            await self.scheduler._check_and_run_tasks()
        
        # Task should still be in the list
        assert "failing_task" in self.scheduler._tasks
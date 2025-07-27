import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from app.services.credit_reset_job import CreditResetJob


class TestCreditResetJob:
    """Test cases for CreditResetJob"""
    
    def setup_method(self):
        """Set up test environment before each test"""
        self.job = CreditResetJob()
        # Mock the services to avoid side effects
        self.job.credit_service = MagicMock()
        self.job.scheduler = MagicMock()
    
    def test_setup_credit_reset_schedule(self):
        """Test setting up the credit reset schedule"""
        self.job.setup_credit_reset_schedule()
        
        # Should schedule a daily task at midnight
        self.job.scheduler.schedule_daily_task.assert_called_once_with(
            name="daily_credit_reset",
            task_func=self.job.reset_all_registered_user_credits,
            hour=0,
            minute=0
        )
    
    def test_reset_all_registered_user_credits_success(self):
        """Test successful execution of credit reset for all users"""
        self.job.reset_all_registered_user_credits()
        
        # Should call credit service reset with no user_id (all users)
        self.job.credit_service.reset_credits.assert_called_once_with()
    
    def test_reset_all_registered_user_credits_error(self):
        """Test error handling in credit reset for all users"""
        # Make credit service raise an exception
        self.job.credit_service.reset_credits.side_effect = Exception("Database error")
        
        # Should raise the exception
        with pytest.raises(Exception, match="Database error"):
            self.job.reset_all_registered_user_credits()
    
    def test_reset_specific_user_credits_success(self):
        """Test successful execution of credit reset for specific user"""
        user_id = "auth0|123456"
        
        self.job.reset_specific_user_credits(user_id)
        
        # Should call credit service reset with specific user_id
        self.job.credit_service.reset_credits.assert_called_once_with(user_id)
    
    def test_reset_specific_user_credits_error(self):
        """Test error handling in credit reset for specific user"""
        user_id = "auth0|123456"
        
        # Make credit service raise an exception
        self.job.credit_service.reset_credits.side_effect = Exception("User not found")
        
        # Should raise the exception
        with pytest.raises(Exception, match="User not found"):
            self.job.reset_specific_user_credits(user_id)
    
    @pytest.mark.asyncio
    async def test_start_scheduler(self):
        """Test starting the scheduler"""
        # Make scheduler.start async
        self.job.scheduler.start = AsyncMock()
        
        await self.job.start_scheduler()
        
        # Should call scheduler start
        self.job.scheduler.start.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_scheduler(self):
        """Test stopping the scheduler"""
        # Make scheduler.stop async
        self.job.scheduler.stop = AsyncMock()
        
        await self.job.stop_scheduler()
        
        # Should call scheduler stop
        self.job.scheduler.stop.assert_called_once()
    
    def test_get_scheduler_status(self):
        """Test getting scheduler status"""
        expected_status = {
            "running": True,
            "tasks": {
                "daily_credit_reset": {
                    "type": "daily",
                    "last_run": None,
                    "next_run": "2025-07-25T00:00:00"
                }
            }
        }
        
        self.job.scheduler.get_task_status.return_value = expected_status
        
        status = self.job.get_scheduler_status()
        
        assert status == expected_status
        self.job.scheduler.get_task_status.assert_called_once()
    
    @patch('app.services.credit_reset_job.credit_service')
    @patch('app.services.credit_reset_job.scheduler_service')
    def test_singleton_instances(self, mock_scheduler, mock_credit_service):
        """Test that the job uses singleton instances"""
        # Create a new job instance
        new_job = CreditResetJob()
        
        # Should use the singleton instances
        assert new_job.credit_service == mock_credit_service
        assert new_job.scheduler == mock_scheduler
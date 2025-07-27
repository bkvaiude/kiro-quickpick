import logging
from app.services.credit_service import credit_service
from app.services.scheduler_service import scheduler_service
from app.config import settings

logger = logging.getLogger(__name__)


class CreditResetJob:
    """
    Background job for resetting registered user credits
    """
    
    def __init__(self):
        self.credit_service = credit_service
        self.scheduler = scheduler_service
    
    def setup_credit_reset_schedule(self):
        """
        Set up the scheduled credit reset job
        """
        # Schedule daily credit reset at midnight (00:00)
        self.scheduler.schedule_daily_task(
            name="daily_credit_reset",
            task_func=self.reset_all_registered_user_credits,
            hour=0,
            minute=0
        )
        
        logger.info("Credit reset job scheduled for daily execution at 00:00 UTC")
    
    async def reset_all_registered_user_credits(self):
        """
        Reset credits for all registered users
        This is the main job function that gets executed by the scheduler
        """
        try:
            logger.info("Starting daily credit reset for all registered users")
            
            # Reset credits for all registered users
            await self.credit_service.reset_credits()
            
            logger.info("Daily credit reset completed successfully")
            
        except Exception as e:
            logger.error(f"Error during daily credit reset: {e}")
            raise
    
    async def reset_specific_user_credits(self, user_id: str):
        """
        Reset credits for a specific user (for manual/admin use)
        
        Args:
            user_id: The user identifier to reset credits for
        """
        try:
            logger.info(f"Manually resetting credits for user: {user_id}")
            
            await self.credit_service.reset_credits(user_id)
            
            logger.info(f"Credits reset successfully for user: {user_id}")
            
        except Exception as e:
            logger.error(f"Error resetting credits for user {user_id}: {e}")
            raise
    
    async def start_scheduler(self):
        """
        Start the background scheduler
        """
        await self.scheduler.start()
        logger.info("Credit reset scheduler started")
    
    async def stop_scheduler(self):
        """
        Stop the background scheduler
        """
        await self.scheduler.stop()
        logger.info("Credit reset scheduler stopped")
    
    def get_scheduler_status(self):
        """
        Get the current status of the credit reset scheduler
        
        Returns:
            Dict: Scheduler status information
        """
        return self.scheduler.get_task_status()


# Create a singleton instance
credit_reset_job = CreditResetJob()
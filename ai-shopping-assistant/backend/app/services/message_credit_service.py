from typing import Dict, Optional, List
from datetime import datetime
from app.config import settings, logger

class MessageCreditService:
    """
    Service for tracking and limiting guest user message credits
    """
    
    def __init__(self):
        # In-memory storage for guest message credits
        # In a production environment, this would be stored in a database
        self._guest_credits: Dict[str, List[Dict]] = {}
        self.credit_limit = settings.guest_action_limit
    
    def track_credit_usage(self, guest_id: str, action_type: str) -> bool:
        """
        Tracks a guest user credit usage and checks if the limit is reached
        
        Args:
            guest_id: The guest user identifier (e.g., session ID or IP address)
            action_type: The type of action (e.g., 'chat', 'search')
            
        Returns:
            bool: True if the credit was tracked, False if the limit is reached
        """
        # Initialize guest credits if not exists
        if guest_id not in self._guest_credits:
            self._guest_credits[guest_id] = []
        
        # Check if limit is reached
        if len(self._guest_credits[guest_id]) >= self.credit_limit:
            logger.info(f"Guest {guest_id} has reached the credit limit")
            return False
        
        # Track the credit usage
        self._guest_credits[guest_id].append({
            "action_type": action_type,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.debug(f"Guest {guest_id} credit tracked: {action_type}, " 
                    f"remaining: {self.credit_limit - len(self._guest_credits[guest_id])}")
        
        return True
    
    def get_remaining_credits(self, guest_id: str) -> int:
        """
        Gets the number of remaining credits for a guest user
        
        Args:
            guest_id: The guest user identifier
            
        Returns:
            int: The number of remaining credits
        """
        if guest_id not in self._guest_credits:
            return self.credit_limit
        
        used_credits = len(self._guest_credits[guest_id])
        remaining = max(0, self.credit_limit - used_credits)
        
        return remaining
    
    def is_limit_reached(self, guest_id: str) -> bool:
        """
        Checks if the guest user has reached the credit limit
        
        Args:
            guest_id: The guest user identifier
            
        Returns:
            bool: True if the limit is reached, False otherwise
        """
        return self.get_remaining_credits(guest_id) <= 0
    
    def reset_credits(self, guest_id: str) -> None:
        """
        Resets the credit count for a guest user
        
        Args:
            guest_id: The guest user identifier
        """
        if guest_id in self._guest_credits:
            self._guest_credits[guest_id] = []
            logger.debug(f"Guest {guest_id} credits reset")

# Create a singleton instance of the message credit service
message_credit_service = MessageCreditService()
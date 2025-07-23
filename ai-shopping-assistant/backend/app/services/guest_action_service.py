from typing import Dict, Optional, List
from datetime import datetime
from app.config import settings, logger

class GuestActionService:
    """
    Service for tracking and limiting guest user actions
    """
    
    def __init__(self):
        # In-memory storage for guest actions
        # In a production environment, this would be stored in a database
        self._guest_actions: Dict[str, List[Dict]] = {}
        self.action_limit = settings.guest_action_limit
    
    def track_action(self, guest_id: str, action_type: str) -> bool:
        """
        Tracks a guest user action and checks if the limit is reached
        
        Args:
            guest_id: The guest user identifier (e.g., session ID or IP address)
            action_type: The type of action (e.g., 'chat', 'search')
            
        Returns:
            bool: True if the action was tracked, False if the limit is reached
        """
        # Initialize guest actions if not exists
        if guest_id not in self._guest_actions:
            self._guest_actions[guest_id] = []
        
        # Check if limit is reached
        if len(self._guest_actions[guest_id]) >= self.action_limit:
            logger.info(f"Guest {guest_id} has reached the action limit")
            return False
        
        # Track the action
        self._guest_actions[guest_id].append({
            "action_type": action_type,
            "timestamp": datetime.now().isoformat()
        })
        
        logger.debug(f"Guest {guest_id} action tracked: {action_type}, " 
                    f"remaining: {self.action_limit - len(self._guest_actions[guest_id])}")
        
        return True
    
    def get_remaining_actions(self, guest_id: str) -> int:
        """
        Gets the number of remaining actions for a guest user
        
        Args:
            guest_id: The guest user identifier
            
        Returns:
            int: The number of remaining actions
        """
        if guest_id not in self._guest_actions:
            return self.action_limit
        
        used_actions = len(self._guest_actions[guest_id])
        remaining = max(0, self.action_limit - used_actions)
        
        return remaining
    
    def is_limit_reached(self, guest_id: str) -> bool:
        """
        Checks if the guest user has reached the action limit
        
        Args:
            guest_id: The guest user identifier
            
        Returns:
            bool: True if the limit is reached, False otherwise
        """
        return self.get_remaining_actions(guest_id) <= 0
    
    def reset_actions(self, guest_id: str) -> None:
        """
        Resets the action count for a guest user
        
        Args:
            guest_id: The guest user identifier
        """
        if guest_id in self._guest_actions:
            self._guest_actions[guest_id] = []
            logger.debug(f"Guest {guest_id} actions reset")

# Create a singleton instance of the guest action service
guest_action_service = GuestActionService()
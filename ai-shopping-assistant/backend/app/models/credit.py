from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from typing import Optional


class UserCredits(BaseModel):
    """Model for user credit information."""
    user_id: str
    is_guest: bool
    available_credits: int
    max_credits: int
    last_reset_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "auth0|123456789",
                "is_guest": False,
                "available_credits": 45,
                "max_credits": 50,
                "last_reset_timestamp": "2025-07-24T00:00:00"
            }
        }
    }


class CreditTransaction(BaseModel):
    """Model for credit transaction records."""
    user_id: str
    transaction_type: str  # 'deduct', 'reset', 'allocate'
    amount: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    description: Optional[str] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "auth0|123456789",
                "transaction_type": "deduct",
                "amount": 1,
                "timestamp": "2025-07-24T12:30:00",
                "description": "Query processed"
            }
        }
    }


class CreditStatus(BaseModel):
    """Model for credit status response."""
    available_credits: int
    max_credits: int
    is_guest: bool
    can_reset: bool
    next_reset_time: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "available_credits": 45,
                "max_credits": 50,
                "is_guest": False,
                "can_reset": True,
                "next_reset_time": "2025-07-25T00:00:00"
            }
        }
    }
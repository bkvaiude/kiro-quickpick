from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class UserConsent(BaseModel):
    """Model for user consent information."""
    user_id: str
    terms_accepted: bool = True
    marketing_consent: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "auth0|123456789",
                "terms_accepted": True,
                "marketing_consent": True,
                "timestamp": "2025-07-21T12:00:00"
            }
        }
    }


class UserConsentCreate(BaseModel):
    """Model for creating user consent."""
    terms_accepted: bool = True
    marketing_consent: bool = False


class UserConsentUpdate(BaseModel):
    """Model for updating user consent."""
    marketing_consent: Optional[bool] = None
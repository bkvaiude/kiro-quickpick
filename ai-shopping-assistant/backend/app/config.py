import os
import logging
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class Settings(BaseModel):
    # API Keys
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    
    # Affiliate Settings
    affiliate_tag: str = os.getenv("AFFILIATE_TAG", "")
    affiliate_program: str = os.getenv("AFFILIATE_PROGRAM", "amazon")
    
    # API Settings
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("DEBUG", "False").lower() in ("true", "1", "t")
    workers: int = int(os.getenv("WORKERS", "4"))
    
    # Security Settings
    allowed_hosts: List[str] = Field(
        default_factory=lambda: os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    )
    
    # Auth0 Settings
    auth0_domain: str = os.getenv("AUTH0_DOMAIN", "your-auth0-domain.auth0.com")
    auth0_api_audience: str = os.getenv("AUTH0_API_AUDIENCE", f"https://{os.getenv('AUTH0_DOMAIN', 'your-auth0-domain.auth0.com')}/api/v2/")
    auth0_algorithms: List[str] = Field(
        default_factory=lambda: ["RS256"]
    )
    auth0_issuer: str = os.getenv("AUTH0_ISSUER", f"https://{os.getenv('AUTH0_DOMAIN', 'your-auth0-domain.auth0.com')}/")
    
    # Guest User Settings
    guest_action_limit: int = int(os.getenv("GUEST_ACTION_LIMIT", "10"))
    
    # CORS Settings
    cors_origins: List[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",  # Vite's default port
            "http://localhost:3000",  # Alternative development port
            "https://ai-shopping-assistant.vercel.app",  # Production frontend URL
        ] + ([os.getenv("FRONTEND_URL")] if os.getenv("FRONTEND_URL") and os.getenv("FRONTEND_URL") not in ["", "null", "undefined"] else [])
    )

# Create settings instance
settings = Settings()

# Validate required settings
def validate_settings():
    missing_vars = []
    
    if not settings.gemini_api_key:
        missing_vars.append("GEMINI_API_KEY")
    
    if not settings.affiliate_tag:
        missing_vars.append("AFFILIATE_TAG")
    
    if missing_vars:
        for var in missing_vars:
            logger.warning(f"{var} is not set in environment variables")
        
        if not settings.debug:
            logger.warning("Missing critical environment variables in production mode")

# Run validation on import
validate_settings()
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

class DatabaseConfig(BaseModel):
    """Configuration for PostgreSQL database connection with optimized settings"""
    database_url: str = Field(description="PostgreSQL connection string")
    pool_size: int = Field(default=15, description="Connection pool size (optimized for production)")
    max_overflow: int = Field(default=25, description="Maximum overflow connections")
    pool_timeout: int = Field(default=20, description="Pool timeout in seconds (reduced for faster failures)")
    pool_recycle: int = Field(default=1800, description="Pool recycle time in seconds (30 minutes)")
    pool_pre_ping: bool = Field(default=True, description="Enable connection health checks")
    echo_sql: bool = Field(default=False, description="Enable SQL query logging")
    
    # Query optimization settings
    statement_timeout: int = Field(default=30000, description="Statement timeout in milliseconds")
    idle_in_transaction_session_timeout: int = Field(default=60000, description="Idle transaction timeout in milliseconds")
    
    # Connection optimization settings
    connect_timeout: int = Field(default=10, description="Connection timeout in seconds")
    command_timeout: int = Field(default=60, description="Command timeout in seconds")
    server_settings: dict = Field(
        default_factory=lambda: {
            "application_name": "ai_shopping_assistant",
            "statement_timeout": "30s",
            "idle_in_transaction_session_timeout": "60s",
            "tcp_keepalives_idle": "300",
            "tcp_keepalives_interval": "30",
            "tcp_keepalives_count": "3"
        },
        description="PostgreSQL server settings for optimization"
    )
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database configuration from environment variables with optimized defaults"""
        return cls(
            database_url=os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ai_shopping_assistant"),
            pool_size=int(os.getenv("DB_POOL_SIZE", "15")),  # Increased default
            max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "25")),  # Increased default
            pool_timeout=int(os.getenv("DB_POOL_TIMEOUT", "20")),  # Reduced for faster failures
            pool_recycle=int(os.getenv("DB_POOL_RECYCLE", "1800")),  # 30 minutes instead of 1 hour
            pool_pre_ping=os.getenv("DB_POOL_PRE_PING", "True").lower() in ("true", "1", "t"),
            echo_sql=os.getenv("DB_ECHO_SQL", "False").lower() in ("true", "1", "t"),
            statement_timeout=int(os.getenv("DB_STATEMENT_TIMEOUT", "30000")),
            idle_in_transaction_session_timeout=int(os.getenv("DB_IDLE_TRANSACTION_TIMEOUT", "60000")),
            connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "10")),
            command_timeout=int(os.getenv("DB_COMMAND_TIMEOUT", "60"))
        )

class CreditSystemConfig(BaseModel):
    """Configuration for the message credit system"""
    max_guest_credits: int = Field(default=10, description="Maximum credits for guest users")
    max_registered_credits: int = Field(default=50, description="Maximum credits for registered users per day")
    credit_reset_interval_hours: int = Field(default=24, description="Hours between credit resets for registered users")
    cache_validity_minutes: int = Field(default=60, description="Minutes that cached query results remain valid")
    
    @classmethod
    def from_env(cls) -> "CreditSystemConfig":
        """Create configuration from environment variables"""
        return cls(
            max_guest_credits=int(os.getenv("MAX_GUEST_CREDITS", "10")),
            max_registered_credits=int(os.getenv("MAX_REGISTERED_CREDITS", "50")),
            credit_reset_interval_hours=int(os.getenv("CREDIT_RESET_INTERVAL_HOURS", "24")),
            cache_validity_minutes=int(os.getenv("CACHE_VALIDITY_MINUTES", "60"))
        )

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
    
    # Guest User Settings (Legacy - to be removed)
    guest_action_limit: int = int(os.getenv("GUEST_ACTION_LIMIT", "10"))  # TODO: Remove after migration to credit system
    
    # Message Credit System Settings
    credit_system: CreditSystemConfig = Field(default_factory=CreditSystemConfig.from_env)
    
    # Database Settings
    database: DatabaseConfig = Field(default_factory=DatabaseConfig.from_env)
    
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
    
    # Validate credit system configuration
    if settings.credit_system.max_guest_credits <= 0:
        logger.warning("MAX_GUEST_CREDITS should be greater than 0")
    
    if settings.credit_system.max_registered_credits <= 0:
        logger.warning("MAX_REGISTERED_CREDITS should be greater than 0")
    
    if settings.credit_system.credit_reset_interval_hours <= 0:
        logger.warning("CREDIT_RESET_INTERVAL_HOURS should be greater than 0")
    
    if settings.credit_system.cache_validity_minutes <= 0:
        logger.warning("CACHE_VALIDITY_MINUTES should be greater than 0")
    
    logger.info(f"Credit system configuration loaded: "
                f"Guest={settings.credit_system.max_guest_credits}, "
                f"Registered={settings.credit_system.max_registered_credits}, "
                f"Reset={settings.credit_system.credit_reset_interval_hours}h, "
                f"Cache={settings.credit_system.cache_validity_minutes}m")
    
    # Validate database configuration
    if not settings.database.database_url:
        logger.warning("DATABASE_URL is not set in environment variables")
    
    if settings.database.pool_size <= 0:
        logger.warning("DB_POOL_SIZE should be greater than 0")
    
    if settings.database.max_overflow < 0:
        logger.warning("DB_MAX_OVERFLOW should be greater than or equal to 0")
    
    if settings.database.pool_timeout <= 0:
        logger.warning("DB_POOL_TIMEOUT should be greater than 0")
    
    logger.info(f"Database configuration loaded: "
                f"Pool={settings.database.pool_size}, "
                f"MaxOverflow={settings.database.max_overflow}, "
                f"Timeout={settings.database.pool_timeout}s, "
                f"EchoSQL={settings.database.echo_sql}")

# Run validation on import
validate_settings()
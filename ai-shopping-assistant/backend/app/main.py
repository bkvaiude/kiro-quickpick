from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import uvicorn
import time
from datetime import datetime, timezone
from jose import JWTError
from contextlib import asynccontextmanager

# Import settings for configuration
from app.config import settings, logger

# Import API router
from app.api.router import router

# Import credit reset job
from app.services.credit_reset_job import credit_reset_job

# Import database manager
from app.database.manager import database_manager
from app.database.health import health_checker

# Import monitoring service
from app.services.monitoring_service import monitoring_service

# Import maintenance service
from app.services.database_maintenance import maintenance_service

# Import custom error handlers
from app.middleware.error_handlers import (
    jwt_error_handler, 
    jwt_expired_handler, 
    missing_token_handler,
    guest_limit_handler
)
from app.middleware.auth import JWTValidationError
from app.middleware.credit_middleware import CreditExhaustedException, credit_exhausted_handler

# Import database error handlers
from app.middleware.database_error_handlers import (
    sqlalchemy_error_handler,
    postgres_error_handler,
    repository_error_handler,
    repository_integrity_error_handler,
    repository_operational_error_handler
)
from sqlalchemy.exc import SQLAlchemyError
from asyncpg.exceptions import PostgresError
from app.database.repositories.base import (
    RepositoryError,
    RepositoryIntegrityError,
    RepositoryOperationalError
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown tasks
    """
    # Startup
    logger.info("Starting AI Shopping Assistant API")
    logger.debug("Debug logging is enabled")
    
    try:
        # Initialize database manager
        logger.info("Initializing database connection...")
        logger.debug(f"Database URL: {settings.database.database_url[:50]}...")
        await database_manager.initialize()
        
        # Run database migrations
        logger.info("Running database migrations...")
        logger.info("Running database migrations......")
        database_manager.run_migrations()
        logger.info("Running database migrations......_-")
        
        # Verify database health
        health_status = await health_checker.check_health()
        if not health_status["healthy"]:
            logger.error("Database health check failed during startup")
            raise RuntimeError("Database is not healthy")
        
        logger.info("Database initialized successfully")
        
        # Set up credit reset schedule
        credit_reset_job.setup_credit_reset_schedule()
        
        # Start the scheduler
        await credit_reset_job.start_scheduler()
        
        # Start database monitoring
        await monitoring_service.start_monitoring(interval_seconds=60)
        
        # Start database maintenance scheduler
        await maintenance_service.start_maintenance_scheduler(interval_seconds=3600)  # Run every hour
        
        logger.info("Application startup completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        # Clean up any partial initialization
        try:
            await database_manager.close()
        except Exception as cleanup_error:
            logger.error(f"Error during startup cleanup: {cleanup_error}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Shopping Assistant API")
    
    try:
        # Stop the scheduler
        await credit_reset_job.stop_scheduler()
        
        # Stop database monitoring
        await monitoring_service.stop_monitoring()
        
        # Stop database maintenance scheduler
        await maintenance_service.stop_maintenance_scheduler()
        
        # Close database connections
        await database_manager.close()
        
        logger.info("Application shutdown completed successfully")
        
    except Exception as e:
        logger.error(f"Error during application shutdown: {e}")


app = FastAPI(
    title="AI Shopping Assistant API",
    description="Backend API for AI Shopping Assistant",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,  # Disable redoc in production
    lifespan=lifespan
)

# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Log request details in debug mode
    logger.debug(f"Incoming request: {request.method} {request.url.path}")
    if request.query_params:
        logger.debug(f"Query params: {dict(request.query_params)}")
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} completed in {process_time:.3f}s with status {response.status_code}")
        logger.debug(f"Response headers: {dict(response.headers)}")
        return response
    except HTTPException:
        # Re-raise HTTP exceptions so they're handled properly by FastAPI
        raise
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"{request.method} {request.url.path} failed after {process_time:.3f}s: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

@app.get("/")
async def root():
    return {
        "message": "Welcome to AI Shopping Assistant API",
        "status": "healthy",
        "version": app.version
    }

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy"}

@app.get("/health/detailed")
async def detailed_health_check():
    """Detailed health check including database status."""
    try:
        db_status = await health_checker.get_detailed_status()
        
        overall_healthy = db_status.get("database", {}).get("healthy", False)
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": db_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": str(e)
        }

@app.get("/health/database")
async def database_health_check():
    """Database-specific health check endpoint."""
    try:
        health_result = await health_checker.check_health()
        status_code = 200 if health_result["healthy"] else 503
        
        return JSONResponse(
            status_code=status_code,
            content=health_result
        )
    except Exception as e:
        logger.error(f"Database health check endpoint failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "healthy": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )

# Include the API router with prefix
app.include_router(router, prefix="/api")

# Register exception handlers
app.add_exception_handler(JWTError, jwt_error_handler)
app.add_exception_handler(JWTValidationError, jwt_expired_handler)
app.add_exception_handler(CreditExhaustedException, credit_exhausted_handler)

# Register database error handlers
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(PostgresError, postgres_error_handler)
app.add_exception_handler(RepositoryError, repository_error_handler)
app.add_exception_handler(RepositoryIntegrityError, repository_integrity_error_handler)
app.add_exception_handler(RepositoryOperationalError, repository_operational_error_handler)

# Don't register a global HTTPException handler - let FastAPI handle them normally

# Add validation error handler for better error messages
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with a standardized format
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        })
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )

if __name__ == "__main__":
    # In development, use reload=True
    # In production, use the settings from environment variables
    uvicorn.run(
        "app.main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1
    )
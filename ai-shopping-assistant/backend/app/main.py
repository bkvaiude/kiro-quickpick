from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import uvicorn
import time
from jose import JWTError

# Import settings for configuration
from app.config import settings, logger

# Import API router
from app.api.router import router

# Import custom error handlers
from app.middleware.error_handlers import (
    jwt_error_handler, 
    jwt_expired_handler, 
    missing_token_handler,
    guest_limit_handler
)
from app.middleware.auth import JWTValidationError

app = FastAPI(
    title="AI Shopping Assistant API",
    description="Backend API for AI Shopping Assistant",
    version="0.1.0",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,  # Disable redoc in production
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
    
    # Process the request
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"{request.method} {request.url.path} completed in {process_time:.3f}s with status {response.status_code}")
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
    return {"status": "healthy"}

# Include the API router with prefix
app.include_router(router, prefix="/api")

# Register exception handlers
app.add_exception_handler(JWTError, jwt_error_handler)
app.add_exception_handler(JWTValidationError, jwt_expired_handler)
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
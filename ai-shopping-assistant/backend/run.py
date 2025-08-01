import uvicorn
import os
from app.config import settings, logger

if __name__ == "__main__":
    print("[RUN.PY] Starting application...")
    logger.info(f"Starting AI Shopping Assistant API in {'debug' if settings.debug else 'production'} mode")
    logger.info(f"API will be available at http://{settings.api_host}:{settings.api_port}")
    logger.debug("This is a DEBUG message from run.py - should be visible if LOG_LEVEL=DEBUG")
    
    # Use simple log level for uvicorn
    uvicorn_log_level = "debug" if settings.debug else "info"
    
    uvicorn.run(
        "app.main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        workers=1,  # Always use 1 worker in development
        log_level=uvicorn_log_level,
        reload=settings.debug,
        access_log=True
    )
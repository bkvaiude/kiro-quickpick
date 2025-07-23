import uvicorn
from app.config import settings, logger

if __name__ == "__main__":
    logger.info(f"Starting AI Shopping Assistant API in {'debug' if settings.debug else 'production'} mode")
    logger.info(f"API will be available at http://{settings.api_host}:{settings.api_port}")
    
    uvicorn.run(
        "app.main:app", 
        host=settings.api_host, 
        port=settings.api_port, 
        workers=settings.workers if not settings.debug else 1,
        log_level=settings.debug and "debug" or "info",
        reload=settings.debug
    )
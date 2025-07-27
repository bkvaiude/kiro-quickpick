"""Health monitoring endpoints for database and application status."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from app.database.health import health_checker
from app.database.manager import database_manager
from app.services.monitoring_service import monitoring_service
from app.middleware.database_error_handlers import handle_database_errors

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
async def basic_health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/database")
@handle_database_errors
async def database_health_check():
    """Database-specific health check with connection pool monitoring."""
    try:
        health_result = await health_checker.check_health()
        status_code = 200 if health_result["healthy"] else 503
        
        return JSONResponse(
            status_code=status_code,
            content={
                **health_result,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
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


@router.get("/detailed")
@handle_database_errors
async def detailed_health_check():
    """Comprehensive health check including all system components."""
    try:
        db_status = await health_checker.get_detailed_status()
        
        overall_healthy = db_status.get("database", {}).get("healthy", False)
        
        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": db_status
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e)
            }
        )


@router.get("/metrics")
@handle_database_errors
async def database_metrics():
    """Get database performance metrics and connection pool information."""
    try:
        # Get connection pool information
        connection_info = await database_manager.get_connection_info()
        
        # Get health check metrics
        health_result = await health_checker.check_health(force_check=True)
        
        # Calculate pool utilization
        pool_utilization = 0.0
        if connection_info.get("pool_size", 0) > 0:
            checked_out = connection_info.get("checked_out", 0)
            pool_size = connection_info.get("pool_size", 1)
            pool_utilization = (checked_out / pool_size) * 100
        
        metrics = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "database": {
                "healthy": health_result["healthy"],
                "response_time_seconds": health_result["check_duration_seconds"],
                "last_check": health_result["last_check"]
            },
            "connection_pool": {
                **connection_info,
                "utilization_percent": round(pool_utilization, 2)
            },
            "system": {
                "initialized": database_manager._initialized
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Failed to get database metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve database metrics: {str(e)}"
        )


@router.get("/connectivity")
@handle_database_errors
async def check_connectivity():
    """Quick connectivity check for monitoring systems."""
    try:
        is_connected = await health_checker.check_basic_connectivity()
        
        return JSONResponse(
            status_code=200 if is_connected else 503,
            content={
                "connected": is_connected,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )
    except Exception as e:
        logger.error(f"Connectivity check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "connected": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@router.get("/monitoring/status")
async def get_monitoring_status():
    """Get the status of the database monitoring service."""
    try:
        status = monitoring_service.get_monitoring_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get monitoring status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring status: {str(e)}"
        )


@router.get("/monitoring/snapshots")
async def get_monitoring_snapshots(minutes: int = 60):
    """Get recent monitoring snapshots."""
    try:
        if minutes <= 0 or minutes > 1440:  # Max 24 hours
            raise HTTPException(
                status_code=400,
                detail="Minutes must be between 1 and 1440"
            )
        
        snapshots = monitoring_service.get_recent_snapshots(minutes)
        return {
            "period_minutes": minutes,
            "snapshot_count": len(snapshots),
            "snapshots": [snapshot.to_dict() for snapshot in snapshots]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monitoring snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring snapshots: {str(e)}"
        )


@router.get("/monitoring/summary")
async def get_monitoring_summary(minutes: int = 60):
    """Get summary statistics for database monitoring."""
    try:
        if minutes <= 0 or minutes > 1440:  # Max 24 hours
            raise HTTPException(
                status_code=400,
                detail="Minutes must be between 1 and 1440"
            )
        
        summary = monitoring_service.get_summary_statistics(minutes)
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get monitoring summary: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get monitoring summary: {str(e)}"
        )


@router.post("/monitoring/start")
async def start_monitoring(interval_seconds: int = 60):
    """Start database monitoring with specified interval."""
    try:
        if interval_seconds < 10 or interval_seconds > 3600:  # Between 10 seconds and 1 hour
            raise HTTPException(
                status_code=400,
                detail="Interval must be between 10 and 3600 seconds"
            )
        
        await monitoring_service.start_monitoring(interval_seconds)
        return {
            "status": "started",
            "interval_seconds": interval_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/monitoring/stop")
async def stop_monitoring():
    """Stop database monitoring."""
    try:
        await monitoring_service.stop_monitoring()
        return {
            "status": "stopped",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop monitoring: {str(e)}"
        )


@router.delete("/monitoring/snapshots")
async def clear_monitoring_snapshots():
    """Clear all stored monitoring snapshots."""
    try:
        monitoring_service.clear_snapshots()
        return {
            "status": "cleared",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to clear monitoring snapshots: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear monitoring snapshots: {str(e)}"
        )
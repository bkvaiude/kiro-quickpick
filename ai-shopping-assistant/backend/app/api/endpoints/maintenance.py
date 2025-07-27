"""Database maintenance and backup API endpoints."""

import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from app.services.database_maintenance import maintenance_service
from app.services.database_backup import backup_service
from app.middleware.database_error_handlers import handle_database_errors

logger = logging.getLogger(__name__)

router = APIRouter()


# Maintenance endpoints
@router.get("/status")
@handle_database_errors
async def get_maintenance_status():
    """Get the current status of database maintenance."""
    try:
        status = await maintenance_service.get_maintenance_statistics()
        return status
    except Exception as e:
        logger.error(f"Failed to get maintenance status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get maintenance status: {str(e)}"
        )


@router.get("/history")
@handle_database_errors
async def get_maintenance_history(limit: int = Query(50, ge=1, le=200)):
    """Get maintenance operation history."""
    try:
        history = maintenance_service.get_maintenance_history(limit)
        return {
            "history": history,
            "total_entries": len(history)
        }
    except Exception as e:
        logger.error(f"Failed to get maintenance history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get maintenance history: {str(e)}"
        )


@router.post("/start")
@handle_database_errors
async def start_maintenance_scheduler(interval_seconds: int = Query(3600, ge=300, le=86400)):
    """Start the automated maintenance scheduler."""
    try:
        await maintenance_service.start_maintenance_scheduler(interval_seconds)
        return {
            "status": "started",
            "interval_seconds": interval_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start maintenance scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start maintenance scheduler: {str(e)}"
        )


@router.post("/stop")
@handle_database_errors
async def stop_maintenance_scheduler():
    """Stop the automated maintenance scheduler."""
    try:
        await maintenance_service.stop_maintenance_scheduler()
        return {
            "status": "stopped",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop maintenance scheduler: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stop maintenance scheduler: {str(e)}"
        )


@router.post("/run")
@handle_database_errors
async def run_maintenance_cycle():
    """Run a complete maintenance cycle manually."""
    try:
        results = await maintenance_service.run_maintenance_cycle()
        
        successful_tasks = sum(1 for r in results if r.success)
        total_items = sum(r.items_processed for r in results)
        
        return {
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_tasks": len(results),
                "successful_tasks": successful_tasks,
                "total_items_processed": total_items
            },
            "results": [
                {
                    "task_name": r.task_name,
                    "success": r.success,
                    "items_processed": r.items_processed,
                    "duration_seconds": r.duration_seconds,
                    "error_message": r.error_message,
                    "details": r.details
                }
                for r in results
            ]
        }
    except Exception as e:
        logger.error(f"Failed to run maintenance cycle: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run maintenance cycle: {str(e)}"
        )


@router.post("/tasks/{task_name}")
async def run_maintenance_task(
    task_name: str,
    days_to_keep: int = Query(None, ge=1, le=365),
    max_entries: int = Query(None, ge=100, le=100000)
):
    """Run a specific maintenance task manually."""
    try:
        kwargs = {}
        if days_to_keep is not None:
            kwargs["days_to_keep"] = days_to_keep
        if max_entries is not None:
            kwargs["max_entries"] = max_entries
        
        result = await maintenance_service.run_manual_maintenance_task(task_name, **kwargs)
        
        return {
            "task_name": result.task_name,
            "success": result.success,
            "items_processed": result.items_processed,
            "duration_seconds": result.duration_seconds,
            "error_message": result.error_message,
            "details": result.details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to run maintenance task {task_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run maintenance task: {str(e)}"
        )


# Backup endpoints
@router.get("/backup/status")
async def get_backup_status():
    """Get the current status of the backup service."""
    try:
        status = backup_service.get_service_status()
        tools_status = await backup_service.verify_backup_tools()
        
        return {
            "service": status,
            "tools": tools_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get backup status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backup status: {str(e)}"
        )


@router.get("/backup/list")
async def list_backups():
    """List available backup files."""
    try:
        backups = backup_service.list_backups()
        return {
            "backups": backups,
            "total_backups": len(backups),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list backups: {str(e)}"
        )


@router.post("/backup/create")
async def create_backup(filename: str = Query(None)):
    """Create a new database backup."""
    try:
        result = await backup_service.create_backup(filename)
        
        if result.success:
            return {
                "status": "success",
                "backup_file": result.backup_file,
                "file_size_bytes": result.file_size_bytes,
                "duration_seconds": result.duration_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "failed",
                    "error_message": result.error_message,
                    "duration_seconds": result.duration_seconds,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Failed to create backup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create backup: {str(e)}"
        )


@router.post("/backup/restore")
async def restore_backup(backup_file: str):
    """Restore database from a backup file."""
    try:
        result = await backup_service.restore_backup(backup_file)
        
        if result.success:
            return {
                "status": "success",
                "restored_from": result.restored_from,
                "duration_seconds": result.duration_seconds,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            return JSONResponse(
                status_code=500,
                content={
                    "status": "failed",
                    "error_message": result.error_message,
                    "restored_from": result.restored_from,
                    "duration_seconds": result.duration_seconds,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
    except Exception as e:
        logger.error(f"Failed to restore backup: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to restore backup: {str(e)}"
        )


@router.get("/backup/{backup_file}/info")
async def get_backup_info(backup_file: str):
    """Get information about a specific backup file."""
    try:
        info = backup_service.get_backup_info(backup_file)
        
        if info:
            return info
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Backup file not found: {backup_file}"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get backup info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get backup info: {str(e)}"
        )


@router.get("/tasks")
async def list_maintenance_tasks():
    """List available maintenance tasks."""
    return {
        "tasks": [
            {
                "name": "cleanup_expired_cache",
                "description": "Remove expired cache entries",
                "parameters": []
            },
            {
                "name": "cleanup_old_transaction_history",
                "description": "Clean up old credit transaction history",
                "parameters": [
                    {
                        "name": "days_to_keep",
                        "type": "integer",
                        "default": 90,
                        "description": "Number of days of transaction history to keep"
                    }
                ]
            },
            {
                "name": "cleanup_old_cache_entries",
                "description": "Clean up old cache entries regardless of expiration",
                "parameters": [
                    {
                        "name": "days_to_keep",
                        "type": "integer",
                        "default": 7,
                        "description": "Number of days of cache entries to keep"
                    }
                ]
            },
            {
                "name": "optimize_cache_size",
                "description": "Optimize cache size by removing oldest entries if over limit",
                "parameters": [
                    {
                        "name": "max_entries",
                        "type": "integer",
                        "default": 10000,
                        "description": "Maximum number of cache entries to keep"
                    }
                ]
            },
            {
                "name": "run_database_vacuum",
                "description": "Run database vacuum operation (PostgreSQL specific)",
                "parameters": []
            }
        ]
    }
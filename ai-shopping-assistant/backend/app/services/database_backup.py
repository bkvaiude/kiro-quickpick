"""Database backup and recovery service."""

import logging
import asyncio
import os
import subprocess
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    """Result of a backup operation."""
    success: bool
    backup_file: Optional[str] = None
    file_size_bytes: Optional[int] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


@dataclass
class RestoreResult:
    """Result of a restore operation."""
    success: bool
    restored_from: Optional[str] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None


class DatabaseBackupService:
    """Service for database backup and recovery operations."""
    
    def __init__(self, backup_directory: str = "/tmp/db_backups"):
        self.backup_directory = Path(backup_directory)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        self._max_backup_files = 10  # Keep last 10 backups
    
    def _get_database_connection_params(self) -> Dict[str, str]:
        """Extract database connection parameters from settings."""
        db_url = settings.database.database_url
        
        # Parse the database URL
        # Format: postgresql+asyncpg://user:password@host:port/database
        if db_url.startswith("postgresql+asyncpg://"):
            db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
        
        # For this implementation, we'll assume the URL format is standard
        # In production, you might want to use a proper URL parser
        try:
            from urllib.parse import urlparse
            parsed = urlparse(db_url)
            
            return {
                "host": parsed.hostname or "localhost",
                "port": str(parsed.port or 5432),
                "database": parsed.path.lstrip('/') if parsed.path else "postgres",
                "username": parsed.username or "postgres",
                "password": parsed.password or ""
            }
        except Exception as e:
            logger.error(f"Failed to parse database URL: {e}")
            # Fallback to default values
            return {
                "host": "localhost",
                "port": "5432",
                "database": "ai_shopping_assistant",
                "username": "postgres",
                "password": ""
            }
    
    def _generate_backup_filename(self) -> str:
        """Generate a backup filename with timestamp."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        return f"ai_shopping_assistant_backup_{timestamp}.sql"
    
    async def create_backup(self, custom_filename: Optional[str] = None) -> BackupResult:
        """Create a database backup using pg_dump."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Get database connection parameters
            db_params = self._get_database_connection_params()
            
            # Generate backup filename
            backup_filename = custom_filename or self._generate_backup_filename()
            backup_path = self.backup_directory / backup_filename
            
            # Prepare pg_dump command
            cmd = [
                "pg_dump",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['username']}",
                f"--dbname={db_params['database']}",
                "--verbose",
                "--clean",
                "--no-owner",
                "--no-privileges",
                f"--file={backup_path}"
            ]
            
            # Set environment variables for authentication
            env = os.environ.copy()
            if db_params['password']:
                env['PGPASSWORD'] = db_params['password']
            
            # Run pg_dump
            logger.info(f"Starting database backup to {backup_path}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            duration = asyncio.get_event_loop().time() - start_time
            
            if process.returncode == 0:
                # Get file size
                file_size = backup_path.stat().st_size if backup_path.exists() else 0
                
                logger.info(f"Database backup completed successfully: {backup_path} ({file_size} bytes)")
                
                # Clean up old backups
                await self._cleanup_old_backups()
                
                return BackupResult(
                    success=True,
                    backup_file=str(backup_path),
                    file_size_bytes=file_size,
                    duration_seconds=duration
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Database backup failed: {error_msg}")
                
                return BackupResult(
                    success=False,
                    duration_seconds=duration,
                    error_message=error_msg
                )
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Database backup failed with exception: {e}")
            
            return BackupResult(
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def restore_backup(self, backup_file: str) -> RestoreResult:
        """Restore database from a backup file using psql."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            backup_path = Path(backup_file)
            if not backup_path.exists():
                return RestoreResult(
                    success=False,
                    error_message=f"Backup file not found: {backup_file}"
                )
            
            # Get database connection parameters
            db_params = self._get_database_connection_params()
            
            # Prepare psql command
            cmd = [
                "psql",
                f"--host={db_params['host']}",
                f"--port={db_params['port']}",
                f"--username={db_params['username']}",
                f"--dbname={db_params['database']}",
                "--verbose",
                f"--file={backup_path}"
            ]
            
            # Set environment variables for authentication
            env = os.environ.copy()
            if db_params['password']:
                env['PGPASSWORD'] = db_params['password']
            
            # Run psql
            logger.info(f"Starting database restore from {backup_path}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                env=env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            duration = asyncio.get_event_loop().time() - start_time
            
            if process.returncode == 0:
                logger.info(f"Database restore completed successfully from {backup_path}")
                
                return RestoreResult(
                    success=True,
                    restored_from=str(backup_path),
                    duration_seconds=duration
                )
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"Database restore failed: {error_msg}")
                
                return RestoreResult(
                    success=False,
                    restored_from=str(backup_path),
                    duration_seconds=duration,
                    error_message=error_msg
                )
                
        except Exception as e:
            duration = asyncio.get_event_loop().time() - start_time
            logger.error(f"Database restore failed with exception: {e}")
            
            return RestoreResult(
                success=False,
                restored_from=backup_file,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    async def _cleanup_old_backups(self):
        """Remove old backup files to maintain storage limits."""
        try:
            # Get all backup files sorted by modification time
            backup_files = [
                f for f in self.backup_directory.glob("*.sql")
                if f.is_file()
            ]
            
            # Sort by modification time (newest first)
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Remove files beyond the limit
            files_to_remove = backup_files[self._max_backup_files:]
            
            for file_path in files_to_remove:
                try:
                    file_path.unlink()
                    logger.info(f"Removed old backup file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to remove old backup file {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backup files."""
        try:
            backup_files = []
            
            for file_path in self.backup_directory.glob("*.sql"):
                if file_path.is_file():
                    stat = file_path.stat()
                    backup_files.append({
                        "filename": file_path.name,
                        "full_path": str(file_path),
                        "size_bytes": stat.st_size,
                        "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                        "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                    })
            
            # Sort by creation time (newest first)
            backup_files.sort(key=lambda x: x["created_at"], reverse=True)
            
            return backup_files
            
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return []
    
    def get_backup_info(self, backup_file: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific backup file."""
        try:
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                return None
            
            stat = backup_path.stat()
            
            return {
                "filename": backup_path.name,
                "full_path": str(backup_path),
                "size_bytes": stat.st_size,
                "size_human": self._format_file_size(stat.st_size),
                "created_at": datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc).isoformat(),
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "exists": True
            }
            
        except Exception as e:
            logger.error(f"Failed to get backup info for {backup_file}: {e}")
            return None
    
    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    async def verify_backup_tools(self) -> Dict[str, Any]:
        """Verify that required backup tools are available."""
        tools_status = {}
        
        # Check pg_dump
        try:
            process = await asyncio.create_subprocess_exec(
                "pg_dump", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode().strip()
                tools_status["pg_dump"] = {
                    "available": True,
                    "version": version
                }
            else:
                tools_status["pg_dump"] = {
                    "available": False,
                    "error": stderr.decode().strip()
                }
        except Exception as e:
            tools_status["pg_dump"] = {
                "available": False,
                "error": str(e)
            }
        
        # Check psql
        try:
            process = await asyncio.create_subprocess_exec(
                "psql", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                version = stdout.decode().strip()
                tools_status["psql"] = {
                    "available": True,
                    "version": version
                }
            else:
                tools_status["psql"] = {
                    "available": False,
                    "error": stderr.decode().strip()
                }
        except Exception as e:
            tools_status["psql"] = {
                "available": False,
                "error": str(e)
            }
        
        # Check backup directory
        tools_status["backup_directory"] = {
            "path": str(self.backup_directory),
            "exists": self.backup_directory.exists(),
            "writable": os.access(self.backup_directory, os.W_OK) if self.backup_directory.exists() else False
        }
        
        return tools_status
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get the current status of the backup service."""
        return {
            "backup_directory": str(self.backup_directory),
            "max_backup_files": self._max_backup_files,
            "available_backups": len(list(self.backup_directory.glob("*.sql"))),
            "directory_exists": self.backup_directory.exists(),
            "directory_writable": os.access(self.backup_directory, os.W_OK) if self.backup_directory.exists() else False
        }


# Global backup service instance
backup_service = DatabaseBackupService()
"""Tests for database maintenance and backup functionality."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.database_maintenance import DatabaseMaintenanceService, MaintenanceResult
from app.services.database_backup import DatabaseBackupService, BackupResult, RestoreResult


class TestDatabaseMaintenanceService:
    """Test database maintenance service functionality."""
    
    @pytest.fixture
    def maintenance_service(self):
        """Create a fresh maintenance service instance for testing."""
        return DatabaseMaintenanceService()
    
    @pytest.mark.asyncio
    async def test_start_stop_maintenance_scheduler(self, maintenance_service):
        """Test starting and stopping the maintenance scheduler."""
        assert not maintenance_service._is_running
        
        # Start scheduler
        await maintenance_service.start_maintenance_scheduler(interval_seconds=10)
        assert maintenance_service._is_running
        assert maintenance_service._maintenance_interval == 10
        assert maintenance_service._maintenance_task is not None
        
        # Stop scheduler
        await maintenance_service.stop_maintenance_scheduler()
        assert not maintenance_service._is_running
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_cache(self, maintenance_service):
        """Test expired cache cleanup."""
        with patch('app.services.database_maintenance.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_cache_repo = AsyncMock()
            mock_cache_repo.cleanup_expired_cache.return_value = 5
            
            async def mock_session_generator():
                yield mock_session
            
            mock_get_session.return_value = mock_session_generator()
            
            with patch('app.services.database_maintenance.CacheRepository', return_value=mock_cache_repo):
                result = await maintenance_service.cleanup_expired_cache()
                
                assert isinstance(result, MaintenanceResult)
                assert result.success is True
                assert result.items_processed == 5
                assert result.task_name == "cleanup_expired_cache"
                assert result.details["deleted_entries"] == 5
    
    @pytest.mark.asyncio
    async def test_cleanup_old_transaction_history(self, maintenance_service):
        """Test old transaction history cleanup."""
        with patch('app.services.database_maintenance.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_credit_repo = AsyncMock()
            mock_credit_repo.cleanup_old_transactions.return_value = 10
            
            async def mock_session_generator():
                yield mock_session
            
            mock_get_session.return_value = mock_session_generator()
            
            with patch('app.services.database_maintenance.CreditRepository', return_value=mock_credit_repo):
                result = await maintenance_service.cleanup_old_transaction_history(days_to_keep=30)
                
                assert isinstance(result, MaintenanceResult)
                assert result.success is True
                assert result.items_processed == 10
                assert result.task_name == "cleanup_old_transaction_history"
                assert result.details["deleted_transactions"] == 10
                assert result.details["days_kept"] == 30
    
    @pytest.mark.asyncio
    async def test_run_maintenance_cycle(self, maintenance_service):
        """Test running a complete maintenance cycle."""
        # Mock all maintenance tasks
        with patch.object(maintenance_service, 'cleanup_expired_cache') as mock_cache, \
             patch.object(maintenance_service, 'cleanup_old_transaction_history') as mock_transactions, \
             patch.object(maintenance_service, 'cleanup_old_cache_entries') as mock_old_cache, \
             patch.object(maintenance_service, 'optimize_cache_size') as mock_optimize:
            
            # Set up mock returns
            mock_cache.return_value = MaintenanceResult("cleanup_expired_cache", True, 5, 0.1)
            mock_transactions.return_value = MaintenanceResult("cleanup_old_transaction_history", True, 10, 0.2)
            mock_old_cache.return_value = MaintenanceResult("cleanup_old_cache_entries", True, 3, 0.1)
            mock_optimize.return_value = MaintenanceResult("optimize_cache_size", True, 0, 0.05)
            
            results = await maintenance_service.run_maintenance_cycle()
            
            assert len(results) == 4
            assert all(r.success for r in results)
            assert sum(r.items_processed for r in results) == 18
            assert maintenance_service._last_maintenance_run is not None
    
    @pytest.mark.asyncio
    async def test_run_manual_maintenance_task(self, maintenance_service):
        """Test running a specific maintenance task manually."""
        with patch.object(maintenance_service, 'cleanup_expired_cache') as mock_cleanup:
            mock_cleanup.return_value = MaintenanceResult("cleanup_expired_cache", True, 5, 0.1)
            
            result = await maintenance_service.run_manual_maintenance_task("cleanup_expired_cache")
            
            assert result.success is True
            assert result.task_name == "cleanup_expired_cache"
            assert result.items_processed == 5
            
            # Test unknown task
            result = await maintenance_service.run_manual_maintenance_task("unknown_task")
            assert result.success is False
            assert "Unknown maintenance task" in result.error_message
    
    @pytest.mark.asyncio
    async def test_get_maintenance_statistics(self, maintenance_service):
        """Test getting maintenance statistics."""
        with patch('app.services.database_maintenance.get_db_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_cache_repo = AsyncMock()
            mock_credit_repo = AsyncMock()
            
            mock_cache_repo.get_cache_statistics.return_value = {"total_entries": 100}
            mock_cache_repo.get_cache_size_info.return_value = {"entry_count": 100}
            mock_credit_repo.get_transaction_statistics.return_value = {"total_transactions": 50}
            
            async def mock_session_generator():
                yield mock_session
            
            mock_get_session.return_value = mock_session_generator()
            
            with patch('app.services.database_maintenance.CacheRepository', return_value=mock_cache_repo), \
                 patch('app.services.database_maintenance.CreditRepository', return_value=mock_credit_repo):
                
                stats = await maintenance_service.get_maintenance_statistics()
                
                assert "maintenance_scheduler" in stats
                assert "cache_status" in stats
                assert "transaction_status" in stats
                assert stats["cache_status"]["total_entries"] == 100
    
    def test_get_maintenance_history(self, maintenance_service):
        """Test getting maintenance history."""
        # Add some test results to history
        test_results = [
            MaintenanceResult("task1", True, 5, 0.1),
            MaintenanceResult("task2", False, 0, 0.2, "Error message"),
            MaintenanceResult("task3", True, 10, 0.3)
        ]
        
        maintenance_service._maintenance_history.extend(test_results)
        
        history = maintenance_service.get_maintenance_history(limit=2)
        
        assert len(history) == 2
        assert history[0]["task_name"] == "task2"  # Most recent first
        assert history[1]["task_name"] == "task3"


class TestDatabaseBackupService:
    """Test database backup service functionality."""
    
    @pytest.fixture
    def backup_service(self, tmp_path):
        """Create a backup service instance with temporary directory."""
        return DatabaseBackupService(backup_directory=str(tmp_path))
    
    def test_generate_backup_filename(self, backup_service):
        """Test backup filename generation."""
        filename = backup_service._generate_backup_filename()
        
        assert filename.startswith("ai_shopping_assistant_backup_")
        assert filename.endswith(".sql")
        assert len(filename) > 30  # Should include timestamp
    
    def test_get_database_connection_params(self, backup_service):
        """Test database connection parameter extraction."""
        with patch('app.services.database_backup.settings') as mock_settings:
            mock_settings.database.database_url = "postgresql+asyncpg://user:pass@localhost:5432/testdb"
            
            params = backup_service._get_database_connection_params()
            
            assert params["host"] == "localhost"
            assert params["port"] == "5432"
            assert params["database"] == "testdb"
            assert params["username"] == "user"
            assert params["password"] == "pass"
    
    @pytest.mark.asyncio
    async def test_create_backup_success(self, backup_service):
        """Test successful backup creation."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful pg_dump process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Success", b"")
            mock_subprocess.return_value = mock_process
            
            # Create a fake backup file
            backup_path = backup_service.backup_directory / "test_backup.sql"
            backup_path.write_text("-- Test backup content")
            
            with patch.object(backup_service, '_generate_backup_filename', return_value="test_backup.sql"), \
                 patch.object(backup_service, '_cleanup_old_backups'):
                
                result = await backup_service.create_backup()
                
                assert result.success is True
                assert result.backup_file is not None
                assert result.file_size_bytes > 0
                assert result.duration_seconds is not None
    
    @pytest.mark.asyncio
    async def test_create_backup_failure(self, backup_service):
        """Test backup creation failure."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock failed pg_dump process
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"pg_dump: error message")
            mock_subprocess.return_value = mock_process
            
            result = await backup_service.create_backup()
            
            assert result.success is False
            assert "error message" in result.error_message
            assert result.duration_seconds is not None
    
    @pytest.mark.asyncio
    async def test_restore_backup_success(self, backup_service):
        """Test successful backup restoration."""
        # Create a test backup file
        backup_file = backup_service.backup_directory / "test_restore.sql"
        backup_file.write_text("-- Test restore content")
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful psql process
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Success", b"")
            mock_subprocess.return_value = mock_process
            
            result = await backup_service.restore_backup(str(backup_file))
            
            assert result.success is True
            assert result.restored_from == str(backup_file)
            assert result.duration_seconds is not None
    
    @pytest.mark.asyncio
    async def test_restore_backup_file_not_found(self, backup_service):
        """Test restore with non-existent backup file."""
        result = await backup_service.restore_backup("nonexistent.sql")
        
        assert result.success is False
        assert "not found" in result.error_message
    
    def test_list_backups(self, backup_service):
        """Test listing backup files."""
        # Create test backup files
        backup1 = backup_service.backup_directory / "backup1.sql"
        backup2 = backup_service.backup_directory / "backup2.sql"
        
        backup1.write_text("-- Backup 1")
        backup2.write_text("-- Backup 2")
        
        backups = backup_service.list_backups()
        
        assert len(backups) == 2
        assert all("filename" in backup for backup in backups)
        assert all("size_bytes" in backup for backup in backups)
        assert all("created_at" in backup for backup in backups)
    
    def test_get_backup_info(self, backup_service):
        """Test getting backup file information."""
        # Create test backup file
        backup_file = backup_service.backup_directory / "test_info.sql"
        backup_file.write_text("-- Test backup for info")
        
        info = backup_service.get_backup_info(str(backup_file))
        
        assert info is not None
        assert info["filename"] == "test_info.sql"
        assert info["size_bytes"] > 0
        assert info["exists"] is True
        
        # Test non-existent file
        info = backup_service.get_backup_info("nonexistent.sql")
        assert info is None
    
    @pytest.mark.asyncio
    async def test_verify_backup_tools(self, backup_service):
        """Test backup tools verification."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful tool checks
            mock_process = AsyncMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"pg_dump (PostgreSQL) 13.0", b"")
            mock_subprocess.return_value = mock_process
            
            tools_status = await backup_service.verify_backup_tools()
            
            assert "pg_dump" in tools_status
            assert "psql" in tools_status
            assert "backup_directory" in tools_status
            assert tools_status["pg_dump"]["available"] is True
            assert tools_status["psql"]["available"] is True
    
    def test_get_service_status(self, backup_service):
        """Test getting service status."""
        status = backup_service.get_service_status()
        
        assert "backup_directory" in status
        assert "max_backup_files" in status
        assert "available_backups" in status
        assert "directory_exists" in status
        assert "directory_writable" in status


@pytest.mark.asyncio
async def test_maintenance_integration():
    """Integration test for maintenance functionality."""
    maintenance_service = DatabaseMaintenanceService()
    
    try:
        # Test that we can get statistics without errors
        stats = await maintenance_service.get_maintenance_statistics()
        assert "maintenance_scheduler" in stats
        
        # Test history functionality
        history = maintenance_service.get_maintenance_history()
        assert isinstance(history, list)
        
    finally:
        await maintenance_service.stop_maintenance_scheduler()


def test_backup_integration(tmp_path):
    """Integration test for backup functionality."""
    backup_service = DatabaseBackupService(backup_directory=str(tmp_path))
    
    # Test service status
    status = backup_service.get_service_status()
    assert status["directory_exists"] is True
    
    # Test listing empty backups
    backups = backup_service.list_backups()
    assert backups == []
"""Tests for database monitoring and health check functionality."""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from app.database.health import DatabaseHealthChecker, health_checker
from app.services.monitoring_service import DatabaseMonitoringService, MetricSnapshot


class TestDatabaseHealthChecker:
    """Test database health checking functionality."""
    
    @pytest.fixture
    def health_checker_instance(self):
        """Create a fresh health checker instance for testing."""
        return DatabaseHealthChecker()
    
    @pytest.mark.asyncio
    async def test_check_health_success(self, health_checker_instance):
        """Test successful health check."""
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager.health_check = AsyncMock(return_value=True)
            mock_manager.get_connection_info = AsyncMock(return_value={
                "status": "initialized",
                "pool_size": 10,
                "checked_out": 2
            })
            
            result = await health_checker_instance.check_health()
            
            assert result["healthy"] is True
            assert result["cached"] is False
            assert "check_duration_seconds" in result
            assert "connection_pool" in result
            assert result["connection_pool"]["pool_size"] == 10
    
    @pytest.mark.asyncio
    async def test_check_health_failure(self, health_checker_instance):
        """Test health check failure."""
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager.health_check = AsyncMock(side_effect=Exception("Connection failed"))
            
            result = await health_checker_instance.check_health()
            
            assert result["healthy"] is False
            assert "error" in result
            assert result["error"] == "Connection failed"
    
    @pytest.mark.asyncio
    async def test_check_health_caching(self, health_checker_instance):
        """Test health check result caching."""
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager.health_check = AsyncMock(return_value=True)
            mock_manager.get_connection_info = AsyncMock(return_value={"status": "initialized"})
            
            # First call
            result1 = await health_checker_instance.check_health()
            assert result1["cached"] is False
            
            # Second call should be cached
            result2 = await health_checker_instance.check_health()
            assert result2["cached"] is True
            
            # Force check should bypass cache
            result3 = await health_checker_instance.check_health(force_check=True)
            assert result3["cached"] is False
    
    @pytest.mark.asyncio
    async def test_check_basic_connectivity(self, health_checker_instance):
        """Test basic connectivity check."""
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager.health_check = AsyncMock(return_value=True)
            
            result = await health_checker_instance.check_basic_connectivity()
            assert result is True
            
            mock_manager.health_check = AsyncMock(side_effect=Exception("Connection failed"))
            result = await health_checker_instance.check_basic_connectivity()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, health_checker_instance):
        """Test performance metrics collection."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_session.execute = AsyncMock(return_value=mock_result)
        
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager._initialized = True
            mock_manager.get_session = AsyncMock(return_value=mock_session)
            
            result = await health_checker_instance.get_performance_metrics()
            
            assert result["status"] == "available"
            assert "metrics" in result
            assert "collected_at" in result
    
    @pytest.mark.asyncio
    async def test_get_connection_pool_metrics(self, health_checker_instance):
        """Test connection pool metrics."""
        with patch('app.database.health.database_manager') as mock_manager:
            mock_manager.get_connection_info = AsyncMock(return_value={
                "status": "initialized",
                "pool_size": 10,
                "checked_out": 3,
                "checked_in": 7,
                "overflow": 0
            })
            
            result = await health_checker_instance.get_connection_pool_metrics()
            
            assert result["status"] == "initialized"
            assert result["utilization_percent"] == 30.0
            assert result["available_connections"] == 7
            assert result["health_status"] == "healthy"


class TestDatabaseMonitoringService:
    """Test database monitoring service functionality."""
    
    @pytest.fixture
    def monitoring_service(self):
        """Create a fresh monitoring service instance for testing."""
        return DatabaseMonitoringService(max_snapshots=10)
    
    @pytest.mark.asyncio
    async def test_collect_snapshot(self, monitoring_service):
        """Test snapshot collection."""
        with patch('app.services.monitoring_service.health_checker') as mock_checker:
            mock_checker.check_health = AsyncMock(return_value={
                "healthy": True,
                "check_duration_seconds": 0.1
            })
            mock_checker.get_connection_pool_metrics = AsyncMock(return_value={
                "utilization_percent": 25.0
            })
            mock_checker.get_performance_metrics = AsyncMock(return_value={
                "metrics": {
                    "active_connections": 3,
                    "total_connections": 10
                }
            })
            
            snapshot = await monitoring_service.collect_snapshot()
            
            assert isinstance(snapshot, MetricSnapshot)
            assert snapshot.healthy is True
            assert snapshot.response_time_seconds == 0.1
            assert snapshot.connection_pool_utilization == 25.0
            assert snapshot.active_connections == 3
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitoring_service):
        """Test starting and stopping monitoring."""
        assert not monitoring_service._is_monitoring
        
        # Start monitoring
        await monitoring_service.start_monitoring(interval_seconds=1)
        assert monitoring_service._is_monitoring
        assert monitoring_service._monitoring_task is not None
        
        # Stop monitoring
        await monitoring_service.stop_monitoring()
        assert not monitoring_service._is_monitoring
    
    def test_get_recent_snapshots(self, monitoring_service):
        """Test getting recent snapshots."""
        now = datetime.now(timezone.utc)
        
        # Add some test snapshots
        old_snapshot = MetricSnapshot(
            timestamp=now - timedelta(hours=2),
            healthy=True,
            response_time_seconds=0.1,
            connection_pool_utilization=20.0
        )
        recent_snapshot = MetricSnapshot(
            timestamp=now - timedelta(minutes=30),
            healthy=True,
            response_time_seconds=0.2,
            connection_pool_utilization=30.0
        )
        
        monitoring_service._snapshots.extend([old_snapshot, recent_snapshot])
        
        # Get snapshots from last 60 minutes
        recent = monitoring_service.get_recent_snapshots(minutes=60)
        assert len(recent) == 1
        assert recent[0] == recent_snapshot
    
    def test_get_summary_statistics(self, monitoring_service):
        """Test summary statistics calculation."""
        now = datetime.now(timezone.utc)
        
        # Add test snapshots
        snapshots = [
            MetricSnapshot(
                timestamp=now - timedelta(minutes=i),
                healthy=True,
                response_time_seconds=0.1 + (i * 0.01),
                connection_pool_utilization=20.0 + i
            )
            for i in range(5)
        ]
        
        monitoring_service._snapshots.extend(snapshots)
        
        summary = monitoring_service.get_summary_statistics(minutes=60)
        
        assert summary["snapshot_count"] == 5
        assert summary["uptime_percentage"] == 100.0
        assert "response_time" in summary
        assert "connection_pool" in summary
        assert summary["health_status"] == "healthy"
    
    def test_get_monitoring_status(self, monitoring_service):
        """Test getting monitoring status."""
        status = monitoring_service.get_monitoring_status()
        
        assert "is_monitoring" in status
        assert "interval_seconds" in status
        assert "snapshots_stored" in status
        assert "max_snapshots" in status
    
    def test_clear_snapshots(self, monitoring_service):
        """Test clearing snapshots."""
        # Add a test snapshot
        snapshot = MetricSnapshot(
            timestamp=datetime.now(timezone.utc),
            healthy=True,
            response_time_seconds=0.1,
            connection_pool_utilization=20.0
        )
        monitoring_service._snapshots.append(snapshot)
        
        assert len(monitoring_service._snapshots) == 1
        
        monitoring_service.clear_snapshots()
        assert len(monitoring_service._snapshots) == 0


class TestMetricSnapshot:
    """Test MetricSnapshot functionality."""
    
    def test_to_dict(self):
        """Test converting snapshot to dictionary."""
        timestamp = datetime.now(timezone.utc)
        snapshot = MetricSnapshot(
            timestamp=timestamp,
            healthy=True,
            response_time_seconds=0.1,
            connection_pool_utilization=25.0,
            active_connections=3,
            total_connections=10,
            database_size="1.2 MB"
        )
        
        result = snapshot.to_dict()
        
        assert result["timestamp"] == timestamp.isoformat()
        assert result["healthy"] is True
        assert result["response_time_seconds"] == 0.1
        assert result["connection_pool_utilization"] == 25.0
        assert result["active_connections"] == 3
        assert result["total_connections"] == 10
        assert result["database_size"] == "1.2 MB"


@pytest.mark.asyncio
async def test_monitoring_integration():
    """Integration test for monitoring functionality."""
    monitoring_service = DatabaseMonitoringService(max_snapshots=5)
    
    try:
        # Test that we can collect a snapshot without errors
        snapshot = await monitoring_service.collect_snapshot()
        assert isinstance(snapshot, MetricSnapshot)
        
        # Test monitoring status
        status = monitoring_service.get_monitoring_status()
        assert status["snapshots_stored"] == 1
        
        # Test summary with real data
        summary = monitoring_service.get_summary_statistics(minutes=60)
        assert summary["snapshot_count"] == 1
        
    finally:
        await monitoring_service.stop_monitoring()
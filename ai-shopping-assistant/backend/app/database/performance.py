"""Database performance monitoring and optimization utilities."""

import logging
import time
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


@dataclass
class QueryPerformanceMetrics:
    """Metrics for database query performance."""
    query_hash: str
    query_type: str  # 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    execution_time_ms: float
    rows_affected: int
    timestamp: datetime = field(default_factory=datetime.utcnow)
    table_name: Optional[str] = None
    error: Optional[str] = None


class DatabasePerformanceMonitor:
    """Monitor and track database performance metrics."""
    
    def __init__(self, max_metrics: int = 1000):
        self.max_metrics = max_metrics
        self.metrics: List[QueryPerformanceMetrics] = []
        self._lock = asyncio.Lock()
    
    async def record_query_metrics(self, metrics: QueryPerformanceMetrics):
        """Record query performance metrics."""
        async with self._lock:
            self.metrics.append(metrics)
            
            # Keep only the most recent metrics
            if len(self.metrics) > self.max_metrics:
                self.metrics = self.metrics[-self.max_metrics:]
            
            # Log slow queries
            if metrics.execution_time_ms > 1000:  # Queries slower than 1 second
                logger.warning(
                    f"Slow query detected: {metrics.query_type} on {metrics.table_name} "
                    f"took {metrics.execution_time_ms:.2f}ms"
                )
    
    async def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        async with self._lock:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff_time]
            
            if not recent_metrics:
                return {
                    "period_hours": hours,
                    "total_queries": 0,
                    "avg_execution_time_ms": 0,
                    "slow_queries": 0,
                    "errors": 0
                }
            
            total_queries = len(recent_metrics)
            avg_execution_time = sum(m.execution_time_ms for m in recent_metrics) / total_queries
            slow_queries = len([m for m in recent_metrics if m.execution_time_ms > 1000])
            errors = len([m for m in recent_metrics if m.error])
            
            # Group by query type
            by_type = {}
            for metric in recent_metrics:
                if metric.query_type not in by_type:
                    by_type[metric.query_type] = {
                        "count": 0,
                        "avg_time_ms": 0,
                        "total_time_ms": 0
                    }
                by_type[metric.query_type]["count"] += 1
                by_type[metric.query_type]["total_time_ms"] += metric.execution_time_ms
            
            # Calculate averages
            for query_type in by_type:
                stats = by_type[query_type]
                stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
                del stats["total_time_ms"]  # Remove total to keep response clean
            
            return {
                "period_hours": hours,
                "total_queries": total_queries,
                "avg_execution_time_ms": round(avg_execution_time, 2),
                "slow_queries": slow_queries,
                "errors": errors,
                "by_query_type": by_type
            }
    
    async def get_slowest_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get the slowest queries recorded."""
        async with self._lock:
            sorted_metrics = sorted(
                self.metrics,
                key=lambda m: m.execution_time_ms,
                reverse=True
            )
            
            return [
                {
                    "query_type": m.query_type,
                    "table_name": m.table_name,
                    "execution_time_ms": m.execution_time_ms,
                    "rows_affected": m.rows_affected,
                    "timestamp": m.timestamp.isoformat(),
                    "error": m.error
                }
                for m in sorted_metrics[:limit]
            ]


# Global performance monitor instance
performance_monitor = DatabasePerformanceMonitor()


@asynccontextmanager
async def monitor_query_performance(
    session: AsyncSession,
    query_type: str,
    table_name: Optional[str] = None,
    query_hash: Optional[str] = None
):
    """Context manager to monitor query performance."""
    start_time = time.time()
    rows_affected = 0
    error = None
    
    try:
        yield
        # Try to get rows affected from session info
        if hasattr(session, 'rowcount'):
            rows_affected = session.rowcount or 0
    except Exception as e:
        error = str(e)
        raise
    finally:
        execution_time_ms = (time.time() - start_time) * 1000
        
        metrics = QueryPerformanceMetrics(
            query_hash=query_hash or f"{query_type}_{table_name}_{int(time.time())}",
            query_type=query_type,
            execution_time_ms=execution_time_ms,
            rows_affected=rows_affected,
            table_name=table_name,
            error=error
        )
        
        await performance_monitor.record_query_metrics(metrics)


class DatabaseAnalyzer:
    """Analyze database performance and provide optimization recommendations."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def analyze_table_sizes(self) -> Dict[str, Any]:
        """Analyze table sizes and storage usage."""
        try:
            # PostgreSQL-specific query for table sizes
            result = await self.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    attname,
                    n_distinct,
                    correlation,
                    most_common_vals,
                    most_common_freqs
                FROM pg_stats 
                WHERE schemaname = 'public' 
                AND tablename IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
                ORDER BY tablename, attname;
            """))
            
            stats = {}
            for row in result:
                table = row.tablename
                if table not in stats:
                    stats[table] = {}
                
                stats[table][row.attname] = {
                    "n_distinct": row.n_distinct,
                    "correlation": row.correlation,
                    "most_common_vals": row.most_common_vals,
                    "most_common_freqs": row.most_common_freqs
                }
            
            return stats
        except SQLAlchemyError as e:
            logger.error(f"Failed to analyze table sizes: {e}")
            return {}
    
    async def analyze_index_usage(self) -> Dict[str, Any]:
        """Analyze index usage statistics."""
        try:
            # PostgreSQL-specific query for index usage
            result = await self.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_tup_read,
                    idx_tup_fetch,
                    idx_scan
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                AND tablename IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
                ORDER BY idx_scan DESC;
            """))
            
            index_stats = []
            for row in result:
                index_stats.append({
                    "schema": row.schemaname,
                    "table": row.tablename,
                    "index": row.indexname,
                    "tuples_read": row.idx_tup_read,
                    "tuples_fetched": row.idx_tup_fetch,
                    "scans": row.idx_scan
                })
            
            return {"index_usage": index_stats}
        except SQLAlchemyError as e:
            logger.error(f"Failed to analyze index usage: {e}")
            return {"index_usage": []}
    
    async def analyze_query_performance(self) -> Dict[str, Any]:
        """Analyze query performance from pg_stat_statements if available."""
        try:
            # Check if pg_stat_statements extension is available
            result = await self.session.execute(text("""
                SELECT EXISTS(
                    SELECT 1 FROM pg_extension WHERE extname = 'pg_stat_statements'
                ) as has_pg_stat_statements;
            """))
            
            has_extension = result.scalar()
            
            if not has_extension:
                return {
                    "pg_stat_statements_available": False,
                    "message": "pg_stat_statements extension not available"
                }
            
            # Get top queries by execution time
            result = await self.session.execute(text("""
                SELECT 
                    query,
                    calls,
                    total_exec_time,
                    mean_exec_time,
                    rows,
                    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
                FROM pg_stat_statements 
                WHERE query LIKE '%user_credits%' 
                   OR query LIKE '%credit_transactions%'
                   OR query LIKE '%user_consents%'
                   OR query LIKE '%query_cache%'
                ORDER BY total_exec_time DESC 
                LIMIT 10;
            """))
            
            query_stats = []
            for row in result:
                query_stats.append({
                    "query": row.query[:200] + "..." if len(row.query) > 200 else row.query,
                    "calls": row.calls,
                    "total_exec_time_ms": row.total_exec_time,
                    "mean_exec_time_ms": row.mean_exec_time,
                    "rows": row.rows,
                    "cache_hit_percent": row.hit_percent
                })
            
            return {
                "pg_stat_statements_available": True,
                "top_queries": query_stats
            }
        except SQLAlchemyError as e:
            logger.error(f"Failed to analyze query performance: {e}")
            return {
                "pg_stat_statements_available": False,
                "error": str(e)
            }
    
    async def get_optimization_recommendations(self) -> List[str]:
        """Generate optimization recommendations based on analysis."""
        recommendations = []
        
        try:
            # Check for missing indexes on foreign key columns
            result = await self.session.execute(text("""
                SELECT 
                    t.table_name,
                    c.column_name
                FROM information_schema.tables t
                JOIN information_schema.columns c ON t.table_name = c.table_name
                WHERE t.table_schema = 'public'
                AND t.table_name IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
                AND c.column_name LIKE '%_id'
                AND NOT EXISTS (
                    SELECT 1 FROM pg_indexes 
                    WHERE tablename = t.table_name 
                    AND indexdef LIKE '%' || c.column_name || '%'
                );
            """))
            
            missing_indexes = result.fetchall()
            for row in missing_indexes:
                recommendations.append(
                    f"Consider adding index on {row.table_name}.{row.column_name}"
                )
            
            # Check for unused indexes
            result = await self.session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_stat_user_indexes 
                WHERE schemaname = 'public'
                AND tablename IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
                AND idx_scan = 0;
            """))
            
            unused_indexes = result.fetchall()
            for row in unused_indexes:
                recommendations.append(
                    f"Consider dropping unused index {row.indexname} on {row.tablename}"
                )
            
            # Check table sizes for partitioning recommendations
            result = await self.session.execute(text("""
                SELECT 
                    tablename,
                    n_tup_ins + n_tup_upd + n_tup_del as total_modifications
                FROM pg_stat_user_tables 
                WHERE schemaname = 'public'
                AND tablename IN ('credit_transactions', 'query_cache')
                AND n_tup_ins + n_tup_upd + n_tup_del > 100000;
            """))
            
            high_activity_tables = result.fetchall()
            for row in high_activity_tables:
                if row.tablename == 'credit_transactions':
                    recommendations.append(
                        "Consider partitioning credit_transactions table by timestamp for better performance"
                    )
                elif row.tablename == 'query_cache':
                    recommendations.append(
                        "Consider implementing automatic cache cleanup for query_cache table"
                    )
            
        except SQLAlchemyError as e:
            logger.error(f"Failed to generate optimization recommendations: {e}")
            recommendations.append("Unable to analyze database for optimization recommendations")
        
        return recommendations


async def run_performance_analysis(session: AsyncSession) -> Dict[str, Any]:
    """Run comprehensive performance analysis."""
    analyzer = DatabaseAnalyzer(session)
    
    analysis_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "table_stats": await analyzer.analyze_table_sizes(),
        "index_usage": await analyzer.analyze_index_usage(),
        "query_performance": await analyzer.analyze_query_performance(),
        "recommendations": await analyzer.get_optimization_recommendations(),
        "performance_summary": await performance_monitor.get_performance_summary(hours=24),
        "slowest_queries": await performance_monitor.get_slowest_queries(limit=5)
    }
    
    return analysis_results


def create_performance_decorator(query_type: str, table_name: Optional[str] = None):
    """Decorator factory for monitoring repository method performance."""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            # Extract session from args (assuming it's the first argument after self)
            session = None
            if len(args) > 0 and hasattr(args[0], 'session'):
                session = args[0].session
            
            if session:
                async with monitor_query_performance(
                    session, query_type, table_name, func.__name__
                ):
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        return wrapper
    return decorator
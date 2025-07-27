#!/usr/bin/env python3
"""Load test for PostgreSQL performance under concurrent operations."""

import asyncio
import time
import random
from datetime import datetime, timedelta

from app.database.manager import database_manager
from app.database.models import UserCreditsDB, CreditTransactionDB, QueryCacheDB
from app.database.repositories.credit_repository import CreditRepository
from app.database.repositories.cache_repository import CacheRepository
from app.database.batch_operations import CreditBatchOperations


async def create_test_users(user_count: int = 100):
    """Create test users for load testing."""
    print(f"🔧 Creating {user_count} test users...")
    
    session = await database_manager.get_session()
    try:
        credit_repo = CreditRepository(session)
        
        user_ids = []
        for i in range(user_count):
            user_id = f"load_test_user_{i}_{int(time.time())}"
            user_credits = UserCreditsDB(
                user_id=user_id,
                is_guest=random.choice([True, False]),
                available_credits=random.randint(1, 50),
                max_credits=50,
                last_reset_timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            )
            await credit_repo.create_user_credits(user_credits)
            user_ids.append(user_id)
        
        await session.commit()
        print(f"✅ Created {len(user_ids)} test users")
        return user_ids
        
    finally:
        await session.close()


async def cleanup_test_users(user_ids: list):
    """Clean up test users."""
    print(f"🧹 Cleaning up {len(user_ids)} test users...")
    
    session = await database_manager.get_session()
    try:
        credit_repo = CreditRepository(session)
        
        for user_id in user_ids:
            await credit_repo.delete_user_credits(user_id)
        
        await session.commit()
        print("✅ Cleanup completed")
        
    finally:
        await session.close()


async def concurrent_credit_operations(user_ids: list, operations_per_user: int = 5):
    """Test concurrent credit operations."""
    print(f"🔄 Testing concurrent credit operations ({len(user_ids)} users, {operations_per_user} ops each)...")
    
    async def user_operations(user_id: str):
        """Perform operations for a single user."""
        session = await database_manager.get_session()
        try:
            credit_repo = CreditRepository(session)
            
            operations_completed = 0
            
            for _ in range(operations_per_user):
                # Random operation
                operation = random.choice(['get', 'update', 'transaction'])
                
                if operation == 'get':
                    await credit_repo.get_user_credits(user_id)
                elif operation == 'update':
                    new_credits = random.randint(0, 50)
                    await credit_repo.update_user_credits(user_id, available_credits=new_credits)
                elif operation == 'transaction':
                    transaction = CreditTransactionDB(
                        user_id=user_id,
                        transaction_type=random.choice(['deduct', 'grant']),
                        amount=random.randint(-10, 10),
                        description=f'Load test transaction'
                    )
                    await credit_repo.create_transaction(transaction)
                
                operations_completed += 1
            
            await session.commit()
            return operations_completed
            
        except Exception as e:
            await session.rollback()
            return 0
        finally:
            await session.close()
    
    # Run concurrent operations
    start_time = time.time()
    
    tasks = [user_operations(user_id) for user_id in user_ids]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    
    # Calculate results
    successful_operations = sum(r for r in results if isinstance(r, int))
    total_expected = len(user_ids) * operations_per_user
    success_rate = (successful_operations / total_expected) * 100
    
    print(f"✅ Concurrent operations completed:")
    print(f"   • Total time: {end_time - start_time:.2f}s")
    print(f"   • Operations completed: {successful_operations}/{total_expected}")
    print(f"   • Success rate: {success_rate:.1f}%")
    print(f"   • Operations per second: {successful_operations / (end_time - start_time):.1f}")
    
    return success_rate > 90  # 90% success rate threshold


async def concurrent_cache_operations(cache_entries: int = 200):
    """Test concurrent cache operations."""
    print(f"💾 Testing concurrent cache operations ({cache_entries} entries)...")
    
    async def cache_operations(entry_id: int):
        """Perform cache operations."""
        session = await database_manager.get_session()
        try:
            cache_repo = CacheRepository(session)
            
            # Create cache entry
            query_hash = f"load_test_hash_{entry_id}_{int(time.time())}"
            cache_entry = QueryCacheDB(
                query_hash=query_hash,
                result={
                    "test_data": f"entry_{entry_id}",
                    "products": list(range(entry_id % 10)),
                    "timestamp": datetime.utcnow().isoformat()
                },
                cached_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            
            await cache_repo.cache_result(cache_entry)
            
            # Retrieve cache entry
            retrieved = await cache_repo.get_cached_result(query_hash)
            
            # Update cache entry (upsert)
            cache_entry.result["updated"] = True
            await cache_repo.cache_result(cache_entry)
            
            await session.commit()
            return query_hash
            
        except Exception as e:
            await session.rollback()
            return None
        finally:
            await session.close()
    
    # Run concurrent cache operations
    start_time = time.time()
    
    tasks = [cache_operations(i) for i in range(cache_entries)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    
    # Calculate results
    successful_operations = sum(1 for r in results if r is not None and not isinstance(r, Exception))
    success_rate = (successful_operations / cache_entries) * 100
    
    print(f"✅ Concurrent cache operations completed:")
    print(f"   • Total time: {end_time - start_time:.2f}s")
    print(f"   • Operations completed: {successful_operations}/{cache_entries}")
    print(f"   • Success rate: {success_rate:.1f}%")
    print(f"   • Operations per second: {successful_operations / (end_time - start_time):.1f}")
    
    # Cleanup cache entries
    session = await database_manager.get_session()
    try:
        cache_repo = CacheRepository(session)
        cleanup_count = await cache_repo.clear_cache()
        await session.commit()
        print(f"🧹 Cleaned up {cleanup_count} cache entries")
    finally:
        await session.close()
    
    return success_rate > 90


async def batch_operations_performance(user_count: int = 100):
    """Test batch operations performance."""
    print(f"📦 Testing batch operations performance ({user_count} users)...")
    
    session = await database_manager.get_session()
    try:
        batch_ops = CreditBatchOperations(session)
        credit_repo = CreditRepository(session)
        
        # Create users for batch operations
        user_ids = []
        for i in range(user_count):
            user_id = f"batch_perf_user_{i}_{int(time.time())}"
            user_credits = UserCreditsDB(
                user_id=user_id,
                is_guest=False,
                available_credits=random.randint(1, 25),
                max_credits=50,
                last_reset_timestamp=datetime.utcnow() - timedelta(hours=25)
            )
            await credit_repo.create_user_credits(user_credits)
            user_ids.append(user_id)
        
        await session.commit()
        
        # Test batch reset performance
        start_time = time.time()
        reset_count = await batch_ops.batch_reset_credits(user_ids, datetime.utcnow())
        reset_time = time.time() - start_time
        
        print(f"✅ Batch reset performance:")
        print(f"   • Users reset: {reset_count}")
        print(f"   • Time taken: {reset_time:.3f}s")
        print(f"   • Users per second: {reset_count / reset_time:.1f}")
        
        # Test batch deduction performance
        deductions = [
            {"user_id": user_id, "amount": random.randint(1, 5), "description": "Load test deduction"}
            for user_id in user_ids
        ]
        
        start_time = time.time()
        deduct_count = await batch_ops.batch_deduct_credits(deductions)
        deduct_time = time.time() - start_time
        
        print(f"✅ Batch deduction performance:")
        print(f"   • Users processed: {deduct_count}")
        print(f"   • Time taken: {deduct_time:.3f}s")
        print(f"   • Users per second: {deduct_count / deduct_time:.1f}")
        
        # Cleanup
        for user_id in user_ids:
            await credit_repo.delete_user_credits(user_id)
        
        await session.commit()
        
        # Performance thresholds
        return reset_time < 1.0 and deduct_time < 1.0  # Should complete within 1 second
        
    finally:
        await session.close()


async def connection_pool_stress_test():
    """Test connection pool under stress."""
    print("🏊 Testing connection pool under stress...")
    
    async def connection_test():
        """Test a single connection."""
        session = await database_manager.get_session()
        try:
            # Simple query to test connection
            result = await session.execute("SELECT 1")
            return result.scalar() == 1
        finally:
            await session.close()
    
    # Test with many concurrent connections
    connection_count = 50
    start_time = time.time()
    
    tasks = [connection_test() for _ in range(connection_count)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    
    successful_connections = sum(1 for r in results if r is True)
    success_rate = (successful_connections / connection_count) * 100
    
    print(f"✅ Connection pool stress test:")
    print(f"   • Concurrent connections: {connection_count}")
    print(f"   • Successful connections: {successful_connections}")
    print(f"   • Success rate: {success_rate:.1f}%")
    print(f"   • Total time: {end_time - start_time:.2f}s")
    
    # Check pool status
    pool_info = await database_manager.get_connection_info()
    print(f"📊 Pool status after stress test: {pool_info}")
    
    return success_rate > 95  # 95% success rate threshold


async def main():
    """Run load performance tests."""
    print("🚀 Starting PostgreSQL Load Performance Tests")
    print("=" * 60)
    
    await database_manager.initialize()
    
    # Test configuration
    user_count = 50  # Reduced for faster testing
    
    tests = []
    
    try:
        # Create test users
        user_ids = await create_test_users(user_count)
        
        # Run load tests
        tests = [
            ("Connection Pool Stress Test", connection_pool_stress_test()),
            ("Concurrent Credit Operations", concurrent_credit_operations(user_ids[:20], 3)),  # Subset for speed
            ("Concurrent Cache Operations", concurrent_cache_operations(50)),  # Reduced count
            ("Batch Operations Performance", batch_operations_performance(30)),  # Reduced count
        ]
        
        results = []
        
        for test_name, test_coro in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = await test_coro
                results.append((test_name, result))
                if result:
                    print(f"✅ {test_name}: PASSED")
                else:
                    print(f"❌ {test_name}: FAILED")
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {e}")
                results.append((test_name, False))
        
        # Cleanup
        await cleanup_test_users(user_ids)
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        results = [("Setup", False)]
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 LOAD TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All load tests passed! PostgreSQL performance is optimized.")
        return True
    else:
        print("⚠️  Some load tests failed. Performance may need further optimization.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
#!/usr/bin/env python3
"""Simple verification script for PostgreSQL performance optimizations."""

import asyncio
import time
from datetime import datetime, timedelta

from app.database.manager import database_manager
from app.database.models import UserCreditsDB, CreditTransactionDB, UserConsentDB, QueryCacheDB
from app.database.repositories.credit_repository import CreditRepository
from app.database.repositories.consent_repository import ConsentRepository
from app.database.repositories.cache_repository import CacheRepository
from app.database.batch_operations import CreditBatchOperations
from app.database.performance import run_performance_analysis
from sqlalchemy import text


async def test_database_connection():
    """Test database connection and health."""
    print("🔍 Testing database connection...")
    
    await database_manager.initialize()
    
    # Test health check
    health_check = await database_manager.health_check()
    assert health_check, "Database health check failed"
    print("✅ Database connection healthy")
    
    # Test connection info
    conn_info = await database_manager.get_connection_info()
    print(f"📊 Connection pool info: {conn_info}")
    
    return True


async def test_performance_indexes():
    """Test that performance indexes are created."""
    print("🔍 Testing performance indexes...")
    
    session = await database_manager.get_session()
    try:
        # Check for performance indexes
        result = await session.execute(text("""
            SELECT indexname, tablename 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('user_credits', 'credit_transactions', 'user_consents', 'query_cache')
            ORDER BY tablename, indexname
        """))
        
        indexes = result.fetchall()
        
        print(f"📈 Found {len(indexes)} indexes:")
        for idx in indexes:
            print(f"   • {idx.tablename}.{idx.indexname}")
        
        # Check for specific performance indexes
        index_names = [idx.indexname for idx in indexes]
        
        expected_indexes = [
            'idx_credit_transactions_user_timestamp_desc',
            'idx_user_credits_reset_lookup',
            'idx_query_cache_cleanup'
        ]
        
        for expected_idx in expected_indexes:
            if expected_idx in index_names:
                print(f"✅ Performance index found: {expected_idx}")
            else:
                print(f"⚠️  Performance index missing: {expected_idx}")
        
        await session.commit()
        return len(indexes) > 10
        
    finally:
        await session.close()


async def test_basic_crud_operations():
    """Test basic CRUD operations."""
    print("🔍 Testing basic CRUD operations...")
    
    session = await database_manager.get_session()
    try:
        credit_repo = CreditRepository(session)
        
        # Test user creation
        user_id = f"test_user_{int(time.time())}"
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=50,
            max_credits=50
        )
        
        created_user = await credit_repo.create_user_credits(user_credits)
        print(f"✅ Created user: {created_user.user_id}")
        
        # Test user retrieval
        retrieved_user = await credit_repo.get_user_credits(user_id)
        assert retrieved_user is not None
        print(f"✅ Retrieved user: {retrieved_user.user_id}")
        
        # Test transaction creation
        transaction = CreditTransactionDB(
            user_id=user_id,
            transaction_type='deduct',
            amount=-5,
            description='Test deduction'
        )
        
        created_transaction = await credit_repo.create_transaction(transaction)
        print(f"✅ Created transaction: {created_transaction.id}")
        
        # Cleanup
        await credit_repo.delete_user_credits(user_id)
        print(f"✅ Cleaned up user: {user_id}")
        
        await session.commit()
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ CRUD operations failed: {e}")
        return False
    finally:
        await session.close()


async def test_batch_operations():
    """Test batch operations performance."""
    print("🔍 Testing batch operations...")
    
    session = await database_manager.get_session()
    try:
        batch_ops = CreditBatchOperations(session)
        credit_repo = CreditRepository(session)
        
        # Create test users
        user_count = 10
        user_ids = [f"batch_user_{i}_{int(time.time())}" for i in range(user_count)]
        
        for user_id in user_ids:
            user_credits = UserCreditsDB(
                user_id=user_id,
                is_guest=False,
                available_credits=5,
                max_credits=10,
                last_reset_timestamp=datetime.utcnow() - timedelta(hours=25)
            )
            await credit_repo.create_user_credits(user_credits)
        
        await session.commit()
        
        # Test batch reset performance
        start_time = time.time()
        reset_count = await batch_ops.batch_reset_credits(user_ids, datetime.utcnow())
        batch_time = time.time() - start_time
        
        print(f"✅ Batch reset {reset_count} users in {batch_time:.3f}s")
        
        # Cleanup
        for user_id in user_ids:
            await credit_repo.delete_user_credits(user_id)
        
        await session.commit()
        return batch_time < 2.0  # Should be fast
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Batch operations failed: {e}")
        return False
    finally:
        await session.close()


async def test_cache_operations():
    """Test cache operations."""
    print("🔍 Testing cache operations...")
    
    session = await database_manager.get_session()
    try:
        cache_repo = CacheRepository(session)
        
        # Test cache creation
        query_hash = f"test_hash_{int(time.time())}"
        cache_entry = QueryCacheDB(
            query_hash=query_hash,
            result={"test": "data", "products": [1, 2, 3]},
            cached_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        cached_result = await cache_repo.cache_result(cache_entry)
        print(f"✅ Cached result: {cached_result.query_hash}")
        
        # Test cache retrieval
        retrieved_cache = await cache_repo.get_cached_result(query_hash)
        assert retrieved_cache is not None
        print(f"✅ Retrieved cache: {retrieved_cache.query_hash}")
        
        # Test cache statistics
        stats = await cache_repo.get_cache_statistics()
        print(f"📊 Cache stats: {stats['total_entries']} entries, {stats['active_entries']} active")
        
        # Cleanup
        await cache_repo.invalidate_cache_entry(query_hash)
        
        await session.commit()
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Cache operations failed: {e}")
        return False
    finally:
        await session.close()


async def test_performance_monitoring():
    """Test performance monitoring."""
    print("🔍 Testing performance monitoring...")
    
    session = await database_manager.get_session()
    try:
        # Run performance analysis
        analysis = await run_performance_analysis(session)
        
        print("📊 Performance analysis completed:")
        print(f"   • Total queries in last 24h: {analysis['performance_summary']['total_queries']}")
        print(f"   • Average execution time: {analysis['performance_summary']['avg_execution_time_ms']:.2f}ms")
        print(f"   • Recommendations: {len(analysis['recommendations'])}")
        
        for rec in analysis['recommendations'][:3]:  # Show first 3 recommendations
            print(f"   • {rec}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance monitoring failed: {e}")
        return False
    finally:
        await session.close()


async def test_data_persistence():
    """Test data persistence across operations."""
    print("🔍 Testing data persistence...")
    
    session = await database_manager.get_session()
    try:
        credit_repo = CreditRepository(session)
        consent_repo = ConsentRepository(session)
        
        # Create test data
        user_id = f"persist_user_{int(time.time())}"
        
        # Create user credits
        user_credits = UserCreditsDB(
            user_id=user_id,
            is_guest=False,
            available_credits=25,
            max_credits=50
        )
        await credit_repo.create_user_credits(user_credits)
        
        # Create user consent
        user_consent = UserConsentDB(
            user_id=user_id,
            terms_accepted=True,
            marketing_consent=True
        )
        await consent_repo.create_consent(user_consent)
        
        await session.commit()
        print(f"✅ Created persistent data for user: {user_id}")
        
        # Close and reopen session to test persistence
        await session.close()
        
        session = await database_manager.get_session()
        credit_repo = CreditRepository(session)
        consent_repo = ConsentRepository(session)
        
        # Verify data persists
        retrieved_credits = await credit_repo.get_user_credits(user_id)
        retrieved_consent = await consent_repo.get_consent(user_id)
        
        assert retrieved_credits is not None
        assert retrieved_credits.available_credits == 25
        assert retrieved_consent is not None
        assert retrieved_consent.marketing_consent is True
        
        print("✅ Data persistence verified")
        
        # Cleanup
        await credit_repo.delete_user_credits(user_id)
        await consent_repo.delete_consent(user_id)
        await session.commit()
        
        return True
        
    except Exception as e:
        await session.rollback()
        print(f"❌ Data persistence test failed: {e}")
        return False
    finally:
        await session.close()


async def main():
    """Run all verification tests."""
    print("🚀 Starting PostgreSQL Performance Verification")
    print("=" * 50)
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Performance Indexes", test_performance_indexes),
        ("Basic CRUD Operations", test_basic_crud_operations),
        ("Batch Operations", test_batch_operations),
        ("Cache Operations", test_cache_operations),
        ("Performance Monitoring", test_performance_monitoring),
        ("Data Persistence", test_data_persistence),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All performance optimizations verified successfully!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
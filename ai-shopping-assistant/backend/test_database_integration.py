"""Integration test for database session management."""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.database.manager import database_manager, create_session_context
from app.database.health import health_checker


async def test_database_integration():
    """Test database manager integration."""
    print("Testing database manager integration...")
    
    try:
        # Test initialization
        print("1. Testing database manager initialization...")
        await database_manager.initialize()
        print("   ✓ Database manager initialized successfully")
        
        # Test health check
        print("2. Testing health check...")
        health_result = await health_checker.check_health()
        print(f"   ✓ Health check result: {health_result['healthy']}")
        
        # Test connection info
        print("3. Testing connection info...")
        conn_info = await database_manager.get_connection_info()
        print(f"   ✓ Connection pool status: {conn_info['status']}")
        
        # Test session context manager
        print("4. Testing session context manager...")
        async with create_session_context() as session:
            print("   ✓ Session context manager created successfully")
            print(f"   ✓ Session type: {type(session)}")
        
        # Test detailed health status
        print("5. Testing detailed health status...")
        detailed_status = await health_checker.get_detailed_status()
        print(f"   ✓ Database healthy: {detailed_status['database']['healthy']}")
        print(f"   ✓ Initialized: {detailed_status['initialized']}")
        
        print("\n✅ All database integration tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Database integration test failed: {e}")
        return False
    
    finally:
        # Clean up
        try:
            await database_manager.close()
            print("   ✓ Database manager closed successfully")
        except Exception as e:
            print(f"   ⚠️  Error during cleanup: {e}")


if __name__ == "__main__":
    success = asyncio.run(test_database_integration())
    sys.exit(0 if success else 1)
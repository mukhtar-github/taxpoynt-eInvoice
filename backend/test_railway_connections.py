#!/usr/bin/env python3
"""
Test script to verify connections to database services (PostgreSQL/SQLite and Redis).
Supports both Railway production connections and local development setup.
"""
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env.development
load_dotenv(os.path.join(os.path.dirname(__file__), ".env.development"))

print("Testing database connections...")
print("=" * 50)

# Determine environment type based on DATABASE_URL
database_url = os.getenv('DATABASE_URL', '')
if database_url.startswith('sqlite'):
    print("🔧 Running in LOCAL DEVELOPMENT mode with SQLite")
else:
    print("🌐 Running in RAILWAY mode with PostgreSQL")
print("=" * 50)

# Test Database connection (PostgreSQL or SQLite)
print("\n[1/2] Testing Database Connection:")
try:
    from app.db.session import get_db_session
    from sqlalchemy import text
    
    db = get_db_session()
    # Simple query to verify connection works
    result = db.execute(text("SELECT 1")).scalar()
    
    if result == 1:
        print("✅ Database connection successful!")
        print(f"   Using: {database_url}")
    else:
        print("⚠️ Database query returned unexpected result")
    
    db.close()
except Exception as e:
    print(f"❌ Database connection failed: {str(e)}")

# Test Redis connection
print("\n[2/2] Testing Redis Connection:")
redis_url = os.getenv('REDIS_URL')

if not redis_url:
    print("ℹ️ Redis not configured in local development mode. This is expected.")
    print("   To enable Redis, uncomment the Redis configuration in .env.development")
else:
    try:
        from app.db.redis import get_redis_client
        
        redis_client = get_redis_client()
        redis_client.set("test_key", "Connection successful!")
        result = redis_client.get("test_key")
        
        if result == "Connection successful!":
            print("✅ Redis connection successful!")
            print(f"   Using: {redis_url}")
            # Clean up test key
            redis_client.delete("test_key")
        else:
            print(f"⚠️ Redis returned unexpected result: {result}")
    except Exception as e:
        print(f"❌ Redis connection failed: {str(e)}")

print("\n" + "=" * 50)
print("Connection tests completed.")
print("\nNext steps:")
print("1. For local development, you're now using SQLite which should work fine.")
print("2. For Railway production access, you'll need to:")
print("   - Install Railway CLI: https://docs.railway.app/develop/cli")
print("   - Link to your project: 'railway link'")
print("   - Use proxied connections: 'railway run python backend/test_railway_connections.py'")
print("=" * 50)

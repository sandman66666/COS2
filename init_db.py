#!/usr/bin/env python3
"""
Database initialization script for Heroku deployment
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from storage.storage_manager_sync import initialize_storage_manager_sync
    
    print("🔄 Initializing database...")
    result = initialize_storage_manager_sync()
    
    if result:
        print("✅ Database initialization completed successfully!")
        print(f"📊 Initialization result: {result}")
    else:
        print("⚠️ Database initialization completed with warnings")
        
except Exception as e:
    print(f"❌ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🎉 Database is ready!") 
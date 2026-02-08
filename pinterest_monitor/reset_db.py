#!/usr/bin/env python3
"""
Reset/Clean database for Pinterest Monitor
This script removes all tracked data to prepare for GitHub publication
"""

import sqlite3
import os

DATABASE_NAME = 'pinterest_monitor.db'

def reset_database():
    """Remove all data from the database"""
    if not os.path.exists(DATABASE_NAME):
        print(f"Database {DATABASE_NAME} does not exist.")
        return
    
    response = input(f"⚠️  This will delete ALL data from {DATABASE_NAME}. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Aborted.")
        return
    
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    
    try:
        # Delete all data
        cursor.execute('DELETE FROM pin_history')
        cursor.execute('DELETE FROM boards')
        cursor.execute('DELETE FROM users')
        
        # Reset autoincrement counters
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="pin_history"')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="boards"')
        cursor.execute('DELETE FROM sqlite_sequence WHERE name="users"')
        
        conn.commit()
        
        print("✅ Database cleaned successfully!")
        print("   - All boards removed")
        print("   - All users removed")
        print("   - All history removed")
        
    except Exception as e:
        print(f"❌ Error cleaning database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Pinterest Monitor - Database Reset")
    print("=" * 60)
    print()
    reset_database()

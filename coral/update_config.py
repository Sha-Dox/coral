#!/usr/bin/env python3
"""
Update Database with Config Settings
====================================

This script updates the CORAL database with trigger URLs
from the central config.yaml file.

Run this after changing ports in config.yaml to update the database.
"""

import sys
import sqlite3
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config_loader import config, get_trigger_urls

def update_database():
    """Update platform trigger URLs in database from config"""
    
    # Get database path
    db_path = Path(__file__).parent / config.get('hub.database', 'coral.db').split('/')[-1]
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("   Run the hub first to create the database")
        return False
    
    # Get trigger URLs from config
    trigger_urls = get_trigger_urls()
    
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         Updating Database from config.yaml                ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()
    
    # Update database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        for platform, url in trigger_urls.items():
            # Check if platform exists
            cursor.execute("SELECT id, name FROM platforms WHERE name = ?", (platform,))
            result = cursor.fetchone()
            
            if result:
                platform_id, name = result
                cursor.execute(
                    "UPDATE platforms SET trigger_url = ? WHERE id = ?",
                    (url, platform_id)
                )
                print(f"✓ Updated {name.capitalize()}: {url}")
            else:
                print(f"⚠ Platform '{platform}' not found in database, skipping")
        
        conn.commit()
        print()
        print("✓ Database updated successfully!")
        print()
        print("Restart services for changes to take effect:")
        print("  ./start_all.sh")
        return True
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == '__main__':
    success = update_database()
    sys.exit(0 if success else 1)

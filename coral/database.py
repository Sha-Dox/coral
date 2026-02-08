#!/usr/bin/env python3
"""
Database layer for CORAL
"""
import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_NAME

@contextmanager
def get_db():
    """Context manager for database connections"""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Initialize database with required tables"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Platforms table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS platforms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                webhook_secret TEXT,
                trigger_url TEXT,
                config_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Persons table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS persons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Linked profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS linked_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                platform_id INTEGER NOT NULL,
                platform_username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE CASCADE,
                FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE,
                UNIQUE(platform_id, platform_username)
            )
        ''')
        
        # Events table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform_id INTEGER NOT NULL,
                person_id INTEGER,
                platform_username TEXT NOT NULL,
                event_type TEXT NOT NULL,
                event_data TEXT,
                summary TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_time TIMESTAMP,
                FOREIGN KEY (platform_id) REFERENCES platforms(id) ON DELETE CASCADE,
                FOREIGN KEY (person_id) REFERENCES persons(id) ON DELETE SET NULL
            )
        ''')
        
        # Indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_linked_profiles_person ON linked_profiles(person_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_linked_profiles_platform ON linked_profiles(platform_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_platform ON events(platform_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_person ON events(person_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_time ON events(event_time DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC)')
        
        # Insert default platforms if not exist
        default_platforms = [
            ('instagram', 'Instagram'),
            ('pinterest', 'Pinterest'),
            ('spotify', 'Spotify')
        ]
        
        for name, display_name in default_platforms:
            cursor.execute('''
                INSERT OR IGNORE INTO platforms (name, display_name)
                VALUES (?, ?)
            ''', (name, display_name))

# Platform operations
def get_platform_by_name(name):
    """Get platform by name"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM platforms WHERE name = ?', (name,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_all_platforms():
    """Get all platforms"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM platforms ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]

def add_platform(name, display_name, webhook_secret=None, config_json=None):
    """Add a new platform"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO platforms (name, display_name, webhook_secret, config_json)
            VALUES (?, ?, ?, ?)
        ''', (name, display_name, webhook_secret, config_json))
        return cursor.lastrowid

def update_platform(platform_id, **kwargs):
    """Update platform fields"""
    with get_db() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        
        for key in ['display_name', 'webhook_secret', 'trigger_url', 'config_json']:
            if key in kwargs:
                fields.append(f'{key} = ?')
                values.append(kwargs[key])
        
        if not fields:
            return False
        
        values.append(platform_id)
        cursor.execute(f'''
            UPDATE platforms SET {', '.join(fields)}
            WHERE id = ?
        ''', values)
        return cursor.rowcount > 0

# Person operations
def get_all_persons():
    """Get all persons with their linked profiles"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM persons ORDER BY name')
        persons = [dict(row) for row in cursor.fetchall()]
        
        for person in persons:
            cursor.execute('''
                SELECT lp.*, p.name as platform_name, p.display_name as platform_display_name
                FROM linked_profiles lp
                JOIN platforms p ON lp.platform_id = p.id
                WHERE lp.person_id = ?
                ORDER BY p.name
            ''', (person['id'],))
            person['profiles'] = [dict(row) for row in cursor.fetchall()]
        
        return persons

def get_person(person_id):
    """Get a specific person with their profiles"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM persons WHERE id = ?', (person_id,))
        row = cursor.fetchone()
        if not row:
            return None
        
        person = dict(row)
        cursor.execute('''
            SELECT lp.*, p.name as platform_name, p.display_name as platform_display_name
            FROM linked_profiles lp
            JOIN platforms p ON lp.platform_id = p.id
            WHERE lp.person_id = ?
            ORDER BY p.name
        ''', (person_id,))
        person['profiles'] = [dict(row) for row in cursor.fetchall()]
        
        return person

def add_person(name, notes=None):
    """Add a new person"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO persons (name, notes)
            VALUES (?, ?)
        ''', (name, notes))
        return cursor.lastrowid

def update_person(person_id, name=None, notes=None):
    """Update person details"""
    with get_db() as conn:
        cursor = conn.cursor()
        fields = []
        values = []
        
        if name is not None:
            fields.append('name = ?')
            values.append(name)
        if notes is not None:
            fields.append('notes = ?')
            values.append(notes)
        
        fields.append('updated_at = ?')
        values.append(datetime.now())
        
        if not fields:
            return False
        
        values.append(person_id)
        cursor.execute(f'''
            UPDATE persons SET {', '.join(fields)}
            WHERE id = ?
        ''', values)
        return cursor.rowcount > 0

def delete_person(person_id):
    """Delete a person and their linked profiles"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM persons WHERE id = ?', (person_id,))
        return cursor.rowcount > 0

# Linked profile operations
def link_profile(person_id, platform_id, platform_username):
    """Link a platform username to a person"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO linked_profiles (person_id, platform_id, platform_username)
                VALUES (?, ?, ?)
            ''', (person_id, platform_id, platform_username))
            
            # Update person's updated_at
            cursor.execute('''
                UPDATE persons SET updated_at = ? WHERE id = ?
            ''', (datetime.now(), person_id))
            
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

def unlink_profile(profile_id):
    """Unlink a profile"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get person_id before deleting
        cursor.execute('SELECT person_id FROM linked_profiles WHERE id = ?', (profile_id,))
        row = cursor.fetchone()
        if not row:
            return False
        
        person_id = row[0]
        
        cursor.execute('DELETE FROM linked_profiles WHERE id = ?', (profile_id,))
        success = cursor.rowcount > 0
        
        if success:
            cursor.execute('''
                UPDATE persons SET updated_at = ? WHERE id = ?
            ''', (datetime.now(), person_id))
        
        return success

def find_person_by_username(platform_id, platform_username):
    """Find person_id by platform username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT person_id FROM linked_profiles
            WHERE platform_id = ? AND platform_username = ?
        ''', (platform_id, platform_username))
        row = cursor.fetchone()
        return row[0] if row else None

# Event operations
def add_event(platform_id, platform_username, event_type, summary, event_time=None, event_data=None):
    """Add a new event"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Try to resolve person_id
        person_id = find_person_by_username(platform_id, platform_username)
        
        # Convert event_data to JSON if it's a dict
        if isinstance(event_data, dict):
            event_data = json.dumps(event_data)
        
        cursor.execute('''
            INSERT INTO events (platform_id, person_id, platform_username, 
                              event_type, summary, event_time, event_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (platform_id, person_id, platform_username, event_type, 
              summary, event_time, event_data))
        
        return cursor.lastrowid

def get_events(platform_id=None, person_id=None, limit=100, offset=0):
    """Get events with filters"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = '''
            SELECT e.*, p.name as platform_name, p.display_name as platform_display_name,
                   per.name as person_name
            FROM events e
            JOIN platforms p ON e.platform_id = p.id
            LEFT JOIN persons per ON e.person_id = per.id
        '''
        
        conditions = []
        params = []
        
        if platform_id is not None:
            conditions.append('e.platform_id = ?')
            params.append(platform_id)
        
        if person_id is not None:
            conditions.append('e.person_id = ?')
            params.append(person_id)
        
        if conditions:
            query += ' WHERE ' + ' AND '.join(conditions)
        
        query += ' ORDER BY COALESCE(e.event_time, e.created_at) DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

def get_unlinked_events(limit=50):
    """Get events that are not linked to any person"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, p.name as platform_name, p.display_name as platform_display_name
            FROM events e
            JOIN platforms p ON e.platform_id = p.id
            WHERE e.person_id IS NULL
            ORDER BY COALESCE(e.event_time, e.created_at) DESC
            LIMIT ?
        ''', (limit,))
        return [dict(row) for row in cursor.fetchall()]

def get_person_latest_event(person_id):
    """Get the most recent event for a person"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.*, p.name as platform_name, p.display_name as platform_display_name
            FROM events e
            JOIN platforms p ON e.platform_id = p.id
            WHERE e.person_id = ?
            ORDER BY COALESCE(e.event_time, e.created_at) DESC
            LIMIT 1
        ''', (person_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

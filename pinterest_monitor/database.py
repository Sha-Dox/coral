import sqlite3
from datetime import datetime
from contextlib import contextmanager

DATABASE_NAME = 'pinterest_monitor.db'

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
        
        # Users/Profiles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT,
                last_checked TIMESTAMP,
                last_activity_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Boards table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                username TEXT NOT NULL,
                current_pin_count INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                last_pin_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Pin history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pin_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL,
                pin_count INTEGER NOT NULL,
                checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE
            )
        ''')
        
        # Indexes for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_board_id ON pin_history(board_id)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_checked_at ON pin_history(checked_at)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_board_username ON boards(username)
        ''')

def add_board(url, name, username, pin_count=0):
    """Add a new board to monitoring"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO boards (url, name, username, current_pin_count, last_checked)
                VALUES (?, ?, ?, ?, ?)
            ''', (url, name, username, pin_count, datetime.now()))
            board_id = cursor.lastrowid
            
            # Record initial pin count
            cursor.execute('''
                INSERT INTO pin_history (board_id, pin_count, checked_at)
                VALUES (?, ?, ?)
            ''', (board_id, pin_count, datetime.now()))
            
            return board_id
        except sqlite3.IntegrityError:
            return None  # Board already exists

def update_pin_count(board_id, new_count):
    """Update pin count for a board and record in history"""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now()
        
        # Get current pin count
        cursor.execute('SELECT current_pin_count FROM boards WHERE id = ?', (board_id,))
        result = cursor.fetchone()
        if not result:
            return False
        
        old_count = result[0]
        
        # Update board
        update_fields = ['current_pin_count = ?', 'last_checked = ?']
        params = [new_count, now]
        
        # If pin count increased, update last_pin_time
        if new_count > old_count:
            update_fields.append('last_pin_time = ?')
            params.append(now)
        
        params.append(board_id)
        cursor.execute(f'''
            UPDATE boards 
            SET {', '.join(update_fields)}
            WHERE id = ?
        ''', params)
        
        # Record in history
        cursor.execute('''
            INSERT INTO pin_history (board_id, pin_count, checked_at)
            VALUES (?, ?, ?)
        ''', (board_id, new_count, now))
        
        return True

def get_all_boards():
    """Get all monitored boards"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, name, username, current_pin_count, 
                   last_checked, last_pin_time, created_at
            FROM boards
            ORDER BY username, name
        ''')
        return [dict(row) for row in cursor.fetchall()]

def get_board(board_id):
    """Get a specific board by ID"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, url, name, username, current_pin_count, 
                   last_checked, last_pin_time, created_at
            FROM boards
            WHERE id = ?
        ''', (board_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

def get_board_history(board_id, limit=100):
    """Get pin count history for a board"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT pin_count, checked_at
            FROM pin_history
            WHERE board_id = ?
            ORDER BY checked_at DESC
            LIMIT ?
        ''', (board_id, limit))
        return [dict(row) for row in cursor.fetchall()]

def delete_board(board_id):
    """Delete a board and its history"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM boards WHERE id = ?', (board_id,))
        return cursor.rowcount > 0

def board_exists(url):
    """Check if a board URL is already being monitored"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM boards WHERE url = ?', (url,))
        return cursor.fetchone() is not None

# User/Profile operations

def add_user(username, display_name=None):
    """Add a new user profile to monitoring"""
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO users (username, display_name, last_checked)
                VALUES (?, ?, ?)
            ''', (username, display_name or username, datetime.now()))
            user_id = cursor.lastrowid
            return user_id
        except sqlite3.IntegrityError:
            # User already exists, update display name
            cursor.execute('''
                UPDATE users SET display_name = ?, last_checked = ?
                WHERE username = ?
            ''', (display_name or username, datetime.now(), username))
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            result = cursor.fetchone()
            return result[0] if result else None

def update_user_activity(username):
    """Update user's last activity time"""
    with get_db() as conn:
        cursor = conn.cursor()
        now = datetime.now()
        cursor.execute('''
            UPDATE users 
            SET last_activity_time = ?, last_checked = ?
            WHERE username = ?
        ''', (now, now, username))
        return cursor.rowcount > 0

def get_all_users():
    """Get all monitored users"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, display_name, last_checked, last_activity_time, created_at
            FROM users
            ORDER BY username
        ''')
        return [dict(row) for row in cursor.fetchall()]

def get_user_by_username(username):
    """Get a user by username"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, display_name, last_checked, last_activity_time, created_at
            FROM users
            WHERE username = ?
        ''', (username,))
        row = cursor.fetchone()
        return dict(row) if row else None

def delete_user(user_id):
    """Delete a user profile and all their boards"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get username before deleting
        cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            return False
        
        username = result[0]
        
        # Delete all boards for this user
        cursor.execute('DELETE FROM boards WHERE username = ?', (username,))
        
        # Delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        return cursor.rowcount > 0

def get_user_board_count(username):
    """Get count of boards for a user"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM boards WHERE username = ?', (username,))
        result = cursor.fetchone()
        return result[0] if result else 0

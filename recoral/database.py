import sqlite3
import json
from datetime import datetime
from contextlib import contextmanager
from config import DATABASE_NAME


@contextmanager
def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate(conn):
    """Add columns to existing tables if missing."""
    c = conn.cursor()
    c.execute("PRAGMA table_info(accounts)")
    cols = {r[1] for r in c.fetchall()}
    for col, typedef in [
        ("last_error", "TEXT"),
        ("error_count", "INTEGER DEFAULT 0"),
    ]:
        if col not in cols:
            c.execute(f"ALTER TABLE accounts ADD COLUMN {col} {typedef}")

    c.execute("PRAGMA table_info(pinterest_boards)")
    cols = {r[1] for r in c.fetchall()}
    if "description" not in cols:
        c.execute("ALTER TABLE pinterest_boards ADD COLUMN description TEXT")


def init_db():
    with get_db() as conn:
        c = conn.cursor()

        c.execute("""
            CREATE TABLE IF NOT EXISTS identities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identity_id INTEGER NOT NULL,
                platform TEXT NOT NULL,
                username TEXT NOT NULL,
                display_name TEXT,
                enabled BOOLEAN DEFAULT 1,
                config_json TEXT,
                last_checked TIMESTAMP,
                last_data TEXT,
                last_error TEXT,
                error_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (identity_id) REFERENCES identities(id) ON DELETE CASCADE,
                UNIQUE(platform, username)
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                summary TEXT,
                event_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS pinterest_boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                url TEXT NOT NULL UNIQUE,
                name TEXT,
                description TEXT,
                current_pin_count INTEGER DEFAULT 0,
                last_checked TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
            )
        """)

        c.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        c.execute("CREATE INDEX IF NOT EXISTS idx_accounts_identity ON accounts(identity_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_accounts_platform ON accounts(platform)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_account ON events(account_id)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_boards_account ON pinterest_boards(account_id)")

        _migrate(conn)


# ---------------------------------------------------------------------------
# Identities
# ---------------------------------------------------------------------------

def get_all_identities():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM identities ORDER BY name")
        identities = [dict(r) for r in c.fetchall()]
        for ident in identities:
            c.execute("SELECT * FROM accounts WHERE identity_id = ? ORDER BY platform, username", (ident["id"],))
            ident["accounts"] = [dict(r) for r in c.fetchall()]
        return identities


def get_identity(identity_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM identities WHERE id = ?", (identity_id,))
        row = c.fetchone()
        if not row:
            return None
        ident = dict(row)
        c.execute("SELECT * FROM accounts WHERE identity_id = ? ORDER BY platform, username", (identity_id,))
        ident["accounts"] = [dict(r) for r in c.fetchall()]
        return ident


def add_identity(name, notes=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT INTO identities (name, notes) VALUES (?, ?)", (name, notes))
        return c.lastrowid


def update_identity(identity_id, **kwargs):
    with get_db() as conn:
        c = conn.cursor()
        fields, values = [], []
        for key in ("name", "notes"):
            if key in kwargs and kwargs[key] is not None:
                fields.append(f"{key} = ?")
                values.append(kwargs[key])
        if not fields:
            return False
        fields.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(identity_id)
        c.execute(f"UPDATE identities SET {', '.join(fields)} WHERE id = ?", values)
        return c.rowcount > 0


def delete_identity(identity_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM identities WHERE id = ?", (identity_id,))
        return c.rowcount > 0


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

def add_account(identity_id, platform, username, display_name=None, config_json=None):
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO accounts (identity_id, platform, username, display_name, config_json) VALUES (?, ?, ?, ?, ?)",
                (identity_id, platform, username, display_name, config_json),
            )
            c.execute("UPDATE identities SET updated_at = ? WHERE id = ?", (datetime.utcnow(), identity_id))
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None


def get_account(account_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
        row = c.fetchone()
        return dict(row) if row else None


def get_enabled_accounts():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM accounts WHERE enabled = 1 ORDER BY platform, username")
        return [dict(r) for r in c.fetchall()]


def update_account(account_id, **kwargs):
    with get_db() as conn:
        c = conn.cursor()
        fields, values = [], []
        for key in ("username", "display_name", "enabled", "config_json",
                     "last_checked", "last_data", "last_error", "error_count"):
            if key in kwargs:
                fields.append(f"{key} = ?")
                values.append(kwargs[key])
        if not fields:
            return False
        values.append(account_id)
        c.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id = ?", values)
        return c.rowcount > 0


def record_check_success(account_id, last_data=None):
    kwargs = {"last_checked": datetime.utcnow(), "last_error": None, "error_count": 0}
    if last_data is not None:
        kwargs["last_data"] = last_data if isinstance(last_data, str) else json.dumps(last_data)
    return update_account(account_id, **kwargs)


def record_check_error(account_id, error_msg):
    acc = get_account(account_id)
    count = (acc.get("error_count") or 0) + 1 if acc else 1
    return update_account(account_id, last_error=str(error_msg), error_count=count)


def delete_account(account_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
        return c.rowcount > 0


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

def add_event(account_id, event_type, summary, event_data=None):
    with get_db() as conn:
        c = conn.cursor()
        if isinstance(event_data, dict):
            event_data = json.dumps(event_data)
        c.execute(
            "INSERT INTO events (account_id, event_type, summary, event_data) VALUES (?, ?, ?, ?)",
            (account_id, event_type, summary, event_data),
        )
        return c.lastrowid


def get_event(event_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT e.*, a.platform, a.username, a.identity_id, i.name as identity_name
            FROM events e
            JOIN accounts a ON e.account_id = a.id
            JOIN identities i ON a.identity_id = i.id
            WHERE e.id = ?
        """, (event_id,))
        row = c.fetchone()
        return dict(row) if row else None


def get_events(account_id=None, identity_id=None, platform=None, limit=100, offset=0):
    with get_db() as conn:
        c = conn.cursor()
        query = """
            SELECT e.*, a.platform, a.username, a.identity_id, i.name as identity_name
            FROM events e
            JOIN accounts a ON e.account_id = a.id
            JOIN identities i ON a.identity_id = i.id
        """
        conditions, params = [], []
        if account_id is not None:
            conditions.append("e.account_id = ?")
            params.append(account_id)
        if identity_id is not None:
            conditions.append("a.identity_id = ?")
            params.append(identity_id)
        if platform is not None:
            conditions.append("a.platform = ?")
            params.append(platform)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY e.created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]


def get_event_count(account_id=None, identity_id=None, platform=None):
    with get_db() as conn:
        c = conn.cursor()
        query = "SELECT COUNT(*) FROM events e JOIN accounts a ON e.account_id = a.id"
        conditions, params = [], []
        if account_id is not None:
            conditions.append("e.account_id = ?")
            params.append(account_id)
        if identity_id is not None:
            conditions.append("a.identity_id = ?")
            params.append(identity_id)
        if platform is not None:
            conditions.append("a.platform = ?")
            params.append(platform)
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        c.execute(query, params)
        return c.fetchone()[0]


def get_identity_latest_event(identity_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT e.*, a.platform, a.username
            FROM events e
            JOIN accounts a ON e.account_id = a.id
            WHERE a.identity_id = ?
            ORDER BY e.created_at DESC LIMIT 1
        """, (identity_id,))
        row = c.fetchone()
        return dict(row) if row else None


# ---------------------------------------------------------------------------
# Pinterest boards
# ---------------------------------------------------------------------------

def get_pinterest_boards(account_id):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM pinterest_boards WHERE account_id = ? ORDER BY name", (account_id,))
        return [dict(r) for r in c.fetchall()]


def add_pinterest_board(account_id, url, name, pin_count=0, description=None):
    with get_db() as conn:
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO pinterest_boards (account_id, url, name, description, current_pin_count, last_checked) VALUES (?, ?, ?, ?, ?, ?)",
                (account_id, url, name, description, pin_count, datetime.utcnow()),
            )
            return c.lastrowid
        except sqlite3.IntegrityError:
            return None


def update_pinterest_board(board_id, pin_count, name=None, description=None):
    with get_db() as conn:
        c = conn.cursor()
        fields = ["current_pin_count = ?", "last_checked = ?"]
        values = [pin_count, datetime.utcnow()]
        if name:
            fields.append("name = ?")
            values.append(name)
        if description is not None:
            fields.append("description = ?")
            values.append(description)
        values.append(board_id)
        c.execute(f"UPDATE pinterest_boards SET {', '.join(fields)} WHERE id = ?", values)
        return c.rowcount > 0


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def get_setting(key, default=None):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = c.fetchone()
        return row["value"] if row else default


def get_all_settings():
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT key, value FROM settings ORDER BY key")
        return {r["key"]: r["value"] for r in c.fetchall()}


def set_setting(key, value):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))


def delete_setting(key):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM settings WHERE key = ?", (key,))
        return c.rowcount > 0

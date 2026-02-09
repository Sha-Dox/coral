import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

PORT = int(os.getenv("CORAL_PORT", 3456))
HOST = os.getenv("CORAL_HOST", "0.0.0.0")
DEBUG = os.getenv("CORAL_DEBUG", "false").lower() == "true"
CHECK_INTERVAL = int(os.getenv("CORAL_CHECK_INTERVAL", 300))
SP_DC_COOKIE = os.getenv("SP_DC_COOKIE", "")
INSTAGRAM_SESSION_FILE = os.getenv("INSTAGRAM_SESSION_FILE", "")

_db_name = os.getenv("CORAL_DB", "coral.db")
_db_path = Path(_db_name)
if not _db_path.is_absolute():
    _db_path = (Path(__file__).resolve().parent / _db_path).resolve()
DATABASE_NAME = str(_db_path)

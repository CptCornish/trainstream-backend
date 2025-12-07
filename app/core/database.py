from pathlib import Path
import sqlite3

# backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "trainstream.db"


def get_connection() -> sqlite3.Connection:
    """
    Open a SQLite connection to trainstream.db with row access by column name.
    Use with 'with get_connection() as conn:' so it closes cleanly.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


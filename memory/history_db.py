"""
Persistent chat history store using SQLite.
Tracks every query with its domain, timestamp, and a short title.
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "history.sqlite3")

DOMAIN_ICONS = {
    "research": "🔬",
    "stock":    "📈",
    "code":     "💻",
    "job":      "💼",
    "flight":   "✈️",
    "image":    "🎨",
    "general":  "💬",
}


def init_history_db():
    """Create the history table if it doesn't exist."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                domain    TEXT    NOT NULL,
                title     TEXT    NOT NULL,
                query     TEXT    NOT NULL,
                timestamp TEXT    NOT NULL
            )
        """)
        conn.commit()


def add_history(domain: str, query: str):
    """Insert a new history entry."""
    title = query[:40] + ("..." if len(query) > 40 else "")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO history (domain, title, query, timestamp) VALUES (?, ?, ?, ?)",
            (domain, title, query, timestamp)
        )
        conn.commit()


def get_history() -> list[dict]:
    """Return all history entries newest-first."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM history ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def clear_history():
    """Delete all history entries."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM history")
        conn.commit()


def get_domain_counts() -> dict:
    """Return {domain: count} for all entries."""
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            "SELECT domain, COUNT(*) as cnt FROM history GROUP BY domain ORDER BY cnt DESC"
        ).fetchall()
    return {row[0]: row[1] for row in rows}

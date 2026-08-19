import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "pins.sqlite3")


def init_db(path: str = None):
    db = path or DB_PATH
    os.makedirs(os.path.dirname(db), exist_ok=True)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS pins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            user_prompt TEXT,
            ai_response TEXT,
            timestamp TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def add_pin(user_prompt: str, ai_response: str, title: str = None, path: str = None):
    db = path or DB_PATH
    init_db(db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()

    # Prevent duplicates by exact ai_response match
    cur.execute("SELECT id FROM pins WHERE ai_response = ?", (ai_response,))
    row = cur.fetchone()
    if row:
        conn.close()
        return row[0]

    ts = datetime.utcnow().isoformat()
    t = title or (user_prompt[:40] + "...")
    cur.execute(
        "INSERT INTO pins (title, user_prompt, ai_response, timestamp) VALUES (?, ?, ?, ?)",
        (t, user_prompt, ai_response, ts),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def get_all_pins(path: str = None, newest_first: bool = True):
    db = path or DB_PATH
    init_db(db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    order = "DESC" if newest_first else "ASC"
    cur.execute(f"SELECT id, title, user_prompt, ai_response, timestamp FROM pins ORDER BY id {order}")
    rows = cur.fetchall()
    conn.close()
    pins = []
    for r in rows:
        pins.append({
            "id": r[0],
            "title": r[1],
            "user_prompt": r[2],
            "content": r[3],
            "timestamp": r[4],
        })
    return pins


def delete_pin(pin_id: int, path: str = None):
    db = path or DB_PATH
    init_db(db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("DELETE FROM pins WHERE id = ?", (pin_id,))
    conn.commit()
    conn.close()


def get_pin(pin_id: int, path: str = None):
    db = path or DB_PATH
    init_db(db)
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    cur.execute("SELECT id, title, user_prompt, ai_response, timestamp FROM pins WHERE id = ?", (pin_id,))
    r = cur.fetchone()
    conn.close()
    if not r:
        return None
    return {
        "id": r[0],
        "title": r[1],
        "user_prompt": r[2],
        "content": r[3],
        "timestamp": r[4],
    }

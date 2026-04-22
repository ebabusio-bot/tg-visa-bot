# -*- coding: utf-8 -*-
"""SQLite storage: users, daily message counters, leads, quiz state."""
import sqlite3
from datetime import date
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c

def init_db():
    with _conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            tg_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            lang TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS daily_count (
            tg_id INTEGER,
            day TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (tg_id, day)
        );
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            username TEXT,
            payload TEXT,
            source TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        """)
        # Migrate: add lang column to existing users table if missing.
        cols = {r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()}
        if "lang" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT")

def upsert_user(tg_id: int, username: str | None, first_name: str | None):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO users(tg_id, username, first_name) VALUES(?,?,?)",
            (tg_id, username, first_name),
        )

def get_user_lang(tg_id: int) -> str | None:
    with _conn() as c:
        row = c.execute(
            "SELECT lang FROM users WHERE tg_id=?", (tg_id,),
        ).fetchone()
        return row["lang"] if row and row["lang"] else None

def set_user_lang(tg_id: int, lang: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO users(tg_id, lang) VALUES(?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET lang=excluded.lang",
            (tg_id, lang),
        )

def get_today_count(tg_id: int) -> int:
    today = date.today().isoformat()
    with _conn() as c:
        row = c.execute(
            "SELECT count FROM daily_count WHERE tg_id=? AND day=?",
            (tg_id, today),
        ).fetchone()
        return row["count"] if row else 0

def inc_today_count(tg_id: int) -> int:
    today = date.today().isoformat()
    with _conn() as c:
        c.execute(
            "INSERT INTO daily_count(tg_id, day, count) VALUES(?,?,1) "
            "ON CONFLICT(tg_id, day) DO UPDATE SET count=count+1",
            (tg_id, today),
        )
        row = c.execute(
            "SELECT count FROM daily_count WHERE tg_id=? AND day=?",
            (tg_id, today),
        ).fetchone()
        return row["count"]

def try_consume_daily(tg_id: int, limit: int) -> tuple[bool, int]:
    """Atomically check-and-increment the daily counter.

    Returns (allowed, count_after_op). If the user is already at or above
    the limit, returns (False, current_count) and does NOT increment.
    Otherwise increments and returns (True, new_count).
    """
    today = date.today().isoformat()
    c = _conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute(
            "SELECT count FROM daily_count WHERE tg_id=? AND day=?",
            (tg_id, today),
        ).fetchone()
        current = row["count"] if row else 0
        if current >= limit:
            c.execute("ROLLBACK")
            return False, current
        c.execute(
            "INSERT INTO daily_count(tg_id, day, count) VALUES(?,?,1) "
            "ON CONFLICT(tg_id, day) DO UPDATE SET count=count+1",
            (tg_id, today),
        )
        c.execute("COMMIT")
        return True, current + 1
    finally:
        c.close()

def save_lead(tg_id: int, username: str | None, payload: str, source: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO leads(tg_id, username, payload, source) VALUES(?,?,?,?)",
            (tg_id, username, payload, source),
        )

def save_msg(tg_id: int, role: str, content: str):
    with _conn() as c:
        c.execute(
            "INSERT INTO history(tg_id, role, content) VALUES(?,?,?)",
            (tg_id, role, content),
        )

def recent_history(tg_id: int, limit: int = 8) -> list[dict]:
    """Return last N messages (oldest first) for conversational context."""
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content FROM history WHERE tg_id=? "
            "ORDER BY id DESC LIMIT ?",
            (tg_id, limit),
        ).fetchall()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def list_users_with_stats(limit: int = 50) -> list[dict]:
    """Return users sorted by most recent activity, with message count."""
    with _conn() as c:
        rows = c.execute(
            "SELECT u.tg_id, u.username, u.first_name, "
            "COUNT(h.id) AS msg_count, "
            "MAX(h.created_at) AS last_msg "
            "FROM users u LEFT JOIN history h ON h.tg_id = u.tg_id "
            "GROUP BY u.tg_id "
            "ORDER BY last_msg DESC NULLS LAST "
            "LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]

def full_history(tg_id: int, limit: int = 100) -> list[dict]:
    """Return up to N most recent messages for a user, oldest first."""
    with _conn() as c:
        rows = c.execute(
            "SELECT role, content, created_at FROM history WHERE tg_id=? "
            "ORDER BY id DESC LIMIT ?",
            (tg_id, limit),
        ).fetchall()
    return [dict(r) for r in reversed(rows)]

def list_leads(limit: int = 30) -> list[dict]:
    """Return recent leads, newest first."""
    with _conn() as c:
        rows = c.execute(
            "SELECT tg_id, username, payload, source, created_at "
            "FROM leads ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]

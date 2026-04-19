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

def upsert_user(tg_id: int, username: str | None, first_name: str | None):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO users(tg_id, username, first_name) VALUES(?,?,?)",
            (tg_id, username, first_name),
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

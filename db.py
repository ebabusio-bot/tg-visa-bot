# -*- coding: utf-8 -*-
"""SQLite storage: users, daily message counters, leads, quiz state."""
import sqlite3
from datetime import date, datetime, timedelta
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
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            event_type TEXT,
            payload TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_events_type_time ON events(event_type, created_at);
        CREATE TABLE IF NOT EXISTS quiz_state (
            tg_id INTEGER,
            kind TEXT,
            started_at TEXT,
            completed_at TEXT,
            reminder1_at TEXT,
            reminder2_at TEXT,
            PRIMARY KEY (tg_id, kind)
        );
        CREATE TABLE IF NOT EXISTS reengagement (
            tg_id INTEGER PRIMARY KEY,
            reminded_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS lead_followup (
            tg_id INTEGER PRIMARY KEY,
            sent_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS usage (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            kind TEXT,                 -- 'ask' | 'translate'
            model TEXT,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            cache_write_tokens INTEGER DEFAULT 0,
            cache_read_tokens INTEGER DEFAULT 0,
            cost_usd REAL DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_usage_time ON usage(created_at);
        """)
        # Migrate: add lang / source columns to existing users table if missing.
        cols = {r["name"] for r in c.execute("PRAGMA table_info(users)").fetchall()}
        if "lang" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN lang TEXT")
        if "source" not in cols:
            c.execute("ALTER TABLE users ADD COLUMN source TEXT")

def upsert_user(tg_id: int, username: str | None, first_name: str | None):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO users(tg_id, username, first_name) VALUES(?,?,?)",
            (tg_id, username, first_name),
        )

def set_user_source(tg_id: int, source: str) -> str | None:
    """Record the traffic source for a user from a deep-link /start parameter.
    First-touch attribution: only set if not already recorded. Returns the
    effective source (the newly set one, or the existing one)."""
    source = "".join(ch for ch in source if ch.isalnum() or ch in "_-")[:32]
    if not source:
        return None
    with _conn() as c:
        c.execute(
            "INSERT INTO users(tg_id, source) VALUES(?,?) "
            "ON CONFLICT(tg_id) DO UPDATE SET source=excluded.source "
            "WHERE users.source IS NULL",
            (tg_id, source),
        )
        row = c.execute(
            "SELECT source FROM users WHERE tg_id=?", (tg_id,),
        ).fetchone()
        return row["source"] if row else source

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

# ── Lifetime (total) question counter ─────────────────────────────────────
# Reuses the daily_count table with a fixed sentinel day='all', so there is
# no schema migration and the count never resets.
_TOTAL_DAY = "all"

def get_total_count(tg_id: int) -> int:
    with _conn() as c:
        row = c.execute(
            "SELECT count FROM daily_count WHERE tg_id=? AND day=?",
            (tg_id, _TOTAL_DAY),
        ).fetchone()
        return row["count"] if row else 0

def try_consume_total(tg_id: int, limit: int) -> tuple[bool, int]:
    """Atomically check-and-increment the lifetime question counter.

    Returns (allowed, count_after_op). If the user is already at or above
    the limit, returns (False, current_count) and does NOT increment.
    Otherwise increments and returns (True, new_count).
    """
    c = _conn()
    try:
        c.execute("BEGIN IMMEDIATE")
        row = c.execute(
            "SELECT count FROM daily_count WHERE tg_id=? AND day=?",
            (tg_id, _TOTAL_DAY),
        ).fetchone()
        current = row["count"] if row else 0
        if current >= limit:
            c.execute("ROLLBACK")
            return False, current
        c.execute(
            "INSERT INTO daily_count(tg_id, day, count) VALUES(?,?,1) "
            "ON CONFLICT(tg_id, day) DO UPDATE SET count=count+1",
            (tg_id, _TOTAL_DAY),
        )
        c.execute("COMMIT")
        return True, current + 1
    finally:
        c.close()

# ── AI cost tracking ──────────────────────────────────────────────────────
def log_usage(tg_id: int, kind: str, model: str, input_tokens: int,
              output_tokens: int, cache_write_tokens: int,
              cache_read_tokens: int, cost_usd: float):
    """Record one LLM call's token usage and computed cost (USD)."""
    with _conn() as c:
        c.execute(
            "INSERT INTO usage(tg_id, kind, model, input_tokens, output_tokens, "
            "cache_write_tokens, cache_read_tokens, cost_usd) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (tg_id, kind, model, input_tokens, output_tokens,
             cache_write_tokens, cache_read_tokens, cost_usd),
        )

def usage_totals(days: int | None = None) -> dict:
    """Aggregate AI usage over the last `days` days (None = all time).
    Returns totals: calls, tokens, cost, plus a per-month breakdown."""
    where = ""
    args: tuple = ()
    if days is not None:
        where = "WHERE created_at >= datetime('now', ?)"
        args = (f"-{int(days)} days",)
    with _conn() as c:
        row = c.execute(
            f"""SELECT COUNT(*) AS calls,
                       COALESCE(SUM(input_tokens),0)        AS input_tokens,
                       COALESCE(SUM(output_tokens),0)       AS output_tokens,
                       COALESCE(SUM(cache_write_tokens),0)  AS cache_write_tokens,
                       COALESCE(SUM(cache_read_tokens),0)   AS cache_read_tokens,
                       COALESCE(SUM(cost_usd),0)            AS cost_usd
                FROM usage {where}""",
            args,
        ).fetchone()
        months = c.execute(
            """SELECT substr(created_at,1,7) AS month,
                      COUNT(*) AS calls,
                      COALESCE(SUM(cost_usd),0) AS cost_usd
               FROM usage
               GROUP BY month ORDER BY month DESC LIMIT 12"""
        ).fetchall()
    return {
        "calls": row["calls"],
        "input_tokens": row["input_tokens"],
        "output_tokens": row["output_tokens"],
        "cache_write_tokens": row["cache_write_tokens"],
        "cache_read_tokens": row["cache_read_tokens"],
        "cost_usd": row["cost_usd"],
        "months": [dict(m) for m in months],
    }

def cost_this_month() -> float:
    """Total AI cost (USD) for the current calendar month."""
    with _conn() as c:
        row = c.execute(
            "SELECT COALESCE(SUM(cost_usd),0) AS c FROM usage "
            "WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m','now')"
        ).fetchone()
        return row["c"] or 0.0

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

# ─── analytics: events + quiz tracking ──────────────────────────────────

def log_event(tg_id: int, event_type: str, payload: str | None = None):
    """Record a funnel event. event_type: start|click|quiz_start|quiz_finish|lead|qa_ask."""
    with _conn() as c:
        c.execute(
            "INSERT INTO events(tg_id, event_type, payload) VALUES(?,?,?)",
            (tg_id, event_type, payload),
        )

def start_quiz(tg_id: int, kind: str):
    """Mark that a user started a given quiz. Resets reminder state."""
    with _conn() as c:
        c.execute(
            "INSERT INTO quiz_state(tg_id, kind, started_at, completed_at, "
            "reminder1_at, reminder2_at) "
            "VALUES(?,?,datetime('now'),NULL,NULL,NULL) "
            "ON CONFLICT(tg_id, kind) DO UPDATE SET "
            "started_at=datetime('now'), completed_at=NULL, "
            "reminder1_at=NULL, reminder2_at=NULL",
            (tg_id, kind),
        )

def finish_quiz(tg_id: int, kind: str):
    """Mark a quiz as completed."""
    with _conn() as c:
        c.execute(
            "UPDATE quiz_state SET completed_at=datetime('now') "
            "WHERE tg_id=? AND kind=? AND completed_at IS NULL",
            (tg_id, kind),
        )

def find_pending_reminders(stage: int) -> list[dict]:
    """Find quizzes that need a reminder.
    stage=1: started ≥ 2h ago, no reminder1 sent, not finished.
    stage=2: reminder1 was sent ≥ 22h ago (= 24h after start), no reminder2 sent."""
    if stage == 1:
        sql = (
            "SELECT tg_id, kind FROM quiz_state "
            "WHERE completed_at IS NULL "
            "AND reminder1_at IS NULL "
            "AND datetime(started_at) <= datetime('now', '-2 hours')"
        )
    elif stage == 2:
        sql = (
            "SELECT tg_id, kind FROM quiz_state "
            "WHERE completed_at IS NULL "
            "AND reminder1_at IS NOT NULL "
            "AND reminder2_at IS NULL "
            "AND datetime(reminder1_at) <= datetime('now', '-22 hours')"
        )
    else:
        return []
    with _conn() as c:
        rows = c.execute(sql).fetchall()
    return [dict(r) for r in rows]

def mark_reminded(tg_id: int, kind: str, stage: int):
    """Mark that we sent reminder stage N for this user+quiz."""
    col = f"reminder{stage}_at"
    with _conn() as c:
        c.execute(
            f"UPDATE quiz_state SET {col}=datetime('now') WHERE tg_id=? AND kind=?",
            (tg_id, kind),
        )

def stats_summary(days: int) -> dict:
    """Aggregate funnel metrics for the last N days. days=0 means 'today only'."""
    if days <= 0:
        cutoff = "datetime('now', 'start of day')"
    else:
        cutoff = f"datetime('now', '-{days} days')"
    with _conn() as c:
        def count(sql, *args):
            return c.execute(sql, args).fetchone()[0]
        starts = count(
            f"SELECT COUNT(*) FROM events WHERE event_type='start' AND created_at >= {cutoff}"
        )
        new_users = count(
            f"SELECT COUNT(*) FROM users WHERE created_at >= {cutoff}"
        )
        quiz_starts = count(
            f"SELECT COUNT(*) FROM events WHERE event_type='quiz_start' AND created_at >= {cutoff}"
        )
        quiz_finishes = count(
            f"SELECT COUNT(*) FROM events WHERE event_type='quiz_finish' AND created_at >= {cutoff}"
        )
        leads = count(
            f"SELECT COUNT(*) FROM leads WHERE created_at >= {cutoff}"
        )
        qa_asks = count(
            f"SELECT COUNT(*) FROM events WHERE event_type='qa_ask' AND created_at >= {cutoff}"
        )
        # Quiz finishes broken down by kind
        kind_rows = c.execute(
            f"SELECT payload, COUNT(*) AS n FROM events "
            f"WHERE event_type='quiz_finish' AND created_at >= {cutoff} "
            f"GROUP BY payload ORDER BY n DESC"
        ).fetchall()
        # Lead sources
        lead_rows = c.execute(
            f"SELECT source, COUNT(*) AS n FROM leads "
            f"WHERE created_at >= {cutoff} "
            f"GROUP BY source ORDER BY n DESC"
        ).fetchall()
        # Language breakdown (of new users in period)
        lang_rows = c.execute(
            f"SELECT lang, COUNT(*) AS n FROM users "
            f"WHERE created_at >= {cutoff} AND lang IS NOT NULL "
            f"GROUP BY lang ORDER BY n DESC"
        ).fetchall()
        # Traffic source breakdown (of new users in period, from deep links)
        src_rows = c.execute(
            f"SELECT COALESCE(source, '(прямой переход)') AS source, COUNT(*) AS n "
            f"FROM users WHERE created_at >= {cutoff} "
            f"GROUP BY source ORDER BY n DESC"
        ).fetchall()
        total_users = count("SELECT COUNT(*) FROM users")
    return {
        "starts": starts,
        "new_users": new_users,
        "total_users": total_users,
        "quiz_starts": quiz_starts,
        "quiz_finishes": quiz_finishes,
        "leads": leads,
        "qa_asks": qa_asks,
        "by_kind": [dict(r) for r in kind_rows],
        "by_source": [dict(r) for r in lead_rows],
        "by_lang": [dict(r) for r in lang_rows],
        "by_traffic": [dict(r) for r in src_rows],
    }

def get_user_for_reminder(tg_id: int) -> dict | None:
    """Get user data needed to send a reminder (lang, first_name)."""
    with _conn() as c:
        row = c.execute(
            "SELECT tg_id, first_name, lang FROM users WHERE tg_id=?", (tg_id,),
        ).fetchone()
    return dict(row) if row else None

def find_reengagement_targets() -> list[int]:
    """Users who visited the bot yesterday (last activity 24-48h ago), never
    left a lead, and have not yet been sent a re-engagement reminder."""
    with _conn() as c:
        rows = c.execute(
            "SELECT e.tg_id, MAX(e.created_at) AS last_seen "
            "FROM events e "
            "WHERE e.tg_id NOT IN (SELECT tg_id FROM leads) "
            "AND e.tg_id NOT IN (SELECT tg_id FROM reengagement) "
            "GROUP BY e.tg_id "
            "HAVING last_seen <= datetime('now', '-24 hours') "
            "AND last_seen >= datetime('now', '-48 hours')"
        ).fetchall()
    return [r["tg_id"] for r in rows]

def mark_reengaged(tg_id: int):
    """Record that a re-engagement reminder was sent (so we never send twice)."""
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO reengagement(tg_id) VALUES(?)", (tg_id,),
        )

def find_lead_followup_targets() -> list[int]:
    """Users whose first lead was left 24-48h ago and who have not yet
    received a follow-up nudge. 'Left a lead' means they raised their hand —
    this warm-up keeps them from going cold before the firm closes them."""
    with _conn() as c:
        rows = c.execute(
            "SELECT l.tg_id, MIN(l.created_at) AS first_lead "
            "FROM leads l "
            "WHERE l.tg_id NOT IN (SELECT tg_id FROM lead_followup) "
            "GROUP BY l.tg_id "
            "HAVING first_lead <= datetime('now', '-24 hours') "
            "AND first_lead >= datetime('now', '-48 hours')"
        ).fetchall()
    return [r["tg_id"] for r in rows]

def mark_lead_followup(tg_id: int):
    """Record that a lead follow-up was sent (so we never send twice)."""
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO lead_followup(tg_id) VALUES(?)", (tg_id,),
        )

# -*- coding: utf-8 -*-
"""SQLite storage: users, daily message counters, leads, quiz state."""
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "bot.db"

def _conn():
    # timeout/busy_timeout: wait for a lock instead of immediately raising
    # OperationalError("database is locked") under concurrent access, so a
    # rate-limit check never crashes a user's request.
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    return c

def init_db():
    with _conn() as c:
        # WAL lets readers and a writer coexist without blocking — far fewer
        # lock collisions for a bot serving many users concurrently. Persistent
        # in the DB file, so setting it once here is enough.
        c.execute("PRAGMA journal_mode=WAL")
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
        CREATE TABLE IF NOT EXISTS admin_relay (
            admin_chat_id INTEGER,
            message_id INTEGER,
            client_id INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY (admin_chat_id, message_id)
        );
        CREATE TABLE IF NOT EXISTS monitor_snapshots (
            source_key TEXT PRIMARY KEY,   -- stable id of the watched page
            url TEXT,
            content_hash TEXT,             -- hash of normalized visible text
            content_text TEXT,             -- normalized text (for diffing)
            last_checked TEXT,
            last_changed TEXT
        );
        CREATE TABLE IF NOT EXISTS monitor_seen_docs (
            doc_id TEXT PRIMARY KEY,        -- Federal Register document number
            created_at TEXT DEFAULT (datetime('now'))
        );
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
        if days <= 0:
            # "Today": from the start of the current day, not "now minus 0 days"
            # (which would be the current instant and exclude everything today).
            where = "WHERE created_at >= datetime('now', 'start of day')"
            args = ()
        else:
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
            f"""SELECT substr(created_at,1,7) AS month,
                       COUNT(*) AS calls,
                       COALESCE(SUM(cost_usd),0) AS cost_usd
                FROM usage {where}
                GROUP BY month ORDER BY month DESC LIMIT 12""",
            args,
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

# ── Admin→client reply relay ──────────────────────────────────────────────
def save_relay(admin_chat_id: int, message_id: int, client_id: int):
    """Remember that the admin-chat message `message_id` is about `client_id`,
    so when the admin replies to it we know whom to relay the answer to."""
    with _conn() as c:
        c.execute(
            "INSERT OR REPLACE INTO admin_relay(admin_chat_id, message_id, client_id) "
            "VALUES(?,?,?)",
            (admin_chat_id, message_id, client_id),
        )

def get_relay_client(admin_chat_id: int, message_id: int) -> int | None:
    with _conn() as c:
        row = c.execute(
            "SELECT client_id FROM admin_relay WHERE admin_chat_id=? AND message_id=?",
            (admin_chat_id, message_id),
        ).fetchone()
        return row["client_id"] if row else None

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
        # IS NULL guard makes this idempotent: a second pass (or a reset+resend
        # race) can't overwrite an already-recorded reminder timestamp.
        c.execute(
            f"UPDATE quiz_state SET {col}=datetime('now') "
            f"WHERE tg_id=? AND kind=? AND {col} IS NULL",
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
    """Users who interacted with the bot (last action 24-48h ago), did NOT
    request a consultation, and have not yet been sent a re-engagement reminder.

    Browsing, finishing a quiz, getting a checklist, or sending a case for a
    free review all qualify — only an actual 'book a consultation / contact a
    human' lead (sources booking / booking_file / human) suppresses it. Those
    hot leads are handled by find_lead_followup_targets instead, so nobody gets
    two reminders."""
    with _conn() as c:
        rows = c.execute(
            "SELECT e.tg_id, MAX(e.created_at) AS last_seen "
            "FROM events e "
            "WHERE e.tg_id NOT IN "
            "  (SELECT tg_id FROM leads WHERE source IN ('booking','booking_file','human')) "
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
    """Users who actually requested a consultation/contact (a booking /
    booking_file / human lead) 24-48h ago and have not yet received a follow-up
    nudge. This warm-up keeps a hot lead from going cold before the firm closes
    it. Quiz/checklist/case-review/browse users are NOT here — they get the
    re-engagement reminder instead (see find_reengagement_targets)."""
    with _conn() as c:
        rows = c.execute(
            "SELECT l.tg_id, MIN(l.created_at) AS first_lead "
            "FROM leads l "
            "WHERE l.source IN ('booking','booking_file','human') "
            "AND l.tg_id NOT IN (SELECT tg_id FROM lead_followup) "
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

# ───────────────────────────────────── official-source monitoring snapshots

def get_monitor_snapshot(source_key: str) -> dict | None:
    """Return the last stored snapshot for a watched page, or None."""
    with _conn() as c:
        row = c.execute(
            "SELECT source_key, url, content_hash, content_text, last_checked, "
            "last_changed FROM monitor_snapshots WHERE source_key=?",
            (source_key,),
        ).fetchone()
    return dict(row) if row else None

def save_monitor_snapshot(source_key: str, url: str, content_hash: str,
                          content_text: str, changed: bool):
    """Upsert a snapshot. Always bumps last_checked; bumps last_changed only
    when `changed` is True (a substantive change was detected)."""
    with _conn() as c:
        c.execute(
            "INSERT INTO monitor_snapshots"
            "(source_key, url, content_hash, content_text, last_checked, last_changed) "
            "VALUES(?,?,?,?, datetime('now'), "
            "       CASE WHEN ? THEN datetime('now') ELSE NULL END) "
            "ON CONFLICT(source_key) DO UPDATE SET "
            "  url=excluded.url, "
            "  content_hash=excluded.content_hash, "
            "  content_text=excluded.content_text, "
            "  last_checked=datetime('now'), "
            "  last_changed=CASE WHEN ? THEN datetime('now') "
            "                    ELSE monitor_snapshots.last_changed END",
            (source_key, url, content_hash, content_text, changed, changed),
        )

def list_monitor_snapshots() -> list[dict]:
    """All snapshots, for the admin /sources report."""
    with _conn() as c:
        rows = c.execute(
            "SELECT source_key, url, last_checked, last_changed "
            "FROM monitor_snapshots ORDER BY source_key"
        ).fetchall()
    return [dict(r) for r in rows]

def monitor_seen_count() -> int:
    """How many Federal Register docs we've already recorded (0 == first run)."""
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM monitor_seen_docs").fetchone()[0]

def has_doc_seen(doc_id: str) -> bool:
    with _conn() as c:
        return c.execute(
            "SELECT 1 FROM monitor_seen_docs WHERE doc_id=?", (doc_id,)
        ).fetchone() is not None

def mark_doc_seen(doc_id: str):
    with _conn() as c:
        c.execute(
            "INSERT OR IGNORE INTO monitor_seen_docs(doc_id) VALUES(?)", (doc_id,)
        )

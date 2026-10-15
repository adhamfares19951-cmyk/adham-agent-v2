"""SQLite storage: conversation history, saved facts, reminders, daily usage."""
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import config

DB_PATH = config.BASE_DIR / "agent_memory.db"


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _db() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS experience_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                problem TEXT NOT NULL,      -- what the photo/issue showed
                solution TEXT NOT NULL,     -- what Adham did to fix it
                embedding BLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text TEXT NOT NULL,
                due_utc TEXT NOT NULL,          -- ISO datetime in UTC
                repeat TEXT NOT NULL DEFAULT 'none',  -- none | daily | weekly | monthly
                days TEXT NOT NULL DEFAULT '',  -- weekly only: comma list of 0-6 (Mon=0)
                active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS seen_items (
                key TEXT PRIMARY KEY,           -- e.g. tg:Gazarecruiters/1234 or web:pef:9035
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS job_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL,
                category TEXT NOT NULL,         -- job | freelance | aid
                score INTEGER,
                title TEXT,
                url TEXT,
                details TEXT,                   -- post/page text, used for cover letters
                card TEXT,                      -- the message sent to Adham
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage (
                day TEXT NOT NULL,
                kind TEXT NOT NULL,
                count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (day, kind)
            );
            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                sector TEXT NOT NULL,
                location TEXT NOT NULL DEFAULT '',
                contact_info TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',  -- new | drafted | sent | replied | won | lost
                notes TEXT NOT NULL DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Migration: older DBs have a facts table with no embedding column yet.
        cols = {row["name"] for row in c.execute("PRAGMA table_info(facts)").fetchall()}
        if "embedding" not in cols:
            c.execute("ALTER TABLE facts ADD COLUMN embedding BLOB")


# ---------------------------------------------------------------- conversation history

def add_message(role: str, content: str) -> None:
    if not content:
        return
    with _db() as c:
        c.execute("INSERT INTO chat_history (role, content) VALUES (?, ?)", (role, content))


def get_history(limit: int) -> list[dict]:
    with _db() as c:
        rows = c.execute(
            "SELECT role, content FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    history = [
        {"role": "user" if r["role"] == "user" else "assistant", "content": r["content"]}
        for r in reversed(rows)
    ]
    # Start with a user message so every provider accepts the order.
    while history and history[0]["role"] != "user":
        history.pop(0)
    return history


def clear_history() -> None:
    with _db() as c:
        c.execute("DELETE FROM chat_history")


# ---------------------------------------------------------------- saved facts
# Long-term memory. Facts are embedded on save; relevant_facts() retrieves only
# the ones that actually matter for the current message instead of dumping
# every saved fact into every prompt (which stops scaling once there are many).

def add_fact(content: str) -> int:
    import embeddings

    vector = embeddings.embed(content)
    with _db() as c:
        return c.execute(
            "INSERT INTO facts (content, embedding) VALUES (?, ?)", (content, vector)
        ).lastrowid


def list_facts() -> list[sqlite3.Row]:
    with _db() as c:
        return c.execute("SELECT id, content FROM facts ORDER BY id").fetchall()


def relevant_facts(query: str, top_k: int = 8) -> list[sqlite3.Row]:
    """The facts most relevant to `query`, ranked by embedding similarity.
    Falls back to the most recent facts if there are few enough to just show all."""
    with _db() as c:
        rows = c.execute("SELECT id, content, embedding FROM facts ORDER BY id").fetchall()
    if len(rows) <= top_k:
        return rows
    import embeddings

    by_id = {r["id"]: r for r in rows}
    order = embeddings.rank_by_similarity(query, [(r["id"], r["embedding"]) for r in rows], top_k)
    return [by_id[i] for i in order]


def delete_fact(fact_id: int) -> bool:
    with _db() as c:
        return c.execute("DELETE FROM facts WHERE id = ?", (fact_id,)).rowcount > 0


# ---------------------------------------------------------------- experience log
# "I've seen this before": Adham logs a technical problem + how he solved it;
# similar future problems can be matched against this before searching the web.

def add_experience(problem: str, solution: str) -> int:
    import embeddings

    vector = embeddings.embed(f"{problem}\n{solution}")
    with _db() as c:
        return c.execute(
            "INSERT INTO experience_log (problem, solution, embedding) VALUES (?, ?, ?)",
            (problem, solution, vector),
        ).lastrowid


def relevant_experience(query: str, top_k: int = 3) -> list[sqlite3.Row]:
    with _db() as c:
        rows = c.execute("SELECT id, problem, solution, embedding FROM experience_log ORDER BY id").fetchall()
    if not rows:
        return []
    import embeddings

    by_id = {r["id"]: r for r in rows}
    order = embeddings.rank_by_similarity(query, [(r["id"], r["embedding"]) for r in rows], top_k)
    return [by_id[i] for i in order]


# ---------------------------------------------------------------- reminders

def add_reminder(text: str, due_utc: str, repeat: str = "none", days: str = "") -> int:
    with _db() as c:
        return c.execute(
            "INSERT INTO reminders (text, due_utc, repeat, days) VALUES (?, ?, ?, ?)",
            (text, due_utc, repeat, days),
        ).lastrowid


def get_reminder(rem_id: int) -> sqlite3.Row | None:
    with _db() as c:
        return c.execute("SELECT * FROM reminders WHERE id = ?", (rem_id,)).fetchone()


def list_active_reminders() -> list[sqlite3.Row]:
    with _db() as c:
        return c.execute("SELECT * FROM reminders WHERE active = 1 ORDER BY due_utc").fetchall()


def set_reminder_due(rem_id: int, due_utc: str) -> None:
    with _db() as c:
        c.execute("UPDATE reminders SET due_utc = ?, active = 1 WHERE id = ?", (due_utc, rem_id))


def deactivate_reminder(rem_id: int) -> bool:
    with _db() as c:
        return c.execute(
            "UPDATE reminders SET active = 0 WHERE id = ? AND active = 1", (rem_id,)
        ).rowcount > 0


# ---------------------------------------------------------------- settings changed from chat

def get_setting(key: str, default: str = "") -> str:
    with _db() as c:
        row = c.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key: str, value: str) -> None:
    with _db() as c:
        c.execute("INSERT INTO settings (key, value) VALUES (?, ?) "
                  "ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, value))


def matches_since(hours: int) -> list[sqlite3.Row]:
    with _db() as c:
        return c.execute(
            "SELECT * FROM job_matches WHERE created_at >= datetime('now', ?) ORDER BY score DESC",
            (f"-{hours} hours",),
        ).fetchall()


# ---------------------------------------------------------------- job monitor

def seen_keys(prefix: str) -> set[str]:
    with _db() as c:
        rows = c.execute("SELECT key FROM seen_items WHERE key LIKE ?", (prefix + "%",)).fetchall()
    return {r["key"] for r in rows}


def mark_seen(keys: list[str]) -> None:
    with _db() as c:
        c.executemany("INSERT OR IGNORE INTO seen_items (key) VALUES (?)", [(k,) for k in keys])


def add_match(key: str, category: str, score: int, title: str, url: str, details: str, card: str) -> int:
    with _db() as c:
        return c.execute(
            "INSERT INTO job_matches (key, category, score, title, url, details, card) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (key, category, score, title, url, details, card),
        ).lastrowid


def get_match(match_id: int) -> sqlite3.Row | None:
    with _db() as c:
        return c.execute("SELECT * FROM job_matches WHERE id = ?", (match_id,)).fetchone()


def recent_matches(limit: int = 10, category: str | None = None) -> list[sqlite3.Row]:
    with _db() as c:
        if category:
            return c.execute(
                "SELECT * FROM job_matches WHERE category = ? ORDER BY id DESC LIMIT ?", (category, limit)
            ).fetchall()
        return c.execute("SELECT * FROM job_matches ORDER BY id DESC LIMIT ?", (limit,)).fetchall()


# ---------------------------------------------------------------- outreach leads (local businesses)

def add_lead(business_name: str, sector: str, location: str = "", contact_info: str = "") -> int:
    with _db() as c:
        return c.execute(
            "INSERT INTO leads (business_name, sector, location, contact_info) VALUES (?, ?, ?, ?)",
            (business_name, sector, location, contact_info),
        ).lastrowid


def get_lead(lead_id: int) -> sqlite3.Row | None:
    with _db() as c:
        return c.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()


def list_leads(status: str | None = None) -> list[sqlite3.Row]:
    with _db() as c:
        if status:
            return c.execute("SELECT * FROM leads WHERE status = ? ORDER BY id DESC", (status,)).fetchall()
        return c.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()


def update_lead_status(lead_id: int, status: str, notes: str = "") -> bool:
    with _db() as c:
        if notes:
            return c.execute(
                "UPDATE leads SET status = ?, notes = ? WHERE id = ?", (status, notes, lead_id)
            ).rowcount > 0
        return c.execute("UPDATE leads SET status = ? WHERE id = ?", (status, lead_id)).rowcount > 0


# ---------------------------------------------------------------- daily usage

def _today() -> str:
    return datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y-%m-%d")


def add_usage(kind: str) -> int:
    """Count one use of `kind` today and return today's total."""
    day = _today()
    with _db() as c:
        c.execute(
            "INSERT INTO usage (day, kind, count) VALUES (?, ?, 1) "
            "ON CONFLICT(day, kind) DO UPDATE SET count = count + 1",
            (day, kind),
        )
        return c.execute("SELECT count FROM usage WHERE day = ? AND kind = ?", (day, kind)).fetchone()[0]


def get_usage(kind: str) -> int:
    with _db() as c:
        row = c.execute("SELECT count FROM usage WHERE day = ? AND kind = ?", (_today(), kind)).fetchone()
    return row[0] if row else 0

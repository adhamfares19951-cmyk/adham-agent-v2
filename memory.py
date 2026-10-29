"""SQLite storage: conversation history, saved facts, reminders, daily usage."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from zoneinfo import ZoneInfo

import config

DB_PATH = config.BASE_DIR / "agent_memory.db"


@contextmanager
def _db():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with _db() as c:
        try:
            c.execute("ALTER TABLE chat_history ADD COLUMN tools_summary TEXT;")
        except Exception:
            pass
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                last_message_id INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        c.executescript("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT,
                content TEXT,
                tools_summary TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS conversation_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                last_message_id INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            CREATE TABLE IF NOT EXISTS approval_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,          -- publish_video | marketing_campaign | store_mod | server_exec
                payload TEXT NOT NULL,              -- JSON payload or action parameters
                description TEXT NOT NULL,          -- Arabic human-readable action brief
                status TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected | executed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved_at DATETIME
            );
            CREATE TABLE IF NOT EXISTS store_products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL DEFAULT 0.0,
                description TEXT NOT NULL,
                features_json TEXT NOT NULL DEFAULT '[]',
                badge TEXT NOT NULL DEFAULT '',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS client_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                phone_whatsapp TEXT NOT NULL,
                service_or_product TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',  -- new | contacted | in_progress | completed | cancelled
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS verified_leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                business_name TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                source_url TEXT NOT NULL,
                proposed_pitch TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'new',  -- new | pitched | contacted | won | dismissed
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                method TEXT NOT NULL DEFAULT 'GET',
                status_code INTEGER NOT NULL,
                response_body TEXT NOT NULL,
                headers_json TEXT NOT NULL DEFAULT '{}',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_api_cache_expires ON api_cache (expires_at);
        """)

        # Auto-seed initial store products if empty
        prod_count = c.execute("SELECT COUNT(*) FROM store_products").fetchone()[0]
        if prod_count == 0:
            seed_products = [
                (
                    "نظام شامل POS (Shamel POS v1.0)",
                    "أنظمة محاسبة ونقاط بيع",
                    250.0,
                    "نظام كاشير ومبيعات مكتبي متكامل بتصميم عصري (Offline-First) يعمل بدون الحاجة لأي اتصال إنترنت، مخصص للمحلات التجارية، معارض الأزياء، والسوبرماركت، مع إدارة المخزون والفواتير والباركود وتقارير الإغلاق اليومي Z-Report.",
                    json.dumps([
                        "يعمل 100% بدون إنترنت (قاعدة بيانات SQLite محلية فائقة السرعة)",
                        "واجهة كاشير لمس سريعة تدعم شاشات اللمس والباركود",
                        "إدارة المخزون، الجرد، والتنبيه التلقائي بالنواقص",
                        "فواتير حرارية وسندات قبض متوافقة مع جميع طابعات ESC/POS",
                        "تقارير محاسبية مفصلة وأرباح يومية وشهرية"
                    ], ensure_ascii=False),
                    "الأكثر طلباً 🔥",
                    1
                ),
                (
                    "منظومة وكلاء الذكاء الاصطناعي (Custom AI Agents)",
                    "أتمتة وذكاء اصطناعي",
                    350.0,
                    "تطوير وكلاء ذكاء اصطناعي مخصصين لشركتك لأتمتة خدمة العملاء والمبيعات والمتابعة اللحظية عبر تيليجرام وواتساب، مع ربط مباشر بقواعد بياناتك واسترجاع دقيق بدون هلوسة.",
                    json.dumps([
                        "توجيه هجين فائق الذكاء (Ollama محلي + OpenRouter + Gemini)",
                        "رد آلي فوري 24/7 عبر تيليجرام والواتساب بصوت ونص ذكي",
                        "ربط حتمي بقاعدة بيانات العملاء والمنتجات",
                        "لوحة تحكم وطابور موافقات لضمان السيطرة البشرية (HITL)",
                        "تنفيذ تلقائي للمهام والتقارير اليومية"
                    ], ensure_ascii=False),
                    "Enterprise AI 🤖",
                    1
                ),
                (
                    "باقة هندسة وبرمجة شبكات MikroTik",
                    "شبكات وبنية تحتية",
                    150.0,
                    "تصميم وهندسة شبكات MikroTik الاحترافية للشركات والفنادق ومزودي الخدمة، تشمل تقسيم VLANs، دمج خطوط الإنترنت (Load Balancing / PCC)، بوابات الهوت سبوت، وحماية الشبكة من الاختراق.",
                    json.dumps([
                        "تقسيم شبكات متقدم (VLANs & Subnetting) مع عزل أمني صارم",
                        "دمج خطوط الإنترنت (Failover & Bandwidth Aggregation)",
                        "نظام Hotspot وكروت مستخدمين وحماية الماك أدرس",
                        "جدار حماية متطور وسكربتات RouterOS RSC مجربة 100%",
                        "إدارة وتحكم عن بُعد مع مراقبة حية للسيرفرات"
                    ], ensure_ascii=False),
                    "هندسة شبكات ⚡",
                    1
                ),
                (
                    "تصميم وبرمجة منظومات الطاقة الشمسية",
                    "طاقة بديلة وهندسة كهربائية",
                    120.0,
                    "دراسة أحمال هندسية دقيقة 100% وحسابات فيزيائية حتمية لمنظومات الطاقة الشمسية المنزلية والتجارية، مع حساب قدرة الإنفرتر، سعة البطاريات (جل وليثيوم)، وتوزيع الألواح وبرمجة شواحن MPPT.",
                    json.dumps([
                        "حسابات حتمية تمنع الأخطاء وحرق الأجهزة (Zero-Hallucination)",
                        "تحديد دقيق لسعة البطاريات المطلوبة بالأمبير-ساعة (Ah)",
                        "حساب قدرة الإنفرتر بالـ VA مع هامش أمان 30% وتيار الإقلاع",
                        "مخطط توصيل الألواح ونظم الشحن MPPT المتوافقة",
                        "دراسة جدوى وتوفير تكاليف مع تقرير فني شامل"
                    ], ensure_ascii=False),
                    "طاقة نظيفة ☀️",
                    1
                ),
                (
                    "تطوير المواقع والتطبيقات المخصصة",
                    "تطوير برمجيات",
                    400.0,
                    "بناء وتطوير تطبيقات سطح المكتب وتطبيقات الويب السحابية السريعة والآمنة باستخدام أحدث التقنيات (Python, Laravel, Tauri, Vue/Tailwind)، مع معمارية معيارية قابلة للتوسع.",
                    json.dumps([
                        "تطبيقات سطح مكتب سريعة وخفيفة الحجم باستخدام Tauri & Rust/Python",
                        "لوحات تحكم وأنظمة إدارة ويب قوية وآمنة بـ Laravel و FastAPI",
                        "تصاميم فريدة وعصرية متجاوبة بالكامل Dark Tech & Mobile-First",
                        "ربط بوابات الدفع الإلكتروني والرسائل القصيرة والمزامنة السحابية",
                        "كود نظيف مع اختبارات جودة آلية 100%"
                    ], ensure_ascii=False),
                    "Full-Stack 💻",
                    1
                )
            ]
            c.executemany(
                "INSERT INTO store_products (name, category, price, description, features_json, badge, is_active) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                seed_products
            )
        # Migration: older DBs have a facts table with no embedding column yet.
        cols = {row["name"] for row in c.execute("PRAGMA table_info(facts)").fetchall()}
        if "embedding" not in cols:
            c.execute("ALTER TABLE facts ADD COLUMN embedding BLOB")


# ---------------------------------------------------------------- conversation history
# Wave 2.1: Tool turns persistence (tools_summary <= 300 chars), rolling summarization,
# uploaded file placeholder, and async wrappers.
import asyncio


def _check_and_roll_summary(c: sqlite3.Connection) -> None:
    """Summarizes older conversation turns into conversation_summary when history exceeds budget."""
    try:
        count_row = c.execute("SELECT COUNT(*) FROM chat_history").fetchone()
        total = count_row[0] if count_row else 0
        if total > 18:
            # Keep the newest 12 messages raw; summarize all older ones
            cutoff_row = c.execute(
                "SELECT id FROM chat_history ORDER BY id DESC LIMIT 1 OFFSET 12"
            ).fetchone()
            if cutoff_row:
                cutoff = cutoff_row[0]
                old_rows = c.execute(
                    "SELECT id, role, content, tools_summary FROM chat_history WHERE id <= ? ORDER BY id ASC",
                    (cutoff,),
                ).fetchall()
                if old_rows:
                    summary_snippets = []
                    for r in old_rows:
                        speaker = "أدهم" if r["role"] == "user" else "البوت"
                        ts = f" (أدوات: {r['tools_summary']})" if r["tools_summary"] else ""
                        summary_snippets.append(f"{speaker}: {str(r['content'])[:75]}{ts}")
                    compact_chunk = " | ".join(summary_snippets[-6:])

                    existing = c.execute("SELECT summary FROM conversation_summary ORDER BY id DESC LIMIT 1").fetchone()
                    if existing and existing[0]:
                        combined_summary = f"{existing[0]} | {compact_chunk}"[-900:]
                    else:
                        combined_summary = compact_chunk[-900:]

                    c.execute(
                        "INSERT INTO conversation_summary (summary, last_message_id) VALUES (?, ?)",
                        (combined_summary, cutoff),
                    )
                    c.execute("DELETE FROM chat_history WHERE id <= ?", (cutoff,))
    except Exception as e:
        pass


def add_message(role: str, content: str, tools_summary: str | None = None) -> None:
    """Adds a message to history with compact tools_summary and file truncation."""
    if not content:
        return

    # Wave 2.1: Do not store massive uploaded file content as user message
    if role == "user" and len(content) > 1000:
        if "[ملف" in content or "Content-Type:" in content or content.startswith("%PDF-") or "base64" in content:
            content = f"[ملف: محتوى مرفق بحجم {len(content)} حرف تم تحليله بنجاح]"

    clean_summary = tools_summary[:300].strip() if tools_summary else None

    with _db() as c:
        c.execute(
            "INSERT INTO chat_history (role, content, tools_summary) VALUES (?, ?, ?)",
            (role, content, clean_summary),
        )
        _check_and_roll_summary(c)


# Wave 2.1: Add alias for add_chat_message
add_chat_message = add_message


def get_history(limit: int) -> list[dict]:
    """Retrieves history including rolling summary anchor and compact tool turns."""
    with _db() as c:
        sum_row = c.execute("SELECT summary FROM conversation_summary ORDER BY id DESC LIMIT 1").fetchone()
        rows = c.execute(
            "SELECT role, content, tools_summary FROM chat_history ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()

    history = []
    for r in reversed(rows):
        body = r["content"]
        if r["role"] != "user" and r["tools_summary"]:
            body += f"\n[ملخص إجراءات الأدوات: {r['tools_summary']}]"
        history.append({
            "role": "user" if r["role"] == "user" else "assistant",
            "content": body,
        })

    # Prepend rolling summary anchor if present
    if sum_row and sum_row[0]:
        history = [
            {"role": "user", "content": f"[ملخص المحادثات والقرارات السابقة مع أدهم]:\n{sum_row[0]}"},
            {"role": "assistant", "content": "تمام يا أدهم، مستحضر كافة النقاط والقرارات السابقة وجاهز لمتابعة العمل معك."},
        ] + history

    # Ensure conversation starts with a user message
    while history and history[0]["role"] != "user":
        history.pop(0)

    return history


def clear_history() -> None:
    with _db() as c:
        c.execute("DELETE FROM chat_history")
        c.execute("""
            CREATE TABLE IF NOT EXISTS conversation_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                summary TEXT NOT NULL,
                last_message_id INTEGER,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        c.execute("DELETE FROM conversation_summary")


# Async wrappers for non-blocking event-loop execution (Rule 8 & Wave 2.1)
async def async_add_message(role: str, content: str, tools_summary: str | None = None) -> None:
    await asyncio.to_thread(add_message, role, content, tools_summary)


async def async_get_history(limit: int) -> list[dict]:
    return await asyncio.to_thread(get_history, limit)


async def async_clear_history() -> None:
    await asyncio.to_thread(clear_history)


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


# ---------------------------------------------------------------- approval queue

def add_approval_item(action_type: str, description: str, payload: str | dict | list) -> int:
    """Adds a sensitive action request to the approval queue for human review."""
    payload_str = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    with _db() as c:
        return c.execute(
            "INSERT INTO approval_queue (action_type, description, payload, status) VALUES (?, ?, ?, 'pending')",
            (action_type, description, payload_str),
        ).lastrowid


def get_pending_approvals() -> list[sqlite3.Row]:
    """Retrieves all pending actions waiting for Adham's approval."""
    with _db() as c:
        return c.execute(
            "SELECT id, action_type, description, payload, created_at FROM approval_queue "
            "WHERE status = 'pending' ORDER BY id DESC"
        ).fetchall()


def get_approval_item(item_id: int) -> sqlite3.Row | None:
    """Retrieves a single approval item by ID."""
    with _db() as c:
        return c.execute("SELECT * FROM approval_queue WHERE id = ?", (item_id,)).fetchone()


def update_approval_status(item_id: int, status: str) -> bool:
    """Updates approval status (approved | rejected | executed) with resolution timestamp."""
    with _db() as c:
        return c.execute(
            "UPDATE approval_queue SET status = ?, resolved_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, item_id),
        ).rowcount > 0


def claim_approval_for_execution(item_id: int) -> sqlite3.Row | None:
    """Atomically marks a pending approval as 'approved' so it can only be executed once."""
    with _db() as c:
        row = c.execute("SELECT * FROM approval_queue WHERE id = ? AND status = 'pending'", (item_id,)).fetchone()
        if not row:
            return None
        c.execute(
            "UPDATE approval_queue SET status = 'approved', resolved_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'pending'",
            (item_id,)
        )
        return row


def reject_approval_item(item_id: int) -> bool:
    """Atomically marks a pending approval as 'rejected'."""
    with _db() as c:
        return c.execute(
            "UPDATE approval_queue SET status = 'rejected', resolved_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'pending'",
            (item_id,)
        ).rowcount > 0


def list_recent_approvals(limit: int = 10) -> list[sqlite3.Row]:
    """Lists the latest approvals for auditing."""
    with _db() as c:
        return c.execute(
            "SELECT * FROM approval_queue ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


# ---------------------------------------------------------------- store products

def list_products(active_only: bool = True) -> list[sqlite3.Row]:
    """Lists store products and services."""
    with _db() as c:
        if active_only:
            return c.execute(
                "SELECT * FROM store_products WHERE is_active = 1 ORDER BY id ASC"
            ).fetchall()
        return c.execute("SELECT * FROM store_products ORDER BY id ASC").fetchall()


def get_product(product_id: int) -> sqlite3.Row | None:
    """Gets a single product by ID."""
    with _db() as c:
        return c.execute("SELECT * FROM store_products WHERE id = ?", (product_id,)).fetchone()


def add_or_update_product(
    name: str,
    category: str,
    price: float,
    description: str,
    badge: str = "",
    features: list[str] | str = None,
    product_id: int | None = None,
    is_active: int = 1,
) -> int:
    """Adds a new store product or updates an existing one."""
    if features is None:
        features_json = "[]"
    elif isinstance(features, list):
        features_json = json.dumps(features, ensure_ascii=False)
    else:
        features_json = str(features)

    with _db() as c:
        if product_id:
            c.execute(
                "UPDATE store_products SET name = ?, category = ?, price = ?, description = ?, "
                "features_json = ?, badge = ?, is_active = ? WHERE id = ?",
                (name, category, float(price), description, features_json, badge, is_active, product_id),
            )
            return product_id
        return c.execute(
            "INSERT INTO store_products (name, category, price, description, features_json, badge, is_active) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, category, float(price), description, features_json, badge, is_active),
        ).lastrowid


def delete_product(product_id: int) -> bool:
    """Deletes a product by ID."""
    with _db() as c:
        return c.execute("DELETE FROM store_products WHERE id = ?", (product_id,)).rowcount > 0


# ---------------------------------------------------------------- client orders

def create_client_order(
    client_name: str,
    phone_whatsapp: str,
    service_or_product: str,
    details: str = "",
) -> int:
    """Creates a new client order from the web platform or store."""
    with _db() as c:
        return c.execute(
            "INSERT INTO client_orders (client_name, phone_whatsapp, service_or_product, details, status) "
            "VALUES (?, ?, ?, ?, 'new')",
            (client_name.strip(), phone_whatsapp.strip(), service_or_product.strip(), details.strip()),
        ).lastrowid


def list_client_orders(status: str | None = None, limit: int = 50) -> list[sqlite3.Row]:
    """Lists client orders, optionally filtered by status (new | contacted | in_progress | completed)."""
    with _db() as c:
        if status:
            return c.execute(
                "SELECT * FROM client_orders WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return c.execute(
            "SELECT * FROM client_orders ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def update_order_status(order_id: int, status: str) -> bool:
    """Updates order status."""
    with _db() as c:
        return c.execute(
            "UPDATE client_orders SET status = ? WHERE id = ?", (status, order_id)
        ).rowcount > 0


def get_client_order(order_id: int) -> sqlite3.Row | None:
    """Retrieves an order by ID."""
    with _db() as c:
        return c.execute("SELECT * FROM client_orders WHERE id = ?", (order_id,)).fetchone()


# ---------------------------------------------------------------- verified leads (Zero-Hallucination)

def add_verified_lead(
    business_name: str,
    phone: str,
    source_url: str,
    proposed_pitch: str = "",
    status: str = "new",
) -> int:
    """Saves a verified real lead into the database."""
    with _db() as c:
        # Check if URL or phone already exists
        if phone:
            existing = c.execute("SELECT id FROM verified_leads WHERE phone = ?", (phone.strip(),)).fetchone()
            if existing:
                return existing[0]
        return c.execute(
            "INSERT INTO verified_leads (business_name, phone, source_url, proposed_pitch, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (business_name.strip(), phone.strip(), source_url.strip(), proposed_pitch.strip(), status),
        ).lastrowid


def list_verified_leads(status: str | None = None, limit: int = 50) -> list[sqlite3.Row]:
    """Lists verified business leads."""
    with _db() as c:
        if status:
            return c.execute(
                "SELECT * FROM verified_leads WHERE status = ? ORDER BY id DESC LIMIT ?",
                (status, limit),
            ).fetchall()
        return c.execute(
            "SELECT * FROM verified_leads ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()


def update_verified_lead_status(lead_id: int, status: str) -> bool:
    """Updates status of a verified lead (new | pitched | contacted | won | dismissed)."""
    with _db() as c:
        return c.execute(
            "UPDATE verified_leads SET status = ? WHERE id = ?", (status, lead_id)
        ).rowcount > 0


def get_verified_lead(lead_id: int) -> sqlite3.Row | None:
    """Retrieves a single verified lead by ID."""
    with _db() as c:
        return c.execute("SELECT * FROM verified_leads WHERE id = ?", (lead_id,)).fetchone()




"""Unified Async & Sync SQLite State Manager for adham-agent.

Manages persistent memory, agent blackboard tasks, YouTube character assets,
video production pipeline, and lead generation tracking via aiosqlite and sqlite3.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import aiosqlite

from config.settings import settings

logger = logging.getLogger("adham_agent.database")


class DatabaseManager:
    """Unified SQLite State & Memory Manager.
    
    Provides synchronous schema initialization & data seeding, alongside
    high-performance async CRUD operations for autonomous multi-agent pipelines.
    """

    def __init__(self, db_path: Optional[Union[Path, str]] = None) -> None:
        self.db_path: Path = Path(db_path or settings.SQLITE_DB_PATH)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db_sync()

    def _get_sync_connection(self) -> sqlite3.Connection:
        """Create a standard synchronous SQLite connection with row factories enabled."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[aiosqlite.Connection]:
        """Async context manager for SQLite connections with Row row_factory and WAL mode."""
        conn = await aiosqlite.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = aiosqlite.Row
        await conn.execute("PRAGMA journal_mode=WAL;")
        await conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            await conn.close()

    def _init_db_sync(self) -> None:
        """Synchronously initialize all 5 required tables and seed baseline profiles/characters."""
        with self._get_sync_connection() as conn:
            cursor = conn.cursor()

            # 1. memory_profile table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS memory_profile (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    skills_tags TEXT NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 2. leads_and_jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads_and_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    platform TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    description TEXT,
                    client_info TEXT,
                    generated_proposal TEXT,
                    cv_path TEXT,
                    status TEXT DEFAULT 'FOUND',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 3. youtube_characters table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS youtube_characters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    role TEXT NOT NULL,
                    visual_prompt TEXT NOT NULL
                );
            """)

            # 4. youtube_videos table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS youtube_videos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    theme TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    tags TEXT NOT NULL,
                    scenes_json TEXT NOT NULL,
                    status TEXT DEFAULT 'IDEA',
                    video_path TEXT,
                    youtube_video_id TEXT,
                    scheduled_time TIMESTAMP,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 5. agent_tasks table (Blackboard Architecture)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_tasks (
                    id TEXT PRIMARY KEY,
                    assigned_agent TEXT NOT NULL,
                    task_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT DEFAULT 'PENDING',
                    result_json TEXT,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 6. server_projects table (Central Server Project Operations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    project_type TEXT NOT NULL,
                    port INTEGER,
                    status TEXT DEFAULT 'STOPPED',
                    pid INTEGER,
                    health_url TEXT,
                    command_start TEXT,
                    last_checked TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 7. media_production_queue table (Unified Video & Voice Pipeline)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS media_production_queue (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    engine TEXT NOT NULL,
                    voice_name TEXT DEFAULT 'ar-EG-ShakirNeural',
                    script_text TEXT,
                    audio_path TEXT,
                    video_path TEXT,
                    status TEXT DEFAULT 'QUEUED',
                    platform TEXT DEFAULT 'youtube_shorts',
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP
                );
            """)

            # 8. crm_clients table (Clients & Deals CRM)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crm_clients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    business_name TEXT,
                    phone TEXT,
                    email TEXT,
                    category TEXT DEFAULT 'pos_client',
                    status TEXT DEFAULT 'NEW',
                    deal_value REAL DEFAULT 0,
                    notes TEXT,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 9. command_audit_log table (Mobile & Bot Command Logs)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS command_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    command TEXT NOT NULL,
                    source TEXT NOT NULL,
                    status TEXT NOT NULL,
                    output TEXT,
                    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 10. social_accounts table (Omnichannel Social Media Accounts)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS social_accounts (
                    id TEXT PRIMARY KEY,
                    platform_name TEXT NOT NULL,
                    account_handle TEXT,
                    profile_url TEXT,
                    auth_status TEXT DEFAULT 'DISCONNECTED',
                    followers_count INTEGER DEFAULT 0,
                    total_posts INTEGER DEFAULT 0,
                    last_synced TIMESTAMP,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # 11. audience_members table (Comprehensive Audience & Followers CRM)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audience_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username_or_handle TEXT,
                    platform TEXT NOT NULL,
                    contact_phone TEXT,
                    contact_email TEXT,
                    segment TEXT DEFAULT 'general',
                    lifecycle_stage TEXT DEFAULT 'follower',
                    engagement_score INTEGER DEFAULT 1,
                    notes TEXT,
                    tags TEXT,
                    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # Pre-populate social_accounts if empty
            cursor.execute("SELECT COUNT(*) FROM social_accounts;")
            if cursor.fetchone()[0] == 0:
                logger.info("Seeding default social accounts into social_accounts table...")
                default_social = [
                    ("youtube", "YouTube", "@coretradeai", "https://youtube.com/@coretradeai", "CONNECTED", 1420, 18, "Core Trade AI & Dev channel"),
                    ("tiktok", "TikTok", "@coretradeai", "https://tiktok.com/@coretradeai", "CONNECTED", 3850, 42, "Trading & Tech viral shorts"),
                    ("facebook", "Facebook", "Adham Alhabbash", "https://facebook.com/adham.alhabbash", "CONNECTED", 2100, 115, "Personal & business network"),
                    ("instagram", "Instagram", "@coretrade.ai", "https://instagram.com/coretrade.ai", "CONNECTED", 1890, 31, "Carousels & trading charts"),
                    ("twitter", "X / Twitter", "@coretradeai", "https://x.com/coretradeai", "CONNECTED", 940, 68, "Market insights & code"),
                    ("linkedin", "LinkedIn", "Adham Alhabbash", "https://linkedin.com/in/adham-alhabbash", "CONNECTED", 1650, 54, "Enterprise tech & POS network"),
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO social_accounts (id, platform_name, account_handle, profile_url, auth_status, followers_count, total_posts, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, default_social)

            # Pre-populate initial audience database if empty
            cursor.execute("SELECT COUNT(*) FROM audience_members;")
            if cursor.fetchone()[0] == 0:
                sample_audience = [
                    ("أحمد النجار", "@ahmed_naggar", "facebook", "+970599111222", "ahmed@gmail.com", "pos_buyer", "customer", 95, "صاحب سوبرماركت مهتم بنظام شمل POS", "gaza, pos, retail"),
                    ("محمد الدليمي", "@m_dulaimi", "twitter", "+964770123456", "dulaimi.fx@yahoo.com", "vip_trader", "lead", 88, "متداول ذهب XAU/USD سأل عن إكسبيرت MQL5", "iraq, gold, fx"),
                    ("سارة خليل", "@sara_kh", "instagram", "+970592333444", "sara.design@outlook.com", "developer", "follower", 75, "مهتمة ببرمجة بايثون والموشن جرافيك", "design, python, dev"),
                    ("طارق منصور", "@tareq_trade", "youtube", "+971501112233", "tareq@dubaitrade.ae", "vip_trader", "engaged", 90, "علق على فيديو SMC وإدارة رأس المال", "dubai, trading, youtube"),
                    ("عمر البيك", "@omar_pos", "tiktok", "+970599555666", "omar.super@gmail.com", "pos_buyer", "lead", 82, "سأل عن سعر طابعة الفواتير والباركود", "gaza, shamel_pos"),
                ]
                cursor.executemany("""
                    INSERT INTO audience_members (name, username_or_handle, platform, contact_phone, contact_email, segment, lifecycle_stage, engagement_score, notes, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, sample_audience)

            # Pre-populate server_projects if empty
            cursor.execute("SELECT COUNT(*) FROM server_projects;")
            if cursor.fetchone()[0] == 0:
                logger.info("Seeding default server projects into server_projects table...")
                default_projects = [
                    ("shamel-pos", "Shamel POS System", "C:/Projects/shamel-pos", "laravel", 8000, "STOPPED", None, "http://127.0.0.1:8000", "php artisan serve --port=8000"),
                    ("lead-preview-bot", "Lead Preview Bot", "C:/Projects/lead-preview-bot", "laravel", 8081, "STOPPED", None, "http://127.0.0.1:8081", "php artisan serve --port=8081"),
                    ("conquerors_bot", "Conquerors Empire Bot", "C:/Projects/conquerors_bot", "python_bot", None, "STOPPED", None, None, "python main.py"),
                    ("ai-cinematic-studio", "AI Cinematic Studio", "C:/Projects/ai-cinematic-studio", "video_studio", None, "STOPPED", None, None, "python main.py"),
                    ("remotion_studio", "Remotion Video Studio", "C:/Projects/remotion_studio", "video_studio", 3000, "STOPPED", None, "http://127.0.0.1:3000", "npm run dev"),
                    ("adham-agent", "Adham Agent Core Swarm", "C:/Projects/adham-agent", "agent_core", 8080, "RUNNING", None, "http://127.0.0.1:8080/api/status", "python dashboard/server.py"),
                    ("ollama", "Ollama Local AI (Qwen-Coder)", "C:/Users/Administrator/AppData/Local/Programs/Ollama", "ai_llm", 11434, "RUNNING", None, "http://127.0.0.1:11434/api/tags", "ollama serve"),
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO server_projects (id, name, path, project_type, port, status, pid, health_url, command_start)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, default_projects)

            # Pre-populate sample CRM clients if empty
            cursor.execute("SELECT COUNT(*) FROM crm_clients;")
            if cursor.fetchone()[0] == 0:
                sample_clients = [
                    ("سوبرماركت المدينة", "Al Madina Supermarket", "+970599000001", "madina@pos.local", "pos_client", "PROPOSAL_SENT", 1200.0, "طلب عرض سعر شامل لنظام Shamel POS مع طابعة فواتير وباركود."),
                    ("شركة الذهب للتجارة", "Gold Trading Co", "+970599000002", "gold@trade.local", "algo_client", "NEW", 2500.0, "مهتم بأتمتة صفقات الذهب XAU/USD عبر خبير MQL5."),
                    ("صيدلية الأمل", "Al Amal Pharmacy", "+970599000003", "amal@pharmacy.local", "pos_client", "DEAL_WON", 1500.0, "تم الاتفاق على ترخيص نقطة البيع السحابية."),
                ]
                cursor.executemany("""
                    INSERT INTO crm_clients (name, business_name, phone, email, category, status, deal_value, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """, sample_clients)

            # Pre-populate memory_profile if empty
            cursor.execute("SELECT COUNT(*) FROM memory_profile;")
            profile_count = cursor.fetchone()[0]
            if profile_count == 0:
                logger.info("Seeding core profile memory into memory_profile table...")
                profiles = [
                    (
                        "Backend & Enterprise Dev",
                        "Full-Stack & Systems Engineering",
                        "10+ years designing enterprise architectures, POS systems (Shamel POS), "
                        "REST/GraphQL APIs, and desktop/cloud platforms. Specialized in PHP (Laravel), "
                        "Python (AsyncIO, FastAPI), C#, SQLite, and MySQL.",
                        "PHP, Laravel, Python, C#, SQLite, MySQL, POS systems, Shamel POS, REST API, Microservices"
                    ),
                    (
                        "FinTech & Algo Trading",
                        "Algorithmic Trading & Quantitative Analysis",
                        "Expert in MetaTrader 5 (MT5) algorithmic execution, MQL5 Expert Advisors (EAs), "
                        "custom indicators, automated risk management (Break-Even, Partial Close), "
                        "Python quantitative backtesting, and technical analysis on XAU/USD (Gold).",
                        "MetaTrader 5, MT5, MQL5, Expert Advisors, Python, Algo Trading, XAU/USD, Technical Analysis, Risk Management"
                    ),
                    (
                        "Network & SysAdmin",
                        "ISP Networks & Systems Administration",
                        "10 years hands-on experience in enterprise networking, MikroTik RouterOS "
                        "(Winbox, Bandwidth Queues, Firewall rules, Hotspot), VLAN segmentation, "
                        "VPN tunnels (WireGuard, OpenVPN), CCTV surveillance, Windows Server Active Directory, "
                        "and hardware diagnostics.",
                        "MikroTik, Winbox, VLAN, VPN, WireGuard, Windows Server, Active Directory, CCTV, Hardware Repair, IT Support"
                    ),
                ]
                cursor.executemany("""
                    INSERT INTO memory_profile (category, title, content, skills_tags)
                    VALUES (?, ?, ?, ?);
                """, profiles)

            # Pre-populate youtube_characters if empty
            cursor.execute("SELECT COUNT(*) FROM youtube_characters;")
            char_count = cursor.fetchone()[0]
            if char_count == 0:
                logger.info("Seeding 3D Pixar-style fruit characters into youtube_characters table...")
                characters = [
                    (
                        "Mr. Orange",
                        "Hardworking Husband",
                        "Cute 3D Pixar-style anthropomorphic orange fruit character, big expressive eyes, "
                        "wearing a simple blue work cap, realistic peel texture, cinematic lighting, 8k"
                    ),
                    (
                        "Mrs. Strawberry",
                        "Arrogant/Betraying Wife",
                        "3D Pixar-style anthropomorphic strawberry character, long eyelashes, "
                        "wearing a tiny golden crown leaf and pearl necklace, glossy red texture, expressive face, 8k"
                    ),
                    (
                        "Rich Banana",
                        "Wealthy Rival",
                        "3D Pixar-style anthropomorphic banana character, wearing cool black sunglasses, "
                        "a tiny gold chain, arrogant smirk, bright yellow smooth texture, luxury vibe, 8k"
                    ),
                    (
                        "Baby Apple",
                        "Innocent Child",
                        "Tiny cute 3D Pixar-style baby red apple character, huge watery innocent eyes, "
                        "holding a small pacifier, adorable proportions, 8k"
                    ),
                ]
                cursor.executemany("""
                    INSERT OR IGNORE INTO youtube_characters (name, role, visual_prompt)
                    VALUES (?, ?, ?);
                """, characters)

            conn.commit()

    # =========================================================================
    # Async CRUD Operations: Agent Tasks (Blackboard Engine)
    # =========================================================================

    async def add_task(
        self,
        assigned_agent: str,
        task_type: str,
        payload: Union[Dict[str, Any], str],
        task_id: Optional[str] = None,
    ) -> str:
        """Register a new task on the agent blackboard."""
        actual_id = task_id or str(uuid.uuid4())
        payload_str = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        now = datetime.utcnow().isoformat()

        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO agent_tasks (id, assigned_agent, task_type, payload_json, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'PENDING', ?, ?);
            """, (actual_id, assigned_agent, task_type, payload_str, now, now))
            await conn.commit()

        return actual_id

    async def get_pending_tasks(self, assigned_agent: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch all PENDING tasks from the blackboard, optionally filtered by agent."""
        query = "SELECT * FROM agent_tasks WHERE status = 'PENDING'"
        params: List[Any] = []
        if assigned_agent:
            query += " AND assigned_agent = ?"
            params.append(assigned_agent)
        query += " ORDER BY created_at ASC"

        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    try:
                        item["payload_json"] = json.loads(item["payload_json"])
                    except Exception:
                        pass
                    results.append(item)
                return results

    async def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Union[Dict[str, Any], str]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update the status, output artifact, or error of a blackboard task."""
        result_str = None
        if result is not None:
            result_str = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)

        now = datetime.utcnow().isoformat()
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                UPDATE agent_tasks
                SET status = ?, result_json = ?, error_message = ?, updated_at = ?
                WHERE id = ?;
            """, (status, result_str, error_message, now, task_id))
            await conn.commit()
            return cursor.rowcount > 0

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific task by its unique ID."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM agent_tasks WHERE id = ?", (task_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                data = dict(row)
                try:
                    data["payload_json"] = json.loads(data["payload_json"])
                except Exception:
                    pass
                if data.get("result_json"):
                    try:
                        data["result_json"] = json.loads(data["result_json"])
                    except Exception:
                        pass
                return data

    # =========================================================================
    # Async CRUD Operations: YouTube Characters & Video Pipeline
    # =========================================================================

    async def get_characters(self) -> List[Dict[str, Any]]:
        """Retrieve all registered 3D Pixar drama characters."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM youtube_characters ORDER BY id ASC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_character_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a character definition by name."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM youtube_characters WHERE name = ?", (name,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def save_youtube_script(
        self,
        theme: str,
        title: str,
        description: str,
        tags: Union[List[str], str],
        scenes: Union[List[Dict[str, Any]], str],
        status: str = "IDEA",
    ) -> int:
        """Insert a newly authored YouTube script & scene storyboard into the database."""
        tags_str = tags if isinstance(tags, str) else ",".join(tags)
        scenes_str = scenes if isinstance(scenes, str) else json.dumps(scenes, ensure_ascii=False)

        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO youtube_videos (theme, title, description, tags, scenes_json, status)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (theme, title, description, tags_str, scenes_str, status))
            await conn.commit()
            return cursor.lastrowid

    async def update_youtube_video_status(
        self,
        video_id: int,
        status: str,
        video_path: Optional[str] = None,
        youtube_video_id: Optional[str] = None,
        views: Optional[int] = None,
        likes: Optional[int] = None,
    ) -> bool:
        """Update production or publish status of a YouTube video."""
        updates: List[str] = ["status = ?"]
        params: List[Any] = [status]

        if video_path is not None:
            updates.append("video_path = ?")
            params.append(video_path)
        if youtube_video_id is not None:
            updates.append("youtube_video_id = ?")
            params.append(youtube_video_id)
        if views is not None:
            updates.append("views = ?")
            params.append(views)
        if likes is not None:
            updates.append("likes = ?")
            params.append(likes)

        params.append(video_id)
        query = f"UPDATE youtube_videos SET {', '.join(updates)} WHERE id = ?;"

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.rowcount > 0

    async def get_youtube_videos(
        self,
        status: Optional[str] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Fetch YouTube videos filtered by status."""
        query = "SELECT * FROM youtube_videos"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    data = dict(row)
                    try:
                        data["scenes_json"] = json.loads(data["scenes_json"])
                    except Exception:
                        pass
                    results.append(data)
                return results

    # =========================================================================
    # Async CRUD Operations: Leads and Career Opportunities
    # =========================================================================

    async def save_job_lead(
        self,
        platform: str,
        title: str,
        url: str,
        description: str = "",
        client_info: str = "",
        generated_proposal: str = "",
        cv_path: str = "",
        status: str = "FOUND",
    ) -> int:
        """Insert or update a job posting or freelance lead."""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO leads_and_jobs (platform, title, url, description, client_info, generated_proposal, cv_path, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    description = excluded.description,
                    client_info = excluded.client_info,
                    generated_proposal = CASE WHEN excluded.generated_proposal != '' THEN excluded.generated_proposal ELSE leads_and_jobs.generated_proposal END,
                    cv_path = CASE WHEN excluded.cv_path != '' THEN excluded.cv_path ELSE leads_and_jobs.cv_path END,
                    status = excluded.status;
            """, (platform, title, url, description, client_info, generated_proposal, cv_path, status))
            await conn.commit()
            return cursor.lastrowid

    async def get_leads_and_jobs(
        self,
        status: Optional[str] = None,
        platform: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve recorded leads and job postings."""
        query = "SELECT * FROM leads_and_jobs WHERE 1=1"
        params: List[Any] = []
        if status:
            query += " AND status = ?"
            params.append(status)
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    # =========================================================================
    # Async CRUD Operations: Profile Memory
    # =========================================================================

    async def get_profile_memory(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch Adham's profile memory items, optionally filtered by category."""
        query = "SELECT * FROM memory_profile"
        params: List[Any] = []
        if category:
            query += " WHERE category = ?"
            params.append(category)
        query += " ORDER BY id ASC"

        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_profile_memory(
        self,
        category: str,
        title: str,
        content: str,
        skills_tags: str,
    ) -> int:
        """Insert or update a profile memory category."""
        now = datetime.utcnow().isoformat()
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO memory_profile (category, title, content, skills_tags, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (category, title, content, skills_tags, now))
            await conn.commit()
            return cursor.lastrowid

    async def get_dashboard_counts(self) -> Dict[str, int]:
        """Retrieve live summary counts for system dashboard."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT COUNT(*) FROM youtube_videos;") as c:
                total_videos = (await c.fetchone())[0]

            async with conn.execute("SELECT COUNT(*) FROM youtube_videos WHERE status IN ('PUBLISHED', 'PUBLISHED_SIMULATED');") as c:
                published_videos = (await c.fetchone())[0]

            async with conn.execute("SELECT COUNT(*) FROM leads_and_jobs;") as c:
                total_leads = (await c.fetchone())[0]

            async with conn.execute("SELECT COUNT(*) FROM leads_and_jobs WHERE cv_path != '';") as c:
                generated_cvs = (await c.fetchone())[0]

            async with conn.execute("SELECT COUNT(*) FROM agent_tasks WHERE status = 'PENDING';") as c:
                pending_tasks = (await c.fetchone())[0]

            return {
                "total_videos": total_videos,
                "published_videos": published_videos,
                "total_leads": total_leads,
                "generated_cvs": generated_cvs,
                "pending_tasks": pending_tasks,
            }

    # =========================================================================
    # Async CRUD Operations: Server Projects
    # =========================================================================

    async def get_server_projects(self) -> List[Dict[str, Any]]:
        """Fetch all registered server projects."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM server_projects ORDER BY id ASC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_project_status(
        self,
        project_id: str,
        status: str,
        pid: Optional[int] = None,
    ) -> bool:
        """Update live running status and PID of a server project."""
        now = datetime.utcnow().isoformat()
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                UPDATE server_projects
                SET status = ?, pid = ?, last_checked = ?
                WHERE id = ?;
            """, (status, pid, now, project_id))
            await conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # Async CRUD Operations: Media Production Queue
    # =========================================================================

    async def add_media_job(
        self,
        title: str,
        topic: str,
        engine: str = "remotion",
        voice_name: str = "ar-EG-ShakirNeural",
        script_text: str = "",
        platform: str = "youtube_shorts",
    ) -> str:
        """Queue a new video/audio media production job."""
        job_id = str(uuid.uuid4())[:8]
        async with self.get_connection() as conn:
            await conn.execute("""
                INSERT INTO media_production_queue (id, title, topic, engine, voice_name, script_text, platform, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'QUEUED');
            """, (job_id, title, topic, engine, voice_name, script_text, platform))
            await conn.commit()
            return job_id

    async def get_media_jobs(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Retrieve recent media production jobs."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM media_production_queue ORDER BY created_at DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_media_job(
        self,
        job_id: str,
        status: str,
        audio_path: Optional[str] = None,
        video_path: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update progress or completion of a media production job."""
        updates: List[str] = ["status = ?"]
        params: List[Any] = [status]

        if audio_path is not None:
            updates.append("audio_path = ?")
            params.append(audio_path)
        if video_path is not None:
            updates.append("video_path = ?")
            params.append(video_path)
        if error_message is not None:
            updates.append("error_message = ?")
            params.append(error_message)
        if status in ("READY", "PUBLISHED", "FAILED"):
            updates.append("completed_at = CURRENT_TIMESTAMP")

        params.append(job_id)
        query = f"UPDATE media_production_queue SET {', '.join(updates)} WHERE id = ?;"

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # Async CRUD Operations: CRM Clients
    # =========================================================================

    async def get_crm_clients(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch CRM clients, optionally filtered by deal status."""
        query = "SELECT * FROM crm_clients"
        params: List[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY last_interaction DESC"

        async with self.get_connection() as conn:
            async with conn.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_crm_client(
        self,
        name: str,
        business_name: str = "",
        phone: str = "",
        email: str = "",
        category: str = "pos_client",
        status: str = "NEW",
        deal_value: float = 0.0,
        notes: str = "",
    ) -> int:
        """Create a new client in the unified CRM."""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO crm_clients (name, business_name, phone, email, category, status, deal_value, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, business_name, phone, email, category, status, deal_value, notes))
            await conn.commit()
            return cursor.lastrowid

    # =========================================================================
    # Async CRUD Operations: Audit Log
    # =========================================================================

    async def log_command_audit(
        self,
        command: str,
        source: str = "mobile_pwa",
        status: str = "SUCCESS",
        output: str = "",
    ) -> int:
        """Record an executed command into the central audit trail."""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO command_audit_log (command, source, status, output)
                VALUES (?, ?, ?, ?);
            """, (command, source, status, output[:1000]))
            await conn.commit()
            return cursor.lastrowid

    async def get_recent_audit_logs(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Retrieve recent commands executed from mobile or telegram."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM command_audit_log ORDER BY executed_at DESC LIMIT ?", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    # =========================================================================
    # Async CRUD Operations: Social Media Accounts
    # =========================================================================

    async def get_social_accounts(self) -> List[Dict[str, Any]]:
        """Fetch all connected social media accounts with follower counts and health."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT * FROM social_accounts ORDER BY followers_count DESC") as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def update_social_account(
        self,
        platform_id: str,
        auth_status: Optional[str] = None,
        followers_count: Optional[int] = None,
        total_posts: Optional[int] = None,
    ) -> bool:
        """Update metrics or status of a social account."""
        updates: List[str] = ["last_synced = CURRENT_TIMESTAMP"]
        params: List[Any] = []

        if auth_status is not None:
            updates.append("auth_status = ?")
            params.append(auth_status)
        if followers_count is not None:
            updates.append("followers_count = ?")
            params.append(followers_count)
        if total_posts is not None:
            updates.append("total_posts = ?")
            params.append(total_posts)

        params.append(platform_id)
        query = f"UPDATE social_accounts SET {', '.join(updates)} WHERE id = ?;"

        async with self.get_connection() as conn:
            cursor = await conn.execute(query, params)
            await conn.commit()
            return cursor.rowcount > 0

    # =========================================================================
    # Async CRUD Operations: Audience Members
    # =========================================================================

    async def get_audience_members(
        self,
        platform: Optional[str] = None,
        segment: Optional[str] = None,
        query: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Retrieve audience members filtered by platform, segment, or search query."""
        sql = "SELECT * FROM audience_members WHERE 1=1"
        params: List[Any] = []

        if platform:
            sql += " AND platform = ?"
            params.append(platform)
        if segment:
            sql += " AND segment = ?"
            params.append(segment)
        if query:
            sql += " AND (name LIKE ? OR username_or_handle LIKE ? OR notes LIKE ? OR tags LIKE ?)"
            wildcard = f"%{query}%"
            params.extend([wildcard, wildcard, wildcard, wildcard])

        sql += " ORDER BY engagement_score DESC, last_interaction DESC LIMIT ?"
        params.append(limit)

        async with self.get_connection() as conn:
            async with conn.execute(sql, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_audience_member(
        self,
        name: str,
        username_or_handle: str = "",
        platform: str = "general",
        contact_phone: str = "",
        contact_email: str = "",
        segment: str = "general",
        lifecycle_stage: str = "follower",
        engagement_score: int = 50,
        notes: str = "",
        tags: str = "",
    ) -> int:
        """Register a new member/follower in the master audience database."""
        async with self.get_connection() as conn:
            cursor = await conn.execute("""
                INSERT INTO audience_members (name, username_or_handle, platform, contact_phone, contact_email, segment, lifecycle_stage, engagement_score, notes, tags)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (name, username_or_handle, platform, contact_phone, contact_email, segment, lifecycle_stage, engagement_score, notes, tags))
            await conn.commit()
            return cursor.lastrowid

    async def get_audience_summary(self) -> Dict[str, Any]:
        """Aggregate total audience reach, platform breakdown, and segment counts."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT COUNT(*), SUM(followers_count) FROM social_accounts;") as c:
                row = await c.fetchone()
                total_platforms = row[0] or 0
                total_social_followers = row[1] or 0

            async with conn.execute("SELECT COUNT(*) FROM audience_members;") as c:
                total_audience_records = (await c.fetchone())[0]

            async with conn.execute("SELECT platform, COUNT(*) FROM audience_members GROUP BY platform;") as c:
                by_platform = {r[0]: r[1] for r in await c.fetchall()}

            async with conn.execute("SELECT segment, COUNT(*) FROM audience_members GROUP BY segment;") as c:
                by_segment = {r[0]: r[1] for r in await c.fetchall()}

            return {
                "total_platforms": total_platforms,
                "total_social_followers": total_social_followers,
                "total_audience_records": total_audience_records,
                "by_platform": by_platform,
                "by_segment": by_segment,
            }


# Global default database manager instance
db_manager = DatabaseManager()

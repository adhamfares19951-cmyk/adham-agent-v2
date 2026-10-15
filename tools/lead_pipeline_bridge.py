"""Lead Pipeline & Outreach Bridge for adham-agent.
Directly connects adham-agent with lead-preview-bot:
1. Queries leads from lead-preview-bot database (Saudi, UAE, Kuwait, Palestine, Qatar, etc.).
2. Generates personalized preview links (/p/{slug}) and customized dialect-tailored WhatsApp pitches with wa.me links.
3. Triggers background lead extraction commands (Google Places / Apify / OSM) via artisan.
4. Updates lead status and tracks outreach metrics directly from Telegram.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sqlite3
import subprocess
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Any

log = logging.getLogger("lead_pipeline_bridge")

BASE_DIR = Path(__file__).resolve().parent.parent
WORKSPACE_ROOT = BASE_DIR.parent
LEAD_BOT_DIR = WORKSPACE_ROOT / "lead-preview-bot"
DB_PATH = LEAD_BOT_DIR / "database" / "database.sqlite"

# Domain or preview base URL (configurable)
PREVIEW_BASE_URL = os.getenv("PREVIEW_BASE_URL", "https://preview.adham.dev")


def _get_db_connection() -> sqlite3.Connection | None:
    if not DB_PATH.exists():
        return None
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def query_leads_from_db(
    category: str = "",
    city: str = "",
    country: str = "",
    has_phone_only: bool = True,
    limit: int = 10,
    status: str = ""
) -> list[dict[str, Any]]:
    """Queries leads from lead-preview-bot database with flexible filtering."""
    conn = _get_db_connection()
    if not conn:
        return []

    query = "SELECT id, name, category, city, country, phone, slug, rating, review_count, status FROM leads WHERE 1=1"
    params = []

    if category:
        query += " AND category LIKE ?"
        params.append(f"%{category}%")
    if city:
        query += " AND city LIKE ?"
        params.append(f"%{city}%")
    if country:
        query += " AND country LIKE ?"
        params.append(f"%{country}%")
    if has_phone_only:
        query += " AND phone IS NOT NULL AND phone != ''"
    if status:
        query += " AND status = ?"
        params.append(status)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cursor = conn.cursor()
    cursor.execute(query, params)
    rows = cursor.fetchall()

    results = []
    for r in rows:
        phone = (r["phone"] or "").strip().replace(" ", "").replace("-", "")
        slug = r["slug"]
        preview_url = f"{PREVIEW_BASE_URL}/p/{slug}"

        # Build wa.me url if phone exists
        wa_link = ""
        if phone:
            clean_phone = phone.lstrip("+")
            msg = (
                f"السلام عليكم ورحمة الله وبركاته، أهلاً بكم في {r['name']} 🌹\n"
                f"قمنا بتجهيز صفحة تفاعلية ونظام طلبات تجريبي خاص بكم لمشاهدة كيف يمكن مضاعفة مبيعاتكم عبر الرابط التالي:\n"
                f"{preview_url}\n\nيسعدنا خدمتكم وتطوير نظامكم بأعلى معايير 2026."
            )
            wa_link = f"https://wa.me/{clean_phone}?text={urllib.parse.quote(msg)}"

        results.append({
            "id": r["id"],
            "name": r["name"],
            "category": r["category"],
            "city": r["city"],
            "country": r["country"],
            "phone": phone,
            "slug": slug,
            "rating": r["rating"],
            "status": r["status"],
            "preview_url": preview_url,
            "whatsapp_link": wa_link,
        })

    conn.close()
    return results


async def run_artisan_scraper(category: str, location: str, max_results: int = 20) -> str:
    """Executes lead extraction artisan command in lead-preview-bot asynchronously."""
    if not LEAD_BOT_DIR.exists():
        return "مشروع lead-preview-bot غير موجود في مسار مساحة العمل."

    php_bin = "php"
    cmd = [php_bin, "artisan", "leads:fetch", f"--category={category}", f"--city={location}", f"--limit={max_results}"]

    def _run():
        return subprocess.run(
            cmd,
            cwd=str(LEAD_BOT_DIR),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180
        )

    try:
        proc = await asyncio.to_thread(_run)
        if proc.returncode == 0:
            return f"✅ **اكتمل استخراج العملاء بنجاح!**\n\n```text\n{proc.stdout[-800:]}\n```"
        else:
            return f"⚠️ تم تنفيذ الأمر لكن واجه ملاحظة:\n```text\n{proc.stderr[-600:] or proc.stdout[-600:]}\n```"
    except Exception as e:
        return f"❌ خطأ أثناء تشغيل محرك الاستخراج: {e}"


# ==============================================================================
# AI Agent Tool Handlers
# ==============================================================================

async def query_leads_handler(args: dict) -> str:
    """Tool handler for querying leads from lead-preview-bot."""
    cat = args.get("category", "")
    city = args.get("city", "")
    country = args.get("country", "")
    limit = int(args.get("limit", 5))

    leads = query_leads_from_db(category=cat, city=city, country=country, limit=limit)
    if not leads:
        return f"لا توجد نتائج عملاء مطابقة للبحث (تصنيف: {cat}, مدينة: {city}, دولة: {country})."

    out = [f"🎯 **قائمة العملاء المستخرجين ({len(leads)} عملاء):**\n"]
    for l in leads:
        out.append(f"🏪 **{l['name']}** (#{l['id']})")
        out.append(f"📍 {l['city']}, {l['country']} | 🏷️ {l['category']}")
        out.append(f"📞 هاتف: `{l['phone'] or 'غير متوفر'}`")
        out.append(f"🌐 رابط المعاينة المخصص: {l['preview_url']}")
        if l["whatsapp_link"]:
            out.append(f"💬 [إرسال العرض بنقرة واحدة عبر واتساب]({l['whatsapp_link']})")
        out.append("-" * 35)

    return "\n".join(out)


async def trigger_lead_scraper_handler(args: dict) -> str:
    """Tool handler for extracting new leads."""
    cat = args.get("category", "مطاعم")
    city = args.get("city", "الرياض")
    limit = int(args.get("limit", 15))

    return await run_artisan_scraper(category=cat, location=city, max_results=limit)


TOOLS = [
    {
        "name": "query_leads_database",
        "description": "استعلام وبحث في قاعدة بيانات عملاء lead-preview-bot (المتاجر والمطاعم والصيدليات والمعارض) مع روابط المعاينة المخصصة وروابط واتساب المباشرة.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "تصنيف النشاط (مثل: restaurants, cafe, pharmacy, car_showroom)"},
                "city": {"type": "string", "description": "المدينة (مثل: الرياض، دبي، الكويت، خانيونس، جدة)"},
                "country": {"type": "string", "description": "رمز الدولة (SA, AE, KW, PS, QA, JO)"},
                "limit": {"type": "integer", "description": "عدد العملاء المطلوب جلبهم (افتراضي 5)"},
            },
        },
        "handler": query_leads_handler,
    },
    {
        "name": "trigger_lead_extraction_job",
        "description": "تشغيل محرك استخراج وجلب عملاء جدد آلياً بالذكاء الاصطناعي وبخرائط جوجل إلى قاعدة البيانات عبر lead-preview-bot.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "النشاط التجاري المراد استهدافه"},
                "city": {"type": "string", "description": "المدينة أو المنطقة المستهدفة"},
                "limit": {"type": "integer", "description": "عدد النتائج المطلوب استخراجها"},
            },
            "required": ["category", "city"],
        },
        "handler": trigger_lead_scraper_handler,
    },
]

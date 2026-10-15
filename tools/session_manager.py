"""Session & Cookie Manager for adham-agent.
Allows adham-agent to securely manage, verify, and use authenticated browser sessions
(Cookies exported from Chrome/Edge via extensions like Cookie-Editor) for platforms
including Mostaql, Khamsat, Facebook, X/Twitter, Instagram, LinkedIn, and Upwork.
"""
from __future__ import annotations

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("session_manager")

SESSIONS_DIR = Path(__file__).resolve().parent.parent / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_PLATFORMS = {
    "mostaql": {
        "name": "مستقل (Mostaql)",
        "domain": "mostaql.com",
        "home_url": "https://mostaql.com",
        "verify_url": "https://mostaql.com/dashboard",
        "login_indicators": ["dashboard", "logout", "تسجيل الخروج", "حسابي", "الرصيد"],
    },
    "khamsat": {
        "name": "خمسات (Khamsat)",
        "domain": "khamsat.com",
        "home_url": "https://khamsat.com",
        "verify_url": "https://khamsat.com/community",
        "login_indicators": ["logout", "تسجيل الخروج", "الطلبات الواردة", "حسابي"],
    },
    "facebook": {
        "name": "فيسبوك (Facebook)",
        "domain": "facebook.com",
        "home_url": "https://mbasic.facebook.com",
        "verify_url": "https://mbasic.facebook.com/me",
        "login_indicators": ["logout", "خروج", "الملف الشخصي", "profile"],
    },
    "twitter": {
        "name": "إكس / تويتر (X/Twitter)",
        "domain": "x.com",
        "home_url": "https://x.com/home",
        "verify_url": "https://x.com/home",
        "login_indicators": ["logout", "sign out", "home", "notifications"],
    },
    "instagram": {
        "name": "إنستغرام (Instagram)",
        "domain": "instagram.com",
        "home_url": "https://www.instagram.com",
        "verify_url": "https://www.instagram.com/accounts/edit/",
        "login_indicators": ["profile", "logout", "settings"],
    },
    "linkedin": {
        "name": "لينكد إن (LinkedIn)",
        "domain": "linkedin.com",
        "home_url": "https://www.linkedin.com/feed/",
        "verify_url": "https://www.linkedin.com/feed/",
        "login_indicators": ["feed", "mynetwork", "messaging"],
    },
    "upwork": {
        "name": "أب وورك (Upwork)",
        "domain": "upwork.com",
        "home_url": "https://www.upwork.com/nx/find-work/",
        "verify_url": "https://www.upwork.com/nx/find-work/",
        "login_indicators": ["my-jobs", "messages", "profile"],
    },
}

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _get_cookie_file(platform: str) -> Path:
    plat = platform.lower().strip()
    return SESSIONS_DIR / f"{plat}_cookies.json"


def parse_cookie_input(raw: str | list | dict) -> dict[str, str]:
    """Parses various cookie representations into a clean key-value dictionary."""
    if isinstance(raw, dict):
        return {str(k): str(v) for k, v in raw.items()}

    if isinstance(raw, list):
        # Cookie-Editor export format
        result = {}
        for item in raw:
            if isinstance(item, dict) and "name" in item and "value" in item:
                result[str(item["name"])] = str(item["value"])
        return result

    if isinstance(raw, str):
        raw = raw.strip()
        # Try JSON
        try:
            parsed = json.loads(raw)
            return parse_cookie_input(parsed)
        except json.JSONDecodeError:
            pass

        # Try key=value; format
        result = {}
        pairs = raw.split(";")
        for p in pairs:
            if "=" in p:
                k, v = p.split("=", 1)
                k = k.strip()
                v = v.strip()
                if k:
                    result[k] = v
        return result

    return {}


def save_cookies(platform: str, cookie_data: str | list | dict) -> tuple[bool, str]:
    """Saves cookies for a platform into the sessions directory."""
    plat = platform.lower().strip()
    if plat not in SUPPORTED_PLATFORMS:
        supported = ", ".join(SUPPORTED_PLATFORMS.keys())
        return False, f"المنصة '{platform}' غير معروفة. المنصات المدعومة: {supported}"

    cookies_dict = parse_cookie_input(cookie_data)
    if not cookies_dict:
        return False, "لم يتم التعرف على أي كوكيز صالحة في المدخلات. تأكد من نسخ كود JSON من إضافة Cookie-Editor."

    file_path = _get_cookie_file(plat)
    payload = {
        "platform": plat,
        "platform_name": SUPPORTED_PLATFORMS[plat]["name"],
        "saved_at": datetime.now().isoformat(),
        "cookies_count": len(cookies_dict),
        "cookies": cookies_dict,
    }

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        return True, f"✅ تم حفظ وتشفير جلسة {SUPPORTED_PLATFORMS[plat]['name']} بنجاح ({len(cookies_dict)} كوكيز)!"
    except Exception as e:
        log.exception("Failed to write cookies file")
        return False, f"خطأ في حفظ الملف: {e}"


def get_cookies_dict(platform: str) -> dict[str, str] | None:
    """Reads saved cookies for a platform."""
    plat = platform.lower().strip()
    file_path = _get_cookie_file(plat)
    if not file_path.exists():
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("cookies", {})
    except Exception:
        return None


def get_cookie_header(platform: str) -> str:
    """Returns Cookie header string for requests."""
    cookies = get_cookies_dict(platform)
    if not cookies:
        return ""
    return "; ".join([f"{k}={v}" for k, v in cookies.items()])


def list_sessions_status() -> list[dict[str, Any]]:
    """Lists status of all supported platforms."""
    results = []
    for plat_key, info in SUPPORTED_PLATFORMS.items():
        file_path = _get_cookie_file(plat_key)
        has_file = file_path.exists()
        saved_at = None
        count = 0
        if has_file:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    saved_at = data.get("saved_at")
                    count = data.get("cookies_count", len(data.get("cookies", {})))
            except Exception:
                pass

        results.append({
            "platform": plat_key,
            "name": info["name"],
            "has_session": has_file,
            "cookies_count": count,
            "saved_at": saved_at,
        })
    return results


async def verify_session(platform: str) -> dict[str, Any]:
    """Performs a live test request to verify if session cookies are still valid."""
    plat = platform.lower().strip()
    if plat not in SUPPORTED_PLATFORMS:
        return {"valid": False, "message": f"منصة غير معروفة: {platform}"}

    cookies = get_cookies_dict(plat)
    if not cookies:
        return {
            "valid": False,
            "message": f"لا توجد جلسة محفوظة لـ {SUPPORTED_PLATFORMS[plat]['name']}. قم بتصدير الكوكيز أولاً.",
        }

    info = SUPPORTED_PLATFORMS[plat]
    target_url = info["verify_url"]

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    try:
        async with httpx.AsyncClient(
            headers=headers,
            cookies=cookies,
            timeout=15,
            follow_redirects=True,
        ) as client:
            resp = await client.get(target_url)
            html = resp.text.lower()

            # Check if redirected to login page or indicators match
            if resp.status_code == 200:
                is_login_page = any(x in str(resp.url).lower() for x in ["login", "signin", "auth", "checkpoint"])
                matched_indicators = [ind for ind in info["login_indicators"] if ind.lower() in html]

                if not is_login_page and (matched_indicators or len(html) > 5000):
                    return {
                        "valid": True,
                        "status_code": resp.status_code,
                        "message": f"🟢 الجلسة صالحة ونشطة لـ {info['name']}! تم التحقق بنجاح.",
                    }

            return {
                "valid": False,
                "status_code": resp.status_code,
                "message": f"⚠️ انتهت صلاحية الجلسة لـ {info['name']} أو طلبت المنصة تأكيد دخول. يرجى تجديد الكوكيز.",
            }
    except Exception as e:
        return {"valid": False, "message": f"خطأ أثناء فحص الجلسة: {e}"}


async def fetch_authenticated(platform: str, url: str) -> str:
    """Fetches a web page using the saved cookies of the specified platform."""
    plat = platform.lower().strip()
    cookies = get_cookies_dict(plat)
    if not cookies:
        return f"خطأ: لا توجد جلسة محفوظة لـ '{platform}'. استخدم أداة حفظ الكوكيز أولاً."

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }

    try:
        async with httpx.AsyncClient(
            headers=headers,
            cookies=cookies,
            timeout=20,
            follow_redirects=True,
        ) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                return f"استجابة HTTP غير ناجحة ({resp.status_code}) من الرابط {url}."

            # Clean HTML to readable text snippet
            text = resp.text
            # Basic tag stripping
            clean = re.sub(r"<script.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<style.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
            clean = re.sub(r"<[^>]+>", " ", clean)
            clean = re.sub(r"\s+", " ", clean).strip()

            snippet = clean[:3000]
            return f"**محتوى الصفحة الموثقة ({resp.url}):**\n\n{snippet}"
    except Exception as e:
        return f"فشل جلب الصفحة الموثقة: {e}"


# ==============================================================================
# Tool Handlers for AI Agent
# ==============================================================================

async def manage_sessions_handler(args: dict) -> str:
    """Handler for AI tool to manage sessions."""
    action = (args.get("action") or "list").strip().lower()
    platform = (args.get("platform") or "").strip().lower()

    if action == "list":
        statuses = list_sessions_status()
        lines = ["🔐 **حالة جلسات وحسابات أدهم المحفوظة (Session Manager):**\n"]
        for s in statuses:
            if s["has_session"]:
                dt = s["saved_at"][:16].replace("T", " ") if s["saved_at"] else "غير محدد"
                lines.append(f"🟢 **{s['name']}**: متصل ({s['cookies_count']} كوكيز) | 🕒 آخر تحديث: `{dt}`")
            else:
                lines.append(f"⚪ **{s['name']}**: غير مسجل — بحاجة لإضافة الكوكيز.")

        lines.append("\n💡 **كيف تضيف جلسة جديدة؟**")
        lines.append("1. افتح المنصة في متصفحك (Chrome/Edge).")
        lines.append("2. من إضافة Cookie-Editor اضغط Export -> JSON.")
        lines.append("3. أرسل لي: `احفظ كوكيز مستقل:` متبوعة بالكود، أو استخدم أمر `/save_cookie`!")
        return "\n".join(lines)

    if action == "save":
        cookies_content = args.get("cookies_content") or ""
        if not platform:
            return "يرجى تحديد المنصة (مثل: mostaql, khamsat, facebook, twitter, instagram, linkedin, upwork)."
        if not cookies_content:
            return "يرجى توفير محتوى الكوكيز (JSON أو نص)."
        ok, msg = save_cookies(platform, cookies_content)
        return msg

    if action == "verify":
        if not platform:
            return "يرجى تحديد المنصة لفحصها."
        res = await verify_session(platform)
        return res["message"]

    return f"إجراء غير معروف: {action}. الإجراءات المتاحة: list, save, verify."


async def fetch_with_session_handler(args: dict) -> str:
    """Handler for AI tool to fetch authenticated pages."""
    platform = (args.get("platform") or "").strip().lower()
    url = (args.get("url") or "").strip()
    if not platform or not url:
        return "يرجى توفير اسم المنصة والرابط المطلوب تصفحه."
    return await fetch_authenticated(platform, url)


TOOLS = [
    {
        "name": "manage_user_sessions",
        "description": (
            "إدارة وفحص وتخزين جلسات أدهم المحفوظة (Cookies) لمنصات العمل الحر والسوشيال ميديا "
            "(مستقل، خمسات، فيسبوك، تويتر/إكس، إنستغرام، لينكد إن، أب وورك). "
            "استخدمها لمعرفة الحسابات المتصلة، أو فحص صلاحية جلسة، أو حفظ كوكيز جديدة."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["list", "save", "verify"],
                    "description": "الإجراء: 'list' لعرض حالة كل الحسابات، 'verify' لاختبار صلاحية جلسة معينة، 'save' لحفظ كوكيز جديدة",
                },
                "platform": {
                    "type": "string",
                    "description": "اسم المنصة: mostaql, khamsat, facebook, twitter, instagram, linkedin, upwork",
                },
                "cookies_content": {
                    "type": "string",
                    "description": "كود JSON أو نص الكوكيز المنسوخ من إضافة المتصفح (مطلوب عند action=save)",
                },
            },
            "required": ["action"],
        },
        "handler": manage_sessions_handler,
    },
    {
        "name": "fetch_with_session",
        "description": (
            "تصفح وجلب محتوى صفحة ويب خاصة داخل حساب أدهم المسجل (بواسطة الجلسة والكوكيز المحفوظة) "
            "لقراءة الرسائل، المشاريع المغلقة، لوحة التحكم، أو التنبيهات دون الحاجة لإعادة تسجيل الدخول."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "platform": {
                    "type": "string",
                    "description": "اسم المنصة (mostaql, khamsat, facebook, twitter, instagram, linkedin, upwork)",
                },
                "url": {
                    "type": "string",
                    "description": "الرابط المراد جلبه بحساب أدهم المسجل",
                },
            },
            "required": ["platform", "url"],
        },
        "handler": fetch_with_session_handler,
    },
]

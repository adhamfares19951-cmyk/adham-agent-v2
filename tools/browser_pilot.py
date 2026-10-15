"""Autonomous Browser Pilot for adham-agent.
Inspired by browser-use/browser-use.
Uses Playwright (or fallback HTTP scraper) to control a real browser, click elements,
fill forms, take full-page screenshots, and inspect web apps without opening a laptop.
Supports authenticated cookies from session_manager.
"""
from __future__ import annotations

import asyncio
import json
import logging
import re
import time
from pathlib import Path
from typing import Any

import httpx

log = logging.getLogger("browser_pilot")

BASE_DIR = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
SESSIONS_DIR = BASE_DIR / "sessions"


def _get_platform_cookies(url: str) -> dict[str, str]:
    """Finds matching platform cookies based on URL domain."""
    domain_map = {
        "facebook.com": "facebook",
        "mostaql.com": "mostaql",
        "khamsat.com": "khamsat",
        "linkedin.com": "linkedin",
        "x.com": "twitter",
        "twitter.com": "twitter",
        "instagram.com": "instagram",
        "upwork.com": "upwork",
    }
    for dom, plat in domain_map.items():
        if dom in url:
            cfile = SESSIONS_DIR / f"{plat}_cookies.json"
            if cfile.exists():
                try:
                    with open(cfile, "r", encoding="utf-8") as f:
                        return json.load(f).get("cookies", {})
                except Exception:
                    pass
    return {}


async def _navigate_playwright(
    url: str,
    actions: list[dict[str, Any]] | None = None,
    capture_screenshot: bool = True,
    wait_seconds: int = 3
) -> dict[str, Any]:
    """Navigates using Playwright async browser with optional cookies and actions."""
    from playwright.async_api import async_playwright

    cookies_dict = _get_platform_cookies(url)
    screenshot_path = None
    extracted_text = ""
    title = ""

    async with async_playwright() as p:
        # Launch headless browser using native system Edge or Chrome
        try:
            browser = await p.chromium.launch(
                channel="msedge",
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
        except Exception:
            try:
                browser = await p.chromium.launch(
                    channel="chrome",
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
            except Exception:
                browser = await p.chromium.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
                )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )

        # Inject cookies if available
        if cookies_dict:
            cookie_objects = []
            # Extract main domain
            domain_match = re.search(r"https?://(?:www\.)?([^/]+)", url)
            base_domain = domain_match.group(1) if domain_match else "localhost"
            for k, v in cookies_dict.items():
                cookie_objects.append({
                    "name": k,
                    "value": str(v),
                    "domain": f".{base_domain}" if not base_domain.startswith(".") else base_domain,
                    "path": "/",
                })
            try:
                await context.add_cookies(cookie_objects)
            except Exception as e:
                log.warning("Could not set cookies in Playwright context: %s", e)

        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            if wait_seconds > 0:
                await asyncio.sleep(wait_seconds)

            title = await page.title()

            # Execute sequential actions if provided
            if actions:
                for act in actions:
                    atype = act.get("action")
                    selector = act.get("selector")
                    val = act.get("value", "")

                    if atype == "click" and selector:
                        await page.click(selector, timeout=5000)
                    elif atype == "fill" and selector:
                        await page.fill(selector, val, timeout=5000)
                    elif atype == "press" and selector:
                        await page.press(selector, val or "Enter", timeout=5000)
                    elif atype == "scroll":
                        await page.evaluate("window.scrollBy(0, 500)")
                    await asyncio.sleep(1)

            # Capture screenshot
            if capture_screenshot:
                filename = f"shot_{int(time.time())}.png"
                target = SCREENSHOTS_DIR / filename
                await page.screenshot(path=str(target), full_page=False)
                screenshot_path = str(target)

            # Extract inner text snippet
            raw_text = await page.evaluate("document.body.innerText")
            clean = re.sub(r"\s+", " ", raw_text).strip()
            extracted_text = clean[:3000]

        finally:
            await browser.close()

    return {
        "success": True,
        "title": title,
        "url": url,
        "text": extracted_text,
        "screenshot": screenshot_path,
    }


async def _navigate_fallback_httpx(url: str, capture_screenshot: bool = True) -> dict[str, Any]:
    """Fallback navigator using HTTPX when Chromium is unavailable."""
    cookies_dict = _get_platform_cookies(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
    }
    async with httpx.AsyncClient(headers=headers, cookies=cookies_dict, timeout=20, follow_redirects=True) as client:
        resp = await client.get(url)
        html = resp.text

        title_m = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
        title = title_m.group(1).strip() if title_m else "بدون عنوان"

        # Basic text extraction
        clean = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<style.*?</style>", "", clean, flags=re.DOTALL | re.IGNORECASE)
        clean = re.sub(r"<[^>]+>", " ", clean)
        clean = re.sub(r"\s+", " ", clean).strip()

        return {
            "success": True,
            "title": title,
            "url": str(resp.url),
            "text": clean[:3000],
            "screenshot": None,
        }


async def browse_url(
    url: str,
    actions: list[dict[str, Any]] | None = None,
    capture_screenshot: bool = True,
    wait_seconds: int = 3
) -> dict[str, Any]:
    """Main browser function with automatic fallback."""
    try:
        return await _navigate_playwright(url, actions, capture_screenshot, wait_seconds)
    except Exception as e:
        log.warning("Playwright navigation failed (%s); falling back to HTTPX reader.", e)
        res = await _navigate_fallback_httpx(url, capture_screenshot)
        res["note"] = f"(تم استخدام المتصفح السريع؛ تعذر تشغيل محرك الرسوميات: {e})"
        return res


# ==============================================================================
# Tool Handlers for AI Agent
# ==============================================================================

async def browser_pilot_handler(args: dict) -> str:
    """Handler for autonomous browser navigation tool."""
    url = (args.get("url") or "").strip()
    if not url:
        return "يرجى تحديد الرابط المطلوب تصفحه (URL)."

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    actions = args.get("actions")
    wait_sec = int(args.get("wait_seconds", 3))

    res = await browse_url(url=url, actions=actions, capture_screenshot=True, wait_seconds=wait_sec)

    out = [
        f"🌐 **تقرير متصفح الويب الآلي (Browser Pilot):**",
        f"🔗 **الرابط:** {res['url']}",
        f"📄 **عنوان الصفحة:** `{res['title']}`\n",
    ]

    if res.get("screenshot"):
        out.append(f"📸 **تم التقاط سكرين شوت للصفحة وحفظه في:**\n`{res['screenshot']}`\n")

    if res.get("note"):
        out.append(f"⚠️ {res['note']}\n")

    out.append("📝 **مقتطف من محتوى الصفحة:**")
    out.append(f"```\n{res['text'][:1500]}\n```")

    return "\n".join(out)


TOOLS = [
    {
        "name": "browse_website_with_pilot",
        "description": (
            "تصفح أي موقع ويب بواسطة متصفح آلي كامل (Browser Pilot)، مع إمكانية التقاط صورة شاشة (Screenshot)، "
            "والنقر على الأزرار وتعبئة الحقول، وقراءة النصوص التفاعلية بالاعتماد على الجلسات المسجلة."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "رابط الموقع المراد فتحه وتصفحه"},
                "wait_seconds": {"type": "integer", "description": "ثواني الانتظار بعد تحميل الصفحة (افتراضي 3)"},
                "actions": {
                    "type": "array",
                    "description": "قائمة الإجراءات التفاعلية: [{\"action\": \"click\", \"selector\": \"button#submit\"}, {\"action\": \"fill\", \"selector\": \"input#email\", \"value\": \"...\"}]",
                },
            },
            "required": ["url"],
        },
        "handler": browser_pilot_handler,
    }
]

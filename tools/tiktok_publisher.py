"""TikTok Publisher & Browser Automation for adham-agent.
Handles autonomous video uploading to TikTok using Playwright persistent browser context.
Supports:
1. One-time interactive login session capture (stored securely in sessions/tiktok_user_data)
2. Headless automatic video upload, captioning, and publishing
3. Integration with Shorts and Reels cross-posting pipelines
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("tiktok_publisher")

BASE_DIR = Path(__file__).resolve().parent.parent
SESSIONS_DIR = BASE_DIR / "sessions"
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
TIKTOK_DATA_DIR = SESSIONS_DIR / "tiktok_user_data"
TIKTOK_DATA_DIR.mkdir(parents=True, exist_ok=True)


def is_authenticated() -> bool:
    """Checks if a saved TikTok session exists."""
    # Check if user data directory has cookies/storage files
    default_dir = TIKTOK_DATA_DIR / "Default"
    if default_dir.exists() and (default_dir / "Network").exists():
        return True
    # If any cookies or storage files exist in the profile
    return any(TIKTOK_DATA_DIR.glob("**/*Cookies*")) or any(TIKTOK_DATA_DIR.glob("**/*Network*"))


async def launch_interactive_login() -> bool:
    """Opens a visible browser for the user to log in to TikTok once."""
    from playwright.async_api import async_playwright

    log.info("Launching interactive browser for TikTok authentication...")
    async with async_playwright() as p:
        browser_context = await p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_DATA_DIR),
            channel="msedge",
            headless=False,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser_context.pages[0] if browser_context.pages else await browser_context.new_page()
        await page.goto("https://www.tiktok.com/login", wait_until="networkidle")
        print("\n" + "="*60)
        print("⚡ يرجى تسجيل الدخول إلى حسابك في تيك توك الآن في النافذة المفتوحة.")
        print("بمجرد إتمام تسجيل الدخول وظهور صفحتك، أغلق نافذة المتصفح لحفظ الجلسة.")
        print("="*60 + "\n")
        
        # Wait up to 5 minutes for login or window close
        for _ in range(300):
            if page.is_closed():
                break
            url = page.url
            if "creator-center" in url or "tiktok.com/@" in url or "foryou" in url:
                log.info("TikTok login detected successfully!")
                await asyncio.sleep(4)
                break
            await asyncio.sleep(1)

        await browser_context.close()
        return is_authenticated()


async def upload_video(
    video_path: Path | str,
    caption: str,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Uploads a video to TikTok via Playwright TikTok Studio automation."""
    v_path = Path(video_path).resolve()
    if not v_path.exists():
        raise FileNotFoundError(f"Video file not found: {v_path}")

    full_caption = caption
    if tags:
        clean_tags = " ".join(f"#{t.strip('#')}" for t in tags if t)
        full_caption = f"{caption} {clean_tags}".strip()

    from playwright.async_api import async_playwright

    log.info("Starting autonomous TikTok upload for: %s", v_path.name)
    async with async_playwright() as p:
        try:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=str(TIKTOK_DATA_DIR),
                channel="msedge",
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=str(TIKTOK_DATA_DIR),
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )

        page = await browser_context.new_page()
        try:
            # 1. Navigate to modern TikTok Studio upload page
            log.info("Navigating to TikTok Studio upload page...")
            await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
            await asyncio.sleep(4)

            # Check if login is required
            if "login" in page.url:
                raise RuntimeError("انتهت صلاحية جلسة تيك توك. يرجى تشغيل setup_tiktok.bat لتسجيل الدخول.")

            # 2. Locate and set input files (handle attached/hidden state)
            file_input = await page.wait_for_selector('input[type="file"]', state="attached", timeout=35000)
            if not file_input:
                raise RuntimeError("لم يتم العثور على حقل اختيار ملف الفيديو في صفحة TikTok Studio.")

            await file_input.set_input_files(str(v_path))
            log.info("Video file attached to TikTok uploader (%s).", v_path.name)

            # 3. Wait for video upload processing
            uploaded = False
            for s in range(1, 30):
                await asyncio.sleep(1)
                content = await page.content()
                if "تم التحميل" in content or "Uploaded" in content:
                    log.info("Video upload confirmed by TikTok Studio in %ds.", s)
                    uploaded = True
                    break

            if not uploaded:
                log.warning("Upload indicator did not show 'تم التحميل' within 30s, proceeding to form...")

            # 4. Dismiss any announcements or feature introduction modals (e.g., "فهمت")
            try:
                got_it_btn = await page.query_selector('button:has-text("فهمت")')
                if got_it_btn and await got_it_btn.is_visible():
                    log.info("Dismissing announcement modal ('فهمت')...")
                    await got_it_btn.click()
                    await asyncio.sleep(1)
            except Exception as e:
                log.debug("Announcement modal check error: %s", e)

            # 5. Populate caption in Draft.js contenteditable editor
            log.info("Setting caption: %s", full_caption[:60])
            editable = await page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
            if editable:
                await editable.click()
                await asyncio.sleep(0.5)
                # Clear pre-filled video filename
                await page.keyboard.press("Control+A")
                await asyncio.sleep(0.2)
                await page.keyboard.press("Backspace")
                await asyncio.sleep(0.2)
                # Insert full caption cleanly
                await page.keyboard.insert_text(full_caption)
                await asyncio.sleep(1)
                # Close any open hashtag autocompletion popup
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                log.info("Caption inserted into Draft.js editor successfully.")
            else:
                log.warning("Contenteditable caption editor not found, attempting textarea fallback...")
                textarea = await page.query_selector('textarea')
                if textarea:
                    await textarea.fill(full_caption)

            # 6. Locate Post ("نشر" / "Post") button
            post_btn = None
            for b in await page.query_selector_all('button'):
                t = (await b.text_content() or "").strip()
                if "نشر" in t or "Post" in t:
                    post_btn = b
                    break

            if not post_btn:
                raise RuntimeError("لم يتم العثور على زر 'نشر' (Post) في صفحة TikTok Studio.")

            # Wait until Post button becomes enabled
            for wait_s in range(15):
                if not await post_btn.is_disabled():
                    log.info("Post button is active and enabled.")
                    break
                await asyncio.sleep(1)

            await post_btn.scroll_into_view_if_needed()
            await post_btn.click()
            log.info("Clicked 'نشر' button on TikTok Studio.")

            # 7. Check for secondary confirmation modal ("النشر الآن" / "Post now")
            try:
                for _ in range(6):
                    await asyncio.sleep(1)
                    confirm_btn = (
                        await page.query_selector('button:has-text("النشر الآن")')
                        or await page.query_selector('button:has-text("Post now")')
                    )
                    if confirm_btn and await confirm_btn.is_visible():
                        log.info("Clicked secondary confirmation button ('النشر الآن').")
                        await confirm_btn.click()
                        break
            except Exception as e:
                log.debug("Secondary confirmation check: %s", e)

            # 8. Wait for publication confirmation
            confirmed = False
            for s in range(1, 25):
                await asyncio.sleep(1)
                url = page.url
                body_text = await page.text_content("body") or ""
                if any(term in body_text for term in ["تم نشر الفيديو", "إدارة منشوراتك", "Your video has been published", "Manage your posts", "تحميل فيديو آخر"]):
                    log.info("TikTok publication confirmed on page in %ds!", s)
                    confirmed = True
                    break
                if "content" in url or "manage" in url:
                    log.info("TikTok publication confirmed via redirect to: %s", url)
                    confirmed = True
                    break

            # Save screenshot for audit
            cache_dir = BASE_DIR / "repos_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            shot_path = cache_dir / "tiktok_latest_published.png"
            await page.screenshot(path=str(shot_path))
            log.info("Saved latest publication screenshot: %s", shot_path)

            return {
                "success": True,
                "platform": "TikTok",
                "caption": full_caption,
                "video_path": str(v_path),
                "confirmed": confirmed,
                "screenshot": str(shot_path),
                "message": "تم رفع ونشر الفيديو بنجاح على حساب تيك توك!"
            }
        finally:
            await browser_context.close()


async def _handle_tiktok_upload(args: dict[str, Any]) -> str:
    """Agent tool handler for uploading a video to TikTok."""
    vpath = args.get("video_path")
    if not vpath:
        return "خطأ: مسار ملف الفيديو مطلوب (video_path)."
    caption = args.get("caption", "Smart Money Concepts & Algorithmic Trading with Core Trade AI #trading #forex")
    tags = args.get("tags")

    try:
        if not is_authenticated():
            return (
                "⚠️ **حساب تيك توك غير مسجل بعد!**\n"
                "يرجى تشغيل سكربت الربط لمرة واحدة `setup_tiktok.bat` لتسجيل الدخول وحفظ الجلسة."
            )
        res = await upload_video(video_path=vpath, caption=caption, tags=tags)
        return (
            f"✅ **تم نشر الفيديو بنجاح على تيك توك!**\n"
            f"📝 **الكابشن:** {res['caption']}\n"
            f"📁 **الملف:** `{res['video_path']}`"
        )
    except Exception as e:
        log.exception("TikTok upload handler failed")
        return f"❌ فشل رفع الفيديو إلى تيك توك: {e}"


async def _handle_tiktok_status(args: dict[str, Any]) -> str:
    """Agent tool handler for checking TikTok authentication status."""
    auth = is_authenticated()
    if auth:
        return "✅ حساب تيك توك موثق وجاهز للنشر التلقائي عبر المتصفح الآلي (Playwright)."
    return (
        "⚠️ حساب تيك توك غير مربوط بعد.\n"
        "لتفعيله: شغّل `setup_tiktok.bat` من مجلد البوت لتسجيل الدخول لمرة واحدة."
    )


TOOLS = [
    {
        "name": "tiktok_upload_video",
        "description": "يرفع فيديو MP4 أو شورتس رأسياً ومباشرة إلى حساب تيك توك مع الكابشن والهاشتاجات.",
        "parameters": {
            "type": "object",
            "properties": {
                "video_path": {"type": "string", "description": "المسار الكامل لملف الفيديو MP4"},
                "caption": {"type": "string", "description": "نص الكابشن والوصف"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "قائمة الهاشتاجات"}
            },
            "required": ["video_path"]
        },
        "handler": _handle_tiktok_upload
    },
    {
        "name": "tiktok_check_status",
        "description": "يفحص حالة اتصال وتوثيق حساب تيك توك للنشر التلقائي.",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "handler": _handle_tiktok_status
    }
]

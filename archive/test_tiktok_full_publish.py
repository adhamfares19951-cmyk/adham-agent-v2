"""Full autonomous TikTok publishing test."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sessions" / "tiktok_user_data"
CACHE_DIR = BASE_DIR / "repos_cache"
VIDEO_PATH = BASE_DIR / "videos" / "subtitled_video_1792314383_1792314415.mp4"

async def test_full_publish():
    caption = "Why Banks Hunt Your Stop Loss: SMC Liquidity Strategy Explained #trading #crypto #forex #smc #stocks"
    print("=== Testing Complete Autonomous TikTok Publish Flow ===")
    
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(DATA_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await ctx.new_page()
        print("1. Navigating to https://www.tiktok.com/tiktokstudio/upload ...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)

        print("2. Attaching video file...")
        file_input = await page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
        await file_input.set_input_files(str(VIDEO_PATH))

        print("3. Waiting for upload processing...")
        # Poll until upload completes (green checkmark or "تم التحميل" or 12 seconds)
        for s in range(1, 13):
            await asyncio.sleep(1)
            content = await page.content()
            if "تم التحميل" in content or "Uploaded" in content:
                print(f"Video uploaded after {s} seconds!")
                break

        # 4. Dismiss modal if present
        try:
            got_it_btn = await page.query_selector('button:has-text("فهمت")')
            if got_it_btn and await got_it_btn.is_visible():
                print("Dismissing 'فهمت' announcement modal...")
                await got_it_btn.click()
                await asyncio.sleep(1)
        except Exception as e:
            print(f"Announcement modal not needed: {e}")

        # 5. Fill caption
        print(f"5. Writing caption: {caption}")
        editable = await page.wait_for_selector('div[contenteditable="true"]', timeout=10000)
        if editable:
            await editable.click()
            await asyncio.sleep(0.5)
            await page.keyboard.press("Control+A")
            await asyncio.sleep(0.2)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.2)
            await page.keyboard.insert_text(caption)
            await asyncio.sleep(1)
            # Press Escape to close any open hashtag popup
            await page.keyboard.press("Escape")
            await asyncio.sleep(0.5)
            print("Caption successfully set!")

        # 6. Locate Post ("نشر") button
        print("6. Locating 'نشر' button...")
        post_btn = None
        for b in await page.query_selector_all('button'):
            t = (await b.text_content() or "").strip()
            if "نشر" in t or "Post" in t:
                post_btn = b
                break

        if not post_btn:
            raise RuntimeError("Post button not found on page!")

        # Ensure button is not disabled
        for wait_s in range(10):
            if not await post_btn.is_disabled():
                print(f"Post button enabled (waited {wait_s}s). Clicking now!")
                break
            await asyncio.sleep(1)

        await post_btn.scroll_into_view_if_needed()
        await post_btn.click()
        print("Clicked 'نشر' button! Checking for confirmation modal ('النشر الآن')...")

        # Check if "النشر الآن" (Post now) popup appeared because content check was still pending
        try:
            for _ in range(5):
                await asyncio.sleep(1)
                confirm_post_btn = await page.query_selector('button:has-text("النشر الآن")') or await page.query_selector('button:has-text("Post now")')
                if confirm_post_btn and await confirm_post_btn.is_visible():
                    print("Found 'النشر الآن' (Post now) confirmation button, clicking!")
                    await confirm_post_btn.click()
                    break
        except Exception as e:
            print(f"Post confirmation modal check: {e}")

        # Wait for redirect or confirmation modal (up to 25 seconds)
        confirmed = False
        for s in range(1, 21):
            await asyncio.sleep(1)
            url = page.url
            body_text = await page.text_content("body") or ""
            if any(term in body_text for term in ["تم نشر الفيديو", "إدارة منشوراتك", "Your video has been published", "Manage your posts", "تحميل فيديو آخر"]):
                print(f"Publish SUCCESS confirmed on page in {s}s! Text match found.")
                confirmed = True
                break
            if "content" in url or "manage" in url:
                print(f"Publish SUCCESS confirmed via redirect to: {url}")
                confirmed = True
                break

        await page.screenshot(path=str(CACHE_DIR / "tiktok_published_success.png"))
        print("Saved confirmation screenshot: repos_cache/tiktok_published_success.png")

        if confirmed:
            print("=== TIKTOK AUTONOMOUS PUBLISH SUCCEEDED 100% ===")
        else:
            print("Publish state inconclusive, review screenshot.")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(test_full_publish())

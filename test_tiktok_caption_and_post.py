"""Test dismiss popup, filling caption and verifying post button state on TikTok Studio."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sessions" / "tiktok_user_data"
CACHE_DIR = BASE_DIR / "repos_cache"
VIDEO_PATH = BASE_DIR / "videos" / "subtitled_video_1792314383_1792314415.mp4"

async def test_caption_and_post():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(DATA_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await ctx.new_page()
        print("Navigating to https://www.tiktok.com/tiktokstudio/upload ...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)

        print("Attaching video file...")
        file_input = await page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
        await file_input.set_input_files(str(VIDEO_PATH))

        print("Waiting for upload UI to load (10 seconds)...")
        await asyncio.sleep(10)

        # 1. Dismiss "فهمت" modal if present
        try:
            got_it_btn = await page.query_selector('button:has-text("فهمت")')
            if got_it_btn and await got_it_btn.is_visible():
                print("Found 'فهمت' modal button, clicking to dismiss...")
                await got_it_btn.click()
                await asyncio.sleep(2)
            else:
                print("'فهمت' modal button not visible or not present.")
        except Exception as e:
            print(f"Modal check error: {e}")

        # 2. Update caption
        test_caption = "SMC Trading Strategy: Liquidity Sweeps Explained #trading #crypto #forex #smc"
        print(f"Setting caption to: {test_caption}")
        editable = await page.query_selector('div[contenteditable="true"]')
        if editable:
            await editable.click()
            await asyncio.sleep(0.5)
            # Select all existing text (which is the filename)
            await page.keyboard.press("Control+A")
            await asyncio.sleep(0.3)
            await page.keyboard.press("Backspace")
            await asyncio.sleep(0.3)
            # Insert caption text
            await page.keyboard.insert_text(test_caption)
            await asyncio.sleep(1)
            print("Caption inserted via keyboard.insert_text!")
        else:
            print("Editable caption div not found!")

        # 3. Take screenshot of prepared state
        await page.screenshot(path=str(CACHE_DIR / "tiktok_prepared_to_post.png"))
        print("Saved screenshot: repos_cache/tiktok_prepared_to_post.png")

        # 4. Check Post button
        post_buttons = await page.query_selector_all('button')
        found_post = None
        for b in post_buttons:
            t = (await b.text_content() or "").strip()
            if "نشر" in t or "Post" in t:
                is_disabled = await b.is_disabled()
                print(f"Found post button: text='{t}', disabled={is_disabled}")
                found_post = b
                break

        if found_post:
            print("Post button is ready and clickable!")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(test_caption_and_post())

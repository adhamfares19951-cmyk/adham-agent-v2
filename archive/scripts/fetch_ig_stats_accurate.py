import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA_DIR = r"C:\Projects\adham-agent\sessions\instagram_user_data"
BRAIN_DIR = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf"
SCREENSHOT_PROFILE = os.path.join(BRAIN_DIR, "ig_profile_live_views.png")
SCREENSHOT_REELS = os.path.join(BRAIN_DIR, "ig_reels_live_views.png")

async def check():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1366, "height": 850},
            locale="ar-SA",
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening IG profile @smartstore.gcc...")
        await page.goto("https://www.instagram.com/smartstore.gcc/", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=SCREENSHOT_PROFILE, full_page=False)
        print("IG profile captured.")

        print("Opening IG Reels tab...")
        await page.goto("https://www.instagram.com/smartstore.gcc/reels/", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=SCREENSHOT_REELS, full_page=False)
        print("IG Reels captured.")

        await context.close()

if __name__ == "__main__":
    asyncio.run(check())

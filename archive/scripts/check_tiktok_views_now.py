import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA_DIR = os.path.abspath("sessions/tiktok_user_data")
SCREENSHOT_PROFILE = os.path.abspath("repos_cache/tiktok_profile_now.png")
SCREENSHOT_STUDIO = os.path.abspath("repos_cache/tiktok_studio_now.png")

async def check_tiktok():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1280, "height": 800},
            locale="ar-SA",
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to TikTok Studio Content...")
        try:
            await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(5000)
            await page.screenshot(path=SCREENSHOT_STUDIO)
            print("Studio screenshot saved.")
            
            # Extract video rows or text
            content_text = await page.evaluate("""() => {
                const rows = document.querySelectorAll('div[data-e2e="content-item"], tr, .tiktok-table-row, div[class*="content-item"]');
                return Array.from(rows).map(r => r.innerText).join('\\n---ROW---\\n');
            }""")
            print("Studio Content Sample:")
            print(content_text[:1500])
        except Exception as e:
            print("Studio error:", e)

        print("\nNavigating to public profile @coretradeai...")
        try:
            await page.goto("https://www.tiktok.com/@coretradeai", wait_until="domcontentloaded", timeout=35000)
            await page.wait_for_timeout(4000)
            await page.screenshot(path=SCREENSHOT_PROFILE)
            print("Profile screenshot saved.")
            
            profile_stats = await page.evaluate("""() => {
                const stats = document.querySelector('[data-e2e="user-info"]') || document.body;
                const videos = document.querySelectorAll('[data-e2e="user-post-item"], div[class*="DivItemContainer"]');
                const vList = Array.from(videos).map(v => v.innerText);
                return { text: stats.innerText.slice(0, 500), videos: vList };
            }""")
            print("Profile Stats:", profile_stats)
        except Exception as e:
            print("Profile error:", e)

        await context.close()

if __name__ == "__main__":
    asyncio.run(check_tiktok())

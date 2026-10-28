import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA_DIR = os.path.abspath("sessions/instagram_user_data")
SCREENSHOT_PROFILE = os.path.abspath("repos_cache/ig_profile_now.png")
SCREENSHOT_REELS = os.path.abspath("repos_cache/ig_reels_now.png")

async def check_instagram():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1280, "height": 800},
            locale="ar-SA",
        )
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("Navigating to Instagram profile @smartstore.gcc...")
        try:
            await page.goto("https://www.instagram.com/smartstore.gcc/", wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(4000)
            await page.screenshot(path=SCREENSHOT_PROFILE)
            print("IG Profile screenshot saved.")
            
            profile_info = await page.evaluate("""() => {
                const header = document.querySelector('header') || document.body;
                return header.innerText;
            }""")
            print("IG Header Info:")
            print(profile_info[:600])
        except Exception as e:
            print("IG profile error:", e)

        print("\nNavigating to Instagram Reels tab...")
        try:
            await page.goto("https://www.instagram.com/smartstore.gcc/reels/", wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(4000)
            await page.screenshot(path=SCREENSHOT_REELS)
            print("IG Reels screenshot saved.")
            
            reels_text = await page.evaluate("""() => {
                const main = document.querySelector('main') || document.body;
                return main.innerText;
            }""")
            print("IG Reels text:")
            print(reels_text[:1000])
        except Exception as e:
            print("IG reels error:", e)

        await context.close()

if __name__ == "__main__":
    asyncio.run(check_instagram())

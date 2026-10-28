import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, r"C:\Projects\adham-agent")
from tools.tiktok_publisher import TIKTOK_DATA_DIR, REPOS_CACHE

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_DATA_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()
        print("1. Going to TikTok Studio Content with domcontentloaded...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(5000)
        
        shot = REPOS_CACHE / "tiktok_content_live.png"
        await page.screenshot(path=str(shot))
        print(f"2. Screenshot saved: {shot}")

        # Let's inspect the page title and url
        print("Current URL:", page.url)
        print("Page Title:", await page.title())

        # Check for videos on page
        texts = await page.locator("div[class*='info'], div[class*='title'], span[class*='title']").all_text_contents()
        print("Video texts found:", len(texts))
        for t in texts[:5]:
            print("Video Title text:", t.strip())

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

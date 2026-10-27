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
        print("Navigating to TikTok Studio Content page...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(5000)
        shot = REPOS_CACHE / "tiktok_manage_content.png"
        await page.screenshot(path=str(shot))
        print(f"Content screenshot saved to {shot}")

        # Look for the action buttons (three dots / more options / delete) on the latest video
        more_btns = page.locator("button:has-text('المزيد'), [data-e2e*='more'], svg[class*='more'], div[class*='action'] button, button:has-text('حذف')")
        count = await more_btns.count()
        print("Found more/action buttons:", count)

        # Let's see video list
        videos = await page.locator("div[class*='video-item'], div[class*='table-row'], div[data-e2e*='video-item']").all_text_contents()
        print("Found videos count:", len(videos))
        for i, v in enumerate(videos[:3]):
            print(f"Video #{i+1}:", v.strip().replace("\n", " | ")[:120])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

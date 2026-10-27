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
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        # Click the three dots icon at x=73, y=311
        print("Clicking at x=73, y=311...")
        await page.mouse.click(73, 311)
        await page.wait_for_timeout(2000)
        
        shot1 = REPOS_CACHE / "after_coord_click.png"
        await page.screenshot(path=str(shot1))
        print(f"Saved {shot1}")

        # Check if popup menu appeared
        del_item = page.locator("div:has-text('حذف'), span:has-text('حذف'), li:has-text('حذف')").last
        if await del_item.is_visible():
            print("Found delete item in popup! Clicking...")
            await del_item.click()
            await page.wait_for_timeout(1500)
            
            shot2 = REPOS_CACHE / "confirm_dialog.png"
            await page.screenshot(path=str(shot2))
            print(f"Saved {shot2}")

            # Confirm button
            confirm = page.locator("button:has-text('حذف')").last
            if await confirm.is_visible():
                print("Confirming deletion...")
                await confirm.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(REPOS_CACHE / "deleted_done.png"))
                print("DELETED SUCCESSFULLY!")
        else:
            print("Delete popup not detected, inspect after_coord_click.png")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

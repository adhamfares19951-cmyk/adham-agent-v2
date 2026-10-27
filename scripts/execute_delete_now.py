import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")
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

        print("1. Clicking the popover container at x=94, y=249...")
        await page.mouse.click(94, 249)
        await page.wait_for_timeout(1500)

        print("2. Clicking 'حذف'...")
        del_item = page.locator("span:has-text('حذف'), div:has-text('حذف')").last
        await del_item.click()
        await page.wait_for_timeout(1500)
        
        await page.screenshot(path=str(REPOS_CACHE / "delete_confirm_modal.png"))
        print("3. Delete confirmation modal opened. Looking for confirm button...")
        
        # In the confirmation modal, find the red/confirm delete button
        confirm_btn = page.locator("div[role='dialog'] button:has-text('حذف'), button:has-text('حذف')").last
        await confirm_btn.click()
        print("4. Clicked confirm delete! Waiting 4 seconds...")
        await page.wait_for_timeout(4000)

        proof = REPOS_CACHE / "trading_video_deleted_proof.png"
        await page.screenshot(path=str(proof))
        print(f"5. Final proof saved to {proof}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

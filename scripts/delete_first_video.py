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
        print("1. Opening TikTok Studio Content...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(4000)

        # Find the first row's more button (three dots)
        # Look at the screenshot: the leftmost icon in the action column is three dots `...`
        print("2. Locating three dots button...")
        dots = page.locator("button:has-text('...'), div[class*='operation'] button, div[class*='action'] button, span:has-text('...')")
        all_dots = await dots.all()
        print(f"Found {len(all_dots)} candidate buttons.")

        # Alternatively click by position or svg
        # In the top row, the buttons are located on the left side:
        # Let's find all buttons or icons with svg
        more_icon = page.locator("button svg, div[class*='more'], button[aria-label*='more'], button[aria-label*='المزيد']")
        count = await more_icon.count()
        print(f"More icons found: {count}")

        # Let's click the first three dots button
        # On the screenshot: top row has 4 action icons: [ ... ] [ chat ] [ share ] [ edit ]
        # The leftmost is three dots `...`
        btn = page.locator("button:has-text('...'), div:has-text('...')").first
        if await btn.is_visible():
            print("Clicking first '...' button...")
            await btn.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(REPOS_CACHE / "after_dots_click.png"))
        else:
            # Let's click by selector on the first row
            row = page.locator("div[class*='table-row'], tr").first
            # or click first button inside row
            first_btn = page.locator("button").filter(has_text="...").first
            if await first_btn.is_visible():
                await first_btn.click()
            else:
                # Find all buttons in the first row
                btns = await page.locator("div[class*='table'] button, div[class*='operation'] button, div[class*='action'] button").all()
                print("Total operation buttons:", len(btns))
                if btns:
                    await btns[0].click()
                    await page.wait_for_timeout(1500)
                    await page.screenshot(path=str(REPOS_CACHE / "after_dots_click.png"))

        # Look for Delete / حذف option
        del_btn = page.locator("div:has-text('حذف'), button:has-text('حذف'), li:has-text('حذف'), div:has-text('Delete'), button:has-text('Delete')").first
        if await del_btn.is_visible():
            print("Found delete option! Clicking...")
            await del_btn.click()
            await page.wait_for_timeout(1500)
            await page.screenshot(path=str(REPOS_CACHE / "after_delete_click.png"))
            
            # Confirm modal
            confirm_btn = page.locator("button:has-text('حذف'), button:has-text('تأكيد'), button:has-text('Delete'), button:has-text('Confirm')").last
            if await confirm_btn.is_visible():
                print("Confirming deletion...")
                await confirm_btn.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path=str(REPOS_CACHE / "after_confirm_delete.png"))
                print("Deleted successfully!")
        else:
            print("Delete option not immediately found. Saved after_dots_click.png for inspection.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

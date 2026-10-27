import asyncio
import sys
import pprint
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

        # Get all interactive buttons/elements in the action cells
        action_elements = await page.evaluate("""() => {
            const firstRow = document.querySelector('[data-tt*="ActionCell"]');
            if (!firstRow) return [];
            return Array.from(firstRow.children).map((c, i) => {
                const rect = c.getBoundingClientRect();
                return {
                    idx: i,
                    html: c.outerHTML.slice(0, 150),
                    x: rect.x + rect.width / 2,
                    y: rect.y + rect.height / 2
                };
            });
        }""")
        print("Action elements in first row:")
        pprint.pprint(action_elements)

        if action_elements:
            # Click the last or first item that represents three dots
            # In RTL (Arabic UI), leftmost element is usually the first or last depending on flex direction
            # Let's find which one is around x=70
            target_el = min(action_elements, key=lambda e: e['x'])
            print(f"Targeting leftmost element at ({target_el['x']}, {target_el['y']})...")
            await page.mouse.click(target_el['x'], target_el['y'])
            await page.wait_for_timeout(2000)
            await page.screenshot(path=str(REPOS_CACHE / "after_target_click.png"))
            
            # Check for menu items
            menu_items = await page.evaluate("""() => {
                return Array.from(document.querySelectorAll('div, li, button, span'))
                    .filter(el => el.innerText && el.innerText.trim().length > 0 && el.innerText.trim().length < 30)
                    .map(el => el.innerText.trim());
            }""")
            print("Visible menu items containing 'حذف' or 'Delete':")
            matching = [m for m in set(menu_items) if any(w in m for w in ["حذف", "Delete", "إزالة"])]
            print(matching)

            if matching:
                print("Clicking delete option...")
                del_btn = page.locator(f"text='{matching[0]}'").first
                await del_btn.click()
                await page.wait_for_timeout(2000)
                await page.screenshot(path=str(REPOS_CACHE / "delete_modal.png"))

                # Click confirmation button
                conf = page.locator("button:has-text('حذف'), button:has-text('Delete')").last
                if await conf.is_visible():
                    print("Confirming video deletion...")
                    await conf.click()
                    await page.wait_for_timeout(4000)
                    await page.screenshot(path=str(REPOS_CACHE / "deleted_final_proof.png"))
                    print("DELETION COMPLETE!")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

# -*- coding: utf-8 -*-
"""Updates TikTok profile bio with the new link."""
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path("sessions/tiktok_user_data").resolve()
new_url_short = "ministries-direct-specify-universe.trycloudflare.com/glamp"

async def update_tt_bio():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 800},
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("1. Opening TikTok Profile...")
        await page.goto("https://www.tiktok.com/@coretradeai", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        # Look for Edit profile button
        edit_btn = page.locator('button:has-text("تعديل الملف الشخصي"), button:has-text("Edit profile"), div[role="button"]:has-text("تعديل")').first
        if await edit_btn.count() > 0:
            print("Found Edit Profile button. Clicking...")
            await edit_btn.click()
            await asyncio.sleep(3)
            await page.screenshot(path="repos_cache/tiktok_edit_modal.png")

            # Look for bio textarea
            bio_input = page.locator('textarea[placeholder*="سيرة"], textarea[placeholder*="Bio"], textarea').first
            if await bio_input.count() > 0:
                print("Updating Bio...")
                await bio_input.fill(f"⚡ مصباح G-Lamp 4in1 شاحن وسبيكر\n🚚 الدفع عند الاستلام:\n{new_url_short}")
                await asyncio.sleep(1)

                save_btn = page.locator('button:has-text("حفظ"), button:has-text("Save")').first
                if await save_btn.count() > 0:
                    print("Clicking Save...")
                    await save_btn.click()
                    await asyncio.sleep(3)
                    print("Saved TikTok bio successfully!")
            else:
                print("Bio input not found in modal.")
        else:
            print("Edit profile button not found.")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(update_tt_bio())

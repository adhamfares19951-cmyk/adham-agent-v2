# -*- coding: utf-8 -*-
"""Updates Instagram bio link to the new live Cloudflare tunnel URL."""
import sys
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

new_tunnel_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"

async def main():
    cookie_path = Path("sessions/instagram_cookies.json")
    raw_cookies = json.loads(cookie_path.read_text(encoding="utf-8"))
    playwright_cookies = []
    for c in raw_cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
            "httpOnly": c.get("httpOnly", False),
            "secure": c.get("secure", False),
        }
        if "expirationDate" in c and c["expirationDate"]:
            cookie["expires"] = float(c["expirationDate"])
        playwright_cookies.append(cookie)

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()

        print("1. Opening Instagram Edit Profile...")
        await page.goto("https://www.instagram.com/accounts/edit/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)

        await page.screenshot(path="repos_cache/ig_edit_profile_before.png")

        # In Instagram Web, bio is a textarea
        bio_elem = page.locator('textarea[id*="pepBio"], textarea').first
        if await bio_elem.count() > 0:
            current_bio = await bio_elem.input_value()
            print("Current Bio:\n", current_bio)

            # Update bio text to include the new link or clear reference
            new_bio = (
                "🌟 وجهتك لأحدث المنتجات الذكية بالخليج\n"
                "⚡ مصباح G-Lamp 4in1 (شاحن 15W وسبيكر)\n"
                "🚚 شحن مجاني + الدفع عند الاستلام 🇸🇦 🇦🇪\n"
                f"👇 اطلب الآن:\n{new_tunnel_url}"
            )

            await bio_elem.fill(new_bio)
            await asyncio.sleep(1)

            # Find Submit button
            submit_btn = page.locator('div[role="button"]:has-text("Submit"), button:has-text("Submit"), div[role="button"]:has-text("إرسال"), button:has-text("إرسال")')
            if await submit_btn.count() > 0:
                print("Clicking Submit...")
                await submit_btn.first.click()
                await asyncio.sleep(4)
                await page.screenshot(path="repos_cache/ig_edit_profile_after.png")
                print("Saved after screenshot to repos_cache/ig_edit_profile_after.png")
            else:
                print("Submit button not found!")
        else:
            print("Bio element not found!")

        # Verify on public profile
        print("2. Verifying on public profile...")
        await page.goto("https://www.instagram.com/smartstore.gcc/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(4)
        await page.screenshot(path="repos_cache/ig_profile_verified.png")

        body_text = await page.inner_text("body")
        for line in body_text.splitlines()[:25]:
            if "trycloudflare" in line or "smartstore" in line or "مصباح" in line:
                print("Profile line:", line.strip())

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

async def main():
    cookie_file = Path(r"C:\Projects\adham-agent\sessions\instagram_cookies.json")
    if not cookie_file.exists():
        print("Error: instagram_cookies.json not found")
        return

    raw_cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
    p_cookies = []
    for c in raw_cookies:
        cookie = {
            "name": c["name"],
            "value": c["value"],
            "domain": c["domain"],
            "path": c.get("path", "/"),
        }
        if c.get("secure") is not None:
            cookie["secure"] = bool(c["secure"])
        if c.get("httpOnly") is not None:
            cookie["httpOnly"] = bool(c["httpOnly"])
        ss = str(c.get("sameSite", "")).lower()
        if "strict" in ss:
            cookie["sameSite"] = "Strict"
        elif "lax" in ss:
            cookie["sameSite"] = "Lax"
        elif "no_restriction" in ss or "none" in ss:
            cookie["sameSite"] = "None"
        p_cookies.append(cookie)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 900})
        await context.add_cookies(p_cookies)
        page = await context.new_page()

        print("1. Navigating to Instagram profile (@smartstore.gcc)...")
        await page.goto("https://www.instagram.com/smartstore.gcc/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(4000)

        shot1 = r"C:\Projects\adham-agent\repos_cache\ig_profile_views.png"
        await page.screenshot(path=shot1)
        print(f"Profile screenshot saved to {shot1}")

        # Check reels tab or reel view count
        print("2. Checking Reel page (/reel/De_nMgAs1F1/)...")
        await page.goto("https://www.instagram.com/reel/De_nMgAs1F1/", wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(4000)

        shot2 = r"C:\Projects\adham-agent\repos_cache\ig_reel_views.png"
        await page.screenshot(path=shot2)
        print(f"Reel screenshot saved to {shot2}")

        # Extract text around likes/views
        texts = await page.locator("section, span[class*='html-span'], div[class*='x1lliihq']").all_text_contents()
        relevant = [t.strip() for t in texts if any(w in t.lower() for w in ["like", "view", "مشاهد", "إعجاب", "plays"])]
        print("Reel view/like snippets:", relevant[:5])

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

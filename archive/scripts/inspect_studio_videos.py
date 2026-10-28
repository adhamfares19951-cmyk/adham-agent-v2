import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.path.insert(0, r"C:\Projects\adham-agent")

async def main():
    cookie_file = Path(r"C:\Projects\adham-agent\sessions\tiktok_cookies.json")
    cookies = json.loads(cookie_file.read_text(encoding="utf-8"))
    p_cookies = []
    for c in cookies:
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
        context = await browser.new_context()
        await context.add_cookies(p_cookies)
        page = await context.new_page()
        print("Navigating to TikTok Studio Content...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="networkidle", timeout=60000)
        await page.wait_for_timeout(6000)
        shot_path = r"C:\Projects\adham-agent\repos_cache\tiktok_studio_videos.png"
        await page.screenshot(path=shot_path)
        print(f"Screenshot saved to {shot_path}")

        # List video titles / items if available
        rows = await page.locator("div[class*='table-row'], div[class*='item-card'], div[data-e2e*='video']").all_text_contents()
        print("Video elements found:", len(rows))
        for r in rows[:5]:
            print("--- ROW ---", r.strip().replace("\n", " | ")[:120])
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

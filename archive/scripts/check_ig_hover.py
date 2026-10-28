import asyncio
import json
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding="utf-8")

async def main():
    cookie_file = Path(r"C:\Projects\adham-agent\sessions\instagram_cookies.json")
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
        await page.goto("https://www.instagram.com/smartstore.gcc/", wait_until="networkidle")
        await page.wait_for_timeout(3000)

        posts = page.locator("main a[href*='/p/'], main a[href*='/reel/']")
        count = await posts.count()
        print(f"Posts found: {count}")
        for i in range(count):
            p_elem = posts.nth(i)
            href = await p_elem.get_attribute("href")
            await p_elem.hover()
            await page.wait_for_timeout(800)
            overlay = await page.evaluate("""(el) => {
                const overlay = el.querySelector('ul, div[class*="overlay"], div[class*="_aajy"]');
                return overlay ? overlay.innerText : el.innerText;
            }""", await p_elem.element_handle())
            print(f"Post {i+1} ({href}): {overlay.replace(chr(10), ' | ')}")

        await page.screenshot(path=r"C:\Projects\adham-agent\repos_cache\ig_hover_stats.png")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

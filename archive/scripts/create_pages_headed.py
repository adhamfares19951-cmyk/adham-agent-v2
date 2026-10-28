import asyncio
from playwright.async_api import async_playwright
import json

async def run():
    with open(r'C:\Projects\adham-agent\sessions\cloudflare_cookies.json', 'r', encoding='utf-8') as f:
        raw_cookies = json.load(f)

    formatted_cookies = []
    for c in raw_cookies:
        cookie = {
            'name': c['name'],
            'value': c['value'],
            'domain': c['domain'],
            'path': c.get('path', '/'),
            'httpOnly': c.get('httpOnly', False),
            'secure': c.get('secure', False),
        }
        if c.get('sameSite') in ['Strict', 'Lax', 'None', 'strict', 'lax', 'no_restriction']:
            s = c['sameSite'].lower()
            if s == 'no_restriction':
                cookie['sameSite'] = 'None'
            elif s == 'lax':
                cookie['sameSite'] = 'Lax'
            elif s == 'strict':
                cookie['sameSite'] = 'Strict'
        formatted_cookies.append(cookie)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context()
        await context.add_cookies(formatted_cookies)
        page = await context.new_page()

        print("Navigating to Cloudflare Pages create...")
        await page.goto("https://dash.cloudflare.com/0d5cfb75481d1c9e9f30bfa147dec860/pages/new", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)

        print("URL:", page.url)
        print("Title:", await page.title())

        screenshot_path = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf\cf_headed_pages.png"
        await page.screenshot(path=screenshot_path)
        print("Screenshot saved to", screenshot_path)

        await browser.close()

asyncio.run(run())

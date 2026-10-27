import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/tiktok_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]

async def main():
    async with async_playwright() as p:
        iphone = p.devices['iPhone 14 Pro Max']
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(**iphone)
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        await page.goto('https://www.tiktok.com/@coretradeai', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        print('Mobile page URL:', page.url)
        await page.screenshot(path='repos_cache/tiktok_mobile_profile.png')
        
        # Check buttons
        buttons = await page.eval_on_selector_all('button, a', 'els => els.map(e => e.innerText.trim())')
        clean_buttons = [b for b in buttons if b]
        print('Mobile buttons/links:', clean_buttons[:20])
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

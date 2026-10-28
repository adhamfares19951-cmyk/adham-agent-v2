import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/snapchat_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = []
for c in raw_cookies:
    cookie = {'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)}
    if 'expirationDate' in c and c['expirationDate']: cookie['expires'] = float(c['expirationDate'])
    same_site = c.get('sameSite')
    if same_site:
        if same_site.lower() in ['no_restriction', 'none']: cookie['sameSite'] = 'None'
        elif same_site.lower() == 'lax': cookie['sameSite'] = 'Lax'
        elif same_site.lower() == 'strict': cookie['sameSite'] = 'Strict'
    playwright_cookies.append(cookie)

logo_path = Path('web_platform/logo_ai.jpg').resolve()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        print('Navigating to Snapchat Profile Manager...')
        await page.goto('https://profile.snapchat.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        print('URL:', page.url)
        print('Title:', await page.title())
        await page.screenshot(path='repos_cache/snapchat_profile_manager.png')
        
        # Check text on page
        text = await page.inner_text('body')
        for line in text.splitlines()[:25]:
            if line.strip():
                print('Snap line:', line.strip())
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

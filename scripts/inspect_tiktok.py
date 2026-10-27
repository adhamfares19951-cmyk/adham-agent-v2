import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import asyncio, json
from playwright.async_api import async_playwright
from tools.tiktok_publisher import TIKTOK_DATA_DIR

raw_cookies = json.loads(Path('sessions/tiktok_cookies.json').read_text(encoding='utf-8'))
playwright_cookies = []
for c in raw_cookies:
    cookie = {
        'name': c['name'],
        'value': c['value'],
        'domain': c['domain'],
        'path': c.get('path', '/'),
        'httpOnly': c.get('httpOnly', False),
        'secure': c.get('secure', False),
    }
    if 'expirationDate' in c and c['expirationDate']:
        cookie['expires'] = float(c['expirationDate'])
    same_site = c.get('sameSite')
    if same_site:
        if same_site.lower() in ['no_restriction', 'none']:
            cookie['sameSite'] = 'None'
        elif same_site.lower() == 'lax':
            cookie['sameSite'] = 'Lax'
        elif same_site.lower() == 'strict':
            cookie['sameSite'] = 'Strict'
    playwright_cookies.append(cookie)

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_DATA_DIR),
            channel='msedge',
            headless=True,
            viewport={'width': 1280, 'height': 800},
            args=['--disable-blink-features=AutomationControlled']
        )
        await ctx.add_cookies(playwright_cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        
        print('Navigating to TikTok Studio...')
        await page.goto('https://www.tiktok.com/tiktokstudio', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(5)
        print('Studio URL:', page.url)
        print('Studio Title:', await page.title())
        await page.screenshot(path='repos_cache/tiktok_studio_home.png')
        
        # Check text on Studio page to find username
        text = await page.inner_text('body')
        for line in text.splitlines():
            line = line.strip()
            if line and any(k in line.lower() for k in ['@', 'follower', 'view', 'post', 'manage', 'analytic']):
                print('Studio line:', line[:80])
                
        await ctx.close()

if __name__ == '__main__':
    asyncio.run(main())

import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.tiktok_publisher import TIKTOK_DATA_DIR

raw_cookies = json.loads(Path('sessions/tiktok_cookies.json').read_text(encoding='utf-8'))
playwright_cookies = []
for c in raw_cookies:
    cookie = {'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)}
    if 'expirationDate' in c and c['expirationDate']: cookie['expires'] = float(c['expirationDate'])
    same = c.get('sameSite')
    if same:
        if same.lower() in ['no_restriction', 'none']: cookie['sameSite'] = 'None'
        elif same.lower() == 'lax': cookie['sameSite'] = 'Lax'
        elif same.lower() == 'strict': cookie['sameSite'] = 'Strict'
    playwright_cookies.append(cookie)

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(user_data_dir=str(TIKTOK_DATA_DIR), channel='msedge', headless=True)
        await ctx.add_cookies(playwright_cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto('https://www.tiktok.com/tiktokstudio/upload?from=webapp', wait_until='networkidle', timeout=30000)
        
        # Check all links containing /@
        links = await page.eval_on_selector_all('a[href*="/@"]', 'els => els.map(e => e.href)')
        print('Profile links found:', list(set(links)))
        
        # Also check page avatar or user button
        user_text = await page.eval_on_selector_all('[data-e2e*="user"], [class*="avatar"], [class*="profile"]', 'els => els.map(e => e.innerText)')
        cleaned_text = [t.strip() for t in user_text if t.strip()]
        print('User text elements:', cleaned_text[:10])
        await ctx.close()

if __name__ == '__main__':
    asyncio.run(main())

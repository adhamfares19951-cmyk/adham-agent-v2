import sys, json, asyncio, re
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.tiktok_publisher import TIKTOK_DATA_DIR

raw_cookies = json.load(open('sessions/tiktok_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(user_data_dir=str(TIKTOK_DATA_DIR), channel='msedge', headless=True)
        await ctx.add_cookies(playwright_cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await page.goto('https://www.tiktok.com/tiktokstudio', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        print('Studio URL:', page.url)
        content = await page.content()
        users = re.findall(r'"uniqueId":"([^"]+)"', content)
        print('Found uniqueId in Studio:', set(users))
        nicknames = re.findall(r'"nickname":"([^"]+)"', content)
        print('Found nicknames in Studio:', set(nicknames))
        
        # Look for user profile endpoints or settings
        # In TikTok Studio, let's look at the sidebar or profile section
        studio_links = await page.eval_on_selector_all('a', 'els => els.map(e => e.href)')
        profile_links = [l for l in studio_links if '@' in l or 'profile' in l or 'setting' in l]
        print('Profile/setting links in studio:', set(profile_links))
        await ctx.close()

if __name__ == '__main__':
    asyncio.run(main())

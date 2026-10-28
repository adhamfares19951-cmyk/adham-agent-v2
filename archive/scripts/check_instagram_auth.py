import asyncio, json
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/instagram_cookies.json', 'r', encoding='utf-8'))
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
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        print("Navigating to https://www.instagram.com/ ...")
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=20000)
        await asyncio.sleep(5)
        print('Final URL:', page.url)
        print('Title:', await page.title())
        is_logged_in = 'login' not in page.url
        print('Is Logged In:', is_logged_in)
        
        # Check for Create button (+) on left sidebar
        create_btn = page.locator('svg[aria-label="New post"], svg[aria-label="منشور جديد"], span:has-text("Create"), span:has-text("إنشاء")')
        print('Create buttons found:', await create_btn.count())
        await page.screenshot(path='repos_cache/instagram_feed.png')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

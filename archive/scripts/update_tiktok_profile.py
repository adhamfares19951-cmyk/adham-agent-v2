import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import asyncio, json
from playwright.async_api import async_playwright
from tools.tiktok_publisher import TIKTOK_DATA_DIR

raw_cookies = json.loads(Path('sessions/tiktok_cookies.json').read_text(encoding='utf-8'))
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
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(TIKTOK_DATA_DIR),
            channel='msedge',
            headless=True,
            viewport={'width': 1280, 'height': 800},
            args=['--disable-blink-features=AutomationControlled']
        )
        await ctx.add_cookies(playwright_cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        
        print('1. Navigating to TikTok home...')
        await page.goto('https://www.tiktok.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # Go to profile
        print('2. Going to user profile...')
        # Look for profile avatar button in header
        profile_btn = page.locator('header a[href*="/@"], header [data-e2e="profile-icon"]').first
        if await profile_btn.count() > 0:
            href = await profile_btn.get_attribute('href')
            print('Profile button found, href:', href)
            if href:
                await page.goto(f'https://www.tiktok.com{href}' if href.startswith('/') else href, wait_until='domcontentloaded', timeout=30000)
            else:
                await profile_btn.click()
        else:
            print('Profile button not found in header, navigating to /@me')
            await page.goto('https://www.tiktok.com/@me', wait_until='domcontentloaded', timeout=30000)
            
        await asyncio.sleep(5)
        print('Profile page URL:', page.url)
        await page.screenshot(path='repos_cache/tiktok_profile_before_edit.png')
        
        # Check for Edit Profile button
        edit_btn = page.locator('button:has-text("Edit profile"), button:has-text("تعديل الملف"), [data-e2e="edit-profile-entrance"]').first
        if await edit_btn.count() > 0:
            print('Edit Profile button found! Clicking...')
            await edit_btn.click()
            await asyncio.sleep(3)
            await page.screenshot(path='repos_cache/tiktok_edit_modal.png')
            print('Edit modal screenshot saved.')
            
            # Inspect inputs in edit modal
            inputs = await page.eval_on_selector_all('input, textarea', '''els => els.map(e => ({
                name: e.name, placeholder: e.placeholder, value: e.value, type: e.type
            }))''')
            print('Modal inputs:', inputs)
        else:
            print('Edit Profile button not found on page!')
            
        await ctx.close()

if __name__ == '__main__':
    asyncio.run(main())

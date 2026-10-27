import sys, asyncio, json
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

with open('sessions/instagram_cookies.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

cookies = []
for c in raw:
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
    same = c.get('sameSite')
    if same:
        if same.lower() in ['no_restriction', 'none']:
            cookie['sameSite'] = 'None'
        elif same.lower() == 'lax':
            cookie['sameSite'] = 'Lax'
        elif same.lower() == 'strict':
            cookie['sameSite'] = 'Strict'
    cookies.append(cookie)

store_url = 'https://console-duration-sage-troubleshooting.trycloudflare.com/glamp'

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(cookies)
        page = await ctx.new_page()
        print('Navigating to Edit Profile...')
        await page.goto('https://www.instagram.com/accounts/edit/', wait_until='networkidle', timeout=30000)
        
        # Find Website input
        website_input = page.locator('input[placeholder="Website"]')
        if await website_input.count() > 0:
            print('Found Website input. Clearing and filling store URL...')
            await website_input.fill('')
            await website_input.fill(store_url)
            await asyncio.sleep(1)
            
            # Find and click Submit
            submit_btn = page.locator('div[role="button"]:has-text("Submit"), button:has-text("Submit")')
            if await submit_btn.count() > 0:
                print('Clicking Submit button...')
                await submit_btn.first.click()
                await asyncio.sleep(4)
                print('Submit clicked!')
        
        await page.screenshot(path='repos_cache/instagram_submitted.png')
        
        # Check public profile
        print('Navigating to public profile...')
        await page.goto('https://www.instagram.com/gazachild24/', wait_until='networkidle', timeout=30000)
        await asyncio.sleep(3)
        await page.screenshot(path='repos_cache/instagram_profile_public.png')
        print('Public profile screenshot saved.')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

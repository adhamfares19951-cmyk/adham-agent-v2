import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/tiktok_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]
logo_path = Path('web_platform/logo_ai.jpg').resolve()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        await page.goto('https://www.tiktok.com/setting', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        btn = page.locator('text="Edit personal details"')
        if await btn.count() > 0:
            print('Found Edit personal details button! Clicking...')
            await btn.first.click()
            await asyncio.sleep(4)
            print('Current URL:', page.url)
            await page.screenshot(path='repos_cache/tiktok_personal_details.png')
            
            # Print inputs found
            inputs = await page.eval_on_selector_all('input, textarea', '''els => els.map(e => ({
                name: e.name, placeholder: e.placeholder, value: e.value, type: e.type, id: e.id
            }))''')
            print('Inputs found in personal details:', inputs)
            
            # Check text on page
            text = await page.inner_text('body')
            for line in text.splitlines():
                line = line.strip()
                if any(k in line.lower() for k in ['name', 'username', 'bio', 'photo', 'avatar', 'edit', 'phone']):
                    print('Details line:', line)
        else:
            print('Edit personal details not found on page')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

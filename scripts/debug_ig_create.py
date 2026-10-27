import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/instagram_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=20000)
        await asyncio.sleep(4)
        
        # Click Create
        create_btn = page.locator('svg[aria-label="New post"]').first
        if await create_btn.count() == 0:
            create_btn = page.locator('span:has-text("Create"), span:has-text("إنشاء")').first
            
        print("Clicking Create button...")
        await create_btn.click()
        await asyncio.sleep(2)
        
        # Check submenus
        print("Checking text after click:")
        text = await page.inner_text('body')
        for line in text.splitlines():
            line = line.strip()
            if any(k in line.lower() for k in ['post', 'story', 'reel', 'live', 'drag', 'select', 'create', 'إنشاء', 'منشور']):
                print('  Line:', line)
                
        # Click "Post" if submenu is visible
        sub_post = page.locator('span:has-text("Post"), span:has-text("منشور")')
        if await sub_post.count() > 0:
            print(f"Found {await sub_post.count()} 'Post' sub-items, clicking first visible...")
            for idx in range(await sub_post.count()):
                if await sub_post.nth(idx).is_visible():
                    await sub_post.nth(idx).click()
                    print(f"Clicked sub_post #{idx}")
                    await asyncio.sleep(2)
                    break
                    
        await page.screenshot(path='repos_cache/instagram_debug_modal.png')
        inputs = await page.eval_on_selector_all('input', 'els => els.map(e => ({type: e.type, accept: e.accept}))')
        print('All inputs after sub-click:', inputs)
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

import sys
from pathlib import Path
import asyncio, json

sys.stdout.reconfigure(encoding='utf-8')
from playwright.async_api import async_playwright

raw_cookies = json.load(open('sessions/instagram_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]
video_path = Path('workspace_data/media/glamp_tiktok_final.mp4').resolve()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # Click the SVG or its parent
        btn = page.locator('svg[aria-label="New post"]')
        print("Clicking svg[aria-label='New post']...")
        await btn.click()
        await asyncio.sleep(3)
        await page.screenshot(path='repos_cache/ig_clicked_new_post.png')
        
        # Check text on page
        text = await page.inner_text('body')
        for line in text.splitlines():
            line = line.strip()
            if any(k in line.lower() for k in ['drag', 'select', 'computer', 'create new post', 'post', 'reel', 'story']):
                print("  Found line:", line)
                
        # Check file inputs
        inputs = await page.eval_on_selector_all('input[type="file"]', 'els => els.length')
        print(f"File inputs count: {inputs}")
        
        # If there is a submenu "Post"
        sub_post = page.locator('span:has-text("Post")')
        if await sub_post.count() > 0 and await sub_post.first.is_visible():
            print("Found Post submenu! Clicking it...")
            await sub_post.first.click()
            await asyncio.sleep(3)
            await page.screenshot(path='repos_cache/ig_after_sub_post.png')
            inputs_after = await page.eval_on_selector_all('input[type="file"]', 'els => els.length')
            print(f"File inputs count after clicking Post: {inputs_after}")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

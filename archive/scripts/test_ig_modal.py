import sys
from pathlib import Path
import asyncio, json

sys.stdout.reconfigure(encoding='utf-8')
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

video_path = Path('workspace_data/media/glamp_tiktok_final.mp4').resolve()

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        
        print("1. Opening Instagram Home...")
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # Check if any restriction modal or dialog is present
        print("2. Dismissing any restriction / info modals...")
        for _ in range(3):
            # Try clicking close button (X) if visible
            close_btn = page.locator('svg[aria-label="Close"], svg[aria-label="إغلاق"], div[role="button"]:has(svg[aria-label="Close"])')
            if await close_btn.count() > 0:
                print("Found Close button (X), clicking...")
                await close_btn.first.click()
                await asyncio.sleep(1)
            else:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
                
        await page.screenshot(path='repos_cache/ig_dismissed.png')
        
        # Now click Create
        print("3. Clicking 'Create' (إنشاء)...")
        create_btn = page.locator('svg[aria-label="New post"], svg[aria-label="منشور جديد"]').first
        if await create_btn.count() == 0:
            create_btn = page.locator('span:has-text("Create"), span:has-text("إنشاء")').first
        await create_btn.click()
        await asyncio.sleep(2)
        
        # Click Post
        sub_post = page.locator('span:has-text("Post"), span:has-text("منشور")')
        if await sub_post.count() > 0:
            for idx in range(await sub_post.count()):
                if await sub_post.nth(idx).is_visible():
                    print(f"Clicking visible submenu item #{idx}...")
                    await sub_post.nth(idx).click()
                    await asyncio.sleep(2)
                    break
                    
        await page.screenshot(path='repos_cache/ig_modal_after_create.png')
        print("Create clicked successfully! Checking file input...")
        
        file_input = page.locator('input[type="file"]')
        print(f"File inputs count: {await file_input.count()}")
        if await file_input.count() > 0:
            print("Attaching video file...")
            await file_input.first.set_input_files(str(video_path))
            print("Attached! Waiting for video processing...")
            await asyncio.sleep(6)
            await page.screenshot(path='repos_cache/ig_video_attached.png')
            
            # Print buttons on modal
            buttons = await page.eval_on_selector_all('button, div[role="button"]', 'els => els.map(e => e.innerText.trim())')
            print("Buttons on modal:", [b for b in buttons if b])
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

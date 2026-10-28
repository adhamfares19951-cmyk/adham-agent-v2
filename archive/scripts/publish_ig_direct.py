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

caption = (
    "مصباح G-Lamp الذكي 4 في 1 🔥\n"
    "شاحن لاسلكي سريع 15W + سبيكر بلوتوث سينمائي نقي + إضاءة RGB تفاعلية مع الموسيقى!\n"
    "⚡ خصم 40% + شحن مجاني لكافة مناطق المملكة والإمارات 🇸🇦 🇦🇪\n"
    "🚚 الدفع عند الاستلام بعد المعاينة!\n"
    "💬 للطلب الفوري: تواصل معنا عبر الخاص (DM)\n\n"
    "#السعودية #الرياض #جدة #سيت_اب #ديكور #شاحن_لاسلكي #تقنية #smartstore #reels"
)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        
        print("1. Opening Instagram Home...")
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # Click the exact Create nav item
        print("2. Clicking '+ Create' nav item...")
        # In sidebar, there is svg aria-label="New post" inside an a/div
        create_nav = page.locator('div:has-text("Create"), span:has-text("Create")').last
        await create_nav.click()
        await asyncio.sleep(3)
        
        # Check if submenu opened or modal opened directly
        submenu_post = page.locator('span:has-text("Post")')
        if await submenu_post.count() > 0 and await submenu_post.first.is_visible():
            print("Submenu 'Post' visible, clicking...")
            await submenu_post.first.click()
            await asyncio.sleep(3)
            
        await page.screenshot(path='repos_cache/ig_modal_now.png')
        
        # Check if file input is available
        file_input = page.locator('input[type="file"]')
        print(f"File inputs found: {await file_input.count()}")
        
        if await file_input.count() > 0:
            print("Attaching video file...")
            await file_input.first.set_input_files(str(video_path))
            print("Video attached! Waiting 6s for Instagram processing...")
            await asyncio.sleep(6)
            await page.screenshot(path='repos_cache/ig_modal_video_attached.png')
            
            # If "Reels are now shared as..." modal pops up, click OK
            ok_btn = page.locator('button:has-text("OK")')
            if await ok_btn.count() > 0 and await ok_btn.first.is_visible():
                print("Clicking OK modal...")
                await ok_btn.first.click()
                await asyncio.sleep(1)
                
            # Click Next (Crop step)
            print("Clicking Next (1)...")
            next1 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
            if await next1.count() > 0:
                await next1.click()
                await asyncio.sleep(3)
                
            # Click Next (Filter/Cover step)
            print("Clicking Next (2)...")
            next2 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
            if await next2.count() > 0:
                await next2.click()
                await asyncio.sleep(3)
                
            # Fill Caption
            print("Entering caption...")
            caption_box = page.locator('div[aria-label="Write a caption..."], div[role="textbox"]').first
            if await caption_box.count() > 0:
                await caption_box.click()
                await asyncio.sleep(0.5)
                await page.keyboard.insert_text(caption)
                await asyncio.sleep(1)
                print("Caption filled!")
                
            await page.screenshot(path='repos_cache/ig_caption_step.png')
            
            # Click Share
            print("Clicking 'Share'...")
            share_btn = page.locator('div[role="button"]:has-text("Share"), button:has-text("Share")').first
            if await share_btn.count() > 0:
                await share_btn.click()
                print("Share clicked! Waiting for publishing confirmation...")
                for s in range(1, 45):
                    await asyncio.sleep(1)
                    content = await page.content()
                    if any(k in content for k in ["Your reel has been shared", "Your post has been shared"]):
                        print(f"🎉 INSTAGRAM REEL CONFIRMED SHARED in {s}s!")
                        break
                        
            await asyncio.sleep(3)
            await page.screenshot(path='repos_cache/ig_shared_success.png')
            print("Finished!")
        else:
            print("Could not find file input on page.")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

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
    "🚚 الدفع عند الاستلام!\n"
    "💬 للطلب المباشر: تواصل معنا عبر الخاص (DM)\n\n"
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
        
        # Press escape in case of modals
        await page.keyboard.press("Escape")
        await asyncio.sleep(1)
        
        # 2. Click Create
        print("2. Clicking 'Create' with force=True...")
        create_btn = page.locator('svg[aria-label="New post"], svg[aria-label="منشور جديد"], a:has-text("Create"), span:has-text("Create")').first
        await create_btn.click(force=True)
        await asyncio.sleep(2)
        
        # Click Post
        sub_post = page.locator('span:has-text("Post"), span:has-text("منشور")')
        if await sub_post.count() > 0:
            for idx in range(await sub_post.count()):
                if await sub_post.nth(idx).is_visible():
                    print(f"Clicking visible submenu item #{idx} with force=True...")
                    await sub_post.nth(idx).click(force=True)
                    await asyncio.sleep(2)
                    break
                    
        await page.screenshot(path='repos_cache/ig_modal_after_create.png')
        print("Screenshot saved to repos_cache/ig_modal_after_create.png")
        
        # 3. Locate file input
        file_input = page.locator('input[type="file"]')
        print(f"File inputs found: {await file_input.count()}")
        if await file_input.count() > 0:
            print("Attaching video file to uploader...")
            await file_input.first.set_input_files(str(video_path))
            print("Attached! Waiting 6s for video processing...")
            await asyncio.sleep(6)
            await page.screenshot(path='repos_cache/ig_video_attached.png')
            
            # Click "OK" if ratio warning pops up ("Reels are now shared as...")
            ok_btn = page.locator('button:has-text("OK"), button:has-text("موافق")')
            if await ok_btn.count() > 0:
                print("Clicking OK on Reels info modal...")
                await ok_btn.first.click(force=True)
                await asyncio.sleep(1)
                
            # 4. Click Next (Step 1 - Crop)
            print("4. Clicking 'Next' (Step 1)...")
            next_btn1 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next"), div[role="button"]:has-text("التالي"), button:has-text("التالي")')
            if await next_btn1.count() > 0:
                await next_btn1.first.click(force=True)
                await asyncio.sleep(3)
                
            # 5. Click Next (Step 2 - Filters)
            print("5. Clicking 'Next' (Step 2)...")
            next_btn2 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next"), div[role="button"]:has-text("التالي"), button:has-text("التالي")')
            if await next_btn2.count() > 0:
                await next_btn2.first.click(force=True)
                await asyncio.sleep(3)
                
            # 6. Enter Caption
            print("6. Entering Caption...")
            caption_box = page.locator('div[aria-label="Write a caption..."], div[aria-label="كتابة شرح توضيحي..."], div[role="textbox"]')
            if await caption_box.count() > 0:
                await caption_box.first.click(force=True)
                await asyncio.sleep(0.5)
                await page.keyboard.insert_text(caption)
                await asyncio.sleep(1)
                print("Caption entered!")
                
            await page.screenshot(path='repos_cache/ig_caption_entered.png')
            
            # 7. Click Share
            print("7. Clicking 'Share' (مشاركة)...")
            share_btn = page.locator('div[role="button"]:has-text("Share"), button:has-text("Share"), div[role="button"]:has-text("مشاركة"), button:has-text("مشاركة")')
            if await share_btn.count() > 0:
                await share_btn.first.click(force=True)
                print("Clicked Share! Waiting for completion...")
                for s in range(1, 45):
                    await asyncio.sleep(1)
                    content = await page.content()
                    if any(k in content for k in ["Your reel has been shared", "Your post has been shared", "تمت مشاركة منشورك"]):
                        print(f"✅ Reel Confirmed Shared in {s}s!")
                        break
                        
            await asyncio.sleep(3)
            await page.screenshot(path='repos_cache/ig_final_shared.png')
            print("Final screenshot saved to repos_cache/ig_final_shared.png")
            print("INSTAGRAM REEL PUBLISHED SUCCESSFULLY!")
        else:
            print("File input not found!")
            
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())

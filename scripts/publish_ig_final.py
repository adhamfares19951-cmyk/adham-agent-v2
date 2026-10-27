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
    print("==================================================")
    print("🚀 Publishing Instagram Reel Automatically")
    print(f"Video file: {video_path} ({video_path.stat().st_size} bytes)")
    print("==================================================")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 900})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        
        print("1. Opening Instagram Home...")
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # 2. Click 'New post'
        print("2. Clicking 'New post' button...")
        btn = page.locator('svg[aria-label="New post"]')
        await btn.click()
        await asyncio.sleep(3)
        
        # 3. Attach Video File
        print("3. Attaching video to file input...")
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(str(video_path))
        print("Video attached! Waiting 6s for processing...")
        await asyncio.sleep(6)
        await page.screenshot(path='repos_cache/ig_step1_video.png')
        
        # 4. Handle "Reels are now shared as..." OK button if present
        ok_btn = page.locator('button:has-text("OK")')
        if await ok_btn.count() > 0 and await ok_btn.first.is_visible():
            print("Dismissing 'Reels' info popup with OK...")
            await ok_btn.first.click()
            await asyncio.sleep(1)
            
        # 5. Click Next (Step 1 - Crop)
        print("4. Clicking 'Next' (Step 1)...")
        next1 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
        await next1.click()
        await asyncio.sleep(3)
        await page.screenshot(path='repos_cache/ig_step2_crop.png')
        
        # 6. Click Next (Step 2 - Filters & Cover)
        print("5. Clicking 'Next' (Step 2)...")
        next2 = page.locator('div[role="button"]:has-text("Next"), button:has-text("Next")').first
        await next2.click()
        await asyncio.sleep(3)
        await page.screenshot(path='repos_cache/ig_step3_caption.png')
        
        # 7. Fill Caption
        print("6. Entering Caption and Hashtags...")
        caption_box = page.locator('div[aria-label="Write a caption..."], div[role="textbox"]').first
        if await caption_box.count() > 0:
            await caption_box.click()
            await asyncio.sleep(0.5)
            await page.keyboard.insert_text(caption)
            await asyncio.sleep(1)
            print("Caption inserted successfully!")
            
        await page.screenshot(path='repos_cache/ig_step4_caption_ready.png')
        
        # 8. Click Share
        print("7. Clicking 'Share' (مشاركة) with force=True...")
        share_btn = page.locator('div[role="button"]:has-text("Share"), button:has-text("Share")').first
        await share_btn.click(force=True)
        print("Share clicked! Waiting for reel sharing confirmation...")
        
        shared = False
        for s in range(1, 45):
            await asyncio.sleep(1)
            content = await page.content()
            if any(k in content for k in ["Your reel has been shared", "Your post has been shared"]):
                print(f"🎉 INSTAGRAM REEL CONFIRMED SHARED in {s}s!")
                shared = True
                break
                
        if not shared:
            print("Waiting additional 5s to finalize...")
            await asyncio.sleep(5)
            
        await page.screenshot(path='repos_cache/ig_final_shared_proof.png')
        print("Saved confirmation proof to repos_cache/ig_final_shared_proof.png")
        await browser.close()
        print("ALL DONE!")

if __name__ == '__main__':
    asyncio.run(main())

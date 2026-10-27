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
        
        print("1. Opening Instagram...")
        await page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        
        # Click New post
        print("2. Clicking New post...")
        await page.locator('svg[aria-label="New post"]').click()
        await asyncio.sleep(3)
        
        # Attach file
        print("3. Attaching video file...")
        await page.locator('input[type="file"]').first.set_input_files(str(video_path))
        await asyncio.sleep(6)
        
        # Dismiss OK if present
        ok = page.locator('button:has-text("OK")')
        if await ok.count() > 0 and await ok.first.is_visible():
            await ok.first.click()
            await asyncio.sleep(1)
            
        # Click Next (1)
        print("4. Clicking Next (1)...")
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
            const b = btns.find(el => el.innerText.trim() === 'Next');
            if (b) b.click();
        }''')
        await asyncio.sleep(3)
        
        # Click Next (2)
        print("5. Clicking Next (2)...")
        await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
            const b = btns.find(el => el.innerText.trim() === 'Next');
            if (b) b.click();
        }''')
        await asyncio.sleep(3)
        
        # Fill Caption
        print("6. Entering Caption...")
        caption_box = page.locator('div[aria-label="Write a caption..."], div[role="textbox"]').first
        if await caption_box.count() > 0:
            await caption_box.click(force=True)
            await asyncio.sleep(0.5)
            await page.keyboard.insert_text(caption)
            await asyncio.sleep(1)
            
        # Click Share via evaluate
        print("7. Clicking Share button via evaluate...")
        shared_clicked = await page.evaluate('''() => {
            const btns = Array.from(document.querySelectorAll('div[role="button"], button'));
            const b = btns.find(el => el.innerText.trim() === 'Share');
            if (b) {
                b.click();
                return true;
            }
            return false;
        }''')
        print("Share button clicked via JS:", shared_clicked)
        
        # Wait and monitor publishing progress
        print("8. Waiting for publishing completion...")
        for s in range(1, 40):
            await asyncio.sleep(1)
            content = await page.content()
            if any(k in content for k in ["Your reel has been shared", "Your post has been shared"]):
                print(f"🎉 INSTAGRAM REEL CONFIRMED SHARED in {s}s!")
                break
                
        await asyncio.sleep(4)
        await page.screenshot(path='repos_cache/ig_published_final_reel.png')
        print("Saved confirmation screenshot.")
        await browser.close()
        print("ALL DONE!")

if __name__ == '__main__':
    asyncio.run(main())

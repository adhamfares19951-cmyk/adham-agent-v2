import sys, json, asyncio
sys.stdout.reconfigure(encoding='utf-8')
from pathlib import Path
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.tiktok_publisher import TIKTOK_DATA_DIR

raw_cookies = json.load(open('sessions/tiktok_cookies.json', 'r', encoding='utf-8'))
playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/'), 'httpOnly': c.get('httpOnly', False), 'secure': c.get('secure', False)} for c in raw_cookies]
logo_path = Path('web_platform/logo_ai.jpg').resolve()

async def main():
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(user_data_dir=str(TIKTOK_DATA_DIR), channel='msedge', headless=True)
        await ctx.add_cookies(playwright_cookies)
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()
        print('Navigating to https://www.tiktok.com/@coretradeai ...')
        await page.goto('https://www.tiktok.com/@coretradeai', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)
        print('Page Title:', await page.title())
        await page.screenshot(path='repos_cache/tiktok_coretradeai.png')
        
        buttons = await page.eval_on_selector_all('button', 'els => els.map(e => e.innerText)')
        print('All buttons on page:', [b.strip() for b in buttons if b.strip()])
        if count > 0:
            print('Clicking Edit Profile...')
            await edit_btn.first.click()
            await asyncio.sleep(3)
            await page.screenshot(path='repos_cache/tiktok_edit_modal.png')
            
            # Check inputs inside dialog
            inputs = await page.eval_on_selector_all('input, textarea', '''els => els.map(e => ({
                name: e.name, placeholder: e.placeholder, value: e.value, type: e.type, id: e.id
            }))''')
            print('Modal inputs found:', inputs)
            
            # 1. Update Name
            name_input = page.locator('input[placeholder="Name"], input[data-e2e="edit-profile-name-input"]')
            if await name_input.count() > 0:
                print('Updating Name to "Smart Store | متجر سمارت"')
                await name_input.fill('Smart Store | متجر سمارت')
                
            # 2. Update Bio
            bio_input = page.locator('textarea[placeholder="Bio"], textarea[data-e2e="edit-profile-bio-input"]')
            if await bio_input.count() > 0:
                print('Updating Bio...')
                bio_text = '🌟 وجهتك لأحدث المنتجات الذكية بالخليج 🇸🇦 🇦🇪\n⚡ مصباح G-Lamp 4in1 (شاحن 15W وسبيكر)\n🚚 شحن مجاني + الدفع عند الاستلام'
                await bio_input.fill(bio_text)
                
            # 3. Update Avatar / Photo
            file_input = page.locator('input[type="file"]')
            if await file_input.count() > 0 and logo_path.exists():
                print(f'Setting avatar to: {logo_path}')
                await file_input.first.set_input_files(str(logo_path))
                await asyncio.sleep(3)
                # Look for crop "Apply" or "Save" button in avatar dialog
                apply_btn = page.locator('button:has-text("Apply"), button:has-text("Save"), button:has-text("تطبيق")')
                if await apply_btn.count() > 0:
                    print('Clicking Apply for avatar...')
                    await apply_btn.last.click()
                    await asyncio.sleep(2)
                    
            # 4. Click Save Profile
            save_btn = page.locator('button:has-text("Save"), [data-e2e="edit-profile-save-btn"]')
            if await save_btn.count() > 0:
                print('Clicking Save Profile button...')
                await save_btn.first.click()
                await asyncio.sleep(4)
                print('Profile Saved!')
                
            await page.screenshot(path='repos_cache/tiktok_profile_after_edit.png')
            print('Saved after-edit screenshot.')
        else:
            print('Edit Profile button not visible directly.')
        await ctx.close()

if __name__ == '__main__':
    asyncio.run(main())

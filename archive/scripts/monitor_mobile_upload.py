import asyncio
import os
import sys
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA_DIR = r"C:\Projects\adham-agent\sessions\tiktok_user_data"
BRAIN_DIR = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf"
SCREENSHOT_PROFILE = os.path.join(BRAIN_DIR, "tiktok_mobile_upload_live.png")
SCREENSHOT_STUDIO = os.path.join(BRAIN_DIR, "tiktok_mobile_studio_live.png")

async def monitor():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1280, "height": 850},
            locale="ar-SA"
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("1. Opening TikTok Studio Content page...")
        try:
            await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=35000)
            await asyncio.sleep(5)
            await page.screenshot(path=SCREENSHOT_STUDIO)
            print("Studio screenshot saved.")

            videos_info = await page.evaluate("""() => {
                const rows = [];
                // Find all table rows or video cards
                document.querySelectorAll('div[class*="table-row"], div[data-e2e="content-item"], tr').forEach(r => {
                    const text = r.innerText.trim();
                    if (text && (text.includes('مصباح') || text.includes('سيت اب') || text.includes('مشاهد') || text.includes(':') || text.includes('اليوم') || text.includes('الآن'))) {
                        rows.push(text);
                    }
                });
                return rows;
            }""")
            print(f"Studio found {len(videos_info)} video rows:")
            for i, v in enumerate(videos_info[:4]):
                print(f"--- Video {i} ---:\n{v}\n")
        except Exception as e:
            print("Error inspecting Studio:", e)

        print("\n2. Opening Public Profile @coretradeai...")
        try:
            await page.goto("https://www.tiktok.com/@coretradeai", wait_until="domcontentloaded", timeout=35000)
            await asyncio.sleep(5)
            await page.screenshot(path=SCREENSHOT_PROFILE)
            print("Profile screenshot saved.")

            profile_data = await page.evaluate("""() => {
                const posts = document.querySelectorAll('div[data-e2e="user-post-item"]');
                const list = [];
                posts.forEach((p, idx) => {
                    const link = p.querySelector('a')?.href || '';
                    const desc = p.querySelector('img')?.alt || p.innerText || '';
                    list.push({ index: idx, link: link, text: desc.slice(0, 100) });
                });
                return list;
            }""")
            print("Profile post items:", profile_data)
        except Exception as e:
            print("Error inspecting profile:", e)

        await context.close()

if __name__ == "__main__":
    asyncio.run(monitor())

import asyncio
import os
import sys
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

USER_DATA_DIR = r"C:\Projects\adham-agent\sessions\tiktok_user_data"
BRAIN_DIR = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf"
SCREENSHOT_STUDIO = os.path.join(BRAIN_DIR, "tiktok_studio_live_views.png")
SCREENSHOT_PROFILE = os.path.join(BRAIN_DIR, "tiktok_profile_live_views.png")

async def check():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=True,
            viewport={"width": 1366, "height": 850},
            locale="ar-SA",
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening TikTok Studio...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(6000)
        await page.screenshot(path=SCREENSHOT_STUDIO, full_page=False)
        print("Studio screenshot captured.")

        # Extract rows
        rows = await page.evaluate("""() => {
            const items = [];
            document.querySelectorAll('tr, div[data-e2e="content-item"], div[class*="video-card"], div[class*="table-row"]').forEach(el => {
                const t = el.innerText.trim();
                if (t && (t.includes('مشاهدة') || t.includes('عرض') || t.includes('G-Lamp') || t.includes(':') || t.includes('2026'))) {
                    items.push(t);
                }
            });
            return items;
        }""")
        print("Extracted rows count:", len(rows))
        for i, r in enumerate(rows[:5]):
            print(f"Row {i}:\n{r}\n")

        print("Opening TikTok Profile @coretradeai...")
        await page.goto("https://www.tiktok.com/@coretradeai", wait_until="domcontentloaded", timeout=45000)
        await page.wait_for_timeout(5000)
        await page.screenshot(path=SCREENSHOT_PROFILE, full_page=False)
        print("Profile screenshot captured.")

        await context.close()

if __name__ == "__main__":
    asyncio.run(check())

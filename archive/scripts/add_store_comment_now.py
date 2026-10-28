import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path(r"C:\Projects\adham-agent\sessions\tiktok_user_data")
video_url = "https://www.tiktok.com/@coretradeai/video/7701607244676205844"
store_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"
comment_text = f"🔥 رابط الطلب المباشر والدفع عند الاستلام (خصم 40% + توصيل مجاني 149 ريال): {store_url} 🇸🇦 🇦🇪"

async def comment():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            headless=True,
            viewport={"width": 1280, "height": 850},
            locale="ar-SA"
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print(f"Opening video {video_url}...")
        await page.goto(video_url, wait_until="domcontentloaded", timeout=35000)
        await asyncio.sleep(4)

        # Click on 'تعليقات' tab or comment icon
        cmt_tab = page.locator('span:has-text("تعليقات"), div:has-text("تعليقات"), button[aria-label*="تعليق"]').first
        if await cmt_tab.count() > 0:
            print("Clicking comments tab...")
            await cmt_tab.click(force=True)
            await asyncio.sleep(2)

        # Look for comment input
        box = page.locator('div[contenteditable="true"], div[data-e2e="comment-input"], textarea').first
        if await box.count() > 0:
            print("Found comment input box! Inserting text...")
            await box.click(force=True)
            await asyncio.sleep(1)
            await page.keyboard.insert_text(comment_text)
            await asyncio.sleep(1)
            await page.keyboard.press("Enter")
            await asyncio.sleep(4)
            print("Comment posted!")

        proof_path = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf\new_video_comment_confirmed.png"
        await page.screenshot(path=proof_path)
        print(f"Proof saved to {proof_path}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(comment())

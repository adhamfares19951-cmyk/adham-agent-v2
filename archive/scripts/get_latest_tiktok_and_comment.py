import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path(r"C:\Projects\adham-agent\sessions\tiktok_user_data")
store_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"
comment_text = f"🔥 رابط الطلب المباشر والدفع عند الاستلام (توصيل مجاني 149 ريال): {store_url} 🇸🇦 🇦🇪"

async def main():
    async with async_playwright() as p:
        context = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            headless=True,
            viewport={"width": 1280, "height": 850},
            locale="ar-SA"
        )
        page = context.pages[0] if context.pages else await context.new_page()

        print("Opening profile @coretradeai...")
        await page.goto("https://www.tiktok.com/@coretradeai", wait_until="domcontentloaded", timeout=35000)
        await asyncio.sleep(5)

        # Click the first video item
        first_video = page.locator('div[data-e2e="user-post-item"]').first
        if await first_video.count() > 0:
            print("Found first video on profile! Clicking...")
            await first_video.click()
            await asyncio.sleep(5)
            video_url = page.url
            print(f"Current Video URL: {video_url}")

            # Try to comment
            comment_box = page.locator('div[contenteditable="true"], div[data-e2e="comment-input"], textarea').first
            if await comment_box.count() > 0:
                print("Inserting store comment...")
                await comment_box.click(force=True)
                await asyncio.sleep(1)
                await page.keyboard.insert_text(comment_text)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(3)
                print("Comment submitted!")

            screenshot_path = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf\tiktok_angle2_comment_proof.png"
            await page.screenshot(path=screenshot_path)
            print(f"Proof saved to {screenshot_path}")
        else:
            print("No video item found on profile yet (might be processing).")

        await context.close()

if __name__ == "__main__":
    asyncio.run(main())

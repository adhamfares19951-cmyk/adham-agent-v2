import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path(r"C:\Projects\adham-agent\sessions\tiktok_user_data")
video_url = "https://www.tiktok.com/@coretradeai/video/7701607244676205844"
store_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"
comment_text = f"🔥 رابط الطلب المباشر والدفع عند الاستلام (خصم 40% + شحن مجاني 149 ريال/درهم): {store_url} 🇸🇦 🇦🇪"

async def check_and_comment():
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
        await asyncio.sleep(5)

        # Check existing comments count
        comments_cnt = await page.evaluate("""() => {
            const el = document.querySelector('[data-e2e="comment-count"]');
            return el ? el.innerText : '0';
        }""")
        print(f"Current comments count on video: {comments_cnt}")

        if comments_cnt == "0" or comments_cnt == "":
            print("No comments yet. Adding pinned store link comment...")
            comment_box = page.locator('div[contenteditable="true"], div[data-e2e="comment-input"], textarea').first
            if await comment_box.count() > 0:
                await comment_box.click(force=True)
                await asyncio.sleep(1)
                await page.keyboard.insert_text(comment_text)
                await asyncio.sleep(1)
                await page.keyboard.press("Enter")
                await asyncio.sleep(4)
                print("Store link comment posted successfully!")
            else:
                print("Comment box not found.")
        else:
            print("Comment already exists on this video.")

        proof_path = r"C:\Users\Administrator\.gemini\antigravity\brain\33a48800-6776-46e5-9ca0-d8560b49d7bf\mobile_video_comment_proof.png"
        await page.screenshot(path=proof_path)
        print(f"Saved proof to {proof_path}")

        await context.close()

if __name__ == "__main__":
    asyncio.run(check_and_comment())

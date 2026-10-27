# -*- coding: utf-8 -*-
"""Posts the purchase link comment on the published TikTok video."""
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path("sessions/tiktok_user_data").resolve()
new_tunnel_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"
video_full_url = "https://www.tiktok.com/@coretradeai/video/7701283907949350164"
comment_text = f"🔥 رابط الطلب المباشر والدفع عند الاستلام (خصم 40% + توصيل مجاني): {new_tunnel_url} 🇸🇦 🇦🇪 أو تواصل معنا خاص DM!"

async def comment_tiktok():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print(f"1. Navigating to TikTok Video: {video_full_url}...")
        await page.goto(video_full_url, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(5)

        await page.screenshot(path="repos_cache/tiktok_video_watch.png")
        print("Video page loaded, screenshot saved.")

        # Look for comment input box
        comment_box = page.locator('div[contenteditable="true"], div[data-e2e="comment-input"], textarea').first
        if await comment_box.count() > 0:
            print("Found comment box. Inserting comment text...")
            await comment_box.click(force=True)
            await asyncio.sleep(1)
            await page.keyboard.insert_text(comment_text)
            await asyncio.sleep(1)

            # Look for Post button or press Enter
            post_btn = page.locator('div[data-e2e="comment-post"], button:has-text("Post"), div[role="button"]:has-text("نشر")').first
            if await post_btn.count() > 0:
                print("Clicking Post button...")
                await post_btn.click(force=True)
            else:
                print("Pressing Enter...")
                await page.keyboard.press("Enter")

            await asyncio.sleep(4)
            await page.screenshot(path="repos_cache/tiktok_comment_posted.png")
            print("Comment posted on TikTok!")
        else:
            print("Comment input not found on page.")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(comment_tiktok())

# -*- coding: utf-8 -*-
"""Checks TikTok Studio uploaded videos and profile to verify link and state."""
import sys
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

user_data = Path("sessions/tiktok_user_data").resolve()

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=str(user_data),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print("1. Opening TikTok Studio Content Manager...")
        await page.goto("https://www.tiktok.com/tiktokstudio/content", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(6)

        await page.screenshot(path="repos_cache/tiktok_content_manager.png")
        print("Saved screenshot to repos_cache/tiktok_content_manager.png")

        text = await page.inner_text("body")
        for line in text.splitlines()[:25]:
            if line.strip():
                print("TT Line:", line.strip())

        await browser.close()

if __name__ == '__main__':
    asyncio.run(check())

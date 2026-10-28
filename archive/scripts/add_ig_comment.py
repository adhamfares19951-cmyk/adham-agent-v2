# -*- coding: utf-8 -*-
"""Adds a direct purchase comment with the new link on the published Instagram Reel."""
import sys
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

reel_url = "https://www.instagram.com/smartstore.gcc/reel/De_nMgAs1F1/"
new_tunnel_url = "https://ministries-direct-specify-universe.trycloudflare.com/glamp"

comment_text = f"🔥 رابط الطلب المباشر والدفع عند الاستلام (خصم 40% + شحن مجاني): {new_tunnel_url} 🇸🇦 🇦🇪 أو تواصل معنا عبر الخاص (DM) للطلب الفوري!"

async def add_comment():
    raw_cookies = json.load(open('sessions/instagram_cookies.json', 'r', encoding='utf-8'))
    playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/')} for c in raw_cookies]

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()

        print(f"1. Navigating to Reel: {reel_url}...")
        await page.goto(reel_url, wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)

        # Look for comment input: aria-label="Add a comment…" or role="textbox"
        comment_box = page.locator('textarea[aria-label="Add a comment…"], textarea[placeholder*="comment"], div[role="textbox"][aria-label*="comment"], textarea').first
        if await comment_box.count() > 0:
            print("Found comment box. Clicking and typing...")
            await comment_box.click(force=True)
            await asyncio.sleep(1)
            await page.keyboard.insert_text(comment_text)
            await asyncio.sleep(1)

            # Find Post button
            post_btn = page.locator('div[role="button"]:has-text("Post"), button:has-text("Post"), div[role="button"]:has-text("نشر"), button:has-text("نشر")').first
            if await post_btn.count() > 0:
                print("Clicking Post...")
                await post_btn.click(force=True)
                await asyncio.sleep(4)
                print("Comment posted!")
            else:
                # Try pressing Enter
                print("Pressing Enter...")
                await page.keyboard.press("Enter")
                await asyncio.sleep(4)

            await page.screenshot(path='repos_cache/ig_reel_comment_added.png')
            print("Screenshot saved to repos_cache/ig_reel_comment_added.png")
        else:
            print("Comment box not found")

        await browser.close()

if __name__ == '__main__':
    asyncio.run(add_comment())

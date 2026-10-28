# -*- coding: utf-8 -*-
import sys
import json
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

sys.stdout.reconfigure(encoding='utf-8')

async def check():
    raw_cookies = json.load(open('sessions/instagram_cookies.json', 'r', encoding='utf-8'))
    playwright_cookies = [{'name': c['name'], 'value': c['value'], 'domain': c['domain'], 'path': c.get('path', '/')} for c in raw_cookies]

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel='msedge', headless=True)
        ctx = await browser.new_context(viewport={'width': 1280, 'height': 800})
        await ctx.add_cookies(playwright_cookies)
        page = await ctx.new_page()
        await page.goto('https://www.instagram.com/smartstore.gcc/', wait_until='domcontentloaded', timeout=30000)
        await asyncio.sleep(4)

        # Look for links pointing to /p/ or /reel/
        post_link = page.locator('a[href*="/reel/"], a[href*="/p/"]').first
        if await post_link.count() > 0:
            href = await post_link.get_attribute('href')
            print('Post href:', href)
            await post_link.click()
            await asyncio.sleep(4)
            await page.screenshot(path='repos_cache/ig_post_modal.png')

            content = await page.inner_text('body')
            for line in content.splitlines():
                if any(k in line for k in ['trycloudflare', 'glamp', 'G-Lamp', 'مصباح', 'خصم', 'الطلب']):
                    print('Post line:', line.strip())
        else:
            print('No post link found')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check())

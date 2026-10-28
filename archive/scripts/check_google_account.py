import asyncio
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://accounts.google.com/signin")
        await page.wait_for_selector('input[type="email"]')
        await page.fill('input[type="email"]', "adhamfares319@gmail.com")
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(4000)
        content = await page.content()
        url = page.url
        print("Final URL:", url)
        if 'type="password"' in content or "password" in url.lower() or "challenge/pwd" in url.lower():
            print("STATUS: EXISTS (Asked for password)")
        elif "couldn't find" in content.lower() or "تعذر العثور" in content:
            print("STATUS: NOT_FOUND (Account does not exist yet)")
        else:
            print("STATUS: UNKNOWN / OTHER")
            page_text = await page.inner_text("body")
            print("Visible text summary:", page_text[:300].replace("\n", " "))
        await browser.close()

asyncio.run(check())

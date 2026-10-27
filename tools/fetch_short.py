import asyncio
import os
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()
        video_urls = []

        page.on("response", lambda res: video_urls.append(res.url) if ("googlevideo.com/videoplayback" in res.url) else None)

        print("Navigating to short...")
        try:
            await page.goto("https://www.youtube.com/shorts/ACoTLZrLyMM", wait_until="load", timeout=30000)
            await page.wait_for_timeout(3000)
        except Exception as e:
            print("Goto error:", e)

        # Handle cookie consent dialog
        for txt in ["Accept all", "Agree", "I agree", "Reject all", "قبول الكل", "أوافق"]:
            try:
                btn = page.locator(f"button:has-text('{txt}')").first
                if await btn.is_visible():
                    await btn.click()
                    print("Clicked consent button:", txt)
                    await page.wait_for_timeout(2000)
                    break
            except Exception:
                pass

        title = await page.title()
        print("Page Title:", title.encode("utf-8", "replace").decode("utf-8"))

        await page.screenshot(path=r"C:\Projects\adham-agent\workspace_data\media\yt_page.png")
        print("Saved screenshot to yt_page.png")

        # Wait for video to start playing and buffer streams
        await page.wait_for_timeout(6000)

        # Try to find video element
        video_el = page.locator("video").first
        try:
            if await video_el.is_visible():
                current_src = await video_el.evaluate("el => el.currentSrc || el.src")
                print("Video currentSrc found:", bool(current_src))
        except Exception as e:
            print("Video el error:", e)

        print(f"Intercepted {len(video_urls)} googlevideo URLs")
        if video_urls:
            with open(r"C:\Projects\adham-agent\workspace_data\media\googlevideo_urls.txt", "w", encoding="utf-8") as f:
                f.write("\n".join(video_urls))
            print("Saved googlevideo URLs to file.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())

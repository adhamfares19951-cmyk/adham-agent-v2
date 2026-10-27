"""Diagnostic script to inspect TikTok Studio Upload Page with existing session."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sessions" / "tiktok_user_data"
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

async def inspect():
    print("Launching Playwright with TikTok user data profile...")
    async with async_playwright() as p:
        try:
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(DATA_DIR),
                channel="msedge",
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"Edge launch failed ({e}), falling back to chromium...")
            ctx = await p.chromium.launch_persistent_context(
                user_data_dir=str(DATA_DIR),
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )

        page = await ctx.new_page()
        
        # 1. Test profile / auth
        print("Navigating to https://www.tiktok.com/@me ...")
        await page.goto("https://www.tiktok.com/@me", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)
        print("Page URL after @me:", page.url)
        print("Page Title:", await page.title())
        await page.screenshot(path=str(CACHE_DIR / "tiktok_me.png"))

        # 2. Test upload center
        upload_urls = [
            "https://www.tiktok.com/tiktokstudio/upload",
            "https://www.tiktok.com/creator-center/upload?from=upload",
            "https://www.tiktok.com/upload?lang=en"
        ]
        
        for u in upload_urls:
            print(f"\nTesting URL: {u}")
            try:
                resp = await page.goto(u, wait_until="domcontentloaded", timeout=45000)
                await asyncio.sleep(5)
                print(f"Landed at: {page.url} (Status: {resp.status if resp else 'N/A'})")
                print("Page Title:", await page.title())
                
                # Check for file input
                inputs = await page.query_selector_all('input[type="file"]')
                print(f"Found {len(inputs)} file input(s) in main page.")
                
                # Check frames
                print(f"Found {len(page.frames)} frame(s):")
                for idx, frame in enumerate(page.frames):
                    print(f"  Frame {idx}: name='{frame.name}', url='{frame.url[:80]}'")
                    f_inputs = await frame.query_selector_all('input[type="file"]')
                    if f_inputs:
                        print(f"  -> FOUND {len(f_inputs)} FILE INPUT(S) IN FRAME {idx}!")
                
                # Screenshot
                shot_name = f"tiktok_upload_test_{u.split('/')[-1][:12]}.png"
                await page.screenshot(path=str(CACHE_DIR / shot_name))
                print(f"Screenshot saved to: {shot_name}")
                
                # If we found file inputs, break
                if inputs or any(await f.query_selector_all('input[type="file"]') for f in page.frames):
                    print(f"SUCCESS: Upload interface confirmed active on {u}!")
                    break
            except Exception as ex:
                print(f"Error on {u}: {ex}")

        await ctx.close()

if __name__ == "__main__":
    asyncio.run(inspect())

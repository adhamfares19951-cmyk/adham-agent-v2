"""Step-by-step diagnostic test of TikTok Studio upload form."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "sessions" / "tiktok_user_data"
CACHE_DIR = BASE_DIR / "repos_cache"
VIDEO_PATH = BASE_DIR / "videos" / "subtitled_video_1792314383_1792314415.mp4"

async def test_upload_flow():
    if not VIDEO_PATH.exists():
        print(f"Video path {VIDEO_PATH} does not exist!")
        return

    print("Launching Edge with persistent context...")
    async with async_playwright() as p:
        ctx = await p.chromium.launch_persistent_context(
            user_data_dir=str(DATA_DIR),
            channel="msedge",
            headless=True,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )

        page = await ctx.new_page()
        print("Navigating to https://www.tiktok.com/tiktokstudio/upload ...")
        await page.goto("https://www.tiktok.com/tiktokstudio/upload", wait_until="domcontentloaded", timeout=45000)
        await asyncio.sleep(4)

        print("Locating attached file input (hidden or visible)...")
        file_input = await page.wait_for_selector('input[type="file"]', state="attached", timeout=30000)
        if not file_input:
            print("File input not found!")
            await ctx.close()
            return

        print(f"Attaching video file: {VIDEO_PATH.name} ({VIDEO_PATH.stat().st_size} bytes)...")
        await file_input.set_input_files(str(VIDEO_PATH))

        print("Waiting for upload UI to load (15 seconds)...")
        for s in range(1, 16):
            await asyncio.sleep(1)
            print(f"Elapsed: {s}s...")

        await page.screenshot(path=str(CACHE_DIR / "tiktok_uploaded_state.png"))
        print("Saved screenshot: tiktok_uploaded_state.png")

        # Inspect form elements
        print("\n--- Inspecting inputs / textareas / contenteditables ---")
        textareas = await page.query_selector_all('textarea')
        print(f"Found {len(textareas)} <textarea> element(s)")
        for idx, t in enumerate(textareas):
            placeholder = await t.get_attribute("placeholder") or ""
            classes = await t.get_attribute("class") or ""
            print(f"  textarea {idx}: placeholder='{placeholder}', class='{classes[:40]}'")

        editables = await page.query_selector_all('div[contenteditable="true"]')
        print(f"Found {len(editables)} contenteditable div(s)")
        for idx, e in enumerate(editables):
            text = (await e.text_content() or "").strip()
            classes = await e.get_attribute("class") or ""
            print(f"  editable {idx}: text='{text[:30]}', class='{classes[:40]}'")

        # Inspect buttons
        print("\n--- Inspecting buttons ---")
        buttons = await page.query_selector_all('button')
        print(f"Found {len(buttons)} <button> element(s)")
        for idx, b in enumerate(buttons):
            b_text = (await b.text_content() or "").strip()
            b_type = await b.get_attribute("type") or ""
            b_class = await b.get_attribute("class") or ""
            if any(k in b_text for k in ["نشر", "Post", "حفظ", "Save", "تجاهل", "Cancel", "تعديل"]):
                print(f"  Button {idx}: text='{b_text}', type='{b_type}', class='{b_class[:40]}'")

        await ctx.close()
        print("\nInspection complete!")

if __name__ == "__main__":
    asyncio.run(test_upload_flow())

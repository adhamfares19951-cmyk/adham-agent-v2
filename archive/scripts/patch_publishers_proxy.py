import re
from pathlib import Path

# Patch tiktok_publisher.py
tt_path = Path(r"C:\Projects\adham-agent\tools\tiktok_publisher.py")
tt_code = tt_path.read_text(encoding="utf-8")

old_snippet = """    from playwright.async_api import async_playwright

    log.info("Starting autonomous TikTok upload for: %s", v_path.name)
    async with async_playwright() as p:
        try:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=str(TIKTOK_DATA_DIR),
                channel="msedge",
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception:
            browser_context = await p.chromium.launch_persistent_context(
                user_data_dir=str(TIKTOK_DATA_DIR),
                headless=True,
                viewport={"width": 1280, "height": 900},
                args=["--disable-blink-features=AutomationControlled"]
            )"""

new_snippet = """    from playwright.async_api import async_playwright
    from core.proxy_manager import get_playwright_proxy_config

    proxy_config = get_playwright_proxy_config()
    if proxy_config:
        log.info("Using localized Gulf proxy for TikTok: %s", proxy_config.get("server"))

    log.info("Starting autonomous TikTok upload for: %s", v_path.name)
    async with async_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(TIKTOK_DATA_DIR),
            "headless": True,
            "viewport": {"width": 1280, "height": 900},
            "args": ["--disable-blink-features=AutomationControlled"],
        }
        if proxy_config:
            launch_kwargs["proxy"] = proxy_config

        try:
            browser_context = await p.chromium.launch_persistent_context(
                channel="msedge",
                **launch_kwargs
            )
        except Exception:
            browser_context = await p.chromium.launch_persistent_context(
                **launch_kwargs
            )"""

if old_snippet in tt_code:
    tt_code = tt_code.replace(old_snippet, new_snippet)
    tt_path.write_text(tt_code, encoding="utf-8")
    print("Patched tools/tiktok_publisher.py successfully")
else:
    # Try normalizing newlines
    tt_code_norm = tt_code.replace("\r\n", "\n")
    if old_snippet in tt_code_norm:
        tt_code_norm = tt_code_norm.replace(old_snippet, new_snippet)
        tt_path.write_text(tt_code_norm, encoding="utf-8")
        print("Patched tools/tiktok_publisher.py (with normalized newlines)")
    else:
        print("Snippet not found in tools/tiktok_publisher.py")

# Patch instagram_publisher.py
ig_path = Path(r"C:\Projects\adham-agent\tools\instagram_publisher.py")
ig_code = ig_path.read_text(encoding="utf-8")

old_ig = """    log.info("Starting autonomous Instagram Reel publishing for: %s", v_path.name)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        ctx = await browser.new_context(viewport={"width": 1280, "height": 900})"""

new_ig = """    from core.proxy_manager import get_playwright_proxy_config
    proxy_config = get_playwright_proxy_config()
    if proxy_config:
        log.info("Using localized Gulf proxy for Instagram: %s", proxy_config.get("server"))

    log.info("Starting autonomous Instagram Reel publishing for: %s", v_path.name)
    async with async_playwright() as p:
        launch_kwargs = {"headless": True}
        context_kwargs = {"viewport": {"width": 1280, "height": 900}}
        if proxy_config:
            context_kwargs["proxy"] = proxy_config

        try:
            browser = await p.chromium.launch(channel="msedge", **launch_kwargs)
        except Exception:
            browser = await p.chromium.launch(**launch_kwargs)
        ctx = await browser.new_context(**context_kwargs)"""

if old_ig in ig_code:
    ig_code = ig_code.replace(old_ig, new_ig)
    ig_path.write_text(ig_code, encoding="utf-8")
    print("Patched tools/instagram_publisher.py successfully")
else:
    ig_code_norm = ig_code.replace("\r\n", "\n")
    if old_ig in ig_code_norm:
        ig_code_norm = ig_code_norm.replace(old_ig, new_ig)
        ig_path.write_text(ig_code_norm, encoding="utf-8")
        print("Patched tools/instagram_publisher.py (with normalized newlines)")
    else:
        print("Snippet not found in tools/instagram_publisher.py")

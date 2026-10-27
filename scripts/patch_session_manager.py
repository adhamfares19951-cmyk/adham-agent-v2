# -*- coding: utf-8 -*-
"""Adds tiktok and snapchat to SUPPORTED_PLATFORMS in tools/session_manager.py."""
from pathlib import Path

p = Path("C:/Projects/adham-agent/tools/session_manager.py")
code = p.read_text(encoding="utf-8")

old_upwork = """    "upwork": {
        "name": "أب وورك (Upwork)",
        "domain": "upwork.com",
        "home_url": "https://www.upwork.com/nx/find-work/",
        "verify_url": "https://www.upwork.com/nx/find-work/",
        "login_indicators": ["my-jobs", "messages", "profile"],
    },
}"""

new_platforms = """    "upwork": {
        "name": "أب وورك (Upwork)",
        "domain": "upwork.com",
        "home_url": "https://www.upwork.com/nx/find-work/",
        "verify_url": "https://www.upwork.com/nx/find-work/",
        "login_indicators": ["my-jobs", "messages", "profile"],
    },
    "tiktok": {
        "name": "تيك توك (TikTok)",
        "domain": "tiktok.com",
        "home_url": "https://www.tiktok.com",
        "verify_url": "https://www.tiktok.com/tiktokstudio/content",
        "login_indicators": ["tiktokstudio", "upload", "profile", "logout"],
    },
    "snapchat": {
        "name": "سناب شات (Snapchat)",
        "domain": "snapchat.com",
        "home_url": "https://web.snapchat.com",
        "verify_url": "https://accounts.snapchat.com",
        "login_indicators": ["profile", "logout", "settings"],
    },
}"""

if old_upwork in code:
    code = code.replace(old_upwork, new_platforms)
    p.write_text(code, encoding="utf-8")
    print("SUCCESS: Added tiktok and snapchat to SUPPORTED_PLATFORMS!")
else:
    print("Target block not found in session_manager.py")

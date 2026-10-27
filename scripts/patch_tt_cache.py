# -*- coding: utf-8 -*-
"""Defines REPOS_CACHE in tools/tiktok_publisher.py."""
from pathlib import Path

p = Path("C:/Projects/adham-agent/tools/tiktok_publisher.py")
code = p.read_text(encoding="utf-8")

old_target = """TIKTOK_DATA_DIR = SESSIONS_DIR / "tiktok_user_data"
TIKTOK_DATA_DIR.mkdir(parents=True, exist_ok=True)"""

new_target = """TIKTOK_DATA_DIR = SESSIONS_DIR / "tiktok_user_data"
TIKTOK_DATA_DIR.mkdir(parents=True, exist_ok=True)
REPOS_CACHE = BASE_DIR / "repos_cache"
REPOS_CACHE.mkdir(parents=True, exist_ok=True)"""

if old_target in code:
    code = code.replace(old_target, new_target)
    p.write_text(code, encoding="utf-8")
    print("SUCCESS: Defined REPOS_CACHE in tools/tiktok_publisher.py!")

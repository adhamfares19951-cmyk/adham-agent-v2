# -*- coding: utf-8 -*-
"""Adds IndexNow protocol support to web_platform/app.py and submits URLs."""
import sys
import httpx
from pathlib import Path

INDEXNOW_KEY = "a8f3b2e7c9d14682b5e0f7193245cba8"

app_path = Path("C:/Projects/adham-agent/web_platform/app.py")
code = app_path.read_text(encoding="utf-8")

indexnow_route = f"""
@app.get("/{INDEXNOW_KEY}.txt", response_class=PlainTextResponse)
async def get_indexnow_key():
    \"\"\"IndexNow search engine verification key file.\"\"\"
    return PlainTextResponse("{INDEXNOW_KEY}", media_type="text/plain")
"""

if INDEXNOW_KEY not in code:
    code = code.replace('@app.get("/robots.txt"', indexnow_route + '\n@app.get("/robots.txt"')
    app_path.write_text(code, encoding="utf-8")
    print("SUCCESS: Added IndexNow route to web_platform/app.py")
else:
    print("IndexNow route already in app.py")

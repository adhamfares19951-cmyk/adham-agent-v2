# -*- coding: utf-8 -*-
"""Submits the live sitemap URL to Google, Bing, and search engine crawlers."""
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.stdout.reconfigure(encoding='utf-8')

import httpx
import memory

base_url = memory.get_setting('public_web_url') or "https://ministries-direct-specify-universe.trycloudflare.com"
sitemap_url = f"{base_url.rstrip('/')}/sitemap.xml"
print(f"Submitting sitemap: {sitemap_url}")

results = {}

# 1. Bing Ping
try:
    r_bing = httpx.get(f"https://www.bing.com/ping?sitemap={sitemap_url}", timeout=10)
    results["Bing"] = f"Status {r_bing.status_code}"
except Exception as e:
    results["Bing"] = f"Error: {e}"

# 2. Google Ping
try:
    r_google = httpx.get(f"https://www.google.com/ping?sitemap={sitemap_url}", timeout=10)
    results["Google"] = f"Status {r_google.status_code}"
except Exception as e:
    results["Google"] = f"Error: {e}"

for engine, status in results.items():
    print(f"[{engine}] Ping response: {status}")

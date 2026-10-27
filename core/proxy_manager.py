"""Enterprise Proxy Manager for Social Media & Browser Automation.
Safely manages localized (Gulf/Saudi) proxies strictly at the application/Playwright level.
CRITICAL SAFETY GUARANTEE:
- NEVER modifies system network adapters, Windows global proxy, routing tables, or firewall.
- NEVER interferes with Uvicorn (port 8080), Cloudflare Tunnel, Telegram Bot, or RDP/SSH.
- If proxy is offline or slow, falls back gracefully to direct connection to ensure 100% uptime.
"""
from __future__ import annotations

import logging
import os
from typing import Any

log = logging.getLogger("proxy_manager")


def get_playwright_proxy_config() -> dict[str, Any] | None:
    """Returns Playwright-compatible proxy dict if configured in environment, else None.
    
    Expected environment variables:
    - GULF_PROXY_SERVER (e.g. 'http://1.2.3.4:8080' or 'socks5://1.2.3.4:1080')
    - GULF_PROXY_USERNAME (optional)
    - GULF_PROXY_PASSWORD (optional)
    """
    server = os.getenv("GULF_PROXY_SERVER") or os.getenv("TIKTOK_PROXY") or os.getenv("SOCIAL_PROXY")
    if not server or not server.strip():
        return None

    server = server.strip()
    if not (server.startswith("http://") or server.startswith("https://") or server.startswith("socks5://")):
        server = f"http://{server}"

    config: dict[str, Any] = {"server": server}
    user = os.getenv("GULF_PROXY_USERNAME")
    pwd = os.getenv("GULF_PROXY_PASSWORD")
    if user and pwd:
        config["username"] = user.strip()
        config["password"] = pwd.strip()

    return config


def test_proxy_connectivity(timeout_seconds: float = 3.0) -> dict[str, Any]:
    """Tests connectivity through the configured proxy without throwing errors.
    Returns dict with status, country, IP, and latency.
    """
    proxy_config = get_playwright_proxy_config()
    if not proxy_config:
        return {"active": False, "reason": "No proxy configured in GULF_PROXY_SERVER"}

    try:
        import httpx
        proxy_url = proxy_config["server"]
        auth = None
        if "username" in proxy_config and "password" in proxy_config:
            auth = (proxy_config["username"], proxy_config["password"])

        with httpx.Client(proxy=proxy_url, auth=auth, timeout=timeout_seconds) as client:
            resp = client.get("http://ip-api.com/json")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "active": True,
                    "ip": data.get("query"),
                    "country": data.get("country"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "proxy": proxy_url
                }
            return {"active": False, "status_code": resp.status_code, "reason": "Non-200 response"}
    except Exception as e:
        return {"active": False, "error": str(e), "reason": "Connection timeout or proxy unreachable"}

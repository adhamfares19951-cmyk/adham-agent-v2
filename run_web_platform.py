"""Launcher for Adham Agent Enterprise Web Platform & Store.
Runs FastAPI via Uvicorn on 0.0.0.0:8080.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import uvicorn

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("web_platform_server")


def main():
    host = os.getenv("WEB_HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("WEB_PORT", "8080")))

    print("=" * 70)
    print("🚀 Starting Adham Agent Enterprise Web Platform & Store")
    print(f"📡 Local Access:    http://localhost:{port}")
    print(f"🌐 Network Access:  http://127.0.0.1:{port}")
    print("⚡ Solar Engine:    Deterministic Zero-Hallucination Active")
    print("🛒 Store Engine:    SQLite Live Sync with Telegram Approval Queue Active")
    print("=" * 70)

    uvicorn.run(
        "web_platform.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()

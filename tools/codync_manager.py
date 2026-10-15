"""Codync Integration & Server Relay Manager.
Enables Adham to connect and control coding AI agents (Claude Code, Codex, Cursor, Gemini)
from his iPhone, desktop, or terminal via encrypted Cloudflare relay.
"""
from __future__ import annotations

import logging
import os
import urllib.request
from pathlib import Path
from typing import Any

log = logging.getLogger("codync_manager")

BASE_DIR = Path(__file__).resolve().parent.parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)

CODYNC_WINDOWS_URL = "https://github.com/leepokai/Codync/releases/latest/download/codync-windows-x64.exe"
CODYNC_LINUX_CMD = "curl -fsSL https://raw.githubusercontent.com/leepokai/Codync/main/packaging/install.sh | sh -s -- --host-only"
CODYNC_IOS_URL = "https://apps.apple.com/app/codync/id6760984418"


def get_codync_setup_info() -> dict[str, Any]:
    """Returns complete configuration, direct downloads, and pairing steps for Codync."""
    return {
        "status": "ready",
        "description": "Codync is an open-source Rust agent host and relay for controlling AI coding agents remotely.",
        "platforms": {
            "windows": {
                "installer_url": CODYNC_WINDOWS_URL,
                "notes": "Run the installer, click More Info -> Run Anyway (SmartScreen), then open tray icon and click Pair iPhone."
            },
            "linux_server": {
                "one_line_install": CODYNC_LINUX_CMD,
                "pair_command": "codync-host pair",
                "notes": "Runs headless on your Linux VPS / Coolify server. No port forwarding needed (Cloudflare E2EE relay is built-in)."
            },
            "ios_app": {
                "app_store_url": CODYNC_IOS_URL,
                "requirements": "iOS 18+, free download."
            }
        },
        "features": [
            "Team channels with multiple AI bots (Coder, Reviewer, DevOps)",
            "End-to-End encrypted relay with zero configuration",
            "Remote computer screen streaming (WebRTC)",
            "Voice conversations with coding agents",
            "Approval cards before any file edits or bash commands"
        ]
    }


def download_codync_windows_client(target_path: str | None = None) -> str:
    """Downloads the official Codync Windows x64 executable."""
    dest = Path(target_path) if target_path else DOWNLOADS_DIR / "codync-windows-x64.exe"
    if dest.exists() and dest.stat().st_size > 10 * 1024 * 1024:
        return f"File already downloaded at: {dest.resolve()} ({dest.stat().st_size / (1024*1024):.1f} MB)"

    log.info("Downloading Codync Windows installer from %s ...", CODYNC_WINDOWS_URL)
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(CODYNC_WINDOWS_URL, headers=headers)
    with urllib.request.urlopen(req) as response, open(dest, "wb") as out_file:
        while chunk := response.read(64 * 1024):
            out_file.write(chunk)

    return f"Codync downloaded successfully to: {dest.resolve()} ({dest.stat().st_size / (1024*1024):.1f} MB)"


async def _handle_get_codync_setup(args: dict) -> str:
    import json
    info = get_codync_setup_info()
    return (
        f"🚀 **دليل ومعلومات إعداد Codync للتحكم بالبوتات عن بعد:**\n\n"
        f"```json\n{json.dumps(info, ensure_ascii=False, indent=2)}\n```\n\n"
        f"📌 **أمر التثبيت على سيرفر لينكس بلمسة واحدة:**\n"
        f"`curl -fsSL https://raw.githubusercontent.com/leepokai/Codync/main/packaging/install.sh | sh -s -- --host-only`\n\n"
        f"📌 **أمر الربط مع الآيفون وإظهار الـ QR Code:**\n"
        f"`codync-host pair`"
    )


async def _handle_download_codync(args: dict) -> str:
    res = download_codync_windows_client(args.get("target_path"))
    return f"✅ {res}"


TOOLS = [
    {
        "name": "get_codync_setup_info",
        "description": "الحصول على روابط وإرشادات وأوامر تشغيل Codync على الويندوز وسيرفرات لينكس وتطبيق الآيفون للتحكم بالـ AI Agents عن بعد.",
        "parameters": {"type": "object", "properties": {}},
        "handler": _handle_get_codync_setup,
    },
    {
        "name": "download_codync_windows_client",
        "description": "تنزيل برنامج Codync الرسمي لنظام ويندوز 64-بت محلياً للربط مع الآيفون.",
        "parameters": {
            "type": "object",
            "properties": {
                "target_path": {"type": "string", "description": "المسار الاختياري لحفظ الملف"}
            }
        },
        "handler": _handle_download_codync,
    },
]


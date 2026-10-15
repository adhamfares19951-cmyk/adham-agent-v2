"""Cloudflare Public Tunnel Manager for adham-agent.
Allows instant exposure of local services (such as lead-preview-bot on port 8000
or Shamel web previews) to the public internet via encrypted HTTPS TryCloudflare tunnels.
Zero configuration, zero port forwarding, works on Windows and Linux.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

log = logging.getLogger("cloud_tunnel")

BASE_DIR = Path(__file__).resolve().parent.parent
BIN_DIR = BASE_DIR / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS_EXE_NAME = "cloudflared.exe"
CLOUDFLARED_PATH = BIN_DIR / WINDOWS_EXE_NAME
CLOUDFLARED_DOWNLOAD_URL = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"

# Global state for active tunnel
_TUNNEL_PROC: subprocess.Popen | None = None
_TUNNEL_URL: str | None = None
_TUNNEL_PORT: int | None = None


def _get_cloudflared_executable() -> str:
    """Finds or downloads cloudflared binary."""
    # 1. Check system PATH
    sys_path = shutil.which("cloudflared")
    if sys_path:
        return sys_path

    # 2. Check local bin directory
    if CLOUDFLARED_PATH.exists() and CLOUDFLARED_PATH.stat().st_size > 10 * 1024 * 1024:
        return str(CLOUDFLARED_PATH.resolve())

    # 3. Download standalone Windows binary
    log.info("Downloading cloudflared standalone binary to %s ...", CLOUDFLARED_PATH)
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(CLOUDFLARED_DOWNLOAD_URL, headers=headers)
    with urllib.request.urlopen(req) as resp, open(CLOUDFLARED_PATH, "wb") as f:
        while chunk := resp.read(128 * 1024):
            f.write(chunk)

    log.info("cloudflared downloaded successfully (%d bytes)", CLOUDFLARED_PATH.stat().st_size)
    return str(CLOUDFLARED_PATH.resolve())


async def start_public_tunnel(port: int = 8000) -> dict[str, Any]:
    """Starts a public HTTPS tunnel for the given local port and returns the public URL."""
    global _TUNNEL_PROC, _TUNNEL_URL, _TUNNEL_PORT

    # Check if already running on the same port
    if _TUNNEL_PROC and _TUNNEL_PROC.poll() is None and _TUNNEL_URL:
        if _TUNNEL_PORT == port:
            return {
                "status": "already_running",
                "public_url": _TUNNEL_URL,
                "local_port": _TUNNEL_PORT,
                "message": f"النفق يعمل مسبقاً على البورت {port} بالرابط: {_TUNNEL_URL}"
            }
        else:
            stop_public_tunnel()

    binary = await asyncio.to_thread(_get_cloudflared_executable)
    cmd = [binary, "tunnel", "--url", f"http://localhost:{port}"]

    log.info("Spawning cloudflared: %s", " ".join(cmd))
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        encoding="utf-8",
        errors="replace"
    )

    _TUNNEL_PROC = proc
    _TUNNEL_PORT = port
    _TUNNEL_URL = None

    # Parse stderr for trycloudflare.com URL
    url_pattern = re.compile(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com")
    start_time = time.time()
    discovered_url = None

    # Give up to 15 seconds for cloudflare to assign public tunnel URL
    while time.time() - start_time < 15:
        if proc.poll() is not None:
            err = proc.stderr.read() if proc.stderr else "Unknown error"
            raise RuntimeError(f"Cloudflared exited prematurely: {err}")

        line = await asyncio.to_thread(proc.stderr.readline)
        if line:
            match = url_pattern.search(line)
            if match:
                discovered_url = match.group(0)
                break
        await asyncio.sleep(0.2)

    if not discovered_url:
        proc.kill()
        _TUNNEL_PROC = None
        raise TimeoutError("فشل العثور على رابط Cloudflare Tunnel خلال 15 ثانية.")

    _TUNNEL_URL = discovered_url
    log.info("Public tunnel established: %s -> http://localhost:%d", _TUNNEL_URL, port)

    return {
        "status": "success",
        "public_url": _TUNNEL_URL,
        "local_port": port,
        "preview_example": f"{_TUNNEL_URL}/p/example-slug",
        "message": f"تم فتح النفق بنجاح! الرابط العام:\n{_TUNNEL_URL}"
    }


def stop_public_tunnel() -> dict[str, Any]:
    """Stops the active public tunnel if any."""
    global _TUNNEL_PROC, _TUNNEL_URL, _TUNNEL_PORT

    if not _TUNNEL_PROC or _TUNNEL_PROC.poll() is not None:
        _TUNNEL_PROC = None
        _TUNNEL_URL = None
        _TUNNEL_PORT = None
        return {"status": "inactive", "message": "لا يوجد نفق نشط لإيقافه حالياً."}

    old_url = _TUNNEL_URL
    try:
        _TUNNEL_PROC.terminate()
        _TUNNEL_PROC.wait(timeout=3)
    except Exception:
        try:
            _TUNNEL_PROC.kill()
        except Exception:
            pass

    _TUNNEL_PROC = None
    _TUNNEL_URL = None
    _TUNNEL_PORT = None

    return {"status": "stopped", "message": f"تم إيقاف النفق السحابي بنجاح ({old_url})."}


def get_tunnel_status() -> dict[str, Any]:
    """Returns the current tunnel state."""
    global _TUNNEL_PROC, _TUNNEL_URL, _TUNNEL_PORT

    if _TUNNEL_PROC and _TUNNEL_PROC.poll() is None and _TUNNEL_URL:
        return {
            "status": "active",
            "public_url": _TUNNEL_URL,
            "local_port": _TUNNEL_PORT,
            "pid": _TUNNEL_PROC.pid
        }
    return {
        "status": "inactive",
        "public_url": None,
        "local_port": None
    }


async def _handle_start_tunnel(args: dict) -> str:
    port = int(args.get("port", 8000))
    res = await start_public_tunnel(port)
    return (
        f"🌐 **تم إطلاق النفق السحابي العام (Cloudflare Tunnel)!**\n\n"
        f"🔗 **الرابط العام المباشر:**\n{res['public_url']}\n\n"
        f"📍 **المسار المحلي:** `http://localhost:{res['local_port']}`\n"
        f"💡 **رابط المعاينة لأصحاب المحلات:**\n`{res['public_url']}/p/slug-name`\n\n"
        f"يمكنك إرسال هذا الرابط للزبائن على الواتساب فوراً وسيفتح معهم كأنه موقع حقيقي على الإنترنت!"
    )


async def _handle_stop_tunnel(args: dict) -> str:
    res = stop_public_tunnel()
    return f"🛑 {res['message']}"


async def _handle_status_tunnel(args: dict) -> str:
    res = get_tunnel_status()
    if res["status"] == "active":
        return f"✅ **النفق السحابي نشط حالياً:**\n- الرابط: {res['public_url']}\n- البورت المحلي: {res['local_port']}"
    return "⚪ لا يوجد نفق سحابي نشط حالياً."


TOOLS = [
    {
        "name": "start_public_tunnel",
        "description": "فتح نفق سحابي مشفر وآمن وفوري (Cloudflare Tunnel) لنشر مشاريعك المحلية (مثل نظام المعاينات بورت 8000) برابط HTTPS عام للزبائن.",
        "parameters": {
            "type": "object",
            "properties": {
                "port": {"type": "integer", "description": "رقم البورت المحلي المراد فتحه (الافتراضي 8000)"}
            }
        },
        "handler": _handle_start_tunnel,
    },
    {
        "name": "stop_public_tunnel",
        "description": "إيقاف النفق السحابي العام النشط وإغلاق الرابط.",
        "parameters": {"type": "object", "properties": {}},
        "handler": _handle_stop_tunnel,
    },
    {
        "name": "get_tunnel_status",
        "description": "فحص حالة النفق السحابي العام ومعرفة الرابط النشط والبورت.",
        "parameters": {"type": "object", "properties": {}},
        "handler": _handle_status_tunnel,
    },
]

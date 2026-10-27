"""Cloudflare Tunnel Manager for Adham Agent Enterprise OS.
Provides:
1. Automated binary detection and download (cloudflared-windows-amd64.exe) to bin/cloudflared.exe.
2. Quick Tunnel and Named Tunnel (via CLOUDFLARE_TUNNEL_TOKEN) orchestration for port 8080.
3. Asynchronous log inspection and public URL extraction (https://xxxx.trycloudflare.com).
4. State persistence in agent_memory.db and instant Telegram notifications to OWNER_ID.
5. Integration with Agency OS Watchdog, marketing pitches, and Telegram /panel.
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

import httpx

import config
import memory

log = logging.getLogger("core.tunnel_manager")

BASE_DIR = getattr(config, "BASE_DIR", Path(__file__).resolve().parent.parent)
BIN_DIR = BASE_DIR / "bin"
BIN_DIR.mkdir(parents=True, exist_ok=True)

WINDOWS_EXE_NAME = "cloudflared.exe"
CLOUDFLARED_PATH = BIN_DIR / WINDOWS_EXE_NAME
CLOUDFLARED_DOWNLOAD_URL = (
    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
)

# Regex matching official Cloudflare Quick Tunnel and Argo Tunnel URLs
TUNNEL_URL_REGEX = re.compile(r"https://[a-zA-Z0-9-]+\.(?:trycloudflare|cfargotunnel)\.com")


class TunnelManager:
    """Orchestrates Cloudflare Tunnels with auto-download, URL discovery, and Telegram alerts."""

    def __init__(self, default_port: int = 8080) -> None:
        self.default_port = default_port
        self._proc: subprocess.Popen | None = None
        self._current_url: str | None = None
        self._local_port: int = default_port
        self._start_time: float = 0.0
        self._lock = asyncio.Lock()

    def get_cloudflared_executable(self) -> str:
        """Finds cloudflared executable in PATH or bin/, or downloads it automatically."""
        # 1. System PATH
        which_path = shutil.which("cloudflared")
        if which_path:
            return which_path

        # 2. Local project bin directory
        if CLOUDFLARED_PATH.exists() and CLOUDFLARED_PATH.stat().st_size > 10 * 1024 * 1024:
            return str(CLOUDFLARED_PATH.resolve())

        # 3. Download standalone Windows release
        log.info("Downloading cloudflared.exe to %s...", CLOUDFLARED_PATH)
        headers = {"User-Agent": "AdhamAgent-EnterpriseOS/2.0"}
        req = urllib.request.Request(CLOUDFLARED_DOWNLOAD_URL, headers=headers)
        with urllib.request.urlopen(req) as resp, open(CLOUDFLARED_PATH, "wb") as f:
            while chunk := resp.read(1024 * 1024):
                f.write(chunk)

        log.info("cloudflared.exe downloaded successfully (%d bytes)", CLOUDFLARED_PATH.stat().st_size)
        return str(CLOUDFLARED_PATH.resolve())

    def get_public_url(self) -> str:
        """Returns the active public URL from memory or SQLite storage."""
        if self._current_url:
            return self._current_url
        try:
            stored = memory.get_setting("public_web_url", "")
            if stored and stored.startswith("https://"):
                return stored
        except Exception:
            pass
        return ""

    async def send_tunnel_telegram_alert(self, public_url: str, port: int) -> bool:
        """Sends an instant formatted alert to Adham's Telegram when the public tunnel is ready."""
        token = getattr(config, "TELEGRAM_TOKEN", None)
        owner_id = getattr(config, "OWNER_ID", None)
        if not token or not owner_id:
            log.warning("Telegram notification skipped: TELEGRAM_TOKEN or OWNER_ID not set.")
            return False

        text = (
            "🚀 **تم تشغيل نفق Cloudflare ونشر المنصة الإلكترونية عالمياً!**\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🌐 **الرابط الخارجي المباشر (Public URL):**\n"
            f"{public_url}\n\n"
            f"📡 **المنفذ المحلي:** `http://127.0.0.1:{port}`\n"
            "🛡️ **الحماية:** تشفير HTTPS آمن وسريع عبر شبكة Cloudflare العالمية\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "*(تم حفظ الرابط وتحديثه تلقائياً في المتجر ورسائل صيد العملاء)*"
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "🔗 فتح المنصة الإلكترونية الآن", "url": public_url}],
            ]
        }

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id": owner_id,
                        "text": text,
                        "parse_mode": "Markdown",
                        "reply_markup": keyboard,
                        "disable_web_page_preview": False,
                    },
                )
                return resp.status_code == 200
        except Exception as e:
            log.warning("Failed to send tunnel Telegram alert: %s", e)
            return False

    async def start_tunnel(self, port: int | None = None, wait_seconds: int = 15) -> dict[str, Any]:
        """Spawns cloudflared, captures public URL via regex, persists state, and alerts Telegram."""
        async with self._lock:
            port = port or self.default_port

            # If already running on same port with valid URL, return immediately
            if self._proc and self._proc.poll() is None and self._current_url:
                if self._local_port == port:
                    return {
                        "status": "already_running",
                        "public_url": self._current_url,
                        "local_port": port,
                        "message": f"النفق يعمل مسبقاً بالرابط: {self._current_url}",
                    }
                else:
                    self.stop_tunnel()

            binary = await asyncio.to_thread(self.get_cloudflared_executable)
            named_token = getattr(config, "CLOUDFLARE_TUNNEL_TOKEN", None) or os.getenv("CLOUDFLARE_TUNNEL_TOKEN")

            if named_token:
                cmd = [binary, "tunnel", "run", "--token", named_token]
            else:
                cmd = [binary, "tunnel", "--url", f"http://127.0.0.1:{port}"]

            log.info("Starting cloudflared process: %s", " ".join(cmd))
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )

            self._proc = proc
            self._local_port = port
            self._current_url = None
            self._start_time = time.time()

            discovered_url = None
            start_time = time.time()

            # Poll stderr/stdout for public URL
            while time.time() - start_time < wait_seconds:
                if proc.poll() is not None:
                    err_out = proc.stderr.read() if proc.stderr else "Unknown error"
                    log.error("cloudflared process exited unexpectedly (code: %s): %s", proc.returncode, err_out)
                    return {
                        "status": "error",
                        "message": f"توقف خادم النفق برمز ({proc.returncode}): {err_out[:200]}",
                    }

                # Non-blocking line check
                line = await asyncio.to_thread(proc.stderr.readline)
                if line:
                    match = TUNNEL_URL_REGEX.search(line)
                    if match:
                        discovered_url = match.group(0)
                        break
                await asyncio.sleep(0.1)

            if discovered_url:
                self._current_url = discovered_url
                # Persist in SQLite
                try:
                    memory.set_setting("public_web_url", discovered_url)
                    memory.set_setting("public_tunnel_active", "1")
                except Exception as e:
                    log.warning("Could not persist tunnel URL in settings: %s", e)

                log.info("Cloudflare Tunnel active: %s -> http://127.0.0.1:%d", discovered_url, port)
                # Dispatch alert to Adham's Telegram
                asyncio.create_task(self.send_tunnel_telegram_alert(discovered_url, port))

                return {
                    "status": "active",
                    "public_url": discovered_url,
                    "local_port": port,
                    "uptime_seconds": round(time.time() - self._start_time, 1),
                }

            return {
                "status": "timeout",
                "message": f"لم يتم التقاط الرابط العام خلال {wait_seconds} ثانية. قد يكون جاري الاتصال.",
            }

    def stop_tunnel(self) -> bool:
        """Terminates the running cloudflared process cleanly."""
        if self._proc and self._proc.poll() is None:
            log.info("Stopping cloudflared tunnel (PID: %s)...", self._proc.pid)
            try:
                self._proc.terminate()
                self._proc.wait(timeout=5)
            except Exception:
                self._proc.kill()
        self._proc = None
        self._current_url = None
        try:
            memory.set_setting("public_tunnel_active", "0")
        except Exception:
            pass
        return True

    async def restart_tunnel(self, port: int | None = None) -> dict[str, Any]:
        """Restarts the tunnel and retrieves a fresh public URL."""
        self.stop_tunnel()
        await asyncio.sleep(1.0)
        return await self.start_tunnel(port=port)

    def get_status(self) -> dict[str, Any]:
        """Returns the current operational status of the tunnel."""
        is_running = self._proc is not None and self._proc.poll() is None
        pub_url = self.get_public_url()
        return {
            "is_running": is_running,
            "public_url": pub_url if is_running else "",
            "local_port": self._local_port,
            "pid": self._proc.pid if is_running else None,
            "uptime_seconds": round(time.time() - self._start_time, 1) if is_running else 0,
        }

    def run_blocking(self, port: int = 8080) -> None:
        """Runs the tunnel in blocking mode for supervisor/daemon execution."""
        binary = self.get_cloudflared_executable()
        named_token = getattr(config, "CLOUDFLARE_TUNNEL_TOKEN", None) or os.getenv("CLOUDFLARE_TUNNEL_TOKEN")

        if named_token:
            cmd = [binary, "tunnel", "run", "--token", named_token]
        else:
            cmd = [binary, "tunnel", "--url", f"http://127.0.0.1:{port}"]

        log.info("Starting blocking tunnel: %s", " ".join(cmd))
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
        )
        self._proc = proc
        self._local_port = port
        self._start_time = time.time()

        def _cleanup(*_):
            proc.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, _cleanup)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, _cleanup)

        # Read stderr line by line to capture URL and forward logs
        while proc.poll() is None:
            line = proc.stderr.readline()
            if not line:
                time.sleep(0.1)
                continue
            line_str = line.strip()
            match = TUNNEL_URL_REGEX.search(line_str)
            if match and not self._current_url:
                url = match.group(0)
                self._current_url = url
                try:
                    memory.set_setting("public_web_url", url)
                    memory.set_setting("public_tunnel_active", "1")
                except Exception:
                    pass
                log.info(">>> Public Cloudflare Tunnel Ready: %s <<<", url)
                asyncio.run(self.send_tunnel_telegram_alert(url, port))


# ==============================================================================
# Global Singleton
# ==============================================================================

_TUNNEL_INSTANCE: TunnelManager | None = None


def get_tunnel_manager() -> TunnelManager:
    """Returns the shared TunnelManager singleton."""
    global _TUNNEL_INSTANCE
    if _TUNNEL_INSTANCE is None:
        _TUNNEL_INSTANCE = TunnelManager(default_port=8080)
    return _TUNNEL_INSTANCE


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    port = int(os.getenv("PORT", os.getenv("WEB_PORT", "8080")))
    tm = get_tunnel_manager()
    tm.run_blocking(port=port)

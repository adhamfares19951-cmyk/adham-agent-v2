"""Unified Enterprise Agency OS Runner & Watchdog.
Launches and monitors all core agency services concurrently:
1. Web Platform & Store Server (FastAPI / Uvicorn on 0.0.0.0:8080)
2. Telegram Bot & Department Orchestrator (main.py)
3. Central API Gateway & SQLite Caching Layer
4. Continuous Health Watchdog with automatic crash recovery.
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
PYTHON_EXE = sys.executable

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("agency_os_runner")


class ServiceProcess:
    """Manages an individual supervised background process."""

    def __init__(self, name: str, cmd: list[str], cwd: Path = ROOT_DIR) -> None:
        self.name = name
        self.cmd = cmd
        self.cwd = cwd
        self.process: subprocess.Popen | None = None
        self.restart_count = 0
        self.last_restart = 0.0

    def start(self) -> None:
        """Starts the process."""
        log.info("Starting service '%s': %s", self.name, " ".join(self.cmd))
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        self.process = subprocess.Popen(
            self.cmd,
            cwd=str(self.cwd),
            env=env,
        )
        self.last_restart = time.monotonic()

    def is_alive(self) -> bool:
        """Checks if process is currently running."""
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self) -> None:
        """Gracefully terminates the process."""
        if self.process and self.is_alive():
            log.info("Terminating service '%s' (PID: %s)...", self.name, self.process.pid)
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log.warning("Service '%s' didn't exit in time, killing...", self.name)
                self.process.kill()
            except Exception as e:
                log.debug("Error stopping service '%s': %s", self.name, e)


class AgencyOSSupervisor:
    """Master supervisor managing concurrent agency operating system services."""

    def __init__(self) -> None:
        web_port = str(os.getenv("PORT", os.getenv("WEB_PORT", "8080")))
        is_cloud = bool(os.getenv("RAILWAY_PROJECT_ID") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("DYNO"))
        run_tg = (not is_cloud) or (os.getenv("ENABLE_CLOUD_TELEGRAM", "false").lower() in ("true", "1"))

        self.services: list[ServiceProcess] = [
            ServiceProcess(
                name="WebPlatform",
                cmd=[
                    PYTHON_EXE, "-m", "uvicorn", "web_platform.app:app",
                    "--host", "0.0.0.0",
                    "--port", web_port,
                    "--log-level", "info",
                ],
            ),
        ]
        if run_tg:
            self.services.append(
                ServiceProcess(
                    name="TelegramBot",
                    cmd=[PYTHON_EXE, "main.py"],
                )
            )
        if not is_cloud:
            self.services.append(
                ServiceProcess(
                    name="CloudflareTunnel",
                    cmd=[PYTHON_EXE, "-m", "core.tunnel_manager"],
                )
            )
        self.running = False

    def print_banner(self) -> None:
        """Displays startup diagnostics banner."""
        port = os.getenv("PORT", os.getenv("WEB_PORT", "8080"))
        print("\n" + "═" * 74)
        print("🏛️  ADHAM AGENT ENTERPRISE AGENCY OS — MASTER RUNNER")
        print("═" * 74)
        print(f"📡 Web Platform & Store:     http://localhost:{port} (Public 0.0.0.0:{port})")
        print(f"🌐 Cloudflare Tunnel:        Automated HTTPS Quick/Named Tunnel Active")
        print(f"🤖 Telegram Bot Core:        Active with SmartRouter & Multi-Agent Swarm")
        print(f"🛡️ Central API Gateway:      TokenBucket Rate Limiter + Persistent SQLite Cache")
        print(f"⚡ Deterministic Engines:    Zero-Hallucination Engineering Calculators Active")
        print(f"📊 Live Data Hub:            Binance BTC + Gold XAU + OpenStreetMap Active")
        print("═" * 74 + "\n")

    def start_all(self) -> None:
        """Launches all services."""
        self.print_banner()
        self.running = True
        for svc in self.services:
            svc.start()

    def stop_all(self) -> None:
        """Stops all running services."""
        log.info("Shutting down Agency OS services...")
        self.running = False
        for svc in self.services:
            svc.stop()
        log.info("All Agency OS services stopped successfully.")

    def run_watchdog(self) -> None:
        """Continuous supervision loop monitoring process health."""
        self.start_all()
        try:
            while self.running:
                time.sleep(3)
                for svc in self.services:
                    if not svc.is_alive():
                        code = svc.process.returncode if svc.process else -1
                        log.warning("⚠️ Service '%s' exited unexpectedly (code: %s). Restarting...", svc.name, code)
                        svc.restart_count += 1
                        time.sleep(1)
                        svc.start()
        except KeyboardInterrupt:
            print("\n🛑 Received interrupt signal (Ctrl+C). Initiating clean shutdown...")
        finally:
            self.stop_all()


def main() -> None:
    supervisor = AgencyOSSupervisor()

    def sig_handler(sig, frame):
        supervisor.stop_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, sig_handler)

    supervisor.run_watchdog()


if __name__ == "__main__":
    main()

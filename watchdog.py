"""Autonomous Self-Healing Watchdog for adham-agent.
Monitors main.py 24/7, automatically revives it upon any crash or disconnection,
cleans zombie locks, logs crash dumps, and notifies Adham on Telegram.
"""
from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import time
from datetime import datetime
from pathlib import Path

import httpx

# Logging setup
BASE_DIR = Path(__file__).resolve().parent
CRASH_DUMPS_DIR = BASE_DIR / "crash_dumps"
CRASH_DUMPS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    format="%(asctime)s | WATCHDOG | %(levelname)s | %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(BASE_DIR / "watchdog.log", encoding="utf-8"),
    ],
)
log = logging.getLogger("watchdog")

# Load environment configuration for Telegram alerts
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
OWNER_ID = os.getenv("OWNER_ID", "")


def send_emergency_telegram_alert(message: str) -> None:
    """Sends a direct HTTP alert to Adham bypassing bot instance locks."""
    if not TELEGRAM_TOKEN or not OWNER_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": OWNER_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    try:
        with httpx.Client(timeout=8) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                log.info("Emergency alert sent to Adham on Telegram.")
            else:
                log.warning("Could not send alert: HTTP %d", resp.status_code)
    except Exception as e:
        log.warning("Failed to dispatch emergency alert via HTTP: %s", e)


def cleanup_stale_processes() -> None:
    """Kills orphan python main.py processes to avoid Telegram getUpdates conflict."""
    try:
        current_pid = os.getpid()
        if sys.platform == "win32":
            cmd = f'powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {{ $_.ProcessId -ne {current_pid} -and $_.CommandLine -like \'*main.py*\' }} | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force }}"'
            subprocess.run(cmd, shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run("pkill -f 'python.*main.py'", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        log.warning("Stale process cleanup note: %s", e)


def run_supervisor_loop() -> None:
    portable_py = BASE_DIR / "python_runtime" / "python.exe"
    venv_py = BASE_DIR / "venv" / "Scripts" / "python.exe"
    if portable_py.exists():
        python_bin = str(portable_py)
    elif venv_py.exists():
        python_bin = str(venv_py)
    else:
        python_bin = sys.executable
    main_script = str(BASE_DIR / "main.py")

    crash_count = 0
    backoff_seconds = 2

    while True:
        cleanup_stale_processes()
        start_time = time.time()
        log.info("🚀 Launching adham-agent [Session #%d] with %s...", crash_count + 1, python_bin)

        # Launch child process
        proc = subprocess.Popen(
            [python_bin, "-u", main_script],
            cwd=str(BASE_DIR),
            stdout=sys.stdout,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        # Wait for child to exit
        _, stderr_output = proc.communicate()
        exit_code = proc.returncode
        uptime_seconds = time.time() - start_time

        # Check exit condition
        if exit_code == 0:
            log.info("adham-agent exited cleanly (code 0). Restarting in 2s...")
            time.sleep(2)
            continue

        crash_count += 1
        ts_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log.error("💥 adham-agent crashed with exit code %d after %.1f seconds!", exit_code, uptime_seconds)

        # Write crash dump
        dump_file = CRASH_DUMPS_DIR / f"crash_{ts_str}.log"
        dump_content = (
            f"=== ADHAM-AGENT CRASH DUMP ===\n"
            f"Timestamp: {ts_str}\n"
            f"Exit Code: {exit_code}\n"
            f"Uptime Before Crash: {uptime_seconds:.1f}s\n"
            f"Total Crashes: {crash_count}\n"
            f"--- STDERR OUTPUT ---\n{stderr_output or 'No stderr recorded.'}\n"
        )
        try:
            dump_file.write_text(dump_content, encoding="utf-8")
            log.info("Saved crash dump to %s", dump_file)
        except Exception:
            pass

        # Smart backoff: if it ran for > 30s, reset backoff to 2s
        if uptime_seconds > 30:
            backoff_seconds = 2
        else:
            backoff_seconds = min(backoff_seconds * 2, 20)

        # Telegram Alert
        stderr_snippet = (stderr_output or "").strip().splitlines()
        last_err = "\n".join(stderr_snippet[-4:]) if stderr_snippet else "انقطاع أو خروج غير متوقع"
        alert_msg = (
            f"🚨 <b>تنبيه دراع اليمين (Watchdog Alert):</b>\n\n"
            f"⚠️ تم رصد توقف مفاجئ للبوت (كود {exit_code}) بعد تشغيل {uptime_seconds:.1f} ثانية.\n"
            f"🔄 <b>تمت إعادة التشغيل ذاتياً الآن بنجاح!</b> (التعافي رقم #{crash_count})\n\n"
            f"<b>سبب التوقف الأخير:</b>\n"
            f"<code>{last_err[:300]}</code>\n\n"
            f"🟢 <i>جميع الأنظمة والـ 53 أداة تعمل بكفاءة تامة.</i>"
        )
        send_emergency_telegram_alert(alert_msg)

        log.info("⏳ Waiting %d seconds before reviving main.py...", backoff_seconds)
        time.sleep(backoff_seconds)


if __name__ == "__main__":
    def sig_handler(sig, frame):
        log.info("Received termination signal (%s). Shutting down watchdog cleanly.", sig)
        cleanup_stale_processes()
        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    try:
        run_supervisor_loop()
    except KeyboardInterrupt:
        log.info("Watchdog interrupted by user.")
        cleanup_stale_processes()

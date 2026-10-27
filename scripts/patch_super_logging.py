import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

# 1. Patch run_agency_os.py
os_file = Path(r"C:\Projects\adham-agent\run_agency_os.py")
os_text = os_file.read_text(encoding="utf-8")

old_services = """        self.services: list[ServiceProcess] = [
            ServiceProcess(
                name="WebPlatform",
                cmd=[
                    PYTHON_EXE, "-m", "uvicorn", "web_platform.app:app",
                    "--host", "0.0.0.0",
                    "--port", web_port,
                    "--log-level", "info",
                ],
            ),
            ServiceProcess(
                name="TelegramBot",
                cmd=[PYTHON_EXE, "main.py"],
            ),
            ServiceProcess(
                name="CloudflareTunnel",
                cmd=[PYTHON_EXE, "-m", "core.tunnel_manager"],
            ),
        ]"""

new_services = """        is_cloud = bool(os.getenv("RAILWAY_PROJECT_ID") or os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RENDER") or os.getenv("DYNO"))
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
            )"""

if old_services in os_text:
    os_text = os_text.replace(old_services, new_services, 1)
    os_file.write_text(os_text, encoding="utf-8")
    print("Patched run_agency_os.py with cloud conflict safeguard.")
else:
    print("Warning: old_services not found in run_agency_os.py")

# 2. Patch main.py for full chat_history persistence
main_file = Path(r"C:\Projects\adham-agent\main.py")
main_text = main_file.read_text(encoding="utf-8")

old_handle = """async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return

    # Autonomous Zero-Hallucination Social Media & SEO Dispatcher"""

new_handle = """async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (update.effective_message.text or "").strip()
    if not text:
        return

    log.info("📥 Received Telegram text from %s: %s", update.effective_user.id if update.effective_user else "unknown", text)
    try:
        import memory
        memory.add_chat_message("user", text)
    except Exception:
        pass

    # Autonomous Zero-Hallucination Social Media & SEO Dispatcher"""

if old_handle in main_text:
    main_text = main_text.replace(old_handle, new_handle, 1)
    main_file.write_text(main_text, encoding="utf-8")
    print("Patched main.py with comprehensive message logging.")
else:
    print("Warning: old_handle not found in main.py")

print("Done.")

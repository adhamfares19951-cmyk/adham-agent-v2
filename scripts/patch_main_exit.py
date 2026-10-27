# -*- coding: utf-8 -*-
"""Ensures main.py cleanly exits on fatal polling errors so the watchdog can revive it."""
from pathlib import Path

main_path = Path("C:/Projects/adham-agent/main.py")
code = main_path.read_text(encoding="utf-8")

old_polling = """    log.info("Bot is running (provider=%s, model=%s). Press Ctrl+C to stop.", config.AI_PROVIDER, config.MODEL)
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)"""

new_polling = """    log.info("Bot is running (provider=%s, model=%s). Press Ctrl+C to stop.", config.AI_PROVIDER, config.MODEL)
    try:
        app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    except Exception as e:
        log.warning("run_polling encountered fatal error: %s. Exiting for watchdog reboot...", e)
        import os
        os._exit(1)"""

if old_polling in code:
    code = code.replace(old_polling, new_polling)
    main_path.write_text(code, encoding="utf-8")
    print("Updated main.py run_polling with fail-fast recovery")

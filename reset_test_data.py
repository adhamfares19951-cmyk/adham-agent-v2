"""One-off maintenance: back up agent_memory.db, then clear all reminders and pending approvals.
Run with the bot STOPPED. Usage: python reset_test_data.py
"""
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

DB = Path(__file__).resolve().parent / "agent_memory.db"

if not DB.exists():
    print("لا توجد قاعدة بيانات (agent_memory.db) - لا شيء لحذفه.")
    sys.exit(0)

backup = DB.with_name(f"agent_memory.backup_{datetime.now():%Y%m%d_%H%M%S}.db")
shutil.copy2(DB, backup)
print(f"نسخة احتياطية: {backup.name}")

con = sqlite3.connect(DB, timeout=30)
try:
    for table in ("reminders", "approval_queue"):
        try:
            n = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            con.execute(f"DELETE FROM {table}")
            print(f"{table}: حُذف {n} سجل")
        except sqlite3.Error as e:
            print(f"{table}: تعذّر ({e})")
    con.commit()
finally:
    con.close()
print("تم.")

import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = "C:/Projects/adham-agent/agent_memory.db"
if not os.path.exists(db_path):
    print("Database not found")
    sys.exit(1)

conn = sqlite3.connect(db_path)
c = conn.cursor()

tables = [r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print("Tables in DB:", tables)

for t in tables:
    if "msg" in t.lower() or "chat" in t.lower() or "telegram" in t.lower() or "log" in t.lower() or "visit" in t.lower():
        print(f"\n--- Table: {t} ---")
        try:
            cols = [col[1] for col in c.execute(f"PRAGMA table_info({t})").fetchall()]
            print("Columns:", cols)
            rows = c.execute(f"SELECT * FROM {t} ORDER BY rowid DESC LIMIT 15").fetchall()
            for r in rows:
                print(r)
        except Exception as e:
            print("Error reading", t, e)

# Also check logs directory or recent log files
print("\n--- Checking logs ---")
log_dir = "C:/Projects/adham-agent/logs"
if os.path.exists(log_dir):
    for f in os.listdir(log_dir):
        print("Log file:", f)

# Also check task-2076 log
task_log = "C:/Users/Administrator/.gemini/antigravity/brain/33a48800-6776-46e5-9ca0-d8560b49d7bf/.system_generated/tasks/task-2076.log"
if os.path.exists(task_log):
    print("\n--- Task 2076 recent log lines ---")
    with open(task_log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        for line in lines[-40:]:
            print(line.strip())

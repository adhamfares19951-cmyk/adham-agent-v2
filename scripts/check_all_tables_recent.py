import sqlite3
import sys

sys.stdout.reconfigure(encoding="utf-8")
conn = sqlite3.connect(r"C:\Projects\adham-agent\agent_memory.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall() if t[0] != "sqlite_sequence"]

for t in tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = cursor.fetchone()[0]
        cursor.execute(f"PRAGMA table_info({t})")
        cols = [c[1] for c in cursor.fetchall()]
        time_col = next((c for c in cols if "time" in c.lower() or "created" in c.lower()), None)
        if time_col and cnt > 0:
            cursor.execute(f"SELECT * FROM {t} ORDER BY {time_col} DESC LIMIT 1")
            row = cursor.fetchone()
            print(f"Table {t} ({cnt} rows), latest at {time_col}:\n  {str(row)[:160]}")
        else:
            print(f"Table {t} ({cnt} rows)")
    except Exception as e:
        print(f"Table {t} error: {e}")

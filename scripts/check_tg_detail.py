import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect(r"C:\Projects\adham-agent\agent_memory.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

for t in tables:
    name = t[0]
    cursor.execute(f"PRAGMA table_info({name})")
    cols = [c[1] for c in cursor.fetchall()]
    print(f"Table {name}: cols={cols}")
    if 'created_at' in cols or 'timestamp' in cols:
        time_col = 'created_at' if 'created_at' in cols else 'timestamp'
        cursor.execute(f"SELECT * FROM {name} ORDER BY rowid DESC LIMIT 3")
        rows = cursor.fetchall()
        print(f"Latest 3 rows in {name}:")
        for r in rows:
            print(r)
        print("-" * 30)

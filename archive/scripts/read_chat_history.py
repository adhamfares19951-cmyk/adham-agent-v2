import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()

c.execute("PRAGMA table_info(chat_history)")
cols = [r[1] for r in c.fetchall()]
print("Columns in chat_history:", cols)

c.execute(f"SELECT {', '.join(cols)} FROM chat_history ORDER BY id DESC LIMIT 10")
rows = c.fetchall()
print(f"Total rows retrieved: {len(rows)}")
for r in reversed(rows):
    print("-" * 40)
    for col, val in zip(cols, r):
        print(f"{col}: {val}")

conn.close()

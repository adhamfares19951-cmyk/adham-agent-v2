import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('C:/Projects/adham-agent/agent_memory.db')
c = conn.cursor()
rows = c.execute("SELECT id, role, content, timestamp FROM chat_history WHERE timestamp LIKE '2026-10-27%' ORDER BY id ASC").fetchall()
print(f"Total messages today: {len(rows)}")
for r in rows:
    print(f"[{r[0]}] {r[1]} @ {r[3]}:")
    print(r[2])
    print("-" * 50)

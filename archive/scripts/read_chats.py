import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in c.fetchall()]
print('Tables:', tables)

for t in tables:
    c.execute(f"SELECT count(*) FROM {t}")
    print(f'{t}: {c.fetchone()[0]}')

conn.close()

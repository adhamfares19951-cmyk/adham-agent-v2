import sqlite3

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()
c.execute("PRAGMA table_info(facts)")
print("Columns in facts:", [r[1] for r in c.fetchall()])
c.execute("SELECT * FROM facts")
for r in c.fetchall():
    print(r)
conn.close()

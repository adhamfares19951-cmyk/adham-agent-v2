import sqlite3

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()
c.execute("PRAGMA table_info(job_matches)")
print("Columns in job_matches:", [r[1] for r in c.fetchall()])

c.execute("SELECT * FROM job_matches ORDER BY id DESC LIMIT 5")
rows = c.fetchall()
for r in rows:
    print(r)
conn.close()

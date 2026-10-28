import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()

c.execute("SELECT id, title, company, description, match_reason, url FROM job_matches ORDER BY id DESC LIMIT 10")
rows = c.fetchall()
print(f"Total job_matches: {len(rows)}")
for r in rows:
    print(f"ID: {r[0]} | Title: {r[1]} | Company: {r[2]}")
    print(f"Reason: {r[4]}")
    print(f"Desc excerpt: {str(r[3])[:300]}")
    print(f"URL: {r[5]}")
    print("="*40)

print("\n--- FACTS ---")
c.execute("SELECT key, value FROM facts")
for k, v in c.fetchall():
    print(f"{k}: {v}")

conn.close()

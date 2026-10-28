import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

conn = sqlite3.connect(r'C:\Projects\adham-agent\agent_memory.db')
c = conn.cursor()

c.execute("SELECT id, content, created_at FROM facts")
for r in c.fetchall():
    print(f"Fact {r[0]}: {r[1]} ({r[2]})")

print("\n--- MSF / DATA ENTRY JOBS ---")
c.execute("SELECT id, title, url, details FROM job_matches WHERE title LIKE '%MSF%' OR details LIKE '%MSF%' OR title LIKE '%Data Entry%'")
for r in c.fetchall():
    print(f"ID: {r[0]} | Title: {r[1]} | URL: {r[2]}")
    print(f"Details: {r[3][:400]}")
    print("="*40)

conn.close()

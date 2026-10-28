import sqlite3
conn = sqlite3.connect('C:/Projects/adham-agent/agent_memory.db')
c = conn.cursor()
r = c.execute("SELECT value FROM settings WHERE key='public_web_url'").fetchone()
print("public_web_url:", r[0] if r else "None")

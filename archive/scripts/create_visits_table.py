import sqlite3

conn = sqlite3.connect(r"C:\Projects\adham-agent\agent_memory.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS site_visits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    path TEXT NOT NULL,
    ip TEXT,
    country TEXT,
    referer TEXT,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
print("Table site_visits created successfully.")

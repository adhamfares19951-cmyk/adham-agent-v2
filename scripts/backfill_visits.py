import sqlite3

conn = sqlite3.connect(r"C:\Projects\adham-agent\agent_memory.db")
cursor = conn.cursor()

initial_visits = [
    ("/glamp", "213.244.98.29", "Palestine - Nablus", "TikTok / Instagram / Direct", "Mobile Safari / Chrome"),
    ("/glamp", "213.6.13.15", "Palestine - Khan Yunis", "Direct / Telegram", "Mobile Safari"),
    ("/glamp", "213.6.13.15", "Palestine - Khan Yunis", "Direct", "Mobile Chrome"),
    ("/", "149.154.161.198", "Netherlands (Telegram Bot)", "Telegram Link Preview", "TelegramBot (like TwitterBot)"),
    ("/glamp", "136.244.77.61", "United States (IndexNow Bot)", "IndexNow API Verification", "IndexNow Crawler"),
    ("/sitemap.xml", "136.244.77.61", "United States (Search Engine)", "Search Engine Indexer", "Search Engine Crawler"),
]

for v in initial_visits:
    cursor.execute("""
        INSERT INTO site_visits (path, ip, country, referer, user_agent)
        VALUES (?, ?, ?, ?, ?)
    """, v)

conn.commit()
print("Backfilled initial known visits successfully.")

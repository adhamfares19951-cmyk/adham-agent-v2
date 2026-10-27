import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

app_path = Path(r"C:\Projects\adham-agent\web_platform\app.py")
content = app_path.read_text(encoding="utf-8")

middleware_code = """
@app.middleware("http")
async def track_visitors_middleware(request: Request, call_next):
    path = request.url.path
    # Only track web pages, not static assets
    if not any(path.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".ico", ".svg", ".css", ".js", ".map"]):
        try:
            ip = request.headers.get("cf-connecting-ip") or request.headers.get("x-forwarded-for") or (request.client.host if request.client else "")
            country = request.headers.get("cf-ipcountry", "Unknown")
            referer = request.headers.get("referer", "Direct")
            ua = request.headers.get("user-agent", "")[:200]
            
            with sqlite3.connect(memory.DB_PATH) as conn:
                c = conn.cursor()
                c.execute(
                    "INSERT INTO site_visits (path, ip, country, referer, user_agent) VALUES (?, ?, ?, ?, ?)",
                    (path, ip, country, referer, ua)
                )
                conn.commit()
        except Exception:
            pass

    return await call_next(request)
"""

endpoint_code = """
@app.get("/api/traffic")
async def get_site_traffic():
    \"\"\"Returns live analytics on website visitors, pageviews, and visitor countries.\"\"\"
    with sqlite3.connect(memory.DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM site_visits")
        total_views = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM site_visits WHERE path = '/glamp'")
        glamp_views = c.fetchone()[0]

        c.execute("SELECT COUNT(DISTINCT ip) FROM site_visits WHERE ip IS NOT NULL AND ip != '' AND ip != '127.0.0.1'")
        unique_ips = c.fetchone()[0]

        c.execute("SELECT path, ip, country, referer, created_at FROM site_visits ORDER BY id DESC LIMIT 10")
        recent = [
            {"path": r[0], "ip": r[1], "country": r[2], "referer": r[3], "time": r[4]}
            for r in c.fetchall()
        ]

        c.execute("SELECT COUNT(*) FROM client_orders")
        total_orders = c.fetchone()[0]

    return {
        "status": "success",
        "total_pageviews": total_views,
        "glamp_landing_views": glamp_views,
        "unique_external_visitors": unique_ips,
        "total_orders": total_orders,
        "recent_visitors": recent,
    }
"""

# Insert middleware after CORS
if "app.add_middleware(" in content and "track_visitors_middleware" not in content:
    target = """    allow_headers=["*"],
)"""
    replacement = target + "\n" + middleware_code
    content = content.replace(target, replacement, 1)
    print("Added visitor tracking middleware.")

# Insert endpoint before end
if "/api/traffic" not in content:
    content += "\n" + endpoint_code
    print("Added /api/traffic endpoint.")

app_path.write_text(content, encoding="utf-8")
print("web_platform/app.py updated.")

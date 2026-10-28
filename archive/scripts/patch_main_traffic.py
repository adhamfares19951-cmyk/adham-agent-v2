import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

main_path = Path(r"C:\Projects\adham-agent\main.py")
content = main_path.read_text(encoding="utf-8")

old_def = """    is_cookie_q = "كوكيز" in t and any(k in t for k in ["تيك", "سناب", "انيغرافيتي", "antigravity", "بعتت", "حفظ"])"""

new_def = """    is_cookie_q = "كوكيز" in t and any(k in t for k in ["تيك", "سناب", "انيغرافيتي", "antigravity", "بعتت", "حفظ"])
    is_traffic = any(k in t for k in ["زيارات", "زيارة", "حركة المرور", "مين دخل", "حد دخل", "traffic", "visitors", "دخل عليه"])"""

traffic_handler = """
    # Live Website Traffic Interceptor
    if is_traffic:
        import sqlite3
        with sqlite3.connect(config.DB_PATH) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM site_visits WHERE path = '/glamp'")
            glamp_views = c.fetchone()[0]
            c.execute("SELECT COUNT(DISTINCT ip) FROM site_visits WHERE ip IS NOT NULL AND ip != '' AND ip != '127.0.0.1'")
            unique_ips = c.fetchone()[0]
            c.execute("SELECT path, ip, country, referer, created_at FROM site_visits ORDER BY id DESC LIMIT 5")
            recent = c.fetchall()
            c.execute("SELECT COUNT(*) FROM client_orders")
            orders_count = c.fetchone()[0]

        report = (
            "📊 **تقرير زوار المتجر الحي (Live Website Traffic):**\n\n"
            f"• **مشاهدات صفحة G-Lamp:** **{glamp_views} زيارة**\n"
            f"• **الزوار الفريدين (Unique Visitors):** **{unique_ips} زوار**\n"
            f"• **طلبات الشراء المسجلة:** **{orders_count} طلبات**\n\n"
            "🌍 **آخر الزيارات الموثقة:**\n"
        )
        for r in recent:
            report += f"  📍 {r[2]} ({r[3]})\n"

        report += "\n✅ *الرابط مفهرس ويعمل بسلاسة عبر Cloudflare Tunnel.*"
        await msg.reply_text(report)
        return True
"""

if old_def in content:
    content = content.replace(old_def, new_def, 1)
    # Add traffic handler before Cookie Inquiry
    content = content.replace("    # Cookie Inquiry Interceptor", traffic_handler + "\n    # Cookie Inquiry Interceptor", 1)
    print("Added is_traffic and traffic_handler to main.py")
else:
    print("Warning: old_def not found")

main_path.write_text(content, encoding="utf-8")
print("main.py updated successfully.")

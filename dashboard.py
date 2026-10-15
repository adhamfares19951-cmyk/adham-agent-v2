"""A tiny local dashboard: reminders, recent opportunities, and usage — at a
glance instead of scrolling Telegram. Read-only, no AI calls.

Run: python dashboard.py
Then open http://127.0.0.1:5000 in a browser on this same PC.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, render_template_string

import config
import memory

memory.init_db()

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>لوحة دراع اليمين</title>
<style>
  body { font-family: "Segoe UI", Tahoma, sans-serif; background:#0f172a; color:#e2e8f0; margin:0; padding:24px; }
  h1 { color:#93c5fd; }
  .grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap:20px; margin-top:20px; }
  .card { background:#1e293b; border-radius:12px; padding:18px; }
  .card h2 { margin-top:0; font-size:18px; color:#7dd3fc; }
  .item { border-bottom:1px solid #334155; padding:10px 0; }
  .item:last-child { border-bottom:none; }
  .muted { color:#94a3b8; font-size:13px; }
  .score { color:#4ade80; font-weight:bold; }
  .empty { color:#64748b; font-style:italic; }
  .stat { font-size:28px; font-weight:bold; color:#fde68a; }
</style>
</head>
<body>
  <h1>🖐️ لوحة تحكم دراع اليمين</h1>
  <div class="muted">آخر تحديث: {{ now }}</div>

  <div class="grid">
    <div class="card">
      <h2>⏰ التذكيرات النشطة ({{ reminders|length }})</h2>
      {% for r in reminders %}
        <div class="item">{{ r.text }}<div class="muted">{{ r.due_utc }} — {{ r.repeat }}</div></div>
      {% else %}
        <div class="empty">ما في تذكيرات نشطة</div>
      {% endfor %}
    </div>

    <div class="card">
      <h2>💼 آخر الفرص ({{ matches|length }})</h2>
      {% for m in matches %}
        <div class="item">
          <span class="score">{{ m.score }}%</span> — {{ m.title }}
          <div class="muted">{{ m.category }} · {{ m.created_at }}</div>
        </div>
      {% else %}
        <div class="empty">ما في فرص محفوظة بعد</div>
      {% endfor %}
    </div>

    <div class="card">
      <h2>📊 الاستخدام اليوم</h2>
      <div class="stat">{{ msg_count }}</div>
      <div class="muted">رسالة من أصل {{ daily_limit }} المسموحين</div>
      <div class="stat" style="margin-top:14px">{{ llm_count }}</div>
      <div class="muted">استدعاء ذكاء اصطناعي</div>
    </div>

    <div class="card">
      <h2>🧠 آخر المعلومات المحفوظة ({{ facts|length }})</h2>
      {% for f in facts %}
        <div class="item">{{ f.content }}</div>
      {% else %}
        <div class="empty">ما في معلومات محفوظة بعد</div>
      {% endfor %}
    </div>
  </div>
</body>
</html>
"""


@app.route("/")
def home():
    now = datetime.now(ZoneInfo(config.TIMEZONE)).strftime("%Y-%m-%d %H:%M")
    return render_template_string(
        PAGE,
        now=now,
        reminders=memory.list_active_reminders(),
        matches=memory.recent_matches(limit=15),
        facts=list(reversed(memory.list_facts()))[:15],
        msg_count=memory.get_usage("message"),
        llm_count=memory.get_usage("llm_call"),
        daily_limit=config.DAILY_MESSAGE_LIMIT,
    )


if __name__ == "__main__":
    print("Dashboard running at http://127.0.0.1:5000 (Ctrl+C to stop)")
    app.run(host="127.0.0.1", port=5000, debug=False)

"""Generates a one-page demo website (real HTML file) plus a personalized
outreach message for a local business lead. Not AI tools themselves — main.py
drives this via a two-step JSON-then-template flow, same pattern as documents.py.
Nothing here ever sends anything: the message is a draft Adham copies and
sends himself, and the HTML file is his to forward or open.
"""

SITE_PLAN_PROMPT = """You design a simple, professional one-page demo website for a local
business, to show its owner what a real website could look like for them. Business info:

Name: {business_name}
Sector: {sector}
Location: {location}

Return ONLY a JSON object with EXACTLY these fields:
{{
  "tagline": "<short catchy tagline in Arabic, fits the business type>",
  "about": "<2-3 sentence About text in Arabic, plausible for this kind of business>",
  "services": ["<service/product 1>", "<service/product 2>", "<service/product 3>", "..."],
  "cta_text": "<short call-to-action in Arabic, e.g. 'تواصل معنا' or 'احجز الآن'>",
  "color_primary": "<a hex color fitting the business sector, e.g. warm colors for a restaurant>",
  "color_secondary": "<a complementary hex color>"
}}

Reply with ONLY the raw JSON object, no explanation, no markdown code fences.
"""

PITCH_MESSAGE_PROMPT = """Write a short, friendly, non-pushy outreach message in Palestinian
Arabic from Adham (an IT support and web technician in Khan Younis, Gaza) to the owner of this
local business, offering to build them a simple website:

Business: {business_name} ({sector}), {location}

The message should:
- Open naturally (not overly formal), mention their business by name.
- Briefly say why a simple website would help them specifically (visible to more customers,
  looks professional, works with WhatsApp/Facebook they probably already use).
- Mention he already made them a free demo/preview attached, no obligation.
- Ask if they'd like to see it live or discuss price, keep it short.
- End with his name, Adham.

Reply with ONLY the message text, no explanation, no quotes.
"""


def build_demo_site_html(business_name: str, sector: str, location: str, plan: dict) -> str:
    primary = plan.get("color_primary") or "#1d4ed8"
    secondary = plan.get("color_secondary") or "#0f172a"
    services = plan.get("services") or []
    services_html = "\n".join(f"<li>{s}</li>" for s in services)

    return f"""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{business_name}</title>
<style>
  body {{ font-family: "Segoe UI", Tahoma, Arial, sans-serif; margin:0; background:#f8fafc; color:#1e293b; }}
  header {{ background:linear-gradient(135deg, {primary}, {secondary}); color:#fff; padding:70px 24px; text-align:center; }}
  header h1 {{ font-size:36px; margin:0 0 10px; }}
  header p {{ font-size:18px; opacity:.95; margin:0 0 24px; }}
  .cta {{ display:inline-block; background:#fff; color:{primary}; padding:12px 28px; border-radius:30px;
          font-weight:bold; text-decoration:none; }}
  section {{ max-width:720px; margin:0 auto; padding:48px 24px; }}
  h2 {{ color:{primary}; border-bottom:2px solid {primary}22; padding-bottom:8px; }}
  ul {{ line-height:2; font-size:17px; }}
  footer {{ text-align:center; padding:24px; color:#64748b; font-size:14px; }}
  .badge {{ background:#fef9c3; color:#854d0e; padding:6px 14px; border-radius:20px; font-size:13px;
            display:inline-block; margin-top:10px; }}
</style>
</head>
<body>
  <header>
    <h1>{business_name}</h1>
    <p>{plan.get("tagline", "")}</p>
    <a class="cta" href="#contact">{plan.get("cta_text", "تواصل معنا")}</a>
  </header>
  <section>
    <h2>مين إحنا</h2>
    <p>{plan.get("about", "")}</p>
  </section>
  <section>
    <h2>اللي منقدمه</h2>
    <ul>{services_html}</ul>
  </section>
  <section id="contact">
    <h2>تواصل معنا</h2>
    <p>📍 {location or "خان يونس، غزة"}</p>
  </section>
  <footer>
    نموذج تجريبي مجاني صممه أدهم الهباش — دراع اليمين لخدمات تقنية المعلومات
    <div class="badge">هاد بس معاينة — موقعك الحقيقي ممكن يبين أحلى وفيه صفحاتك كلها</div>
  </footer>
</body>
</html>"""

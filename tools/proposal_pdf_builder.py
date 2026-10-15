"""Executive 1-Page PDF Proposal & Pitch Deck Builder for adham-agent.
Generates pixel-perfect, modern PDF proposals for clients, local businesses, and freelance platforms.
Uses Playwright to render high-aesthetic HTML/CSS templates to print-ready A4 PDFs.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("proposal_pdf_builder")

BASE_DIR = Path(__file__).resolve().parent.parent
PROPOSALS_DIR = BASE_DIR / "proposals"
PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def generate_proposal_pdf(
    client_name: str,
    project_title: str,
    problem_statement: str,
    proposed_solution: str,
    deliverables: list[str],
    pricing: str = "$350 - $600 USD (أو ما يعادله بالشيكل)",
    timeline: str = "3 إلى 5 أيام عمل",
    contact_phone: str = "+970 59-715-0000",
    theme: str = "executive_dark",
) -> Path:
    """Renders a stunning 1-page A4 executive proposal PDF."""
    ts = int(time.time())
    safe_client = "".join(c for c in client_name if c.isalnum() or c in ("-", "_")).strip() or "client"
    output_pdf = PROPOSALS_DIR / f"proposal_{safe_client}_{ts}.pdf"
    temp_html = CACHE_DIR / f"proposal_temp_{ts}.html"

    deliverables_html = "".join(f"<li><span class='check'>✓</span> {d}</li>" for d in deliverables)

    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Outfit:wght@500;700;800&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  @page {{
    size: A4;
    margin: 0;
  }}
  
  body {{
    width: 210mm;
    height: 297mm;
    margin: 0;
    padding: 16mm 18mm;
    font-family: 'Cairo', sans-serif;
    background: #0b0f19;
    color: #f1f5f9;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    position: relative;
    -webkit-print-color-adjust: exact;
  }}

  /* Top decorative gradient */
  .top-bar {{
    height: 6px;
    width: 100%;
    position: absolute;
    top: 0;
    left: 0;
    background: linear-gradient(90deg, #6366f1, #a855f7, #ec4899);
  }}

  /* Header */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.12);
  }}

  .brand h1 {{
    font-size: 22px;
    font-weight: 900;
    color: #ffffff;
    letter-spacing: -0.5px;
  }}

  .brand p {{
    font-size: 11px;
    color: #818cf8;
    font-weight: 600;
    margin-top: 2px;
  }}

  .badge {{
    background: rgba(99, 102, 241, 0.15);
    border: 1px solid rgba(99, 102, 241, 0.35);
    color: #c7d2fe;
    padding: 6px 14px;
    border-radius: 9999px;
    font-size: 11px;
    font-weight: 700;
  }}

  /* Project Meta Card */
  .meta-card {{
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 14px 18px;
    margin-top: 14px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .meta-item h4 {{
    font-size: 10px;
    color: #94a3b8;
    text-transform: uppercase;
    font-weight: 600;
  }}

  .meta-item p {{
    font-size: 13px;
    color: #f8fafc;
    font-weight: 700;
    margin-top: 3px;
  }}

  /* Sections */
  .section {{
    margin-top: 14px;
  }}

  .section-title {{
    font-size: 13px;
    font-weight: 800;
    color: #a5b4fc;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }}

  .section-title::before {{
    content: '';
    width: 4px;
    height: 14px;
    background: #6366f1;
    border-radius: 2px;
    display: inline-block;
  }}

  .section-body {{
    font-size: 11.5px;
    line-height: 1.6;
    color: #cbd5e1;
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 10px;
    padding: 12px 14px;
  }}

  /* Deliverables List */
  .deliverables-list {{
    list-style: none;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }}

  .deliverables-list li {{
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 11px;
    color: #e2e8f0;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .check {{
    color: #10b981;
    font-weight: 900;
  }}

  /* Pricing & Timeline Grid */
  .terms-grid {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-top: 14px;
  }}

  .term-box {{
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.5) 0%, rgba(15, 23, 42, 0.7) 100%);
    border: 1px solid rgba(99, 102, 241, 0.25);
    border-radius: 10px;
    padding: 12px 16px;
    text-align: center;
  }}

  .term-box span {{
    font-size: 10px;
    color: #94a3b8;
    display: block;
    margin-bottom: 4px;
  }}

  .term-box strong {{
    font-size: 14px;
    color: #38bdf8;
    font-weight: 800;
  }}

  /* Footer */
  .footer {{
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10.5px;
    color: #64748b;
  }}

  .engineer-card strong {{
    color: #f1f5f9;
  }}
</style>
</head>
<body>
  <div class="top-bar"></div>

  <div>
    <!-- Header -->
    <div class="header">
      <div class="brand">
        <h1>م. أدهم الهباش | Adham Alhabbash</h1>
        <p>Senior Systems & Solutions Architect • 10+ Years Experience</p>
      </div>
      <div class="badge">📄 عرض فني ومالي تنفيذي</div>
    </div>

    <!-- Meta Card -->
    <div class="meta-card">
      <div class="meta-item">
        <h4>الجهة المستهدفة</h4>
        <p>{client_name}</p>
      </div>
      <div class="meta-item">
        <h4>المشروع</h4>
        <p>{project_title}</p>
      </div>
      <div class="meta-item">
        <h4>التاريخ</h4>
        <p>{time.strftime('%Y-%m-%d')}</p>
      </div>
      <div class="meta-item">
        <h4>الصلاحية</h4>
        <p>14 يوماً</p>
      </div>
    </div>

    <!-- Problem Statement -->
    <div class="section">
      <div class="section-title">التشخيص والتحدي الحالي</div>
      <div class="section-body">
        {problem_statement}
      </div>
    </div>

    <!-- Proposed Solution -->
    <div class="section">
      <div class="section-title">الحل الهندسي المقترح وقيمته المضافة</div>
      <div class="section-body">
        {proposed_solution}
      </div>
    </div>

    <!-- Deliverables -->
    <div class="section">
      <div class="section-title">مخرجات المشروع وضمانات التنفيذ (Deliverables)</div>
      <ul class="deliverables-list">
        {deliverables_html}
      </ul>
    </div>

    <!-- Terms -->
    <div class="terms-grid">
      <div class="term-box">
        <span>المدة الزمنية للتسليم النهائي</span>
        <strong>⏳ {timeline}</strong>
      </div>
      <div class="term-box">
        <span>الاستثمار المقدر للمشروع</span>
        <strong>💰 {pricing}</strong>
      </div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    <div class="engineer-card">
      تم إعداد العرض بواسطة: <strong>م. أدهم فايز الهباش</strong> • غزة - فلسطين
    </div>
    <div>
      واتساب ومباشر: <strong>{contact_phone}</strong> • دعم فني وضمان متواصل
    </div>
  </div>
</body>
</html>
"""

    temp_html.write_text(html_content, encoding="utf-8")

    # Render HTML to PDF via Playwright
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                browser = await p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = await p.chromium.launch(headless=True)

        page = await browser.new_page()
        await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
        await page.pdf(
            path=str(output_pdf),
            format="A4",
            print_background=True,
            prefer_css_page_size=True,
        )
        await browser.close()

    try:
        if temp_html.exists():
            temp_html.unlink()
    except Exception:
        pass

    log.info("Proposal PDF generated: %s (%d bytes)", output_pdf, output_pdf.stat().st_size)
    return output_pdf


async def _handle_generate_proposal(args: dict) -> str:
    client_name = args.get("client_name", "العميل الكريم")
    project_title = args.get("project_title", "نظام نقاط البيع وإدارة الأعمال")
    problem = args.get("problem_statement", "الحاجة لأتمتة العمليات وتقليل الأخطاء وزيادة المبيعات.")
    solution = args.get("proposed_solution", "بناء نظام تقني متكامل، سريع، يعمل بدون انقطاع مع تقارير فورية ودعم فني.")
    deliverables = args.get("deliverables", [
        "تطبيق الأندرويد أو لوحة التحكم جاهزة ومثبتة",
        "قاعدة بيانات محلية سريعة ومحمية",
        "ربط فواتير الواتساب وتقارير الإقفال اليومي",
        "تدريب الطاقم ودعم فني مجاني لمدة 3 أشهر"
    ])
    pricing = args.get("pricing", "$350 - $600 USD")
    timeline = args.get("timeline", "3 إلى 5 أيام عمل")

    pdf_path = await generate_proposal_pdf(
        client_name=client_name,
        project_title=project_title,
        problem_statement=problem,
        proposed_solution=solution,
        deliverables=deliverables,
        pricing=pricing,
        timeline=timeline,
    )

    return (
        f"📄 **تم إنشاء ملف العرض الفني والمالي (PDF) بنجاح!**\n\n"
        f"• **العميل:** {client_name}\n"
        f"• **المشروع:** {project_title}\n"
        f"• **مسار الملف:** `{pdf_path.resolve()}`\n"
        f"• **الحجم:** {pdf_path.stat().st_size / 1024:.1f} KB\n\n"
        f"الملف جاهز للإرسال المباشر على الواتساب أو إرفاقه في مستقل وخمسات!"
    )


TOOLS = [
    {
        "name": "generate_client_proposal_pdf",
        "description": "توليد ملف عرض فني ومالي تنفيذي (PDF) من صفحة واحدة A4 فخمة ومصممة بأعلى معايير التصميم العالمي للعملاء ولأصحاب المشاريع على مستقل وخمسات والواتساب.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {"type": "string", "description": "اسم العميل أو المتجر"},
                "project_title": {"type": "string", "description": "عنوان المشروع أو النظام"},
                "problem_statement": {"type": "string", "description": "ملخص المشكلة أو الاحتياج الحالي"},
                "proposed_solution": {"type": "string", "description": "الحل الهندسي المقترح وميزاته"},
                "deliverables": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "قائمة مخرجات المشروع وضمانات التسليم"
                },
                "pricing": {"type": "string", "description": "الميزانية أو حزمة السعر المقترحة"},
                "timeline": {"type": "string", "description": "المدة الزمنية المتوقعة للتسليم"}
            },
            "required": ["client_name", "project_title"]
        },
        "handler": _handle_generate_proposal,
    }
]

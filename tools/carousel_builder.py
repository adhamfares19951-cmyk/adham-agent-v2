"""Social Carousel & Multi-Slide Infographic Builder for adham-agent.
Generates 1080x1080 pixel-perfect square slide cards for Instagram & LinkedIn carousels.
Uses Playwright to render modern, dark-mode CSS3 cards with Arabic RTL typography.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("carousel_builder")

BASE_DIR = Path(__file__).resolve().parent.parent
CAROUSELS_DIR = BASE_DIR / "carousels"
CAROUSELS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


async def generate_carousel(
    title: str,
    slides_data: list[dict[str, str]],
    brand: str = "م. أدهم الهباش | الذكاء الاصطناعي",
    category_badge: str = "💡 نصيحة تقنية",
) -> dict[str, Any]:
    """Generates an album of 1080x1080 square PNG slides.
    
    slides_data format:
    [
        {"title": "...", "content": "...", "points": ["...", "..."]},
        ...
    ]
    """
    ts = int(time.time())
    folder_name = f"carousel_{ts}"
    out_dir = CAROUSELS_DIR / folder_name
    out_dir.mkdir(parents=True, exist_ok=True)

    total_slides = len(slides_data)
    generated_files: list[Path] = []

    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                browser = await p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = await p.chromium.launch(headless=True)

        for idx, slide in enumerate(slides_data, start=1):
            slide_title = slide.get("title", "")
            slide_content = slide.get("content", "")
            slide_points = slide.get("points", [])
            points_html = "".join(f"<li><span class='bullet'>✦</span> {pt}</li>" for pt in slide_points)

            is_cover = (idx == 1)
            is_last = (idx == total_slides)

            html = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Outfit:wght@700;800&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1080px;
    background: radial-gradient(circle at 50% 20%, #1e1b4b 0%, #0b0f19 60%, #030712 100%);
    color: #f8fafc;
    font-family: 'Cairo', sans-serif;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 80px 70px;
    position: relative;
    overflow: hidden;
  }}

  /* Top Bar */
  .top-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .badge {{
    background: rgba(99, 102, 241, 0.2);
    border: 1px solid rgba(99, 102, 241, 0.4);
    color: #c7d2fe;
    padding: 8px 18px;
    border-radius: 9999px;
    font-size: 20px;
    font-weight: 700;
  }}

  .counter {{
    font-family: 'Outfit', sans-serif;
    font-size: 22px;
    font-weight: 800;
    color: #818cf8;
    background: rgba(255, 255, 255, 0.06);
    padding: 6px 16px;
    border-radius: 20px;
  }}

  /* Main Card Content */
  .content-box {{
    display: flex;
    flex-direction: column;
    justify-content: center;
    flex: 1;
    margin: 40px 0;
  }}

  .slide-title {{
    font-size: { '52px' if is_cover else '40px' };
    font-weight: 900;
    line-height: 1.25;
    color: #ffffff;
    margin-bottom: 24px;
    letter-spacing: -0.5px;
  }}

  .slide-title span {{
    background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .slide-desc {{
    font-size: 26px;
    line-height: 1.6;
    color: #cbd5e1;
    font-weight: 600;
    margin-bottom: 24px;
  }}

  .points-list {{
    list-style: none;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }}

  .points-list li {{
    font-size: 24px;
    line-height: 1.5;
    color: #e2e8f0;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 14px;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 14px;
    padding: 14px 20px;
  }}

  .bullet {{
    color: #38bdf8;
    font-size: 24px;
  }}

  /* Footer */
  .footer-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 24px;
  }}

  .brand-text {{
    font-size: 22px;
    font-weight: 700;
    color: #94a3b8;
  }}

  .swipe-hint {{
    font-size: 20px;
    font-weight: 700;
    color: #38bdf8;
  }}
</style>
</head>
<body>
  <div class="top-row">
    <div class="badge">{category_badge}</div>
    <div class="counter">{idx} / {total_slides}</div>
  </div>

  <div class="content-box">
    <h2 class="slide-title">{slide_title}</h2>
    { f'<p class="slide-desc">{slide_content}</p>' if slide_content else '' }
    { f'<ul class="points-list">{points_html}</ul>' if slide_points else '' }
  </div>

  <div class="footer-row">
    <div class="brand-text">{brand}</div>
    <div class="swipe-hint">{ 'اسحب لليسار 👈' if not is_last else 'احفظ المنشور وشاركه 📌' }</div>
  </div>
</body>
</html>
"""
            temp_html = CACHE_DIR / f"carousel_{ts}_{idx}.html"
            temp_html.write_text(html, encoding="utf-8")

            out_png = out_dir / f"slide_{idx}.png"
            page = await browser.new_page(viewport={"width": 1080, "height": 1080})
            await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(out_png))
            await page.close()

            try:
                temp_html.unlink()
            except Exception:
                pass

            generated_files.append(out_png)

        await browser.close()

    caption = (
        f"📌 **{title}**\n\n"
        f"اسحب الصور لليسار للاطلاع على كامل الدليل والمعلومات الهندسية 💡\n\n"
        f"لا تنسَ حفظ المنشور والرجوع إليه وقت الحاجة!\n\n"
        f"#تقنية #ذكاء_اصطناعي #برمجة #انستغرام #لينكد_إن #تطوير_برمجيات #أدهم_الهباش"
    )

    return {
        "folder": str(out_dir.resolve()),
        "total_slides": total_slides,
        "slides": [str(p.resolve()) for p in generated_files],
        "caption": caption
    }


async def _handle_generate_carousel(args: dict) -> str:
    title = args.get("title", "نصائح تقنية")
    slides_data = args.get("slides", [])
    if not slides_data:
        slides_data = [
            {"title": "كيف تبني تطبيقاً <span>بسرعة البرق</span>؟", "content": "دليلك لاختصار 60% من وقت التطوير باستخدام الأدوات الحديثة."},
            {"title": "الخطوة الأولى: <span>التخطيط الصارم</span>", "points": ["تحديد المشكلة بدقة", "رسم المعمارية قبل الكود", "تجنب التجريد الزائد"]},
            {"title": "الخطوة الثانية: <span>اختيار التقنية المناسبة</span>", "points": ["Flutter لتطبيقات الموبايل", "Laravel للباك إند والـ APIs", "SQLite للعمل أوفلاين"]},
            {"title": "الخلاصة <span>والنصيحة الذهبية</span>", "content": "البساطة والتنفيذ العملي دائماً يفوزان على التعقيد!"}
        ]

    res = await generate_carousel(title=title, slides_data=slides_data)
    return (
        f"🎨 **تم إنشاء ألبوم الكاروسيل ({res['total_slides']} سلايدات) بنجاح!**\n\n"
        f"• **المجلد:** `{res['folder']}`\n"
        f"• **الأبعاد:** 1080x1080 مربع فخم لإنستغرام ولينكد إن\n\n"
        f"📝 **الكابشن المقترح للنشر:**\n{res['caption']}"
    )


TOOLS = [
    {
        "name": "generate_social_carousel",
        "description": "توليد سلايدات وتصاميم كاروسيل مربعة (1080x1080) لإنستغرام ولينكد إن تشرح مواضيع تقنية أو مبيعات شامل POS بستايل دارك فخم.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "عنوان الكاروسيل الرئيسي"},
                "slides": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "points": {"type": "array", "items": {"type": "string"}}
                        }
                    },
                    "description": "قائمة السلايدات مع عنوان ومحتوى ونقاط كل سلايد"
                }
            },
            "required": ["title"]
        },
        "handler": _handle_generate_carousel,
    }
]

import asyncio
import time
from pathlib import Path
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
VIDEOS_DIR = BASE_DIR / "videos"
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

THEME_PALETTES = [
    {
        "name": "cyber_cyan",
        "primary": "#06b6d4",
        "secondary": "#38bdf8",
        "glow": "rgba(6, 182, 212, 0.45)",
        "gradient": "linear-gradient(135deg, #06b6d4, #0284c7)",
        "highlight": "#67e8f9",
        "badge_bg": "rgba(6, 182, 212, 0.2)",
    },
    {
        "name": "crimson_alert",
        "primary": "#ef4444",
        "secondary": "#f87171",
        "glow": "rgba(239, 68, 68, 0.45)",
        "gradient": "linear-gradient(135deg, #ef4444, #dc2626)",
        "highlight": "#fca5a5",
        "badge_bg": "rgba(239, 68, 68, 0.2)",
    },
    {
        "name": "golden_bull",
        "primary": "#eab308",
        "secondary": "#facc15",
        "glow": "rgba(234, 179, 8, 0.45)",
        "gradient": "linear-gradient(135deg, #eab308, #ca8a04)",
        "highlight": "#fef08a",
        "badge_bg": "rgba(234, 179, 8, 0.2)",
    },
    {
        "name": "neon_emerald",
        "primary": "#10b981",
        "secondary": "#34d399",
        "glow": "rgba(16, 185, 129, 0.45)",
        "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "highlight": "#6ee7b7",
        "badge_bg": "rgba(16, 185, 129, 0.2)",
    },
    {
        "name": "electric_violet",
        "primary": "#8b5cf6",
        "secondary": "#a855f7",
        "glow": "rgba(139, 92, 246, 0.45)",
        "gradient": "linear-gradient(135deg, #8b5cf6, #7c3aed)",
        "highlight": "#d8b4fe",
        "badge_bg": "rgba(139, 92, 246, 0.2)",
    },
]

AVAILABLE_CHARTS = [
    VIDEOS_DIR / "chart_liquidity_sweep.jpg",
    VIDEOS_DIR / "chart_order_block.jpg",
    VIDEOS_DIR / "chart_fvg.jpg",
    VIDEOS_DIR / "chart_gold_trap.jpg",
    VIDEOS_DIR / "terminal_bg.jpg",
]

def render_scene_html(
    scene_type: str,
    title: str,
    hook: str,
    points: list[str],
    bg_image_path: Path,
    theme: dict,
    is_arabic: bool = False,
    brand_name: str = "Core Trade AI",
) -> str:
    """Builds hyper-modern 1080x1920 HTML for a specific video scene."""
    lang_attr = "ar" if is_arabic else "en"
    dir_attr = "rtl" if is_arabic else "ltr"
    font_family = "'Cairo', sans-serif" if is_arabic else "'Outfit', 'Inter', sans-serif"
    bg_url = f"file:///{bg_image_path.as_posix()}"

    p_col = theme["primary"]
    s_col = theme["secondary"]
    glow = theme["glow"]
    grad = theme["gradient"]
    high = theme["highlight"]

    content_html = ""
    if scene_type == "hook":
        badge_text = "⚡ إشارة دخول مؤسسية" if is_arabic else "⚡ INSTITUTIONAL RADAR"
        content_html = f"""
        <div class="card hook-card">
          <div class="card-header">
            <div class="badge">{badge_text}</div>
            <div class="brand-pill">{brand_name}</div>
          </div>
          <div class="headline">{hook}</div>
          <div class="subline">{title}</div>
        </div>
        """
    elif scene_type == "trap":
        badge_text = "⚠️ فخ المتداولين الأفراد" if is_arabic else "⚠️ RETAIL TRADER TRAP"
        trap_title = "كيف تصطاد البنوك وقفك؟" if is_arabic else "Why 90% Get Liquidated"
        trap_desc = (
            "المتداولون يضعون وقوفهم عند القمم والقيعان الواضحة. خوارزميات البنوك تضرب هذه المستويات لتجميع العقود الضخمة."
            if is_arabic else
            "Retail traders place predictable stop losses at obvious double tops & bottoms. High-frequency algorithms sweep this liquidity before the real expansion."
        )
        content_html = f"""
        <div class="card trap-card">
          <div class="card-header">
            <div class="badge badge-danger">{badge_text}</div>
            <div class="metric-chip">SWEEP DETECTED</div>
          </div>
          <div class="headline headline-danger">{trap_title}</div>
          <p class="body-text">{trap_desc}</p>
          <div class="alert-box">
            <span class="pulse-dot"></span>
            <span>{"🛑 تجنب الشراء عند الكسر الكاذب" if is_arabic else "🛑 STOP BUYING THE BREAKOUT TRAP"}</span>
          </div>
        </div>
        """
    elif scene_type == "solution":
        badge_text = "🎯 خطة الدخول الذكية" if is_arabic else "🎯 SMART MONEY BLUEPRINT"
        sol_title = "نموذج صناع السوق (SMC)" if is_arabic else "The High-Probability Entry"
        items_html = ""
        default_pts = points if points else (
            ["سحب السيولة بالكامل", "تأكيد فجوة القيمة العادلة (FVG)", "عائد للمخاطرة 1 إلى 3"]
            if is_arabic else
            ["Full Liquidity Sweep Confirmation", "Displacement into Fair Value Gap", "Minimum 1:3 Risk-to-Reward"]
        )
        icons = ["💎", "⚡", "🎯", "🛡️"]
        for idx, pt in enumerate(default_pts[:3]):
            icon = icons[idx % len(icons)]
            items_html += f"""
            <div class="checklist-item">
              <div class="item-icon">{icon}</div>
              <div class="item-text">{pt}</div>
            </div>
            """
        content_html = f"""
        <div class="card solution-card">
          <div class="card-header">
            <div class="badge badge-success">{badge_text}</div>
            <div class="metric-chip">WIN RATE: 84%</div>
          </div>
          <div class="headline headline-success">{sol_title}</div>
          <div class="checklist">
            {items_html}
          </div>
        </div>
        """
    else:  # outro / cta
        cta_badge = "👑 انضم إلى النخبة" if is_arabic else "👑 BECOME THE HUNTER"
        cta_head = "توقف عن كونك السيولة" if is_arabic else "Stop Being The Liquidity."
        cta_sub = (
            "تابع الحساب لمشاهدة التحليلات المؤسسية اليومية • الرابط بالبايو"
            if is_arabic else
            "Follow @CoreTradeAI for daily algorithmic footprints • Link in Bio"
        )
        content_html = f"""
        <div class="card outro-card">
          <div class="outro-logo-circle">⚡</div>
          <div class="badge badge-gold">{cta_badge}</div>
          <div class="headline headline-gold">{cta_head}</div>
          <p class="outro-sub">{cta_sub}</p>
          <div class="subscribe-btn">
            <span>{brand_name}</span>
          </div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="{dir_attr}">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;900&family=Outfit:wght@600;800;900&family=Inter:wght@600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1920px;
    background: url('{bg_url}') center center / cover no-repeat;
    position: relative;
    overflow: hidden;
    font-family: {font_family};
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    padding: 70px 45px;
    color: #f8fafc;
  }}

  /* Dark Vignette Overlay */
  .vignette {{
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at center, rgba(10, 15, 29, 0.45) 0%, rgba(3, 7, 18, 0.88) 100%);
    pointer-events: none;
    z-index: 1;
  }}

  /* Top Glow Orb */
  .glow-orb {{
    position: absolute;
    top: -120px;
    left: 50%;
    transform: translateX(-50%);
    width: 650px;
    height: 650px;
    background: radial-gradient(circle, {glow} 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
    z-index: 2;
  }}

  /* Card Base */
  .card {{
    position: relative;
    z-index: 10;
    background: rgba(11, 17, 32, 0.88);
    backdrop-filter: blur(28px);
    -webkit-backdrop-filter: blur(28px);
    border: 2px solid rgba(255, 255, 255, 0.12);
    border-radius: 36px;
    padding: 40px 45px;
    box-shadow: 0 30px 60px rgba(0, 0, 0, 0.75), 0 0 35px {glow};
  }}

  .card-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 24px;
  }}

  .badge {{
    background: {grad};
    color: #ffffff;
    font-size: 24px;
    font-weight: 900;
    padding: 10px 26px;
    border-radius: 999px;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    box-shadow: 0 6px 20px {glow};
  }}
  .badge-danger {{
    background: linear-gradient(135deg, #ef4444, #b91c1c);
    box-shadow: 0 6px 20px rgba(239, 68, 68, 0.4);
  }}
  .badge-success {{
    background: linear-gradient(135deg, #10b981, #047857);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  }}
  .badge-gold {{
    background: linear-gradient(135deg, #f59e0b, #d97706);
    box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
  }}

  .brand-pill {{
    color: {s_col};
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}

  .metric-chip {{
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.2);
    color: #e2e8f0;
    font-size: 20px;
    font-weight: 700;
    padding: 8px 18px;
    border-radius: 999px;
    letter-spacing: 1px;
  }}

  .headline {{
    font-size: 48px;
    font-weight: 900;
    line-height: 1.25;
    color: #ffffff;
    margin-bottom: 18px;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.8);
  }}
  .headline-danger {{
    color: #fca5a5;
  }}
  .headline-success {{
    color: #6ee7b7;
  }}
  .headline-gold {{
    color: #fef08a;
  }}

  .subline {{
    font-size: 32px;
    color: #cbd5e1;
    font-weight: 700;
    line-height: 1.4;
  }}

  .body-text {{
    font-size: 32px;
    color: #e2e8f0;
    line-height: 1.5;
    margin-bottom: 30px;
  }}

  .alert-box {{
    display: flex;
    align-items: center;
    gap: 16px;
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.4);
    border-radius: 20px;
    padding: 20px 26px;
    font-size: 28px;
    font-weight: 800;
    color: #fca5a5;
  }}
  .pulse-dot {{
    width: 16px;
    height: 16px;
    border-radius: 50%;
    background: #ef4444;
    box-shadow: 0 0 12px #ef4444;
  }}

  /* Solution Checklist */
  .checklist {{
    display: flex;
    flex-direction: column;
    gap: 20px;
    margin-top: 15px;
  }}
  .checklist-item {{
    display: flex;
    align-items: center;
    gap: 24px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 24px;
    padding: 24px 30px;
  }}
  .item-icon {{
    font-size: 36px;
  }}
  .item-text {{
    font-size: 32px;
    font-weight: 800;
    color: #f1f5f9;
  }}

  /* Outro Card Specifics */
  .outro-card {{
    text-align: center;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 60px 50px;
    margin-top: 60px;
  }}
  .outro-logo-circle {{
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: {grad};
    font-size: 60px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px {glow};
  }}
  .outro-sub {{
    font-size: 34px;
    color: #cbd5e1;
    font-weight: 700;
    margin: 25px 0 40px 0;
    line-height: 1.45;
  }}
  .subscribe-btn {{
    background: {grad};
    color: #ffffff;
    font-size: 38px;
    font-weight: 900;
    padding: 22px 60px;
    border-radius: 999px;
    box-shadow: 0 15px 35px {glow};
  }}

  /* Watermark Footer */
  .footer-watermark {{
    position: absolute;
    bottom: 50px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    padding: 12px 34px;
    border-radius: 999px;
    color: #94a3b8;
    font-size: 22px;
    font-weight: 700;
    z-index: 10;
  }}
  .footer-watermark span {{
    color: {s_col};
    font-weight: 800;
  }}
</style>
</head>
<body>
  <div class="vignette"></div>
  <div class="glow-orb"></div>

  {content_html}

  <div class="footer-watermark">
    <span>@{brand_name.replace(' ', '')}</span> • Institutional Market Intelligence
  </div>
</body>
</html>"""

async def test():
    theme = THEME_PALETTES[0] # cyber cyan
    charts = AVAILABLE_CHARTS
    
    scenes = [
        ("hook", "Stop Loss Hunt Mechanics", "Why Banks ALWAYS Sweep Your Stop Loss", ["Equal Highs Sweep", "Order Block Imbalance"], charts[0]),
        ("trap", "The 90% Breakout Trap", "Why Retail Breakout Traders Get Wiped Out", [], charts[1]),
        ("solution", "The Institutional Blueprint", "How To Trade With The Smart Money", ["Wait for Liquidity Sweep", "Fair Value Gap Confirmation", "Target Next Liquidity Pool"], charts[2]),
        ("outro", "Core Trade AI", "Stop Being The Liquidity. Become The Hunter.", [], charts[4]),
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        
        for idx, (stype, title, hook, pts, bg) in enumerate(scenes):
            html = render_scene_html(stype, title, hook, pts, bg, theme)
            out_file = CACHE_DIR / f"test_scene_{idx}_{stype}.png"
            temp_html = CACHE_DIR / f"temp_{idx}.html"
            temp_html.write_text(html, encoding="utf-8")
            await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(out_file), full_page=False)
            print(f"Generated scene {idx} ({stype}): {out_file} ({out_file.stat().st_size} bytes)")
            temp_html.unlink()
            
        await browser.close()
        print("All 4 test scenes generated successfully!")

if __name__ == "__main__":
    asyncio.run(test())

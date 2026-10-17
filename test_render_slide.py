import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

async def render_trading_slide():
    chart_path = Path("e:/Users/adham/Desktop/new/adham-agent/videos/chart_liquidity_sweep.jpg")
    out_png = Path("e:/Users/adham/Desktop/new/adham-agent/videos/trading_slide_test.png")
    
    html = f"""<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@700;800;900&family=Inter:wght@600;700&display=swap');
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    width: 1080px;
    height: 1920px;
    background: url('file:///{chart_path.as_posix()}') center center / cover no-repeat;
    position: relative;
    overflow: hidden;
    font-family: 'Outfit', sans-serif;
  }}
  
  /* Top Hook Header Card */
  .top-banner {{
    position: absolute;
    top: 70px;
    left: 40px;
    right: 40px;
    background: rgba(10, 15, 29, 0.88);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-top: 3px solid #ef4444;
    border-radius: 28px;
    padding: 30px 36px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(239, 68, 68, 0.25);
    z-index: 20;
  }}
  .badge-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }}
  .badge {{
    background: linear-gradient(135deg, #ef4444, #dc2626);
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    padding: 8px 22px;
    border-radius: 999px;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 4px 15px rgba(239, 68, 68, 0.5);
  }}
  .channel-pill {{
    display: flex;
    align-items: center;
    gap: 8px;
    color: #38bdf8;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: 0.5px;
  }}
  .hook-title {{
    color: #ffffff;
    font-size: 46px;
    font-weight: 900;
    line-height: 1.25;
    letter-spacing: -0.5px;
    text-shadow: 0 4px 20px rgba(0,0,0,0.8);
  }}
  .hook-title span {{
    color: #facc15;
    text-shadow: 0 0 25px rgba(250, 204, 21, 0.5);
  }}

  /* Bottom subtle vignette for subtitles */
  .bottom-shade {{
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 480px;
    background: linear-gradient(to top, rgba(3, 7, 18, 0.95) 0%, rgba(3, 7, 18, 0.7) 50%, transparent 100%);
    pointer-events: none;
    z-index: 10;
  }}

  /* Floating Watermark */
  .watermark {{
    position: absolute;
    bottom: 50px;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    align-items: center;
    gap: 12px;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 12px 30px;
    border-radius: 999px;
    color: #e2e8f0;
    font-size: 24px;
    font-weight: 700;
    z-index: 15;
  }}
  .watermark span {{
    color: #38bdf8;
    font-weight: 800;
  }}
</style>
</head>
<body>
  <div class="top-banner">
    <div class="badge-row">
      <div class="badge">⚠️ SMC LIQUIDITY TRAP</div>
      <div class="channel-pill">⚡ Core Trade AI</div>
    </div>
    <div class="hook-title">Why Do Banks Always <span>Hunt Your Stop Loss?</span></div>
  </div>
  
  <div class="bottom-shade"></div>
  
  <div class="watermark">
    <span>@CoreTradeAI</span> • Institutional Algo Hub
  </div>
</body>
</html>"""

    temp_html = Path("e:/Users/adham/Desktop/new/adham-agent/repos_cache/temp_trading_slide.html")
    temp_html.write_text(html, encoding="utf-8")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
        await page.screenshot(path=str(out_png), full_page=False)
        await browser.close()
    
    print("Slide rendered to:", out_png)

if __name__ == "__main__":
    asyncio.run(render_trading_slide())

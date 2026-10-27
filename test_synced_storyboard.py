"""Testing full synced 4-scene narrative engine where visuals strictly match the narration."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
import test_chart_engine as tce

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def build_narrative_scene_svg(
    asset_key: str,
    scene_index: int,
    title: str,
    hook: str,
    candles: list[dict],
    width: int = 1080,
    height: int = 1920,
) -> str:
    cfg = tce.ASSET_CONFIGS.get(asset_key, tce.ASSET_CONFIGS["XAUUSD"])
    
    chart_top = 340
    chart_bottom = 1520
    chart_left = 60
    chart_right = 960
    chart_w = chart_right - chart_left
    chart_h = chart_bottom - chart_top
    
    all_highs = [c["high"] for c in candles]
    all_lows = [c["low"] for c in candles]
    min_p = min(all_lows) * 0.998
    max_p = max(all_highs) * 1.002
    p_range = max_p - min_p
    
    def price_to_y(price: float) -> float:
        return chart_bottom - ((price - min_p) / p_range) * chart_h

    candle_w = chart_w / len(candles)
    bar_w = max(candle_w * 0.65, 4.0)

    # Candlesticks
    candles_svg = []
    for i, c in enumerate(candles):
        cx = chart_left + (i + 0.5) * candle_w
        cy_open = price_to_y(c["open"])
        cy_close = price_to_y(c["close"])
        cy_high = price_to_y(c["high"])
        cy_low = price_to_y(c["low"])
        color = "#10b981" if c["is_up"] else "#ef4444"
        
        candles_svg.append(f'<line x1="{cx:.1f}" y1="{cy_high:.1f}" x2="{cx:.1f}" y2="{cy_low:.1f}" stroke="{color}" stroke-width="2.5" opacity="0.9"/>')
        body_top = min(cy_open, cy_close)
        body_h = max(abs(cy_open - cy_close), 2.5)
        candles_svg.append(f'<rect x="{cx - bar_w/2:.1f}" y="{body_top:.1f}" width="{bar_w:.1f}" height="{body_h:.1f}" fill="{color}" rx="1"/>')
        
        # Volume
        vol_height = 180 if (c.get("is_sweep") or c.get("is_displacement")) else 50
        candles_svg.append(f'<rect x="{cx - bar_w/2:.1f}" y="{1640 - vol_height}" width="{bar_w:.1f}" height="{vol_height}" fill="{color}" opacity="0.45"/>')

    # Gridlines
    grid_lines = []
    for s in range(7):
        price = min_p + (s / 6) * p_range
        y = price_to_y(price)
        decimals = cfg["price_decimals"]
        grid_lines.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1" stroke-dasharray="4 4"/>')
        grid_lines.append(f'<text x="{chart_right + 14}" y="{y + 5:.1f}" fill="#64748b" font-family="monospace" font-size="18">{price:.{decimals}f}</text>')

    sweep_idx = next((i for i, c in enumerate(candles) if c.get("is_sweep")), 14)
    sweep_candle = candles[sweep_idx]
    sweep_cx = chart_left + (sweep_idx + 0.5) * candle_w
    sweep_cy_high = price_to_y(sweep_candle["high"])
    eqh_price = max(c["high"] for c in candles[sweep_idx-6:sweep_idx])
    eqh_y = price_to_y(eqh_price)

    # Narrative Overlay for each specific scene
    narrative_overlay = ""
    if scene_index == 0:  # Scene 1: The Hook & The Retail Trap Setup
        narrative_overlay = f'''
        <!-- Top Hook Header Card -->
        <rect x="40" y="60" width="1000" height="230" fill="rgba(10,15,29,0.92)" stroke="rgba(255,255,255,0.15)" stroke-width="2" rx="32"/>
        <rect x="40" y="60" width="1000" height="8" fill="{cfg["theme_color"]}" rx="4"/>
        
        <rect x="75" y="90" width="280" height="42" fill="{cfg["theme_color"]}" rx="999"/>
        <text x="215" y="118" fill="#ffffff" font-family="sans-serif" font-size="20" font-weight="900" text-anchor="middle">⚠️ SMC LIQUIDITY TRAP</text>
        <text x="965" y="120" fill="#38bdf8" font-family="sans-serif" font-size="24" font-weight="900" text-anchor="end">⚡ Core Trade AI</text>
        
        <text x="75" y="185" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="44" font-weight="900">{hook}</text>
        <text x="75" y="245" fill="#cbd5e1" font-family="'Outfit', sans-serif" font-size="28" font-weight="700">{title}</text>

        <!-- Retail Stops Highlight -->
        <line x1="{chart_left + 100}" y1="{eqh_y:.1f}" x2="{chart_right - 40}" y2="{eqh_y:.1f}" stroke="#ef4444" stroke-width="3" stroke-dasharray="8 6"/>
        <rect x="180" y="{eqh_y - 45:.1f}" width="440" height="40" fill="rgba(239,68,68,0.25)" stroke="#ef4444" stroke-width="2" rx="8"/>
        <text x="400" y="{eqh_y - 18:.1f}" fill="#ffffff" font-family="sans-serif" font-size="18" font-weight="900" text-anchor="middle">🚨 90% OF RETAIL STOPS PLACED HERE</text>
        '''
    elif scene_index == 1:  # Scene 2: The Liquidity Sweep / The Bank Hunt
        narrative_overlay = f'''
        <!-- Top Hunt Card -->
        <rect x="40" y="60" width="1000" height="220" fill="rgba(15,23,42,0.92)" stroke="#facc15" stroke-width="2" rx="32"/>
        <rect x="75" y="90" width="320" height="42" fill="#ef4444" rx="999"/>
        <text x="235" y="118" fill="#ffffff" font-family="sans-serif" font-size="20" font-weight="900" text-anchor="middle">⚡ THE LIQUIDITY SWEEP</text>
        <text x="965" y="120" fill="#facc15" font-family="sans-serif" font-size="24" font-weight="900" text-anchor="end">INSTITUTIONAL ALGO</text>

        <text x="75" y="185" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="44" font-weight="900">Banks Sweep The Highs</text>
        <text x="75" y="235" fill="#fca5a5" font-family="'Outfit', sans-serif" font-size="28" font-weight="700">Retail breakout buyers are instantly trapped &amp; liquidated</text>

        <!-- Liquidity Sweep Wick Pointer -->
        <circle cx="{sweep_cx:.1f}" cy="{sweep_cy_high:.1f}" r="14" fill="#facc15" stroke="#ffffff" stroke-width="3"/>
        <rect x="{sweep_cx - 200:.1f}" y="{sweep_cy_high - 110:.1f}" width="400" height="75" fill="rgba(10,15,29,0.95)" stroke="#facc15" stroke-width="2.5" rx="16"/>
        <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 72:.1f}" fill="#facc15" font-family="sans-serif" font-size="22" font-weight="900" text-anchor="middle">⚡ LIQUIDITY SWEEP WICK</text>
        <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 45:.1f}" fill="#ef4444" font-family="monospace" font-size="16" font-weight="800" text-anchor="middle">-$48,000,000 RETAIL LIQUIDATIONS</text>
        <path d="M {sweep_cx:.1f} {sweep_cy_high - 35:.1f} L {sweep_cx:.1f} {sweep_cy_high - 15:.1f}" stroke="#facc15" stroke-width="3"/>
        '''
    elif scene_index == 2:  # Scene 3: The Smart Money Execution / Order Block Setup
        ob_y1 = price_to_y(eqh_price)
        ob_y2 = price_to_y(eqh_price * 0.993)
        last_cx = chart_left + (len(candles) - 4 + 0.5) * candle_w
        last_cy = price_to_y(candles[-4]["close"])

        narrative_overlay = f'''
        <!-- Top Blueprint Card -->
        <rect x="40" y="60" width="1000" height="230" fill="rgba(10,15,29,0.92)" stroke="#10b981" stroke-width="2" rx="32"/>
        <rect x="75" y="90" width="340" height="42" fill="#10b981" rx="999"/>
        <text x="245" y="118" fill="#ffffff" font-family="sans-serif" font-size="20" font-weight="900" text-anchor="middle">🎯 SMART MONEY BLUEPRINT</text>
        <text x="965" y="120" fill="#34d399" font-family="sans-serif" font-size="24" font-weight="900" text-anchor="end">WIN RATE: 86.4%</text>

        <text x="75" y="185" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="44" font-weight="900">Enter On The Order Block</text>
        <text x="75" y="235" fill="#6ee7b7" font-family="'Outfit', sans-serif" font-size="28" font-weight="700">Minimum 1:3.5 Asymmetric Risk-To-Reward</text>

        <!-- Order Block Zone Box -->
        <rect x="{sweep_cx - 40:.1f}" y="{ob_y1:.1f}" width="420" height="{abs(ob_y2 - ob_y1):.1f}" fill="rgba(6,182,212,0.25)" stroke="#06b6d4" stroke-width="2.5" rx="8"/>
        <text x="{sweep_cx - 20:.1f}" y="{ob_y1 + 30:.1f}" fill="#38bdf8" font-family="sans-serif" font-size="18" font-weight="900">INSTITUTIONAL ORDER BLOCK</text>

        <!-- Asymmetric Target Line -->
        <line x1="{sweep_cx + 40:.1f}" y1="{sweep_cy_high + 60:.1f}" x2="{last_cx - 20:.1f}" y2="{last_cy - 40:.1f}" stroke="#10b981" stroke-width="4.5" stroke-dasharray="8 6"/>
        <rect x="{last_cx - 180:.1f}" y="{last_cy + 25:.1f}" width="260" height="50" fill="rgba(16,185,129,0.25)" stroke="#10b981" stroke-width="2" rx="10"/>
        <text x="{last_cx - 50:.1f}" y="{last_cy + 58:.1f}" fill="#6ee7b7" font-family="sans-serif" font-size="22" font-weight="900" text-anchor="middle">🎯 1:3.8 RR TARGET HIT</text>
        '''
    else:  # Scene 4: The Outro / Channel CTA
        narrative_overlay = f'''
        <!-- Full Screen VIP Terminal Card -->
        <rect x="60" y="280" width="960" height="900" fill="rgba(11,17,32,0.94)" stroke="rgba(255,255,255,0.15)" stroke-width="2" rx="40"/>
        
        <circle cx="540" cy="460" r="70" fill="url(#btnGrad)"/>
        <text x="540" y="485" fill="#ffffff" font-family="sans-serif" font-size="65" font-weight="900" text-anchor="middle">⚡</text>

        <rect x="360" y="580" width="360" height="46" fill="url(#goldGrad)" rx="999"/>
        <text x="540" y="612" fill="#ffffff" font-family="sans-serif" font-size="22" font-weight="900" text-anchor="middle">👑 BECOME THE HUNTER</text>

        <text x="540" y="700" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="52" font-weight="900" text-anchor="middle">Stop Being The Liquidity.</text>
        <text x="540" y="770" fill="#cbd5e1" font-family="'Outfit', sans-serif" font-size="32" font-weight="700" text-anchor="middle">Daily Institutional Algorithmic Footprints</text>

        <rect x="220" y="850" width="640" height="90" fill="url(#btnGrad)" rx="999"/>
        <text x="540" y="908" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="38" font-weight="900" text-anchor="middle">Subscribe to Core Trade AI</text>

        <text x="540" y="1030" fill="#94a3b8" font-family="sans-serif" font-size="24" font-weight="700" text-anchor="middle">Link in Bio • Free SMC Strategy Guide</text>
        '''

    # TradingView Top Bar
    tv_bar = f'''
    <rect x="0" y="0" width="{width}" height="60" fill="#0b0f19" opacity="0.95"/>
    <text x="60" y="38" fill="#94a3b8" font-family="monospace" font-size="18" font-weight="700">{cfg["symbol"]} • {cfg["timeframe"]} • {cfg["exchange"]}</text>
    <circle cx="{width - 60}" cy="30" r="8" fill="#10b981"/>
    '''

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background-color: #030712;">
  <defs>
    <linearGradient id="btnGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4"/>
      <stop offset="100%" stop-color="#2563eb"/>
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <linearGradient id="bottomShade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(3,7,18,0)"/>
      <stop offset="60%" stop-color="rgba(3,7,18,0.85)"/>
      <stop offset="100%" stop-color="rgba(3,7,18,0.98)"/>
    </linearGradient>
  </defs>

  <!-- Grid -->
  {"".join(grid_lines)}

  <!-- Candlesticks -->
  {"".join(candles_svg)}

  <!-- Top Bar -->
  {tv_bar}

  <!-- Narrative Overlay -->
  {narrative_overlay}

  <!-- Lower Third Subtitle Protection Gradient -->
  <rect x="0" y="1450" width="{width}" height="470" fill="url(#bottomShade)"/>
</svg>'''

async def test():
    print("Testing 4 narrative scenes for Gold XAU/USD...")
    candles = tce.generate_candlestick_data(base_price=2415.50, count=30)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        
        scenes = [
            ("Scene 1 - The Hook", "The 90% Stop Loss Trap", "Why Banks Always Hunt Your Stop Loss"),
            ("Scene 2 - The Sweep", "The Liquidity Sweep", "Algorithms Sweep Obvious Highs"),
            ("Scene 3 - The Setup", "Order Block Imbalance", "Enter With Institutional Volume"),
            ("Scene 4 - The Outro", "Core Trade AI", "Stop Being The Liquidity"),
        ]
        
        for idx, (label, title, hook) in enumerate(scenes):
            svg = build_narrative_scene_svg("XAUUSD", idx, title, hook, candles)
            temp_svg = CACHE_DIR / f"narrative_{idx}.svg"
            temp_svg.write_text(svg, encoding="utf-8")
            out_png = CACHE_DIR / f"narrative_scene_{idx}.png"
            await page.goto(f"file:///{temp_svg.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(out_png), full_page=False)
            print(f"Generated {label}: {out_png} ({out_png.stat().st_size} bytes)")
            temp_svg.unlink()
            
        await browser.close()
    print("All 4 narrative scenes generated successfully!")

if __name__ == "__main__":
    asyncio.run(test())

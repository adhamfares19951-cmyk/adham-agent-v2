"""Procedural TradingView Chart Generator for adham-agent.
Generates razor-sharp, photorealistic 1080x1920 dark-mode TradingView charts
with authentic candles, volume profiles, technical indicators, and institutional SMC annotations.
"""
import random
import time
from pathlib import Path
import asyncio
from playwright.async_api import async_playwright

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

ASSET_CONFIGS = {
    "XAUUSD": {
        "symbol": "XAU/USD • GOLD",
        "timeframe": "15m",
        "price_base": 2415.50,
        "price_decimals": 2,
        "exchange": "OANDA",
        "theme_color": "#f59e0b",
        "theme_glow": "rgba(245, 158, 11, 0.45)",
    },
    "EURUSD": {
        "symbol": "EUR/USD",
        "timeframe": "4h",
        "price_base": 1.08450,
        "price_decimals": 5,
        "exchange": "FXCM",
        "theme_color": "#06b6d4",
        "theme_glow": "rgba(6, 182, 212, 0.45)",
    },
    "BTCUSD": {
        "symbol": "BTC/USDT • BITCOIN",
        "timeframe": "1h",
        "price_base": 67850.0,
        "price_decimals": 1,
        "exchange": "BINANCE",
        "theme_color": "#10b981",
        "theme_glow": "rgba(16, 185, 129, 0.45)",
    },
    "US100": {
        "symbol": "NAS100 • NASDAQ",
        "timeframe": "5m",
        "price_base": 20420.0,
        "price_decimals": 1,
        "exchange": "CME",
        "theme_color": "#8b5cf6",
        "theme_glow": "rgba(139, 92, 246, 0.45)",
    },
}

def generate_candlestick_data(base_price: float, count: int = 32, volatility: float = 0.003) -> list[dict]:
    """Generates realistic candlestick series with an institutional liquidity sweep and expansion."""
    candles = []
    p = base_price
    
    # 1. Building accumulation / range (first 14 candles)
    for i in range(14):
        delta = (random.random() - 0.48) * volatility * p
        o = p
        c = o + delta
        h = max(o, c) + random.random() * volatility * 0.8 * p
        l = min(o, c) - random.random() * volatility * 0.8 * p
        candles.append({"open": o, "high": h, "low": l, "close": c, "is_up": c >= o})
        p = c
    
    # 2. Equal highs resistance level
    high_level = max(c["high"] for c in candles[-6:])
    
    # 3. Liquidity sweep candle (wicks high above equal highs, then closes bearish)
    sweep_open = p
    sweep_high = high_level + (volatility * 1.8 * p)
    sweep_close = sweep_open - (volatility * 0.9 * p)
    sweep_low = sweep_close - (volatility * 0.3 * p)
    candles.append({
        "open": sweep_open, "high": sweep_high, "low": sweep_low, "close": sweep_close,
        "is_up": False, "is_sweep": True
    })
    p = sweep_close

    # 4. Violent displacement expansion (6 large bearish candles)
    for i in range(7):
        delta = -1 * (random.random() * 0.7 + 0.6) * volatility * p
        o = p
        c = o + delta
        h = o + random.random() * volatility * 0.2 * p
        l = c - random.random() * volatility * 0.4 * p
        candles.append({"open": o, "high": h, "low": l, "close": c, "is_up": False, "is_displacement": True})
        p = c

    # 5. Consolidation and FVG retest (remaining candles)
    for i in range(count - len(candles)):
        delta = (random.random() - 0.45) * volatility * p
        o = p
        c = o + delta
        h = max(o, c) + random.random() * volatility * 0.3 * p
        l = min(o, c) - random.random() * volatility * 0.3 * p
        candles.append({"open": o, "high": h, "low": l, "close": c, "is_up": c >= o})
        p = c

    return candles

def render_chart_svg(
    candles: list[dict],
    asset: str,
    setup_type: str = "sweep",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Renders a pixel-perfect, dark-mode TradingView chart directly in SVG."""
    cfg = ASSET_CONFIGS.get(asset, ASSET_CONFIGS["XAUUSD"])
    
    chart_top = 220
    chart_bottom = 1450
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

    # Candlesticks elements
    candles_svg = []
    volume_svg = []
    
    for i, c in enumerate(candles):
        cx = chart_left + (i + 0.5) * candle_w
        cy_open = price_to_y(c["open"])
        cy_close = price_to_y(c["close"])
        cy_high = price_to_y(c["high"])
        cy_low = price_to_y(c["low"])
        
        is_up = c["is_up"]
        color = "#10b981" if is_up else "#ef4444"
        
        # Wick
        candles_svg.append(f'<line x1="{cx:.1f}" y1="{cy_high:.1f}" x2="{cx:.1f}" y2="{cy_low:.1f}" stroke="{color}" stroke-width="2.5" opacity="0.9"/>')
        
        # Body
        body_top = min(cy_open, cy_close)
        body_h = max(abs(cy_open - cy_close), 2.5)
        candles_svg.append(f'<rect x="{cx - bar_w/2:.1f}" y="{body_top:.1f}" width="{bar_w:.1f}" height="{body_h:.1f}" fill="{color}" rx="1"/>')
        
        # Volume bar at bottom
        vol_height = random.randint(20, 110)
        if c.get("is_sweep") or c.get("is_displacement"):
            vol_height = random.randint(130, 240)
        vol_y = 1580 - vol_height
        candles_svg.append(f'<rect x="{cx - bar_w/2:.1f}" y="{vol_y}" width="{bar_w:.1f}" height="{vol_height}" fill="{color}" opacity="0.45"/>')

    # Gridlines and price labels
    grid_lines = []
    steps = 8
    for s in range(steps + 1):
        price = min_p + (s / steps) * p_range
        y = price_to_y(price)
        decimals = cfg["price_decimals"]
        price_str = f"{price:.{decimals}f}"
        grid_lines.append(f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1" stroke-dasharray="4 4"/>')
        grid_lines.append(f'<text x="{chart_right + 14}" y="{y + 5:.1f}" fill="#64748b" font-family="monospace" font-size="19" font-weight="600">{price_str}</text>')

    # SMC Institutional Visual Annotations
    annotations = []
    sweep_idx = next((i for i, c in enumerate(candles) if c.get("is_sweep")), 14)
    sweep_candle = candles[sweep_idx]
    sweep_cx = chart_left + (sweep_idx + 0.5) * candle_w
    sweep_cy_high = price_to_y(sweep_candle["high"])
    
    # 1. Equal Highs / Retail Stops Line
    eqh_price = max(c["high"] for c in candles[sweep_idx-6:sweep_idx])
    eqh_y = price_to_y(eqh_price)
    annotations.append(f'''
    <!-- Retail Stops Line -->
    <line x1="{chart_left + 150}" y1="{eqh_y:.1f}" x2="{chart_right - 40}" y2="{eqh_y:.1f}" stroke="#ef4444" stroke-width="2.5" stroke-dasharray="8 6"/>
    <rect x="{chart_left + 220}" y="{eqh_y - 34:.1f}" width="340" height="30" fill="rgba(239,68,68,0.2)" stroke="#ef4444" stroke-width="1.5" rx="6"/>
    <text x="{chart_left + 235}" y="{eqh_y - 14:.1f}" fill="#fca5a5" font-family="sans-serif" font-size="16" font-weight="800">RETAIL STOP LOSSES (EQH POOL)</text>
    ''')

    # 2. Institutional Sweep Callout Marker
    annotations.append(f'''
    <!-- Liquidity Sweep Wick Pointer -->
    <circle cx="{sweep_cx:.1f}" cy="{sweep_cy_high:.1f}" r="8" fill="#facc15" stroke="#ffffff" stroke-width="2"/>
    <rect x="{sweep_cx - 150:.1f}" y="{sweep_cy_high - 85:.1f}" width="300" height="55" fill="rgba(15,23,42,0.92)" stroke="#facc15" stroke-width="2" rx="12" filter="url(#glow)"/>
    <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 58:.1f}" fill="#facc15" font-family="sans-serif" font-size="17" font-weight="900" text-anchor="middle">⚡ LIQUIDITY SWEEP</text>
    <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 40:.1f}" fill="#94a3b8" font-family="monospace" font-size="14" font-weight="700" text-anchor="middle">HIGH-FREQUENCY ALGO HUNT</text>
    <path d="M {sweep_cx:.1f} {sweep_cy_high - 30:.1f} L {sweep_cx:.1f} {sweep_cy_high - 10:.1f}" stroke="#facc15" stroke-width="2.5"/>
    ''')

    # 3. Institutional Order Block (OB) Box
    ob_top_price = eqh_price
    ob_bot_price = eqh_price * 0.993
    ob_y1 = price_to_y(ob_top_price)
    ob_y2 = price_to_y(ob_bot_price)
    annotations.append(f'''
    <!-- Order Block Zone -->
    <rect x="{sweep_cx - 40:.1f}" y="{ob_y1:.1f}" width="420" height="{abs(ob_y2 - ob_y1):.1f}" fill="rgba(6,182,212,0.18)" stroke="#06b6d4" stroke-width="2" rx="8"/>
    <rect x="{sweep_cx - 30:.1f}" y="{ob_y1 + 8:.1f}" width="280" height="26" fill="rgba(6,182,212,0.3)" rx="4"/>
    <text x="{sweep_cx - 20:.1f}" y="{ob_y1 + 26:.1f}" fill="#38bdf8" font-family="sans-serif" font-size="15" font-weight="800">ORDER BLOCK [OB] ZONE</text>
    ''')

    # 4. Asymmetric Risk/Reward Target Arrow (Displacement)
    last_candle = candles[-4]
    last_cx = chart_left + (len(candles) - 4 + 0.5) * candle_w
    last_cy = price_to_y(last_candle["close"])
    annotations.append(f'''
    <!-- Target Hit Arrow -->
    <line x1="{sweep_cx + 40:.1f}" y1="{sweep_cy_high + 60:.1f}" x2="{last_cx - 20:.1f}" y2="{last_cy - 40:.1f}" stroke="#10b981" stroke-width="4" stroke-dasharray="6 4"/>
    <circle cx="{last_cx:.1f}" cy="{last_cy:.1f}" r="10" fill="#10b981"/>
    <rect x="{last_cx - 160:.1f}" y="{last_cy + 25:.1f}" width="220" height="42" fill="rgba(16,185,129,0.2)" stroke="#10b981" stroke-width="1.5" rx="8"/>
    <text x="{last_cx - 50:.1f}" y="{last_cy + 52:.1f}" fill="#6ee7b7" font-family="sans-serif" font-size="18" font-weight="900" text-anchor="middle">🎯 1:3.8 RR HIT</text>
    ''')

    # Top TradingView UI Bar
    tv_bar = f'''
    <!-- TradingView Top Navigation Bar -->
    <rect x="0" y="0" width="{width}" height="140" fill="#0b0f19" opacity="0.95"/>
    <line x1="0" y1="140" x2="{width}" y2="140" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
    
    <text x="60" y="80" fill="#ffffff" font-family="'Outfit', sans-serif" font-size="36" font-weight="900">{cfg["symbol"]}</text>
    <rect x="360" y="52" width="75" height="38" fill="rgba(255,255,255,0.08)" rx="8"/>
    <text x="397" y="78" fill="#38bdf8" font-family="sans-serif" font-size="20" font-weight="800" text-anchor="middle">{cfg["timeframe"]}</text>
    
    <rect x="450" y="52" width="110" height="38" fill="rgba(255,255,255,0.08)" rx="8"/>
    <text x="505" y="78" fill="#cbd5e1" font-family="sans-serif" font-size="20" font-weight="700" text-anchor="middle">Candles</text>

    <text x="{width - 240}" y="80" fill="#94a3b8" font-family="sans-serif" font-size="22" font-weight="700">{cfg["exchange"]}</text>
    <circle cx="{width - 80}" cy="72" r="14" fill="#10b981" opacity="0.8"/>
    '''

    # Volume Sub-Panel Header
    vol_header = f'''
    <line x1="60" y1="1340" x2="{width-60}" y2="1340" stroke="rgba(255,255,255,0.12)" stroke-width="1"/>
    <text x="65" y="1370" fill="#94a3b8" font-family="sans-serif" font-size="18" font-weight="700">Volume Profile (Institutional Delta)</text>
    '''

    # Complete SVG Assembly
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background-color: #030712;">
  <defs>
    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Background Grid -->
  {"".join(grid_lines)}

  <!-- Candlesticks -->
  {"".join(candles_svg)}

  <!-- SMC Annotations -->
  {"".join(annotations)}

  <!-- Volume Sub-Panel -->
  {vol_header}

  <!-- TradingView Top Bar -->
  {tv_bar}
</svg>'''

async def main():
    print("Generating 3 distinct procedural charts: Gold XAU/USD, Euro EUR/USD, Bitcoin BTC/USD...")
    
    assets = ["XAUUSD", "EURUSD", "BTCUSD"]
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="msedge", headless=True)
        page = await browser.new_page(viewport={"width": 1080, "height": 1920})
        
        for asset in assets:
            cfg = ASSET_CONFIGS[asset]
            candles = generate_candlestick_data(base_price=cfg["price_base"], count=30)
            svg_content = render_chart_svg(candles=candles, asset=asset)
            
            temp_svg = CACHE_DIR / f"test_{asset}.svg"
            temp_svg.write_text(svg_content, encoding="utf-8")
            
            out_png = CACHE_DIR / f"procedural_chart_{asset}.png"
            await page.goto(f"file:///{temp_svg.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(out_png), full_page=False)
            print(f"Generated chart for {asset}: {out_png} ({out_png.stat().st_size} bytes)")
            temp_svg.unlink()
            
        await browser.close()
    print("Done generating procedural charts!")

if __name__ == "__main__":
    asyncio.run(main())

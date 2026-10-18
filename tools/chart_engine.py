"""Procedural TradingView Chart & Multi-Scene Storyboard Engine for adham-agent.
Generates razor-sharp, photorealistic 1080x1920 dark-mode TradingView charts
with authentic candlesticks, volume profile, live technical indicators,
and institutional SMC annotations strictly synchronized to video narrative beats.
"""
from __future__ import annotations

import html
import logging
import random
import time
from pathlib import Path
from typing import Any

from playwright.async_api import async_playwright

log = logging.getLogger("chart_engine")

BASE_DIR = Path(__file__).resolve().parent.parent
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
        "theme_gradient": "goldGrad",
        "volatility": 0.0035,
    },
    "BTCUSD": {
        "symbol": "BTC/USDT • BITCOIN",
        "timeframe": "1h",
        "price_base": 68250.0,
        "price_decimals": 1,
        "exchange": "BINANCE",
        "theme_color": "#10b981",
        "theme_gradient": "greenGrad",
        "volatility": 0.0042,
    },
    "EURUSD": {
        "symbol": "EUR/USD",
        "timeframe": "4h",
        "price_base": 1.08450,
        "price_decimals": 5,
        "exchange": "FXCM",
        "theme_color": "#06b6d4",
        "theme_gradient": "cyanGrad",
        "volatility": 0.0018,
    },
    "US100": {
        "symbol": "NAS100 • NASDAQ",
        "timeframe": "5m",
        "price_base": 20420.0,
        "price_decimals": 1,
        "exchange": "CME",
        "theme_color": "#8b5cf6",
        "theme_gradient": "purpleGrad",
        "volatility": 0.0030,
    },
    "ETHUSD": {
        "symbol": "ETH/USDT • ETHEREUM",
        "timeframe": "15m",
        "price_base": 2640.0,
        "price_decimals": 2,
        "exchange": "BINANCE",
        "theme_color": "#38bdf8",
        "theme_gradient": "blueGrad",
        "volatility": 0.0038,
    },
}

ALL_ASSET_KEYS = list(ASSET_CONFIGS.keys())


def detect_or_rotate_asset(query: str = "") -> str:
    """Detects target asset from text, or rotates across assets to guarantee visual variety."""
    q = (query or "").lower()
    if any(k in q for k in ["gold", "xau", "ذهب"]):
        return "XAUUSD"
    if any(k in q for k in ["btc", "bitcoin", "crypto", "بيتكوين", "كريبتو"]):
        return "BTCUSD"
    if any(k in q for k in ["eur", "forex", "currency", "يورو", "فوركس", "عملات"]):
        return "EURUSD"
    if any(k in q for k in ["nasdaq", "nas100", "us100", "tech", "نازداك", "مؤشرات"]):
        return "US100"
    if any(k in q for k in ["eth", "ethereum", "إيثيريوم"]):
        return "ETHUSD"

    # Rotation tracking to ensure consecutive videos use different assets
    last_asset_file = CACHE_DIR / "last_used_asset.txt"
    last_asset = ""
    if last_asset_file.exists():
        try:
            last_asset = last_asset_file.read_text(encoding="utf-8").strip()
        except Exception:
            pass

    available = [a for a in ALL_ASSET_KEYS if a != last_asset]
    chosen = random.choice(available if available else ALL_ASSET_KEYS)
    try:
        last_asset_file.write_text(chosen, encoding="utf-8")
    except Exception:
        pass
    return chosen


def xml_escape(text: str) -> str:
    """Safely escapes text for SVG XML inclusion."""
    return html.escape(str(text), quote=True)


def generate_candlestick_data(base_price: float, count: int = 32, volatility: float = 0.003) -> list[dict[str, Any]]:
    """Generates realistic candlestick series with an institutional liquidity sweep and violent expansion."""
    candles = []
    # Add random offset to base price so identical assets have different levels every time
    p = base_price * (1.0 + (random.random() - 0.5) * 0.02)
    
    # 1. Building accumulation / range (first 14 candles)
    for _ in range(14):
        delta = (random.random() - 0.48) * volatility * p
        o = p
        c = o + delta
        h = max(o, c) + random.random() * volatility * 0.7 * p
        l = min(o, c) - random.random() * volatility * 0.7 * p
        candles.append({"open": o, "high": h, "low": l, "close": c, "is_up": c >= o})
        p = c

    # 2. Equal highs resistance level
    high_level = max(c["high"] for c in candles[-6:])

    # 3. Liquidity sweep candle (wicks high above equal highs, then closes violently bearish)
    sweep_open = p
    sweep_high = high_level + (volatility * 1.8 * p)
    sweep_close = sweep_open - (volatility * 0.9 * p)
    sweep_low = sweep_close - (volatility * 0.3 * p)
    candles.append({
        "open": sweep_open,
        "high": sweep_high,
        "low": sweep_low,
        "close": sweep_close,
        "is_up": False,
        "is_sweep": True,
    })
    p = sweep_close

    # 4. Violent displacement expansion (7 large bearish institutional candles)
    for _ in range(7):
        delta = -1 * (random.random() * 0.7 + 0.6) * volatility * p
        o = p
        c = o + delta
        h = o + random.random() * volatility * 0.2 * p
        l = c - random.random() * volatility * 0.4 * p
        candles.append({
            "open": o,
            "high": h,
            "low": l,
            "close": c,
            "is_up": False,
            "is_displacement": True,
        })
        p = c

    # 5. Consolidation and FVG retest
    for _ in range(count - len(candles)):
        delta = (random.random() - 0.45) * volatility * p
        o = p
        c = o + delta
        h = max(o, c) + random.random() * volatility * 0.3 * p
        l = min(o, c) - random.random() * volatility * 0.3 * p
        candles.append({"open": o, "high": h, "low": l, "close": c, "is_up": c >= o})
        p = c

    return candles


def build_narrative_scene_svg(
    asset_key: str,
    scene_index: int,
    title: str,
    hook: str,
    candles: list[dict[str, Any]],
    is_arabic: bool = False,
    brand_name: str = "Core Trade AI",
    width: int = 1080,
    height: int = 1920,
) -> str:
    """Builds a pixel-perfect, 1080x1920 SVG for a specific scene synchronized to script narration."""
    cfg = ASSET_CONFIGS.get(asset_key, ASSET_CONFIGS["XAUUSD"])

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

    # 1. Candlestick Elements
    candles_svg = []
    for i, c in enumerate(candles):
        cx = chart_left + (i + 0.5) * candle_w
        cy_open = price_to_y(c["open"])
        cy_close = price_to_y(c["close"])
        cy_high = price_to_y(c["high"])
        cy_low = price_to_y(c["low"])
        color = "#10b981" if c["is_up"] else "#ef4444"

        # Candle Wick
        candles_svg.append(
            f'<line x1="{cx:.1f}" y1="{cy_high:.1f}" x2="{cx:.1f}" y2="{cy_low:.1f}" stroke="{color}" stroke-width="2.5" opacity="0.9"/>'
        )
        # Candle Body
        body_top = min(cy_open, cy_close)
        body_h = max(abs(cy_open - cy_close), 2.5)
        candles_svg.append(
            f'<rect x="{cx - bar_w/2:.1f}" y="{body_top:.1f}" width="{bar_w:.1f}" height="{body_h:.1f}" fill="{color}" rx="1"/>'
        )

        # Volume Profile bar
        vol_height = random.randint(30, 90)
        if c.get("is_sweep") or c.get("is_displacement"):
            vol_height = random.randint(140, 240)
        candles_svg.append(
            f'<rect x="{cx - bar_w/2:.1f}" y="{1640 - vol_height}" width="{bar_w:.1f}" height="{vol_height}" fill="{color}" opacity="0.45"/>'
        )

    # 2. Gridlines & Price Scale
    grid_lines = []
    for s in range(7):
        price = min_p + (s / 6) * p_range
        y = price_to_y(price)
        decimals = cfg["price_decimals"]
        grid_lines.append(
            f'<line x1="{chart_left}" y1="{y:.1f}" x2="{chart_right}" y2="{y:.1f}" stroke="rgba(255,255,255,0.06)" stroke-width="1" stroke-dasharray="4 4"/>'
        )
        grid_lines.append(
            f'<text x="{chart_right + 14}" y="{y + 5:.1f}" fill="#64748b" font-family="monospace" font-size="18">{price:.{decimals}f}</text>'
        )

    # Key institutional levels
    sweep_idx = next((i for i, c in enumerate(candles) if c.get("is_sweep")), 14)
    sweep_candle = candles[sweep_idx]
    sweep_cx = chart_left + (sweep_idx + 0.5) * candle_w
    sweep_cy_high = price_to_y(sweep_candle["high"])
    eqh_price = max(c["high"] for c in candles[sweep_idx - 6 : sweep_idx])
    eqh_y = price_to_y(eqh_price)

    # 3. Synchronized Narrative Overlay per Scene
    safe_hook = xml_escape(hook)
    safe_title = xml_escape(title)
    safe_brand = xml_escape(brand_name)

    narrative_overlay = ""
    font_main = "'Cairo', sans-serif" if is_arabic else "'Outfit', 'Inter', sans-serif"

    if scene_index == 0:  # Scene 1: The Hook & The Retail Trap Setup
        badge = "⚠️ فخ سيولة الأفراد (SMC)" if is_arabic else "⚠️ SMC LIQUIDITY TRAP"
        stops_text = "🚨 90% من وقوف الخسارة هنا" if is_arabic else "🚨 90% OF RETAIL STOPS PLACED HERE"

        narrative_overlay = f"""
        <!-- Top Hook Header Card -->
        <rect x="40" y="60" width="1000" height="230" fill="rgba(10,15,29,0.92)" stroke="rgba(255,255,255,0.15)" stroke-width="2" rx="32"/>
        <rect x="40" y="60" width="1000" height="8" fill="{cfg['theme_color']}" rx="4"/>

        <rect x="75" y="90" width="300" height="42" fill="{cfg['theme_color']}" rx="999"/>
        <text x="225" y="118" fill="#ffffff" font-family="{font_main}" font-size="20" font-weight="900" text-anchor="middle">{xml_escape(badge)}</text>
        <text x="965" y="120" fill="#38bdf8" font-family="{font_main}" font-size="24" font-weight="900" text-anchor="end">⚡ {safe_brand}</text>

        <text x="75" y="185" fill="#ffffff" font-family="{font_main}" font-size="42" font-weight="900">{safe_hook}</text>
        <text x="75" y="245" fill="#cbd5e1" font-family="{font_main}" font-size="28" font-weight="700">{safe_title}</text>

        <!-- Equal Highs / Retail Stops Line -->
        <line x1="{chart_left + 80}" y1="{eqh_y:.1f}" x2="{chart_right - 40}" y2="{eqh_y:.1f}" stroke="#ef4444" stroke-width="3" stroke-dasharray="8 6"/>
        <rect x="180" y="{eqh_y - 45:.1f}" width="460" height="42" fill="rgba(239,68,68,0.25)" stroke="#ef4444" stroke-width="2" rx="8"/>
        <text x="410" y="{eqh_y - 17:.1f}" fill="#ffffff" font-family="{font_main}" font-size="19" font-weight="900" text-anchor="middle">{xml_escape(stops_text)}</text>
        """

    elif scene_index == 1:  # Scene 2: The Liquidity Sweep / The Bank Hunt
        badge = "⚡ سحب السيولة المؤسسي" if is_arabic else "⚡ THE LIQUIDITY SWEEP"
        algo_label = "خوارزميات البنوك" if is_arabic else "INSTITUTIONAL ALGO"
        h2_title = "البنوك تبتلع القمم والقيعان" if is_arabic else "Banks Sweep The Highs"
        h2_sub = (
            "تسييل فوري لصفقات الشراء عند الكسر الكاذب وتجميع السيولة"
            if is_arabic
            else "Retail breakout buyers are instantly trapped and liquidated"
        )
        callout_title = "⚡ ذيل سحب السيولة" if is_arabic else "⚡ LIQUIDITY SWEEP WICK"
        callout_sub = "-$48,000,000 تسييل صفقات" if is_arabic else "-$48,000,000 RETAIL LIQUIDATIONS"

        narrative_overlay = f"""
        <!-- Top Hunt Card -->
        <rect x="40" y="60" width="1000" height="220" fill="rgba(15,23,42,0.92)" stroke="#facc15" stroke-width="2" rx="32"/>
        <rect x="75" y="90" width="320" height="42" fill="#ef4444" rx="999"/>
        <text x="235" y="118" fill="#ffffff" font-family="{font_main}" font-size="20" font-weight="900" text-anchor="middle">{xml_escape(badge)}</text>
        <text x="965" y="120" fill="#facc15" font-family="{font_main}" font-size="24" font-weight="900" text-anchor="end">{xml_escape(algo_label)}</text>

        <text x="75" y="185" fill="#ffffff" font-family="{font_main}" font-size="44" font-weight="900">{xml_escape(h2_title)}</text>
        <text x="75" y="235" fill="#fca5a5" font-family="{font_main}" font-size="28" font-weight="700">{xml_escape(h2_sub)}</text>

        <!-- Liquidity Sweep Wick Pointer -->
        <circle cx="{sweep_cx:.1f}" cy="{sweep_cy_high:.1f}" r="14" fill="#facc15" stroke="#ffffff" stroke-width="3"/>
        <rect x="{sweep_cx - 200:.1f}" y="{sweep_cy_high - 110:.1f}" width="400" height="75" fill="rgba(10,15,29,0.95)" stroke="#facc15" stroke-width="2.5" rx="16"/>
        <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 72:.1f}" fill="#facc15" font-family="{font_main}" font-size="22" font-weight="900" text-anchor="middle">{xml_escape(callout_title)}</text>
        <text x="{sweep_cx:.1f}" y="{sweep_cy_high - 45:.1f}" fill="#ef4444" font-family="monospace" font-size="16" font-weight="800" text-anchor="middle">{xml_escape(callout_sub)}</text>
        <path d="M {sweep_cx:.1f} {sweep_cy_high - 35:.1f} L {sweep_cx:.1f} {sweep_cy_high - 15:.1f}" stroke="#facc15" stroke-width="3"/>
        """

    elif scene_index == 2:  # Scene 3: The Smart Money Execution / Order Block Setup
        ob_y1 = price_to_y(eqh_price)
        ob_y2 = price_to_y(eqh_price * 0.993)
        last_cx = chart_left + (len(candles) - 4 + 0.5) * candle_w
        last_cy = price_to_y(candles[-4]["close"])

        badge = "🎯 مخطط الدخول الذكي" if is_arabic else "🎯 SMART MONEY BLUEPRINT"
        winrate = "نسبة النجاح: 86.4%" if is_arabic else "WIN RATE: 86.4%"
        h3_title = "الدخول مع الأوردر بلوك" if is_arabic else "Enter On The Order Block"
        h3_sub = "عائد للمخاطرة 1 إلى 3.5 على الأقل" if is_arabic else "Minimum 1:3.5 Asymmetric Risk-To-Reward"
        ob_label = "منطقة الأوردر بلوك المؤسسي" if is_arabic else "INSTITUTIONAL ORDER BLOCK"
        target_label = "🎯 تم تحقيق الهدف 1:3.8 RR" if is_arabic else "🎯 1:3.8 RR TARGET HIT"

        narrative_overlay = f"""
        <!-- Top Blueprint Card -->
        <rect x="40" y="60" width="1000" height="230" fill="rgba(10,15,29,0.92)" stroke="#10b981" stroke-width="2" rx="32"/>
        <rect x="75" y="90" width="340" height="42" fill="#10b981" rx="999"/>
        <text x="245" y="118" fill="#ffffff" font-family="{font_main}" font-size="20" font-weight="900" text-anchor="middle">{xml_escape(badge)}</text>
        <text x="965" y="120" fill="#34d399" font-family="{font_main}" font-size="24" font-weight="900" text-anchor="end">{xml_escape(winrate)}</text>

        <text x="75" y="185" fill="#ffffff" font-family="{font_main}" font-size="44" font-weight="900">{xml_escape(h3_title)}</text>
        <text x="75" y="235" fill="#6ee7b7" font-family="{font_main}" font-size="28" font-weight="700">{xml_escape(h3_sub)}</text>

        <!-- Order Block Zone Box -->
        <rect x="{sweep_cx - 40:.1f}" y="{ob_y1:.1f}" width="420" height="{abs(ob_y2 - ob_y1):.1f}" fill="rgba(6,182,212,0.25)" stroke="#06b6d4" stroke-width="2.5" rx="8"/>
        <text x="{sweep_cx - 20:.1f}" y="{ob_y1 + 30:.1f}" fill="#38bdf8" font-family="{font_main}" font-size="18" font-weight="900">{xml_escape(ob_label)}</text>

        <!-- Asymmetric Target Line -->
        <line x1="{sweep_cx + 40:.1f}" y1="{sweep_cy_high + 60:.1f}" x2="{last_cx - 20:.1f}" y2="{last_cy - 40:.1f}" stroke="#10b981" stroke-width="4.5" stroke-dasharray="8 6"/>
        <rect x="{last_cx - 180:.1f}" y="{last_cy + 25:.1f}" width="280" height="50" fill="rgba(16,185,129,0.25)" stroke="#10b981" stroke-width="2" rx="10"/>
        <text x="{last_cx - 40:.1f}" y="{last_cy + 58:.1f}" fill="#6ee7b7" font-family="{font_main}" font-size="22" font-weight="900" text-anchor="middle">{xml_escape(target_label)}</text>
        """

    else:  # Scene 4: The Outro / Channel CTA
        badge = "👑 انضم إلى نخبة المتداولين" if is_arabic else "👑 BECOME THE HUNTER"
        outro_head = "توقف عن كونك السيولة" if is_arabic else "Stop Being The Liquidity."
        outro_sub = (
            "تتبع البصمة المؤسسية وخوارزميات البنوك يومياً"
            if is_arabic
            else "Daily Institutional Algorithmic Footprints"
        )
        sub_btn = "اشترك في Core Trade AI" if is_arabic else f"Subscribe to {brand_name}"
        bio_txt = "الرابط بالبايو • دليل استراتيجيات SMC مجاناً" if is_arabic else "Link in Bio • Free SMC Strategy Guide"

        narrative_overlay = f"""
        <!-- Full Screen VIP Terminal Card -->
        <rect x="60" y="280" width="960" height="900" fill="rgba(11,17,32,0.94)" stroke="rgba(255,255,255,0.15)" stroke-width="2" rx="40"/>

        <circle cx="540" cy="460" r="70" fill="url(#cyanGrad)"/>
        <text x="540" y="485" fill="#ffffff" font-family="sans-serif" font-size="65" font-weight="900" text-anchor="middle">⚡</text>

        <rect x="340" y="580" width="400" height="46" fill="url(#goldGrad)" rx="999"/>
        <text x="540" y="612" fill="#ffffff" font-family="{font_main}" font-size="22" font-weight="900" text-anchor="middle">{xml_escape(badge)}</text>

        <text x="540" y="700" fill="#ffffff" font-family="{font_main}" font-size="52" font-weight="900" text-anchor="middle">{xml_escape(outro_head)}</text>
        <text x="540" y="770" fill="#cbd5e1" font-family="{font_main}" font-size="32" font-weight="700" text-anchor="middle">{xml_escape(outro_sub)}</text>

        <rect x="200" y="850" width="680" height="90" fill="url(#cyanGrad)" rx="999"/>
        <text x="540" y="908" fill="#ffffff" font-family="{font_main}" font-size="38" font-weight="900" text-anchor="middle">{xml_escape(sub_btn)}</text>

        <text x="540" y="1030" fill="#94a3b8" font-family="{font_main}" font-size="24" font-weight="700" text-anchor="middle">{xml_escape(bio_txt)}</text>
        """

    # 4. TradingView Top Navigation Bar
    tv_bar = f"""
    <rect x="0" y="0" width="{width}" height="60" fill="#0b0f19" opacity="0.95"/>
    <text x="60" y="38" fill="#94a3b8" font-family="monospace" font-size="18" font-weight="700">{xml_escape(cfg['symbol'])} • {xml_escape(cfg['timeframe'])} • {xml_escape(cfg['exchange'])}</text>
    <circle cx="{width - 60}" cy="30" r="8" fill="#10b981"/>
    """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" style="background-color: #030712;">
  <defs>
    <linearGradient id="cyanGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#06b6d4"/>
      <stop offset="100%" stop-color="#2563eb"/>
    </linearGradient>
    <linearGradient id="goldGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f59e0b"/>
      <stop offset="100%" stop-color="#d97706"/>
    </linearGradient>
    <linearGradient id="greenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#10b981"/>
      <stop offset="100%" stop-color="#059669"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#8b5cf6"/>
      <stop offset="100%" stop-color="#6d28d9"/>
    </linearGradient>
    <linearGradient id="bottomShade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(3,7,18,0)"/>
      <stop offset="60%" stop-color="rgba(3,7,18,0.85)"/>
      <stop offset="100%" stop-color="rgba(3,7,18,0.98)"/>
    </linearGradient>
  </defs>

  <!-- Price Grid -->
  {"".join(grid_lines)}

  <!-- Candlesticks & Volume Profile -->
  {"".join(candles_svg)}

  <!-- Top TradingView Header -->
  {tv_bar}

  <!-- Narrative Overlay -->
  {narrative_overlay}

  <!-- Lower Third Subtitle Protection Gradient -->
  <rect x="0" y="1450" width="{width}" height="470" fill="url(#bottomShade)"/>
</svg>"""


async def render_procedural_scenes(
    topic: str,
    title: str,
    hook: str,
    points: list[str] | None = None,
    is_arabic: bool = False,
    brand_name: str = "Core Trade AI",
) -> tuple[list[Path], str]:
    """Generates 4 narrative scene PNGs strictly reflecting the trading topic and spoken narration.
    
    Returns:
        tuple of (list of 4 PNG paths, chosen asset key)
    """
    asset_key = detect_or_rotate_asset(f"{topic} {title} {hook}")
    cfg = ASSET_CONFIGS[asset_key]
    log.info("Rendering procedural TradingView scenes for asset: %s (%s)", asset_key, cfg["symbol"])

    candles = generate_candlestick_data(base_price=cfg["price_base"], count=32, volatility=cfg["volatility"])
    ts = int(time.time() * 1000)

    rendered_pngs: list[Path] = []

    async with async_playwright() as p:
        try:
            browser = await p.chromium.launch(channel="msedge", headless=True)
        except Exception:
            try:
                browser = await p.chromium.launch(channel="chrome", headless=True)
            except Exception:
                browser = await p.chromium.launch(headless=True)

        page = await browser.new_page(viewport={"width": 1080, "height": 1920})

        for idx in range(4):
            svg_content = build_narrative_scene_svg(
                asset_key=asset_key,
                scene_index=idx,
                title=title,
                hook=hook,
                candles=candles,
                is_arabic=is_arabic,
                brand_name=brand_name,
            )
            temp_svg = CACHE_DIR / f"temp_{ts}_{asset_key}_{idx}.svg"
            out_png = CACHE_DIR / f"storyboard_{ts}_{asset_key}_{idx}.png"

            temp_svg.write_text(svg_content, encoding="utf-8")
            await page.goto(f"file:///{temp_svg.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(out_png), full_page=False)
            rendered_pngs.append(out_png)

            try:
                if temp_svg.exists():
                    temp_svg.unlink()
            except Exception:
                pass

        await browser.close()

    log.info("Successfully rendered 4 procedural scenes for %s: %s", asset_key, [p.name for p in rendered_pngs])
    return rendered_pngs, asset_key

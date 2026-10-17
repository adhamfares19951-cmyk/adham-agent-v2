"""Autonomous AI Video Assembler for adham-agent.
Produces vertical 9:16 (1080x1920) viral Short/Reel/TikTok videos from text scripts.
Combines:
1. Microsoft Azure Neural Voiceover (via edge-tts)
2. High-aesthetic dark-mode glassmorphic 1080x1920 slide cards (HTML/CSS via Playwright or SVG)
3. Standalone FFmpeg 7.1 encoder with smooth zoom motion and audio sync.
Outputs ready-to-post MP4 videos directly sent to Telegram with pre-crafted captions and hashtags.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any
import re

import imageio_ffmpeg
from tools import voice_studio

log = logging.getLogger("video_assembler")

BASE_DIR = Path(__file__).resolve().parent.parent
VIDEOS_DIR = BASE_DIR / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = BASE_DIR / "repos_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _get_ffmpeg_path() -> str:
    """Returns the bundled standalone FFmpeg binary."""
    return imageio_ffmpeg.get_ffmpeg_exe()


async def render_html_card(
    title: str,
    hook: str,
    points: list[str],
    cta: str,
    output_png: Path,
    brand: str = "Adham Tech | الذكاء الاصطناعي",
    badge: str = "🔥 حصرياً 2026",
) -> Path:
    """Renders a sleek, vertical 1080x1920 slide card using Playwright or fallback SVG."""
    is_en = bool(re.search(r"[a-zA-Z]{4,}", title + " " + hook))
    dir_attr = "ltr" if is_en else "rtl"
    lang_attr = "en" if is_en else "ar"
    font_family = "'Outfit', 'Inter', sans-serif" if is_en else "'Cairo', sans-serif"

    brand_html = brand if brand != "Adham Tech | الذكاء الاصطناعي" else ("Core <span>Trade</span> AI" if is_en else "Adham<span>AI</span> • Studio")
    sub_cta_text = "Subscribe to Core Trade AI • Track Smart Money Algorithmic Footprints" if is_en else "الرابط بالبايو • تابع الحساب لتصلك أحدث أدوات الذكاء الاصطناعي"

    bg_img = VIDEOS_DIR / "terminal_bg.jpg"
    bg_css = f"background: linear-gradient(rgba(11, 15, 25, 0.85), rgba(3, 7, 18, 0.94)), url('file:///{bg_img.as_posix()}') center/cover no-repeat;" if (bg_img.exists() and is_en) else "background: radial-gradient(circle at 50% 15%, #1e1b4b 0%, #0b0f19 50%, #030712 100%);"

    html_content = f"""<!DOCTYPE html>
<html lang="{lang_attr}" dir="{dir_attr}">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Outfit:wght@600;800;900&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1920px;
    {bg_css}
    color: #f8fafc;
    font-family: {font_family};
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 100px 70px;
    position: relative;
    overflow: hidden;
  }}

  /* Glowing background orbs */
  .orb-1 {{
    position: absolute;
    top: -150px;
    left: 50%;
    transform: translateX(-50%);
    width: 700px;
    height: 700px;
    background: radial-gradient(circle, rgba(99, 102, 241, 0.25) 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
  }}
  .orb-2 {{
    position: absolute;
    bottom: 200px;
    right: -100px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(168, 85, 247, 0.2) 0%, transparent 70%);
    filter: blur(80px);
    pointer-events: none;
  }}

  /* Header */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 10;
  }}
  .badge {{
    background: linear-gradient(135deg, #f59e0b, #ef4444);
    color: #ffffff;
    font-size: 32px;
    font-weight: 900;
    padding: 12px 34px;
    border-radius: 999px;
    box-shadow: 0 10px 25px rgba(239, 68, 68, 0.4);
    letter-spacing: 0.5px;
  }}
  .brand {{
    font-family: 'Outfit', sans-serif;
    font-size: 34px;
    font-weight: 800;
    color: #94a3b8;
    display: flex;
    align-items: center;
    gap: 12px;
  }}
  .brand span {{
    color: #38bdf8;
  }}

  /* Hero Hook */
  .hero-box {{
    z-index: 10;
    margin-top: 40px;
    background: rgba(30, 41, 59, 0.6);
    border: 2px solid rgba(148, 163, 184, 0.2);
    border-radius: 40px;
    padding: 60px 50px;
    backdrop-filter: blur(20px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  }}
  .hook {{
    font-size: 58px;
    font-weight: 900;
    line-height: 1.35;
    background: linear-gradient(135deg, #ffffff 30%, #38bdf8 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 10px 30px rgba(56, 189, 248, 0.2);
    margin-bottom: 25px;
  }}
  .title {{
    font-size: 38px;
    font-weight: 700;
    color: #cbd5e1;
    line-height: 1.5;
  }}

  /* Content Cards */
  .features-container {{
    z-index: 10;
    display: flex;
    flex-direction: column;
    gap: 30px;
    margin: 40px 0;
  }}
  .feature-item {{
    display: flex;
    align-items: center;
    gap: 30px;
    background: rgba(15, 23, 42, 0.75);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 30px;
    padding: 35px 40px;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
  }}
  .feature-icon {{
    width: 75px;
    height: 75px;
    border-radius: 22px;
    background: linear-gradient(135deg, #6366f1, #a855f7);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 38px;
    flex-shrink: 0;
    box-shadow: 0 10px 20px rgba(99, 102, 241, 0.4);
  }}
  .feature-text {{
    font-size: 40px;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1.4;
  }}

  /* Footer CTA */
  .footer-cta {{
    z-index: 10;
    background: linear-gradient(135deg, #4f46e5, #7c3aed);
    border-radius: 35px;
    padding: 45px 50px;
    text-align: center;
    box-shadow: 0 20px 40px rgba(124, 58, 237, 0.4);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }}
  .cta-text {{
    font-size: 46px;
    font-weight: 900;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
  }}
  .cta-sub {{
    font-size: 28px;
    color: #e0e7ff;
    margin-top: 10px;
    font-weight: 600;
  }}
</style>
</head>
<body>
  <div class="orb-1"></div>
  <div class="orb-2"></div>

  <div class="header">
    <div class="badge">{badge}</div>
    <div class="brand">{brand_html}</div>
  </div>

  <div class="hero-box">
    <div class="hook">{hook}</div>
    <div class="title">{title}</div>
  </div>

  <div class="features-container">
"""
    icons = ["⚡", "🚀", "💡", "🎯", "🛡️"]
    for i, p in enumerate(points[:4]):
        icon = icons[i % len(icons)]
        html_content += f"""
    <div class="feature-item">
      <div class="feature-icon">{icon}</div>
      <div class="feature-text">{p}</div>
    </div>
"""

    html_content += f"""
  </div>

  <div class="footer-cta">
    <div class="cta-text">🔥 {cta}</div>
    <div class="cta-sub">{sub_cta_text}</div>
  </div>
</body>
</html>
"""

    temp_html = CACHE_DIR / f"card_{int(time.time()*1000)}.html"
    temp_html.write_text(html_content, encoding="utf-8")

    # Render with Playwright at 1080x1920 using system browser
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                try:
                    browser = await p.chromium.launch(channel="chrome", headless=True)
                except Exception:
                    browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1080, "height": 1920})
            await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(output_png), full_page=False)
            await browser.close()
    except Exception as e:
        log.warning("Playwright rendering failed (%s); generating SVG fallback...", e)
        _render_svg_fallback(title, hook, points, cta, output_png)
    finally:
        try:
            if temp_html.exists():
                temp_html.unlink()
        except Exception:
            pass

    return output_png


def _render_svg_fallback(title: str, hook: str, points: list[str], cta: str, output_png: Path) -> Path:
    """Generates an image via FFmpeg if Playwright is unavailable."""
    ffmpeg = _get_ffmpeg_path()
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi",
        "-i", "color=c=#0f172a:s=1080x1920",
        "-frames:v", "1",
        str(output_png)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_png


async def render_trading_chart_slide(
    title: str,
    hook: str,
    output_png: Path,
    badge: str = "⚠️ SMC LIQUIDITY TRAP",
) -> Path:
    """Renders an elite 1080x1920 institutional TradingView chart slide with a sleek top hook card."""
    txt = (title + " " + hook + " " + badge).lower()
    if any(k in txt for k in ["order block", "ob", "accumulation", "btc", "crypto"]):
        chart_img = VIDEOS_DIR / "chart_order_block.jpg"
        theme_color = "#06b6d4"  # cyan
        theme_glow = "rgba(6, 182, 212, 0.45)"
        theme_grad = "linear-gradient(135deg, #06b6d4, #0284c7)"
        highlight_color = "#38bdf8"
        effective_badge = badge if badge != "⚠️ SMC LIQUIDITY TRAP" else "⚡ INSTITUTIONAL ORDER BLOCK"
    elif any(k in txt for k in ["fvg", "gap", "imbalance", "eur", "fair value"]):
        chart_img = VIDEOS_DIR / "chart_fvg.jpg"
        theme_color = "#d946ef"  # magenta
        theme_glow = "rgba(217, 70, 239, 0.45)"
        theme_grad = "linear-gradient(135deg, #d946ef, #a855f7)"
        highlight_color = "#f472b6"
        effective_badge = badge if badge != "⚠️ SMC LIQUIDITY TRAP" else "🔮 FAIR VALUE GAP (FVG)"
    elif any(k in txt for k in ["gold", "xau", "equal high", "pool"]):
        chart_img = VIDEOS_DIR / "chart_gold_trap.jpg"
        theme_color = "#eab308"  # gold
        theme_glow = "rgba(234, 179, 8, 0.45)"
        theme_grad = "linear-gradient(135deg, #eab308, #ca8a04)"
        highlight_color = "#fef08a"
        effective_badge = badge if badge != "⚠️ SMC LIQUIDITY TRAP" else "👑 GOLD LIQUIDITY POOL"
    else:
        chart_img = VIDEOS_DIR / "chart_liquidity_sweep.jpg"
        theme_color = "#ef4444"  # crimson
        theme_glow = "rgba(239, 68, 68, 0.45)"
        theme_grad = "linear-gradient(135deg, #ef4444, #dc2626)"
        highlight_color = "#facc15"
        effective_badge = badge

    if not chart_img.exists():
        chart_img = VIDEOS_DIR / "chart_liquidity_sweep.jpg"
    if not chart_img.exists():
        chart_img = VIDEOS_DIR / "terminal_bg.jpg"

    # Format hook title with dynamic highlight
    words = hook.split()
    if len(words) > 3:
        highlight_idx = max(len(words) // 2, 2)
        hook_formatted = " ".join(words[:highlight_idx]) + f" <span>{' '.join(words[highlight_idx:])}</span>"
    else:
        hook_formatted = f"<span>{hook}</span>"

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
    background: url('file:///{chart_img.as_posix()}') center center / cover no-repeat;
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
    border-top: 3px solid {theme_color};
    border-radius: 28px;
    padding: 30px 36px;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.7), 0 0 30px {theme_glow};
    z-index: 20;
  }}
  .badge-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 14px;
  }}
  .badge {{
    background: {theme_grad};
    color: #ffffff;
    font-size: 22px;
    font-weight: 800;
    padding: 8px 22px;
    border-radius: 999px;
    letter-spacing: 1px;
    text-transform: uppercase;
    box-shadow: 0 4px 15px {theme_glow};
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
    color: {highlight_color};
    text-shadow: 0 0 25px {theme_glow};
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
      <div class="badge">{effective_badge}</div>
      <div class="channel-pill">⚡ Core Trade AI</div>
    </div>
    <div class="hook-title">{hook_formatted}</div>
  </div>
  
  <div class="bottom-shade"></div>
  
  <div class="watermark">
    <span>@CoreTradeAI</span> • Institutional Algo Hub
  </div>
</body>
</html>"""

    temp_html = CACHE_DIR / f"trading_slide_{int(time.time()*1000)}.html"
    temp_html.write_text(html, encoding="utf-8")

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            try:
                browser = await p.chromium.launch(channel="msedge", headless=True)
            except Exception:
                try:
                    browser = await p.chromium.launch(channel="chrome", headless=True)
                except Exception:
                    browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1080, "height": 1920})
            await page.goto(f"file:///{temp_html.as_posix()}", wait_until="networkidle")
            await page.screenshot(path=str(output_png), full_page=False)
            await browser.close()
    finally:
        try:
            if temp_html.exists():
                temp_html.unlink()
        except Exception:
            pass

    return output_png


async def assemble_short_video(
    title: str,
    hook: str,
    points: list[str],
    script_narration: str,
    cta: str = "احصل على الكود والروابط كاملة بالبايو!",
    voice_key: str = "ar_male_egypt",
    badge: str = "🔥 حصرياً 2026",
) -> dict[str, Any]:
    """Generates a complete 9:16 vertical video with synchronized voiceover.
    
    Returns:
        dict containing video_path, audio_path, caption, hashtags, and metadata.
    """
    ts = int(time.time())
    output_png = CACHE_DIR / f"slide_{ts}.png"
    output_mp4 = VIDEOS_DIR / f"video_{ts}.mp4"

    TRADING_KEYWORDS = [
        "trade", "trading", "forex", "crypto", "smc", "liquidity", "sweep",
        "stop loss", "order block", "fvg", "gold", "xau", "btc", "smart money", "core trade"
    ]
    is_trading = any(k in (title + " " + hook + " " + script_narration).lower() for k in TRADING_KEYWORDS)

    # 1. Generate Voiceover via Edge-TTS
    log.info("Generating voiceover for script...")
    audio_path = await voice_studio.generate_speech(text=script_narration, voice_key=voice_key)
    if not audio_path.exists():
        raise RuntimeError(f"Voiceover generation failed: {audio_path}")

    # 1b. Mix Lo-Fi Tech BGM with auto-ducking
    final_audio = audio_path
    bgm_audio = VIDEOS_DIR / f"audio_bgm_{ts}.wav"
    try:
        from tools import media_studio
        await media_studio.mix_audio_with_ambient_bgm(audio_path, bgm_audio, bgm_volume=0.13)
        if bgm_audio.exists():
            final_audio = bgm_audio
            log.info("Lo-Fi BGM mixed successfully with voiceover.")
    except Exception as e:
        log.warning("BGM mix skipped or failed: %s", e)

    # 2. Render 1080x1920 Slide Card
    if is_trading:
        log.info("Trading content detected! Rendering High-Impact Trading Terminal Slide...")
        await render_trading_chart_slide(
            title=title,
            hook=hook,
            output_png=output_png,
            badge=badge if badge != "🔥 حصرياً 2026" else "⚠️ SMC LIQUIDITY TRAP"
        )
    else:
        log.info("Rendering 1080x1920 visual slide card...")
        await render_html_card(
            title=title,
            hook=hook,
            points=points,
            cta=cta,
            output_png=output_png,
            badge=badge,
        )

    # 3. Assemble with FFmpeg (Image + Audio + Zoom Motion)
    ffmpeg = _get_ffmpeg_path()
    log.info("Assembling video with FFmpeg: %s", ffmpeg)

    # Subtle slow zoom filter for dynamic reel engagement
    cmd = [
        ffmpeg, "-y",
        "-loop", "1",
        "-i", str(output_png),
        "-i", str(final_audio),
        "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0003,1.06)':d=750:x='iw/2-(iw/zoom/2)':y='ih*0.35-(ih/zoom*0.35)':s=1080x1920:fps=30",
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_mp4)
    ]

    proc = await asyncio.to_thread(
        subprocess.run,
        cmd,
        capture_output=True,
        text=True
    )

    if proc.returncode != 0:
        log.error("FFmpeg assembly error: %s", proc.stderr)
        # Fallback without zoompan if zoompan fails
        cmd_fallback = [
            ffmpeg, "-y",
            "-loop", "1",
            "-i", str(output_png),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            str(output_mp4)
        ]
        proc_fb = await asyncio.to_thread(subprocess.run, cmd_fallback, capture_output=True, text=True)
        if proc_fb.returncode != 0:
            raise RuntimeError(f"FFmpeg failed to create video: {proc_fb.stderr}")

    # Clean temporary PNG
    try:
        if output_png.exists():
            output_png.unlink()
    except Exception:
        pass

    # Craft viral social media caption with tags
    caption = (
        f"🚨 {hook}\n\n"
        f"📌 {title}\n"
        f"الميزات الأساسية:\n" + "\n".join(f"▫️ {p}" for p in points) + "\n\n"
        f"🔗 {cta}\n\n"
        f"#ذكاء_اصطناعي #برمجة #تقنية #fyp #ai_tools #تطوير_برمجيات #shorts #reels"
    )

    size_mb = output_mp4.stat().st_size / (1024 * 1024)

    return {
        "success": True,
        "video_path": str(output_mp4),
        "audio_path": str(audio_path),
        "duration_estimate": "synced to voiceover",
        "file_size_mb": round(size_mb, 2),
        "caption": caption,
        "title": title,
        "hook": hook,
    }


# ==============================================================================
# Agent Tool Handlers
# ==============================================================================

async def video_creator_handler(args: dict) -> str:
    """Tool handler for AI Agent to build and render viral videos."""
    title = args.get("title", "أداة ذكاء اصطناعي ثورية")
    hook = args.get("hook", "هل تعلم أنك تستطيع توفير آلاف الدولارات بهذا الكود؟")
    points = args.get("points", ["مجاني 100%", "يعمل محلياً بدون خوادم مكلفة", "ربط سريع بنقرة واحدة"])
    if isinstance(points, str):
        points = [p.strip() for p in points.split(",") if p.strip()]

    script = args.get("script_narration")
    if not script:
        script = f"{hook}. {title}. أهم النقاط: " + ". ".join(points) + ". الرابط بانتظارك في البايو!"

    cta = args.get("cta", "الرابط مثبت بالبايو أو راسلنا على تلجرام!")
    voice_key = args.get("voice_key", "ar_male_egypt")
    badge = args.get("badge", "🔥 حصرياً 2026")

    try:
        res = await assemble_short_video(
            title=title,
            hook=hook,
            points=points,
            script_narration=script,
            cta=cta,
            voice_key=voice_key,
            badge=badge,
        )
        return (
            f"🎬 **تم إنشاء ورندرة الفيديو بنجاح!**\n\n"
            f"📁 **مسار ملف الفيديو MP4:** `{res['video_path']}`\n"
            f"⚖️ **حجم الفيديو:** {res['file_size_mb']} MB (جاهز للمشاركة الفورية على تيك توك، ريلز، وشورتس)\n\n"
            f"📝 **الكابشن والهاشتاجات الجاهزة للنشر:**\n"
            f"```text\n{res['caption']}\n```"
        )
    except Exception as e:
        log.exception("Video creator handler failed")
        return f"❌ فشل إنشاء الفيديو: {e}"


async def autonomous_publish_short(
    topic: str = "",
    title: str = "",
    hook: str = "",
    script: str = "",
    points: list[str] | None = None,
    language: str = "en",
    privacy: str = "public",
) -> dict[str, Any]:
    """Generates, subtitles, and publishes an institutional trading YouTube Short end-to-end."""
    import random

    CURATED_TOPICS = [
        {
            "topic": "liquidity sweeps",
            "title": "The Secret of Liquidity Sweeps",
            "hook": "Why do banks always hunt your Stop Loss?",
            "script": "Retail traders place stop losses at obvious levels. Institutional algorithms sweep those levels to fill massive orders. At Core Trade AI, we track the smart money footprint. Stop being the liquidity, become the hunter. Subscribe to Core Trade AI.",
            "points": ["Smart Money Concepts", "Liquidity Tracking", "Algorithmic Precision"],
        },
        {
            "topic": "order blocks",
            "title": "Institutional Order Blocks Revealed",
            "hook": "Where do hedge funds actually enter the market?",
            "script": "Hedge funds don't chase green candles. They accumulate massive positions inside hidden Order Blocks before the markup phase. Stop guessing reversals on retail indicators. Follow smart money volume. Subscribe to Core Trade AI.",
            "points": ["Institutional Footprint", "Order Block Zones", "High Probability Entries"],
        },
        {
            "topic": "fair value gaps",
            "title": "The Power of Fair Value Gaps",
            "hook": "Why does price always return to Fair Value Gaps?",
            "script": "When high-frequency algorithms inject sudden momentum, they create price imbalances known as Fair Value Gaps. Price returns like a magnet to rebalance liquidity. Learn to trade with institutional flow. Subscribe to Core Trade AI.",
            "points": ["Market Imbalances", "Algorithmic Magnets", "Precision Re-entries"],
        },
        {
            "topic": "stop loss hunting",
            "title": "The 90% Stop Loss Trap",
            "hook": "Are market makers hunting your Stop Loss?",
            "script": "Your stop loss is an institutional target. Algorithms engineered by Wall Street trigger retail liquidations before expanding toward true targets. Trade alongside institutional volume, not against it. Subscribe to Core Trade AI.",
            "points": ["Liquidity Engineering", "Stop Hunt Mechanics", "Smart Money Footprint"],
        },
        {
            "topic": "gold xauusd",
            "title": "Trading Gold Like Institutions",
            "hook": "Why does Gold respect Liquidity Pools?",
            "script": "Gold is the most algorithmic asset in financial markets. It seeks liquidity above equal highs and below equal lows before reversing with speed. Stop chasing breakouts; wait for the sweep. Subscribe to Core Trade AI.",
            "points": ["XAUUSD Liquidity", "Equal Highs & Lows", "Institutional Timing"],
        },
    ]

    t_lower = (topic or "").lower()
    matched = None
    for item in CURATED_TOPICS:
        if any(kw in t_lower for kw in item["topic"].split()):
            matched = item
            break

    if not matched:
        matched = random.choice(CURATED_TOPICS)

    final_title = title or matched["title"]
    final_hook = hook or matched["hook"]
    final_script = script or matched["script"]
    final_points = points or matched["points"]

    is_english = language == "en" or bool(re.search(r"[a-zA-Z]{4,}", final_script))
    voice_key = "en_male_tech" if is_english else "ar_male_egypt"
    badge = "🔥 Core Trade AI" if is_english else "🔥 حصرياً 2026"
    cta = "Subscribe to Core Trade AI!" if is_english else "الرابط بالبايو!"

    # 1. Assemble raw video with TradingView background + voiceover + Lo-Fi music
    res_v = await assemble_short_video(
        title=final_title,
        hook=final_hook,
        points=final_points,
        script_narration=final_script,
        cta=cta,
        voice_key=voice_key,
        badge=badge,
    )
    v_path = Path(res_v["video_path"])

    # 2. Burn karaoke word-by-word subtitles
    from tools import video_autocaption, youtube_publisher
    res_c = await video_autocaption.burn_karaoke_subtitles(v_path, language="en" if is_english else "ar")
    final_video = Path(res_c["video_path"])

    # 3. Upload to YouTube Channel
    yt_res = await youtube_publisher.upload_video(
        video_path=final_video,
        title=f"{final_title} #Shorts",
        description=f"{final_hook}\n\n{final_script}\n\n#Shorts #Trading #SMC #Forex #CoreTradeAI #Crypto #Finance",
        privacy_status=privacy,
        is_short=True,
    )

    return {
        "success": True,
        "title": yt_res["title"],
        "youtube_url": yt_res["url"],
        "video_path": str(final_video),
        "hook": final_hook,
        "script": final_script,
    }


async def publish_trading_short_handler(args: dict) -> str:
    """Agent tool handler for end-to-end creation and YouTube publishing."""
    topic = args.get("topic", "")
    title = args.get("title", "")
    hook = args.get("hook", "")
    script = args.get("script", "")
    language = args.get("language", "en")

    try:
        res = await autonomous_publish_short(
            topic=topic,
            title=title,
            hook=hook,
            script=script,
            language=language,
        )
        return (
            f"🎉 **تم إنشاء ورندرة ونشر فيديو الشورتس بنجاح على قناة يوتيوب!**\n\n"
            f"🎬 **العنوان:** {res['title']}\n"
            f"🔗 **رابط المشاهدة على يوتيوب:** {res['youtube_url']}\n"
            f"📁 **مسار الفيديو المولد:** `{res['video_path']}`\n\n"
            f"⚡ تم تفعيل شارت TradingView حقيقي وموسيقى تقنية لو فاي وكابشن كاريوكي نيون."
        )
    except Exception as e:
        log.exception("Publish trading short tool failed")
        return f"❌ فشل إنشاء ونشر الشورتس: {e}"


TOOLS = [
    {
        "name": "create_viral_short_video",
        "description": (
            "توليد ورندرة فيديو قصير عمودي (9:16 Shorts/Reels/TikTok) كامل وبأعلى جودة، مع تعليق صوتي طبيعي متزامن، "
            "وبطاقات جرافيك احترافية مخصصة، مع تجهيز الكابشن والهاشتاجات الجاهزة للنشر لجلب الزيارات والأرباح."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "عنوان الفيديو الأساسي أو اسم الأداة"},
                "hook": {"type": "string", "description": "الجملة الافتتاحية الجذابة (Hook) لجذب الانتباه في أول 3 ثوانٍ"},
                "points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "قائمة النقاط والمزايا المعروضة في الفيديو (2-4 نقاط)",
                },
                "script_narration": {
                    "type": "string",
                    "description": "نص الاسكريبت الكامل الذي سينطقه المعلق الصوتي باللغة العربية أو الإنجليزية",
                },
                "cta": {"type": "string", "description": "الدعوة لاتخاذ إجراء (Call To Action) مثل: الرابط بالبايو"},
                "voice_key": {
                    "type": "string",
                    "description": "نبرة الصوت: ar_male_egypt (مصري حماسي), ar_male_gulf (خليجي رسمي), en_male_tech (إنجليزي تقني)",
                },
                "badge": {"type": "string", "description": "شارة العرض أعلى الفيديو (مثال: '🔥 أداة مجانية 2026')"},
            },
            "required": ["title", "hook", "script_narration"],
        },
        "handler": video_creator_handler,
    },
    {
        "name": "create_and_publish_trading_short",
        "description": (
            "ينشئ وينشر فيديو شورتس كامل تلقائياً ومباشرة على قناة يوتيوب (Core Trade AI): "
            "صوت عصبي + شارت TradingView حقيقي 1080x1920 + موسيقى Lo-Fi محيطية + كابشن كاريوكي نيون + رفع فوري إلى يوتيوب. "
            "يكفي تمرير موضوع الفيديو (topic) أو فكرته وسيتولى كل شيء من الألف إلى الياء."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "موضوع الفيديو (مثال: 'Liquidity Sweeps', 'Order Blocks', 'Stop Loss Hunting', 'Fair Value Gaps', 'Gold Trading')"},
                "title": {"type": "string", "description": "عنوان مخصص اختياري"},
                "hook": {"type": "string", "description": "خطاف مخصص اختياري"},
                "script": {"type": "string", "description": "اسكريبت مخصص اختياري"},
                "language": {"type": "string", "enum": ["en", "ar"], "description": "اللغة (en لقناة Core Trade AI أو ar)"},
            },
        },
        "handler": publish_trading_short_handler,
    },
]

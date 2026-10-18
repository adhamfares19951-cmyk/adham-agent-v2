"""Autonomous AI Video Assembler & Multi-Scene Storyboard Engine for adham-agent.
Produces vertical 9:16 (1080x1920) viral Short/Reel/TikTok videos from text scripts.

Features:
1. Dynamic 4-Scene Storyboard Architecture (Hook, Trap/Problem, Smart Setup/Solution, Outro/CTA)
   - Switches visual charts and backgrounds across 4 timed narrative cuts per video
   - Guarantees visual diversity across consecutive videos with 5 neon theme palettes and rotated chart assets
2. Edge Neural Voiceover (Microsoft Azure Neural TTS) + Ambient Lo-Fi Background Music with Auto-Ducking
3. Millisecond-precision ASS Karaoke Word-by-Word Subtitles (via Groq Whisper large-v3)
4. Instant FFmpeg Multi-Segment Concat (~1-2s render time)
5. Automated Dual-Publishing to both YouTube Shorts and TikTok Creator Center
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import random
import re
import subprocess
import time
from pathlib import Path
from typing import Any

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


THEME_PALETTES = [
    {
        "name": "cyber_cyan",
        "primary": "#06b6d4",
        "secondary": "#38bdf8",
        "glow": "rgba(6, 182, 212, 0.45)",
        "gradient": "linear-gradient(135deg, #06b6d4, #0284c7)",
        "highlight": "#67e8f9",
    },
    {
        "name": "crimson_alert",
        "primary": "#ef4444",
        "secondary": "#f87171",
        "glow": "rgba(239, 68, 68, 0.45)",
        "gradient": "linear-gradient(135deg, #ef4444, #dc2626)",
        "highlight": "#fca5a5",
    },
    {
        "name": "golden_bull",
        "primary": "#eab308",
        "secondary": "#facc15",
        "glow": "rgba(234, 179, 8, 0.45)",
        "gradient": "linear-gradient(135deg, #eab308, #ca8a04)",
        "highlight": "#fef08a",
    },
    {
        "name": "neon_emerald",
        "primary": "#10b981",
        "secondary": "#34d399",
        "glow": "rgba(16, 185, 129, 0.45)",
        "gradient": "linear-gradient(135deg, #10b981, #059669)",
        "highlight": "#6ee7b7",
    },
    {
        "name": "electric_violet",
        "primary": "#8b5cf6",
        "secondary": "#a855f7",
        "glow": "rgba(139, 92, 246, 0.45)",
        "gradient": "linear-gradient(135deg, #8b5cf6, #7c3aed)",
        "highlight": "#d8b4fe",
    },
]

AVAILABLE_CHARTS = [
    VIDEOS_DIR / "chart_liquidity_sweep.jpg",
    VIDEOS_DIR / "chart_order_block.jpg",
    VIDEOS_DIR / "chart_fvg.jpg",
    VIDEOS_DIR / "chart_gold_trap.jpg",
    VIDEOS_DIR / "terminal_bg.jpg",
]


def _probe_audio_duration(audio_path: Path) -> float:
    """Probes exact audio duration in seconds using FFmpeg banner output."""
    ffmpeg = _get_ffmpeg_path()
    res = subprocess.run([ffmpeg, "-i", str(audio_path)], stderr=subprocess.PIPE, text=True)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", res.stderr)
    if m:
        return float(m.group(1)) * 3600 + float(m.group(2)) * 60 + float(m.group(3))
    return 25.0


def render_scene_html(
    scene_type: str,
    title: str,
    hook: str,
    points: list[str],
    bg_image_path: Path,
    theme: dict[str, str],
    is_arabic: bool = False,
    brand_name: str = "Core Trade AI",
) -> str:
    """Generates hyper-modern 1080x1920 HTML for a specific video scene cut."""
    lang_attr = "ar" if is_arabic else "en"
    dir_attr = "rtl" if is_arabic else "ltr"
    font_family = "'Cairo', sans-serif" if is_arabic else "'Outfit', 'Inter', sans-serif"
    bg_url = f"file:///{bg_image_path.as_posix()}"

    s_col = theme["secondary"]
    glow = theme["glow"]
    grad = theme["gradient"]

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
        alert_text = "🛑 تجنب الشراء عند الكسر الكاذب" if is_arabic else "🛑 STOP BUYING THE BREAKOUT TRAP"
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
            <span>{alert_text}</span>
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
  .headline-danger {{ color: #fca5a5; }}
  .headline-success {{ color: #6ee7b7; }}
  .headline-gold {{ color: #fef08a; }}

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
  .item-icon {{ font-size: 36px; }}
  .item-text {{
    font-size: 32px;
    font-weight: 800;
    color: #f1f5f9;
  }}

  /* Outro Card */
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
    <span dir="ltr">@{brand_name.replace(' ', '')}</span> • Institutional Market Intelligence
  </div>
</body>
</html>"""


async def render_storyboard_scenes(
    title: str,
    hook: str,
    points: list[str],
    is_arabic: bool = False,
    brand_name: str = "Core Trade AI",
    topic: str = "",
) -> tuple[list[Path], str]:
    """Renders 4 distinct procedural 1080x1920 TradingView scenes strictly synchronized to narrative beats."""
    from tools import chart_engine
    return await chart_engine.render_procedural_scenes(
        topic=topic or title,
        title=title,
        hook=hook,
        points=points,
        is_arabic=is_arabic,
        brand_name=brand_name,
    )


async def assemble_short_video(
    title: str,
    hook: str,
    points: list[str],
    script_narration: str,
    cta: str = "احصل على الكود والروابط كاملة بالبايو!",
    voice_key: str = "ar_male_egypt",
    badge: str = "🔥 حصرياً 2026",
    topic: str = "",
) -> dict[str, Any]:
    """Generates a complete dynamic 4-scene 9:16 vertical video with synchronized voiceover & BGM.
    
    Returns:
        dict containing video_path, audio_path, caption, hashtags, and metadata.
    """
    ts = int(time.time())
    output_mp4 = VIDEOS_DIR / f"video_{ts}.mp4"

    is_arabic = bool(re.search(r"[\u0600-\u06FF]", title + " " + hook + " " + script_narration))
    brand_name = "Core Trade AI" if not is_arabic else "Adham AI • Studio"

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

    # 2. Probe exact audio duration
    total_dur = _probe_audio_duration(final_audio)
    log.info("Total audio duration: %.2f seconds", total_dur)

    # Proportional durations across the 4 narrative scenes
    d1 = round(total_dur * 0.22, 2)
    d2 = round(total_dur * 0.30, 2)
    d3 = round(total_dur * 0.30, 2)
    d4 = round(total_dur - d1 - d2 - d3, 2)
    durations = [d1, d2, d3, d4]

    # 3. Render 4 Procedural TradingView Scenes strictly matching narration
    log.info("Rendering 4 procedural TradingView scene slides...")
    scene_pngs, asset_used = await render_storyboard_scenes(
        title=title,
        hook=hook,
        points=points,
        is_arabic=is_arabic,
        brand_name=brand_name,
        topic=topic,
    )

    # 4. Assemble Segments with Cinematic Micro-Motion via FFmpeg
    ffmpeg = _get_ffmpeg_path()
    segment_files: list[Path] = []
    
    pan_filters = [
        "zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)':y='ih*0.4-(ih/zoom*0.4)':d={frames}:s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0008,1.08)':x='iw/2-(iw/zoom/2)':y='ih*0.3-(ih/zoom*0.3)':d={frames}:s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0006,1.06)':x='iw/2-(iw/zoom/2)':y='ih*0.6-(ih/zoom*0.6)':d={frames}:s=1080x1920:fps=30",
        "zoompan=z='min(zoom+0.0005,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=30",
    ]

    try:
        for idx, (png, dur) in enumerate(zip(scene_pngs, durations)):
            seg = CACHE_DIR / f"seg_{ts}_{idx}.mp4"
            frames = int(dur * 30)
            vf_filter = pan_filters[idx % len(pan_filters)].format(frames=frames)
            
            # Attempt cinematic zoompan; fallback to stillimage loop if needed
            cmd_seg = [
                ffmpeg, "-y",
                "-loop", "1",
                "-i", str(png),
                "-vf", vf_filter,
                "-t", str(dur),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                str(seg)
            ]
            res = await asyncio.to_thread(subprocess.run, cmd_seg, capture_output=True)
            if res.returncode != 0:
                log.warning("Zoompan filter failed, falling back to static loop for segment %d", idx)
                cmd_fallback = [
                    ffmpeg, "-y",
                    "-loop", "1",
                    "-i", str(png),
                    "-t", str(dur),
                    "-c:v", "libx264",
                    "-tune", "stillimage",
                    "-pix_fmt", "yuv420p",
                    "-r", "30",
                    str(seg)
                ]
                await asyncio.to_thread(subprocess.run, cmd_fallback, capture_output=True, check=True)

            segment_files.append(seg)

        # Concatenate 4 video segments and map continuous audio
        concat_cmd = [
            ffmpeg, "-y",
            "-i", str(segment_files[0]),
            "-i", str(segment_files[1]),
            "-i", str(segment_files[2]),
            "-i", str(segment_files[3]),
            "-i", str(final_audio),
            "-filter_complex", "[0:v][1:v][2:v][3:v]concat=n=4:v=1:a=0[outv]",
            "-map", "[outv]",
            "-map", "4:a",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(output_mp4)
        ]
        proc = await asyncio.to_thread(subprocess.run, concat_cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg multi-scene assembly failed: {proc.stderr}")
        log.info("Procedural multi-scene video assembled successfully (%s): %s", asset_used, output_mp4)

    finally:
        # Cleanup temporary files
        for p in scene_pngs:
            try:
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        for s in segment_files:
            try:
                if s.exists():
                    s.unlink()
            except Exception:
                pass

    caption = (
        f"🚨 {hook}\n\n"
        f"📌 {title}\n"
        f"الميزات الأساسية:\n" + "\n".join(f"▫️ {p}" for p in points) + "\n\n"
        f"🔗 {cta}\n\n"
        f"#ذكاء_اصطناعي #تداول #فوركس #fyp #trading #smc #shorts #reels #tiktok"
    )

    size_mb = output_mp4.stat().st_size / (1024 * 1024)

    return {
        "success": True,
        "video_path": str(output_mp4),
        "audio_path": str(final_audio),
        "duration_estimate": f"{total_dur:.1f}s",
        "file_size_mb": round(size_mb, 2),
        "caption": caption,
        "title": title,
        "hook": hook,
    }


async def autonomous_publish_short(
    topic: str = "",
    title: str = "",
    hook: str = "",
    script: str = "",
    points: list[str] | None = None,
    language: str = "en",
    privacy: str = "public",
    publish_to_tiktok: bool = True,
    publish_to_youtube: bool = True,
) -> dict[str, Any]:
    """Generates, subtitles, and publishes a multi-scene trading video to YouTube and TikTok end-to-end."""
    CURATED_TOPICS = [
        {
            "topic": "gold xauusd liquidity sweeps",
            "title": "Trading Gold Like Institutions",
            "hook": "Why does Gold respect Liquidity Pools?",
            "script": "Gold is the most algorithmic asset in financial markets. It seeks liquidity above equal highs and below equal lows before reversing with speed. Stop chasing breakouts; wait for the sweep. Subscribe to Core Trade AI.",
            "points": ["XAUUSD Liquidity", "Equal Highs & Lows", "Institutional Timing"],
        },
        {
            "topic": "bitcoin crypto order blocks",
            "title": "Institutional Order Blocks Revealed",
            "hook": "Where do hedge funds actually enter the market?",
            "script": "Hedge funds don't chase green candles. They accumulate massive positions inside hidden Order Blocks before the markup phase. Stop guessing reversals on retail indicators. Follow smart money volume. Subscribe to Core Trade AI.",
            "points": ["Institutional Footprint", "Order Block Zones", "High Probability Entries"],
        },
        {
            "topic": "forex eur fair value gaps",
            "title": "The Power of Fair Value Gaps",
            "hook": "Why does price always return to Fair Value Gaps?",
            "script": "When high-frequency algorithms inject sudden momentum, they create price imbalances known as Fair Value Gaps. Price returns like a magnet to rebalance liquidity. Learn to trade with institutional flow. Subscribe to Core Trade AI.",
            "points": ["Market Imbalances", "Algorithmic Magnets", "Precision Re-entries"],
        },
        {
            "topic": "nasdaq tech stop loss hunting",
            "title": "The 90% Stop Loss Trap",
            "hook": "Are market makers hunting your Stop Loss?",
            "script": "Your stop loss is an institutional target. Algorithms engineered by Wall Street trigger retail liquidations before expanding toward true targets. Trade alongside institutional volume, not against it. Subscribe to Core Trade AI.",
            "points": ["Liquidity Engineering", "Stop Hunt Mechanics", "Smart Money Footprint"],
        },
        {
            "topic": "ethereum defi liquidity sweeps",
            "title": "The Secret of Liquidity Sweeps",
            "hook": "Why do banks always hunt your Stop Loss?",
            "script": "Retail traders place stop losses at obvious levels. Institutional algorithms sweep those levels to fill massive orders. At Core Trade AI, we track the smart money footprint. Stop being the liquidity, become the hunter. Subscribe to Core Trade AI.",
            "points": ["Smart Money Concepts", "Liquidity Tracking", "Algorithmic Precision"],
        },
    ]

    t_lower = (topic or "").lower()
    matched = None
    if t_lower:
        for item in CURATED_TOPICS:
            if any(kw in t_lower for kw in item["topic"].split()):
                matched = item
                break

    if not matched:
        # Automatic rotation to ensure consecutive videos never use the same topic or asset
        last_topic_file = CACHE_DIR / "last_curated_topic.txt"
        last_t = ""
        if last_topic_file.exists():
            try:
                last_t = last_topic_file.read_text(encoding="utf-8").strip()
            except Exception:
                pass
        available_topics = [t for t in CURATED_TOPICS if t["topic"] != last_t]
        matched = random.choice(available_topics if available_topics else CURATED_TOPICS)
        try:
            last_topic_file.write_text(matched["topic"], encoding="utf-8")
        except Exception:
            pass

    final_title = title or matched["title"]
    final_hook = hook or matched["hook"]
    final_script = script or matched["script"]
    final_points = points or matched["points"]

    is_english = language == "en" or not bool(re.search(r"[\u0600-\u06FF]", final_script))
    voice_key = "en_male_tech" if is_english else "ar_male_egypt"
    badge = "🔥 Core Trade AI" if is_english else "🔥 حصرياً 2026"
    cta = "Subscribe to Core Trade AI!" if is_english else "الرابط بالبايو!"

    # 1. Assemble raw procedural multi-scene video (4 scene cuts + voiceover + Lo-Fi music)
    res_v = await assemble_short_video(
        title=final_title,
        hook=final_hook,
        points=final_points,
        script_narration=final_script,
        cta=cta,
        voice_key=voice_key,
        badge=badge,
        topic=matched["topic"] if not topic else topic,
    )
    v_path = Path(res_v["video_path"])

    # 2. Burn karaoke word-by-word subtitles
    from tools import video_autocaption, youtube_publisher, tiktok_publisher
    res_c = await video_autocaption.burn_karaoke_subtitles(v_path, language="en" if is_english else "ar")
    final_video = Path(res_c["video_path"])

    results: dict[str, Any] = {
        "success": True,
        "title": final_title,
        "hook": final_hook,
        "script": final_script,
        "video_path": str(final_video),
        "youtube": None,
        "tiktok": None,
    }

    # 3. Upload to YouTube Channel
    if publish_to_youtube:
        try:
            yt_res = await youtube_publisher.upload_video(
                video_path=final_video,
                title=f"{final_title} #Shorts",
                description=f"{final_hook}\n\n{final_script}\n\n#Shorts #Trading #SMC #Forex #CoreTradeAI #Crypto #Finance",
                privacy_status=privacy,
                is_short=True,
            )
            results["youtube"] = {
                "published": True,
                "url": yt_res.get("url"),
                "title": yt_res.get("title"),
            }
        except Exception as e:
            log.warning("YouTube publishing error: %s", e)
            results["youtube"] = {"published": False, "error": str(e)}

    # 4. Upload to TikTok
    if publish_to_tiktok and tiktok_publisher.is_authenticated():
        try:
            tiktok_caption = f"{final_hook} 🎯 {final_title} #trading #smc #forex #crypto #coretradeai #fyp #foryou"
            tt_res = await tiktok_publisher.upload_video(
                video_path=final_video,
                caption=tiktok_caption,
            )
            results["tiktok"] = {
                "published": True,
                "message": tt_res.get("message", "تم الرفع بنجاح على تيك توك!"),
            }
        except Exception as e:
            log.warning("TikTok publishing error: %s", e)
            results["tiktok"] = {"published": False, "error": str(e)}
    else:
        results["tiktok"] = {"published": False, "reason": "TikTok not authenticated or skipped"}

    results["youtube_url"] = (results.get("youtube") or {}).get("url") or "https://youtube.com/@CoreTradeAI"
    results["tiktok_status"] = (results.get("tiktok") or {}).get("message") or (results.get("tiktok") or {}).get("reason") or "جاهز للنشر"

    return results


async def video_creator_handler(args: dict) -> str:
    """Tool handler for AI Agent to build and render multi-scene viral videos."""
    title = args.get("title", "استراتيجية صيد السيولة")
    hook = args.get("hook", "لماذا تضرب البنوك وقف خسارتك دائماً؟")
    points = args.get("points", ["تتبع عقود المؤسسات", "فهم سحب السيولة", "عائد للمخاطرة 1 إلى 3"])
    if isinstance(points, str):
        points = [p.strip() for p in points.split(",") if p.strip()]

    script = args.get("script_narration")
    if not script:
        script = f"{hook}. {title}. أهم النقاط: " + ". ".join(points) + ". الرابط بانتظارك في البايو!"

    cta = args.get("cta", "الرابط مثبت بالبايو!")
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
            topic=args.get("topic", ""),
        )
        return (
            f"🎬 **تم إنشاء ورندرة الفيديو الاحترافي متعدد المشاهد بنجاح!**\n\n"
            f"📁 **مسار ملف الفيديو MP4:** `{res['video_path']}`\n"
            f"⏱️ **المدة الزمنية:** {res['duration_estimate']} | ⚖️ **الحجم:** {res['file_size_mb']} MB\n"
            f"✨ **المشاهد:** 4 مشاهد ديناميكية مقسمة ومدمجة بأعلى دقة 1080x1920 (Hook, Trap, Solution, Outro)\n\n"
            f"📝 **الكابشن والهاشتاجات المقترحة:**\n"
            f"```text\n{res['caption']}\n```"
        )
    except Exception as e:
        log.exception("Video creator handler failed")
        return f"❌ فشل إنشاء الفيديو: {e}"


async def publish_trading_short_handler(args: dict) -> str:
    """Agent tool handler for end-to-end multi-scene creation and dual YouTube + TikTok publishing."""
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
        yt_info = res.get("youtube") or {}
        tt_info = res.get("tiktok") or {}

        yt_msg = f"🔗 **يوتيوب شورتس:** {yt_info.get('url', 'فشل أو غير مفعل')}" if yt_info.get("published") else f"⚠️ يوتيوب: {yt_info.get('error', 'غير منشور')}"
        tt_msg = f"📱 **تيك توك:** {tt_info.get('message', 'تم النشر')}" if tt_info.get("published") else f"ℹ️ تيك توك: {tt_info.get('reason') or tt_info.get('error', 'غير منشور')}"

        return (
            f"🎉 **تم إنتاج ونشر الفيديو متعدد المشاهد بنجاح على المنصات!**\n\n"
            f"🎬 **العنوان:** {res['title']}\n"
            f"{yt_msg}\n"
            f"{tt_msg}\n"
            f"📁 **مسار الفيديو المولد:** `{res['video_path']}`\n\n"
            f"⚡ **مواصفات الإنتاج:**\n"
            f"• 4 مشاهد جرافيكية منفصلة مع شارتات TradingView مختلفة في نفس الفيديو.\n"
            f"• تعليق صوتي عصبي عالي الجودة وموسيقى تقنية Lo-Fi خافتة.\n"
            f"• ترجمة كاريوكي متحركة ومضاءة كلمة بكلمة بالنيون.\n"
            f"• نشر تلقائي مزدوج على يوتيوب شورتس وتيك توك."
        )
    except Exception as e:
        log.exception("Publish trading short tool failed")
        return f"❌ فشل إنشاء ونشر الشورتس: {e}"


TOOLS = [
    {
        "name": "create_viral_short_video",
        "description": (
            "توليد ورندرة فيديو قصير عمودي (9:16 Shorts/Reels/TikTok) احترافي متعدد المشاهد (4 مشاهد ديناميكية مختلفة: الخطاف، الفخ، الحل، الخاتمة)، "
            "مع تعليق صوتي عصبي، وتنوع في الشارتات والألوان، وموسيقى لو فاي، وكابشن مخصص."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "عنوان الفيديو الأساسي أو اسم الأداة/الاستراتيجية"},
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
                "badge": {"type": "string", "description": "شارة العرض أعلى الفيديو"},
            },
            "required": ["title", "hook", "script_narration"],
        },
        "handler": video_creator_handler,
    },
    {
        "name": "create_and_publish_trading_short",
        "description": (
            "ينشئ وينشر فيديو شورتس/تيك توك احترافي متكامل تلقائياً ومباشرة على يوتيوب وتيك توك: "
            "4 مشاهد منفصلة من الشارتات المؤسسية + صوت عصبي + موسيقى Lo-Fi + كابشن كاريوكي نيون كلمة بكلمة + رفع مزدوج تلقائي."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "موضوع الفيديو (مثال: 'Liquidity Sweeps', 'Order Blocks', 'Stop Loss Hunting', 'Fair Value Gaps', 'Gold Trading')"},
                "title": {"type": "string", "description": "عنوان مخصص اختياري"},
                "hook": {"type": "string", "description": "خطاف مخصص اختياري"},
                "script": {"type": "string", "description": "اسكريبت مخصص اختياري"},
                "language": {"type": "string", "enum": ["en", "ar"], "description": "اللغة (en أو ar)"},
            },
        },
        "handler": publish_trading_short_handler,
    },
]

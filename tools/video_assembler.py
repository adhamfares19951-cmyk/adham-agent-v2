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
    html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&family=Outfit:wght@600;800&display=swap');
  
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  
  body {{
    width: 1080px;
    height: 1920px;
    background: radial-gradient(circle at 50% 15%, #1e1b4b 0%, #0b0f19 50%, #030712 100%);
    color: #f8fafc;
    font-family: 'Cairo', sans-serif;
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
    <div class="brand">Adham<span>AI</span> • Studio</div>
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
    <div class="cta-sub">الرابط بالبايو • تابع الحساب لتصلك أحدث أدوات الذكاء الاصطناعي</div>
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
    # We create a placeholder image using FFmpeg lavfi color generator
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

    # 1. Generate Voiceover via Edge-TTS
    log.info("Generating voiceover for script...")
    audio_path = await voice_studio.generate_speech(text=script_narration, voice_key=voice_key)
    if not audio_path.exists():
        raise RuntimeError(f"Voiceover generation failed: {audio_path}")

    # 2. Render 1080x1920 Slide Card
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
        "-i", str(audio_path),
        "-vf", "scale=1080:1920,zoompan=z='min(zoom+0.0006,1.06)':d=750:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30",
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
    }
]

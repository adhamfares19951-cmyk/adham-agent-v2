"""Motion Video Studio Bridge for adham-agent.
Integrates the Remotion 60FPS motion graphics engine (motion-video-studio)
into adham-agent tools and Telegram commands.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import Any

log = logging.getLogger("motion_studio")

BASE_DIR = Path(__file__).resolve().parent.parent
STUDIO_DIR = BASE_DIR.parent / "motion-video-studio"
STUDIO_SCRIPT = STUDIO_DIR / "studio.py"
PORTABLE_PY = BASE_DIR / "python_runtime" / "python.exe"


async def generate_motion_masterclass(
    topic: str = "Ø§Ø³ØªØ±Ø§ØªÙŠØ¬ÙŠØ© ØµÙŠØ¯ Ø§Ù„Ø³ÙŠÙˆÙ„Ø© ÙˆØ§Ù„Ø£ÙˆØ±Ø¯Ø± Ø¨Ù„ÙˆÙƒ Ù„Ù„Ø°Ù‡Ø¨",
    ratio: str = "16:9",
    voice: str = "ar_male",
) -> dict[str, Any]:
    """Runs the motion-video-studio Remotion pipeline and returns the output video path."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--topic", topic,
        "--ratio", ratio,
        "--voice", voice,
    ]

    log.info("Launching Motion Video Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Motion Video Studio failed: %s", err_msg)
        raise RuntimeError(f"ÙØ´Ù„ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„Ù…ÙˆØ´Ù† Ø¬Ø±Ø§ÙÙŠÙƒ: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    pattern = "masterclass_*.mp4" if ratio == "16:9" else "masterclass_*_9x16.mp4"
    matching = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        # Fallback to any recent mp4
        matching = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("Ù„Ù… ÙŠØªÙ… Ø§Ù„Ø¹Ø«ÙˆØ± Ø¹Ù„Ù‰ Ù…Ù„Ù Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ø§Ù„Ù†Ø§ØªØ¬ ÙÙŠ Ù…Ø¬Ù„Ø¯ out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "topic": topic,
        "ratio": ratio,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
        "message": f"ØªÙ… Ø¥Ù†ØªØ§Ø¬ Ù…Ø§Ø³ØªØ±ÙƒÙ„Ø§Ø³ Ø§Ù„Ù…ÙˆØ´Ù† Ø¬Ø±Ø§ÙÙŠÙƒ Ø¨Ù†Ø¬Ø§Ø­! Ø§Ù„Ù…Ù„Ù: {output_video.name}"
    }


async def generate_talking_fruit_short(
    topic: str = "Ù…Ø³ØªØ± Ø¨Ø±ØªÙ‚Ø§Ù„ ÙÙŠ Ø®Ø·Ø±",
    character: str = "orange",
    voice: str = "ar_fruit_funny",
) -> dict[str, Any]:
    """Runs the talking fruit/character short production pipeline."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--mode", "fruit",
        "--character", character,
        "--topic", topic,
        "--voice", voice,
    ]

    log.info("Launching Talking Fruit Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Talking Fruit Studio failed: %s", err_msg)
        raise RuntimeError(f"ÙØ´Ù„ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„ÙÙˆØ§ÙƒÙ‡ Ø§Ù„Ù…ØªÙƒÙ„Ù…Ø©: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    matching = sorted(out_dir.glob(f"talking_{character}_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        matching = sorted(out_dir.glob("talking_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("Ù„Ù… ÙŠØªÙ… Ø§Ù„Ø¹Ø«ÙˆØ± Ø¹Ù„Ù‰ Ù…Ù„Ù ÙÙŠØ¯ÙŠÙˆ Ø§Ù„ÙØ§ÙƒÙ‡Ø© ÙÙŠ Ù…Ø¬Ù„Ø¯ out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "character": character,
        "topic": topic,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
    }


async def _handle_motion_masterclass(args: dict[str, Any]) -> str:
    """Agent tool handler for generating 60FPS motion graphics videos."""
    topic = args.get("topic", "Ø£Ø³Ø±Ø§Ø± Ø§Ù„Ø³ÙŠÙˆÙ„Ø© Ø§Ù„Ù…Ø¤Ø³Ø³Ø§ØªÙŠØ© ÙˆØªØ¯Ø§ÙˆÙ„ Ø§Ù„Ø°Ù‡Ø¨")
    ratio = args.get("ratio", "16:9")
    voice = args.get("voice", "ar_male")

    try:
        res = await generate_motion_masterclass(topic=topic, ratio=ratio, voice=voice)
        return (
            f"ðŸ† **ØªÙ… Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„Ù…ÙˆØ´Ù† Ø¬Ø±Ø§ÙÙŠÙƒ Ø§Ù„Ø§Ø­ØªØ±Ø§ÙÙŠ Ø¨Ù†Ø¬Ø§Ø­!**\n\n"
            f"ðŸ“Œ **Ø§Ù„Ù…ÙˆØ¶ÙˆØ¹:** {res['topic']}\n"
            f"ðŸ“ **Ø§Ù„Ø£Ø¨Ø¹Ø§Ø¯:** {res['ratio']}\n"
            f"âš¡ **Ø§Ù„ØªÙ‚Ù†ÙŠØ©:** Remotion 60FPS + Ø´Ù…ÙˆØ¹ Ø­Ø±ÙƒÙŠØ© + ÙƒØ±ÙˆØª Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒÙŠØ© ØªÙ†Ø¨Ø«Ù‚ ÙˆØªØªØ­Ø±Ùƒ\n"
            f"ðŸ“ **Ù…Ø³Ø§Ø± Ø§Ù„Ù…Ù„Ù:** `{res['video_path']}`\n"
            f"ðŸ’¾ **Ø§Ù„Ø­Ø¬Ù…:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Motion masterclass error")
        return f"âŒ Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„Ù…ÙˆØ´Ù† Ø¬Ø±Ø§ÙÙŠÙƒ: {e}"


async def generate_fruit_drama_short(
    topic: str = "الموزة خانت الفراولة بطريقة صادمة 💔",
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Runs the multi-character Pixar Fruit Drama short production pipeline."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--mode", "drama",
        "--topic", topic,
    ]
    if output_filename:
        cmd.extend(["--out", output_filename])

    log.info("Launching Pixar Fruit Drama Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Fruit Drama Studio failed: %s", err_msg)
        raise RuntimeError(f"فشل إنتاج دراما الفواكه بيكسار: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    pattern = "fruit_drama_*.mp4"
    matching = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        raise FileNotFoundError("لم يتم العثور على ملف فيديو الدراما الناتج في مجلد out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "topic": topic,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
    }


async def _handle_fruit_drama_short(args: dict[str, Any]) -> str:
    """Agent tool handler for generating viral Pixar fruit drama storytelling shorts."""
    topic = args.get("topic", "الموزة خانت الفراولة بطريقة صادمة 💔")
    try:
        res = await generate_fruit_drama_short(topic=topic)
        return (
            f"🎬 **تم إنتاج حلقة دراما الفواكه بيكسار 3D بنجاح!**\n\n"
            f"📖 **القصة والموضوع:** {res['topic']}\n"
            f"🍓 **أبطال العمل:** الفراولة الحزينة + الموزة الخائنة + التفاحة المتواطئة + الراوي العميق\n"
            f"📐 **الأبعاد:** 1080x1920 (9:16 Shorts / Reels / TikTok)\n"
            f"✨ **المؤثرات:** محاكاة بيكسار 3D كاملة + اهتزاز كاميرا صدمة + تكبير سينمائي + ترجمة عربية بخط Cairo-Bold + 4 أصوات ذكاء اصطناعي مختلفة\n"
            f"📁 **مسار الملف:** `{res['video_path']}`\n"
            f"💾 **الحجم:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Fruit drama short error")
        return f"❌ خطأ أثناء إنتاج دراما الفواكه: {e}"


async def generate_fruit_fight_match(
    output_filename: str | None = None,
) -> dict[str, Any]:
    """Runs the 3-round fruit wrestling match production pipeline."""
    if not STUDIO_SCRIPT.exists():
        raise FileNotFoundError(f"Motion Video Studio not found at: {STUDIO_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    cmd = [
        python_bin,
        str(STUDIO_SCRIPT),
        "--mode", "fight",
    ]

    log.info("Launching Fruit Wrestling Match: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(STUDIO_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("Fruit Wrestling Match failed: %s", err_msg)
        raise RuntimeError(f"ÙØ´Ù„ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ù…ØµØ§Ø±Ø¹Ø© Ø§Ù„ÙÙˆØ§ÙƒÙ‡: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    matching = sorted(out_dir.glob("fruit_fight_*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        matching = sorted(out_dir.glob("fruit_wrestling_match.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("Ù„Ù… ÙŠØªÙ… Ø§Ù„Ø¹Ø«ÙˆØ± Ø¹Ù„Ù‰ Ù…Ù„Ù ÙÙŠØ¯ÙŠÙˆ Ù†Ø²Ø§Ù„ Ø§Ù„ÙÙˆØ§ÙƒÙ‡ ÙÙŠ Ù…Ø¬Ù„Ø¯ out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "title": "Ø§Ù„Ù…Ø¹Ø±ÙƒØ© Ø§Ù„ÙƒØ¨Ø±Ù‰: Ø£ÙÙˆÙƒØ§Ø¯Ùˆ Ø¶Ø¯ ØªÙØ§Ø­Ø© (3 Ø¬ÙˆÙ„Ø§Øª)",
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
    }


async def _handle_talking_fruit_short(args: dict[str, Any]) -> str:
    """Agent tool handler for generating talking fruit / object comedy shorts."""
    topic = args.get("topic", "Ù…Ø³ØªØ± Ø¨Ø±ØªÙ‚Ø§Ù„ ÙÙŠ Ø®Ø·Ø±")
    character = args.get("character", "orange")
    voice = args.get("voice", "ar_fruit_funny")

    try:
        res = await generate_talking_fruit_short(topic=topic, character=character, voice=voice)
        return (
            f"ðŸŠ **ØªÙ… Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„ÙØ§ÙƒÙ‡Ø© Ø§Ù„Ù…ØªÙƒÙ„Ù…Ø© (Talking Character) Ø¨Ù†Ø¬Ø§Ø­!**\n\n"
            f"ðŸŽ­ **Ø§Ù„Ø´Ø®ØµÙŠØ©:** {res['character']}\n"
            f"ðŸ“Œ **Ø§Ù„Ù…ÙˆØ¶ÙˆØ¹:** {res['topic']}\n"
            f"âœ¨ **Ø§Ù„Ù…ÙŠØ²Ø§Øª:** Ø¹ÙŠÙˆÙ† ÙˆØ§Ù‚Ø¹ÙŠØ© ØªØ±Ù…Ø´ ÙˆØªØªØ­Ø±Ùƒ + ÙÙ… ÙŠØªØ²Ø§Ù…Ù† Ù…Ø¹ Ù…Ø®Ø§Ø±Ø¬ Ø§Ù„Ø­Ø±ÙˆÙ + ØµÙˆØª ÙƒØ±ØªÙˆÙ†ÙŠ Ù…Ø±Ø­ + ÙƒØ±ÙˆØª ØªÙŠÙƒ ØªÙˆÙƒ Ù‚Ø§ÙØ²Ø©\n"
            f"ðŸ“ **Ù…Ø³Ø§Ø± Ø§Ù„Ù…Ù„Ù:** `{res['video_path']}`\n"
            f"ðŸ’¾ **Ø§Ù„Ø­Ø¬Ù…:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Talking fruit short error")
        return f"âŒ Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ø§Ù„ÙØ§ÙƒÙ‡Ø© Ø§Ù„Ù…ØªÙƒÙ„Ù…Ø©: {e}"


async def _handle_fruit_fight_match(args: dict[str, Any]) -> str:
    """Agent tool handler for generating the 3-round fruit wrestling brawl."""
    try:
        res = await generate_fruit_fight_match()
        return (
            f"ðŸ¥Š **ØªÙ… Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ù†Ø²Ø§Ù„ Ø§Ù„Ù…ØµØ§Ø±Ø¹Ø© Ø¨ÙŠÙ† Ø§Ù„Ø£ÙÙˆÙƒØ§Ø¯Ùˆ ÙˆØ§Ù„ØªÙØ§Ø­Ø© Ø¨Ù†Ø¬Ø§Ø­!**\n\n"
            f"ðŸŸï¸ **Ø§Ù„Ø­Ù„Ø¨Ø©:** Ø­Ù„Ø¨Ø© Ù…ØµØ§Ø±Ø¹Ø© ÙƒØ§Ù…Ù„Ø© + Ø­Ø¨Ø§Ù„ Ø¯ÙŠÙ†Ø§Ù…ÙŠÙƒÙŠØ© + ÙƒØ´Ø§ÙØ§Øª Ø³ØªØ§Ø¯ÙŠÙˆÙ… + Ø¬Ù…Ù‡ÙˆØ± ÙŠÙ‡ØªÙ ÙˆÙŠØ±ÙØ¹ Ù„Ø§ÙØªØ§Øª\n"
            f"âš¡ **Ø§Ù„Ù†Ø²Ø§Ù„:** 3 Ø¬ÙˆÙ„Ø§Øª ÙƒØ§Ù…Ù„Ø© (Round 1 + Round 2 + Final K.O.)\n"
            f"ðŸ¥‘ **Ø§Ù„Ù…Ù‚Ø§ØªÙ„ 1:** Ø§Ù„Ø£ÙÙˆÙƒØ§Ø¯Ùˆ Ø¨Ù‚ÙØ§Ø²Ø§Øª Ù…Ù„Ø§ÙƒÙ…Ø© Ø­Ù…Ø±Ø§Ø¡\n"
            f"ðŸŽ **Ø§Ù„Ù…Ù‚Ø§ØªÙ„ 2:** Ø§Ù„ØªÙØ§Ø­Ø© Ø¨Ù‚ÙØ§Ø²Ø§Øª Ù…Ù„Ø§ÙƒÙ…Ø© Ø²Ø±Ù‚Ø§Ø¡ ÙˆØ¹ØµØ§Ø¨Ø© Ø±Ø£Ø³ Ù…Ù‚Ø§ØªÙ„\n"
            f"ðŸ‹ **Ø§Ù„Ø­ÙƒÙ…:** Ù„ÙŠÙ…ÙˆÙ†Ø© Ø¨Ù‚Ù…ÙŠØµ Ø§Ù„Ø­ÙƒØ§Ù… Ø§Ù„Ù…Ù‚Ù„Ù… ÙˆØµÙØ§Ø±Ø© ÙŠÙ‚Ù Ø¨ÙŠÙ†Ù‡Ù…Ø§ ÙˆÙŠØ­Ø³Ù… Ø§Ù„Ù†ØªÙŠØ¬Ø©\n"
            f"ðŸ“Š **Ø§Ù„Ù€ HUD:** Ø£Ø´Ø±Ø·Ø© ØµØ­Ø© (Health Bars) ØªÙ†Ù‚Øµ Ù…Ø¹ ÙƒÙ„ Ø¶Ø±Ø¨Ø© + Ù…Ø¤Ø«Ø±Ø§Øª POW! Ùˆ BAM! Ùˆ K.O.!\n"
            f"ðŸŽ™ï¸ **Ø§Ù„ØªØ¹Ù„ÙŠÙ‚:** ØªØ¹Ù„ÙŠÙ‚ Ø­Ù…Ø§Ø³ÙŠ Ø§Ø­ØªØ±Ø§ÙÙŠ Ø¨Ù†Ø¨Ø±Ø© Ù…Ø¹Ù„Ù‚ÙŠ Ø§Ù„Ù…ØµØ§Ø±Ø¹Ø© Ø§Ù„Ø¹Ø§Ù„Ù…ÙŠØ©\n"
            f"ðŸ“ **Ù…Ø³Ø§Ø± Ø§Ù„Ù…Ù„Ù:** `{res['video_path']}`\n"
            f"ðŸ’¾ **Ø§Ù„Ø­Ø¬Ù…:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Fruit fight match error")
        return f"âŒ Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ Ø¥Ù†ØªØ§Ø¬ ÙÙŠØ¯ÙŠÙˆ Ù†Ø²Ø§Ù„ Ø§Ù„ÙÙˆØ§ÙƒÙ‡: {e}"


CINEMA_DIR = BASE_DIR.parent / "ai-cinematic-studio"
CINEMA_SCRIPT = CINEMA_DIR / "studio.py"


async def generate_cinematic_storyboard(template: str = "drama", output_prefix: str = "") -> dict[str, Any]:
    """Runs the AI Cinematic Studio storyboard director."""
    if not CINEMA_SCRIPT.exists():
        raise FileNotFoundError(f"AI Cinematic Studio script not found at: {CINEMA_SCRIPT}")

    python_bin = str(PORTABLE_PY) if PORTABLE_PY.exists() else sys.executable
    prefix = output_prefix or f"telegram_{template}_{int(time.time())}"
    cmd = [
        python_bin,
        str(CINEMA_SCRIPT),
        "--template", template,
        "--output", prefix,
    ]

    log.info("Launching AI Cinematic Studio: %s", " ".join(cmd))
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(CINEMA_DIR),
    )

    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err_msg = stderr.decode("utf-8", errors="replace")
        log.error("AI Cinematic Studio failed: %s", err_msg)
        raise RuntimeError(f"ÙØ´Ù„ Ø¥Ù†ØªØ§Ø¬ Ø§Ù„Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯ Ø§Ù„Ø³ÙŠÙ†Ù…Ø§Ø¦ÙŠ: {err_msg[:400]}")

    out_dir = CINEMA_DIR / "out"
    json_file = out_dir / f"{prefix}_storyboard.json"
    md_file = out_dir / f"{prefix}_treatment.md"

    md_content = md_file.read_text(encoding="utf-8") if md_file.exists() else ""

    return {
        "success": True,
        "template": template,
        "json_path": str(json_file),
        "md_path": str(md_file),
        "treatment_preview": md_content[:2500] if md_content else "",
        "message": f"ØªÙ… Ø¥Ù†ØªØ§Ø¬ Ø§Ù„Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯ Ø§Ù„Ø³ÙŠÙ†Ù…Ø§Ø¦ÙŠ ÙˆØ§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø¥Ø®Ø±Ø§Ø¬ÙŠØ© Ù„Ù‚Ø§Ù„Ø¨ [{template}] Ø¨Ù†Ø¬Ø§Ø­!"
    }


async def _handle_cinematic_storyboard(args: dict[str, Any]) -> str:
    """Agent tool handler for creating cinematic storyboards and prompts."""
    try:
        template = args.get("template", "drama")
        res = await generate_cinematic_storyboard(template=template)
        return (
            f"ðŸŽ¬ **ØªÙ… Ø¥Ù†ØªØ§Ø¬ Ø§Ù„Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯ Ø§Ù„Ø³ÙŠÙ†Ù…Ø§Ø¦ÙŠ Ø¨Ù†Ø¬Ø§Ø­!**\n\n"
            f"ðŸŽ­ **Ø§Ù„Ù‚Ø§Ù„Ø¨:** `{template}`\n"
            f"ðŸ“ **Ù…Ù„Ù Ø§Ù„Ù€ JSON Ø§Ù„Ø¨Ø±Ù…Ø¬ÙŠ:** `{res['json_path']}`\n"
            f"ðŸ“„ **Ù…Ù„Ù Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© (Markdown):** `{res['md_path']}`\n\n"
            f"**Ù…Ø¹Ø§ÙŠÙ†Ø© Ø§Ù„Ù…Ø¹Ø§Ù„Ø¬Ø© Ø§Ù„Ø¥Ø®Ø±Ø§Ø¬ÙŠØ© ÙˆØ§Ù„Ø¨Ø±ÙˆÙ…Ø¨ØªØ§Øª:**\n"
            f"{res['treatment_preview'][:1500]}"
        )
    except Exception as e:
        log.exception("Cinematic storyboard error")
        return f"âŒ Ø®Ø·Ø£ Ø£Ø«Ù†Ø§Ø¡ ØªÙˆÙ„ÙŠØ¯ Ø§Ù„Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯ Ø§Ù„Ø³ÙŠÙ†Ù…Ø§Ø¦ÙŠ: {e}"


TOOLS = [
    {
        "name": "create_motion_masterclass",
        "description": "ÙŠÙ†ØªØ¬ ÙÙŠØ¯ÙŠÙˆÙ‡Ø§Øª Ø·ÙˆÙŠÙ„Ø© (Masterclass / ÙˆØ«Ø§Ø¦Ù‚ÙŠØ©) Ø£Ùˆ Ø´ÙˆØ±ØªØ³ Ø¨ØªÙ‚Ù†ÙŠØ© Ø§Ù„Ù…ÙˆØ´Ù† Ø¬Ø±Ø§ÙÙŠÙƒ 60FPS Ø¹Ø¨Ø± Remotion Ù…Ø¹ Ø´Ù…ÙˆØ¹ ØªØ¯Ø§ÙˆÙ„ Ù…Ø±Ø³ÙˆÙ…Ø© Ù„Ø§ÙŠÙØŒ ÙƒØ±ÙˆØª ØªØ·ÙÙˆ ÙˆØªÙ†Ø²Ù„Ù‚ØŒ ØªÙ‚Ø³ÙŠÙ… ÙØµÙˆÙ„ØŒ ÙˆØµÙˆØª Ø¹ØµØ¨ÙŠ Ø§Ø­ØªØ±Ø§ÙÙŠ.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Ù…ÙˆØ¶ÙˆØ¹ Ø§Ù„Ù…Ø§Ø³ØªØ±ÙƒÙ„Ø§Ø³ Ø£Ùˆ Ø§Ù„ÙÙŠØ¯ÙŠÙˆ"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16"], "description": "Ø£Ø¨Ø¹Ø§Ø¯ Ø§Ù„ÙÙŠØ¯ÙŠÙˆ: 16:9 Ù„Ù„ÙŠÙˆØªÙŠÙˆØ¨ Ø£Ùˆ 9:16 Ù„Ù„Ø´ÙˆØ±ØªØ³ ÙˆØªÙŠÙƒ ØªÙˆÙƒ"},
                "voice": {"type": "string", "description": "Ø§Ù„ØµÙˆØª Ø§Ù„Ø¹ØµØ¨ÙŠ (ar_male, ar_egypt, en_male)"}
            },
            "required": ["topic"]
        },
        "handler": _handle_motion_masterclass
    },
    {
        "name": "create_talking_fruit_short",
        "description": "ÙŠÙ†ØªØ¬ ÙÙŠØ¯ÙŠÙˆÙ‡Ø§Øª ÙƒÙˆÙ…ÙŠØ¯ÙŠØ© Ø´ÙˆØ±ØªØ³ ÙˆØªÙŠÙƒ ØªÙˆÙƒ Ù„Ù„ÙÙˆØ§ÙƒÙ‡ ÙˆØ§Ù„Ø£Ø´ÙŠØ§Ø¡ Ø§Ù„Ù…ØªÙƒÙ„Ù…Ø© (Talking Fruits / Talking Objects) Ù…Ø«Ù„ Ø§Ù„Ø¨Ø±ØªÙ‚Ø§Ù„ØŒ Ø§Ù„Ø£ÙÙˆÙƒØ§Ø¯ÙˆØŒ Ø§Ù„ØªÙØ§Ø­ØŒ Ø§Ù„Ù…ÙˆØ²ØŒ Ø§Ù„Ù„ÙŠÙ…ÙˆÙ†ØŒ ÙˆØ§Ù„Ø¨ÙŠØªÙƒÙˆÙŠÙ† Ø§Ù„Ù…ØªÙƒÙ„Ù… Ù…Ø¹ Ø¹ÙŠÙˆÙ† ØªØ±Ù…Ø´ ÙˆØªØªØ­Ø±Ùƒ ÙˆÙÙ… ÙŠØªÙƒÙ„Ù… Ø¨Ø­Ø±ÙƒØ§Øª Ø´ÙØ§Ù‡ ÙˆØ§Ù‚Ø¹ÙŠØ© ÙˆØµÙˆØª ÙƒØ±ØªÙˆÙ†ÙŠ Ù…Ø¶Ø­Ùƒ.",
        "parameters": {
            "type": "object",
            "properties": {
                "character": {
                    "type": "string",
                    "enum": ["orange", "apple", "avocado", "banana", "lemon", "bitcoin", "coffee"],
                    "description": "Ù†ÙˆØ¹ Ø§Ù„Ø´Ø®ØµÙŠØ© Ø£Ùˆ Ø§Ù„ÙØ§ÙƒÙ‡Ø© Ø§Ù„Ù…ØªÙƒÙ„Ù…Ø©"
                },
                "topic": {"type": "string", "description": "Ù…ÙˆØ¶ÙˆØ¹ Ø£Ùˆ Ù‚ØµØ© Ø§Ù„ÙÙŠØ¯ÙŠÙˆ Ø§Ù„ÙƒÙˆÙ…ÙŠØ¯ÙŠ"},
                "voice": {"type": "string", "description": "Ù†Ù…Ø· Ø§Ù„ØµÙˆØª (ar_fruit_funny, ar_fruit_cute, ar_fruit_deep, ar_fruit_panicked, en_cartoon)"}
            },
            "required": ["character"]
        },
        "handler": _handle_talking_fruit_short
    },
    {
        "name": "create_fruit_drama_short",
        "description": "ينتج فيديوهات دراما الفواكه بيكسار 3D كاملة (مثل خيانة الموزة للفراولة) بأبعاد تيك توك وشورتس 9:16 مع حوارات متعددة، كاميرا درامية، أصوات إيموشن لكل فاكهة، وترجمة عربية متحركة.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "قصة الدراما أو عنوان الحلقة الفيروسي"}
            },
            "required": []
        },
        "handler": _handle_fruit_drama_short
    },
    {
        "name": "create_fruit_fight_match",
        "description": "ÙŠÙ†ØªØ¬ ÙÙŠØ¯ÙŠÙˆ Ù…Ù„Ø­Ù…ÙŠ Ù„Ù†Ø²Ø§Ù„ Ù…ØµØ§Ø±Ø¹Ø© ÙˆÙ…Ù„Ø§ÙƒÙ…Ø© Ù…ØªÙƒØ§Ù…Ù„ Ø¨ÙŠÙ† Ø§Ù„ÙÙˆØ§ÙƒÙ‡ (Ø£ÙÙˆÙƒØ§Ø¯Ùˆ Ø¶Ø¯ ØªÙØ§Ø­Ø©) ÙÙŠ Ø­Ù„Ø¨Ø© Ù…ØµØ§Ø±Ø¹Ø© Ù…Ø¹ Ø­Ø¨Ø§Ù„ ÙˆØ£Ø¶ÙˆØ§Ø¡ ÙˆØ¬Ù…Ù‡ÙˆØ± ÙŠÙ‡ØªÙØŒ ÙˆØ­ÙƒÙ… Ø±Ø³Ù…ÙŠØŒ ÙˆØ£Ø´Ø±Ø·Ø© ØµØ­Ø© Health BarsØŒ ÙˆÙ‚ØªØ§Ù„ Ø¹Ù„Ù‰ 3 Ø¬ÙˆÙ„Ø§Øª ÙŠÙ†ØªÙ‡ÙŠ Ø¨Ø§Ù„Ø¶Ø±Ø¨Ø© Ø§Ù„Ù‚Ø§Ø¶ÙŠØ© K.O. ÙˆØªØ¹Ù„ÙŠÙ‚ Ø­Ù…Ø§Ø³ÙŠ.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "handler": _handle_fruit_fight_match
    },
    {
        "name": "create_cinematic_storyboard",
        "description": "ÙŠÙ†ØªØ¬ Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯ Ø³ÙŠÙ†Ù…Ø§Ø¦ÙŠ ÙˆÙ…Ø¹Ø§Ù„Ø¬Ø© Ø¥Ø®Ø±Ø§Ø¬ÙŠØ© ÙØ§Ø¦Ù‚Ø© Ø§Ù„ÙˆØ§Ù‚Ø¹ÙŠØ© 8K (ARRI Alexa, Unreal Engine 5.4, Micro-droplets, Sub-surface scattering) Ù„Ø£ÙÙ„Ø§Ù… Ø§Ù„ÙÙˆØ§ÙƒÙ‡ Ø§Ù„ÙÙŠØ±ÙˆØ³ÙŠØ© Ù…Ø«Ù„ Ø¯Ø±Ø§Ù…Ø§ Ø§Ù„ØªÙØ§Ø­Ø© Ø§Ù„Ø­Ø²ÙŠÙ†Ø© Ø£Ùˆ Ù‚ØªØ§Ù„ Ù…ÙˆØ±ØªØ§Ù„ ÙƒÙˆÙ…Ø¨Ø§Øª Ù…Ø¹ Ø£ÙˆØ§Ù…Ø± ÙÙŠØ²ÙŠØ§Ø¡ Ø§Ù„ÙƒØ§Ù…ÙŠØ±Ø§ ÙˆØ§Ù„ØªØ¹Ù„ÙŠÙ‚ Ø§Ù„ØµÙˆØªÙŠ.",
        "parameters": {
            "type": "object",
            "properties": {
                "template": {
                    "type": "string",
                    "enum": ["drama", "fight"],
                    "description": "Ù‚Ø§Ù„Ø¨ Ø§Ù„Ø³ØªÙˆØ±ÙŠØ¨ÙˆØ±Ø¯: drama (Ø¯Ø±Ø§Ù…Ø§ Ø§Ù„ØªÙØ§Ø­Ø© Ø§Ù„Ø­Ø²ÙŠÙ†Ø© ÙˆØ§Ù„Ø£Ù…ÙˆÙ…Ø©) Ø£Ùˆ fight (Ù…ÙˆØ±ØªØ§Ù„ ÙƒÙˆÙ…Ø¨Ø§Øª Ø§Ù„ÙÙˆØ§ÙƒÙ‡)"
                }
            },
            "required": ["template"]
        },
        "handler": _handle_cinematic_storyboard
    }
]

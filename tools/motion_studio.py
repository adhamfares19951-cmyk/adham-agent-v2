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
    topic: str = "استراتيجية صيد السيولة والأوردر بلوك للذهب",
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
        raise RuntimeError(f"فشل إنتاج فيديو الموشن جرافيك: {err_msg[:400]}")

    out_dir = STUDIO_DIR / "out"
    pattern = "masterclass_*.mp4" if ratio == "16:9" else "masterclass_*_9x16.mp4"
    matching = sorted(out_dir.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matching:
        # Fallback to any recent mp4
        matching = sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not matching:
        raise FileNotFoundError("لم يتم العثور على ملف الفيديو الناتج في مجلد out.")

    output_video = matching[0]
    return {
        "success": True,
        "video_path": str(output_video),
        "topic": topic,
        "ratio": ratio,
        "size_mb": round(output_video.stat().st_size / (1024 * 1024), 2),
        "message": f"تم إنتاج ماستركلاس الموشن جرافيك بنجاح! الملف: {output_video.name}"
    }


async def _handle_motion_masterclass(args: dict[str, Any]) -> str:
    """Agent tool handler for generating 60FPS motion graphics videos."""
    topic = args.get("topic", "أسرار السيولة المؤسساتية وتداول الذهب")
    ratio = args.get("ratio", "16:9")
    voice = args.get("voice", "ar_male")

    try:
        res = await generate_motion_masterclass(topic=topic, ratio=ratio, voice=voice)
        return (
            f"🏆 **تم إنتاج فيديو الموشن جرافيك الاحترافي بنجاح!**\n\n"
            f"📌 **الموضوع:** {res['topic']}\n"
            f"📐 **الأبعاد:** {res['ratio']}\n"
            f"⚡ **التقنية:** Remotion 60FPS + شموع حركية + كروت ديناميكية تنبثق وتتحرك\n"
            f"📁 **مسار الملف:** `{res['video_path']}`\n"
            f"💾 **الحجم:** {res['size_mb']} MB"
        )
    except Exception as e:
        log.exception("Motion masterclass error")
        return f"❌ خطأ أثناء إنتاج فيديو الموشن جرافيك: {e}"


TOOLS = [
    {
        "name": "create_motion_masterclass",
        "description": "ينتج فيديوهات طويلة (Masterclass / وثائقية) أو شورتس بتقنية الموشن جرافيك 60FPS عبر Remotion مع شموع تداول مرسومة لايف، كروت تطفو وتنزلق، تقسيم فصول، وصوت عصبي احترافي.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "موضوع الماستركلاس أو الفيديو"},
                "ratio": {"type": "string", "enum": ["16:9", "9:16"], "description": "أبعاد الفيديو: 16:9 لليوتيوب أو 9:16 للشورتس وتيك توك"},
                "voice": {"type": "string", "description": "الصوت العصبي (ar_male, ar_egypt, en_male)"}
            },
            "required": ["topic"]
        },
        "handler": _handle_motion_masterclass
    }
]
